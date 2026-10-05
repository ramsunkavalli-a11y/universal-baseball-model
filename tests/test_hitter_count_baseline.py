import copy
import numpy as np
import pytest
from universal_baseball.hitter_count_baseline import assemble, objective, fit, probabilities, past_profile


def test_prior_missing_and_dilution():
    ref=np.array([.45,.22,.08,.01,.15,.05,.01,.03]); p=ref.copy();p[0]-=.05;p[7]+=.05
    c=dict(source='minor',precision_PA=50,probability=p)
    a,pa=assemble([c],ref,50); b,pb=assemble([c,dict(source='MLB',precision_PA=1000,probability=ref)],ref,1050)
    assert a['count_reliability']==50/1250
    assert abs(pb[7]-ref[7])<abs(pa[7]-ref[7])
    m,pm=assemble([],ref,0);assert m['count_missing']==1 and np.array_equal(pm,ref)
    with pytest.raises(ValueError):assemble([c],ref,0)


def test_gradient_symmetry_probability_and_fit():
    rng=np.random.default_rng(3);x=rng.normal(size=(17,3));aug=np.column_stack([np.ones(17),x])
    c=rng.integers(1,30,(17,8)).astype(float);offset=rng.normal(size=(17,8));b=rng.normal(size=(4,8))*.02
    v,g=objective(b.ravel(),aug,c,offset)
    for i in [0,7,8,17,31]:
        plus=b.ravel().copy();minus=plus.copy();plus[i]+=1e-6;minus[i]-=1e-6
        assert np.isclose(g[i],(objective(plus,aug,c,offset)[0]-objective(minus,aug,c,offset)[0])/2e-6,atol=1e-8)
    order=rng.permutation(8)
    assert np.isclose(v,objective(b[:,order].ravel(),aug,c[:,order],offset[:,order])[0])
    m=fit(x,c,offset,np.ones(17));p=probabilities(m['beta'],x,offset)
    assert np.allclose(p.sum(1),1) and (p>0).all()
    assert np.allclose(m['beta'].sum(1),0,atol=1e-7)


def test_foreign_future_probability_has_no_effect():
    ref=np.array([.45,.22,.08,.01,.15,.05,.01,.03]);cnt=dict(pa=100,so=20,bb=10,ibb=0,hbp=1,hits=27,doubles=5,triples=1,hr=4)
    from universal_baseball.foreign_component_translation import events
    counts=events(cnt);p=(counts+.5)/104
    source=dict(origin_year=2024,candidate_key='2024:1',foreign_history_counts={})
    for l in ['NPB','KBO']:
        for lag in range(3):
            source['foreign_history_counts'][f'{l}_{lag}']=dict(season=2024-lag,counts=cnt if l=='NPB' and lag==0 else {k:0 for k in cnt},player_identity_and_stat_observed=l=='NPB' and lag==0)
    archived=dict(candidate_key='2024:1',origin_year=2024,outer_fold=1,excluded_folds=[1,2],leagues=[dict(league='NPB',
        own_pooled_probability=p,pooled_reference=ref,mover_people=0,translated_probability='INVALID FUTURE',
        observed_seasons=[dict(season=2024,counts=counts,pa=100,probabilities=p,reference=ref,recency=5)])])
    graph=dict(cutoff=2024,max_source_year=2024,excluded_folds=[1,2],mlb_reference=ref,offsets={})
    a,note=past_profile([],graph,source,archived,origin=2024,outer_fold=1,own_fold=2)
    assert a['count_NPB_share']==100/1300 and not note['future_foreign_probabilities_used']
    altered=copy.deepcopy(archived);altered['leagues'][0]['translated_probability']=None
    b,_=past_profile([],graph,source,altered,origin=2024,outer_fold=1,own_fold=2)
    assert a==b
    with pytest.raises(ValueError):past_profile([],graph,source,archived,origin=2024,outer_fold=3,own_fold=2)
