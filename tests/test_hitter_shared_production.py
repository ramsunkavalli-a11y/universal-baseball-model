import numpy as np
import pytest
from universal_baseball.hitter_shared_production import assemble, reanchor, probability, profile, FEATURES


def test_reanchor_identity_and_reference():
    p=np.array([.5,.2,.08,.01,.12,.05,.01,.03]); r=np.full(8,1/8)
    assert np.allclose(reanchor(p,r,r),p)
    assert np.allclose(reanchor(p,p,r),r)


def test_prior_once_symmetric_and_small_sample():
    ref=np.full(8,1/8); p=ref.copy();p[0]-=.1;p[7]+=.1
    c=[dict(source='minor',precision_PA=1,probability=p)]
    f=assemble(c,ref,1)
    assert np.isclose(f['shared_event_HR'],1/1201)
    assert abs(sum(f[n] for n in FEATURES[:8]))<1e-12
    assert f['shared_reliability']==1/1201


def test_mlb_dilutes_old_minor_and_removal_recomputes():
    ref=np.full(8,1/8); p=ref.copy();p[0]-=.1;p[7]+=.1
    c=[dict(source='minor',precision_PA=100,probability=p)]
    a=assemble(c,ref,100)
    c.append(dict(source='MLB',precision_PA=1800,probability=ref))
    b=assemble(c,ref,1900)
    assert 0<b['shared_event_HR']<a['shared_event_HR']
    z=assemble(c,ref,1900,remove='minor')
    assert z['shared_event_HR']==0 and z['shared_minor_share']==0
    assert z['shared_reliability']==1800/3000


def test_bad_event_data_rejected():
    with pytest.raises(ValueError):probability([.1]*8)
    with pytest.raises(ValueError):assemble([dict(source='minor',precision_PA=-1,probability=np.full(8,1/8))],np.full(8,1/8),1)


def test_future_and_held_fold_graph_rejected():
    graph=dict(cutoff=2024,max_source_year=2024,excluded_folds=[0],mlb_reference=[.125]*8,offsets={})
    with pytest.raises(ValueError,match='contamination'):
        profile([],graph,None,None,origin=2024,outer_fold=0,own_fold=1)
    graph['excluded_folds']=[0,1];graph['max_source_year']=2025
    with pytest.raises(ValueError,match='Future'):
        profile([],graph,None,None,origin=2024,outer_fold=0,own_fold=1)
