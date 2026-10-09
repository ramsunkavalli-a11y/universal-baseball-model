import pytest
from universal_baseball.hitter_role_budget_v1 import evidence,predict


def annual(year=2026,mlb=True,pos=10,amount=100):
    r=dict(player_id=1,season=year,is_mlb=mlb,starts_10=amount if pos==10 else 0)
    r.update({f'outs_{p}':amount if p==pos else 0 for p in range(2,10)})
    return r


def row(**kw):
    return dict(player_id=1,origin_year=2026,pa_0=600,source_position='10',stage='current_mlb',preseason_pa=600,**kw)


def test_pure_dh_no_fielding():
    r=row();r.update(evidence(r,[annual()],27))
    assert r['role_shares']==[0.]*8+[1.]
    tables={('all',):dict(key=['all'],people=40,effective_people=25,denominator_PA=20000,job_outs_per_PA=6)}
    p=predict(r,tables,27)
    assert p['values'][:8]==[0.]*8 and p['values'][8]>0
    assert sum(p['values'][:8])+27*p['values'][8]==pytest.approx(p['job_budget'])


def test_tiny_promotion_keeps_minor_role_and_never_donates():
    r=row();r['pa_0']=10;r['source_position']='3'
    e=evidence(r,[annual(pos=10,amount=2),annual(mlb=False,pos=3,amount=2000)],27)
    assert e['role_shares'][1]>e['role_shares'][8]
    assert all(x==0 for i,x in enumerate(e['role_shares']) if i not in (1,8))


def test_future_ignored_unknown_unallocated():
    r=row();r.update(pa_0=0,source_position='unknown')
    e=evidence(r,[annual(year=2027,pos=2)],27)
    assert e['unknown'] and sum(e['role_shares'])==0
    with pytest.raises(ValueError):evidence(r,[],0)


def test_rehab_does_not_erase_larger_mlb_history():
    from universal_baseball.hitter_role_fallback_v1 import evidence as repaired
    r=row();r.update(pa_0=0,source_position='6')
    old=annual(year=2025,pos=6,amount=3000)
    rehab=annual(mlb=False,pos=10,amount=2)
    e=repaired(r,[old,rehab],27)
    assert e['role_shares'][4]==pytest.approx(1500/1554)
    assert e['role_shares'][8]==pytest.approx(54/1554)
    assert len(e['fallback_sources'])==2
