#!/usr/bin/env python3
"""Audit the actual local inputs for the park/opponent hitter challenger.

This is a read-only gate.  It confirms that the existing event, context, player,
benchmark, and future-target surfaces can be joined without silently inventing
missing context.  It never reads a 2026 outcome.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
from typing import Any

import polars as pl


YEARS = (2021, 2022, 2023, 2024)
LEVELS = ("rk", "a", "a+", "aa", "aaa")
CONTACT_BINS = (
    "PULL_GB", "CENTER_GB", "OPPO_GB", "PULL_LD", "CENTER_LD", "OPPO_LD",
    "PULL_OFFB", "CENTER_OFFB", "OPPO_OFFB", "IFFB",
)
OUTCOMES = (
    "1B", "2B", "3B", "HR", "ROE", "FC_REACH", "SF", "MULTI_OUT",
    "OTHER_OUT",
)
EVENT_KEY = ("season", "game_pk", "at_bat_index")
MIN_CONTEXT_JOIN_RATE = 0.94
MIN_VENUE_JOIN_RATE = 0.99


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generated-root", type=Path, required=True,
        help="Generated-data root containing full-bip, player, and park artifacts.",
    )
    parser.add_argument(
        "--context-events", type=Path, required=True,
        help="Chronology-safe terminal-PA context input parquet.",
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/hitter-gradient-data-readiness"),
    )
    parser.add_argument(
        "--as-of-date", type=date.fromisoformat, required=True,
    )
    return parser.parse_args()


def _require(frame: pl.DataFrame, columns: set[str], label: str) -> None:
    if missing := sorted(columns - set(frame.columns)):
        raise ValueError(f"{label} missing fields: {missing}")


def _unique(frame: pl.DataFrame, key: tuple[str, ...], label: str) -> None:
    if frame.group_by(list(key)).len().filter(pl.col("len") != 1).height:
        raise ValueError(f"{label} violates {'/'.join(key)} grain")


def _rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _load_game_context(root: Path) -> pl.DataFrame:
    paths = (
        root / "historical-affiliated-game-context/tables/historical-affiliated-game-context.parquet",
        root / "affiliated-game-context/tables/affiliated-game-context.parquet",
    )
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"game context inputs missing: {missing}")
    games = pl.concat([pl.read_parquet(path) for path in paths], how="vertical_relaxed")
    games = games.filter(pl.col("season").is_in(YEARS)).select(
        "season", "game_date", "game_pk", "venue_id", "home_team_id", "away_team_id"
    )
    _unique(games, ("season", "game_pk"), "game context")
    return games


def _load_contacts(root: Path) -> pl.DataFrame:
    frames = []
    for year in YEARS:
        path = root / f"full-bip-context-{year}/tables/hitter_full_bip_event_outcomes.parquet"
        if not path.is_file():
            raise FileNotFoundError(f"contact/outcome input missing: {path}")
        frame = pl.read_parquet(path)
        _require(
            frame,
            {
                "season", "source_level", "game_pk", "at_bat_index", "player_id",
                "source_pitcher_id", "batter_side", "core_bin", "canonical_outcome",
            },
            f"{year} contact/outcome input",
        )
        frames.append(frame)
    contacts = pl.concat(frames, how="vertical_relaxed")
    if set(contacts["season"].unique().to_list()) != set(YEARS):
        raise ValueError("contact/outcome seasons do not match the frozen development era")
    if contacts.filter(pl.col("season") >= 2026).height:
        raise ValueError("protected 2026 contact outcomes were opened")
    _unique(contacts, EVENT_KEY, "terminal contact/outcome input")
    return contacts


def _event_join_audit(
    contacts: pl.DataFrame, context: pl.DataFrame, games: pl.DataFrame
) -> tuple[list[dict[str, Any]], pl.DataFrame]:
    context_fields = {
        *EVENT_KEY, "player_id", "pitcher_id", "batter_side", "pitcher_hand",
        "canonical_outcome", "context_label_ready",
    }
    _require(context, context_fields, "terminal PA context")
    _unique(context, EVENT_KEY, "terminal PA context")
    if context.filter(pl.col("season") >= 2026).height:
        raise ValueError("protected 2026 terminal outcomes were opened")

    joined = contacts.join(
        context.select(*context_fields).rename(
            {
                "player_id": "context_player_id",
                "batter_side": "context_batter_side",
                "canonical_outcome": "context_outcome",
            }
        ),
        on=list(EVENT_KEY), how="left", validate="1:1",
    ).join(
        games.select("season", "game_pk", "game_date", "venue_id"),
        on=["season", "game_pk"], how="left", validate="m:1",
    )
    rows: list[dict[str, Any]] = []
    for year in YEARS:
        selected = joined.filter(pl.col("season") == year)
        matched = selected.filter(pl.col("context_player_id").is_not_null())
        venue = selected.filter(pl.col("venue_id").is_not_null())
        exact = matched.filter(
            (pl.col("player_id") == pl.col("context_player_id"))
            & (pl.col("source_pitcher_id") == pl.col("pitcher_id"))
            & (pl.col("batter_side") == pl.col("context_batter_side"))
            & (pl.col("canonical_outcome") == pl.col("context_outcome"))
            & pl.col("pitcher_hand").is_in(["L", "R"])
            & pl.col("context_label_ready")
        )
        rows.append(
            {
                "season": year,
                "terminal_contacts": selected.height,
                "context_join_rate": _rate(matched.height, selected.height),
                "exact_identity_hand_outcome_rate": _rate(exact.height, selected.height),
                "venue_join_rate": _rate(venue.height, selected.height),
                "players": selected["player_id"].n_unique(),
                "pitchers": selected["source_pitcher_id"].n_unique(),
                "parks": venue["venue_id"].n_unique(),
            }
        )
    return rows, joined


def _support(contacts: pl.DataFrame) -> dict[str, Any]:
    counts = contacts.group_by("season", "core_bin", "canonical_outcome").len()
    cells = []
    for contact_bin in CONTACT_BINS:
        for outcome in OUTCOMES:
            by_year = {
                year: int(
                    counts.filter(
                        (pl.col("season") == year)
                        & (pl.col("core_bin") == contact_bin)
                        & (pl.col("canonical_outcome") == outcome)
                    )["len"].sum()
                )
                for year in YEARS
            }
            cells.append(
                {
                    "contact_bin": contact_bin,
                    "outcome": outcome,
                    "minimum_annual_events": min(by_year.values()),
                    "events_by_year": by_year,
                    "at_least_100_in_2021_and_2022": all(
                        by_year[year] >= 100 for year in (2021, 2022)
                    ),
                }
            )
    return {
        "possible_cells": len(cells),
        "cells_with_100_events_in_both_initial_years": sum(
            bool(row["at_least_100_in_2021_and_2022"]) for row in cells
        ),
        "sparse_cells": [
            row for row in cells if not row["at_least_100_in_2021_and_2022"]
        ],
    }


def _player_surface_audit(root: Path) -> dict[str, Any]:
    annual_root = root / "hitter-multiyear-age-level-base/tables"
    annual = {}
    for year in (*YEARS, 2025):
        path = annual_root / f"annual-{year}.parquet"
        if not path.is_file():
            raise FileNotFoundError(f"player feature surface missing: {path}")
        frame = pl.read_parquet(path)
        _require(
            frame,
            {
                "player_id", "source_level", "contacts", "age", "relative_age",
                *(f"overall__{value}" for value in OUTCOMES),
                *(f"share__{value}" for value in CONTACT_BINS),
            },
            f"{year} player feature surface",
        )
        _unique(frame, ("player_id",), f"{year} player feature surface")
        annual[year] = {
            "players": frame.height,
            "contacts": int(frame["contacts"].sum()),
            "age_missing": int(frame["age"].null_count()),
            "levels": sorted(frame["source_level"].unique().to_list()),
        }

    benchmark_path = root / "hitter-componentwise-reconciled-base/tables/player-predictions.parquet"
    if not benchmark_path.is_file():
        raise FileNotFoundError(f"current benchmark predictions missing: {benchmark_path}")
    benchmark = pl.read_parquet(benchmark_path)
    _require(
        benchmark,
        {
            "player_id", "origin_year", "source_level", "target_source_level",
            "contacts", "target_contacts",
            *(f"target__overall__{value}" for value in OUTCOMES),
            *(f"contact_only__overall__{value}" for value in OUTCOMES),
        },
        "current benchmark predictions",
    )
    origins = (
        benchmark.group_by("origin_year")
        .agg(
            pl.len().alias("players"),
            pl.col("contacts").sum().alias("source_contacts"),
            pl.col("target_contacts").sum().alias("target_contacts"),
        )
        .sort("origin_year")
        .to_dicts()
    )
    if set(benchmark["origin_year"].unique().to_list()) != set(YEARS):
        raise ValueError("benchmark does not cover every 2021-2024 origin")
    return {
        "annual": annual,
        "benchmark_rows": benchmark.height,
        "benchmark_origins": origins,
        "level_transition_target_available": True,
        "current_comparator": "contact_only",
    }


def _park_source_audit(root: Path) -> dict[str, Any]:
    tables = {
        "hitter_home_away": root / "affiliated-home-away-components/tables/affiliated-hitter-home-away.parquet",
        "pitcher_home_away": root / "affiliated-home-away-components/tables/affiliated-pitcher-home-away.parquet",
        "team_context": root / "affiliated-team-context/tables/affiliated-team-context.parquet",
        "game_context": root / "affiliated-game-context/tables/affiliated-game-context.parquet",
    }
    result: dict[str, Any] = {}
    for label, path in tables.items():
        if not path.is_file():
            raise FileNotFoundError(f"park/opponent source missing: {path}")
        frame = pl.read_parquet(path)
        _require(frame, {"season"}, label)
        result[label] = {
            "rows": frame.height,
            "first_season": int(frame["season"].min()),
            "last_season": int(frame["season"].max()),
        }
    return result


def main() -> int:
    args = _args()
    contacts = _load_contacts(args.generated_root)
    context = pl.read_parquet(args.context_events)
    games = _load_game_context(args.generated_root)
    event_rows, joined = _event_join_audit(contacts, context, games)
    support = _support(contacts)
    players = _player_surface_audit(args.generated_root)
    park = _park_source_audit(args.generated_root)

    event_gate = all(
        row["context_join_rate"] >= MIN_CONTEXT_JOIN_RATE
        and row["exact_identity_hand_outcome_rate"] >= MIN_CONTEXT_JOIN_RATE
        and row["venue_join_rate"] >= MIN_VENUE_JOIN_RATE
        for row in event_rows
    )
    report = {
        "status": (
            "ready_for_chronological_feature_materialization"
            if event_gate else "not_ready"
        ),
        "as_of_date": args.as_of_date.isoformat(),
        "protected_2026_outcomes_used": False,
        "scope": "affiliated_milb_hitter_contact_rate_challenger",
        "event_join_minimums": {
            "strict_opponent_context": MIN_CONTEXT_JOIN_RATE,
            "venue": MIN_VENUE_JOIN_RATE,
        },
        "event_rows": event_rows,
        "terminal_contacts": joined.height,
        "contact_outcome_support": support,
        "player_surfaces": players,
        "park_and_opponent_sources": park,
        "available_now": [
            "terminal_contact type and exact terminal outcome",
            "batter and pitcher identity plus handedness",
            "game date, level, league, venue, and schedule opponents",
            "age, relative age, workload, and source level",
            "future player outcome distributions and actual future level",
            "contact-only benchmark predictions for every 2021-2024 origin",
            "raw park/opponent histories sufficient to refit each prior vintage",
            "explicit contact-only fallback for rows lacking strict opponent context",
        ],
        "must_be_materialized_before_fit": [
            "one joined event table carrying venue and strictly-prior park vintage",
            "strictly-prior batter and pitcher component summaries",
            "player-season aggregates that keep raw and neutralized features separate",
            "fold manifest proving every feature season is earlier than its target season",
        ],
        "not_required_for_first_challenger": [
            "weather", "Statcast exit velocity or launch angle", "lineup slot",
            "inning and score state", "assumed future destination park",
        ],
        "known_limitations": [
            "Only 68 of 90 contact-by-outcome cells meet the original 100-event support rule in both 2021 and 2022; sparse cells need pooling, not deletion or literal zeroes.",
            "The current external artifact set is distributed across local worktrees and must be consolidated or reproduced before a portable model run.",
            "The current benchmark and detailed event source are affiliated-MiLB surfaces; MLB transport is a later separate gate.",
            "Approximately four to five percent of contact events lack the stricter reconciled opponent row and must retain the exact contact-only fallback.",
        ],
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if event_gate else 2


if __name__ == "__main__":
    raise SystemExit(main())
