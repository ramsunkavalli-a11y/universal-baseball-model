"""Locked smooth conditional-mean contrast, with actual-fold preflight."""
import sys
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_bounded_workload import SmoothWorkload
from universal_baseball.storage import sha256_file
import evaluate_hitter_workload_anchor_v61 as previous

ROOT=previous.ROOT;BASE=previous.BASE
SOURCE=previous.OUT
OUT=ROOT/'reports/generated/hitter-bounded-workload-v62'
ARMS=['smooth62','bounded62']
read=previous.read


def write(n,o):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/n).write_text(previous.json.dumps(o,indent=2,default=str,allow_nan=False)+'\n',encoding='utf8')


def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    assert read(SOURCE/'report.json')['player_walkthrough_status']=='complete'
    assert not(OUT/'preflight.json').exists()
    old=read(SOURCE/'preflight.json')
    for p,h in old['input_hashes'].items():assert sha256_file(previous.Path(p))==h,p
    f=pl.read_parquet(SOURCE/'features.parquet');cells=[];supports=[];ranges=[]
    assert f['next_pa'].min()>=0 and f['next_pa'].max()<=800
    for c in old['cells']:
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
        te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');names=c['features61']
        sp,note=preflight(tr,te,cutoff=c['year'],fold=c['fold'],features=names,
            expected_keys=te.select('row_id','horizon').iter_rows());supports.append(sp)
        m=SmoothWorkload(names,'logit');x=tr.select(names).to_numpy();tx=te.select(names).to_numpy();b=m.basis(x)
        active=int((np.ptp(b,axis=0)>1e-12).sum())
        for i,(n,s) in enumerate(zip(names,m.scales)):
            low=float(x[:,i].min());high=float(x[:,i].max())
            ranges.append(dict(year=c['year'],fold=c['fold'],feature=n,scale=float(s),
                training_min=low,training_max=high,
                saturated_training=int((np.abs(x[:,i])>s).sum()),
                saturated_test=int((np.abs(tx[:,i])>s).sum()),
                outside_training=int(((tx[:,i]<low)|(tx[:,i]>high)).sum())))
        cells.append(dict(**c,actual_heads62={a:note for a in ARMS},active_basis=active))
        print(f'Smooth preflight {c["year"]}/{c["fold"]}: {active} active basis terms.',flush=True)
    pl.concat(supports).write_parquet(OUT/'support.parquet')
    pl.DataFrame(ranges).write_parquet(OUT/'ranges.parquet')
    paths=[SOURCE/'features.parquet',SOURCE/'preflight.json',SOURCE/'report.json',SOURCE/'profile-support.parquet',
        BASE/'scored-predictions.parquet',previous.Path(__file__),
        ROOT/'src/universal_baseball/hitter_bounded_workload.py',ROOT/'docs/hitter-bounded-workload-v62-contract.md']
    write('preflight.json',dict(before_fitting=True,cells=cells,arms=ARMS,source_rows=len(f),
        input_hashes={str(p):sha256_file(p)for p in paths},solver_penalty=.0001,
        protected_outcomes_used=False,historical_publication_vintage_verified=False))
    print('35 cells / 70 smooth heads preflighted before fitting.',flush=True)


def fit():
    pre=read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(previous.Path(p))==h,p
    f=pl.read_parquet(SOURCE/'features.parquet');base=pl.read_parquet(BASE/'scored-predictions.parquet');fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];fp=OUT/f'forecast-{y}-{k}.parquet'
            if fp.exists():
                note=read(OUT/f'fit-{y}-{k}.json');assert sha256_file(fp)==note['prediction_sha256']
                for h in note['heads']:assert sha256_file(previous.Path(h['path']))==h['sha256']
                fits.append(note);continue
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q=base.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            assert q['row_id'].equals(te['row_id'])
            names=c['features61'];x=tr.select(names).to_numpy();tx=te.select(names).to_numpy();heads=[]
            for a,link in [('smooth62','identity'),('bounded62','logit')]:
                m=SmoothWorkload(names,link).fit(x,tr['next_pa'].to_numpy(),previous.weights(tr))
                assert m.solver['basis_active']==c['active_basis']
                raw=m.predict(tx);pa=previous.forecast(raw,q['hard_unavailable'].to_numpy()|q['reported_retired'].to_numpy())
                q=q.with_columns(pl.Series(a+'_raw_pa',raw),pl.Series(a+'_pa',pa),pl.col('repaired_rate').alias(a+'_rate'))
                q=q.with_columns((pl.col(a+'_pa')*(pl.col(a+'_rate')/600+pl.col('origin_replacement_rate'))).alias(a+'_value'))
                path=OUT/f'{a}-{y}-{k}.joblib';joblib.dump(m,path,compress=3)
                heads.append(dict(arm=a,link=link,path=str(path),sha256=sha256_file(path),features=names,
                    solver=m.solver,training_rows=len(tr),training_players=tr['player_id'].n_unique(),
                    clip_low=int((raw<0).sum()),clip_high=int((raw>800).sum())))
            q.write_parquet(fp);note=dict(year=y,fold=k,heads=heads,prediction_sha256=sha256_file(fp))
            write(f'fit-{y}-{k}.json',note);fits.append(note)
            print(f'Smooth workload {y}/{k}: saved matched heads.',flush=True)
    q=pl.concat([pl.read_parquet(OUT/f"forecast-{c['year']}-{c['fold']}.parquet")for c in pre['cells']]).sort('row_id')
    assert len(q)==30506 and q.select(base.columns).equals(base.sort('row_id'))
    q.write_parquet(OUT/'predictions.parquet');write('fits.json',fits)
    write('fit-report.json',dict(heads=70,baseline_columns_exact=True,batting_rate_exact=True,
        player_walkthrough_status='pending',protected_outcomes_used=False,frozen_forecast_changed=False))


if __name__=='__main__':{'prepare':prepare,'fit':fit}[sys.argv[1]]()
