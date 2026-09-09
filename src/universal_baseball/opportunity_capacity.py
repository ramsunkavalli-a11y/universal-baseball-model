"""Closed-system checks for league playing-time projections."""

from __future__ import annotations

import polars as pl


def historical_mlb_workload_pools(stats: pl.DataFrame) -> pl.DataFrame:
    """Return actual league PA and BF totals; those totals must match by identity."""

    required = {
        "season", "stat_group", "sport_id", "plate_appearances", "batters_faced"
    }
    if missing := sorted(required - set(stats.columns)):
        raise ValueError(f"historical workload source missing columns: {missing}")
    mlb = stats.filter(pl.col("sport_id") == 1)
    hitter = (
        mlb.filter(pl.col("stat_group") == "hitting")
        .group_by("season")
        .agg(pl.col("plate_appearances").sum().alias("actual_pa"))
    )
    pitcher = (
        mlb.filter(pl.col("stat_group") == "pitching")
        .group_by("season")
        .agg(pl.col("batters_faced").sum().alias("actual_bf"))
    )
    result = hitter.join(pitcher, on="season", how="inner", validate="1:1").sort(
        "season"
    )
    return result.with_columns(
        (pl.col("actual_pa") - pl.col("actual_bf")).alias("pa_minus_bf")
    )


def audit_projected_workload_capacity(
    hitter_paths: pl.DataFrame,
    pitcher_paths: pl.DataFrame,
    *,
    reference_league_workload: float,
) -> pl.DataFrame:
    """Compare independently projected hitter and pitcher sides of the same PA pool."""

    if reference_league_workload <= 0:
        raise ValueError("reference league workload must be positive")
    hitter_required = {"season", "expected_mlb_pa"}
    pitcher_required = {"season", "expected_mlb_bf"}
    if missing := sorted(hitter_required - set(hitter_paths.columns)):
        raise ValueError(f"hitter paths missing columns: {missing}")
    if missing := sorted(pitcher_required - set(pitcher_paths.columns)):
        raise ValueError(f"pitcher paths missing columns: {missing}")
    hitter = hitter_paths.group_by("season").agg(
        pl.col("expected_mlb_pa").sum().alias("projected_hitter_pa")
    )
    pitcher = pitcher_paths.group_by("season").agg(
        pl.col("expected_mlb_bf").sum().alias("projected_pitcher_bf")
    )
    return (
        hitter.join(pitcher, on="season", how="inner", validate="1:1")
        .with_columns(
            (pl.col("projected_hitter_pa") - pl.col("projected_pitcher_bf"))
            .alias("hitter_pitcher_gap"),
            pl.lit(float(reference_league_workload)).alias(
                "reference_league_workload"
            ),
        )
        .with_columns(
            (
                pl.col("hitter_pitcher_gap").abs()
                / pl.col("reference_league_workload")
            ).alias("hitter_pitcher_gap_share"),
            (
                1.0
                - pl.col("projected_hitter_pa")
                / pl.col("reference_league_workload")
            ).alias("unassigned_hitter_share"),
            (
                1.0
                - pl.col("projected_pitcher_bf")
                / pl.col("reference_league_workload")
            ).alias("unassigned_pitcher_share"),
            (pl.col("projected_hitter_pa") <= pl.col("reference_league_workload"))
            .alias("hitter_capacity_not_exceeded"),
            (pl.col("projected_pitcher_bf") <= pl.col("reference_league_workload"))
            .alias("pitcher_capacity_not_exceeded"),
            (pl.col("hitter_pitcher_gap").abs() < 1e-6).alias(
                "closed_system_identity_passed"
            ),
            pl.min_horizontal(
                pl.col("reference_league_workload"),
                (
                    pl.col("projected_hitter_pa")
                    + pl.col("projected_pitcher_bf")
                ) / 2.0,
            ).alias("symmetric_shared_pool"),
        )
        .with_columns(
            (pl.col("symmetric_shared_pool") / pl.col("projected_hitter_pa"))
            .alias("research_hitter_scale"),
            (pl.col("symmetric_shared_pool") / pl.col("projected_pitcher_bf"))
            .alias("research_pitcher_scale"),
            (
                1.0
                - pl.col("symmetric_shared_pool")
                / pl.col("reference_league_workload")
            ).alias("explicit_external_or_replacement_share"),
        )
        .sort("season")
    )
