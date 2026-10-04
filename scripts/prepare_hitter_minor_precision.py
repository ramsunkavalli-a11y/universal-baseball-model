"""Freeze contact noise and outer-fold support before additive forecast fits."""
from pathlib import Path
import json
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.hitter_minor_precision import moments, materialize, names
from universal_baseball.hitter_minor_statcast_forecast import route, LEAGUES
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
import prepare_hitter_minor_statcast_next_year as old

ROOT=old.ROOT;OUT=ROOT/'reports/generated/hitter-minor-statcast-precision'
CONTRACT=ROOT/'docs/hitter-minor-statcast-precision-contract.md'
read=old.read


def write(name,value):
    p=OUT/name;assert not p.exists(),f'Preserve {p}'
    p.write_text(json.dumps(value,indent=2,allow_nan=False,default=str)+'\n',encoding='utf8',newline='\n')


def baseline(f,c):
    y,k=c['year'],c['fold'];models=[]
    path=old.BRIDGE/f'translated_ridge-{y}-{k}.joblib'
    models.append((f['prior_debut'].to_numpy()==0,path,read(old.BRIDGE/'preflight.json')['features']['translated_ridge']))
    path=old.mlb.OUT/f'ridge_measurements-{y}-{k}.joblib'
    models.append(((f['prior_debut'].to_numpy()==1)&f['sc_tracked'].to_numpy(),path,read(old.mlb.OUT/'preflight.json')['arms']['ridge_measurements']))
    current=ROOT/'reports/generated/practical-hitter-numeric-repair-v53'
    h=next(h for h in read(current/f'fit-{y}-{k}.json')['heads'] if h['head']=='rate')
    models.append(((f['prior_debut'].to_numpy()==1)&~f['sc_tracked'].to_numpy(),Path(h['path']),read(current/'preflight.json')['rate_features']))
    pred=np.zeros(len(f));mapping=[]
    assert np.all(sum(mask.astype(int) for mask,_,_ in models)==1)
    for mask,path,cols in models:
        if mask.any():pred[mask]=joblib.load(path).predict(safe_matrix(f.filter(pl.Series(mask)),cols))
        mapping.append(dict(path=str(path),sha256=sha256_file(path),features=cols,rows=int(mask.sum())))
    return pred,mapping


def routed(f,c):
    tr,te,context,disabled=route(f,c['training_row_ids'],c['test_row_ids'],20)
    assert context==c['league_context'] and disabled==c['disabled_features']
    control,values=names()
    off=[n for n in control+values if any(n.startswith(f'msp_{r["league_id"]}_') for r in context if not r['enabled'])]
    if off:
        tr=tr.with_columns([pl.lit(0.).alias(n) for n in off]);te=te.with_columns([pl.lit(0.).alias(n) for n in off])
    return tr,te,off


def main():
    assert not OUT.exists(),'Preserve preparation; inspect partial artifacts instead of restarting'
    final=read(old.OUT/'final-review.json');assert final['player_walkthrough_status']=='complete'
    old.verify_hashes(final['artifact_hashes'])
    OUT.mkdir(parents=True)
    a=moments(pl.read_parquet(old.OUT/'annual-launch-features.parquet'),
        [pl.read_parquet(old.SOURCE/f'launch-events-{y}.parquet') for y in range(2021,2025)])
    a.write_parquet(OUT/'annual-contact-noise.parquet')
    print('All',len(a),'annual measurement counts/means independently match source; bootstrap noise saved.',flush=True)
    oldpre=read(old.OUT/'preflight.json');control,values=names();arms=dict(precision_coverage=control,precision_measurements=control+values)
    supports=[];cells=[];ranges=[];paths=[CONTRACT,Path(__file__),ROOT/'src/universal_baseball/hitter_minor_precision.py',
        ROOT/'tests/test_hitter_minor_precision.py',ROOT/'scripts/fit_hitter_minor_precision.py',old.OUT/'final-review.json',
        old.OUT/'preflight.json',old.OUT/'scored-predictions.parquet',OUT/'annual-contact-noise.parquet']
    anchor=pl.read_parquet(old.OUT/'scored-predictions.parquet').sort('row_id');anchor.write_parquet(OUT/'anchor.parquet');paths.append(OUT/'anchor.parquet')
    with threadpool_limits(limits=2):
        for k in range(5):
            f,refs=materialize(pl.read_parquet(old.OUT/f'features-{k}.parquet'),a,k)
            f.write_parquet(OUT/f'features-{k}.parquet');write(f'noise-reference-{k}.json',dict(held_fold=k,references=refs,future_outcomes_used=False))
            paths += [OUT/f'features-{k}.parquet',OUT/f'noise-reference-{k}.json',old.OUT/f'features-{k}.parquet']
            for c in [c for c in oldpre['cells'] if c['fold']==k]:
                tr,te,off=routed(f,c)
                support,note=preflight(tr,te,cutoff=c['year'],fold=k,features=arms['precision_measurements'],expected_keys=te.select('row_id','horizon').iter_rows())
                supports.append(support.with_columns(pl.lit(c['year']).alias('msc_origin'),pl.lit(k).alias('msc_fold')))
                base_tr,mapping=baseline(tr,c);base_te,_=baseline(te,c)
                got=anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                assert np.allclose(base_te,got['combined_rate'],atol=1e-10,rtol=0)
                p=OUT/f'base-{c["year"]}-{k}.parquet'
                pl.concat([tr.select('row_id').with_columns(pl.Series('base_rate',base_tr),pl.lit('train').alias('split')),
                    te.select('row_id').with_columns(pl.Series('base_rate',base_te),pl.lit('test').alias('split'))]).write_parquet(p)
                paths.append(p);paths += [Path(m['path']) for m in mapping]
                for n in control+values:
                    ranges.append(dict(year=c['year'],fold=k,feature=n,min_train=float(tr[n].min()),max_train=float(tr[n].max()),
                        outside=int(((te[n]<tr[n].min())|(te[n]>tr[n].max())).sum())))
                cells.append(dict(**c,precision_preflight=note,precision_disabled_features=off,baseline_heads=mapping,baseline_path=str(p)))
            print('Fold',k,'noise references, actual base-head replays and all preflights sealed.',flush=True)
    pl.concat(supports).write_parquet(OUT/'support.parquet');write('ranges.json',dict(ranges=ranges))
    paths += [OUT/'support.parquet',OUT/'ranges.json',old.OUT/'profile-support.parquet']
    write('preflight.json',dict(cells=cells,arms=arms,ridge_alpha=10.,fit_intercept=False,source_rows=63282,forecasts=30506,
        before_fitting=True,baseline_test_replays=35,full_profile_validation=False,old_profile_support_path=str(old.OUT/'profile-support.parquet'),
        bootstrap_replicates=128,training_residuals_cross_fitted=False,deployment_approved=False,
        input_hashes={str(p):sha256_file(p) for p in set(paths)}))
    print('Preparation complete; no new adjustment fitted.',flush=True)


if __name__=='__main__':main()
