"""Actual-fold age/level support and exact linear accounting; no new fits."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
import fit_hitter_talent_opportunity as fit

ROOT=fit.ROOT
OUT=ROOT/'reports/generated/hitter-rate-support-audit'
BUCKETS=['MLB','AAA','AA','Aplus','A','Aminus','RK120','RK121','RK124','RK128','RK134','RKother','DSL','MEX']


def tagged(f):
    x=f.select([b+'_0_pa' for b in BUCKETS]).to_numpy()
    assert np.isfinite(x).all() and (x>=0).all()
    labels=np.array(BUCKETS)[x.argmax(axis=1)].astype(object)
    labels[x.max(axis=1)==0]='absent'
    return f.with_columns(pl.Series('dominant_level',labels.tolist()),
        pl.when(pl.col('age_unknown')==1).then(pl.lit('unknown'))
        .when(pl.col('age')<=17).then(pl.lit('<=17'))
        .when(pl.col('age')<=20).then(pl.lit('18-20'))
        .when(pl.col('age')<=23).then(pl.lit('21-23'))
        .when(pl.col('age')<=27).then(pl.lit('24-27'))
        .when(pl.col('age')<=34).then(pl.lit('28-34'))
        .otherwise(pl.lit('35+')).alias('audit_age_band'))


def main():
    assert not (OUT/'report.json').exists(),'Preserve audit receipt'
    completed=fit.read(fit.OUT/'final-report.json')
    assert completed['player_walkthrough_status']=='complete'
    fit.verify(completed['source_and_execution_hashes']);fit.verify(completed['review_hashes'])
    pre=fit.read(fit.OUT/'preflight.json')
    f=tagged(pl.read_parquet(fit.setup.current.OUT/'features.parquet'))
    q=pl.read_parquet(fit.OUT/'scored-predictions.parquet').sort('row_id')
    keys=['dominant_level','audit_age_band','prior_debut'];rows=[];cells=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold']; tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])&(pl.col('next_pa')>0))
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert not set(tr['player_id'])&set(te['player_id']) and tr['target_year'].max()<=y
            counts=tr.group_by(keys).agg(pl.col('player_id').n_unique().alias('rate_profile_people'),
                pl.len().alias('rate_profile_rows'),pl.col('next_pa').sum().alias('profile_target_pa'))
            support=te.select('row_id',*keys).join(counts,on=keys,how='left',validate='m:1').with_columns(
                pl.col('rate_profile_people','rate_profile_rows','profile_target_pa').fill_null(0))
            head=next(h for h in fit.read(fit.setup.RATE/f'fit-{y}-{k}.json')['heads'] if h['head']=='rate')
            fit.verify({head['path']:head['sha256']}); m=joblib.load(head['path']);names=pre['rate_features'];x=safe_matrix(te,names)
            terms=x*m.coef_; predicted=m.intercept_+terms.sum(axis=1)
            saved=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert np.allclose(predicted,saved['baseline_rate'],rtol=0,atol=1e-10)
            age_cols=[i for i,n in enumerate(names) if n in ['age_centered','age_squared']]
            level_cols=[i for i,n in enumerate(names) if any(n.startswith((b+'_','pooled_'+b+'_')) for b in BUCKETS)]
            age=terms[:,age_cols].sum(axis=1);level=terms[:,level_cols].sum(axis=1)
            rows.append(support.with_columns(pl.Series('rate_intercept',np.repeat(m.intercept_,len(te))),
                pl.Series('age_term',age),pl.Series('level_term',level),
                pl.Series('other_term',terms.sum(axis=1)-age-level),pl.Series('replayed_rate',predicted)))
            cells.append(dict(origin=y,fold=k,training_rows=len(tr),training_people=tr['player_id'].n_unique(),
                minimum_training_age=float(tr['age'].min()),maximum_training_age=float(tr['age'].max()),
                groups=counts.sort(keys).to_dicts(),head_hash=head['sha256']))
    r=q.join(pl.concat(rows),on='row_id',how='left',validate='1:1')
    assert len(r)==30506 and r.select(q.columns).equals(q) and r['dominant_level'].null_count()==0
    OUT.mkdir(parents=True,exist_ok=True);r.write_parquet(OUT/'rows.parquet')
    low=(pl.col('dominant_level').is_in(['DSL','RK120','RK121','RK124','RK128','RK134','RKother','Aminus','A','Aplus']))&(pl.col('prior_debut')==0)
    scopes=[('all',r),('lower_origin_exposure',r.filter(low)),('lower_under_21',r.filter(low&(pl.col('age')<21))),
        ('positive_lower_under_21',r.filter(low&(pl.col('age')<21)&(pl.col('baseline_rate')>0)))]
    summaries=[]
    for name,g in scopes:
        summaries.append(dict(scope=name,rows=len(g),people=g['player_id'].n_unique(),
            absent_rate_profiles=g.filter(pl.col('rate_profile_people')==0).height,
            sparse_rate_profiles=g.filter(pl.col('rate_profile_people')<20).height,
            positive_estimates=g.filter(pl.col('baseline_rate')>0).height,
            actual_active_rows=g.filter(pl.col('next_pa')>0).height,
            median_age_term=float(g['age_term'].median()),median_level_term=float(g['level_term'].median())))
    selected=fit.read(fit.OUT/'cases.json')+fit.read(fit.OUT/'supplementary-cases.json')
    ids=[c['origin']['row_id'] for c in selected]
    cases=r.filter(pl.col('row_id').is_in(ids)).select('row_id','player_id','player_name','origin_year','age',*keys,
        'baseline_rate','rate_intercept','age_term','level_term','other_term','rate_profile_people','rate_profile_rows',
        'profile_target_pa','current_pa','talent_pa','next_pa').sort('row_id').to_dicts()
    paths=[Path(__file__),ROOT/'docs/hitter-rate-support-audit-contract.md',fit.OUT/'final-report.json',
        fit.setup.current.OUT/'features.parquet',fit.OUT/'scored-predictions.parquet',OUT/'rows.parquet']
    report=dict(no_fits=True,all_current_columns_exact=True,rate_heads_replayed=35,rows=30506,
        summaries=summaries,cells=cells,cases=cases,player_walkthrough_status='pending',protected_outcomes_used=False,
        source_hashes={str(p):sha256_file(p) for p in paths})
    (OUT/'report.json').write_text(__import__('json').dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf8')
    print(summaries)
    print(cases)


if __name__=='__main__':
    main()
