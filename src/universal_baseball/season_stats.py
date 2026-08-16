"""Explicit schema adapter for reusable armstjc season-player stat releases.

The release files use compact source names such as ``batting_PA`` and
``team_league_id``. Downstream certification should not guess what those names
mean, and raw files remain immutable. This module therefore exposes a small,
versionable standardized view with common grain columns and descriptive stat
names.

Only observed and intentionally mapped fields are renamed. Missing optional
fields stay missing so source limitations remain visible.
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
}

REQUIRED_GRAIN_COLUMNS = ("season", "league_id", "team_id", "player_id")


def _column_map(kind: SeasonStatKind) -> dict[str, str]:
    if kind == "batting":
        return {**COMMON_COLUMN_MAP, **BATTING_COLUMN_MAP}
    if kind == "pitching":
        return {**COMMON_COLUMN_MAP, **PITCHING_COLUMN_MAP}
    raise ValueError(f"unsupported season-stat kind: {kind!r}")


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
