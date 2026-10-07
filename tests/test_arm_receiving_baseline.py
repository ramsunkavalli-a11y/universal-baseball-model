import pytest
from universal_baseball.arm_receiving_baseline import history


def row(year=2022,n=1,runs=.192277,valid=True):
    return dict(kind='arm',season=year,opportunities=n,runs=runs,isolated_outfield_quality_valid=valid)


def test_small_sample_shrinks_signal_not_just_a_feature():
    r=history('arm',[row()],2022)
    assert r['history']==pytest.approx(19.2277/301)
    assert r['reliability']==pytest.approx(1/301)


def test_future_and_invalid_sources_cannot_drive_prediction():
    r=history('arm',[row(2023),row(valid=False)],2022)
    assert r['history']==0 and not r['quality_evidence_observed']


def test_recency_and_cutoff():
    r=history('arm',[row(2022,100,1),row(2021,100,2),row(2020,100,4),row(2019,100,500)],2022)
    assert r['history_opportunities']==175 and r['history_runs']==3
    assert r['history']==pytest.approx(300/475)


def test_receiving_opportunities_are_throws_not_innings():
    s=dict(kind='receiving',season=2022,opportunities=600,runs=6,quality_valid=True)
    r=history('receiving',[s],2022)
    assert r['history']==.5 and r['reliability']==.5
