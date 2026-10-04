"""Focused safeguards against misleading exported forecasts."""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from verify_hitter_risk_research_explorer import validate_row


def example():
    source = dict(row_id=1, player_id=10, player_name='Example', target_year=2025,
        preseason_rate=1.2, preseason_p=.5, preseason_conditional_pa=200.,
        preseason_pa=100., origin_replacement_rate=.003, preseason_value=.5,
        next_pa=0., next_value=0., next_batting_rate=0.)
    row = dict(row_id=1, player_id=10, player_name='Example', target_year=2025,
        origin_year=2024, rate=1.2, p=.5, conditional_pa=200., pa=100.,
        replacement_rate=.003, value=.5, next_pa=0., next_value=0., next_rate=None,
        ranges={a: [0., 0., 2., 0., .1, 0.] for a in ['associated','independent','normal','fixed']})
    for a in row['ranges']:
        for name, value in zip(['q10','q50','q90','p_negative','p_two','impossible_mass'], row['ranges'][a]):
            source[a+'_'+name] = value
    return row, source


def test_valid_nonarrival_is_unobserved_rate_not_zero_talent():
    row, source = example()
    validate_row(row, source)
    assert row['rate'] > 0 and row['next_rate'] is None


@pytest.mark.parametrize('key,value', [('next_rate', 0.), ('pa', 101.), ('rate', 1.21),
    ('player_id', 11), ('value', .6), ('target_year', 2026)])
def test_export_drift_and_future_targets_rejected(key, value):
    row, source = example(); row[key] = value
    with pytest.raises(AssertionError):
        validate_row(row, source)


def test_active_value_uses_identical_reference_and_rate():
    row, source = example()
    source.update(next_pa=300., next_value=1.5, next_batting_rate=1.2)
    row.update(next_pa=300., next_value=1.5, next_rate=1.2)
    validate_row(row, source)
    wrong = copy.deepcopy(row); wrong['replacement_rate'] = .004
    with pytest.raises(AssertionError):
        validate_row(wrong, source)


def test_coherent_law_cannot_claim_impossible_outcome_mass():
    row, source = example()
    row['ranges']['associated'][-1] = source['associated_impossible_mass'] = .01
    with pytest.raises(AssertionError):
        validate_row(row, source)
