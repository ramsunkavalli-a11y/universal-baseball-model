"""Dedicated origin-active MLB workload head, not future-outcome conditioning."""
from pathlib import Path
import json
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
import evaluate_hitter_games_v38 as previous
from fit_practical_hitter_v31 import tree,weights
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file

OUT=previous.s.r.ROOT/'reports/generated/practical-hitter-v39'


def write(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False,default=str),encoding='utf8')


def prepare():
    OUT.mkdir(parents=True,exist_ok=True);assert not (OUT/'preflight.json').exists()
    assert previous.s.r.read(previous.OUT/'report.json')['player_walkthrough_status']=='complete'
    old=previous.s.r.read(previous.OUT/'preflight.json');f=pl.read_parquet(previous.OUT/'features.parquet');cells=[];support=[]
    for c in old['cells']:
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])&(pl.col('pa_0')>0));te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])&(pl.col('pa_0')>0))
        sup,note=preflight(tr,te,cutoff=c['year'],fold=c['fold'],features=old['features'],expected_keys=te.select('row_id','horizon').iter_rows())
        def profile(g):return g.with_columns((pl.col('age')//5).alias('age_group'),
            pl.when(pl.col('pa_0')<200).then(pl.lit('brief')).when(pl.col('pa_0')<400).then(pl.lit('partial')).otherwise(pl.lit('regular')).alias('volume_group'),
            (pl.col('elapsed')<=1).alias('new_mlb'))
        keys=['age_group','volume_group','new_mlb'];cnt=profile(tr).group_by(keys).agg(pl.col('player_id').n_unique().alias('mlb_profile_players'))
        support.append(sup.join(profile(te).select('row_id',*keys),on='row_id',validate='1:1').join(cnt,on=keys,how='left',validate='m:1').with_columns(pl.col('mlb_profile_players').fill_null(0)))
        cells.append(dict(year=c['year'],fold=c['fold'],training_row_ids=tr['row_id'].to_list(),test_row_ids=te['row_id'].to_list(),
            full_training_row_ids=c['training_row_ids'],full_test_row_ids=c['test_row_ids'],subset_check=note,
            training_future_zero_rows=int((tr['next_pa']==0).sum()),training_future_zero_players=tr.filter(pl.col('next_pa')==0)['player_id'].n_unique()))
    pl.concat(support).write_parquet(OUT/'support.parquet')
    paths=[previous.OUT/'features.parquet',previous.OUT/'preflight.json',previous.OUT/'predictions.parquet',previous.OUT/'report.json',
        OUT/'support.parquet',Path(__file__),previous.s.r.ROOT/'docs/practical-hitter-v39-contract.md']
    write('preflight.json',dict(before_fitting=True,features=old['features'],cells=cells,input_hashes={str(p):sha256_file(p) for p in paths},
        eval_rows=30506,mlb_eval_rows=sum(len(c['test_row_ids']) for c in cells),fixed_rate=True,source_features=str(previous.OUT/'features.parquet')))
    print('All 35 current-MLB subset preflights saved, retaining future exits.',flush=True)


def fit():
    pre=previous.s.r.read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    f=pl.read_parquet(pre['source_features']);base=pl.read_parquet(previous.OUT/'predictions.parquet');cols=pre['features'];frames=[];fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];path=OUT/f'forecast-{y}-{k}.parquet'
            if path.exists():
                n=previous.s.r.read(OUT/f'fit-{y}-{k}.json');assert sha256_file(path)==n['prediction_sha256'];assert sha256_file(Path(n['path']))==n['sha256']
                frames.append(pl.read_parquet(path));fits.append(n);continue
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id');te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            model=tree();model.fit(tr.select(cols).to_numpy(),tr['next_pa'].to_numpy(),sample_weight=weights(tr))
            artifact=OUT/f'mlb-pa-{y}-{k}.joblib';joblib.dump(model,artifact,compress=3)
            raw=model.predict(te.select(cols).to_numpy());assert np.isfinite(raw).all();p=np.clip(raw,0,800);p[te['hard_unavailable'].to_numpy()]=0
            fresh=te.select('row_id').with_columns(pl.Series('_new_pa',p));q=base.filter(pl.col('row_id').is_in(c['full_test_row_ids'])).sort('player_id')
            q=q.join(fresh,on='row_id',how='left',validate='1:1').with_columns(pl.col('_new_pa').fill_null(pl.col('games_pa')).alias('domain_pa'),pl.col('games_rate').alias('domain_rate')).drop('_new_pa')
            q=q.with_columns((pl.col('domain_pa')*(pl.col('domain_rate')/600+pl.col('origin_replacement_rate'))).alias('domain_value'))
            q.write_parquet(path);n=dict(path=str(artifact),sha256=sha256_file(artifact),prediction_sha256=sha256_file(path),features=cols,
                training_rows=len(tr),training_players=tr['player_id'].n_unique(),maximum_target_year=int(tr['target_year'].max()),
                clipped_rows=int(((raw<0)|(raw>800)).sum()),subset_current_mlb=True,year=y,fold=k)
            write(f'fit-{y}-{k}.json',n);fits.append(n);frames.append(q);print(f'{y}/{k}: {len(te)} dedicated MLB, {len(q)-len(te)} unchanged others',flush=True)
    q=pl.concat(frames).sort('row_id');assert q.select(base.columns).equals(base.sort('row_id'))
    absent=q.filter(pl.col('pa_0')==0);assert absent['domain_pa'].equals(absent['games_pa']) and absent['domain_value'].equals(absent['games_value'])
    q.write_parquet(OUT/'predictions.parquet');write('fits.json',fits)
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    write('fit-report.json',dict(new_heads=35,rows=len(q),fixed_rate=True,absent_forecasts_bit_exact=True,protected_outcomes_used=False,player_walkthrough_status='pending'))


if __name__=='__main__':
    import sys
    prepare() if '--prepare' in sys.argv else fit()
