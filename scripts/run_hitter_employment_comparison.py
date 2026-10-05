"""Prepare all matched checks, then fit only corrected opportunity heads."""
import argparse
from pathlib import Path
import json
import subprocess
import sys
import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from universal_baseball.employment_comparison import FLAGS, corrected_frame, support
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights

ROOT=Path(__file__).resolve().parents[1]
GEN=ROOT/'reports/generated'
OLD=GEN/'hitter-evidence-representation'
OUT=GEN/'hitter-employment-comparison'
FIX=GEN/'hitter-employment-v3'


def read(p): return json.loads(Path(p).read_text(encoding='utf8'))


def save(name, value):
    p=OUT/name
    if p.exists(): raise ValueError('Preserve existing execution: '+name)
    p.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')


def verify(hashes):
    for name,h in hashes.items():
        p=Path(name)
        if not p.is_absolute(): p=ROOT/p
        if sha256_file(p)!=h: raise ValueError('Changed sealed artifact: '+name)


def prepare():
    if OUT.exists(): raise ValueError('Inspect existing preparation; do not restart')
    review=read(FIX/'final-review.json')
    assert review['source_review_status']=='complete' and review['player_walkthrough_status']=='complete'
    verify(review['hashes']); verify(read(FIX/'source-seal.json')['hashes'])
    verify(read(FIX/'execution-recovery.json')['hashes'])
    oldreview=read(OLD/'final-review.json'); assert oldreview['player_walkthrough_status']=='complete'
    verify(oldreview['hashes'])
    pre=read(OLD/'preflight.json'); verify(pre['source_hashes'])
    fit=read(OLD/'fit-report.json')
    for cell in fit['cells']: verify(cell['hashes'])
    assert sha256_file(OLD/'predictions.parquet')==fit['predictions_sha256']
    test=subprocess.run([sys.executable,'-m','pytest','-q','-p','no:cacheprovider',
        'tests/test_employment_comparison.py'],cwd=ROOT,capture_output=True,text=True)
    if test.returncode: raise ValueError(test.stdout+test.stderr)
    q=pl.read_parquet(OLD/'predictions.parquet').sort('row_id')
    assert q.height==30519 and q['row_id'].n_unique()==30519 and q['target_year'].max()==2025
    indicator=pl.read_parquet(FIX/'employment-indicators.parquet')
    previous=read(GEN/'hitter-status-evidence-v2/status-ledger.json')['rows']
    oldstatus=pl.DataFrame([dict(player_id=r['player_id'],origin_year=r['origin_year'],
        **{n:r[n] for n in FLAGS}) for r in previous]); del previous
    paths=[Path(__file__),ROOT/'docs/hitter-employment-comparison-contract.md',
        ROOT/'src/universal_baseball/employment_comparison.py',ROOT/'tests/test_employment_comparison.py',
        ROOT/'src/universal_baseball/forecast_validation.py',ROOT/'scripts/fit_practical_hitter_v31.py',
        FIX/'final-review.json',FIX/'source-seal.json',FIX/'execution-recovery.json',
        FIX/'employment-indicators.parquet',OLD/'preflight.json',OLD/'fit-report.json',
        OLD/'predictions.parquet',OLD/'final-review.json',GEN/'hitter-status-evidence-v2/status-ledger.json',
        GEN/'foreign-origin-inputs/origin-inputs.json',GEN/'practical-hitter-v31/dated-stints.parquet',
        GEN/'overseas-opportunity-inventory/inventory.json']
    paths += [OLD/f'features-{k}.parquet' for k in range(5)]
    paths += [Path(h['path']) for c in fit['cells'] for h in c['heads'] if h['arm']=='common']
    OUT.mkdir()
    save('source-seal.json',dict(before_fitting=True,hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in paths}))
    frames={}; sourcechanges=[]
    for k in range(5):
        f=pl.read_parquet(OLD/f'features-{k}.parquet').sort('row_id')
        join=f.select('row_id','origin_year','player_id',*FLAGS).join(oldstatus,
            on=['origin_year','player_id'],how='left',suffix='_source',validate='1:1')
        for n in FLAGS: assert (join[n]==join[n+'_source']).all(),n
        n=corrected_frame(f,indicator)
        assert n.height==63314
        n.write_parquet(OUT/f'features-{k}.parquet'); paths.append(OUT/f'features-{k}.parquet')
        frames[k]=n
        if k==0:
            changes=np.any(f.select(FLAGS+['signed_first_team_work']).to_numpy()!=n.select(FLAGS+['signed_first_team_work']).to_numpy(),axis=1)
            sourcechanges=f.select('row_id').with_columns(pl.Series('employment_input_changed',changes))
        print(json.dumps(dict(prepared_fold=k,source_rows=n.height)),flush=True)
    checks=[]; profileparts=[]; ranges=[]
    # Every old/corrected, full/active subset is checked before any new fit.
    for c in pre['cells']:
        y,k=c['year'],c['fold']; old=pl.read_parquet(OLD/f'features-{k}.parquet'); new=frames[k]
        for arm,f in [('old_job',old),('corrected_job',new)]:
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert tr['ctx_information_date'].max()<te['ctx_information_date'].min()
            assert te['row_id'].equals(q.filter((pl.col('origin_year')==y)&(pl.col('outer_fold')==k)).sort('row_id')['row_id'])
            for head,sub in [('participation',tr),('conditional_pa',tr.filter(pl.col('next_pa')>0))]:
                base,note=preflight(sub,te,cutoff=y,fold=k,features=pre['job_features'],
                    expected_keys=te.select('row_id','horizon').iter_rows())
                detail=support(sub,te).join(base.select('row_id','extrapolation','sparse_profile'),on='row_id',validate='1:1')
                detail=detail.with_columns(pl.lit(arm).alias('arm'),pl.lit(head).alias('head'),
                    pl.lit(y).alias('origin'),pl.lit(k).alias('fold'))
                profileparts.append(detail)
                checks.append(dict(arm=arm,head=head,origin=y,fold=k,**note,
                    exact_profile_zero=int((detail['profile_people']==0).sum()),
                    exact_profile_under20=int((detail['profile_people']<20).sum())))
                lower=sub.select(pre['job_features']).to_numpy().min(axis=0)
                upper=sub.select(pre['job_features']).to_numpy().max(axis=0)
                outside=((te.select(pre['job_features']).to_numpy()<lower)|
                         (te.select(pre['job_features']).to_numpy()>upper)).sum(axis=0)
                ranges.extend(dict(arm=arm,head=head,origin=y,fold=k,feature=n,
                    minimum=float(lo),maximum=float(hi),test_outside=int(count))
                    for n,lo,hi,count in zip(pre['job_features'],lower,upper,outside,strict=True))
    assert len(checks)==140
    pl.concat(profileparts).write_parquet(OUT/'profile-support.parquet')
    save('feature-ranges.json',dict(rows=ranges))
    # Whole baseline replay, not a surrogate or refitted old model.
    replayed=0
    with threadpool_limits(limits=2):
        for c in fit['cells']:
            y,k=c['origin'],c['fold']; old=pl.read_parquet(OLD/f'features-{k}.parquet')
            g=q.filter((pl.col('origin_year')==y)&(pl.col('outer_fold')==k)).sort('row_id')
            te=old.filter(pl.col('row_id').is_in(g['row_id'])).sort('row_id')
            for h in [h for h in c['heads'] if h['arm']=='common']:
                assert h['features']==pre['job_features']
                m=joblib.load(h['path']); assert m.get_params()==(HistGradientBoostingClassifier if h['head']=='participation' else HistGradientBoostingRegressor)(**pre['settings']).get_params()
                x=te.select(h['features']).to_numpy()
                pred=m.predict_proba(x)[:,1] if h['head']=='participation' else m.predict(x)
                suffix='raw_p' if h['head']=='participation' else 'raw_conditional_pa'
                assert np.allclose(pred,g['repaired_domestic_'+suffix],atol=1e-10,rtol=0)
                replayed+=1
    assert replayed==70
    sourcechanges.write_parquet(OUT/'source-changes.parquet')
    save('preflight.json',dict(before_fitting=True,new_fits=0,checks=checks,cells=pre['cells'],
        job_features=pre['job_features'],settings=pre['settings'],baseline_heads_replayed=70,
        source_rows=63314,original_rows=30506,addition_rows=13,allowed_changes=FLAGS+['signed_first_team_work'],
        target_year_maximum=2025,player_walkthrough_status='pending',deployment_approved=False,
        hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in paths+[OUT/'profile-support.parquet',
            OUT/'feature-ranges.json',OUT/'source-changes.parquet',OUT/'source-seal.json']}))
    verify(read(OUT/'source-seal.json')['hashes'])
    print(json.dumps(dict(preflight='complete',checks=140,baseline_replayed=70,new_fits=0)),flush=True)


