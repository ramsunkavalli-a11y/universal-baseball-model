"""Preseason game-budget arithmetic, independent of role and medical prognosis."""
from datetime import date
from math import isfinite


def day(value):
    return value if isinstance(value, date) else date.fromisoformat(value)


def whole(value, label, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError(f'Invalid {label}')
    if int(value) != value or value < int(positive):
        raise ValueError(f'Invalid {label}')
    return int(value)


def budget(observation, facts, *, player_id, cutoff, target_year, season_games, season_start):
    cutoff, start = day(cutoff), day(season_start)
    games = whole(season_games, 'season games', positive=True)
    if start.year != target_year or cutoff >= start:
        raise ValueError('Full-season budget requires a matching preseason cutoff')
    active = observation['observation_unresolved_channels']
    if any(day(r['event_date']) > cutoff for r in active.values()):
        raise ValueError('Restriction state contains a future event')
    if bool(observation['hard_unavailable']) != any(r['kind'] in {'permanent_ineligible', 'deceased'}
                                                 for r in active.values()):
        raise ValueError('Hard status and observation channels disagree')
    common = dict(target_year=target_year, season_games=games, current_channels=sorted(active),
        medical_recovery_certified=False, MLB_job_certified=False, forecast_changed=False,
        original_sentence_games=active.get('suspended', {}).get('duration_games'),
        source_report=None, known_suspension_fraction=None, eligible_games=None)
    if observation['hard_unavailable']:
        return dict(common, state='hard_unavailable', eligible_games=0, known_suspension_fraction=0.)
    if not active:
        return dict(common, state='no_current_observed_restriction', eligible_games=games,
                    known_suspension_fraction=1.)
    suspension = active.get('suspended')
    if suspension is None or suspension.get('ambiguous'):
        return dict(common, state='unresolved_nonmedical_requires_scenarios')
    sentence = suspension.get('duration_games')
    if sentence is not None:
        sentence = whole(sentence, 'original sentence', positive=True)
    matching = [r for r in facts if r['player_id'] == player_id and r['target_year'] == target_year
        and r['restriction_event_date'] == suspension['event_date'] and day(r['known_date']) <= cutoff]
    if not matching:
        return dict(common, state='finite_budget_unknown' if sentence is not None else 'duration_and_budget_unknown')
    for r in matching:
        if day(r['known_date']) < day(r['restriction_event_date']) or not r.get('source_url'):
            raise ValueError('Budget lacks valid dated source provenance')
    latest = max(day(r['known_date']) for r in matching)
    reports = [r for r in matching if day(r['known_date']) == latest]
    amounts = {whole(r['remaining_games_at_season_start'], 'remaining games') for r in reports}
    if len(amounts) != 1:
        raise ValueError('Conflicting same-date remaining-game reports')
    owed = next(iter(amounts))
    if sentence is not None and owed > sentence:
        raise ValueError('Remaining games exceed original sentence')
    # More than one season can be owed. Clamping is opportunity arithmetic,
    # not a claim that the remaining sentence has been served.
    eligible = max(0, games - owed)
    common.update(source_report=reports[0], eligible_games=eligible,
                  known_suspension_fraction=eligible / games)
    if set(active) != {'suspended'}:
        return dict(common, state='parallel_restriction_requires_scenarios')
    return dict(common, state='reported_finite_season_budget')


def apply_to_role(probability, conditional_pa, hitting_rate, evidence, *, excludes_known_suspension):
    if not excludes_known_suspension:
        raise ValueError('Already-adjusted opportunity cannot be used as an independent role baseline')
    if not all(isfinite(x) for x in [probability, conditional_pa, hitting_rate]) or not 0 <= probability <= 1 or conditional_pa < 0:
        raise ValueError('Invalid independent role projection')
    if evidence['state'] not in {'hard_unavailable', 'no_current_observed_restriction', 'reported_finite_season_budget'}:
        raise ValueError('Unresolved nonmedical evidence needs explicit scenarios, not an invented point factor')
    factor = evidence['known_suspension_fraction']
    if factor is None or not 0 <= factor <= 1:
        raise ValueError('Invalid opportunity fraction')
    adjusted_probability = probability if factor > 0 else 0.
    adjusted_conditional = conditional_pa * factor
    return dict(probability=adjusted_probability, conditional_pa=adjusted_conditional,
        expected_pa=adjusted_probability * adjusted_conditional, hitting_rate=hitting_rate,
        suspension_factor=factor, medical_and_role_risk_in_baseline=True,
        baseline_excludes_known_suspension=True)
