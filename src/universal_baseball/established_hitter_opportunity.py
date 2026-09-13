"""Apply validated incumbent-hitter survival probabilities without changing talent."""

from __future__ import annotations

import polars as pl


MODEL_ID = "established_hitter_recent_history_talent_probability_v1"


def apply_established_hitter_probabilities(
    paths: pl.DataFrame, scores: pl.DataFrame
) -> pl.DataFrame:
    """Replace only active probability for covered current-MLB hitters."""

    required_paths = {
        "player_id",
        "horizon",
        "mlb_active_probability",
        "conditional_mlb_pa",
        "conditional_war_per_600_pa",
        "expected_mlb_pa",
        "expected_war",
        "probability_model_id",
        "coverage_tier",
    }
    if missing := sorted(required_paths - set(paths.columns)):
        raise ValueError(f"hitter paths missing fields: {missing}")
    required_scores = {"player_id", "horizon", "predicted_probability"}
    if missing := sorted(required_scores - set(scores.columns)):
        raise ValueError(f"established hitter scores missing fields: {missing}")
    if scores.group_by("player_id", "horizon").len().filter(pl.col("len") != 1).height:
        raise ValueError("established hitter scores violate player-horizon grain")
    if scores.filter(~pl.col("predicted_probability").is_between(0.0, 1.0)).height:
        raise ValueError("established hitter probabilities must be between zero and one")

    result = (
        paths.join(
            scores.select("player_id", "horizon", "predicted_probability"),
            on=["player_id", "horizon"],
            how="left",
            validate="1:1",
        )
        .with_columns(
            pl.col("predicted_probability").is_not_null().alias(
                "established_probability_applied"
            ),
            pl.coalesce("predicted_probability", "mlb_active_probability").alias(
                "mlb_active_probability"
            ),
        )
        .with_columns(
            (pl.col("mlb_active_probability") * pl.col("conditional_mlb_pa")).alias(
                "expected_mlb_pa"
            ),
            (
                pl.col("mlb_active_probability")
                * pl.col("conditional_mlb_pa")
                * pl.col("conditional_war_per_600_pa")
                / 600.0
            ).alias("expected_war"),
            pl.when(pl.col("established_probability_applied"))
            .then(pl.lit(MODEL_ID))
            .otherwise(pl.col("probability_model_id"))
            .alias("probability_model_id"),
            pl.when(pl.col("established_probability_applied"))
            .then(pl.lit("established_mlb_recent_history_talent"))
            .otherwise(pl.col("coverage_tier"))
            .alias("coverage_tier"),
        )
        .drop("predicted_probability")
        .sort(["player_id", "horizon"])
    )
    if result.height != paths.height:
        raise RuntimeError("established hitter bridge changed path coverage")
    return result
