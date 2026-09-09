#!/usr/bin/env python3
"""Build current Phase 1 skill rates and join them to opportunity/control paths."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.conditional_war_rates import (
    build_hitter_conditional_war_rates,
    build_pitcher_conditional_war_rates,
)
from universal_baseball.storage import write_canonical_parquet


NON_CONTROL_STATUSES = {"free_agent", "free_agent_eligible"}


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--forecast-seasons", default="2027,2028,2029,2030,2031,2032")
    parser.add_argument(
        "--skill-source-root", type=Path,
        default=Path("reports/generated/current-mlb-skill-source"),
    )
    parser.add_argument(
        "--current-source-root", type=Path,
        default=Path("reports/generated/opportunity-current-source-2026-09-08/tables/2026"),
    )
    parser.add_argument(
        "--opportunity-root", type=Path,
        default=Path("reports/generated/current-opportunity-paths/2026-09-08/tables"),
    )
    parser.add_argument(
        "--control-path", type=Path,
        default=Path("reports/generated/league-control/2026-09-08/future-control-path.parquet"),
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/current-conditional-war-paths"),
    )
    return parser.parse_args()


def _parse_seasons(raw: str) -> tuple[int, ...]:
    seasons = tuple(sorted({int(value.strip()) for value in raw.split(",") if value.strip()}))
    if not seasons:
        raise ValueError("forecast-seasons must not be empty")
    return seasons


def _position_source(roster: pl.DataFrame) -> pl.DataFrame:
    return roster.group_by("player_id").agg(
        pl.col("position_codes").n_unique().alias("position_count"),
        pl.col("position_codes").first().alias("first_position_code"),
    ).with_columns(
        pl.when(pl.col("position_count") == 1)
        .then(pl.col("first_position_code"))
        .otherwise(pl.lit(""))
        .alias("position_code")
    ).select("player_id", "position_code")


def _attach_control(expected: pl.DataFrame, control: pl.DataFrame) -> pl.DataFrame:
    normalized = control.select(
        "player_id",
        pl.col("control_year").alias("season"),
        "control_status",
    ).with_columns(
        (~pl.col("control_status").is_in(sorted(NON_CONTROL_STATUSES))).alias(
            "is_controlled_season"
        )
    )
    return expected.join(normalized, on=["player_id", "season"], how="left").with_columns(
        pl.when(pl.col("control_status").is_null())
        .then(pl.lit("missing"))
        .otherwise(pl.lit("matched"))
        .alias("control_coverage"),
        pl.when(pl.col("control_status").is_null())
        .then(None)
        .when(pl.col("is_controlled_season"))
        .then(pl.col("expected_war"))
        .otherwise(0.0)
        .alias("controlled_expected_war"),
    )


def _coverage(frame: pl.DataFrame) -> dict[str, int]:
    return {
        "player_years": frame.height,
        "control_matched_player_years": frame.filter(pl.col("control_coverage") == "matched").height,
        "control_missing_player_years": frame.filter(pl.col("control_coverage") == "missing").height,
        "population_prior_player_years": frame.filter(pl.col("evidence_tier") == "population_prior").height,
    }


def main() -> int:
    args = _args()
    seasons = _parse_seasons(args.forecast_seasons)
    skill_root = args.skill_source_root / args.as_of_date.isoformat()
    source_report = json.loads((skill_root / "report.json").read_text(encoding="utf-8"))
    reference = source_report["reference_environment"]
    hitting = pl.read_parquet(skill_root / "tables/mlb_hitting_components.parquet")
    pitching = pl.read_parquet(skill_root / "tables/mlb_pitching_components.parquet")
    hitter_snapshot = pl.read_parquet(args.current_source_root / "hitter_snapshot.parquet")
    pitcher_snapshot = pl.read_parquet(args.current_source_root / "pitcher_snapshot.parquet")
    roster = pl.read_parquet(args.current_source_root / "full_roster_details.parquet")
    hitter_players = hitter_snapshot.select("player_id", "age_years").join(
        _position_source(roster), on="player_id", how="left"
    ).with_columns(pl.col("position_code").fill_null(""))
    pitcher_players = pitcher_snapshot.select("player_id", "age_years")

    hitter_rates = build_hitter_conditional_war_rates(
        hitter_players, hitting, current_season=args.as_of_date.year,
        forecast_seasons=seasons,
        reference_plate_appearances=int(reference["batting_plate_appearances"]),
        runs_per_win=float(reference["runs_per_win"]),
    )
    pitcher_rates = build_pitcher_conditional_war_rates(
        pitcher_players, pitching, current_season=args.as_of_date.year,
        forecast_seasons=seasons,
        reference_batters_faced=int(reference["pitching_batters_faced"]),
        runs_per_win=float(reference["runs_per_win"]),
    )
    hitter_opportunity = pl.read_parquet(args.opportunity_root / "hitter_opportunity_paths.parquet")
    pitcher_opportunity = pl.read_parquet(args.opportunity_root / "pitcher_opportunity_paths.parquet")
    hitter_expected = hitter_opportunity.join(
        hitter_rates, on=["player_id", "season"], how="inner", validate="1:1"
    ).with_columns(
        (pl.col("mlb_active_probability") * pl.col("conditional_mlb_pa")
         * pl.col("conditional_war_per_600_pa") / 600.0).alias("expected_war")
    )
    pitcher_expected = pitcher_opportunity.join(
        pitcher_rates, on=["player_id", "season"], how="inner", validate="1:1"
    ).with_columns(
        (pl.col("mlb_active_probability") * pl.col("conditional_mlb_bf")
         * pl.col("conditional_war_per_800_bf") / 800.0).alias("expected_war")
    )
    if hitter_expected.height != hitter_opportunity.height or pitcher_expected.height != pitcher_opportunity.height:
        raise RuntimeError("conditional rate coverage differs from opportunity coverage")
    control = pl.read_parquet(args.control_path)
    hitter_paths = _attach_control(hitter_expected, control)
    pitcher_paths = _attach_control(pitcher_expected, control)

    output_root = args.output_root / args.as_of_date.isoformat()
    tables = output_root / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    storage = {
        "hitter_rates": write_canonical_parquet(hitter_rates, tables / "hitter_conditional_war_rates.parquet", table_name="hitter_conditional_war_rates").as_record(),
        "pitcher_rates": write_canonical_parquet(pitcher_rates, tables / "pitcher_conditional_war_rates.parquet", table_name="pitcher_conditional_war_rates").as_record(),
        "hitter_paths": write_canonical_parquet(hitter_paths, tables / "hitter_expected_war_paths.parquet", table_name="hitter_expected_war_paths").as_record(),
        "pitcher_paths": write_canonical_parquet(pitcher_paths, tables / "pitcher_expected_war_paths.parquet", table_name="pitcher_expected_war_paths").as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "current_phase1_conditional_war_and_expected_war_paths",
        "as_of_date": args.as_of_date.isoformat(),
        "forecast_seasons": list(seasons),
        "reference_environment": reference,
        "hitter": _coverage(hitter_paths),
        "pitcher": _coverage(pitcher_paths),
        "current_team_depth_used": False,
        "current_season_included": False,
        "control_missing_policy": "null; never inferred uncontrolled",
        "ranking_status": "not_publishable_baseline",
        "limitations": [
            "Hitter defense and baserunning are league-average zero fallbacks.",
            "Players without recent MLB rate history receive an explicit population prior.",
            "Pitcher contact quality and role-specific replacement/leverage are deferred.",
            "2032 and identities outside the dated control source retain null controlled WAR.",
        ],
        "storage": storage,
    }
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"gate": report["gate"], "hitter": report["hitter"], "pitcher": report["pitcher"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
