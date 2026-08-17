"""Reconcile observed tracked batted balls to certified Current Talent environments.

Tracking availability is structurally uneven in the historical minor leagues, so
this layer deliberately assigns provenance from the *observed tracked game/player
row* rather than declaring an entire level tracked.  A complete EV/LA batted ball
may enter the richer Current Talent tier only after ``game_pk + player_id`` maps
unambiguously to the already-certified player-game evidence.

The resulting capability key is descriptive provenance, not an eligibility rule:
for example, observing one 2022 AAA tracked game does not imply that all 2022 AAA
games were tracked.
"""

from __future__ import annotations

import polars as pl

from universal_baseball.current_talent_batted_ball_quality import TRACKED_BBE_SCHEMA


TRACKED_SOURCE_FAMILIES = frozenset({"MLB_SAVANT", "MILB_SAVANT_TRACKED"})

RECONCILED_TRACKED_BBE_SCHEMA: dict[str, pl.DataType] = {
    **TRACKED_BBE_SCHEMA,
    "season": pl.Int64,
    "league_id": pl.Int64,
    "level_group": pl.String,
    "source_family": pl.String,
    "source_capability_tier": pl.String,
}


def _require_columns(frame: pl.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing fields: {missing}")


def reconcile_tracked_bbe_to_certified_environment(
    tracked_bbe: pl.DataFrame,
    certified_player_games: pl.DataFrame,
    *,
    source_family: str,
) -> pl.DataFrame:
    """Attach certified season/league/level provenance to complete tracked BBE.

    ``certified_player_games`` may contain the full Current Talent game-summary
    surface; only ``game_pk + player_id + season + league_id + level_group`` are
    used here.  Multiple summary rows for a player/game are allowed only when
    they collapse to one identical environment.  Any complete tracked BBE with
    no certified environment fails closed rather than being assigned a level from
    the tracking source itself.
    """

    if source_family not in TRACKED_SOURCE_FAMILIES:
        raise ValueError(f"unsupported tracked source family: {source_family}")
    _require_columns(tracked_bbe, set(TRACKED_BBE_SCHEMA), "tracked batted-ball evidence")
    _require_columns(
        certified_player_games,
        {"game_pk", "player_id", "season", "league_id", "level_group"},
        "certified player-game evidence",
    )
    if tracked_bbe.is_empty():
        return pl.DataFrame(schema=RECONCILED_TRACKED_BBE_SCHEMA)

    duplicate_bbe = tracked_bbe.group_by(["game_pk", "player_id", "at_bat_number"]).len().filter(
        pl.col("len") != 1
    )
    if not duplicate_bbe.is_empty():
        raise ValueError("tracked batted-ball evidence violates canonical BBE grain")

    environments = (
        certified_player_games.select(
            pl.col("game_pk").cast(pl.Int64),
            pl.col("player_id").cast(pl.Int64),
            pl.col("season").cast(pl.Int64),
            pl.col("league_id").cast(pl.Int64),
            pl.col("level_group").cast(pl.String),
        )
        .unique()
    )
    ambiguous = (
        environments.group_by(["game_pk", "player_id"])
        .agg(
            pl.struct(["season", "league_id", "level_group"]).n_unique().alias("environment_count")
        )
        .filter(pl.col("environment_count") != 1)
    )
    if not ambiguous.is_empty():
        raise ValueError("certified player-game evidence has ambiguous game/player environment")

    environments = environments.unique(subset=["game_pk", "player_id"], keep="first")
    joined = tracked_bbe.join(
        environments,
        on=["game_pk", "player_id"],
        how="left",
    )
    unmatched = joined.filter(
        pl.col("season").is_null()
        | pl.col("league_id").is_null()
        | pl.col("level_group").is_null()
    )
    if not unmatched.is_empty():
        raise ValueError(
            "complete tracked BBE do not all reconcile to certified game/player environments: "
            f"{unmatched.height} unmatched rows"
        )

    if source_family == "MLB_SAVANT":
        non_mlb = joined.filter(pl.col("level_group") != "MLB")
        if not non_mlb.is_empty():
            raise ValueError("MLB Savant tracked BBE reconciled to a non-MLB environment")
    else:
        accidental_mlb = joined.filter(pl.col("level_group") == "MLB")
        if not accidental_mlb.is_empty():
            raise ValueError("Minor Savant tracked BBE reconciled to an MLB environment")

    result = (
        joined.with_columns(
            pl.lit(source_family).alias("source_family"),
            pl.concat_str(
                [
                    pl.lit(source_family),
                    pl.col("season").cast(pl.String),
                    pl.col("league_id").cast(pl.String),
                    pl.col("level_group"),
                ],
                separator=":",
            ).alias("source_capability_tier"),
        )
        .select(*RECONCILED_TRACKED_BBE_SCHEMA)
        .cast(RECONCILED_TRACKED_BBE_SCHEMA, strict=True)
        .sort(["game_date", "game_pk", "player_id", "at_bat_number"])
    )
    return result
