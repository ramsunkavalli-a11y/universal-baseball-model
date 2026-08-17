"""Reusable raw-source materialization for richer tracked batted-ball evidence.

This module performs no network I/O. It converts retained Baseball Savant CSV
bytes into the corrected canonical result-producing/non-bunt BBE surface and then
reconciles those rows to the already-certified Current Talent player-game
environment.

The same projection/reconciliation path is used for:

- retained certified MLB Savant raw caches; and
- tracked-only Minor League Savant raw captures after the live source gate.

Broad source measurement completeness is kept separate from model BBE and uses
the same observed certified environments. This prevents separate source parsers,
identity rules, or capability labels from drifting apart.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.current_talent_batted_ball_quality import (
    TRACKED_BBE_KEY,
    project_complete_tracked_bbe,
)
from universal_baseball.current_talent_batted_ball_reconciliation import (
    RECONCILED_TRACKED_BBE_SCHEMA,
    TRACKED_SOURCE_FAMILIES,
    reconcile_tracked_bbe_to_certified_environment,
)
from universal_baseball.current_talent_batted_ball_source_diagnostics import (
    project_savant_bbe_tracking_observations,
)


RAW_SAVANT_BBE_FIELDS = (
    "game_date",
    "game_pk",
    "batter",
    "at_bat_number",
    "pitch_number",
    "events",
    "type",
    "des",
    "description",
    "bb_type",
    "launch_speed",
    "launch_angle",
)

TRACKING_ENVIRONMENT_COMPLETENESS_SCHEMA: dict[str, pl.DataType] = {
    "source_family": pl.String,
    "source_capability_tier": pl.String,
    "season": pl.Int64,
    "league_id": pl.Int64,
    "level_group": pl.String,
    "bbe_like_observations": pl.Int64,
    "complete_ev_la_observations": pl.Int64,
    "complete_ev_la_share": pl.Float64,
    "ambiguous_complete_ev_la_observations": pl.Int64,
    "tracked_game_count": pl.Int64,
    "player_count": pl.Int64,
}


def read_retained_savant_csv_tree(raw_root: Path) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Read exact retained Savant CSV chunks and return data + file manifest."""

    paths = sorted(raw_root.rglob("*.csv"))
    if not paths:
        raise ValueError(f"no Savant CSV files found under {raw_root}")

    frames: list[pl.DataFrame] = []
    manifest_rows: list[dict[str, object]] = []
    for path in paths:
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        frame = pl.read_csv(
            path,
            infer_schema=False,
            null_values=["", "null", "NA"],
            ignore_errors=False,
        )
        missing = sorted(set(RAW_SAVANT_BBE_FIELDS) - set(frame.columns))
        if missing:
            raise ValueError(f"retained Savant CSV {path} missing fields: {missing}")
        frames.append(frame.select(*RAW_SAVANT_BBE_FIELDS))
        manifest_rows.append(
            {
                "path": str(path),
                "sha256": digest,
                "response_bytes": len(content),
                "row_count": int(frame.height),
                "column_count": len(frame.columns),
            }
        )

    combined = pl.concat(frames, how="vertical_relaxed")
    manifest = pl.DataFrame(manifest_rows).sort("path")
    return combined, manifest


def load_certified_player_game_environments(
    evidence_root: Path,
    *,
    season: int,
    source_family: str,
) -> pl.DataFrame:
    """Load certified player-game environment keys for one source family."""

    if source_family not in TRACKED_SOURCE_FAMILIES:
        raise ValueError(f"unsupported tracked source family: {source_family}")
    pattern = (
        f"current_talent_game_summary_{season}_mlb.parquet"
        if source_family == "MLB_SAVANT"
        else f"current_talent_game_summary_{season}_*.parquet"
    )
    paths = sorted(evidence_root.rglob(pattern))
    if not paths:
        raise ValueError(
            f"no certified {source_family} player-game summaries for {season} under {evidence_root}"
        )

    frames: list[pl.DataFrame] = []
    for path in paths:
        frame = pl.read_parquet(path).select(
            pl.col("game_pk").cast(pl.Int64),
            pl.col("player_id").cast(pl.Int64),
            pl.col("season").cast(pl.Int64),
            pl.col("league_id").cast(pl.Int64),
            pl.col("level_group").cast(pl.String),
        )
        frames.append(frame)
    combined = pl.concat(frames, how="vertical_relaxed").unique()

    seasons = {int(value) for value in combined.get_column("season").unique().to_list()}
    if seasons != {int(season)}:
        raise ValueError(
            f"certified player-game season mismatch: observed={sorted(seasons)}, expected={[season]}"
        )
    if source_family == "MLB_SAVANT":
        bad = combined.filter(pl.col("level_group") != "MLB")
        if not bad.is_empty():
            raise ValueError("MLB certified environment input contains non-MLB rows")
    else:
        bad = combined.filter(pl.col("level_group") == "MLB")
        if not bad.is_empty():
            raise ValueError("MiLB certified environment input contains MLB rows")
    return combined.sort(["game_pk", "player_id"])


