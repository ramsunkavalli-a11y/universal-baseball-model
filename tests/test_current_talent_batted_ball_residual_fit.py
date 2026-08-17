from datetime import date
import math

import polars as pl
import pytest

from universal_baseball.current_talent_batted_ball_residual_fit import (
    FIXED_RESIDUAL_L2_PENALTY,
    build_batted_ball_residual_training_table,
    fit_batted_ball_residual_coefficients,
)
from universal_baseball.performance_season import ALL_CORE_BINS, CONTACT_CORE_BINS


B2_WEIGHTS = {
    "BB_HBP": 0.10,
    "K": 0.20,
    "IFFB": 0.05,
    "PULL_OFFB": 0.08,
    "CENTER_OFFB": 0.07,
    "OPPO_OFFB": 0.05,
    "PULL_LD": 0.08,
    "CENTER_LD": 0.09,
    "OPPO_LD": 0.06,
    "PULL_GB": 0.09,
    "CENTER_GB": 0.08,
    "OPPO_GB": 0.05,
}


def _b2_profile(player_ids: tuple[int, ...] = (1, 2)) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "player_id": player_id,
                "core_bin": core_bin,
                "baseline2_latent_probability": B2_WEIGHTS[core_bin],
            }
            for player_id in player_ids
            for core_bin in ALL_CORE_BINS
        ]
    )


def _offsets() -> pl.DataFrame:
    rows = []
    for level in ("AAA", "MLB"):
        for core_bin in ALL_CORE_BINS:
            effect = 0.0
            if level == "AAA" and core_bin == "PULL_LD":
                effect = 0.20
            elif level == "AAA" and core_bin == "OPPO_GB":
                effect = -0.20
            rows.append(
                {
                    "level_group": level,
                    "core_bin": core_bin,
                    "clr_environment_effect": effect,
                }
            )
    return pl.DataFrame(rows)


def _standardized_features(*, cutoff: date = date(2021, 7, 15)) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "as_of_date": [cutoff, cutoff],
            "player_id": [1, 2],
            "tracked_bbe_eligible": [True, False],
            "z_mean_exit_velocity": [1.0, -1.0],
            "z_sweet_spot_share": [0.5, -0.5],
        }
    )


def _targets(*, cutoff: date = date(2021, 7, 15)) -> tuple[pl.DataFrame, pl.DataFrame]:
    summary = pl.DataFrame(
        [
            {
                "as_of_date": cutoff,
                "player_id": player_id,
                "target_season": 2021,
                "target_league_id": 11,
                "target_level_group": "AAA",
                "future_core_events": 100,
            }
            for player_id in (1, 2)
        ]
    )
    counts = {"BB_HBP": 10, "K": 20, **{core_bin: 7 for core_bin in CONTACT_CORE_BINS}}
    profile = pl.DataFrame(
        [
            {
                "as_of_date": cutoff,
                "player_id": player_id,
                "target_season": 2021,
                "target_league_id": 11,
                "target_level_group": "AAA",
                "core_bin": core_bin,
                "future_occurrence_count": counts[core_bin],
            }
            for player_id in (1, 2)
            for core_bin in ALL_CORE_BINS
        ]
    )
    return summary, profile


def test_training_table_uses_only_eligible_features_and_future_contact_counts() -> None:
    cutoff = date(2021, 7, 15)
    summary, profile = _targets(cutoff=cutoff)

    observed = build_batted_ball_residual_training_table(
        _b2_profile(),
        _standardized_features(cutoff=cutoff),
        summary,
        profile,
        _offsets(),
        expected_as_of_date=cutoff,
    )

    assert observed.height == 10
    assert observed.get_column("player_id").unique().to_list() == [1]
    assert observed.get_column("future_contact_events").unique().to_list() == [70]
    assert observed.get_column("future_contact_occurrence_count").sum() == 70
    assert observed.get_column("baseline2_latent_conditional_contact_probability").sum() == pytest.approx(1.0)
    assert observed.get_column("baseline2_target_conditional_contact_probability").sum() == pytest.approx(1.0)

    lookup = {row["core_bin"]: row for row in observed.iter_rows(named=True)}
    latent_ratio = (
        lookup["PULL_LD"]["baseline2_latent_conditional_contact_probability"]
        / lookup["OPPO_GB"]["baseline2_latent_conditional_contact_probability"]
    )
    target_ratio = (
        lookup["PULL_LD"]["baseline2_target_conditional_contact_probability"]
        / lookup["OPPO_GB"]["baseline2_target_conditional_contact_probability"]
    )
    assert target_ratio > latent_ratio


