"""Required source-to-input player walks and repaired-source support checks."""
import json
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
import finalize_hitter_minor_statcast_source as final

ROOT,OUT,SOURCE=final.ROOT,final.OUT,final.SOURCE
CURRENT=ROOT/'reports/generated/hitter-preseason-readiness-v68'


def read(path):return json.loads(Path(path).read_text(encoding='utf8'))


def repaired_support(f,annual):
    parts=[]
    for lag in range(3):
        parts.append(f.select('row_id','player_id',(pl.col('origin_year')-lag).alias('season')).join(
            annual.select('player_id','season','league_id','measured_ev_contacts','measured_pair_contacts'),
            on=['player_id','season'],how='inner'))
    c=pl.concat(parts).group_by('row_id','league_id').agg(pl.col('measured_ev_contacts').sum().alias('ev_n'),
        pl.col('measured_pair_contacts').sum().alias('pair_n'))
    q=f.select('row_id','player_id','origin_year','outer_fold','prior_debut','snapshot_level','age','next_pa').join(c,on='row_id').filter(pl.col('ev_n')>0)
    q=q.with_columns((pl.col('age')//5).cast(pl.Int64).alias('age_band'),pl.when(pl.col('ev_n')<50).then(pl.lit('under50'))
        .when(pl.col('ev_n')<200).then(pl.lit('50to199')).otherwise(pl.lit('200plus')).alias('sample_band'))
    before=pl.read_parquet(SOURCE/'origin-tracking-support-features.parquet')
    keys=['row_id','league_id','player_id','origin_year','outer_fold','prior_debut','age_band','sample_band']
    assert q.select(keys).sort(keys).equals(before.select(keys).sort(keys)), 'Repair changed support profile membership'
    q.write_parquet(OUT/'origin-tracking-support-features.parquet')
    original=read(SOURCE/'training-support-review.json')
    profile=pl.read_parquet(SOURCE/'tracked-profile-support.parquet')
    updated=profile.drop('ev_n','pair_n').join(q.select('row_id','league_id','ev_n','pair_n'),on=['row_id','league_id'],validate='1:1')
    updated.write_parquet(OUT/'tracked-profile-support.parquet')
    # Membership and every cutoff-known profile are equal; independent distinct-
    # person counts therefore reproduce the original support, not merely rows.
    pre=read(CURRENT/'preflight.json');checked=0
    for cell in pre['cells']:
        tr=q.filter(pl.col('row_id').is_in(cell['training_row_ids'])&(pl.col('next_pa')>0))
        assert tr.filter((pl.col('origin_year')+1>cell['year'])|(pl.col('outer_fold')==cell['fold'])).is_empty()
        groups=tr.group_by('league_id','prior_debut','age_band','sample_band').agg(pl.col('player_id').n_unique().alias('n'))
        test=updated.filter(pl.col('test_origin')==cell['year']).filter(pl.col('test_fold')==cell['fold']).join(groups,
            on=['league_id','prior_debut','age_band','sample_band'],how='left').with_columns(pl.col('n').fill_null(0))
        assert test.select((pl.col('n')==pl.col('active_training_profile_people')).all()).item();checked+=1
    final.write('training-support-review.json',dict(original,verified_against_repaired_source=True,profile_membership_unchanged=True,
        independently_rechecked_folds=checked,original_support_review_sha256=sha256_file(SOURCE/'training-support-review.json'),
        reviewed_annual_sha256=sha256_file(OUT/'annual-launch-features.parquet')))
    return updated


def main():
    report=read(OUT/'source-report.json')
    for group in ['input_hashes','output_hashes']:
        for p,h in report[group].items():assert sha256_file(Path(p))==h
    annual=pl.read_parquet(OUT/'annual-launch-features.parquet');f=pl.read_parquet(CURRENT/'features.parquet')
    q=pl.read_parquet(ROOT/'reports/generated/hitter-statcast-next-year/scored-predictions.parquet')
    dated=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet')
    names=read(ROOT/'reports/generated/practical-hitter-numeric-repair-v53/preflight.json')['rate_features']
    support=repaired_support(f,annual)
    fixed=[(682829,2022),(682829,2023),(691406,2023),(691406,2024),(694671,2023),
        (701762,2024),(805811,2024),(821181,2024),(643271,2023),(676551,2023),(676939,2023)]
    legacy=pl.concat([pl.read_csv(p,columns=final.original.capture.COLUMNS,
        schema_overrides={c:pl.String for c in final.original.capture.COLUMNS},null_values=['','null'])
        for p in sorted(final.original.capture.LEGACY.glob('*.csv'))])
    legacy=legacy.filter((pl.col('type')=='X')&pl.col('events').is_not_null())
    fresh=pl.read_parquet(OUT/'launch-events-2023.parquet').filter(pl.col('game_date')<=pl.date(2023,6,15))
    cases=[];hashes={str(p):sha256_file(p) for p in [Path(__file__),CURRENT/'features.parquet',CURRENT/'scored-predictions.parquet',
        ROOT/'reports/generated/hitter-statcast-next-year/scored-predictions.parquet',OUT/'source-report.json',
        ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet']}
    with threadpool_limits(limits=2):
        for pid,year in fixed:
            row=q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==year));assert len(row)==1
            o=row.row(0,named=True);rid=o['row_id'];feature=f.filter(pl.col('row_id')==rid)
            h=next(h for h in read(ROOT/f'reports/generated/practical-hitter-numeric-repair-v53/fit-{year}-{o["outer_fold"]}.json')['heads'] if h['head']=='rate')
            assert sha256_file(Path(h['path']))==h['sha256'];hashes[h['path']]=h['sha256']
            model=joblib.load(h['path']);x=safe_matrix(feature,names)[0];terms=model.coef_*x
            replay=float(model.intercept_+terms.sum());assert np.isclose(replay,o['preseason_rate'],atol=1e-10)
            fields=['row_id','player_id','player_name','origin_year','target_year','outer_fold','age','snapshot_level','prior_debut',
                'preseason_p','preseason_conditional_pa','preseason_pa','preseason_rate','preseason_value',
                'sc_own_ev_n','ridge_measurements_rate','ridge_measurements_value','next_pa','next_value']
            origin={k:o[k] for k in fields};origin['actual_future_relative_rate']=o['actual_future_relative_rate'] if o['next_pa']>0 else None
            history=annual.filter((pl.col('player_id')==pid)&pl.col('season').is_between(year-2,year)).sort('season','league_id')
            # Peer identities depend only on origin-known features, never targets.
            pool=q.filter((pl.col('origin_year')==year)&(pl.col('snapshot_level')==o['snapshot_level'])&
                (pl.col('prior_debut')==o['prior_debut'])&(pl.col('player_id')!=pid))
            pool=pool.with_columns((((pl.col('age')-o['age'])/3)**2+((pl.col('pa_0')-o['pa_0'])/250)**2+
                ((pl.col('minor_pa_0')-o['minor_pa_0'])/250)**2+((pl.col('quality_0')-o['quality_0'])/2)**2).alias('peer_distance')).sort('peer_distance','player_id').head(4)
            peers=[]
            for p in pool.iter_rows(named=True):
                r={k:p[k] for k in fields};r['peer_distance']=p['peer_distance']
                r['actual_future_relative_rate']=p['actual_future_relative_rate'] if p['next_pa']>0 else None
                r['minor_launch_history']=annual.filter((pl.col('player_id')==p['player_id'])&pl.col('season').is_between(year-2,year)).to_dicts()
                peers.append(r)
            same_window=fresh.filter(pl.col('player_id')==pid) if year==2023 else fresh.head(0)
            old=legacy.filter(pl.col('batter')==str(pid)) if year==2023 else legacy.head(0)
            mapped=old.with_columns(pl.col('game_pk').cast(pl.Int64),pl.col('at_bat_number').cast(pl.Int64),
                pl.col('pitch_number').cast(pl.Int64),pl.col('batter').cast(pl.Int64).alias('player_id'))
            lost=same_window.join(mapped.select('game_pk','player_id','at_bat_number','pitch_number'),
                on=['game_pk','player_id','at_bat_number','pitch_number'],how='anti')
            cases.append(dict(origin=origin,selection='fixed source diagnostic cases, including pilot high/low contact profiles; no result-selected win',
                dated_production=dated.filter((pl.col('player_id')==pid)&pl.col('season').is_between(year-2,year)).to_dicts(),
                minor_launch_history=history.to_dicts(),own_minor_ev_n=int(history['measured_ev_contacts'].sum()),
                current_model_inputs=feature.select(names).to_dicts()[0],current_rate_trace=dict(intercept=float(model.intercept_),
                    sum_terms=float(terms.sum()),replayed_rate=replay,head_sha256=h['sha256'],
                    all_terms=[dict(feature=n,input=float(v),coefficient=float(c),term=float(t)) for n,v,c,t in zip(names,x,model.coef_,terms)]),
                training_profiles=support.filter(pl.col('row_id')==rid).to_dicts(),
                partial_2023_cache=dict(applicable=year==2023,recovered_nonbunt_contacts_through_June15=len(same_window),
                    old_raw_terminal_contacts_through_June15=len(old),new_nonbunt_contacts_missing_in_old_keys=len(lost)),
                peers=peers,no_minor_tracking_in_existing_forecast=True,forecast_changed=False))
    final.write('player-source-walkthrough.json',dict(cases=cases,current_rate_replays=len(cases),input_hashes=hashes,
        peer_rule='Same origin/snapshot level/debut; four nearest age, MLB/minor PA and current production before inspecting outcomes.',
        player_walkthrough_status='machine_traces_complete_readable_review_pending',models_fitted=0,predictive_gain_claimed=False))
    print('Source player-origin walks:',len(cases),'all current rate heads replayed; no forecasts changed.')


if __name__=='__main__':main()