def fit():
    pre=read(OUT/'preflight.json'); verify(pre['hashes']); assert len(pre['checks'])==140
    if (OUT/'fit-report.json').exists(): raise ValueError('Completed test; do not repeat')
    if list(OUT.glob('corrected-*.joblib')) or list(OUT.glob('forecast-*.parquet')):
        raise ValueError('Inspect interrupted fit explicitly; never silently restart')
    save('fit-seal.json',dict(before_fitting=True,preflight_sha256=sha256_file(OUT/'preflight.json'),
                             runner_sha256=sha256_file(Path(__file__))))
    q=pl.read_parquet(OLD/'predictions.parquet').sort('row_id')
    forecasts=[]; receipts=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold']; f=pl.read_parquet(OUT/f'features-{k}.parquet')
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            g=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert g['row_id'].equals(te['row_id'])
            heads=[]; preds={}
            for head,sub,cls,target in [('participation',tr,HistGradientBoostingClassifier,'next_active'),
                ('conditional_pa',tr.filter(pl.col('next_pa')>0),HistGradientBoostingRegressor,'next_pa')]:
                m=cls(**pre['settings']);names=pre['job_features']
                m.fit(sub.select(names).to_numpy(),sub[target].to_numpy(),sample_weight=weights(sub))
                path=OUT/f'corrected-{head}-{y}-{k}.joblib';joblib.dump(m,path,compress=3)
                note=dict(head=head,path=str(path.relative_to(ROOT)),sha256=sha256_file(path),
                    origin=y,fold=k,training_rows=sub.height,training_people=sub['player_id'].n_unique(),
                    maximum_training_target=int(sub['target_year'].max()),features=names)
                save(f'head-{head}-{y}-{k}.json',note);heads.append(note)
                x=te.select(names).to_numpy();preds[head]=m.predict_proba(x)[:,1] if head=='participation' else m.predict(x)
            raw=preds['participation'];p=raw.copy()
            p[(te['status_hard_unavailable'].to_numpy()>0)|(te['status_retired'].to_numpy()>0)]=0
            cond=np.clip(preds['conditional_pa'],1,800);pa=p*cond
            rate=np.where(g['source_addition'].to_numpy(),g['repaired_domestic_rate'].to_numpy(),g['current_rate'].to_numpy())
            assert np.isfinite(rate).all()
            oldpa=g['repaired_domestic_pa'].to_numpy(); oldp=g['repaired_domestic_p'].to_numpy()
            g=g.with_columns(pl.Series('old_job_p',oldp),pl.Series('old_job_pa',oldpa),pl.Series('old_job_rate',rate),
                pl.Series('old_job_value',oldpa*(rate/600+g['origin_replacement_rate'].to_numpy())),
                pl.Series('corrected_job_raw_p',raw),pl.Series('corrected_job_raw_conditional_pa',preds['conditional_pa']),
                pl.Series('corrected_job_p',p),pl.Series('corrected_job_conditional_pa',cond),pl.Series('corrected_job_pa',pa),
                pl.Series('corrected_job_rate',rate),pl.Series('corrected_job_value',pa*(rate/600+g['origin_replacement_rate'].to_numpy())))
            assert np.isfinite(g.select([n for n in g.columns if n.startswith(('old_job_','corrected_job_'))]).to_numpy()).all()
            assert g.select(q.columns).equals(q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id'))
            path=OUT/f'forecast-{y}-{k}.parquet';g.write_parquet(path)
            note=dict(origin=y,fold=k,heads=heads,predictions_path=str(path.relative_to(ROOT)),
                      predictions_sha256=sha256_file(path),test_row_ids=c['test_row_ids'])
            save(f'fit-{y}-{k}.json',note);receipts.append(note);forecasts.append(g)
            print(json.dumps(dict(fitted_origin=y,fold=k,heads=2,test_rows=g.height)),flush=True)
    result=pl.concat(forecasts).sort('row_id')
    assert result.height==30519 and result.select(q.columns).equals(q)
    result=result.join(pl.read_parquet(OUT/'source-changes.parquet'),on='row_id',validate='1:1')
    result.write_parquet(OUT/'predictions.parquet')
    save('fit-report.json',dict(cells=receipts,new_heads=70,rows=30519,
        predictions_sha256=sha256_file(OUT/'predictions.parquet'),player_walkthrough_status='pending',
        deployment_approved=False,protected_outcomes_read=False))
    verify(pre['hashes'])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','fit'])
    {'prepare':prepare,'fit':fit}[parser.parse_args().phase]()
