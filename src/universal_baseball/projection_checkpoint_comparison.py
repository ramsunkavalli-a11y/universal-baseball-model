"""Compare two projection checkpoints without mixing universe and value changes."""

from __future__ import annotations

import polars as pl


def compare_projection_checkpoints(
    earlier: pl.DataFrame,
    later: pl.DataFrame,
    *,
    component: str,
    workload_column: str,
    rate_column: str,
    workload_unit: float,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Return shared player-season changes and separate player-universe changes."""

    required = {
        "as_of_date",
        "player_id",
        "season",
        workload_column,
        rate_column,
        "expected_war",
    }
    for label, frame in (("earlier", earlier), ("later", later)):
        missing = sorted(required - set(frame.columns))
        if missing:
            raise ValueError(f"{label} projection checkpoint missing fields: {missing}")
        if frame.group_by("player_id", "season").len().filter(
            pl.col("len") != 1
        ).height:
            raise ValueError(f"{label} projection checkpoint violates player-season grain")
    if workload_unit <= 0.0:
        raise ValueError("projection comparison workload unit must be positive")

    early_dates = earlier.get_column("as_of_date").unique().to_list()
    later_dates = later.get_column("as_of_date").unique().to_list()
    if len(early_dates) != 1 or len(later_dates) != 1 or not (
        early_dates[0] < later_dates[0]
    ):
        raise ValueError("projection checkpoints must have one increasing as-of date")

    keys = ["player_id", "season"]
    early = earlier.select(
        *keys,
        pl.col(workload_column).alias("earlier_expected_workload"),
        pl.col(rate_column).alias("earlier_conditional_war_rate"),
        pl.col("expected_war").alias("earlier_expected_war"),
    )
    new = later.select(
        *keys,
        pl.col(workload_column).alias("later_expected_workload"),
        pl.col(rate_column).alias("later_conditional_war_rate"),
        pl.col("expected_war").alias("later_expected_war"),
    )
    changes = early.join(new, on=keys, how="inner", validate="1:1").with_columns(
        pl.lit(component).alias("projection_component"),
        (pl.col("later_expected_war") - pl.col("earlier_expected_war")).alias(
            "expected_war_delta"
        ),
        (
            (pl.col("later_expected_workload") - pl.col("earlier_expected_workload"))
            * pl.col("earlier_conditional_war_rate")
            / workload_unit
        ).alias("opportunity_effect_war"),
        (
            pl.col("later_expected_workload")
            * (
                pl.col("later_conditional_war_rate")
                - pl.col("earlier_conditional_war_rate")
            )
            / workload_unit
        ).alias("skill_effect_war"),
    ).with_columns(
        (
            pl.col("expected_war_delta")
            - pl.col("opportunity_effect_war")
            - pl.col("skill_effect_war")
        ).alias("decomposition_residual_war")
    ).sort(["player_id", "season"])
    if changes.is_empty() or changes.filter(
        pl.col("decomposition_residual_war").abs() > 1e-9
    ).height:
        raise ValueError("projection checkpoint WAR decomposition does not reconcile")

    early_ids = earlier.select("player_id").unique()
    later_ids = later.select("player_id").unique()
    universe = pl.concat(
        [
            early_ids.join(later_ids, on="player_id", how="semi").with_columns(
                pl.lit("retained").alias("universe_status")
            ),
            later_ids.join(early_ids, on="player_id", how="anti").with_columns(
                pl.lit("new").alias("universe_status")
            ),
            early_ids.join(later_ids, on="player_id", how="anti").with_columns(
                pl.lit("departed").alias("universe_status")
            ),
        ]
    ).with_columns(pl.lit(component).alias("projection_component")).sort("player_id")
    return changes, universe
