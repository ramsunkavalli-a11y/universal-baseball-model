import numpy as np
import pytest

from universal_baseball.defense_jobs import evidence, allocate, reconcile, group


def annual(y, dh=0, **outs):
    return dict(season=y,is_mlb=True,**{f'outs_{p}':outs.get(str(p),0) for p in range(2,10)},
                **{f'starts_{p}':0 for p in range(2,10)},starts_10=dh)


def row(**changes):
    return dict(origin_year=2024,source_position='10',prior_debut=1,pa_0=600,pa_1=600,pa_2=600,**changes)


def test_current_dh_is_not_unknown_or_old_of_only():
    e=evidence(row(),[annual(2024,dh=150),annual(2022,**{'9':22})],27.)
    assert not e['job_unknown'] and e['job_primary_role']==10
    assert e['job_own_shares'][8]>.998


def test_rehab_does_not_overwrite_mlb():
    mlb=annual(2023,**{'6':4000});minor=annual(2024,**{'3':200});minor['is_mlb']=False
    r=row();r['pa_0']=0
    e=evidence(r,[mlb,minor],27.)
    assert e['job_own_shares'][4]==1 and e['job_evidence_kind']=='weighted_MLB'


def test_unknown_stays_unallocated_and_no_catcher_from_broad_prior():
    r=row();r['source_position']='unknown';e=evidence(r,[],27.);r.update(e)
    assert allocate(r,{},100)['unknown_mass']==100
    r['source_position']='3';r.update(evidence(r,[],27.))
    cell=dict(people=30,effective_people=20,denominator_job_time=100,shares=[.5,0,0,0,0,0,0,0,.5])
    assert allocate(r,{('all',):cell},100)['shares'][0]==0


def test_pure_dh_training_and_people_not_rows():
    rows=[dict(player_id=1,job_primary_role=10,job_family='DH',job_status='prior_MLB',
               target_year=2022,next_pa=100,actual_job_vector=[0]*8+[270])]*3
    g=group(rows,('all',),True)
    assert g['people']==1 and g['rows']==3 and g['shares'][-1]==1


def test_capacity_no_forced_column_fill_no_new_roles():
    seed=np.array([[9.,1.,0],[1.,9.,0]])
    out,receipt=reconcile(seed,[6.,15.,10.])
    assert np.allclose(out.sum(axis=1),[10,10])
    assert np.isclose(out[:,0].sum(),6,atol=1e-4)
    assert out[:,2].sum()==0 and out[:,1].sum()<15
    assert receipt['feasibility']


def test_feasible_seed_unchanged():
    seed=np.array([[2.,3.],[0.,1.]])
    out,_=reconcile(seed,[10.,10.])
    assert np.allclose(out,seed)


def test_infeasible_role_graph_fails_not_invents_position():
    with pytest.raises(ValueError,match='support graph'):
        reconcile([[10.,0.],[10.,0.]],[5.,20.])


def test_overfull_total_scales_jobs_not_fills_zeros():
    out,receipt=reconcile([[10.,10.],[10.,10.]],[5.,5.])
    assert receipt['global_mass_factor']==.25
    assert np.allclose(out.sum(axis=1),[5,5])
