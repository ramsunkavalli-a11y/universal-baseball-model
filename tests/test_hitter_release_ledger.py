from dataclasses import replace
from datetime import date
import pytest

from universal_baseball.hitter_release_ledger import (
    COMPONENTS, ComponentEstimate, annual_ledger, batting_rate_from_legacy, control_value)

CUTOFF = date(2026,10,8)


def estimates():
    rows = [ComponentEstimate(c,'whole_player',0.,0.,1.,'specified_opportunities',
            'not_applicable','test_only','synthetic_fixture',CUTOFF) for c in sorted(COMPONENTS)]
    values = {'batting':20.,'stealing':2.,'advancement':1.,'range':4.,'position':-10.,'replacement':20.}
    return [replace(r,runs_per_unit=values[r.component],opportunities=1.,evidence_tier='individual_history')
            if r.component in values else r for r in rows]


def ledger(rows=None, **kwargs):
    return annual_ledger(player_id=1,season=2027,as_of=CUTOFF,
        estimates=estimates() if rows is None else rows,runs_per_win=kwargs.get('runs_per_win',10.),
        fielding_reference=kwargs.get('fielding_reference','position_relative'),
        batting_reference=kwargs.get('batting_reference','park_neutral'),deployment_status='development')


def test_exact_sum_replacement_once_and_negative_value_retained():
    result=ledger()
    assert result['war']==pytest.approx(3.7)
    assert sum(result['component_war'].values())==pytest.approx(result['war'])
    assert result['component_runs']['position']==-10
    rows=[replace(r,runs_per_unit=-100.) if r.component=='batting' else r for r in estimates()]
    assert ledger(rows)['war']<0


def test_legacy_batting_conversion_does_not_relabel_fixed_win_units():
    assert batting_rate_from_legacy(1.17)==pytest.approx(11.7)
    assert ledger(runs_per_win=9.)['war']==pytest.approx(37/9)


def test_missing_duplicate_or_future_component_blocked():
    with pytest.raises(ValueError,match='Every component'):
        ledger(estimates()[:-1])
    with pytest.raises(ValueError,match='Duplicate'):
        ledger(estimates()+estimates()[:1])
    with pytest.raises(ValueError,match='Future'):
        ledger([replace(r,source_cutoff=date(2027,1,1)) for r in estimates()])


def test_native_range_reference_and_double_park_adjustment_blocked():
    with pytest.raises(ValueError,match='positional reference'):
        ledger(fielding_reference='intrinsic')
    rows=[replace(r,runs_per_unit=1.,opportunities=1.,evidence_tier='accounting_reference')
          if r.component=='park' else r for r in estimates()]
    with pytest.raises(ValueError,match='another park'):
        ledger(rows)


def test_explicit_profile_estimate_is_not_missing_or_individual_measurement():
    rows=[replace(r,evidence_tier='comparable_players') if r.component=='range' else r for r in estimates()]
    assert ledger(rows)['comparable_player_components']==['range']


def test_abs_catcher_value_is_separate_from_framing():
    rows=[replace(r,runs_per_unit=2.,opportunities=1.,evidence_tier='individual_history')
          if r.component=='abs_challenge' else r for r in estimates()]
    assert ledger(rows)['war']==pytest.approx(3.9)
    assert ledger(rows)['component_runs']['framing']==0.


def value(**overrides):
    args=dict(seasons=[2027,2028,2029],first_season=2027,
              war_paths=[[0.,2.,3.]],rights_paths=[[1.,1.,0.]],obligation_paths=[[1e6,2e6,3e6]],
              tail_complete=True,breakpoints=[],rates=[10e6],discount_rate=0.,
              assumptions={k:'explicit_test_scenario' for k in ['control_source','contract_source','rules_scenario','pricing_scenario','path_model']})
    args.update(overrides)
    return control_value(**args)


def test_costs_when_no_play_and_after_rights_end():
    result=value()
    assert result['mean_controlled_war']==2.
    assert result['mean_gross_value']==20e6
    assert result['mean_cost']==6e6
    assert result['mean_surplus']==14e6


def test_incomplete_tail_and_hitter_only_two_way_contract_not_full_value():
    assert value(tail_complete=False)['mean_surplus'] is None
    assert value(two_way_player=True)['mean_surplus'] is None


def test_irregular_years_and_array_truncation_blocked():
    with pytest.raises(ValueError,match='Consecutive'):
        value(seasons=[2027,2029,2030])
    with pytest.raises(ValueError,match='calendar years'):
        value(war_paths=[[2.,3.]])


def test_price_paths_before_averaging_and_preserve_negative_surplus():
    r=value(war_paths=[[0.,0.,0.],[4.,0.,0.]],rights_paths=[[1.,0.,0.],[1.,0.,0.]],
            obligation_paths=[[15e6,0.,0.],[15e6,0.,0.]],breakpoints=[2.],rates=[5e6,15e6])
    assert r['mean_gross_value']==20e6
    assert r['surplus_paths']==[-15e6,25e6]


def test_delayed_arrival_control_can_extend_beyond_six_calendar_years():
    years=list(range(2027,2035))
    r=value(seasons=years,war_paths=[[0.,0.,1.,1.,1.,1.,1.,1.]],rights_paths=[[1.]*8],obligation_paths=[[0.]*8])
    assert r['mean_controlled_war']==6.
    assert r['seasons'][-1]==2034
