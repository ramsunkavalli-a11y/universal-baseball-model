"""One fixed representation comparison with preflight/source checks before fits."""
from pathlib import Path
import json
import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits
import evaluate_hitter_2020_extension as old
import prepare_practical_hitter_v33 as s
from fit_practical_hitter_v31 import tree,weights
from universal_baseball.forecast_validation import preflight
from universal_baseball.shared_hitting_evidence import materialize
from universal_baseball.storage import sha256_file

OUT=old.r.ROOT/'reports/generated/practical-hitter-v35'


def write(n,o):(OUT/n).write_text(json.dumps(o,indent=2,allow_nan=False,default=str),encoding='utf8')


def prepare():
    assert old.r.read(old.OUT/'report.json')['player_walkthrough_status']=='complete'
    assert not (OUT/'preflight.json').exists()
    OUT.mkdir(parents=True,exist_ok=True)
    source=pl.read_parquet(old.SOURCE/'features.parquet');counts=pl.read_parquet(old.r.OUT/'counts.parquet')
    f=materialize(source,counts,old.r.BUCKETS);f.write_parquet(OUT/'features.parquet')
    previous=old.r.read(old.OUT/'preflight.json');features=previous['features'];cells=[]
    assert np.isfinite(s.safe_matrix(f,features)).all()
    for c in previous['cells']:
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']));te=f.filter(pl.col('row_id').is_in(c['test_row_ids']))
        _,note=preflight(tr,te,cutoff=c['year'],fold=c['fold'],features=features,expected_keys=te.select('row_id','horizon').iter_rows())
        assert tr['target_year'].max()<=c['year'] and (tr['target_year']!=2020).all()
        cells.append(dict(**c,representation_preflight=note))
    # Same identities/context means all/active support counts remain identical.
    support=pl.read_parquet(old.OUT/'support.parquet');support.write_parquet(OUT/'support.parquet')
    fixed=[(643446,2018),(668715,2022),(691026,2023),(701762,2024),(621566,2022),
        (592450,2024),(666158,2023),(680574,2024),(665487,2022)]
    traces=[]
    for pid,y in fixed:
        a=source.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y));b=f.filter(pl.col('row_id').is_in(a['row_id']))
        assert len(a)==len(b)==1
        o=a.to_dicts()[0];n=b.to_dicts()[0]
        traces.append(dict(player_id=pid,player_name=o['player_name'],origin_year=y,
            history=counts.filter((pl.col('player_id')==pid)&pl.col('season').is_between(y-2,y)).to_dicts(),
            transformation={c:dict(old=o[c],new=n[c]) for c in features if o[c]!=n[c]}))
    write('before-fit-source-traces.json',traces)
    paths=[OUT/'features.parquet',OUT/'support.parquet',OUT/'before-fit-source-traces.json',old.OUT/'predictions.parquet',old.OUT/'report.json',
        old.r.OUT/'counts.parquet',Path(__file__),old.r.ROOT/'src/universal_baseball/shared_hitting_evidence.py',old.r.ROOT/'docs/practical-hitter-v35-contract.md']
    write('preflight.json',dict(before_fitting=True,features=features,cells=cells,input_hashes={str(p):sha256_file(p) for p in paths},
        unchanged_eval_rows=30506,all_active_support_unchanged=True,protected_outcomes_used=False))
    print('Shared-count transforms, nine pre-fit source traces and 35 preflights complete.',flush=True)


def fit():
    pre=old.r.read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    f=pl.read_parquet(OUT/'features.parquet');base=pl.read_parquet(old.OUT/'predictions.parquet');frames=[];fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];path=OUT/f'forecast-{y}-{k}.parquet'
            if path.exists():
                notes=old.r.read(OUT/f'fits-{y}-{k}.json');assert sha256_file(path)==notes['prediction_sha256']
                for n in notes['models']:assert sha256_file(Path(n['path']))==n['sha256']
                frames.append(pl.read_parquet(path));fits.extend(notes['models']);continue
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q=base.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');cols=pre['features'];notes=[]
            for metric in ['pa','rate']:
                sub=tr.filter(pl.col('next_pa')>0) if metric=='rate' else tr;w=weights(sub)
                if metric=='rate':w*=sub['next_pa'].to_numpy();w*=len(w)/w.sum()
                model=Ridge(alpha=100) if metric=='rate' else tree()
                model.fit(s.safe_matrix(sub,cols) if metric=='rate' else sub.select(cols).to_numpy(),
                    sub['next_batting_rate' if metric=='rate' else 'next_pa'].to_numpy(),sample_weight=w)
                artifact=OUT/f'shared-{metric}-{y}-{k}.joblib';joblib.dump(model,artifact,compress=3)
                pred=model.predict(s.safe_matrix(te,cols) if metric=='rate' else te.select(cols).to_numpy());assert np.isfinite(pred).all()
                if metric=='pa':pred=np.clip(pred,0,800);pred[te['hard_unavailable'].to_numpy()]=0
                q=q.with_columns(pl.Series('shared_'+metric,pred))
                notes.append(dict(metric=metric,path=str(artifact),sha256=sha256_file(artifact),features=cols,
                    training_rows=len(sub),training_players=sub['player_id'].n_unique(),maximum_target_year=int(sub['target_year'].max())))
            q=q.with_columns(
                (pl.col('shared_pa')*(pl.col('shared_rate')/600+pl.col('origin_replacement_rate'))).alias('shared_value'),
                pl.col('cohort_pa').alias('rate_only_pa'),pl.col('shared_rate').alias('rate_only_rate'),
                (pl.col('cohort_pa')*(pl.col('shared_rate')/600+pl.col('origin_replacement_rate'))).alias('rate_only_value'),
                pl.col('shared_pa').alias('pa_only_pa'),pl.col('cohort_rate').alias('pa_only_rate'),
                (pl.col('shared_pa')*(pl.col('cohort_rate')/600+pl.col('origin_replacement_rate'))).alias('pa_only_value'))
            q.write_parquet(path);write(f'fits-{y}-{k}.json',dict(models=notes,prediction_sha256=sha256_file(path)))
            frames.append(q);fits.extend(notes);print(f'{y}/{k}: 2 heads, {len(q)} unchanged forecasts',flush=True)
    out=pl.concat(frames).sort('row_id');assert out.select(base.columns).equals(base.sort('row_id'))
    out.write_parquet(OUT/'predictions.parquet');write('fits.json',fits)
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    write('fit-report.json',dict(new_heads=len(fits),rows=len(out),player_walkthrough_status='pending',protected_outcomes_used=False))


if __name__=='__main__':
    import sys
    prepare() if '--prepare' in sys.argv else fit()