def materialize_reconciled_tracked_bbe(
    raw_savant: pl.DataFrame,
    certified_player_games: pl.DataFrame,
    *,
    source_family: str,
) -> pl.DataFrame:
    """Project corrected model BBE and attach certified environment provenance."""

    projected = project_complete_tracked_bbe(raw_savant)
    return reconcile_tracked_bbe_to_certified_environment(
        projected,
        certified_player_games,
        source_family=source_family,
    )


def build_tracking_environment_completeness(
    raw_savant: pl.DataFrame,
    certified_player_games: pl.DataFrame,
    *,
    source_family: str,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Summarize broad EV/LA measurement completeness by observed environment.

    Unlike model-BBE reconciliation, broad source observations may include players
    without usable Current Talent core evidence. Unmatched broad observations are
    therefore reported as source coverage rather than causing model failure. Only
    matched observations contribute to environment-specific completeness rows.
    """

    if source_family not in TRACKED_SOURCE_FAMILIES:
        raise ValueError(f"unsupported tracked source family: {source_family}")
    observations = project_savant_bbe_tracking_observations(raw_savant)
    if observations.is_empty():
        return pl.DataFrame(schema=TRACKING_ENVIRONMENT_COMPLETENESS_SCHEMA), {
            "bbe_like_observations": 0,
            "matched_bbe_like_observations": 0,
            "unmatched_bbe_like_observations": 0,
            "certified_match_share": None,
        }

    environment = certified_player_games.select(
        "game_pk", "player_id", "season", "league_id", "level_group"
    ).unique()
    ambiguous = (
        environment.group_by(["game_pk", "player_id"])
        .agg(pl.struct(["season", "league_id", "level_group"]).n_unique().alias("n"))
        .filter(pl.col("n") != 1)
    )
    if not ambiguous.is_empty():
        raise ValueError("certified player-game environment is ambiguous for broad tracking audit")
    environment = environment.unique(subset=["game_pk", "player_id"], keep="first")

    joined = observations.join(environment, on=["game_pk", "player_id"], how="left")
    matched = joined.filter(
        pl.col("season").is_not_null()
        & pl.col("league_id").is_not_null()
        & pl.col("level_group").is_not_null()
    )
    total = int(joined.height)
    matched_count = int(matched.height)
    metrics = {
        "bbe_like_observations": total,
        "matched_bbe_like_observations": matched_count,
        "unmatched_bbe_like_observations": total - matched_count,
        "certified_match_share": matched_count / total if total else None,
    }
    if matched.is_empty():
        return pl.DataFrame(schema=TRACKING_ENVIRONMENT_COMPLETENESS_SCHEMA), metrics

    result = (
        matched.group_by(["season", "league_id", "level_group"])
        .agg(
            pl.len().cast(pl.Int64).alias("bbe_like_observations"),
            pl.col("has_complete_ev_la").sum().cast(pl.Int64).alias(
                "complete_ev_la_observations"
            ),
            pl.col("ambiguous_multiple_complete_ev_la")
            .sum()
            .cast(pl.Int64)
            .alias("ambiguous_complete_ev_la_observations"),
            pl.col("game_pk").n_unique().cast(pl.Int64).alias("tracked_game_count"),
            pl.col("player_id").n_unique().cast(pl.Int64).alias("player_count"),
        )
        .with_columns(
            (
                pl.col("complete_ev_la_observations")
                / pl.col("bbe_like_observations").cast(pl.Float64)
            ).alias("complete_ev_la_share"),
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
        .select(*TRACKING_ENVIRONMENT_COMPLETENESS_SCHEMA)
        .cast(TRACKING_ENVIRONMENT_COMPLETENESS_SCHEMA, strict=True)
        .sort(["season", "level_group", "league_id"])
    )
    return result, metrics


def combine_reconciled_tracked_bbe(
    frames: list[pl.DataFrame],
    *,
    expected_season: int,
) -> pl.DataFrame:
    """Combine MLB/MiLB reconciled BBE for one season without source overlap."""

    if not frames:
        raise ValueError("at least one reconciled tracked-BBE frame is required")
    for frame in frames:
        missing = sorted(set(RECONCILED_TRACKED_BBE_SCHEMA) - set(frame.columns))
        if missing:
            raise ValueError(f"reconciled tracked BBE missing fields: {missing}")
    combined = pl.concat(
        [frame.select(*RECONCILED_TRACKED_BBE_SCHEMA) for frame in frames],
        how="vertical_relaxed",
    ).cast(RECONCILED_TRACKED_BBE_SCHEMA, strict=True)
    if combined.is_empty():
        return combined

    seasons = {int(value) for value in combined.get_column("season").unique().to_list()}
    if seasons != {int(expected_season)}:
        raise ValueError(
            f"combined tracking season mismatch: observed={sorted(seasons)}, "
            f"expected={[expected_season]}"
        )
    duplicate = combined.group_by(list(TRACKED_BBE_KEY)).len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError("MLB/MiLB reconciled tracking overlaps at canonical BBE key")
    return combined.sort(["game_date", *TRACKED_BBE_KEY])
