"""Independently reconstruct the history repair and preserve every reviewed case."""
from collections import Counter,defaultdict
import json
import subprocess
import sys

import numpy as np
import polars as pl

from prepare_foreign_component_translation_v2 import ROOT,OUT,OLD,INPUTS,read,save,verify
from prepare_foreign_component_translation import NPB,KBO,DOMESTIC
from review_foreign_component_translation import independent_counts,prob,logcenter,selected
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.storage import sha256_file


def main():
    assert not (OUT/'independent-review.json').exists(),'Preserve review'
    receipt=read(OUT/'fit-receipt.json');verify(receipt['source_hashes']);verify(receipt['artifact_hashes'])
    oldreview=read(OLD/'final-review.json');verify(oldreview['artifact_hashes'])
    totals=defaultdict(lambda:np.zeros(8));held=defaultdict(lambda:np.zeros(8));history=defaultdict(lambda:np.zeros(8))
    for l,path in [('NPB',NPB),('KBO',KBO),('MLB',DOMESTIC)]:
        f=pl.read_parquet(path)
        if l=='MLB':f=f.filter((pl.col('season')<=2024)&(pl.col('bucket')=='MLB'))
        rows=f.to_dicts();counts=independent_counts(rows,l=='MLB')
        for r,c in zip(rows,counts):
            key=l,r['season'];totals[key]+=c
            if r['player_id'] is not None:
                held[key,player_fold(r['player_id'])]+=c
                if l!='MLB':history[r['player_id'],l,r['season']]+=c
    def ref(l,y,k):return prob(totals[l,y]-sum((held[(l,y),fold] for fold in set(k)),np.zeros(8)))
    def pool(pid,l,y,k):
        own=np.zeros(8);env=np.zeros(8);n=0.;years=[]
        for lag,w in enumerate([5,4,3]):
            c=history.get((pid,l,y-lag))
            if c is not None and c.sum()>0:
                mass=w*c.sum();own+=mass*prob(c);env+=mass*ref(l,y-lag,k);n+=mass;years.append(y-lag)
        assert n>0
        return logcenter(own/n)-logcenter(env/n),own/n,env/n,sorted(years)
    fits=read(OUT/'fits.json')['fits'];profiles=read(OUT/'profiles.json')['profiles'];pairs=read(INPUTS/'pair-role-evidence.json')['pairs']
    inputs={r['candidate_key']:r for r in read(INPUTS/'origin-inputs.json')['rows']}
    oldfits={r['fit_key']:r for r in read(OLD/'fits.json')['fits']}
    checked=0
    for m in fits:
        y=m['cutoff'];k=m['excluded_folds'];p=selected(pairs,y,k);reps=Counter(r['player_id'] for r in p)
        x=[];t=[];weights=[]
        assert len(p)==len(m['pairs'])==len(oldfits[m['fit_key']]['pairs'])
        for a,recorded,old in zip(p,m['pairs'],oldfits[m['fit_key']]['pairs']):
            z,own,env,years=pool(a['player_id'],a['a'],a['from_year'],k)
            assert years==recorded['source_history']['observed_source_years']
            assert max(years)<=a['from_year']<a['through_year']<=y
            assert np.allclose(z,recorded['source_relative_clr'],rtol=0,atol=1e-12)
            assert np.allclose(own,recorded['source_history']['pooled_probability'],rtol=0,atol=1e-12)
            assert np.allclose(env,recorded['source_history']['pooled_reference'],rtol=0,atol=1e-12)
            v=logcenter(prob(independent_counts([a['to_counts']])[0]))-logcenter(ref('MLB',a['through_year'],k))
            assert np.allclose(v,recorded['target_relative_clr'],rtol=0,atol=1e-12)
            assert all(recorded[field]==old[field] for field in ['player_id','league','from_year','target_year','weight','target_relative_clr'])
            w=min(2*a['from_pa']*a['to_pa']/(a['from_pa']+a['to_pa'])/300,1)/reps[a['player_id']]
            assert abs(w-recorded['weight'])<1e-12
            x.append(z);t.append(v);weights.append(w)
        x=np.array(x).reshape((-1,8));t=np.array(t).reshape((-1,8));w=np.array(weights)
        for j,c in enumerate(np.array(m['coefficients'])):
            d=np.array([[int(a['a']=='NPB'),int(a['a']=='KBO'),x[i,j]] for i,a in enumerate(p)]).reshape((-1,3))
            g=d.T@(w*(d@c-t[:,j]))+2*c
            assert np.max(np.abs(g[:2]))<1e-7 and 0<=c[2]<=2
            assert (g[2]>=-1e-7 if c[2]<1e-6 else g[2]<=1e-7 if c[2]>2-1e-6 else abs(g[2])<1e-7)
            checked+=1
    flut={m['fit_key']:m for m in fits}
    oldprofiles={(p['candidate_key'],p['outer_fold']):p for p in read(OLD/'profiles.json')['profiles']}
    for p in profiles:
        original=oldprofiles[p['candidate_key'],p['outer_fold']];m=flut[p['fit_key']];i=inputs[p['candidate_key']]
        assert p['excluded_folds']==sorted({p['outer_fold'],player_fold(p['player_id'])})
        assert p['leagues'] and len(p['leagues'])==len(original['leagues'])
        total=np.zeros(8);n=0.;coef=np.array(m['coefficients'])
        for piece,opiece in zip(p['leagues'],original['leagues']):
            for field in ['league','recency_weighted_exposure','mover_people','own_pooled_probability','pooled_reference','source_relative_clr','observed_seasons']:
                assert piece[field]==opiece[field]
            l=piece['league'];source,own,env,years=pool(p['player_id'],l,p['origin_year'],p['excluded_folds'])
            assert np.allclose(source,piece['source_relative_clr'],rtol=0,atol=1e-12)
            if piece['mover_people']:
                z=logcenter(ref('MLB',p['origin_year'],p['excluded_folds']))+coef[:,['NPB','KBO'].index(l)]+coef[:,2]*source
                q=np.exp(z-z.max());q/=q.sum()
                assert np.allclose(q,piece['translated_probability'],rtol=0,atol=1e-12)
                exposure=piece['recency_weighted_exposure'];total+=exposure*q;n+=exposure
            else:assert piece['translated_probability'] is None
        assert p['missing_translation']==original['missing_translation']==(n==0)
        if n:assert np.allclose(total/n,p['translated_probability'],rtol=0,atol=1e-12)
    cases=[]
    for c in read(OLD/'reviewed-cases.json')['cases']:
        p=next((p for p in profiles if p['player_id']==c['player_id'] and p['origin_year']==c['origin_year'] and p['outer_fold']==player_fold(c['player_id'])),None)
        cases.append(dict(**c,repaired_profile=p,repaired_model=flut[p['fit_key']] if p else None))
    save(OUT/'reviewed-cases.json',dict(cases=cases,ordinary_unresolved_controls=read(OLD/'ordinary-and-unresolved-controls.json'),walkthrough='arithmetic_complete_manual_pending'))
    tests=subprocess.run([sys.executable,'-m','pytest','tests/test_foreign_component_translation.py','tests/test_foreign_component_translation_v2.py','tests/test_foreign_origin_inputs.py','tests/test_foreign_mover_support_v2.py','-q','-p','no:cacheprovider'],cwd=ROOT,capture_output=True,text=True)
    assert tests.returncode==0,tests.stdout+tests.stderr
    freeze=subprocess.run([sys.executable,'scripts/verify_hitter_full_2026_freeze.py'],cwd=ROOT,capture_output=True,text=True)
    assert freeze.returncode==0,freeze.stdout+freeze.stderr
    save(OUT/'independent-review.json',dict(status='arithmetic_complete_manual_pending',component_optima_checked=checked,profiles_reconstructed=len(profiles),same_pair_targets_and_weights=True,
        same_prediction_history_and_references=True,cases=len(cases),tests=tests.stdout,protected_freeze=json.loads(freeze.stdout),
        hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [OUT/'fits.json',OUT/'profiles.json',OUT/'preflight.json',OUT/'fit-receipt.json',OUT/'reviewed-cases.json',ROOT/'scripts/review_foreign_component_translation_v2.py']}))
    print(json.dumps(dict(optima=checked,profiles=len(profiles),cases=len(cases),review='manual_pending')),flush=True)


if __name__=='__main__':main()
