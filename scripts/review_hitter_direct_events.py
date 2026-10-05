"""Append numerical scope correction and independently verify direct scores."""
import json
import numpy as np
import polars as pl

from check_hitter_direct_events import OUT,OLD,GEN,ARMS,read,save,verify,event_scores
from finalize_hitter_shared_events import independent_score
from review_hitter_overseas_integration import score
from review_hitter_evidence_representation import interval,rate_interval
from supplement_hitter_overseas_scores import rate_score
from universal_baseball.storage import sha256_file


def clean_foreign_precision(q):
    # Recovering total precision from log1p leaves sub-picoplate-appearance
    # residuals. These cannot establish a real foreign source or move a bin.
    return q.with_columns(pl.when(pl.col('foreign_supported_PA').abs()<1e-6)
        .then(0.).otherwise(pl.col('foreign_supported_PA')).alias('foreign_supported_PA'))


def scope(q,name):
    g=q.filter(pl.col('source_addition')) if name=='additions' else q.filter(~pl.col('source_addition'))
    if name=='all_never_debut':g=g.filter(pl.col('prior_debut')==0)
    elif name in ['upper_never_debut','lower_never_debut']:g=g.filter((pl.col('prior_debut')==0)&(pl.col('stage')==('Upper minors' if name.startswith('upper') else 'Lower minors')))
    elif name=='original_no_arrival':g=g.filter(pl.col('next_pa')==0)
    elif name=='foreign_never_debut':g=g.filter((pl.col('prior_debut')==0)&(pl.col('foreign_supported_PA')>0))
    elif name=='established_component_diagnostic':g=g.filter(pl.col('prior_debut')>0)
    elif name.startswith('origin_'):g=g.filter(pl.col('origin_year')==int(name[7:]))
    elif name.startswith('never_exposure_'):
        lo,hi=map(float,name[len('never_exposure_'):].split('_'))
        g=g.filter((pl.col('prior_debut')==0)&(pl.col('US_supported_PA')+pl.col('foreign_supported_PA')>=lo)&(pl.col('US_supported_PA')+pl.col('foreign_supported_PA')<hi))
    return g


def independent_events(g, population, arm):
    h=g.filter(pl.col('next_pa')>0).filter(pl.col('direct_domestic_supported' if population=='US_supported' else 'direct_foreign_supported'))
    col={'origin_reference':'direct_reference','past_US':'past_US_probability','future_US':'direct_domestic_probability','future_combined':'direct_foreign_probability'}[arm]
    yearly=[]
    for y in sorted(h['origin_year'].unique()):
        z=h.filter(pl.col('origin_year')==y)
        p=np.array(z[col].to_list());c=np.array(z['actual_events'].to_list());pa=c.sum(1);total=pa.sum()
        # Sum actual one-hot event losses directly over recorded event counts.
        log=-float(np.sum(c*np.log(p))/total)
        br=0.
        for j in range(8):
            one=np.zeros(8);one[j]=1
            br+=float(np.sum(c[:,j]*np.sum((p-one)**2,axis=1))/total)
        yearly.append((log,br,(p*pa[:,None]).sum(0)/total,c.sum(0)/total))
    return float(np.mean([r[0] for r in yearly])),float(np.mean([r[1] for r in yearly])),np.mean([r[2] for r in yearly],axis=0),np.mean([r[3] for r in yearly],axis=0)


def main():
    assert not (OUT/'calculation-review.json').exists(),'Preserve review'
    verify(read(OUT/'preflight.json')['input_hashes']);verify(read(OUT/'evaluation-receipt.json')['hashes'])
    original=pl.read_parquet(OUT/'predictions.parquet');q=clean_foreign_precision(original)
    old=read(OUT/'scores.json');corrected=[];changes=[];check_count=0
    for s in old['scopes']:
        name=s['scope'];g=scope(q,name);active=g.filter(pl.col('next_pa')>0)
        if g.height!=s['rows']:
            changes.append(dict(scope=name,old_rows=s['rows'],correct_rows=g.height,old_actual_PA=s['actual_PA'],correct_actual_PA=int(g['next_pa'].sum())))
            s=dict(scope=name,rows=g.height,people=g['player_id'].n_unique(),actual_PA=int(g['next_pa'].sum()),actual_value=float(g['actual_relative_value'].sum()),
                scores={a:score(g,a) for a in s['scores']},PA_weighted_rate={a:rate_score(active,a+'_rate','actual_relative_rate',True) if active.height else None for a in s['scores']},event_forecasts=event_scores(g))
        for a,expected in s['scores'].items():
            z,rate=independent_score(g,a)
            for key,v in z.items():
                assert (v is None and expected[key] is None) or np.isclose(v,expected[key],atol=1e-10,rtol=0),(name,a,key)
                check_count+=1
            assert (rate is None and s['PA_weighted_rate'][a] is None) or np.isclose(rate,s['PA_weighted_rate'][a],atol=1e-10,rtol=0)
            check_count+=1
        for e in s['event_forecasts']:
            for a,v in e['scores'].items():
                ll,br,p,c=independent_events(g,e['population'],a)
                assert np.isclose(ll,v['logloss'],atol=1e-12,rtol=0) and np.isclose(br,v['multiclass_brier'],atol=1e-12,rtol=0)
                assert np.allclose(p,v['predicted_frequency'],atol=1e-12,rtol=0) and np.allclose(c,v['actual_frequency'],atol=1e-12,rtol=0)
                check_count+=18
        corrected.append(s)
    save('corrected-scores.json',dict(scopes=corrected))
    foreign=scope(q,'foreign_never_debut');active=foreign.filter(pl.col('next_pa')>0)
    save('corrected-foreign-intervals.json',[dict(scope='foreign_never_debut',arm=a,value=interval(foreign,a,'current'),rate=rate_interval(foreign,a,'current') if active.height else None) for a in ARMS])
    save('numerical-scope-correction.json',dict(changes=changes,forecast_changes=0,new_fits=0,
        explanation='Sub-1e-6 PA floating point residue from inverse log exposure is not observed foreign evidence. Original scope receipt and forecasts retained; corrected scope scores appended.',
        preserved_prediction_sha256=sha256_file(OUT/'predictions.parquet')))
    cases=read(OUT/'reviewed-cases.json')['cases']
    for c in cases:
        assert c['profile']['persistence_excluded_folds']==[c['origin']['outer_fold']]
        for a,t in c['direct_traces'].items():
            assert np.isclose(sum(t['event_value_terms'].values()),t['raw_rate'],atol=1e-10,rtol=0)
            assert np.isclose(t['PA'],t['p']*t['conditional_PA'],atol=1e-10,rtol=0)
            row=q.filter(pl.col('row_id')==c['row_id']).row(0,named=True)
            assert np.isclose(t['value'],t['PA']*(t['routed_rate']/600+row['origin_replacement_rate']),atol=1e-10,rtol=0)
        if c['actual']['PA']==0:assert c['actual']['rate'] is None
    save('calculation-review.json',dict(independent_score_fields=check_count,cases_replayed=len(cases),new_fits=0,
        correction=read(OUT/'numerical-scope-correction.json'),player_walkthrough_status='pending',protected_outcomes_used=False,
        hashes={str(OUT/n):sha256_file(OUT/n) for n in ['corrected-scores.json','corrected-foreign-intervals.json','numerical-scope-correction.json']}))
    print(f'{check_count} independent fields and {len(cases)} case calculations verified; baseball judgment pending.')


if __name__=='__main__':main()
