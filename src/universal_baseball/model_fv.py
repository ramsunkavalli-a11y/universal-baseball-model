"""Independent production-based Model FV assembly."""

from __future__ import annotations

from math import erf, sqrt

import polars as pl

from universal_baseball.prospect_value import (
    benchmark_value_from_model_fv,
    display_fv,
    model_fv_from_expected_war,
)


MODEL_FV_ID = "phase2_production_outcome_model_fv_v2"


def _normal_tail(threshold: float, mean: float, variance: float) -> float:
    if variance <= 0:
        return float(mean >= threshold)
    z = (threshold - mean) / sqrt(variance)
    return 0.5 * (1.0 - erf(z / sqrt(2.0)))


def diagnostic_role_bucket(player_type: str, role: str, fv: int) -> str:
    """Describe the projected population for diagnostics; never change a grade."""

    if player_type == "hitter":
        quality = "all_star" if fv >= 60 else "regular" if fv >= 50 else "depth"
        return f"{quality}_{role.lower()}"
    if role == "starter":
        quality = (
            "ace" if fv >= 70 else "number_2" if fv >= 65 else
            "number_3" if fv >= 60 else "number_4" if fv >= 55 else "number_5_or_depth"
        )
        return f"starter_{quality}"
    quality = "closer" if fv >= 60 else "setup" if fv >= 55 else "middle_or_depth"
    return f"reliever_{quality}"


def build_model_fv(
    hitter_paths: pl.DataFrame,
    pitcher_paths: pl.DataFrame,
    uncertainty: pl.DataFrame,
    *,
    pre_mlb_player_ids: set[int] | None = None,
) -> pl.DataFrame:
    """Turn projected six-year production distributions into internal FV grades."""

    required = {"player_id", "season", "expected_war"}
    if required - set(hitter_paths.columns) or required - set(pitcher_paths.columns):
        raise ValueError("expected WAR paths have an unexpected schema")
    if {"player_id", "season", "annual_war_variance"} - set(uncertainty.columns):
        raise ValueError("WAR uncertainty has an unexpected schema")

    pre_mlb_player_ids = pre_mlb_player_ids or set()
    hitter = hitter_paths.group_by("player_id").agg(
        pl.col("expected_war").sum().alias("hitter_expected_six_year_war"),
        pl.col("mlb_active_probability").max().alias(
            "hitter_six_year_arrival_probability"
        ),
        (
            pl.col("conditional_war_per_600_pa")
            * pl.when(pl.col("primary_position") == "C")
            .then(450.0)
            .otherwise(550.0)
            / 600.0
        ).sum().alias(
            "hitter_six_control_year_war_if_arrived"
        ),
        pl.col("primary_position").drop_nulls().first().alias("primary_position"),
    )
    pitcher = pitcher_paths.group_by("player_id").agg(
        pl.col("expected_war").sum().alias("pitcher_expected_six_year_war"),
        pl.col("mlb_active_probability").max().alias(
            "pitcher_six_year_arrival_probability"
        ),
        (
            pl.col("conditional_war_per_800_bf")
            * (
                800.0 * pl.col("starter_probability_if_active")
                + 450.0 * pl.col("swingman_probability_if_active")
                + 250.0 * pl.col("reliever_probability_if_active")
            )
            / 800.0
        ).sum().alias("pitcher_six_control_year_war_if_arrived"),
        pl.col("starter_probability_if_active").mean().alias("starter_probability"),
        pl.col("reliever_probability_if_active").mean().alias("reliever_probability"),
    )
    variance = uncertainty.group_by("player_id").agg(
        pl.col("annual_war_variance").sum().alias("six_year_war_variance")
    )
    joined = (
        hitter.join(pitcher, on="player_id", how="full", coalesce=True)
        .join(variance, on="player_id", how="left")
        .with_columns(
            pl.col("hitter_expected_six_year_war").fill_null(0.0),
            pl.col("pitcher_expected_six_year_war").fill_null(0.0),
            pl.col("six_year_war_variance").fill_null(0.0),
        )
        .with_columns(
            (
                pl.col("hitter_expected_six_year_war")
                + pl.col("pitcher_expected_six_year_war")
            ).alias("expected_six_year_war"),
            pl.when(
                pl.col("pitcher_expected_six_year_war")
                > pl.col("hitter_expected_six_year_war")
            )
            .then(pl.lit("pitcher"))
            .otherwise(pl.lit("hitter"))
            .alias("model_player_type"),
        )
    )

    rows = []
    for row in joined.iter_rows(named=True):
        player_type = str(row["model_player_type"])
        player_id = int(row["player_id"])
        expected_war = float(row["expected_six_year_war"])
        outcome_method = "next_six_calendar_years"
        if player_id in pre_mlb_player_ids:
            if player_type == "hitter":
                arrival = float(row["hitter_six_year_arrival_probability"] or 0.0)
                if_arrived = float(row["hitter_six_control_year_war_if_arrived"] or 0.0)
            else:
                arrival = float(row["pitcher_six_year_arrival_probability"] or 0.0)
                if_arrived = float(row["pitcher_six_control_year_war_if_arrived"] or 0.0)
            expected_war = arrival * if_arrived
            outcome_method = "six_control_years_after_probabilistic_arrival"
        granular = model_fv_from_expected_war(expected_war, player_type)
        if player_type == "hitter":
            role = str(row["primary_position"] or "position_player")
        elif float(row["starter_probability"] or 0.0) >= 0.5:
            role = "starter"
        else:
            role = "reliever"
        shown_fv = display_fv(granular)
        rows.append(
            {
                **row,
                "expected_six_year_war": expected_war,
                "outcome_method": outcome_method,
                "model_role": role,
                "model_fv_granular": granular,
                "model_fv_display": shown_fv,
                "diagnostic_role_bucket": diagnostic_role_bucket(
                    player_type, role, shown_fv
                ),
                "talent_benchmark_value_dollars": benchmark_value_from_model_fv(
                    granular, player_type
                ),
                "star_outcome_probability": _normal_tail(
                    18.0, expected_war, float(row["six_year_war_variance"])
                ),
                "model_fv_id": MODEL_FV_ID,
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None).sort("player_id")
