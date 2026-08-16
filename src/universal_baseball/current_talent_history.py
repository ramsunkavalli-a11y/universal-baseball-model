"""Historical source-coverage planning for Current Talent materialization.

This module inventories release metadata only.  It does not infer that a season
is model-ready merely because files exist; it identifies which year x affiliated
level cells have both player-game outcome snapshots and reusable PBP contact
assets so deeper certification/materialization can be prioritized efficiently.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any, Protocol


CURRENT_AFFILIATED_FILENAME_LEVELS = ("aaa", "aa", "a+", "a", "rk")


class HistoricalAsset(Protocol):
    year: int
    filename_period: int
    filename_level: str
    size_bytes: int


def summarize_historical_source_coverage(
    pbp_assets: Iterable[HistoricalAsset],
    player_game_assets: Iterable[HistoricalAsset],
    *,
    levels: tuple[str, ...] = CURRENT_AFFILIATED_FILENAME_LEVELS,
) -> dict[str, Any]:
    """Summarize year/level overlap between PBP and player-game releases."""

    normalized_levels = tuple(str(level).strip().lower() for level in levels)
    if not normalized_levels or len(set(normalized_levels)) != len(normalized_levels):
        raise ValueError("historical source levels must be non-empty and unique")

    pbp = defaultdict(list)
    games = defaultdict(list)
    for asset in pbp_assets:
        key = (int(asset.year), str(asset.filename_level).strip().lower())
        if key[1] in normalized_levels:
            pbp[key].append(asset)
    for asset in player_game_assets:
        key = (int(asset.year), str(asset.filename_level).strip().lower())
        if key[1] in normalized_levels:
            games[key].append(asset)

    years = sorted({year for year, _ in set(pbp) | set(games)})
    cells: list[dict[str, Any]] = []
    complete_years: list[int] = []

    for year in years:
        year_complete = True
        for level in normalized_levels:
            pbp_rows = pbp.get((year, level), [])
            game_rows = games.get((year, level), [])
            pbp_periods = sorted({int(row.filename_period) for row in pbp_rows})
            game_periods = sorted({int(row.filename_period) for row in game_rows})
            common_periods = sorted(set(pbp_periods) & set(game_periods))
            has_both = bool(pbp_rows and game_rows)
            year_complete = year_complete and has_both
            cells.append(
                {
                    "year": year,
                    "filename_level": level,
                    "pbp_asset_count": len(pbp_rows),
                    "player_game_asset_count": len(game_rows),
                    "pbp_periods": pbp_periods,
                    "player_game_periods": game_periods,
                    "common_periods": common_periods,
                    "pbp_size_bytes": sum(int(row.size_bytes) for row in pbp_rows),
                    "player_game_size_bytes": sum(int(row.size_bytes) for row in game_rows),
                    "has_both_source_families": has_both,
                }
            )
        if year_complete:
            complete_years.append(year)

    latest_complete_year = max(complete_years) if complete_years else None
    return {
        "levels": list(normalized_levels),
        "observed_years": years,
        "complete_all_level_years": complete_years,
        "latest_complete_all_level_year": latest_complete_year,
        "year_level_cells": cells,
        "interpretation": (
            "Inventory overlap only. File presence does not certify event semantics, participant "
            "authority, league mapping, chronology, or frozen-Performance reconciliation."
        ),
    }
