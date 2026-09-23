"""Test dropping only an exogenously unavailable annual block, without scaling odds."""
import argparse
import json
from pathlib import Path
import warnings
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from fit_hitter_arrival_coherence_v1 import save
from fit_hitter_detail_arrival_v1 import OUT as SOURCE
from universal_baseball.hitter_detail_arrival import TARGETS, eligible, target_values
from universal_baseball.hitter_canceled_season import available_columns, outage_mask, hide_annual_block, fit_model, predict
from universal_baseball.storage import sha256_file

OUT = Path('reports/generated/hitter-canceled-season-v1')
PACKAGE = Path('model_artifacts/hitter-canceled-season-v1-2026-09-23')
HISTORY = Path('model_artifacts/hitter-history-calibration-v1-2026-09-23/predictions.parquet')
CODE = [Path('docs/hitter-canceled-season-v1-plan.md'),Path(__file__),
        Path('src/universal_baseball/hitter_canceled_season.py'),Path('tests/test_hitter_canceled_season.py'),
        Path('src/universal_baseball/hitter_detail_arrival.py'),Path('src/universal_baseball/hitter_model_tournament.py')]


def hashes():
    return {str(p):sha256_file(p) for p in [*CODE,SOURCE/'input-panel.parquet',SOURCE/'prefit-manifest.json',
            SOURCE/'predictions.parquet',SOURCE/'reference-predictions.parquet',HISTORY]}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--freeze',action='store_true'); args = ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True); (OUT/'fits').mkdir(exist_ok=True)
    p = pl.read_parquet(SOURCE/'input-panel.parquet')
    columns = json.loads((SOURCE/'prefit-manifest.json').read_text())['arms']['R']
    if args.freeze:
        if (OUT/'prefit-manifest.json').exists(): raise ValueError('Already frozen')
        save(OUT/'prefit-manifest.json',{'hashes':hashes(),'columns':columns,
             'omission_columns':{str(k):available_columns(columns,[k]) for k in (1,2)},
             'no_prior_columns':available_columns(columns,[1,2]),'protected_outcomes_used':False})
        print(json.dumps({'frozen':True,'features':{str(k):len(available_columns(columns,[k])) for k in (1,2)}})); return
    pre = json.loads((OUT/'prefit-manifest.json').read_text()); assert hashes() == pre['hashes']
    old = pl.read_parquet(SOURCE/'predictions.parquet').filter(~pl.col('cold') & ~pl.col('pandemic') &
             (pl.col('engine') == 'lightgbm') & (pl.col('arm') == 'R'))
    frames = []; notes = []
    for (target,year),base in old.partition_by('target','origin_year',as_dict=True).items():
        query = p.filter(pl.col('origin_year') == year)
        np.testing.assert_array_equal(base['player_id'],query['player_id'])
        frames.append(base)
        for arm in ('O','N'):
            mask = outage_mask(query,year)
            result = base['probability'].to_numpy().copy()
            if mask.any():
                path = OUT/'fits'/f'{target}-{year}-{arm}.parquet'
                if path.exists() and path.with_suffix('.json').exists():
                    note = json.loads(path.with_suffix('.json').read_text())
                    assert note['sha256'] == sha256_file(path)
                    forecast = pl.read_parquet(path)
                else:
                    omitted = [year-2020] if arm == 'O' else [1,2]
                    cols = available_columns(columns,omitted)
                    train = eligible(p,year,target)
                    print(f'{target} {year} {arm} omit {omitted}',flush=True)
                    model,used,note = fit_model(train,cols,target)
                    result[mask] = predict(model,used,query)[mask]
                    forecast = base.with_columns(pl.Series('probability',result),pl.lit(arm).alias('arm'))
                    forecast.write_parquet(path)
                    note.update(target=target,year=year,arm=arm,omitted=omitted,routed_rows=int(mask.sum()),
                                latest_label=int(train['origin_year'].max())+TARGETS[target],sha256=sha256_file(path))
                    save(path.with_suffix('.json'),note)
                frames.append(forecast); notes.append(note)
            else:
                frames.append(base.with_columns(pl.lit(arm).alias('arm')))
    combined = pl.concat(frames,how='vertical_relaxed')
    combined.write_parquet(OUT/'predictions.parquet')
    stress = []; stress_notes = []; replay_max = 0.
    for year in (2017,2018):
        query = p.filter(pl.col('origin_year') == year)
        train = eligible(p,year,'next_year')
        base = old.filter((pl.col('origin_year') == year) & (pl.col('target') == 'next_year'))
        print(f'Outage stress {year} original replay',flush=True)
        model,used,note = fit_model(train,columns,'next_year')
        intact = predict(model,used,query)
        np.testing.assert_array_equal(intact,base['probability'])
        replay_max = max(replay_max,float(np.max(abs(intact-base['probability'].to_numpy()))))
        for lag in (1,2):
            masked = hide_annual_block(query,lag)
            broken = predict(model,used,masked)
            print(f'Outage stress {year} omit {lag}',flush=True)
            alt,altcols,anote = fit_model(train,available_columns(columns,[lag]),'next_year')
            recovered = predict(alt,altcols,masked)
            # All retained features exactly match; no hidden-block dependence remains.
            assert masked.select(altcols).equals(query.select(altcols))
            np.testing.assert_array_equal(recovered,predict(alt,altcols,query))
            for name,prob in [('intact_R',intact),('masked_R',broken),('available_O',recovered)]:
                stress.append(base.with_columns(pl.Series('probability',prob),pl.lit(name).alias('arm'),pl.lit(lag).alias('hidden_lag')))
            stress_notes.append({'year':year,'hidden_lag':lag,'original':note,'available':anote})
    pl.concat(stress).write_parquet(OUT/'outage-stress.parquet')
    # Future labels and predictor snapshots cannot affect a 2021 fit or its query.
    m = p
    for h in (1,2,3):
        m = m.with_columns(pl.when(pl.col('origin_year')+h > 2021).then(9999.).otherwise(pl.col(f'pa_h{h}')).alias(f'pa_h{h}'))
    m = m.with_columns(*[pl.when(pl.col('origin_year') > 2021).then(987.).otherwise(pl.col(c).cast(pl.Float64)).alias(c) for c in columns])
    print('Future-mutation refit',flush=True)
    model,used,_ = fit_model(eligible(m,2021,'regular_three'),available_columns(columns,[1]),'regular_three')
    query = m.filter(pl.col('origin_year') == 2021); mask = outage_mask(query,2021)
    mutated = predict(model,used,query)[mask]
    expected = combined.filter((pl.col('origin_year') == 2021) & (pl.col('target') == 'regular_three') & (pl.col('arm') == 'O'))['probability'].to_numpy()[mask]
    np.testing.assert_array_equal(mutated,expected)
    assert hashes() == pre['hashes']
    diagnosis = p.filter(pl.col('prospect')).group_by('origin_year','missing_lag1').agg(
        pl.len().alias('rows'),(pl.col('pa_h1')>0).sum().alias('next_year_arrivals'),
        pl.col('age').mean().alias('mean_age'),pl.col('pa_lag0').mean().alias('mean_current_pa')).sort('origin_year','missing_lag1').to_dicts()
    save(OUT/'fit-manifest.json',{'fits':notes,'stress':stress_notes,'missingness_diagnosis':diagnosis,
        'original_replay_max_difference':replay_max,'future_mutation_max_difference':float(np.max(abs(mutated-expected))),
        'prefit_sha256':sha256_file(OUT/'prefit-manifest.json'),
        'files':{n:sha256_file(OUT/n) for n in ('predictions.parquet','outage-stress.parquet')},
        'protected_outcomes_used':False,'production_forecasts_changed':False})
    print(json.dumps({'real_fits':len(notes),'stress_fits':6,'mutation_refits':1,'prediction_rows':combined.height,'verified_future_invariance':True}))


if __name__ == '__main__':
    warnings.filterwarnings('ignore',message='X does not have valid feature names')
    with threadpool_limits(limits=4):main()
