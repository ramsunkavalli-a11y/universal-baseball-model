#!/usr/bin/env python3
"""Materialize mature post-debut workload priors without using scouting grades."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_outcome_quality import (
    build_post_debut_workload_paths,
    summarize_workload_priors,
)
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--people-path",
        type=Path,
        default=Path(
            "reports/generated/historical-people-control/2025-10-15/tables/people.parquet"
        ),
    )
    parser.add_argument(
        "--career-root",
        type=Path,
        default=Path("reports/generated/career-mlb-outcome-inventory/tables"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/prospect-outcome-quality"),
    )
    return parser.parse_args()


def _stability(paths: pl.DataFrame) -> list[dict[str, object]]:
    rows = []
    for player_type in ("hitter", "pitcher"):
        typed = paths.filter(pl.col("player_type") == player_type)
        for tier in ("fringe", "meaningful"):
            tiered = typed.filter(pl.col("outcome_tier") == tier)
            early = tiered.filter(pl.col("debut_year") <= 2017)
            late = tiered.filter(pl.col("debut_year") >= 2018)
            early_mean = early.get_column("adjusted_total_workload").mean()
            late_mean = late.get_column("adjusted_total_workload").mean()
            rows.append(
                {
                    "player_type": player_type,
                    "outcome_tier": tier,
                    "early_players": early.height,
                    "late_players": late.height,
                    "early_mean_workload": early_mean,
                    "late_mean_workload": late_mean,
                    "late_to_early_ratio": (
                        None
                        if early_mean in (None, 0)
                        else float(late_mean) / float(early_mean)
                    ),
                }
            )
    return rows


def main() -> int:
    args = _args()
    people = pl.read_parquet(args.people_path)
    hitter = build_post_debut_workload_paths(
        people,
        pl.read_parquet(args.career_root / "mlb_batting_2015_2024.parquet"),
        player_type="hitter",
    )
    pitcher = build_post_debut_workload_paths(
        people,
        pl.read_parquet(args.career_root / "mlb_pitching_2015_2024.parquet"),
        player_type="pitcher",
    )
    paths = pl.concat([hitter, pitcher], how="vertical_relaxed")
    priors = summarize_workload_priors(paths)
    args.output_root.mkdir(parents=True, exist_ok=True)
    storage = {
        "paths": write_canonical_parquet(
            paths,
            args.output_root / "post-debut-workload-paths.parquet",
            table_name="prospect_post_debut_workload_paths",
        ).as_record(),
        "priors": write_canonical_parquet(
            priors,
            args.output_root / "post-debut-workload-priors.parquet",
            table_name="prospect_post_debut_workload_priors",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "status": "outcome_quality_prior_development_not_integrated",
        "method": (
            "six calendar seasons beginning with true MLB debut; missing seasons are "
            "zero workload and 2020 is scaled by 162/60"
        ),
        "boundaries": {
            "debut_years": [2015, 2019],
            "publication_grades_used": False,
            "survivors_only": False,
            "six_service_seasons_claimed": False,
            "war_quality_modeled": False,
            "current_values_changed": False,
        },
        "players": {"hitter": hitter.height, "pitcher": pitcher.height},
        "priors": priors.to_dicts(),
        "early_late_stability": _stability(paths),
        "storage": storage,
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
