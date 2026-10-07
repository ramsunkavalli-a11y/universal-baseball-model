import numpy as np
import pytest

from universal_baseball.defense_transition import evidence, group, allocate, keys


def row(**extra):
    return dict(player_id=1,origin_year=2023,source_position='8',pa_0=0,pa_1=0,pa_2=0,
                prior_debut=0,repertoire_shares=[0,0,0,0,0,0,1,0],repertoire_primary_role=8,**extra)


def usage(year, mlb, pos):
    r=dict(player_id=1,season=year,is_mlb=mlb,defensive_outs=600)
    r.update({f'outs_{p}':600 if p==pos else 0 for p in range(2,10)})
    r.update({f'starts_{p}':20 if p==pos else 0 for p in range(2,11)})
    return r


def prepared(**extra):
    r=row();r.update(extra);r.update(evidence(r,[]));r.update(repair_potential_outs=1000,repair_10=10)
    return r


def tables(r,shares,people=20):
    return {key:dict(key=list(key),people=people,effective_people=12,denominator_outs=1000,shares=shares) for key in keys(r)}


def test_cf_can_move_to_corner_without_becoming_a_catcher():
    r=prepared();p=allocate(r,tables(r,[.1,0,0,0,0,.6,.1,.2]))
    assert p['values'][0]==0 and p['values'][5]>0 and p['values'][7]>0
    assert np.isclose(sum(p['values'][:8]),1000) and p['values'][8]==10


def test_repeated_seasons_do_not_add_people():
    r=prepared();r.update(next_pa=100,**{f'actual_{p}':100 if p==8 else 0 for p in range(2,10)})
    g=group([r,r,r],keys(r)[0],True)
    assert g['people']==1 and g['rows']==3 and g['effective_people']==1


def test_sparse_group_retains_individual_positions():
    r=prepared();p=allocate(r,tables(r,[0,0,1,0,0,0,0,0],people=19))
    assert p['unsupported_transition'] and p['shares']==r['transition_shares']


def test_established_return_uses_MLB_not_minor_rehab():
    r=row();r.update(pa_1=500,prior_debut=1)
    e=evidence(r,[usage(2022,True,6),usage(2023,False,8)])
    assert e['transition_primary_role']==6 and e['transition_shares'][4]==1
    assert e['transition_status']=='prior_MLB' and e['transition_returning_history']
    assert e['transition_evidence_PA']==250 and e['transition_weight']==250/350


def test_future_fielding_cannot_change_origin_evidence():
    r=row();a=evidence(r,[usage(2023,False,8)])
    b=evidence(r,[usage(2023,False,8),usage(2024,True,2)])
    assert a==b


def test_unknown_does_not_invent_positions():
    r=prepared(repertoire_shares=[0]*8,repertoire_primary_role=10,source_position='10')
    p=allocate(r,tables(r,[0,0,0,0,0,1,0,0]))
    assert sum(p['values'][:8])==0 and p['unallocated_outs']==1000


def test_actual_minor_catching_permits_future_C():
    r=row();r.update(evidence(r,[usage(2023,False,2)]));r.update(repair_potential_outs=1000,repair_10=0)
    assert allocate(r,tables(r,[1,0,0,0,0,0,0,0]))['values'][0]==1000


def test_current_MLB_sample_is_not_erased_by_minor_assignment():
    r=prepared(pa_0=500,prior_debut=1)
    p=allocate(r,tables(r,[0,0,0,0,0,1,0,0]))
    assert np.isclose(p['shares'][6],500/600)


def test_invalid_training_denominator_rejected():
    r=prepared(next_pa=0);r.update({f'actual_{p}':100 if p==8 else 0 for p in range(2,10)})
    with pytest.raises(ValueError):group([r],keys(r)[0])
