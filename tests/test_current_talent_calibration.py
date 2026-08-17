from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.current_talent_calibration import (
    build_component_calibration_coefficients,
)
from universal_baseball.performance_season import ALL_CORE_BINS


def _ideal_projected_and_target() -> tuple[pl.DataFrame, pl.DataFrame]:
    projected_rows: list[dict[str, object]] = []
    target_rows: list[dict[str, object]] = []
    k_probabilities = [0.10, 0.20, 0.30, 0.40]
    opportunities = 11_000
    other_bins = [core_bin for core_bin in ALL_CORE_BINS if core_bin != "K"]

    for player_id, k_probability in enumerate(k_probabilities, start=1):
        other_probability = (1.0 - k_probability) / len(other_bins)
        # Explicit rounding avoids a synthetic-fixture artifact such as
        # 0.063636... * 11000 evaluating to 699.999999999 instead of 700.
        k_count = int(round(k_probability * opportunities))
        other_count = int(round(other_probability * opportunities))
        assert k_count + other_count * len(other_bins) == opportunities
        for core_bin in ALL_CORE_BINS:
            probability = k_probability if core_bin == "K" else other_probability
            count = k_count if core_bin == "K" else other_count
            projected_rows.append(
                {
                    "player_id": player_id,
                    "target_season": 2021,
                    "target_league_id": 103,
                    "target_level_group": "MLB",
                    "future_core_events": opportunities,
                    "core_bin": core_bin,
                    "baseline0_target_probability": probability,
                    "baseline1_target_probability": probability,
                }
            )
            target_rows.append(
                {
                    "player_id": player_id,
                    "target_season": 2021,
                    "target_league_id": 103,
                    "target_level_group": "MLB",
                    "core_bin": core_bin,
                    "future_occurrence_count": count,
                }
            )
    return pl.DataFrame(projected_rows), pl.DataFrame(target_rows)


def test_ideal_component_forecasts_have_zero_intercept_unit_slope() -> None:
    projected, target = _ideal_projected_and_target()
    result = build_component_calibration_coefficients(projected, target)

    assert result.height == 2 * len(ALL_CORE_BINS)
    assert result.filter(~pl.col("converged")).is_empty()
    assert result.get_column("calibration_intercept").abs().max() == pytest.approx(
        0.0,
        abs=1e-9,
    )
    assert (
        result.get_column("calibration_slope") - 1.0
    ).abs().max() == pytest.approx(0.0, abs=1e-9)
    assert result.get_column("absolute_intercept_error").max() == pytest.approx(
        0.0,
        abs=1e-9,
    )
    assert result.get_column("absolute_slope_error").max() == pytest.approx(
        0.0,
        abs=1e-9,
    )


def test_calibration_coefficients_reject_invalid_grouped_counts() -> None:
    projected, target = _ideal_projected_and_target()
    bad = target.with_columns(
        pl.when((pl.col("player_id") == 1) & (pl.col("core_bin") == "K"))
        .then(pl.lit(20_000))
        .otherwise(pl.col("future_occurrence_count"))
        .alias("future_occurrence_count")
    )
    with pytest.raises(ValueError, match="invalid grouped-binomial counts"):
        build_component_calibration_coefficients(projected, bad)


def test_flatter_observed_relationship_yields_calibration_slope_below_one() -> None:
    projected, target = _ideal_projected_and_target()
    # For K only, pull realized rates halfway toward 0.25 while leaving predicted
    # probabilities unchanged. That makes the predictions too dispersed.
    adjusted = target.with_columns(
        pl.when(pl.col("core_bin") == "K")
        .then(
            pl.when(pl.col("player_id") == 1)
            .then(pl.lit(1925))
            .when(pl.col("player_id") == 2)
            .then(pl.lit(2475))
            .when(pl.col("player_id") == 3)
            .then(pl.lit(3025))
            .otherwise(pl.lit(3575))
        )
        .otherwise(pl.col("future_occurrence_count"))
        .alias("future_occurrence_count")
    )
    result = build_component_calibration_coefficients(projected, adjusted)
    k = result.filter((pl.col("model") == "baseline1") & (pl.col("core_bin") == "K"))
    assert k.item(0, "converged")
    assert 0.0 < k.item(0, "calibration_slope") < 1.0
