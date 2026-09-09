#!/usr/bin/env python3
"""Score current six-year hitter and pitcher opportunity paths."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_opportunity_paths import (
    HitterOpportunityFit,
    score_hitter_opportunity_paths,
)
from universal_baseball.pitcher_opportunity_paths import (
    PitcherOpportunityFit,
    score_pitcher_opportunity_paths,
)
from universal_baseball.opportunity_history_source import build_opportunity_snapshots
from universal_baseball.storage import write_canonical_parquet


def _integers(value: str) -> tuple[int, ...]:
    result = tuple(sorted({int(item.strip()) for item in value.split(",") if item.strip()}))
    if not result:
        raise argparse.ArgumentTypeError("expected comma-separated horizons")
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--forecast-year", type=int, required=True)
    parser.add_argument("--horizons", type=_integers, default=(1, 2, 3, 4, 5, 6))
    parser.add_argument("--current-source-root", type=Path, required=True)
    parser.add_argument(
        "--fit-root",
        type=Path,
        default=Path("reports/generated/opportunity-historical-fits/tables"),
    )
    parser.add_argument("--selected-hitter-next-year", type=Path)
    parser.add_argument("--selected-pitcher-next-year", type=Path)
    parser.add_argument("--selected-hitter-multihorizon", type=Path)
    parser.add_argument("--selected-pitcher-multihorizon", type=Path)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-opportunity-paths"),
    )
    return parser.parse_args()


def _coverage(paths: pl.DataFrame) -> list[dict[str, object]]:
    return (
        paths.group_by(["horizon", "coverage_tier"])
        .agg(
            pl.len().cast(pl.Int64).alias("players"),
            pl.col("mlb_active_probability").mean().alias("mean_active_probability"),
        )
        .sort(["horizon", "coverage_tier"])
        .to_dicts()
    )


def main() -> int:
    args = _parse_args()
    current_tables = args.current_source_root / "tables"
    season_root = current_tables / str(args.as_of_date.year)
    hitters, pitchers = build_opportunity_snapshots(
        pl.read_parquet(season_root / "full_roster_details.parquet"),
        pl.read_parquet(season_root / "affiliated_season_stats.parquet"),
    )
    selected = (
        pl.read_parquet(args.selected_hitter_next_year)
        if args.selected_hitter_next_year is not None
        else None
    )
    if args.selected_hitter_multihorizon is not None:
        additional = pl.read_parquet(args.selected_hitter_multihorizon)
        selected = (
            additional
            if selected is None
            else pl.concat([selected, additional], how="diagonal_relaxed")
        )
    selected_pitcher = (
        pl.read_parquet(args.selected_pitcher_next_year)
        if args.selected_pitcher_next_year is not None
        else None
    )
    if args.selected_pitcher_multihorizon is not None:
        additional = pl.read_parquet(args.selected_pitcher_multihorizon)
        selected_pitcher = (
            additional
            if selected_pitcher is None
            else pl.concat([selected_pitcher, additional], how="diagonal_relaxed")
        )
    selected_model_id = "playing_time_v1"
    selected_model_status = "selected"
    if selected is not None:
        if "model_id" in selected.columns:
            model_ids = selected.get_column("model_id").unique().to_list()
            if any(value is None for value in model_ids):
                raise ValueError("selected hitter predictions have null model_id")
            selected_model_id = (
                str(model_ids[0])
                if len(model_ids) == 1
                else "row_labeled_multiple_hitter_models"
            )
        if "model_status" in selected.columns:
            model_statuses = selected.get_column("model_status").unique().to_list()
            if any(value is None for value in model_statuses):
                raise ValueError("selected hitter predictions have null model_status")
            selected_model_status = (
                str(model_statuses[0])
                if len(model_statuses) == 1
                else "row_labeled_multiple_statuses"
            )
    selected_pitcher_model_id = "pitcher_opportunity_v1"
    selected_pitcher_model_status = "selected"
    if selected_pitcher is not None:
        if "model_id" in selected_pitcher.columns:
            model_ids = selected_pitcher.get_column("model_id").unique().to_list()
            if any(value is None for value in model_ids):
                raise ValueError("selected pitcher predictions have null model_id")
            selected_pitcher_model_id = (
                str(model_ids[0])
                if len(model_ids) == 1
                else "row_labeled_multiple_pitcher_models"
            )
        if "model_status" in selected_pitcher.columns:
            statuses = selected_pitcher.get_column("model_status").unique().to_list()
            if any(value is None for value in statuses):
                raise ValueError("selected pitcher predictions have null model_status")
            selected_pitcher_model_status = (
                str(statuses[0])
                if len(statuses) == 1
                else "row_labeled_multiple_statuses"
            )
    hitter_fit = HitterOpportunityFit(
        references=pl.read_parquet(args.fit_root / "hitter_references.parquet"),
        horizons=args.horizons,
        age_band_width=2,
        participation_prior_players=50.0,
        workload_prior_positive_players=20.0,
    )
    pitcher_fit = PitcherOpportunityFit(
        references=pl.read_parquet(args.fit_root / "pitcher_references.parquet"),
        horizons=args.horizons,
        age_band_width=2,
    )
    hitter_paths = score_hitter_opportunity_paths(
        hitters,
        hitter_fit,
        as_of_date=args.as_of_date,
        forecast_year=args.forecast_year,
        selected_next_year=selected,
        selected_model_id=selected_model_id,
        selected_model_status=selected_model_status,
    )
    pitcher_paths = score_pitcher_opportunity_paths(
        pitchers,
        pitcher_fit,
        as_of_date=args.as_of_date,
        forecast_year=args.forecast_year,
        selected_next_year=selected_pitcher,
        selected_model_id=selected_pitcher_model_id,
        selected_model_status=selected_pitcher_model_status,
    )
    args.output_root.mkdir(parents=True, exist_ok=True)
    tables = args.output_root / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    storage = {
        "hitter_paths": write_canonical_parquet(
            hitter_paths,
            tables / "hitter_opportunity_paths.parquet",
            table_name="current_hitter_opportunity_paths",
        ).as_record(),
        "pitcher_paths": write_canonical_parquet(
            pitcher_paths,
            tables / "pitcher_opportunity_paths.parquet",
            table_name="current_pitcher_opportunity_paths",
        ).as_record(),
    }
    hitter_ids = set(hitters.get_column("player_id").to_list())
    pitcher_ids = set(pitchers.get_column("player_id").to_list())
    report = {
        "report_schema_version": "0.1",
        "gate": "current_full_future_season_opportunity_paths",
        "as_of_date": args.as_of_date.isoformat(),
        "forecast_start_season": args.forecast_year,
        "horizons": list(args.horizons),
        "hitter_players": len(hitter_ids),
        "pitcher_players": len(pitcher_ids),
        "two_component_players": len(hitter_ids & pitcher_ids),
        "hitter_player_years": hitter_paths.height,
        "pitcher_player_years": pitcher_paths.height,
        "selected_hitter_model_supplied": selected is not None,
        "selected_hitter_model_id": selected_model_id if selected is not None else None,
        "selected_hitter_model_ids": (
            sorted(str(value) for value in selected.get_column("model_id").unique())
            if selected is not None and "model_id" in selected.columns
            else []
        ),
        "selected_hitter_model_status": (
            selected_model_status if selected is not None else None
        ),
        "selected_hitter_model_statuses": (
            sorted(str(value) for value in selected.get_column("model_status").unique())
            if selected is not None and "model_status" in selected.columns
            else []
        ),
        "selected_pitcher_model_supplied": selected_pitcher is not None,
        "selected_pitcher_model_id": (
            selected_pitcher_model_id if selected_pitcher is not None else None
        ),
        "selected_pitcher_model_ids": (
            sorted(
                str(value) for value in selected_pitcher.get_column("model_id").unique()
            )
            if selected_pitcher is not None and "model_id" in selected_pitcher.columns
            else []
        ),
        "selected_pitcher_model_status": (
            selected_pitcher_model_status if selected_pitcher is not None else None
        ),
        "selected_pitcher_model_statuses": (
            sorted(
                str(value)
                for value in selected_pitcher.get_column("model_status").unique()
            )
            if selected_pitcher is not None and "model_status" in selected_pitcher.columns
            else []
        ),
        "hitter_coverage": _coverage(hitter_paths),
        "pitcher_coverage": _coverage(pitcher_paths),
        "future_team_or_depth_used": False,
        "current_season_included": False,
        "current_season_boundary": "requires separate rest-of-season path",
        "protected_outcome_use": "2026 evidence used as predictor only, not evaluation target",
        "storage": storage,
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
