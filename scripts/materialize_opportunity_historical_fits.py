#!/usr/bin/env python3
"""Build zero-inclusive hitter/pitcher opportunity histories and fallback fits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_opportunity_paths import (
    build_hitter_opportunity_history,
    fit_hitter_opportunity_fallbacks,
)
from universal_baseball.opportunity_history_source import build_opportunity_snapshots
from universal_baseball.pitcher_opportunity_paths import (
    build_pitcher_opportunity_history,
    fit_pitcher_opportunity_fallbacks,
)
from universal_baseball.storage import write_canonical_parquet


def _integers(value: str) -> tuple[int, ...]:
    result = tuple(sorted({int(item.strip()) for item in value.split(",") if item.strip()}))
    if not result:
        raise argparse.ArgumentTypeError("expected comma-separated integers")
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path("reports/generated/opportunity-history-sources/tables"),
    )
    parser.add_argument(
        "--outcome-root",
        type=Path,
        default=Path("reports/generated/career-mlb-outcome-inventory/tables"),
    )
    parser.add_argument("--forecast-year", type=int, default=2025)
    parser.add_argument("--horizons", type=_integers, default=(1, 2, 3, 4, 5, 6))
    parser.add_argument("--excluded-snapshot-seasons", type=_integers, default=(2020,))
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/opportunity-historical-fits"),
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    hitter_frames = []
    pitcher_frames = []
    for year_root in sorted(path for path in args.source_root.iterdir() if path.is_dir()):
        season = int(year_root.name)
        if season in args.excluded_snapshot_seasons:
            continue
        hitters, pitchers = build_opportunity_snapshots(
            pl.read_parquet(year_root / "full_roster_details.parquet"),
            pl.read_parquet(year_root / "affiliated_season_stats.parquet"),
        )
        hitter_frames.append(hitters)
        pitcher_frames.append(pitchers)
    if not hitter_frames or not pitcher_frames:
        raise ValueError("no historical source seasons are available after exclusions")
    hitter_snapshots = pl.concat(hitter_frames)
    pitcher_snapshots = pl.concat(pitcher_frames)
    batting = pl.read_parquet(args.outcome_root / "mlb_batting_2015_2024.parquet")
    pitching = pl.read_parquet(args.outcome_root / "mlb_pitching_2015_2024.parquet")
    completed = tuple(range(2015, args.forecast_year))

    hitter_history = build_hitter_opportunity_history(
        hitter_snapshots,
        batting.select("season", "player_id", pl.col("batting_pa").cast(pl.Float64)),
        horizons=args.horizons,
        completed_seasons=completed,
    )
    pitcher_history = build_pitcher_opportunity_history(
        pitcher_snapshots,
        pitching.select(
            "season",
            "player_id",
            pl.col("pitching_bf").cast(pl.Float64),
            "pitching_games",
            "pitching_starts",
        ),
        horizons=args.horizons,
        completed_seasons=completed,
    )
    hitter_fit = fit_hitter_opportunity_fallbacks(
        hitter_history, forecast_year=args.forecast_year, horizons=args.horizons
    )
    pitcher_fit = fit_pitcher_opportunity_fallbacks(
        pitcher_history, forecast_year=args.forecast_year, horizons=args.horizons
    )
    args.output_root.mkdir(parents=True, exist_ok=True)
    tables = args.output_root / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    storage = {
        "hitter_history": write_canonical_parquet(
            hitter_history, tables / "hitter_history.parquet", table_name="hitter_opportunity_history"
        ).as_record(),
        "hitter_references": write_canonical_parquet(
            hitter_fit.references, tables / "hitter_references.parquet", table_name="hitter_opportunity_references"
        ).as_record(),
        "pitcher_history": write_canonical_parquet(
            pitcher_history, tables / "pitcher_history.parquet", table_name="pitcher_opportunity_history"
        ).as_record(),
        "pitcher_references": write_canonical_parquet(
            pitcher_fit.references, tables / "pitcher_references.parquet", table_name="pitcher_opportunity_references"
        ).as_record(),
    }
    hitter_population = hitter_fit.references.filter(
        pl.col("reference_level") == "population"
    ).select(
        "horizon", "observation_count", "positive_count",
        "mlb_active_probability", "conditional_mlb_pa",
        "conditional_mlb_pa_variance",
    )
    pitcher_population = pitcher_fit.references.filter(
        pl.col("reference_level") == "population"
    ).select(
        "horizon",
        "observation_count",
        "positive_count",
        "mlb_active_probability",
        "conditional_mlb_bf",
        "conditional_mlb_bf_variance",
        "starter_probability_if_active",
        "swingman_probability_if_active",
        "reliever_probability_if_active",
    )
    report = {
        "report_schema_version": "0.1",
        "gate": "opportunity_zero_inclusive_historical_fits",
        "forecast_cutoff_year": args.forecast_year,
        "horizons": list(args.horizons),
        "excluded_snapshot_seasons": list(args.excluded_snapshot_seasons),
        "exclusion_reason": "2020 had no normal affiliated minor-league season",
        "future_team_or_depth_used": False,
        "workload_cap_used": False,
        "hitter_population_by_horizon": hitter_population.to_dicts(),
        "pitcher_population_by_horizon": pitcher_population.to_dicts(),
        "storage": storage,
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
