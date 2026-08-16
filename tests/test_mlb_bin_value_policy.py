from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.mlb_bin_value_policy import (
    MLB_PRIOR_STRENGTH,
    estimate_certified_mlb_bin_values,
)


def _direct_values() -> pl.DataFrame:
    rows = []
    for league_id, adjustment in [(103, 0.00), (104, 0.02)]:
        for core_bin, mean, n in [
            ("BB_HBP", 0.30, 200),
            ("K", -0.05, 300),
            ("PULL_GB", 0.10, 120),
            ("CENTER_LD", 0.28, 60),
        ]:
            rows.append(
                {
                    "season": 2024,
                    "league_id": league_id,
                    "core_bin": core_bin,
                    "occurrence_count": n,
                    "mean_run_value": mean + adjustment,
                }
            )
    return pl.DataFrame(rows)


def test_mlb_values_use_pre_specified_peer_league_prior() -> None:
    result = estimate_certified_mlb_bin_values(_direct_values())
    row = result.filter(
        (pl.col("league_id") == 103) & (pl.col("core_bin") == "BB_HBP")
    ).to_dicts()[0]

    expected = (0.30 * 200 + 0.32 * MLB_PRIOR_STRENGTH) / (200 + MLB_PRIOR_STRENGTH)
    assert MLB_PRIOR_STRENGTH == 5
    assert row["level_group"] == "MLB"
    assert row["prior_strength"] == 5
    assert row["prior_environment_count"] == 1
    assert row["prior_source_occurrence_count"] == 200
    assert row["prior_mean_run_value"] == pytest.approx(0.32)
    assert row["estimated_mean_run_value"] == pytest.approx(expected)
    assert row["estimator_method"] == "certified_same_level_peer_pooling"
    assert row["estimator_certified"] is True


def test_mlb_policy_never_falls_back_without_peer_support() -> None:
    only_al = _direct_values().filter(pl.col("league_id") == 103)
    row = estimate_certified_mlb_bin_values(only_al).filter(
        pl.col("core_bin") == "BB_HBP"
    ).to_dicts()[0]
    assert row["estimated_mean_run_value"] == pytest.approx(0.30)
    assert row["prior_environment_count"] == 0
    assert row["prior_strength"] == 5
    assert row["estimator_method"] == "direct_missing_required_peer_support"
    assert row["estimator_certified"] is False


def test_mlb_policy_rejects_affiliated_leagues() -> None:
    bad = _direct_values().with_columns(
        pl.when(pl.col("league_id") == 103)
        .then(pl.lit(112))
        .otherwise(pl.col("league_id"))
        .alias("league_id")
    )
    with pytest.raises(ValueError, match="non-MLB league IDs"):
        estimate_certified_mlb_bin_values(bad)
