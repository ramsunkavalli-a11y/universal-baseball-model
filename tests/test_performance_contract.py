from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.performance_contract import (
    BATTING_PERFORMANCE_CONTRACT_VERSION,
    validate_batting_performance_contract,
)


def _summary() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2024],
            "league_id": [112],
            "player_id": [10],
            "batting_plate_appearances": [100],
            "bb_hbp_count": [12],
            "strikeout_count": [20],
            "aggregate_contact_count": [65],
            "contact_event_count": [65],
            "core_contact_count": [50],
            "bunt_contact_count": [5],
            "foul_air_excluded_count": [4],
            "unknown_contact_count": [6],
            "official_overlay_contact_count": [2],
            "core_profile_event_count": [82],
            "core_profile_uncovered_pa_count": [18],
            "core_profile_coverage_rate": [0.82],
            "contact_count_residual_vs_aggregate": [0],
            "valued_core_event_count": [82],
            "unvalued_core_event_count": [0],
            "core_expected_run_value_total": [4.2],
            "core_expected_run_value_per_100_pa": [4.2],
            "has_uncertified_or_missing_bin_value": [False],
        }
    )


def _profile() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2024, 2024],
            "league_id": [112, 112],
            "player_id": [10, 10],
            "core_bin": ["BB_HBP", "K"],
            "occurrence_count": [12, 20],
            "batting_plate_appearances": [100, 100],
            "share_of_plate_appearances": [0.12, 0.20],
            "estimated_mean_run_value": [0.30, -0.05],
            "expected_run_value": [3.6, -1.0],
            "estimator_method": [
                "certified_same_level_peer_pooling",
                "certified_same_level_peer_pooling",
            ],
            "estimator_certified": [True, True],
        }
    )


def _values() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2024, 2024],
            "league_id": [112, 112],
            "core_bin": ["BB_HBP", "K"],
            "estimated_mean_run_value": [0.30, -0.05],
            "estimator_method": [
                "certified_same_level_peer_pooling",
                "certified_same_level_peer_pooling",
            ],
            "estimator_certified": [True, True],
            "prior_strength": [25, 25],
            "direct_occurrence_count": [200, 300],
        }
    )


def test_valid_contract_returns_stable_version_and_metrics() -> None:
    metrics = validate_batting_performance_contract(_summary(), _profile(), _values())
    assert metrics["contract_version"] == BATTING_PERFORMANCE_CONTRACT_VERSION
    assert metrics["summary_row_count"] == 1
    assert metrics["total_plate_appearances"] == 100
    assert metrics["core_profile_coverage_rate"] == pytest.approx(0.82)


def test_contract_allows_additive_diagnostic_columns() -> None:
    summary = _summary().with_columns(pl.lit("extra").alias("new_diagnostic"))
    validate_batting_performance_contract(summary, _profile(), _values())


def test_contract_rejects_covered_uncovered_pa_mismatch() -> None:
    summary = _summary().with_columns(
        pl.lit(17).alias("core_profile_uncovered_pa_count")
    )
    with pytest.raises(ValueError, match="covered \+ uncovered"):
        validate_batting_performance_contract(summary, _profile(), _values())


def test_contract_rejects_uncertified_values_for_production() -> None:
    values = _values().with_columns(
        pl.when(pl.col("core_bin") == "K")
        .then(pl.lit(False))
        .otherwise(pl.col("estimator_certified"))
        .alias("estimator_certified")
    )
    with pytest.raises(ValueError, match="requires certified bin values"):
        validate_batting_performance_contract(_summary(), _profile(), values)


def test_contract_can_validate_diagnostic_uncertified_output_when_explicitly_allowed() -> None:
    values = _values().with_columns(pl.lit(False).alias("estimator_certified"))
    validate_batting_performance_contract(
        _summary(), _profile(), values, require_certified_values=False
    )


def test_contract_rejects_profile_player_orphans() -> None:
    profile = _profile().with_columns(pl.lit(999).alias("player_id"))
    with pytest.raises(ValueError, match="absent from summary"):
        validate_batting_performance_contract(_summary(), profile, _values())
