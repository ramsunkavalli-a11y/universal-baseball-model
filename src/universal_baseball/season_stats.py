"""Explicit schema adapter for reusable armstjc season-player stat releases.

The release files use compact source names such as ``batting_PA`` and
``team_league_id``. Downstream certification should not guess what those names
mean, and raw files remain immutable. This module therefore exposes a small,
versionable standardized view with common grain columns and descriptive stat
names.

Only observed and intentionally mapped fields are renamed. Missing optional
fields stay missing so source limitations remain visible.

Completed-2024 all-level certification also supports three convenience fields
on both sides of the ball: ground outs, air outs, and pitch count. These are
standardized here, but ground/air *outs* are not treated as one-per-contact
trajectory event counts. Detailed trajectory hit/out components and aggregate
swings/whiffs remain outside the certified production mapping pending separate
semantic/fidelity validation.
"""

from __future__ import annotations

from typing import Any, Literal

import polars as pl


SeasonStatKind = Literal["batting", "pitching"]

COMMON_COLUMN_MAP: dict[str, str] = {
    "season": "season",
    "team_id": "team_id",
    "team_name": "team_name",
    "team_league_id": "league_id",
    "team_league": "league_name",
    "team_level_id": "level_id",
    "team_level_abv": "level",
    "player_id": "player_id",
    "player_full_name": "player_name",
}

BATTING_COLUMN_MAP: dict[str, str] = {
    "G": "batting_games_played",
    "batting_PA": "batting_plate_appearances",
    "batting_AB": "batting_at_bats",
    "batting_H": "batting_hits",
    "batting_2B": "batting_doubles",
    "batting_3B": "batting_triples",
    "batting_HR": "batting_home_runs",
    "batting_BB": "batting_base_on_balls",
    "batting_IBB": "batting_intentional_walks",
    "batting_HBP": "batting_hit_by_pitch",
    "batting_SO": "batting_strike_outs",
    "batting_SH": "batting_sac_bunts",
    "batting_SF": "batting_sac_flies",
    "batting_CI": "batting_catchers_interference_reached",
    "batting_balls_in_play": "batting_balls_in_play",
    "batting_ground_hits": "batting_ground_hits",
    "batting_fly_hits": "batting_fly_hits",
    "batting_pop_hits": "batting_pop_hits",
    "batting_line_hits": "batting_line_hits",
    # Independently exposed by the official person-season representation and
    # exact in the 2024 all-level reconciliation sample.
    "batting_GO": "batting_ground_outs",
    "batting_AO": "batting_air_outs",
    "batting_pitches_faced": "batting_pitches_seen",
}

PITCHING_COLUMN_MAP: dict[str, str] = {
    "pitching_G": "pitching_games_played",
    "pitching_GS": "pitching_games_started",
    "pitching_BF": "pitching_batters_faced",
    "pitching_AB": "pitching_at_bats",
    "pitching_H": "pitching_hits",
    "pitching_2B": "pitching_doubles",
    "pitching_3B": "pitching_triples",
    "pitching_HR": "pitching_home_runs",
    "pitching_BB": "pitching_base_on_balls",
    "pitching_IBB": "pitching_intentional_walks",
    "pitching_HBP": "pitching_hit_batsmen",
    "pitching_SO": "pitching_strike_outs",
    # Current audited releases do not expose this source column, but keeping the
    # expected alias makes the limitation explicit and future-proofs the adapter.
    "pitching_SH": "pitching_sac_bunts",
    "pitching_SF": "pitching_sac_flies",
    "pitching_CI": "pitching_catchers_interference",
    "pitching_balls_in_play": "pitching_balls_in_play",
    # Independently exposed by the official person-season representation and
    # exact in the 2024 all-level reconciliation sample.
    "pitching_GO": "pitching_ground_outs",
    "pitching_AO": "pitching_air_outs",
    "pitching_PI": "pitching_pitches_thrown",
}

REQUIRED_GRAIN_COLUMNS = ("season", "league_id", "team_id", "player_id")
SAMPLE_VOLUME_COLUMNS: dict[SeasonStatKind, str] = {
    "batting": "batting_plate_appearances",
    "pitching": "pitching_batters_faced",
}

BATTING_PA_COMPONENT_COLUMNS = (
    "batting_at_bats",
    "batting_base_on_balls",
    "batting_hit_by_pitch",
    "batting_sac_bunts",
    "batting_sac_flies",
    "batting_catchers_interference_reached",
)


def _column_map(kind: SeasonStatKind) -> dict[str, str]:
    if kind == "batting":
        return {**COMMON_COLUMN_MAP, **BATTING_COLUMN_MAP}
    if kind == "pitching":
        return {**COMMON_COLUMN_MAP, **PITCHING_COLUMN_MAP}
    raise ValueError(f"unsupported season-stat kind: {kind!r}")


