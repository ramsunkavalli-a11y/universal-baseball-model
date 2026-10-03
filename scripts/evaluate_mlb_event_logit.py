"""Reconstruct count targets, preflight every fold, then fit one coherent model."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
import evaluate_hitter_2020_extension as old
import prepare_practical_hitter_v33 as s
from fit_practical_hitter_v31 import weights
from universal_baseball.forecast_validation import preflight
from universal_baseball.mlb_event_logit import EVENTS,VALUES,fit,probabilities,batting_rate
from universal_baseball.storage import sha256_file

OUT=old.r.ROOT/'reports/generated/practical-hitter-v36'
COUNT_COLS=['strike_outs','unintentional_walks','hit_by_pitch','singles','doubles','triples','home_runs']
META=['age_centered','age_squared','age_unknown','elapsed_scaled','prior_debut','on_40man','last_stat_gap',
    'career_mlb_observed_pa','career_mlb_left_truncated',*[f'position_{p}' for p in old.r.POS],
    *[f'milb_canceled_{lag}' for lag in range(3)],*s.PED]
FEATURES=META+[f'pooled_{b}_{ev}' for b in old.r.BUCKETS for ev in ['pa',*old.r.EVENTS]]


def write(n,o):(OUT/n).write_text(__import__('json').dumps(o,indent=2,allow_nan=False,default=str),encoding='utf8')


def prepare():
    assert old.r.read(old.r.ROOT/'reports/generated/practical-hitter-v35/report.json')['player_walkthrough_status']=='complete'
    assert not (OUT/'preflight.json').exists();OUT.mkdir(parents=True,exist_ok=True)
    f=pl.read_parquet(old.SOURCE/'features.parquet');counts=pl.read_parquet(old.r.OUT/'dated-stints.parquet').filter(pl.col('sport_id')==1)
    counts=counts.group_by('season','player_id').agg(pl.col('plate_appearances',*COUNT_COLS).sum())
    assert counts['season'].max()==2025
    counts=counts.with_columns((pl.col('plate_appearances')-pl.sum_horizontal(COUNT_COLS)).alias('other'))
    assert not counts.filter(pl.col('other')<0).height
    environment=counts.group_by('season').agg(pl.col('plate_appearances','other',*COUNT_COLS).sum()).sort('season')
    # Offsets get only a negligible positivity floor; scoring/reconstruction use exact observed environment.
    env={r['season']:np.array([r[c] for c in ['other',*COUNT_COLS]],float)/r['plate_appearances'] for r in environment.iter_rows(named=True)}
    assert all((q>0).all() and np.isclose(q.sum(),1) for q in env.values())
    lut={(r['season'],r['player_id']):r for r in counts.iter_rows(named=True)};rows=[]
    for o in f.iter_rows(named=True):
        raw=lut.get((o['target_year'],o['player_id']));pa=raw['plate_appearances'] if raw else 0
        assert pa==o['next_pa'],(o['player_id'],o['origin_year'],'target PA')
        v=np.array([raw[c] if raw else 0 for c in ['other',*COUNT_COLS]],float);assert v.sum()==pa
        if pa:
            actual=float(batting_rate(v[None,:]/pa,env[o['target_year']][None,:])[0])
            assert np.isclose(actual,o['next_batting_rate'],atol=1e-9),(o['player_id'],actual,o['next_batting_rate'])
        row={'row_id':o['row_id']}
        row.update({f'count_{ev}':v[i] for i,ev in enumerate(EVENTS)})
        row.update({f'origin_env_{ev}':env[o['origin_year']][i] for i,ev in enumerate(EVENTS)})
        row.update({f'target_env_{ev}':env[o['target_year']][i] for i,ev in enumerate(EVENTS)})
        rows.append(row)
    f=f.join(pl.DataFrame(rows),on='row_id',validate='1:1');f.write_parquet(OUT/'features.parquet')
    previous=old.r.read(old.OUT/'preflight.json');cells=[]
    for c in previous['cells']:
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']));te=f.filter(pl.col('row_id').is_in(c['test_row_ids']))
        _,note=preflight(tr,te,cutoff=c['year'],fold=c['fold'],features=FEATURES,expected_keys=te.select('row_id','horizon').iter_rows())
        assert tr['target_year'].max()<=c['year'] and (tr['target_year']!=2020).all()
        assert all(not col.startswith(('target_','count_','next_')) for col in FEATURES)
        cells.append(dict(**c,event_preflight=note))
    pl.read_parquet(old.OUT/'support.parquet').write_parquet(OUT/'support.parquet')
    paths=[OUT/'features.parquet',OUT/'support.parquet',old.OUT/'predictions.parquet',old.SOURCE/'source-review.json',
        old.r.OUT/'dated-stints.parquet',Path(__file__),old.r.ROOT/'src/universal_baseball/mlb_event_logit.py',old.r.ROOT/'docs/practical-hitter-v36-contract.md']
    write('preflight.json',dict(before_fitting=True,features=FEATURES,cells=cells,input_hashes={str(p):sha256_file(p) for p in paths},
        target_counts_reconstruct_existing_rate=True,all_eval_rows=30506,protected_outcomes_used=False,
        environment_provenance='Actual league target counts are mature labels only; test predictors use completed origin environment.'))
    print('All event counts and rate labels reconstruct; 35 preflights complete.',len(FEATURES),'features.',flush=True)


def fit_all():
    pre=old.r.read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    f=pl.read_parquet(OUT/'features.parquet');baseline=pl.read_parquet(old.OUT/'predictions.parquet');frames=[];fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];path=OUT/f'forecast-{y}-{k}.parquet'
            if path.exists():
                n=old.r.read(OUT/f'fits-{y}-{k}.json');assert sha256_file(path)==n['prediction_sha256']
                assert sha256_file(Path(n['path']))==n['sha256'];frames.append(pl.read_parquet(path));fits.append(n);continue
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])&(pl.col('next_pa')>0)).sort('row_id')
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');cols=pre['features']
            model=fit(s.safe_matrix(tr,cols),tr.select([f'count_{ev}' for ev in EVENTS]).to_numpy(),
                tr.select([f'target_env_{ev}' for ev in EVENTS]).to_numpy(),weights(tr))
            model['features']=cols;artifact=OUT/f'event-logit-{y}-{k}.joblib';joblib.dump(model,artifact,compress=3)
            env=te.select([f'origin_env_{ev}' for ev in EVENTS]).to_numpy()
            p=probabilities(model['beta'],s.safe_matrix(te,cols),env);rate=batting_rate(p,env)
            q=baseline.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id').with_columns(
                pl.Series('event_rate',rate),pl.col('cohort_pa').alias('event_pa'),*[pl.Series('event_p_'+ev,p[:,i]) for i,ev in enumerate(EVENTS)])
            q=q.with_columns((pl.col('event_pa')*(pl.col('event_rate')/600+pl.col('origin_replacement_rate'))).alias('event_value'))
            q.write_parquet(path);n=dict(path=str(artifact),sha256=sha256_file(artifact),features=cols,optimizer=model['optimizer'],
                training_rows=len(tr),training_players=tr['player_id'].n_unique(),maximum_target_year=int(tr['target_year'].max()),prediction_sha256=sha256_file(path))
            write(f'fits-{y}-{k}.json',n);frames.append(q);fits.append(n)
            print(f'{y}/{k}: converged in {model["optimizer"]["iterations"]} iterations; {len(q)} forecasts',flush=True)
    q=pl.concat(frames).sort('row_id');assert q.select(baseline.columns).equals(baseline.sort('row_id'))
    q.write_parquet(OUT/'predictions.parquet');write('fits.json',fits)
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    write('fit-report.json',dict(new_heads=35,rows=len(q),player_walkthrough_status='pending',protected_outcomes_used=False,frozen_forecast_changed=False))


if __name__=='__main__':
    import sys
    prepare() if '--prepare' in sys.argv else fit_all()
