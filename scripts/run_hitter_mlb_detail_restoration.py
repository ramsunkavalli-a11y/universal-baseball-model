"""One four-input restoration, source audit and preflight before fixed fits."""
import argparse
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.hitter_mlb_detail import DETAIL, reconstruct
from universal_baseball.hitter_past_direct_value import fit
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file
from prepare_hitter_overseas_integration import annual_labels
from fit_practical_hitter_v31 import weights
from run_hitter_count_baseline import ROOT, GEN, OUT as COUNT, read, verify, matrix, tagged
from run_hitter_past_direct_value import OUT as DIRECT, save as old_save, past_rate
import json

OUT=GEN/'hitter-mlb-detail-restoration'


def save(name,obj):
    p=OUT/name; assert not p.exists(),f'Preserve {p}'
    p.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n',encoding='utf8',newline='\n')


def profiles(f):
    return tagged(f).with_columns(pl.when(pl.col('pa_0')==0).then(pl.lit('no_MLB'))
        .when(pl.col('quality_0')<-.5).then(pl.lit('under_minus_half')).when(pl.col('quality_0')>.5).then(pl.lit('over_half')).otherwise(pl.lit('middle')).alias('MLB_quality_group'))


def prepare():
    assert not OUT.exists()
    final=read(DIRECT/'final-review.json'); verify(final['hashes']); assert final['player_walkthrough_status']=='complete'
    previous=read(DIRECT/'preflight.json'); verify(previous['source_hashes'])
    for c in read(DIRECT/'fit-report.json')['cells']: verify(c['hashes'])
    counts,env=annual_labels(pl.read_parquet(GEN/'practical-hitter-v31/dated-stints.parquet'))
    f0=pl.read_parquet(COUNT/'features-0.parquet').sort('row_id'); raw=[]; notes={}
    fixed={c['row_id'] for c in read(DIRECT/'player-walks.json')['cases']}; assert len(fixed)==16
    for r in f0.iter_rows(named=True):
        v,note=reconstruct(r['player_id'],r['origin_year'],counts,env)
        assert all(np.isclose(r[n],v[n],atol=1e-10,rtol=0) for n in DETAIL)
        assert all(a['PA']==r[f'pa_{lag}'] for lag,a in enumerate(note['seasons']))
        raw.append(dict(row_id=r['row_id'],**v))
        if r['row_id'] in fixed:
            y=r['origin_year']; mutated=dict(counts); mutated_env=dict(env)
            for future in [y+1,y+2]:
                mutated[(future,r['player_id'])]=np.arange(8,dtype=float)*999+99
                mutated_env[future]=np.ones(8)/8
            assert reconstruct(r['player_id'],y,mutated,mutated_env)==(v,note)
            notes[r['row_id']]=dict(row_id=r['row_id'],player_name=r['player_name'],origin_year=y,features=v,source=note,future_mutation_unchanged=True)
    OUT.mkdir(parents=True)
    reconstructed=pl.DataFrame(raw).sort('row_id')
    paths=[Path(__file__),ROOT/'docs/hitter-mlb-detail-restoration-contract.md',ROOT/'src/universal_baseball/hitter_mlb_detail.py',ROOT/'tests/test_hitter_mlb_detail.py',
           DIRECT/'final-review.json',DIRECT/'preflight.json',DIRECT/'predictions.parquet',DIRECT/'player-walks.json',COUNT/'profile-support.parquet',
           GEN/'practical-hitter-v31/dated-stints.parquet',ROOT/'src/universal_baseball/hitter_past_direct_value.py',ROOT/'scripts/run_hitter_past_direct_value.py',
           ROOT/'scripts/run_hitter_count_baseline.py',ROOT/'scripts/prepare_hitter_overseas_integration.py',ROOT/'scripts/prepare_practical_hitter_v33.py',ROOT/'scripts/fit_practical_hitter_v31.py',ROOT/'src/universal_baseball/forecast_validation.py']
    arms={arm:names+DETAIL for arm,names in previous['arms'].items()}
    assert {k:len(v) for k,v in arms.items()}==dict(base=116,prospect=125,tracking=179)
    checks=[]; support=[]; ranges=[]
    keys=['prior_debut','stage','age_group','mlb_exposure','MLB_quality_group','has_NPB','has_KBO','scout_high']
    for k in range(5):
        path=COUNT/f'features-{k}.parquet';paths.append(path);f=pl.read_parquet(path).sort('row_id')
        assert f.select('row_id',*DETAIL).equals(f0.select('row_id',*DETAIL))
        assert np.allclose(f.select(DETAIL).to_numpy(),reconstructed.select(DETAIL).to_numpy(),atol=1e-10,rtol=0)
        for c in [c for c in previous['cells'] if c['fold']==k]:
            full=f.filter(pl.col('row_id').is_in(c['training_row_ids'])); tr=full.filter(pl.col('next_pa')>0).sort('row_id'); te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert tr['target_year'].max()<=c['year'] and 2020 not in tr['target_year']
            for arm,names in arms.items():
                check,n=preflight(tr,te,cutoff=c['year'],fold=k,features=names,expected_keys=te.select('row_id','horizon').iter_rows())
                assert np.isfinite(matrix(tr,names)).all() and np.isfinite(matrix(te,names)).all()
                checks.append(dict(origin=c['year'],fold=k,arm=arm,note=n))
                for name in DETAIL:
                    lo,hi=float(tr[name].min()),float(tr[name].max()); outside=(te[name]<lo)|(te[name]>hi)
                    if outside.any(): ranges.append(dict(origin=c['year'],fold=k,arm=arm,feature=name,minimum=lo,maximum=hi,row_ids=te.filter(pl.Series(outside))['row_id'].to_list()))
            for subset,g in [('full',full),('active',tr)]:
                cnt=profiles(g).group_by(keys).agg(pl.col('player_id').n_unique().alias('people'))
                s=profiles(te).select('row_id',*keys).join(cnt,on=keys,how='left',validate='m:1').with_columns(pl.col('people').fill_null(0),pl.lit(subset).alias('subset'),pl.lit(c['year']).alias('origin'),pl.lit(k).alias('fold'))
                support.append(s)
        print(f'Reconstructed four source fields and checked extended feature lists, fold {k}.',flush=True)
    assert len(checks)==105
    pl.concat(support).write_parquet(OUT/'profile-support.parquet');save('feature-ranges.json',ranges)
    save('source-walks.json',list(notes.values()))
    save('source-audit.json',dict(source_rows=f0.height,matrices_checked=5,reconstructed_column_checks=f0.height*4*5,maximum_tolerance=1e-10,
         source_walks=len(notes),future_mutation_cases=len(notes),source_years=[2009,2024],legacy_values_preserved=True,source_walkthrough_status='pending_readable_review',protected_outcomes_used=False))
    paths += [OUT/'profile-support.parquet',OUT/'feature-ranges.json',OUT/'source-walks.json',OUT/'source-audit.json']
    save('preflight.json',dict(before_fitting=True,checks_before_fits=len(checks),checks=checks,arms=arms,cells=previous['cells'],fixed_case_row_ids=sorted(fixed),
         alpha=100,source_hashes={str(p):sha256_file(p) for p in paths},protected_outcomes_used=False,deployment_approved=False))


