"""Reusable raw-source materialization for richer tracked batted-ball evidence.

This module performs no network I/O. It converts retained Baseball Savant CSV
bytes into the corrected canonical result-producing/non-bunt BBE surface and then
reconciles those rows to the already-certified Current Talent player-game
environment.

The same projection/reconciliation path is used for:

- retained certified MLB Savant raw caches; and
- tracked-only Minor League Savant raw captures after the live source gate.

This prevents separate source parsers or identity rules from drifting apart.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

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
