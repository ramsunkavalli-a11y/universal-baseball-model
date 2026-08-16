"""Combine MLB and affiliated batting Performance on one stable contract.

Performance remains observed evidence at actual-league grain.  This module adds
only reporting/environment context and concatenates already-certified MLB and
MiLB outputs; it performs no cross-level translation or talent inference.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from universal_baseball.bin_value_policy import LEAGUE_LEVEL_GROUP
from universal_baseball.mlb_bin_value_policy import MLB_LEAGUE_IDS
from universal_baseball.performance_contract import validate_batting_performance_contract
from universal_baseball.performance_materialization import LEAGUE_FILENAME_LEVEL


UNIVERSAL_LEVEL_GROUP: dict[int, str] = {
    **{int(k): str(v) for k, v in LEAGUE_LEVEL_GROUP.items()},
    **{int(k): "MLB" for k in MLB_LEAGUE_IDS},
}
UNIVERSAL_FILENAME_LEVEL: dict[int, str] = {
    **{int(k): str(v) for k, v in LEAGUE_FILENAME_LEVEL.items()},
    **{int(k): "mlb" for k in MLB_LEAGUE_IDS},
}
UNIVERSAL_LEAGUE_IDS = frozenset(UNIVERSAL_LEVEL_GROUP)


def add_universal_environment_context(frame: pl.DataFrame) -> pl.DataFrame:
    """Add normalized level/source bucket labels from actual league ID."""

    if "league_id" not in frame.columns:
        raise ValueError("universal Performance frame missing league_id")
    observed = {
        int(value)
        for value in frame.get_column("league_id").cast(pl.Int64, strict=False).drop_nulls().unique().to_list()
    }
    unknown = sorted(observed - set(UNIVERSAL_LEAGUE_IDS))
    if unknown:
        raise ValueError(f"universal Performance frame contains unknown league IDs: {unknown}")
    return frame.with_columns(
        pl.col("league_id").cast(pl.Int64),
        pl.col("league_id")
        .cast(pl.Int64)
        .replace_strict(UNIVERSAL_LEVEL_GROUP, default=None, return_dtype=pl.String)
        .alias("level_group"),
        pl.col("league_id")
        .cast(pl.Int64)
        .replace_strict(UNIVERSAL_FILENAME_LEVEL, default=None, return_dtype=pl.String)
        .alias("source_level_bucket"),
    )


def combine_universal_batting_performance(
    affiliated_summary: pl.DataFrame,
    affiliated_profile: pl.DataFrame,
    affiliated_bin_values: pl.DataFrame,
    mlb_summary: pl.DataFrame,
    mlb_profile: pl.DataFrame,
    mlb_bin_values: pl.DataFrame,
    *,
    expected_season: int | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    """Combine certified MLB and affiliated frames without cross-level scoring."""

    affiliated_contract = validate_batting_performance_contract(
        affiliated_summary,
        affiliated_profile,
        affiliated_bin_values,
        require_certified_values=True,
    )
    mlb_contract = validate_batting_performance_contract(
        mlb_summary,
        mlb_profile,
        mlb_bin_values,
        require_certified_values=True,
    )

    summary = add_universal_environment_context(
        pl.concat([affiliated_summary, mlb_summary], how="vertical_relaxed")
    )
    profile = add_universal_environment_context(
        pl.concat([affiliated_profile, mlb_profile], how="vertical_relaxed")
    )
    values = add_universal_environment_context(
        pl.concat([affiliated_bin_values, mlb_bin_values], how="vertical_relaxed")
    )

    if expected_season is not None:
        for label, frame in (("summary", summary), ("profile", profile), ("bin values", values)):
            seasons = sorted(int(value) for value in frame.get_column("season").unique().to_list())
            if seasons != [int(expected_season)]:
                raise ValueError(
                    f"{label} universal season mismatch: observed={seasons}, expected={[int(expected_season)]}"
                )

    observed_leagues = set(int(value) for value in summary.get_column("league_id").unique().to_list())
    if observed_leagues != set(UNIVERSAL_LEAGUE_IDS):
        raise ValueError(
            "universal summary league coverage mismatch: "
            f"missing={sorted(set(UNIVERSAL_LEAGUE_IDS) - observed_leagues)}, "
            f"extra={sorted(observed_leagues - set(UNIVERSAL_LEAGUE_IDS))}"
        )

    # Revalidate the concatenated stable contract after context columns are added.
    combined_contract = validate_batting_performance_contract(
        summary,
        profile,
        values,
        require_certified_values=True,
    )
    metrics: dict[str, Any] = {
        "actual_league_count": len(observed_leagues),
        "level_group_count": summary.get_column("level_group").n_unique(),
        "level_groups": sorted(summary.get_column("level_group").unique().to_list()),
        "affiliated_contract": affiliated_contract,
        "mlb_contract": mlb_contract,
        "combined_contract": combined_contract,
    }
    return (
        summary.sort(["season", "league_id", "player_id"]),
        profile.sort(["season", "league_id", "player_id", "core_bin"]),
        values.sort(["season", "league_id", "core_bin"]),
        metrics,
    )
