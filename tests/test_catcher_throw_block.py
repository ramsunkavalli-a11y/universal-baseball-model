import pytest

from universal_baseball.catcher_throw_block import normalize
from universal_baseball.catcher_throw_block_coverage import qualified
from universal_baseball.catcher_throw_block_baseline import history


def native(year=2022,kind='blocking',runs=.425):
    return dict(player_id=10,season=year,position=2,native_outs=100,exposure_valid=True,**{kind+'_runs':runs})


def blocking():
    return dict(player_id='10',player_name='Test',start_year='2022',end_year='',pitches='100',
                n_pbwp='2',x_pbwp='3.7',blocks_above_average_per_game='.68',blocks_above_average='2',catcher_blocking_runs='0',
                diff_pbwp_easy='.5',diff_pbwp_medium='.7',diff_pbwp_tough='.5',freq_pbwp_easy='.9',freq_pbwp_medium='.08',freq_pbwp_tough='.02')


def throwing(year=2022):
    return dict(player_id='10',player_name='Test',start_year=str(year),end_year=str(year),sb_attempts='10',n_cs='3',
        est_cs_pct='.2',rate_cs='.3',caught_stealing_above_average='1',cs_aa_per_throw='.1',catcher_stealing_runs='.65',
        pop_time='2',runner_distance_from_second='55',seasonal_runner_speed='28')


def test_blocking_uses_exact_expected_minus_observed_not_rounded_display():
    r=normalize('blocking',2022,blocking(),native())
    assert r['numerator']==pytest.approx(1.7) and r['runs']==pytest.approx(.425)
    assert r['opportunities']==100 and r['rate_per_1000']==pytest.approx(4.25)


def test_blocking_never_uses_framing_pitch_denominator():
    row=blocking();row['pitches']='200'
    with pytest.raises(AssertionError):normalize('blocking',2022,row,native())


def test_stale_year_stops():
    with pytest.raises(AssertionError):normalize('throwing',2021,throwing(),native(kind='throwing',runs=.65))


def test_native_run_disagreement_stops():
    with pytest.raises(AssertionError):normalize('blocking',2022,blocking(),native(runs=.6))


def test_expected_caught_stealing_identity():
    row=throwing();r=normalize('throwing',2022,row,native(kind='throwing',runs=.65))
    assert r['expected_events']==2 and r['numerator']==1
    row['est_cs_pct']='.25'
    with pytest.raises(AssertionError):normalize('throwing',2022,row,native(kind='throwing',runs=.65))


def test_early_context_mismatch_quarantined_not_zero_talent():
    row=throwing(2016);row['est_cs_pct']='.25'
    r=qualified('throwing',2016,row,native(2016,'throwing',.65))
    assert not r['measurement_valid'] and r['runs']==.65 and not r['context_identity_valid']


def test_new_context_incompatibility_requires_review():
    row=throwing();row['est_cs_pct']='.25'
    with pytest.raises(AssertionError):qualified('throwing',2022,row,native(kind='throwing',runs=.65))


def source(kind,year,n,runs,valid=True):
    return dict(component=kind,season=year,opportunities=n,runs=runs,measurement_valid=valid)


def test_tiny_sample_is_shrunk_inside_calculation():
    r=history('throwing',[source('throwing',2022,1,.65)],2022)
    assert r['history']==pytest.approx(65/101) and r['reliability']==pytest.approx(1/101)


def test_future_records_and_other_components_cannot_change_input():
    past=[source('blocking',2022,1000,1.)]
    assert history('blocking',past,2022)==history('blocking',past+[source('blocking',2023,5000,30),source('throwing',2022,10,8)],2022)


def test_quarantine_and_absent_history_are_unknown_evidence():
    r=history('throwing',[source('throwing',2016,50,20,False)],2016)
    assert r['history']==0 and not r['quality_evidence_observed']


def test_sample_accumulation_increases_evidence_not_opportunity_forecast():
    one=history('blocking',[source('blocking',2022,1000,1.)],2022)
    two=history('blocking',[source('blocking',2022,2000,2.)],2022)
    assert two['reliability']>one['reliability'] and two['history']>one['history']
    assert 'future_opportunities' not in two
