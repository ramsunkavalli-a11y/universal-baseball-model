#!/usr/bin/env python3
"""Build universal hitter historical-comparable evidence for the explorer."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.historical_hitter_performance import (
    build_historical_hitter_performance_paths,
)
from universal_baseball.prospect_arrival import build_arrival_cohort
from universal_baseball.prospect_historical_comparables import (
    DEFAULT_COMPARABLES,
    score_hitter_comparables,
)
from universal_baseball.storage import write_canonical_parquet


HORIZON = 4


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/prospect-historical-comparables"),
    )
    return parser.parse_args()


def _history_stats(root: Path) -> pl.DataFrame:
    return pl.concat(
        [pl.read_parquet(path) for path in sorted(root.glob("*/affiliated_season_stats.parquet"))],
        how="vertical_relaxed",
    )


def _outcomes(
    cohort: pl.DataFrame,
    hitting: pl.DataFrame,
    *,
    origin: int,
    runs_per_win: float,
) -> pl.DataFrame:
    annual = (
        pl.DataFrame(
            [
                {
                    "path_player_id": int(player_id),
                    "player_type": "hitter",
                    "outcome_tier_v2": "unknown",
                    "career_role": "hitter",
                    "path_year": season - origin,
                    "source_season": season,
                    "adjusted_workload": 0.0,
                    "annual_role": "inactive",
                }
                for player_id in cohort["player_id"].to_list()
                for season in range(origin + 1, origin + HORIZON + 1)
            ]
        )
        .join(
            hitting.select(
                pl.col("player_id").alias("path_player_id"),
                pl.col("season").alias("source_season"),
                pl.col("batting_plate_appearances").cast(pl.Float64).alias("raw_pa"),
            ),
            on=["path_player_id", "source_season"],
            how="left",
            validate="m:1",
        )
        .with_columns(
            pl.when(pl.col("source_season") == 2020)
            .then(pl.col("raw_pa").fill_null(0.0) * 2.7)
            .otherwise(pl.col("raw_pa").fill_null(0.0))
            .alias("adjusted_workload"),
            pl.when(pl.col("raw_pa").fill_null(0.0) > 0)
            .then(pl.lit("hitter"))
            .otherwise(pl.lit("inactive"))
            .alias("annual_role"),
        )
        .drop("raw_pa")
    )
    return (
        build_historical_hitter_performance_paths(
            annual,
            hitting,
            runs_per_win=runs_per_win,
            shortened_2020_scale=2.7,
        )
        .group_by("path_player_id")
        .agg(
            pl.col("observed_component_war").sum().alias("later_component_war"),
            pl.col("adjusted_workload").sum().alias("later_mlb_workload"),
        )
        .rename({"path_player_id": "player_id"})
    )


def _metrics(actual: np.ndarray, prediction: np.ndarray) -> dict[str, float]:
    error = prediction - actual
    return {
        "bias": float(error.mean()),
        "mae": float(np.abs(error).mean()),
        "rmse": float(np.sqrt(np.square(error).mean())),
    }


def main() -> int:
    args = _args()
    generated = Path("reports/generated")
    history_root = generated / "opportunity-history-sources-v2/tables"
    stats = _history_stats(history_root)
    snapshots = pl.read_parquet(history_root / "hitter_snapshots.parquet")
    membership = pl.read_parquet(
        generated / "opportunity-40man-history/tables/historical_40man_membership.parquet"
    )
    skill = pl.read_parquet(
        generated / "phase2-arrival-skill-source/tables/affiliated_hitting_components.parquet"
    )
    demographics = pl.read_parquet(
        generated / "player-demographics/tables/player-demographics.parquet"
    )
    debut = pl.read_parquet(
        generated / "career-mlb-outcome-inventory-2009-2025/tables/people-debut-dates.parquet"
    )
    hitting = pl.read_parquet(
        generated / "career-mlb-outcome-inventory-2009-2025/tables/mlb_hitting_components_2009_2025.parquet"
    )
    runs_per_win = float(
        json.loads(Path("docs/prospect-component-uncertainty-result.json").read_text())[
            "runs_per_win"
        ]
    )
    cohorts: dict[int, pl.DataFrame] = {}
    for origin in (2018, 2021):
        cohort = build_arrival_cohort(
            snapshots,
            stats,
            membership,
            skill,
            debut,
            snapshot_year=origin,
            horizon=HORIZON,
            player_type="hitter",
            demographics=demographics,
        )
        cohorts[origin] = (
            cohort.join(
                _outcomes(cohort, hitting, origin=origin, runs_per_win=runs_per_win),
                on="player_id",
                how="left",
                validate="1:1",
            )
            .with_columns(
                pl.col("later_component_war").fill_null(0.0),
                pl.col("later_mlb_workload").fill_null(0.0),
                pl.lit(origin).alias("origin_year"),
            )
        )

    validation_reference = cohorts[2018].join(
        cohorts[2021].select("player_id"), on="player_id", how="anti"
    )
    validation = score_hitter_comparables(
        validation_reference,
        cohorts[2021],
        comparable_count=DEFAULT_COMPARABLES,
    ).join(
        cohorts[2021].select("player_id", "later_component_war"),
        on="player_id",
        validate="1:1",
    )
    actual = validation["later_component_war"].to_numpy()
    candidate = validation["historical_component_war_4y"].to_numpy()
    population = np.full(len(actual), float(validation_reference["later_component_war"].mean()))

    reference = pl.concat([cohorts[2018], cohorts[2021]], how="vertical_relaxed")
    current_path = (
        generated
        / "phase2-prospect-arrival"
        / args.as_of_date.isoformat()
        / "hitter-arrival-probabilities.parquet"
    )
    current = pl.read_parquet(current_path)
    scored = score_hitter_comparables(reference, current)
    output = args.output_root / args.as_of_date.isoformat()
    output.mkdir(parents=True, exist_ok=True)
    write_canonical_parquet(
        scored,
        output / "hitter-comparables.parquet",
        table_name="prospect_hitter_historical_comparables",
    )

    report = {
        "as_of_date": args.as_of_date.isoformat(),
        "status": "universal_hitter_comparable_evidence_not_fv_model",
        "method": {
            "reference_origins": [2018, 2021],
            "horizon_years": HORIZON,
            "same_primary_level": True,
            "comparable_count": DEFAULT_COMPARABLES,
            "rate_regression_pa": 200.0,
            "features": [
                "age", "primary level", "current workload", "walk rate",
                "strikeout rate", "home-run rate", "extra-base-hit rate",
            ],
            "nonarrivals_scored_zero": True,
            "outside_fv_used": False,
        },
        "reference_players": reference.height,
        "current_players": scored.height,
        "time_ordered_2021_validation": {
            "players": validation.height,
            "reference_origin": 2018,
            "same_player_overlap_removed": True,
            "population_baseline": _metrics(actual, population),
            "historical_comparables": _metrics(actual, candidate),
        },
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    Path("docs/prospect-hitter-historical-comparables-result.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
