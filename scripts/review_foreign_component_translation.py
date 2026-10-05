"""Independent event/reference/optimum/profile reconstruction and player walks."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import polars as pl

from universal_baseball.post_arrival_history import player_fold
from universal_baseball.storage import sha256_file
from prepare_foreign_component_translation import ROOT, OUT, INPUTS, NPB, KBO, DOMESTIC, read, save, verify

EVIDENCE=ROOT/'reports/model-evidence/foreign-component-translation'
EVENTS=['other','K','UBB','HBP','1B','2B','3B','HR']


def independent_counts(rows, domestic=False):
    columns=['plate_appearances','strike_outs','base_on_balls','intentional_walks','hit_by_pitch',
             'hits','doubles','triples','home_runs'] if domestic else ['pa','so','bb','ibb','hbp','hits','doubles','triples','hr']
    a=np.asarray([[r[c] for c in columns] for r in rows],dtype=float).reshape((-1,9))
    known=np.column_stack((a[:,1],a[:,2]-a[:,3],a[:,4],a[:,5]-a[:,6]-a[:,7]-a[:,8],a[:,6],a[:,7],a[:,8]))
    c=np.column_stack((a[:,0]-known.sum(1),known))
    assert (c>=0).all() and np.array_equal(c.sum(1),a[:,0])
    return c


def prob(c):
    return (c+.5)/(c.sum()+4)


def logcenter(p):
    z=np.log(p); return z-z.mean()


def selected(pairs,year,excluded):
    return [p for p in pairs if p['through_year']<=year and p['fold'] not in excluded
            and p['minimum_pa']==30 and p['mechanism']=='consecutive_season'
            and p['a'] in ['NPB','KBO'] and p['b']=='MLB'
            and not p['domestic_2020_exception'] and p['role_evidence']['supported_hitter']]


def main():
    assert not (OUT/'independent-review.json').exists(),'Preserve existing review'
    receipt=read(OUT/'fit-receipt.json'); verify(receipt['source_hashes']); verify(receipt['artifact_hashes'])
    pre=read(OUT/'preflight.json'); fits=read(OUT/'fits.json')['fits']; profiles=read(OUT/'profiles.json')['profiles']
    pairs=read(INPUTS/'pair-role-evidence.json')['pairs']; inputs=read(INPUTS/'origin-inputs.json')['rows']
    lut={r['candidate_key']:r for r in inputs}; flut={r['fit_key']:r for r in fits}
    totals=defaultdict(lambda:np.zeros(8)); held=defaultdict(lambda:np.zeros(8)); unmapped=defaultdict(float)
    source_rows=0
    for league,path in [('NPB',NPB),('KBO',KBO),('MLB',DOMESTIC)]:
        frame=pl.read_parquet(path)
        frame=frame.filter((pl.col('season')<=2025)&(pl.col('bucket')=='MLB')) if league=='MLB' else frame
        rows=frame.to_dicts(); counts=independent_counts(rows,league=='MLB'); source_rows+=len(rows)
        for r,c in zip(rows,counts):
            key=league,r['season']; totals[key]+=c
            if r['player_id'] is None: unmapped[key]+=c.sum()
            else: held[key,player_fold(r['player_id'])]+=c
    def reference(league,year,excluded):
        assert year<=2024
        key=league,year
        return prob(totals[key]-sum((held[key,k] for k in set(excluded)),np.zeros(8)))
    max_gradient=0.; checked_heads=0
    for m in fits:
        y=m['cutoff']; excluded=m['excluded_folds']; pool=selected(pairs,y,excluded)
        ids=Counter(p['player_id'] for p in pool)
        assert len(ids)==m['people'] and len(pool)==len(m['pairs'])
        assert m['people_by_league']=={l:len({p['player_id'] for p in pool if p['a']==l}) for l in ['NPB','KBO']}
        x=[]; t=[]; w=[]
        for p, recorded in zip(pool,m['pairs']):
            assert p['through_year']==p['from_year']+1<=y
            assert p['fold']==player_fold(p['player_id']) and p['fold'] not in excluded
            a=independent_counts([p['from_counts']])[0]; b=independent_counts([p['to_counts']])[0]
            x.append(logcenter(prob(a))-logcenter(reference(p['a'],p['from_year'],excluded)))
            t.append(logcenter(prob(b))-logcenter(reference('MLB',p['through_year'],excluded)))
            w.append(min((2*p['from_pa']*p['to_pa']/(p['from_pa']+p['to_pa']))/300,1)/ids[p['player_id']])
            assert np.allclose(x[-1],recorded['source_relative_clr'],rtol=0,atol=1e-12)
            assert np.allclose(t[-1],recorded['target_relative_clr'],rtol=0,atol=1e-12)
            assert abs(w[-1]-recorded['weight'])<1e-12
        x=np.asarray(x).reshape((-1,8)); t=np.asarray(t).reshape((-1,8)); w=np.asarray(w)
        for j,coef in enumerate(np.asarray(m['coefficients'])):
            design=np.array([[int(p['a']=='NPB'),int(p['a']=='KBO'),x[i,j]] for i,p in enumerate(pool)]).reshape((-1,3))
            g=design.T@(w*(design@coef-t[:,j]))+2*coef
            assert np.max(np.abs(g[:2]))<1e-7
            assert 0<=coef[2]<=2
            assert (g[2]>=-1e-7 if coef[2]<1e-6 else g[2]<=1e-7 if coef[2]>2-1e-6 else abs(g[2])<1e-7)
            assert np.allclose(g,m['optimizer_gradients'][j],rtol=0,atol=1e-7)
            max_gradient=max(max_gradient,np.max(np.abs(g[:2]))); checked_heads+=1
    for p in profiles:
        i=lut[p['candidate_key']]; m=flut[p['fit_key']]; excluded=sorted({p['outer_fold'],player_fold(i['player_id'])})
        assert excluded==p['excluded_folds']==m['excluded_folds'] and i['origin_year']==m['cutoff']
        ref=reference('MLB',i['origin_year'],excluded)
        assert np.allclose(ref,p['MLB_reference'],rtol=0,atol=1e-12)
        weighted=np.zeros(8); supported=0.; total=0.; coef=np.array(m['coefficients'])
        for l in ['NPB','KBO']:
            own=np.zeros(8); env=np.zeros(8); n=0.
            for lag,recency in enumerate([5,4,3]):
                s=i['foreign_history_counts'][f'{l}_{lag}']
                if s['player_identity_and_stat_observed'] and s['counts']['pa']>0:
                    a=independent_counts([s['counts']])[0]; weight=recency*a.sum()
                    own+=weight*prob(a); env+=weight*reference(l,s['season'],excluded); n+=weight
            if not n: continue
            piece=next(q for q in p['leagues'] if q['league']==l); total+=n
            assert np.allclose(own/n,piece['own_pooled_probability'],rtol=0,atol=1e-12)
            source=logcenter(own/n)-logcenter(env/n)
            assert np.allclose(source,piece['source_relative_clr'],rtol=0,atol=1e-12)
            if m['people_by_league'][l]:
                z=logcenter(ref)+coef[:,['NPB','KBO'].index(l)]+coef[:,2]*source
                q=np.exp(z-z.max()); q/=q.sum(); weighted+=n*q; supported+=n
                assert np.allclose(q,piece['translated_probability'],rtol=0,atol=1e-12)
            else: assert piece['translated_probability'] is None
        assert total==p['total_weighted_exposure'] and supported==p['supported_weighted_exposure']
        assert p['missing_translation']==(supported==0)
        if supported: assert np.allclose(weighted/supported,p['translated_probability'],rtol=0,atol=1e-12)
        else: assert p['translated_probability'] is None
    cases=read(INPUTS/'reviewed-cases.json')['cases']
    # Keep all preselected source controls and all four foreign context controls.
    for pid,y,name in [(519346,2016,'Eric Thames'),(808982,2024,'Jung Hoo Lee'),(673490,2022,'Ha-Seong Kim')]:
        original=next(r for r in inputs if r['player_id']==pid and r['origin_year']==y)
        cases.append(dict(name=name,player_id=pid,origin_year=y,origin_inputs=original,
                          origin_only_peers=[],selection='previous_context_comparison_control'))
    domestic=pl.read_parquet(DOMESTIC).filter((pl.col('season')<=2025)&(pl.col('bucket')=='MLB'))
    anchor=pl.read_parquet(ROOT/'reports/generated/hitter-minor-statcast-precision/scored-predictions.parquet')
    reviewed=[]
    for c in cases:
        pid,y=c['player_id'],c['origin_year']; own=player_fold(pid)
        translated=next((r for r in profiles if r['player_id']==pid and r['origin_year']==y and r['outer_fold']==own),None)
        actual=domestic.filter((pl.col('player_id')==pid)&(pl.col('season')==y+1))
        actual_counts=independent_counts(actual.to_dicts(),True).sum(0)
        old=anchor.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)).select('combined_rate','preseason_pa','preseason_p','preseason_conditional_pa').to_dicts()
        model=flut[translated['fit_key']] if translated else None
        source=c['origin_inputs']; peers=c.get('origin_only_peers',[])
        if not peers and source:
            pool=[]
            for other in inputs:
                if other['origin_year']!=y or other['player_id']==pid: continue
                if other['recent_foreign_pa']<=0: continue
                distance=abs(np.log1p(other['recent_foreign_pa'])-np.log1p(source['recent_foreign_pa']))
                if other['age_at_information_date'] is not None and source['age_at_information_date'] is not None:
                    distance+=abs(other['age_at_information_date']-source['age_at_information_date'])/5
                pool.append(dict(player_id=other['player_id'],origin_year=y,distance=float(distance),recent_foreign_pa=other['recent_foreign_pa']))
            peers=sorted(pool,key=lambda q:(q['distance'],q['player_id']))[:3]
        observations=[]
        for peer in peers:
            opid=peer['player_id']; a=domestic.filter((pl.col('player_id')==opid)&(pl.col('season')==y+1))
            cc=independent_counts(a.to_dicts(),True).sum(0)
            observations.append(dict(**peer,next_MLB_pa=float(cc.sum()),next_MLB_probability=(cc/cc.sum()).tolist() if cc.sum() else None))
        reviewed.append(dict(name=c['name'],player_id=pid,origin_year=y,
            selection=c.get('selection','fixed_before_source_and_component_fit'),source_input=source,
            translated_profile=translated,model=model,unchanged_saved_forecast=old,
            observed_next_MLB_counts=actual_counts.tolist(),observed_next_MLB_PA=float(actual_counts.sum()),
            observed_next_MLB_probability=(actual_counts/actual_counts.sum()).tolist() if actual_counts.sum() else None,
            origin_only_peers=observations,new_MLB_PA_forecast=None,new_full_value_forecast=None))
    save(OUT/'reviewed-cases.json',dict(cases=reviewed,player_walkthrough_status='arithmetic_complete_manual_pending'))
    tests=subprocess.run([sys.executable,'-m','pytest','tests/test_foreign_component_translation.py','tests/test_foreign_origin_inputs.py','tests/test_foreign_mover_support_v2.py','-q','-p','no:cacheprovider'],cwd=ROOT,capture_output=True,text=True)
    assert tests.returncode==0,tests.stdout+tests.stderr
    freeze=subprocess.run([sys.executable,'scripts/verify_hitter_full_2026_freeze.py'],cwd=ROOT,capture_output=True,text=True)
    assert freeze.returncode==0,freeze.stdout+freeze.stderr
    hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [OUT/'preflight.json',OUT/'fits.json',OUT/'profiles.json',OUT/'fit-receipt.json',OUT/'reviewed-cases.json',Path(__file__)]}
    save(OUT/'independent-review.json',dict(status='arithmetic_complete_manual_pending',hashes=hashes,
         source_rows_reconstructed=source_rows,component_optima_checked=checked_heads,max_intercept_gradient=float(max_gradient),
         profiles_reconstructed=len(profiles),cases=len(reviewed),tests=tests.stdout,protected_freeze=json.loads(freeze.stdout),
         player_walkthrough_status='arithmetic_complete_manual_pending',new_full_hitter_forecasts=0,
         mean_estimate_is_not_uncertainty_distribution=True,unmapped_reference_identity_limit=True))
    print(json.dumps(dict(profiles_reconstructed=len(profiles),optima=checked_heads,cases=len(reviewed),manual_review='pending')),flush=True)


if __name__=='__main__': main()
