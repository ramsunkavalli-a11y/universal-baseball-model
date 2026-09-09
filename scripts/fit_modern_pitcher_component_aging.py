#!/usr/bin/env python3
"""Fit and validate modern regressed adjacent-season pitcher component aging."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.conditional_war_rates import apply_tango_pitcher_aging
from universal_baseball.pitcher_component_aging import (
    apply_fitted_pitcher_aging,
    build_adjacent_pitcher_profiles,
    component_log_loss,
    fit_pitcher_component_aging,
)
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--development-max-target-season", type=int, default=2021)
    parser.add_argument("--validation-start-season", type=int, default=2022)
    parser.add_argument(
        "--career-root", type=Path,
        default=Path("reports/generated/career-mlb-outcome-inventory"),
    )
    parser.add_argument(
        "--current-root", type=Path,
        default=Path("reports/generated/current-mlb-skill-source"),
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/modern-pitcher-component-aging"),
    )
    return parser.parse_args()


def _ages(raw_roots: tuple[Path, ...]) -> pl.DataFrame:
    rows: dict[tuple[int, int], float] = {}
    for root in raw_roots:
        for path in sorted(root.glob("pitching-*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            for block in payload.get("stats") or []:
                for split in block.get("splits") or []:
                    player = split.get("player") or split.get("person") or {}
                    stat = split.get("stat") or {}
                    if player.get("id") is None or stat.get("age") is None:
                        continue
                    key = (int(split.get("season") or path.name.split("-")[1]), int(player["id"]))
                    age = float(stat["age"])
                    if key in rows and rows[key] != age:
                        raise ValueError(f"conflicting pitcher age for {key}")
                    rows[key] = age
    if not rows:
        raise RuntimeError("no pitcher ages found in retained official captures")
    return pl.DataFrame(
        [
            {"season": season, "player_id": player_id, "age": age}
            for (season, player_id), age in sorted(rows.items())
        ]
    )


def _history(career_root: Path, current_root: Path, as_of_date: date) -> pl.DataFrame:
    historical = pl.read_parquet(
        career_root / "tables/mlb_pitching_2015_2024.parquet"
    ).select("season", "player_id", "pitching_bf", "pitching_so", "pitching_ubb", "pitching_hbp", "pitching_hr").rename(
        {
            "pitching_bf": "bf", "pitching_so": "so", "pitching_ubb": "ubb",
            "pitching_hbp": "hbp", "pitching_hr": "hr",
        }
    )
    current = pl.read_parquet(
        current_root / as_of_date.isoformat() / "tables/mlb_pitching_components.parquet"
    ).filter(pl.col("season") == as_of_date.year - 1).group_by(
        "season", "player_id"
    ).agg(
        pl.col("pitching_batters_faced").sum().alias("bf"),
        pl.col("pitching_strike_outs").sum().alias("so"),
        (
            pl.col("pitching_base_on_balls").sum()
            - pl.col("pitching_intentional_walks").sum()
        ).alias("ubb"),
        pl.col("pitching_hit_batsmen").sum().alias("hbp"),
        pl.col("pitching_home_runs").sum().alias("hr"),
    )
    return pl.concat([historical, current]).sort(["season", "player_id"])


def main() -> int:
    args = _args()
    latest_completed = args.as_of_date.year - 1
    current_dated = args.current_root / args.as_of_date.isoformat()
    history = _history(args.career_root, args.current_root, args.as_of_date)
    ages = _ages((args.career_root / "raw", current_dated / "raw"))
    pairs = build_adjacent_pitcher_profiles(history, ages, regression_bf=200.0)
    development = fit_pitcher_component_aging(
        pairs,
        maximum_target_season=args.development_max_target_season,
        regression_bf=200.0,
        ridge_weight=20_000.0,
        model_id="pitcher_adjacent_clr_quadratic_development_v1",
    )
    validation = pairs.filter(
        pl.col("target_season").is_between(
            args.validation_start_season, latest_completed
        )
    )
    no_aging_loss = component_log_loss(
        validation, lambda source, _source_age, _target_age: source
    )
    modern_loss = component_log_loss(
        validation,
        lambda source, source_age, target_age: apply_fitted_pitcher_aging(
            source,
            current_age=source_age,
            target_age=target_age,
            parameters=development,
        ),
    )
    tango_loss = component_log_loss(
        validation,
        lambda source, source_age, target_age: apply_tango_pitcher_aging(
            source, current_age=source_age, target_age=target_age
        ),
    )
    yearly_loss: dict[str, dict[str, float]] = {}
    for season in range(args.validation_start_season, latest_completed + 1):
        year = validation.filter(pl.col("target_season") == season)
        yearly_loss[str(season)] = {
            "no_aging": component_log_loss(
                year, lambda source, _source_age, _target_age: source
            ),
            "tango_regressed_curve": component_log_loss(
                year,
                lambda source, source_age, target_age: apply_tango_pitcher_aging(
                    source, current_age=source_age, target_age=target_age
                ),
            ),
            "modern_fitted_curve": component_log_loss(
                year,
                lambda source, source_age, target_age: apply_fitted_pitcher_aging(
                    source,
                    current_age=source_age,
                    target_age=target_age,
                    parameters=development,
                ),
            ),
        }
    final = fit_pitcher_component_aging(
        pairs,
        maximum_target_season=latest_completed,
        regression_bf=200.0,
        ridge_weight=20_000.0,
        model_id="pitcher_adjacent_clr_quadratic_2015_2025_v1",
    )
    selected = modern_loss < no_aging_loss and modern_loss <= tango_loss
    output_root = args.output_root / args.as_of_date.isoformat()
    output_root.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        pairs, output_root / "adjacent-pitcher-profiles.parquet",
        table_name="regressed_adjacent_pitcher_profiles",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "gate": "modern_adjacent_pitcher_component_aging",
        "as_of_date": args.as_of_date.isoformat(),
        "source_seasons": [int(history.get_column("season").min()), latest_completed],
        "development_max_target_season": args.development_max_target_season,
        "validation_target_seasons": [args.validation_start_season, latest_completed],
        "validation_pair_count": validation.height,
        "validation_pitcher_count": validation.get_column("player_id").n_unique(),
        "validation_target_bf": int(validation.get_column("target_bf").sum()),
        "validation_log_loss": {
            "no_aging": no_aging_loss,
            "tango_regressed_curve": tango_loss,
            "modern_fitted_curve": modern_loss,
            "modern_delta_vs_no_aging": modern_loss - no_aging_loss,
            "modern_delta_vs_tango": modern_loss - tango_loss,
        },
        "validation_log_loss_by_year": yearly_loss,
        "selection_rule": "modern must beat both no aging and Tango on later seasons",
        "modern_selected": selected,
        "development_parameters": asdict(development),
        "final_parameters": asdict(final),
        "estimand": "component-rate change conditional on appearing in MLB in adjacent seasons",
        "attrition_policy": "handled by the separate participation/workload path",
        "current_partial_season_used": False,
        "storage": storage,
    }
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"gate": report["gate"], "loss": report["validation_log_loss"], "modern_selected": selected}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
