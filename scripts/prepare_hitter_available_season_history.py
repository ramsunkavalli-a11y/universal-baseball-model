"""Rebuild the evidence clock and seal both actual preflights before fitting."""
from pathlib import Path
import json

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from prepare_hitter_extended_training import profile, verify
from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_available_season_history import rebuild
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/generated/hitter-available-season-history'
CURRENT = ROOT/'reports/generated/hitter-preseason-readiness-v68'
ANCHOR = ROOT/'reports/generated/hitter-extended-training/scored-predictions.parquet'
FIXED = [(677594,2021),(677951,2021),(679631,2021),(691023,2022)]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def write(name, data):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n',encoding='utf8')


def main():
    assert not (OUT/'preflight.json').exists(), 'Preserve prefit evidence'
    prior = read(CURRENT/'preflight.json')
    final = read(ROOT/'reports/generated/hitter-prospect-workload-specialization/completed-review.json')
    assert final['player_walkthrough_status']=='complete'
    base = profile(pl.read_parquet(CURRENT/'features.parquet')).sort('row_id')
    counts_path = ROOT/'reports/generated/practical-hitter-v31/counts.parquet'
    games_path = ROOT/'reports/generated/practical-hitter-v38/game-counts.parquet'
    counts = pl.read_parquet(counts_path).filter(pl.col('season')<=2024)
    games = pl.read_parquet(games_path).filter(pl.col('season')<=2024)
    calendar, calendar_dates, names = rebuild(base,counts,games,available=False)
    source, dates, _ = rebuild(base,counts,games,available=True)
    repairs = []
    for n in names:
        old,new = base[n].to_numpy(),calendar[n].to_numpy()
        np.testing.assert_allclose(old,new,atol=1e-12,rtol=0,err_msg=n)
        different = abs(source[n].to_numpy()-old)>1e-12
        if different.any():
            changed_years = sorted(base.filter(pl.Series(different))['origin_year'].unique().to_list())
            assert set(changed_years)<={2020,2021,2022}, (n,changed_years)
            repairs.append(dict(feature=n,changed_rows=int(different.sum()),origins=changed_years,
                maximum_absolute_difference=float(np.max(abs(source[n].to_numpy()-old)))))
    assert source.filter(~pl.col('origin_year').is_in([2020,2021,2022])).select(prior['pa_features']).equals(
        base.filter(~pl.col('origin_year').is_in([2020,2021,2022])).select(prior['pa_features']))
    q = pl.read_parquet(ANCHOR).sort('row_id')
    original = pl.read_parquet(CURRENT/'scored-predictions.parquet').sort('row_id')
    assert q.select(original.columns).equals(original) and len(q)==30506
    assert base.filter(pl.col('row_id').is_in(q['row_id'].to_list()))['next_pa'].equals(q['next_pa'])
    OUT.mkdir(parents=True,exist_ok=True)
    source.write_parquet(OUT/'features.parquet')
    dates.write_parquet(OUT/'source-years.parquet')
    cases = []
    for pid,y in FIXED:
        a = base.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y))
        assert len(a)==1,(pid,y)
        o = a.row(0,named=True)
        b = source.filter(pl.col('row_id')==o['row_id']).row(0,named=True)
        shifted = dates.filter(pl.col('row_id')==o['row_id']).row(0,named=True)
        changed = {n:dict(calendar=o[n],available=b[n]) for n in names if abs(o[n]-b[n])>1e-12}
        history = counts.filter((pl.col('player_id')==pid)&pl.col('season').is_between(y-3,y)).sort('season','bucket')
        cases.append(dict(player_id=pid,name=o['player_name'],origin=y,actual_age=o['age'],
            calendar_source_years=[y-k for k in range(3)],available_source_years=shifted,
            actual_source_counts=history.to_dicts(),changed_inputs=changed,
            preserved=dict(last_stat_gap=o['last_stat_gap'],scout_rank=o['scout_rank_score_0'],draft_elapsed=o['draft_elapsed'],
                stage=o['stage'],canceled_calendar_flags=[o['milb_canceled_'+str(k)] for k in range(3)])))
    write('source-review.json',dict(calendar_reconstruction_maximum_tolerance=1e-12,
        rows=len(base),candidate_changed_columns=repairs,profile_semantics='Original actual origin-season profiles retained',
        fixed_source_cases=cases,source_walkthrough_status='pending'))
    cells,supports,profiles = [],[],[]
    replayed = 0
    with threadpool_limits(limits=2):
        for c in prior['cells']:
            y,k = c['year'],c['fold']
            teids, trids = c['test_row_ids'],c['training_row_ids']
            control_query = base.filter(pl.col('row_id').is_in(teids)).sort('row_id')
            candidate_query = source.filter(pl.col('row_id').is_in(teids)).sort('row_id')
            checks = {}
            for arm,f in [('calendar',base),('available',source)]:
                tr = f.filter(pl.col('row_id').is_in(trids)).sort('row_id')
                te = f.filter(pl.col('row_id').is_in(teids)).sort('row_id')
                sup,note = preflight(tr,te,cutoff=y,fold=k,features=prior['pa_features'],expected_keys=te.select('row_id','horizon').iter_rows())
                checks[arm] = note
                supports.append(sup.with_columns(pl.lit(arm).alias('arm')))
                for kind,keys in [('broad',['prior_debut','dominant_level','age_band']),
                                  ('refined',['prior_debut','dominant_level','age_band','rank_band','thin_pro','new_draftee'])]:
                    for subset,sub in [('all',tr),('positive',tr.filter(pl.col('next_pa')>0))]:
                        n = sub.group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
                        profiles.append(te.select('row_id',*keys).join(n,on=keys,how='left',validate='m:1').with_columns(
                            pl.col('profile_people').fill_null(0),pl.lit(arm).alias('arm'),pl.lit(kind).alias('kind'),pl.lit(subset).alias('subset')))
            fit = read(CURRENT/f'fit-{y}-{k}.json')
            head = next(h for h in fit['heads'] if h['head']=='participation')
            verify({head['path']:head['sha256']})
            model = joblib.load(head['path'])
            baseline = model.predict_proba(control_query.select(prior['pa_features']).to_numpy())[:,1]
            scored = q.filter(pl.col('row_id').is_in(teids)).sort('row_id')
            np.testing.assert_array_equal(baseline,scored['preseason_raw_p'].to_numpy())
            replayed += 1
            a = base.filter(pl.col('row_id').is_in(trids)).sort('row_id')
            b = source.filter(pl.col('row_id').is_in(trids)).sort('row_id')
            identical = a.select(prior['pa_features']).equals(b.select(prior['pa_features'])) and control_query.select(prior['pa_features']).equals(candidate_query.select(prior['pa_features']))
            assert identical == (y in [2016,2017,2018])
            cells.append(dict(year=y,fold=k,information_date=c['information_date'],training_row_ids=trids,test_row_ids=teids,
                checks=checks,control=head,identical_matrices=identical))
    pl.concat(supports).write_parquet(OUT/'support.parquet')
    pl.concat(profiles,how='diagonal_relaxed').write_parquet(OUT/'profile-support.parquet')
    paths = [Path(__file__),ROOT/'src/universal_baseball/hitter_available_season_history.py',
        ROOT/'tests/test_hitter_available_season_history.py',ROOT/'docs/hitter-available-season-history-contract.md',
        ROOT/'scripts/evaluate_hitter_available_season_history.py',
        CURRENT/'preflight.json',CURRENT/'features.parquet',CURRENT/'scored-predictions.parquet',ANCHOR,
        counts_path,games_path,OUT/'source-review.json',OUT/'features.parquet',OUT/'source-years.parquet',
        OUT/'support.parquet',OUT/'profile-support.parquet',ROOT/'scripts/fit_practical_hitter_v31.py',
        ROOT/'src/universal_baseball/forecast_validation.py']
    write('preflight.json',dict(before_fitting=True,checks_before_fits=70,controls_replayed=replayed,
        new_fits=20,reused_identical_controls=15,features=prior['pa_features'],settings=prior['settings'],cells=cells,
        input_hashes={str(p):sha256_file(p) for p in paths},source_review_complete=False,
        source_rows=len(source),evaluation_rows=len(q),protected_outcomes_used=False,
        source_case_review_required_before_fit=True,player_walkthrough_status='pending'))
    print(json.dumps(dict(rows=len(source),changed_columns=len(repairs),fixed_source_cases=[(c['name'],c['origin'],len(c['changed_inputs'])) for c in cases],
        checks=70,controls_replayed=replayed,new_fits=20),indent=2),flush=True)


if __name__=='__main__':
    main()
