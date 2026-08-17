"""Player-level provenance summary for observed richer batted-ball evidence.

The EV/LA feature builder intentionally collapses tracked BBE to player-level
physical summaries. This module preserves *where those observed BBE came from* so
partial historical tracking cannot disappear after aggregation.

Capability summaries are descriptive diagnostics only. They never impute missing
tracking or promote an unobserved game/league to tracked status.
"""

from __future__ import annotations

from datetime import date

import polars as pl

from universal_baseball.current_talent_batted_ball_quality import TRACKED_BBE_KEY
from universal_baseball.current_talent_batted_ball_reconciliation import (
    RECONCILED_TRACKED_BBE_SCHEMA,
)


PLAYER_TRACKING_CAPABILITY_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "observed_model_bbe": pl.Int64,
    "observed_tracked_game_count": pl.Int64,
    "observed_mlb_bbe": pl.Int64,
    "observed_milb_bbe": pl.Int64,
    "source_family_group": pl.String,
    "source_family_count": pl.Int64,
    "source_capability_tier_count": pl.Int64,
    "observed_source_capability_tiers": pl.String,
    "observed_level_groups": pl.String,
    "observed_league_ids": pl.String,
}


def _sorted_join(values: list[object]) -> str:
    return "|".join(sorted({str(value) for value in values if value is not None}))


def build_player_tracking_capability(
    reconciled_bbe: pl.DataFrame,
    *,
    cutoff: date,
) -> pl.DataFrame:
    """Summarize observed pre-cutoff model-BBE provenance by player."""

    missing = sorted(set(RECONCILED_TRACKED_BBE_SCHEMA) - set(reconciled_bbe.columns))
    if missing:
        raise ValueError(f"reconciled tracked BBE missing fields: {missing}")
    if reconciled_bbe.is_empty():
        return pl.DataFrame(schema=PLAYER_TRACKING_CAPABILITY_SCHEMA)

    duplicate = reconciled_bbe.group_by(list(TRACKED_BBE_KEY)).len().filter(
        pl.col("len") != 1
    )
    if not duplicate.is_empty():
        raise ValueError("reconciled tracked BBE violates canonical pitch-grain BBE key")

    working = reconciled_bbe.with_columns(
        pl.col("game_date").cast(pl.Date, strict=False).alias("game_date")
    ).filter(pl.col("game_date") < pl.lit(cutoff))
    if working.is_empty():
        return pl.DataFrame(schema=PLAYER_TRACKING_CAPABILITY_SCHEMA)

    rows: list[dict[str, object]] = []
    for key, group in working.group_by("player_id", maintain_order=True):
        player_id = int(key[0]) if isinstance(key, tuple) else int(key)
        families = [str(value) for value in group.get_column("source_family").to_list()]
        family_set = set(families)
        if family_set == {"MLB_SAVANT"}:
            family_group = "MLB_ONLY"
        elif family_set == {"MILB_SAVANT_TRACKED"}:
            family_group = "MILB_ONLY"
        elif family_set == {"MLB_SAVANT", "MILB_SAVANT_TRACKED"}:
            family_group = "MLB_MILB_MIXED"
        else:
            raise ValueError(f"unsupported observed source-family combination: {sorted(family_set)}")

        rows.append(
            {
                "as_of_date": cutoff,
                "player_id": player_id,
                "observed_model_bbe": int(group.height),
                "observed_tracked_game_count": int(group.get_column("game_pk").n_unique()),
                "observed_mlb_bbe": int(
                    group.filter(pl.col("source_family") == "MLB_SAVANT").height
                ),
                "observed_milb_bbe": int(
                    group.filter(pl.col("source_family") == "MILB_SAVANT_TRACKED").height
                ),
                "source_family_group": family_group,
                "source_family_count": len(family_set),
                "source_capability_tier_count": int(
                    group.get_column("source_capability_tier").n_unique()
                ),
                "observed_source_capability_tiers": _sorted_join(
                    group.get_column("source_capability_tier").to_list()
                ),
                "observed_level_groups": _sorted_join(
                    group.get_column("level_group").to_list()
                ),
                "observed_league_ids": _sorted_join(
                    group.get_column("league_id").to_list()
                ),
            }
        )

    return (
        pl.DataFrame(rows, schema=PLAYER_TRACKING_CAPABILITY_SCHEMA)
        .sort("player_id")
    )
