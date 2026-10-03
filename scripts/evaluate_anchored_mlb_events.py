"""Empirical anchor repair; preserve event-model settings and all comparisons."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
import evaluate_mlb_event_logit as previous
from fit_practical_hitter_v31 import weights
from universal_baseball.forecast_validation import preflight
from universal_baseball.mlb_event_logit import EVENTS,fit,probabilities,batting_rate
from universal_baseball.mlb_event_anchor import empirical_anchor,transport_anchor
from universal_baseball.storage import sha256_file

old=previous.old;s=previous.s
OUT=old.r.ROOT/'reports/generated/practical-hitter-v37'


def write(n,o):(OUT/n).write_text(__import__('json').dumps(o,indent=2,allow_nan=False,default=str),encoding='utf8')


def prepare():
    assert old.r.read(previous.OUT/'report.json')['player_walkthrough_status']=='complete'
    assert not (OUT/'preflight.json').exists();OUT.mkdir(parents=True,exist_ok=True)
    f=pl.read_parquet(previous.OUT/'features.parquet')
    raw=pl.read_parquet(old.r.OUT/'dated-stints.parquet').filter(pl.col('sport_id')==1).group_by('season','player_id').agg(
        pl.col('plate_appearances',*previous.COUNT_COLS).sum()).with_columns(
        (pl.col('plate_appearances')-pl.sum_horizontal(previous.COUNT_COLS)).alias('other'))
    lut={(r['season'],r['player_id']):r for r in raw.iter_rows(named=True)};counts=[]
    for o in f.iter_rows(named=True):
        n=np.zeros(8)
        for lag,w in enumerate([1.,.8,.6]):
            h=lut.get((o['origin_year']-lag,o['player_id']))
            if h:n+=w*np.array([h[c] for c in ['other',*previous.COUNT_COLS]],float)
        assert np.isclose(n.sum(),o['pooled_MLB_pa'],atol=1e-9)
        counts.append(n)
    counts=np.asarray(counts);origin=f.select([f'origin_env_{ev}' for ev in EVENTS]).to_numpy()
    target=f.select([f'target_env_{ev}' for ev in EVENTS]).to_numpy()
    anchor=empirical_anchor(counts,origin);offset=transport_anchor(anchor,origin,target)
    assert np.allclose(anchor.sum(1),1) and np.allclose(offset.sum(1),1)
    assert np.allclose(probabilities(np.zeros((len(previous.FEATURES)+1,7)),s.safe_matrix(f,previous.FEATURES),anchor),anchor,atol=1e-12)
    f=f.with_columns(*[pl.Series('anchor_'+ev,anchor[:,i]) for i,ev in enumerate(EVENTS)],
        *[pl.Series('training_offset_'+ev,offset[:,i]) for i,ev in enumerate(EVENTS)],pl.Series('anchor_weighted_mlb_pa',counts.sum(1)))
    f.write_parquet(OUT/'features.parquet');pre=old.r.read(previous.OUT/'preflight.json');cells=[]
    for c in pre['cells']:
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']));te=f.filter(pl.col('row_id').is_in(c['test_row_ids']))
        _,note=preflight(tr,te,cutoff=c['year'],fold=c['fold'],features=pre['features'],expected_keys=te.select('row_id','horizon').iter_rows())
        assert tr['target_year'].max()<=c['year'] and (tr['target_year']!=2020).all()
        cells.append(dict(**c,anchor_preflight=note))
    pl.read_parquet(previous.OUT/'support.parquet').write_parquet(OUT/'support.parquet')
    paths=[OUT/'features.parquet',OUT/'support.parquet',previous.OUT/'predictions.parquet',previous.OUT/'report.json',
        old.r.OUT/'dated-stints.parquet',Path(__file__),old.r.ROOT/'src/universal_baseball/mlb_event_logit.py',
        old.r.ROOT/'src/universal_baseball/mlb_event_anchor.py',old.r.ROOT/'docs/practical-hitter-v37-contract.md']
    write('preflight.json',dict(before_fitting=True,features=pre['features'],cells=cells,input_hashes={str(p):sha256_file(p) for p in paths},
        target_counts_unchanged=True,old_features_unchanged=True,all_eval_rows=30506,protected_outcomes_used=False))
    print('Empirical anchors/count exposures verified; 35 preflights complete.',flush=True)


def fit_all():
    pre=old.r.read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    f=pl.read_parquet(OUT/'features.parquet');baseline=pl.read_parquet(previous.OUT/'predictions.parquet');frames=[];fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];path=OUT/f'forecast-{y}-{k}.parquet'
            if path.exists():
                n=old.r.read(OUT/f'fits-{y}-{k}.json');assert sha256_file(path)==n['prediction_sha256']
                assert sha256_file(Path(n['path']))==n['sha256'];frames.append(pl.read_parquet(path));fits.append(n);continue
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])&(pl.col('next_pa')>0)).sort('row_id')
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');cols=pre['features']
            model=fit(s.safe_matrix(tr,cols),tr.select([f'count_{ev}' for ev in EVENTS]).to_numpy(),
                tr.select([f'training_offset_{ev}' for ev in EVENTS]).to_numpy(),weights(tr))
            model['features']=cols;artifact=OUT/f'anchored-event-{y}-{k}.joblib';joblib.dump(model,artifact,compress=3)
            anchor=te.select([f'anchor_{ev}' for ev in EVENTS]).to_numpy();env=te.select([f'origin_env_{ev}' for ev in EVENTS]).to_numpy()
            p=probabilities(model['beta'],s.safe_matrix(te,cols),anchor)
            q=baseline.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id').with_columns(
                pl.Series('anchored_rate',batting_rate(p,env)),pl.col('cohort_pa').alias('anchored_pa'),
                pl.Series('anchor_only_rate',batting_rate(anchor,env)),pl.col('cohort_pa').alias('anchor_only_pa'),
                *[pl.Series('anchored_p_'+ev,p[:,i]) for i,ev in enumerate(EVENTS)])
            q=q.with_columns(*[(pl.col(a+'_pa')*(pl.col(a+'_rate')/600+pl.col('origin_replacement_rate'))).alias(a+'_value') for a in ['anchored','anchor_only']])
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
