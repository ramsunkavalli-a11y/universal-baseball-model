import numpy as np
import pytest

from universal_baseball.defense_repertoire import ROLES,POSITIONS,make_repertoire,mean_group,predict,keys


def row(pa=600,pos="3"):
    return dict(player_id=1,origin_year=2022,source_position=pos,pa_0=pa,preseason_pa=500,stage="Current MLB",
                **{f"carry_{p}":0 for p in ROLES})


def annual(season=2022,mlb=True,pos=3,outs=3000,starts=100):
    return dict(player_id=1,season=season,is_mlb=mlb,defensive_outs=outs,
                **{f"outs_{p}":outs if p==pos else 0 for p in ROLES},
                **{f"starts_{p}":starts if p==pos else 0 for p in ROLES})


def prior(r,rate=6):
    return {k:dict(key=list(k),people=30,effective_people=15,denominator_PA=10000,outs_per_PA=rate,DH_starts_per_PA=.02) for k in keys(r)}


def test_noncatcher_does_not_borrow_catcher_exposure():
    r=row();r.update(make_repertoire(r,[annual()]));r["carry_3"]=3000
    p=predict(r,prior(r));assert p["values"][0]==0 and sum(p["values"][1:8])==p["potential_total_outs"]
    assert all(p["values"][j]==0 for j,pos in enumerate(POSITIONS) if pos!=3)


def test_tiny_mlb_evidence_uses_full_minor_repertoire():
    r=row(5,"2");r.update(make_repertoire(r,[annual(pos=10,outs=0,starts=2),annual(mlb=False,pos=2,outs=2400)]))
    assert r["repertoire_primary_role"]==2 and r["repertoire_shares"][0]==1
    assert np.isclose(r["repertoire_weight"],5/105)


def test_latest_minor_record_removes_older_outfield_overhang():
    r=row(0);r.update(make_repertoire(r,[annual(2021,False,9),annual(2022,False,3)]))
    assert r["repertoire_fallback_season"]==2022 and r["repertoire_shares"][1]==1
    assert r["repertoire_shares"][7]==0


def test_current_mlb_regular_dominates_tiny_rehab_different_position():
    r=row();r.update(make_repertoire(r,[annual(pos=6),annual(mlb=False,pos=5,outs=27,starts=1)]))
    assert r["repertoire_primary_role"]==6 and r["repertoire_shares"][4]>r["repertoire_shares"][3]


def test_future_rows_do_not_change_repertoire():
    r=row();a=make_repertoire(r,[annual()]);b=make_repertoire(r,[annual(),annual(2023,False,2)])
    assert a==b


def test_no_history_unknown_role_keeps_potential_unallocated():
    r=row(0,"unknown");r.update(make_repertoire(r,[]));p=predict(r,prior(r))
    assert sum(p["values"][:8])==0 and p["unallocated_outs"]==3000


def test_DH_not_counted_as_defensive_outs():
    r=row(600,"10");r.update(make_repertoire(r,[annual(pos=10,outs=0)]));r["carry_10"]=100
    p=predict(r,prior(r));assert sum(p["values"][:8])==0 and p["values"][8]>0


def test_repeated_seasons_not_independent_people():
    tr=[dict(player_id=1,next_pa=500,repertoire_primary_role=3,repertoire_family="1B",stage="Current MLB") for _ in range(5)]
    c=mean_group(tr,("role","3"));assert c["rows"]==5 and c["people"]==1 and c["effective_people"]==1


def test_conditional_group_rejects_zero_PA():
    with pytest.raises(ValueError):mean_group([dict(player_id=1,next_pa=0)],("all",))


def test_zero_expected_PA_yields_no_defense_or_DH():
    r=row();r["preseason_pa"]=0;r.update(make_repertoire(r,[annual()]));p=predict(r,prior(r))
    assert sum(p["values"])==0


def test_defense_only_current_evidence_is_not_erased_by_zero_PA():
    r=row(0,"unknown");r.update(make_repertoire(r,[annual(pos=6,outs=3,starts=0)]))
    assert r["repertoire_shares"][4]==1