def test_training_table_fails_closed_on_cutoff_mismatch() -> None:
    cutoff = date(2021, 7, 15)
    summary, profile = _targets(cutoff=cutoff)

    with pytest.raises(ValueError, match="cutoff does not match"):
        build_batted_ball_residual_training_table(
            _b2_profile(),
            _standardized_features(cutoff=date(2021, 7, 14)),
            summary,
            profile,
            _offsets(),
            expected_as_of_date=cutoff,
        )


def _synthetic_training_table(*, signal: bool) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    player_features = {
        1: (1.0, 1.0),
        2: (1.0, -1.0),
        3: (-1.0, 1.0),
        4: (-1.0, -1.0),
    }
    uniform = 1.0 / len(CONTACT_CORE_BINS)
    for player_id, (z_ev, z_ss) in player_features.items():
        if signal:
            favored = "PULL_LD" if z_ev > 0 else "OPPO_GB"
            counts = {core_bin: (55 if core_bin == favored else 5) for core_bin in CONTACT_CORE_BINS}
        else:
            counts = {core_bin: 10 for core_bin in CONTACT_CORE_BINS}
        assert sum(counts.values()) == 100
        for core_bin in CONTACT_CORE_BINS:
            rows.append(
                {
                    "as_of_date": date(2021, 7, 15),
                    "player_id": player_id,
                    "target_season": 2021,
                    "target_league_id": 11,
                    "target_level_group": "AAA",
                    "core_bin": core_bin,
                    "z_mean_exit_velocity": z_ev,
                    "z_sweet_spot_share": z_ss,
                    "baseline2_latent_conditional_contact_probability": uniform,
                    "clr_environment_effect": 0.0,
                    "baseline2_target_conditional_contact_probability": uniform,
                    "future_contact_occurrence_count": counts[core_bin],
                    "future_contact_events": 100,
                    "future_core_events": 120,
                }
            )
    return pl.DataFrame(rows)


def test_fixed_penalty_residual_fit_learns_contact_shape_signal() -> None:
    fit = fit_batted_ball_residual_coefficients(_synthetic_training_table(signal=True))

    assert fit.metrics["converged"] is True
    assert fit.metrics["fixed_l2_penalty"] == FIXED_RESIDUAL_L2_PENALTY
    assert fit.metrics["penalty_search_performed"] is False
    assert fit.metrics["final_mean_contact_log_loss"] < fit.metrics["initial_mean_contact_log_loss"]
    lookup = {row["core_bin"]: row for row in fit.coefficients.iter_rows(named=True)}
    assert lookup["PULL_LD"]["beta_mean_exit_velocity"] > 0
    assert lookup["OPPO_GB"]["beta_mean_exit_velocity"] < 0
    assert all(
        math.isfinite(row["beta_mean_exit_velocity"])
        and math.isfinite(row["beta_sweet_spot_share"])
        for row in fit.coefficients.iter_rows(named=True)
    )


def test_no_signal_training_stays_at_zero_residual() -> None:
    fit = fit_batted_ball_residual_coefficients(_synthetic_training_table(signal=False))

    assert fit.metrics["final_mean_contact_log_loss"] == pytest.approx(
        fit.metrics["initial_mean_contact_log_loss"], abs=1e-12
    )
    assert fit.coefficients.get_column("beta_mean_exit_velocity").to_list() == pytest.approx(
        [0.0] * len(CONTACT_CORE_BINS), abs=1e-12
    )
    assert fit.coefficients.get_column("beta_sweet_spot_share").to_list() == pytest.approx(
        [0.0] * len(CONTACT_CORE_BINS), abs=1e-12
    )
