"""Historical source-coverage planning for Current Talent materialization.

This module inventories release metadata only. It does not infer that a season
is model-ready merely because files exist; it identifies which year x affiliated
level cells have both player-game outcome snapshots and reusable PBP contact
assets so deeper certification/materialization can be prioritized efficiently.

Two completeness concepts are intentionally separate:

- source-family presence: at least one PBP and one player-game asset exist;
- period parity: the observed filename-period sets match exactly between the two
  source families for every requested level in a year.

Period parity is still only a planning gate, not semantic certification. It
prevents a sparse partial release (for example one player-game month beside six
PBP months) from being described as a complete historical training year.
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
    """Summarize year/level overlap between PBP and player-game releases.

    ``complete_all_level_years`` preserves the original broad inventory meaning:
    both source families are present at every requested level. The stricter
    ``period_parity_all_level_years`` requires matching filename-period sets at
    every requested level and is the preferred first-pass history planning gate.
    Neither field certifies baseball semantics or model readiness.
    """

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
    period_parity_years: list[int] = []

    for year in years:
        year_complete = True
        year_period_parity = True
        for level in normalized_levels:
            pbp_rows = pbp.get((year, level), [])
            game_rows = games.get((year, level), [])
            pbp_periods = sorted({int(row.filename_period) for row in pbp_rows})
            game_periods = sorted({int(row.filename_period) for row in game_rows})
            common_periods = sorted(set(pbp_periods) & set(game_periods))
            union_periods = sorted(set(pbp_periods) | set(game_periods))
            has_both = bool(pbp_rows and game_rows)
            period_sets_match = bool(has_both and pbp_periods == game_periods)
            common_period_coverage_ratio = (
                len(common_periods) / len(union_periods) if union_periods else 0.0
            )
            year_complete = year_complete and has_both
            year_period_parity = year_period_parity and period_sets_match
            cells.append(
                {
                    "year": year,
                    "filename_level": level,
                    "pbp_asset_count": len(pbp_rows),
                    "player_game_asset_count": len(game_rows),
                    "pbp_periods": pbp_periods,
                    "player_game_periods": game_periods,
                    "common_periods": common_periods,
                    "period_sets_match": period_sets_match,
                    "common_period_coverage_ratio": common_period_coverage_ratio,
                    "pbp_size_bytes": sum(int(row.size_bytes) for row in pbp_rows),
                    "player_game_size_bytes": sum(int(row.size_bytes) for row in game_rows),
                    "has_both_source_families": has_both,
                }
            )
        if year_complete:
            complete_years.append(year)
        if year_period_parity:
            period_parity_years.append(year)

    latest_complete_year = max(complete_years) if complete_years else None
    latest_period_parity_year = max(period_parity_years) if period_parity_years else None
    return {
        "levels": list(normalized_levels),
        "observed_years": years,
        "complete_all_level_years": complete_years,
        "latest_complete_all_level_year": latest_complete_year,
        "period_parity_all_level_years": period_parity_years,
        "latest_period_parity_all_level_year": latest_period_parity_year,
        "year_level_cells": cells,
        "interpretation": (
            "Inventory overlap only. Source-family presence is a weak gate; period parity is a "
            "stricter planning gate. Neither certifies event semantics, participant authority, "
            "league mapping, chronology, or frozen-Performance reconciliation."
        ),
    }
