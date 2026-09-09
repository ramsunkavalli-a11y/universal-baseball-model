#!/usr/bin/env python3
"""Materialize universal multi-year hitter arrival and MLB PA paths."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import polars as pl

from universal_baseball.hitter_opportunity_paths import (
    build_hitter_opportunity_history,
    fit_hitter_opportunity_fallbacks,
    score_hitter_opportunity_paths,
)
from universal_baseball.storage import write_canonical_parquet


def _integers(value: str) -> tuple[int, ...]:
    result = tuple(sorted({int(item.strip()) for item in value.split(",") if item.strip()}))
    if not result:
        raise argparse.ArgumentTypeError("expected at least one comma-separated integer")
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshots", type=Path, required=True)
    parser.add_argument("--mlb-pa-outcomes", type=Path, required=True)
    parser.add_argument("--universe", type=Path, required=True)
    parser.add_argument("--selected-next-year", type=Path)
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--forecast-year", type=int, required=True)
    parser.add_argument("--horizons", type=_integers, default=(1, 2, 3, 4, 5, 6))
    parser.add_argument("--completed-seasons", type=_integers, required=True)
    parser.add_argument("--age-band-width", type=int, default=2)
    parser.add_argument("--participation-prior-players", type=float, default=50.0)
    parser.add_argument("--workload-prior-positive-players", type=float, default=20.0)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/hitter-opportunity-v1"),
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    history = build_hitter_opportunity_history(
        pl.read_parquet(args.snapshots),
        pl.read_parquet(args.mlb_pa_outcomes),
        horizons=args.horizons,
        completed_seasons=args.completed_seasons,
    )
    fit = fit_hitter_opportunity_fallbacks(
        history,
        forecast_year=args.forecast_year,
        horizons=args.horizons,
        age_band_width=args.age_band_width,
        participation_prior_players=args.participation_prior_players,
        workload_prior_positive_players=args.workload_prior_positive_players,
    )
    selected = (
        pl.read_parquet(args.selected_next_year) if args.selected_next_year is not None else None
    )
    paths = score_hitter_opportunity_paths(
        pl.read_parquet(args.universe),
        fit,
        as_of_date=args.as_of_date,
        forecast_year=args.forecast_year,
        selected_next_year=selected,
    )

    args.output_root.mkdir(parents=True, exist_ok=True)
    tables = args.output_root / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    storage = {
        "history": write_canonical_parquet(
            history,
            tables / "hitter_opportunity_history.parquet",
            table_name="hitter_opportunity_v1_history",
        ).as_record(),
        "references": write_canonical_parquet(
            fit.references,
            tables / "hitter_opportunity_references.parquet",
            table_name="hitter_opportunity_v1_references",
        ).as_record(),
        "paths": write_canonical_parquet(
            paths,
            tables / "hitter_opportunity_paths.parquet",
            table_name="hitter_opportunity_v1_paths",
        ).as_record(),
    }
    coverage = (
        paths.group_by("coverage_tier")
        .agg(pl.len().cast(pl.Int64).alias("player_years"))
        .sort("coverage_tier")
        .to_dicts()
    )
    report = {
        "report_schema_version": "0.1",
        "gate": "hitter_opportunity_v1_universal_paths",
        "as_of_date": args.as_of_date.isoformat(),
        "forecast_year": args.forecast_year,
        "horizons": list(args.horizons),
        "completed_seasons": list(args.completed_seasons),
        "history_rows": history.height,
        "historical_snapshot_players": history.select(
            "snapshot_year", "player_id"
        ).unique().height,
        "forecast_players": paths.get_column("player_id").n_unique(),
        "forecast_player_years": paths.height,
        "coverage": coverage,
        "method": {
            "next_year_preference": "frozen selected Playing Time v1 when supplied",
            "fallback": "horizon-specific age/level cohorts with hierarchical shrinkage",
            "participation_prior_players": args.participation_prior_players,
            "workload_prior_positive_players": args.workload_prior_positive_players,
            "team_depth_used": False,
            "plate_appearance_cap_used": False,
        },
        "storage": storage,
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Hitter Opportunity v1 paths",
        "",
        f"- forecast players: {report['forecast_players']:,}",
        f"- forecast player-years: {report['forecast_player_years']:,}",
        f"- horizons: {', '.join(str(value) for value in args.horizons)}",
        "- current-team depth used: no",
        "- plate-appearance cap used: no",
        "",
        "## Coverage",
        "",
        *[
            f"- {row['coverage_tier']}: {row['player_years']:,} player-years"
            for row in coverage
        ],
        "",
    ]
    (args.output_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