def _integer_like_expr(column: str, alias: str) -> pl.Expr:
    """Parse integer-like numeric values, including source strings like ``125.0``.

    Counts and MLBAM IDs are integral even though some release files serialize
    them as decimal strings. Parse through Float64 but reject non-integral values
    instead of silently truncating them.
    """

    numeric = pl.col(column).cast(pl.Float64, strict=False)
    return (
        pl.when(numeric.is_not_null() & (numeric == numeric.floor()))
        .then(numeric.cast(pl.Int64, strict=False))
        .otherwise(None)
        .alias(alias)
    )


def standardize_armstjc_season_stats(
    frame: pl.DataFrame,
    kind: SeasonStatKind,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Return a standardized view without mutating or filling raw evidence.

    A raw-to-canonical collision is a hard error. We do not silently prefer one
    column because that would make upstream schema drift invisible.
    """

    mapping = _column_map(kind)
    rename: dict[str, str] = {}
    for raw, canonical in mapping.items():
        if raw not in frame.columns or raw == canonical:
            continue
        if canonical in frame.columns:
            raise ValueError(
                f"season-stat source contains both raw {raw!r} and canonical "
                f"{canonical!r}; refusing ambiguous rename"
            )
        rename[raw] = canonical

    result = frame.rename(rename)
    missing_grain = sorted(set(REQUIRED_GRAIN_COLUMNS) - set(result.columns))
    if missing_grain:
        raise ValueError(
            f"{kind} season-stat source missing required standardized grain "
            f"columns: {missing_grain}"
        )

    mapped = {
        raw: canonical
        for raw, canonical in mapping.items()
        if raw in frame.columns
    }
    absent_optional = sorted(
        canonical
        for raw, canonical in mapping.items()
        if raw not in frame.columns and canonical not in REQUIRED_GRAIN_COLUMNS
    )
    return result, {
        "kind": kind,
        "mapped_columns": mapped,
        "rename_count": len(rename),
        "absent_optional_columns": absent_optional,
        "required_grain_columns": list(REQUIRED_GRAIN_COLUMNS),
    }


def with_batting_pa_residual(frame: pl.DataFrame) -> pl.DataFrame:
    """Expose true PA counts not explained by the standard aggregate components.

    The common identity ``PA = AB + BB + HBP + SH + SF + CI`` is exact in nearly
    all certified 2024 rows but not literally universal: one Double-A row had a
    +1 residual. We preserve that evidence as ``batting_other_plate_appearances``
    rather than silently forcing the standard components to equal PA or guessing
    the underlying rare event type.

    The residual is signed on purpose. A negative value is a quality signal and
    must not be clamped to zero.
    """

    required = {"batting_plate_appearances", *BATTING_PA_COMPONENT_COLUMNS}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"batting PA residual missing required columns: {missing}")

    total = pl.col("batting_plate_appearances").cast(pl.Int64, strict=False)
    components = sum(
        (pl.col(column).cast(pl.Int64, strict=False) for column in BATTING_PA_COMPONENT_COLUMNS),
        start=pl.lit(0, dtype=pl.Int64),
    )
    return frame.with_columns(
        (total - components).alias("batting_other_plate_appearances")
    )


def select_reconciliation_players(
    frame: pl.DataFrame,
    kind: SeasonStatKind,
    *,
    per_league: int = 1,
) -> list[dict[str, int]]:
    """Choose deterministic high-volume, single-league players for validation.

    The official person-season endpoint is queried at the broader sport level
    (for example Triple-A or Rookie). To make that total comparable to one actual
    source league, candidates who appeared in more than one source league are
    excluded. Volume is summed across team rows within the remaining league and
    ties are broken by MLBAM player ID.
    """

    if per_league < 1:
        raise ValueError("per_league must be at least 1")
    if kind not in SAMPLE_VOLUME_COLUMNS:
        raise ValueError(f"unsupported season-stat kind: {kind!r}")

    volume_column = SAMPLE_VOLUME_COLUMNS[kind]
    required = {"league_id", "player_id", volume_column}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(
            f"{kind} reconciliation sampling missing required columns: {missing}"
        )

    working = (
        frame.select(
            _integer_like_expr("league_id", "league_id"),
            _integer_like_expr("player_id", "player_id"),
            _integer_like_expr(volume_column, "__volume"),
        )
        .drop_nulls(["league_id", "player_id", "__volume"])
        .filter(pl.col("__volume") > 0)
    )
    player_league_counts = working.group_by("player_id").agg(
        pl.col("league_id").n_unique().alias("__league_count")
    )
    candidates = (
        working.join(player_league_counts, on="player_id", how="left")
        .filter(pl.col("__league_count") == 1)
        .group_by(["league_id", "player_id"])
        .agg(pl.col("__volume").sum().alias("sample_volume"))
        .sort(
            ["league_id", "sample_volume", "player_id"],
            descending=[False, True, False],
        )
    )
    if candidates.is_empty():
        return []

    selected = (
        candidates.group_by("league_id", maintain_order=True)
        .head(per_league)
        .sort(
            ["league_id", "sample_volume", "player_id"],
            descending=[False, True, False],
        )
    )
    return [
        {
            "league_id": int(row["league_id"]),
            "player_id": int(row["player_id"]),
            "sample_volume": int(row["sample_volume"]),
        }
        for row in selected.to_dicts()
    ]
