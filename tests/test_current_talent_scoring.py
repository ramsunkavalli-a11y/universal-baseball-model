from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.current_talent_scoring import (
    project_latent_profiles_to_target_environment,
    score_current_talent_profiles,
)
from universal_baseball.performance_season import ALL_CORE_BINS


def _probabilities(*, k: float, bb: float) -> dict[str, float]:
    remainder = 1.0 - k - bb
    other_bins = [core_bin for core_bin in ALL_CORE_BINS if core_bin not in {"K", "BB_HBP"}]
    each = remainder / len(other_bins)
    return {
        core_bin: (k if core_bin == "K" else bb if core_bin == "BB_HBP" else each)
        for core_bin in ALL_CORE_BINS
    }


def _baseline_profile(
    baseline0: dict[str, float],
    baseline1: dict[str, float],
    *,
    player_id: int = 1,
) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "player_id": player_id,
                "core_bin": core_bin,
                "baseline0_latent_probability": baseline0[core_bin],
                "baseline1_latent_probability": baseline1[core_bin],
            }
            for core_bin in ALL_CORE_BINS
        ]
    )


def _offsets(*, rookie_k: float = 0.0, rookie_bb: float = 0.0) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for level_group in ("MLB", "ROOKIE_COMPLEX"):
        for core_bin in ALL_CORE_BINS:
            effect = 0.0
            if level_group == "ROOKIE_COMPLEX":
                if core_bin == "K":
                    effect = rookie_k
                elif core_bin == "BB_HBP":
                    effect = rookie_bb
            rows.append(
                {
                    "level_group": level_group,
                    "core_bin": core_bin,
                    "clr_environment_effect": effect,
                }
            )
    return pl.DataFrame(rows)


def _target_summary(*, level: str = "MLB", core_events: int = 100) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "player_id": [1],
            "target_season": [2021],
            "target_league_id": [103 if level == "MLB" else 130],
            "target_level_group": [level],
            "future_core_events": [core_events],
        }
    )


def test_zero_target_environment_effect_preserves_latent_profiles() -> None:
    baseline0 = _probabilities(k=0.30, bb=0.10)
    baseline1 = _probabilities(k=0.20, bb=0.12)
    projected = project_latent_profiles_to_target_environment(
        _baseline_profile(baseline0, baseline1),
        _target_summary(level="MLB"),
        _offsets(),
    )

    for core_bin in ALL_CORE_BINS:
        row = projected.filter(pl.col("core_bin") == core_bin).to_dicts()[0]
        assert row["baseline0_target_probability"] == pytest.approx(baseline0[core_bin])
        assert row["baseline1_target_probability"] == pytest.approx(baseline1[core_bin])


def test_forward_target_mapping_adds_environment_effect() -> None:
    latent = _probabilities(k=0.25, bb=0.10)
    neutral = project_latent_profiles_to_target_environment(
        _baseline_profile(latent, latent),
        _target_summary(level="ROOKIE_COMPLEX"),
        _offsets(),
    )
    adjusted = project_latent_profiles_to_target_environment(
        _baseline_profile(latent, latent),
        _target_summary(level="ROOKIE_COMPLEX"),
        _offsets(rookie_k=-0.40, rookie_bb=0.40),
    )

    neutral_k = neutral.filter(pl.col("core_bin") == "K").item(0, "baseline1_target_probability")
    adjusted_k = adjusted.filter(pl.col("core_bin") == "K").item(0, "baseline1_target_probability")
    neutral_bb = neutral.filter(pl.col("core_bin") == "BB_HBP").item(0, "baseline1_target_probability")
    adjusted_bb = adjusted.filter(pl.col("core_bin") == "BB_HBP").item(0, "baseline1_target_probability")

    assert adjusted_k < neutral_k
    assert adjusted_bb > neutral_bb
    assert adjusted.get_column("baseline1_target_probability").sum() == pytest.approx(1.0)


def test_proper_scores_reward_better_future_profile_and_reliability_is_exact() -> None:
    baseline0 = _probabilities(k=0.50, bb=0.05)
    baseline1 = _probabilities(k=0.20, bb=0.10)
    projected = project_latent_profiles_to_target_environment(
        _baseline_profile(baseline0, baseline1),
        _target_summary(level="MLB", core_events=100),
        _offsets(),
    )

    counts = {
        core_bin: int(round(baseline1[core_bin] * 100))
        for core_bin in ALL_CORE_BINS
    }
    # The chosen probabilities are exactly integer-valued at n=100.
    assert sum(counts.values()) == 100
    target_profile = pl.DataFrame(
        [
            {
                "player_id": 1,
                "target_season": 2021,
                "target_league_id": 103,
                "target_level_group": "MLB",
                "core_bin": core_bin,
                "future_occurrence_count": count,
            }
            for core_bin, count in counts.items()
            if count > 0
        ]
    )
    scoring_context = pl.DataFrame(
        {
            "player_id": [1],
            "target_season": [2021],
            "target_league_id": [103],
            "target_level_group": ["MLB"],
            "target_transition": ["SAME_LEVEL"],
        }
    )

    report = score_current_talent_profiles(
        projected,
        target_profile,
        scoring_context=scoring_context,
        calibration_bin_count=10,
    )
    metrics = {row["model"]: row for row in report.aggregate_metrics.iter_rows(named=True)}

    assert metrics["baseline1"]["event_weighted_log_loss"] < metrics["baseline0"]["event_weighted_log_loss"]
    assert metrics["baseline1"]["event_weighted_multinomial_brier"] < metrics["baseline0"]["event_weighted_multinomial_brier"]
    assert metrics["baseline1"]["future_core_events"] == 100
    assert report.metrics["scored_player_count"] == 1
    assert report.metrics["scored_target_environment_count"] == 1
    assert report.stratified_metrics.get_column("target_transition").unique().to_list() == ["SAME_LEVEL"]

    baseline1_calibration = report.component_calibration.filter(pl.col("model") == "baseline1")
    assert baseline1_calibration.filter(pl.col("absolute_calibration_error") > 1e-12).is_empty()
