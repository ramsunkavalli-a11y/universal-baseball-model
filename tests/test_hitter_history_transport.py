import numpy as np
import polars as pl
import pytest
from universal_baseball.hitter_history_transport import (
    transform,
    fit_effects,
    normalize_history,
    transition_matrix,
    OUTCOMES,
)


def test_transport_roundtrip_and_rare_conditional_ratios():
    p = np.random.default_rng(3).dirichlet(np.ones(12), 20)
    d = np.array([0.2, -0.1, 0.3, -0.2])
    q = transform(p, d)
    assert np.allclose(transform(q, -d), p)
    assert np.allclose(q.sum(axis=1), 1)
    for a, b in [("3B", "1B"), ("FC_REACH", "ROE"), ("SF", "OTHER_OUT")]:
        i, j = OUTCOMES.index(a), OUTCOMES.index(b)
        assert np.allclose(p[:, i] / p[:, j], q[:, i] / q[:, j])
    zero = np.zeros((1, 12))
    zero[0, OUTCOMES.index("OTHER_OUT")] = 1
    assert np.allclose(transform(zero, d), zero)


def history():
    p = np.ones(12) / 12
    return pl.DataFrame(
        [
            {
                "player_id": i,
                "season": y,
                "league_id": 1,
                "level_group": level,
                **dict(zip(OUTCOMES, p * 120)),
            }
            for i in range(10)
            for y in [2021, 2022]
            for level in ["AAA", "MLB"]
        ]
    )


def test_same_season_effects_zero_when_performance_identical():
    h = history()
    effects, _ = fit_effects(h, 2022)
    assert np.allclose(effects, 0)
    assert np.allclose(
        normalize_history(h, effects).select(OUTCOMES).to_numpy(),
        h.select(OUTCOMES).to_numpy(),
    )
    with pytest.raises(ValueError, match="cutoff"):
        fit_effects(h, 2021)


def test_aliases_and_zero_evidence_do_not_create_information():
    h = history().with_columns(
        pl.lit("HIGH_A").alias("level_group"), *[pl.lit(0.0).alias(o) for o in OUTCOMES]
    )
    assert (
        normalize_history(h, np.ones((6, 4)) * 0.1).select(OUTCOMES).to_numpy().sum()
        == 0
    )


def test_transitions_use_only_adjacent_observed_years():
    h = history()
    matrix, support = transition_matrix(h, 2022)
    assert np.allclose(matrix.sum(axis=1), 1)
    assert sum(support) == 10
    # Removing the adjacent year creates no imaginary observations across the gap.
    gap = h.with_columns(
        pl.when(pl.col("season") == 2022)
        .then(2023)
        .otherwise(pl.col("season"))
        .alias("season")
    )
    matrix, support = transition_matrix(gap, 2023)
    assert sum(support) == 0
    assert np.allclose(matrix, np.eye(6))
