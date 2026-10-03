import pytest
from universal_baseball.shared_hitting_evidence import shared_deviation


def test_absent_level_does_not_invent_evidence():
    assert shared_deviation(0,0,500,.23)==0


def test_centered_evidence_conserves_counts_without_double_shrinkage():
    assert shared_deviation(10,50,550,.23)+shared_deviation(60,500,550,.23)==pytest.approx((70-550*.23)/650)


def test_minor_influence_falls_with_competing_mlb_evidence():
    assert abs(shared_deviation(40,500,500,.03))>abs(shared_deviation(40,500,2300,.03))


def test_reject_inconsistent_opportunity_counts():
    with pytest.raises(ValueError):shared_deviation(3,2,2,.23)
