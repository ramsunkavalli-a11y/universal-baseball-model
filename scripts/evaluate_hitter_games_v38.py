"""Fixed game/role workload extension; strongest batting head is unchanged."""
import json
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
import prepare_hitter_games_v38 as s
import evaluate_hitter_2020_extension as old
from fit_practical_hitter_v31 import tree,weights
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file

OUT=s.OUT
write=s.write


def prepare():
    assert s.r.read(OUT/'source-review.json')['source_walkthrough_status']=='complete'
    assert s.r.read(old.OUT/'report.json')['player_walkthrough_status']=='complete'
    assert not (OUT/'preflight.json').exists()
    audit=s.r.read(OUT/'source-audit.json')
    for p,h in audit['input_hashes'].items():assert sha256_file(Path(p))==h,p
    f=pl.read_parquet(OUT/'features.parquet');prior=s.r.read(old.OUT/'preflight.json')
    cols=prior['features']+audit['new_features'];cells=[];profiles=[]
    for c in prior['cells']:
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']));te=f.filter(pl.col('row_id').is_in(c['test_row_ids']))
        _,note=preflight(tr,te,cutoff=c['year'],fold=c['fold'],features=cols,expected_keys=te.select('row_id','horizon').iter_rows())
        def profile(g):return g.with_columns((pl.col('role_mlb_0')<3).alias('brief_appearance'),
            (pl.col('games_mlb_0')>=100).alias('frequent_mlb'),(pl.col('games_minor_0')>=90).alias('frequent_minor'))
        keys=['stage','prior_debut','brief_appearance','frequent_mlb','frequent_minor']
        counts=profile(tr).group_by(keys).agg(pl.col('player_id').n_unique().alias('role_profile_players'))
        profiles.append(profile(te).select('row_id',*keys).join(counts,on=keys,how='left',validate='m:1').with_columns(pl.col('role_profile_players').fill_null(0)))
        cells.append(dict(**c,games_preflight=note))
    pl.concat(profiles).write_parquet(OUT/'role-support.parquet')
    paths=[OUT/'source-audit.json',OUT/'source-review.json',OUT/'source-walkthrough.md',OUT/'features.parquet',OUT/'role-support.parquet',
        old.OUT/'preflight.json',old.OUT/'predictions.parquet',old.OUT/'report.json',Path(__file__),Path(s.__file__),
        s.r.ROOT/'docs/practical-hitter-v38-contract.md']
    write('preflight.json',dict(before_fitting=True,features=cols,old_features=prior['features'],added_features=audit['new_features'],cells=cells,
        input_hashes={str(p):sha256_file(p) for p in paths},evaluation_rows=30506,batting_head_fixed=True,protected_outcomes_used=False))
    print('35 actual folds audited before fitting; 239 PA inputs, unchanged batting head.',flush=True)


def fit():
    pre=s.r.read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    f=pl.read_parquet(OUT/'features.parquet');base=pl.read_parquet(old.OUT/'predictions.parquet');cols=pre['features'];frames=[];fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];path=OUT/f'forecast-{y}-{k}.parquet'
            if path.exists():
                n=s.r.read(OUT/f'fit-{y}-{k}.json');assert sha256_file(path)==n['prediction_sha256'];assert sha256_file(Path(n['path']))==n['sha256']
                frames.append(pl.read_parquet(path));fits.append(n);continue
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id');te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q=base.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');assert te['row_id'].equals(q['row_id'])
            model=tree();model.fit(tr.select(cols).to_numpy(),tr['next_pa'].to_numpy(),sample_weight=weights(tr))
            artifact=OUT/f'games-pa-{y}-{k}.joblib';joblib.dump(model,artifact,compress=3)
            raw=model.predict(te.select(cols).to_numpy());assert np.isfinite(raw).all()
            pred=np.clip(raw,0,800);pred[te['hard_unavailable'].to_numpy()]=0
            q=q.with_columns(pl.Series('games_pa',pred),pl.col('cohort_rate').alias('games_rate')).with_columns(
                (pl.col('games_pa')*(pl.col('games_rate')/600+pl.col('origin_replacement_rate'))).alias('games_value'))
            q.write_parquet(path)
            n=dict(path=str(artifact),sha256=sha256_file(artifact),prediction_sha256=sha256_file(path),features=cols,
                training_rows=len(tr),training_players=tr['player_id'].n_unique(),maximum_target_year=int(tr['target_year'].max()),
                clipped_rows=int(((raw<0)|(raw>800)).sum()),hard_unavailable_rows=int(te['hard_unavailable'].sum()))
            write(f'fit-{y}-{k}.json',n);fits.append(n);frames.append(q);print(f'{y}/{k}: {len(q)} forecasts',flush=True)
    q=pl.concat(frames).sort('row_id');assert q.select(base.columns).equals(base.sort('row_id'))
    q.write_parquet(OUT/'predictions.parquet');write('fits.json',fits)
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    write('fit-report.json',dict(new_heads=len(fits),rows=len(q),fixed_batting_head=True,player_walkthrough_status='pending',protected_outcomes_used=False))


if __name__=='__main__':
    import sys
    prepare() if '--prepare' in sys.argv else fit()
