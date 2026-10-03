import polars as pl
import pytest

from universal_baseball.forecast_validation import claim_status, preflight


def fixtures():
    train = pl.DataFrame({'row_id': [0, 1, 2], 'player_id': [1, 1, 2], 'origin_year': [2010, 2011, 2011],
        'horizon': [6]*3, 'target_year': [2016, 2017, 2017], 'outer_fold': [0, 0, 1],
        'elapsed': [0, 1, 0], 'age': [22., 23., 24.], 'current_state': [3, 3, 1],
        'regular_window': [0, 1, 0], 'quality_0': [0., 1., -.5], 'window_complete': [True]*3,
        'next_pa': [10, 600, 0], 'next_value': [0., 3., 0.]})
    test = pl.DataFrame({'row_id': [3], 'player_id': [3], 'origin_year': [2017], 'horizon': [6],
        'target_year': [2023], 'outer_fold': [2], 'elapsed': [5], 'age': [27.], 'current_state': [3],
        'regular_window': [3], 'quality_0': [1.5], 'window_complete': [True], 'next_pa': [600], 'next_value': [4.]})
    return train, test


def run(train, test, keys=((3, 6),)):
    return preflight(train, test, cutoff=2017, fold=2, features=['quality_0'], expected_keys=keys)


def test_original_failure_cannot_pass_by_repeating_training_rows():
    a, b = fixtures()
    rows, note = run(a, b)
    assert note['integrity_pass']
    assert note['max_training_elapsed'] == 1
    assert note['elapsed_outside'] == 1
    assert not note['full_cohort_profile_check_pass']
    assert rows['current_players'].item() == 1  # two seasons, one player
    assert claim_status(integrity=True, full_profile_support=False, predictive_gates=True, coherent=True).startswith('unsupported')


def test_support_is_not_selected_using_future_results():
    a, b = fixtures()
    original = run(a, b)[0]
    changed = run(a, b.with_columns(pl.lit(0).alias('next_pa'), pl.lit(0.).alias('next_value')))[0]
    assert original.equals(changed)


@pytest.mark.parametrize('change,message', [
    (lambda a: a.with_columns(pl.lit(2).alias('outer_fold')), 'Held-player'),
    (lambda a: a.with_columns(pl.when(pl.col('player_id') == 1).then(3).otherwise(pl.col('player_id')).alias('player_id')), 'Held-player'),
    (lambda a: a.with_columns(pl.lit(False).alias('window_complete')), 'history'),
    (lambda a: a.with_columns(pl.lit(2018).alias('target_year')), 'horizon'),
    (lambda a: a.with_columns(pl.lit(2026).alias('target_year')), 'Protected'),
])
def test_integrity_failures_stop_execution(change, message):
    a, b = fixtures()
    with pytest.raises(ValueError, match=message):
        run(change(a), b)


def test_dropping_difficult_evaluation_player_is_forbidden():
    a, b = fixtures()
    with pytest.raises(ValueError, match='population changed'):
        run(a, b, keys=((3, 6), (4, 6)))


def test_duplicate_and_impossible_labels_are_forbidden():
    a, b = fixtures()
    with pytest.raises(ValueError, match='duplicate'):
        run(pl.concat([a, a.head(1)]), b)
    with pytest.raises(ValueError, match='delivered-value'):
        run(a, b.with_columns(pl.lit(0).alias('next_pa')))


def test_passing_code_and_scores_never_implies_deployment():
    assert claim_status(integrity=True, full_profile_support=True, predictive_gates=True, coherent=True) == 'development_evidence_only_requires_separate_deployment_review'
    assert claim_status(integrity=True, full_profile_support=True, predictive_gates=True, coherent=False) == 'incoherent_forecast_not_promotable'
