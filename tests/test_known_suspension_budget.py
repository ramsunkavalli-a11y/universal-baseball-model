from copy import deepcopy

import pytest

from universal_baseball.known_suspension_budget import apply_to_role, budget


OBS = dict(hard_unavailable=False, observation_unresolved_channels={
    'suspended': dict(kind='suspended_unspecified', event_date='2022-08-12', duration_games=80, ambiguous=False)})
FACT = dict(player_id=1, target_year=2023, restriction_event_date='2022-08-12',
            known_date='2022-10-25', remaining_games_at_season_start=20, source_url='https://example.org/report')


def run(obs=None, facts=None, **extra):
    kwargs = dict(player_id=1, cutoff='2023-01-26', target_year=2023, season_games=162, season_start='2023-03-30')
    kwargs.update(extra)
    return budget(deepcopy(OBS) if obs is None else obs, [deepcopy(FACT)] if facts is None else facts, **kwargs)


def test_original_sentence_is_not_remaining_season_absence():
    r = run()
    assert r['original_sentence_games'] == 80 and r['eligible_games'] == 142
    assert r['known_suspension_fraction'] == pytest.approx(142 / 162)
    assert not r['medical_recovery_certified'] and not r['MLB_job_certified']


@pytest.mark.parametrize('field,value', [('known_date', '2023-02-01'), ('target_year', 2024),
                                         ('player_id', 2), ('restriction_event_date', '2021-08-12')])
def test_future_or_unmatched_fact_does_not_set_current_budget(field, value):
    assert run(facts=[dict(FACT, **{field: value})])['known_suspension_fraction'] is None


def test_parallel_restrictions_cannot_be_cleared_by_suspension_budget():
    obs = deepcopy(OBS)
    obs['observation_unresolved_channels']['restricted'] = dict(kind='restricted', event_date='2022-09-01')
    r = run(obs=obs)
    assert r['eligible_games'] == 142 and r['state'] == 'parallel_restriction_requires_scenarios'
    with pytest.raises(ValueError, match='scenarios'):
        apply_to_role(.97, 600, 2., r, excludes_known_suspension=True)


def test_scope_resolution_does_not_reapply_original_or_reported_sentence():
    r = run(obs=dict(hard_unavailable=False, observation_unresolved_channels={}))
    assert r['eligible_games'] == 162 and r['source_report'] is None
    assert apply_to_role(.8, 500, -1., r, excludes_known_suspension=True)['expected_pa'] == 400


def test_hard_unavailability_is_zero_not_medical_clearance():
    r = run(obs=dict(hard_unavailable=True, observation_unresolved_channels={
        'ineligible': dict(kind='permanent_ineligible', event_date='2022-08-12')}))
    result = apply_to_role(.9, 600, 2., r, excludes_known_suspension=True)
    assert result['probability'] == result['conditional_pa'] == result['expected_pa'] == 0
    assert result['hitting_rate'] == 2.


def test_missing_budget_does_not_mean_zero_lost_games():
    r = run(facts=[])
    assert r['state'] == 'finite_budget_unknown'
    with pytest.raises(ValueError, match='scenarios'):
        apply_to_role(.97, 600, 2., r, excludes_known_suspension=True)


def test_factor_reduces_work_once_not_appearance_twice():
    r = apply_to_role(.97, 600, 2., run(), excludes_known_suspension=True)
    assert r['probability'] == .97 and r['hitting_rate'] == 2.
    assert r['expected_pa'] == pytest.approx(.97 * 600 * 142 / 162)


def test_bad_existing_baseline_is_not_silently_adjusted_again():
    with pytest.raises(ValueError, match='independent'):
        apply_to_role(.1535, 400, 1.313, run(), excludes_known_suspension=False)


def test_conflicting_report_and_impossible_remaining_games_stop():
    with pytest.raises(ValueError, match='Conflicting'):
        run(facts=[FACT, dict(FACT, remaining_games_at_season_start=21)])
    with pytest.raises(ValueError, match='exceed'):
        run(facts=[dict(FACT, remaining_games_at_season_start=81)])


def test_inseason_use_and_future_legal_state_stop():
    with pytest.raises(ValueError, match='preseason'):
        run(cutoff='2023-04-20')
    obs = deepcopy(OBS)
    obs['observation_unresolved_channels']['suspended']['event_date'] = '2023-02-01'
    with pytest.raises(ValueError, match='future'):
        run(obs=obs)


@pytest.mark.parametrize('prob,pa,rate', [(-.1, 600, 1.), (1.1, 600, 1.), (.9, -1, 1.), (.9, 600, float('nan'))])
def test_invalid_role_input_stops(prob, pa, rate):
    with pytest.raises(ValueError, match='Invalid'):
        apply_to_role(prob, pa, rate, run(), excludes_known_suspension=True)


def test_full_season_finite_budget_is_not_a_permanent_ban():
    obs = deepcopy(OBS)
    obs['observation_unresolved_channels']['suspended']['duration_games'] = 200
    r = run(obs=obs, facts=[dict(FACT, remaining_games_at_season_start=200)])
    assert r['eligible_games'] == 0 and r['state'] == 'reported_finite_season_budget'
    assert apply_to_role(.9, 600, 2., r, excludes_known_suspension=True)['expected_pa'] == 0
