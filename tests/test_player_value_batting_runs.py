from __future__ import annotations

import math

import polars as pl
import pytest

from universal_baseball.performance_season import ALL_CORE_BINS
from universal_baseball.player_value_batting_runs import (
    BATTING_RUN_CONVERSION_ID,
    build_v1_mlb_batting_reference,
    calculate_v1_projected_batting_runs,
)


def _synthetic_reference_frames() -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    summary = pl.DataFrame(
        {
            "season": [2024, 2024],
            "league_id": [103, 104],
            "batting_plate_appearances": [1200, 800],
            "core_profile_event_count": [1080, 720],
        }
    )

    profile_rows: list[dict[str, object]] = []
    value_rows: list[dict[str, object]] = []
    # 12 bins x 150 pooled occurrences = 1800 core events. AL/NL are 60/40.
    for index, core_bin in enumerate(ALL_CORE_BINS):
        for league_id, count in ((103, 90), (104, 60)):
            profile_rows.append(
                {
                    "season": 2024,
                    "league_id": league_id,
                    "core_bin": core_bin,
                    "occurrence_count": count,
                }
            )
            # Give each bin a distinct value and NL a small offset so pooling is testable.
            value_rows.append(
                {
                    "season": 2024,
                    "league_id": league_id,
                    "core_bin": core_bin,
                    "estimated_mean_run_value": (index - 5.5) / 10 + (0.05 if league_id == 104 else 0.0),
                    "estimator_certified": True,
                }
            )
    return summary, pl.DataFrame(profile_rows), pl.DataFrame(value_rows)


def _reference():
    summary, profile, values = _synthetic_reference_frames()
    return build_v1_mlb_batting_reference(summary, profile, values, season=2024)


def test_reference_pools_both_mlb_leagues_and_uses_fixed_coverage() -> None:
    reference = _reference()
    assert reference.batting_run_conversion_id == BATTING_RUN_CONVERSION_ID
    assert reference.core_event_rate_per_pa == pytest.approx(0.9)
    assert sum(reference.reference_probabilities.values()) == pytest.approx(1.0)
    assert all(
        probability == pytest.approx(1 / len(ALL_CORE_BINS))
        for probability in reference.reference_probabilities.values()
    )
    # AL/NL count weights are 60/40, so the +0.05 NL offset contributes +0.02.
    assert reference.bin_run_values[ALL_CORE_BINS[0]] == pytest.approx(-0.55 + 0.02)


def test_reference_composition_projects_to_exactly_zero_runs() -> None:
    reference = _reference()
    result = calculate_v1_projected_batting_runs(
        reference.reference_probabilities,
        projected_expected_mlb_pa=600,
        reference=reference,
    )
    assert result.projected_batting_runs_above_mlb_reference == pytest.approx(0.0, abs=1e-12)


def test_better_core_mix_scales_by_mlb_coverage_and_projected_pa() -> None:
    reference = _reference()
    probabilities = dict(reference.reference_probabilities)
    low_bin = ALL_CORE_BINS[0]
    high_bin = ALL_CORE_BINS[-1]
    shift = 0.05
    probabilities[low_bin] -= shift
    probabilities[high_bin] += shift

    result = calculate_v1_projected_batting_runs(
        probabilities,
        projected_expected_mlb_pa=500,
        reference=reference,
    )
    value_gap = reference.bin_run_values[high_bin] - reference.bin_run_values[low_bin]
    expected = 500 * 0.9 * shift * value_gap
    assert result.projected_batting_runs_above_mlb_reference == pytest.approx(expected)


def test_zero_projected_pa_produces_zero_runs() -> None:
    reference = _reference()
    result = calculate_v1_projected_batting_runs(
        reference.reference_probabilities,
        projected_expected_mlb_pa=0,
        reference=reference,
    )
    assert result.projected_batting_runs_above_mlb_reference == 0.0


def test_profile_summary_core_event_mismatch_is_rejected() -> None:
    summary, profile, values = _synthetic_reference_frames()
    summary = summary.with_columns(
        pl.when(pl.col("league_id") == 103)
        .then(pl.col("core_profile_event_count") + 1)
        .otherwise(pl.col("core_profile_event_count"))
        .alias("core_profile_event_count")
    )
    with pytest.raises(ValueError, match="reconcile"):
        build_v1_mlb_batting_reference(summary, profile, values, season=2024)


def test_uncertified_mlb_bin_value_is_rejected() -> None:
    summary, profile, values = _synthetic_reference_frames()
    values = values.with_columns(
        pl.when((pl.col("league_id") == 103) & (pl.col("core_bin") == ALL_CORE_BINS[0]))
        .then(False)
        .otherwise(pl.col("estimator_certified"))
        .alias("estimator_certified")
    )
    with pytest.raises(ValueError, match="certified"):
        build_v1_mlb_batting_reference(summary, profile, values, season=2024)


@pytest.mark.parametrize("bad_pa", [-1, math.inf, -math.inf, math.nan, "nope"])
def test_invalid_projected_pa_is_rejected(bad_pa: object) -> None:
    reference = _reference()
    with pytest.raises(ValueError, match="finite nonnegative"):
        calculate_v1_projected_batting_runs(
            reference.reference_probabilities,
            projected_expected_mlb_pa=bad_pa,
            reference=reference,
        )


def test_projection_probabilities_must_be_complete_simplex() -> None:
    reference = _reference()
    incomplete = dict(reference.reference_probabilities)
    incomplete.pop(ALL_CORE_BINS[0])
    with pytest.raises(ValueError, match="core-bin set mismatch"):
        calculate_v1_projected_batting_runs(
            incomplete,
            projected_expected_mlb_pa=500,
            reference=reference,
        )

    bad_sum = dict(reference.reference_probabilities)
    bad_sum[ALL_CORE_BINS[0]] += 0.01
    with pytest.raises(ValueError, match="sum to one"):
        calculate_v1_projected_batting_runs(
            bad_sum,
            projected_expected_mlb_pa=500,
            reference=reference,
        )