def certify():
    pre=read(OUT/'preflight.json');verify(pre['source_hashes'])
    doc=ROOT/'docs/hitter-mlb-detail-restoration-source-review.md';assert doc.exists()
    assert read(OUT/'source-audit.json')['source_walks']==16
    save('source-review.json',dict(approved_for_fixed_fit=True,source_walkthrough_status='complete',
         hashes={str(p):sha256_file(p) for p in [Path(__file__),doc,OUT/'preflight.json',OUT/'source-walks.json',OUT/'source-audit.json']},deployment_approved=False,protected_outcomes_used=False))


def run_fit():
    pre=read(OUT/'preflight.json');verify(pre['source_hashes']);cert=read(OUT/'source-review.json');verify(cert['hashes'])
    assert cert['approved_for_fixed_fit'] and pre['checks_before_fits']==105 and not (OUT/'fit-report.json').exists()
    seal=dict(runner_sha256=sha256_file(Path(__file__)),preflight_sha256=sha256_file(OUT/'preflight.json'),source_review_sha256=sha256_file(OUT/'source-review.json'))
    if (OUT/'fit-seal.json').exists():assert read(OUT/'fit-seal.json')==seal
    else:save('fit-seal.json',seal)
    previous=pl.read_parquet(DIRECT/'predictions.parquet').sort('row_id');forecasts=[];receipts=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];path=OUT/f'forecast-{y}-{k}.parquet'
            if path.exists():
                note=read(OUT/f'fit-{y}-{k}.json');verify(note['hashes']);receipts.append(note);forecasts.append(pl.read_parquet(path));continue
            f=pl.read_parquet(COUNT/f'features-{k}.parquet');tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])&(pl.col('next_pa')>0)).sort('row_id');te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            q=previous.filter(pl.col('row_id').is_in(te['row_id'].to_list())).sort('row_id');assert q['row_id'].equals(te['row_id'])
            train_base,test_base=past_rate(tr,True),past_rate(te);candidate={};heads=[];hashes={}
            assert np.allclose(test_base,q['scalar_baseline_rate'],atol=1e-10)
            for arm,names in pre['arms'].items():
                m=fit(matrix(tr,names),tr['actual_relative_rate'].to_numpy(),train_base,weights(tr)*tr['next_pa'].to_numpy())
                p=OUT/f'{arm}-rate-{y}-{k}.joblib';assert not p.exists();joblib.dump(m,p,compress=3);hashes[str(p)]=sha256_file(p)
                candidate[arm]=test_base+m.predict(matrix(te,names));heads.append(dict(arm=arm,path=str(p),features=names,training_rows=tr.height,training_people=tr['player_id'].n_unique(),maximum_target_year=int(tr['target_year'].max()),alpha=100))
            rate=np.where(te['prior_debut'].to_numpy()==0,candidate['prospect'],np.where(te['sc_tracked'].to_numpy(),candidate['tracking'],candidate['base']));pa=q['scalar_pa'].to_numpy()
            q=q.with_columns(pl.Series('restored_rate',rate),pl.Series('restored_pa',pa),pl.Series('restored_value',pa*(rate/600+q['origin_replacement_rate'].to_numpy())))
            assert np.isfinite(q.select('restored_rate','restored_value').to_numpy()).all()
            q.write_parquet(path);hashes[str(path)]=sha256_file(path);note=dict(origin=y,fold=k,heads=heads,hashes=hashes)
            save(f'fit-{y}-{k}.json',note);receipts.append(note);forecasts.append(q);print(f'Fitted one matched restoration {y}/{k}.',flush=True)
    q=pl.concat(forecasts).sort('row_id');assert q.height==30519 and q.select(previous.columns).equals(previous) and q['restored_pa'].equals(q['scalar_pa'])
    q.write_parquet(OUT/'predictions.parquet');save('fit-report.json',dict(new_heads=105,cells=receipts,rows=q.height,predictions_sha256=sha256_file(OUT/'predictions.parquet'),player_walkthrough_status='pending',deployment_approved=False,protected_outcomes_used=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','certify','fit']);a=p.parse_args();{'prepare':prepare,'certify':certify,'fit':run_fit}[a.phase]()
