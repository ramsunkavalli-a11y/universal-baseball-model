"""Historical source-coverage planning for Current Talent materialization.

This module inventories release metadata and summarizes cheap player-game league
mapping evidence. It does not infer that a season is model-ready merely because
files exist; it identifies which historical slices deserve deeper semantic and
Performance reconciliation before Current Talent training.

Two inventory completeness concepts are intentionally separate:

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

import polars as pl


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


def summarize_historical_league_mapping(
    observations: pl.DataFrame,
    *,
    years: tuple[int, ...],
    levels: tuple[str, ...] = CURRENT_AFFILIATED_FILENAME_LEVELS,
) -> dict[str, Any]:
    """Summarize observed actual-league IDs from historical player-game evidence.

    This is a cheap mapping/cross-level sanity gate before downloading historical
    PBP at scale. ``observations`` should be projected player-game rows with
    explicit source year and filename level. Only regular-season batting rows
    with positive PA participate in the observed league map.

    The function deliberately does not map old league IDs to 2024 level IDs or
    claim model readiness. It records what the source actually says and fails the
    mapping gate when a league ID crosses filename levels within one season,
    player-game rows disagree on league identity, expected year/level cells are
    empty, or a retained game date falls outside its source year.
    """

    normalized_years = tuple(sorted({int(year) for year in years}))
    normalized_levels = tuple(str(level).strip().lower() for level in levels)
    if not normalized_years:
        raise ValueError("historical league mapping years cannot be empty")
    if not normalized_levels or len(set(normalized_levels)) != len(normalized_levels):
        raise ValueError("historical league mapping levels must be non-empty and unique")

    required = {
        "source_year",
        "filename_level",
        "game_id",
        "game_date",
        "game_type",
        "league_id",
        "player_id",
        "batting_PA",
        "source_asset",
    }
    missing = sorted(required - set(observations.columns))
    if missing:
        raise ValueError(f"historical league mapping observations missing fields: {missing}")
    if observations.is_empty():
        raise ValueError("historical league mapping observations cannot be empty")

    frame = observations.select(sorted(required)).with_columns(
        pl.col("source_year").cast(pl.Int64, strict=False),
        pl.col("filename_level").cast(pl.String).str.to_lowercase(),
        pl.col("game_id").cast(pl.Int64, strict=False),
        pl.col("game_date").cast(pl.String).str.to_date(strict=False),
        pl.col("game_type").cast(pl.String),
        pl.col("league_id").cast(pl.Int64, strict=False),
        pl.col("player_id").cast(pl.Int64, strict=False),
        pl.col("batting_PA").cast(pl.Float64, strict=False),
        pl.col("source_asset").cast(pl.String),
    )
    frame = frame.filter(
        pl.col("source_year").is_in(list(normalized_years))
        & pl.col("filename_level").is_in(list(normalized_levels))
    )
    eligible = frame.filter(
        (pl.col("game_type") == "R")
        & pl.col("league_id").is_not_null()
        & pl.col("game_id").is_not_null()
        & pl.col("player_id").is_not_null()
        & (pl.col("batting_PA") > 0)
    )

    date_mismatches = eligible.filter(
        pl.col("game_date").is_not_null()
        & (pl.col("game_date").dt.year() != pl.col("source_year"))
    )
    league_identity_conflicts = (
        eligible.group_by(["source_year", "filename_level", "game_id", "player_id"])
        .agg(pl.col("league_id").n_unique().alias("league_id_count"))
        .filter(pl.col("league_id_count") > 1)
    )

    dedup = eligible.unique(
        subset=["source_year", "filename_level", "game_id", "player_id", "league_id"],
        maintain_order=False,
    )
    mapping_rows: list[dict[str, Any]] = []
    missing_cells: list[dict[str, Any]] = []
    for year in normalized_years:
        for level in normalized_levels:
            cell = dedup.filter(
                (pl.col("source_year") == year) & (pl.col("filename_level") == level)
            )
            league_ids = sorted(
                int(value)
                for value in cell.get_column("league_id").drop_nulls().unique().to_list()
            )
            game_dates = cell.get_column("game_date").drop_nulls()
            row = {
                "year": year,
                "filename_level": level,
                "league_ids": league_ids,
                "league_count": len(league_ids),
                "regular_game_count": int(cell.get_column("game_id").n_unique()),
                "positive_pa_player_game_count": int(cell.height),
                "source_asset_count": int(cell.get_column("source_asset").n_unique()),
                "min_game_date": (
                    game_dates.min().isoformat() if not game_dates.is_empty() else None
                ),
                "max_game_date": (
                    game_dates.max().isoformat() if not game_dates.is_empty() else None
                ),
            }
            mapping_rows.append(row)
            if not league_ids:
                missing_cells.append({"year": year, "filename_level": level})

    cross_level_conflicts: list[dict[str, Any]] = []
    for year in normalized_years:
        year_rows = [row for row in mapping_rows if row["year"] == year]
        league_levels: dict[int, set[str]] = defaultdict(set)
        for row in year_rows:
            for league_id in row["league_ids"]:
                league_levels[int(league_id)].add(str(row["filename_level"]))
        for league_id, observed_levels in sorted(league_levels.items()):
            if len(observed_levels) > 1:
                cross_level_conflicts.append(
                    {
                        "year": year,
                        "league_id": league_id,
                        "filename_levels": sorted(observed_levels),
                    }
                )

    accepted = not (
        missing_cells
        or cross_level_conflicts
        or date_mismatches.height
        or league_identity_conflicts.height
    )
    return {
        "years": list(normalized_years),
        "levels": list(normalized_levels),
        "raw_observation_count": int(observations.height),
        "eligible_positive_pa_observation_count": int(eligible.height),
        "year_level_rows": mapping_rows,
        "missing_year_level_cells": missing_cells,
        "cross_level_league_conflicts": cross_level_conflicts,
        "date_year_mismatch_count": int(date_mismatches.height),
        "player_game_league_identity_conflict_count": int(league_identity_conflicts.height),
        "accepted_mapping_gate": bool(accepted),
        "interpretation": (
            "Observed player-game actual-league mapping only. Passing this gate does not certify "
            "historical PBP semantics, participant authority, chronology, or Performance parity."
        ),
    }
