from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.current_talent_score_diagnostics import (
    add_diagnostic_bands,
    build_calibration_summary,
    build_component_proper_score_contributions,
    build_separate_stratified_metrics,
)
from universal_baseball.current_talent_scoring import score_current_talent_profiles
from universal_baseball.performance_season import ALL_CORE_BINS


def _probabilities(*, k: float, bb: float) -> dict[str, float]:
    other = [core_bin for core_bin in ALL_CORE_BINS if core_bin not in {"K", "BB_HBP"}]
    each = (1.0 - k - bb) / len(other)
    return {
        core_bin: k if core_bin == "K" else bb if core_bin == "BB_HBP" else each
        for core_bin in ALL_CORE_BINS
    }


def _projected_and_target() -> tuple[pl.DataFrame, pl.DataFrame]:
    b0 = _probabilities(k=0.50, bb=0.05)
    b1 = _probabilities(k=0.20, bb=0.10)
    projected = pl.DataFrame(
        [
            {
                "player_id": 1,
                "target_season": 2021,
                "target_league_id": 103,
                "target_level_group": "MLB",
                "future_core_events": 100,
                "core_bin": core_bin,
                "baseline0_target_probability": b0[core_bin],
                "baseline1_target_probability": b1[core_bin],
            }
            for core_bin in ALL_CORE_BINS
        ]
    )
    target = pl.DataFrame(
        [
            {
                "player_id": 1,
                "target_season": 2021,
                "target_league_id": 103,
                "target_level_group": "MLB",
                "core_bin": core_bin,
                "future_occurrence_count": int(round(b1[core_bin] * 100)),
            }
            for core_bin in ALL_CORE_BINS
            if int(round(b1[core_bin] * 100)) > 0
        ]
    )
    return projected, target


def test_fixed_diagnostic_bands_are_descriptive_only() -> None:
    context = pl.DataFrame(
        {
            "age_years": [19.9, 21.0, 23.0, 25.0, 30.0],
            "effective_core_events_translated": [10.0, 30.0, 75.0, 150.0, 250.0],
        }
    )
    result = add_diagnostic_bands(context)
    assert result.get_column("age_band").to_list() == ["<20", "20-21.9", "22-23.9", "24-26.9", "27+"]
    assert result.get_column("evidence_band").to_list() == ["<25", "25-49", "50-99", "100-199", "200+"]


def test_component_contributions_sum_to_aggregate_proper_scores() -> None:
    projected, target = _projected_and_target()
    report = score_current_talent_profiles(projected, target)
    components = build_component_proper_score_contributions(projected, target)

    aggregate = {row["model"]: row for row in report.aggregate_metrics.iter_rows(named=True)}
    summed = components.group_by("model").agg(
        pl.col("multinomial_log_loss_contribution").sum().alias("log_loss"),
        pl.col("binary_brier_contribution").sum().alias("brier"),
    )
    for row in summed.iter_rows(named=True):
        model = row["model"]
        assert row["log_loss"] == pytest.approx(aggregate[model]["event_weighted_log_loss"])
        assert row["brier"] == pytest.approx(aggregate[model]["event_weighted_multinomial_brier"])

    calibration_summary = build_calibration_summary(report.component_calibration)
    b1 = calibration_summary.filter(pl.col("model") == "baseline1")
    assert b1.filter(pl.col("event_weighted_expected_calibration_error") > 1e-12).is_empty()


def test_separate_strata_do_not_require_cross_product_groups() -> None:
    environment_scores = pl.DataFrame(
        {
            "player_id": [1, 1, 2, 2],
            "target_season": [2021] * 4,
            "target_league_id": [103] * 4,
            "target_level_group": ["MLB"] * 4,
            "model": ["baseline0", "baseline1", "baseline0", "baseline1"],
            "future_core_events": [100, 100, 50, 50],
            "log_loss": [2.3, 2.2, 2.4, 2.3],
            "multinomial_brier": [0.88, 0.86, 0.90, 0.89],
            "target_transition": ["SAME_LEVEL", "SAME_LEVEL", "PROMOTION", "PROMOTION"],
        }
    )
    context = add_diagnostic_bands(
        pl.DataFrame(
            {
                "player_id": [1, 2],
                "target_season": [2021, 2021],
                "target_league_id": [103, 103],
                "target_level_group": ["MLB", "MLB"],
                "age_years": [25.0, 19.0],
                "effective_core_events_translated": [150.0, 20.0],
            }
        )
    )
    result = build_separate_stratified_metrics(environment_scores, context)
    assert set(result.get_column("stratum_type").unique().to_list()) == {
        "target_level_group",
        "target_transition",
        "age_band",
        "evidence_band",
    }
    assert result.filter(
        (pl.col("stratum_type") == "target_transition")
        & (pl.col("stratum_value") == "SAME_LEVEL")
        & (pl.col("model") == "baseline1")
    ).item(0, "event_weighted_log_loss") == pytest.approx(2.2)
