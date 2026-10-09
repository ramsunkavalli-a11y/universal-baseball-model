import pytest
from universal_baseball.hitter_defense_rates_v1 import DefenseRates


def model(**kwargs):
    return DefenseRates(origin=2026,native=kwargs.get('native',[]),framing=kwargs.get('framing',[]),
        catcher=kwargs.get('catcher',[]),arm_receiving=kwargs.get('arm_receiving',[]))


def test_unknown_is_prior_not_observed_and_no_awarded_runs():
    rows=model().player(10)
    assert len(rows)==12
    assert all(r['evidence_tier']=='comparable' and not r['individual_evidence_observed'] for r in rows)
    assert all(r['projected_runs'] is None and r['projected_opportunities'] is None for r in rows)


def test_catcher_rates_use_different_opportunities():
    f=[dict(season=2026,player_id=10,framing_measurement_valid=True,pitches=6000,framing_runs=6.)]
    c=[dict(season=2026,player_id=10,component='throwing',measurement_valid=True,opportunities=100,runs=4.),
       dict(season=2026,player_id=10,component='blocking',measurement_valid=True,opportunities=3000,runs=-3.)]
    rows={r['component']:r for r in model(framing=f,catcher=c).player(10)}
    assert rows['framing']['runs_per_unit']==.5
    assert rows['catcher_throwing']['runs_per_unit']==2.
    assert rows['blocking']['runs_per_unit']==-.5


def test_recent_history_and_isolated_arm_scope():
    a=[dict(season=2025,player_id=10,kind='arm',isolated_outfield_quality_valid=True,opportunities=200,runs=4.),
       dict(season=2026,player_id=10,kind='arm',isolated_outfield_quality_valid=False,opportunities=100,runs=100.)]
    row=next(r for r in model(arm_receiving=a).player(10) if r['component']=='arm')
    assert row['weighted_history_opportunities']==100.
    assert row['runs_per_unit']==.5


def test_future_and_duplicate_sources_fail():
    r=dict(season=2027,player_id=10,position=3)
    with pytest.raises(ValueError,match='Future'):model(native=[r])
    r=dict(season=2026,player_id=10,position=3,range_valid=False)
    with pytest.raises(ValueError,match='Duplicate'):model(native=[r,r])


def test_outfield_centers_before_shrinking():
    native=[dict(season=2026,player_id=10,position=8,range_valid=True,native_outs=100,range_runs=1.),
            dict(season=2026,player_id=11,position=8,range_valid=True,native_outs=100,range_runs=1.)]
    row=next(r for r in model(native=native).player(10) if r['component']=='range' and r['context']=='8')
    assert row['runs_per_unit']==0.
    assert row['individual_evidence_observed']
