#!/usr/bin/env python3
"""Build universal pitcher historical-comparable evidence for the explorer."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

try:
    from scripts.materialize_prospect_hitter_comparables import (
        HORIZON,
        _conditional_rate_metrics,
        _conditional_support_sensitivity,
        _history_stats,
        _validation_summary,
    )
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from materialize_prospect_hitter_comparables import (
        HORIZON,
        _conditional_rate_metrics,
        _conditional_support_sensitivity,
        _history_stats,
        _validation_summary,
    )
from universal_baseball.historical_pitcher_performance import (
    build_historical_pitcher_performance_paths,
)
from universal_baseball.prospect_arrival import build_arrival_cohort
from universal_baseball.prospect_historical_comparables import (
    CONDITIONAL_MINIMUM_NEIGHBOR_ARRIVALS,
    DEFAULT_COMPARABLES,
    primary_exact_level,
    score_pitcher_comparables,
)
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/prospect-historical-comparables"),
    )
    return parser.parse_args()


def _outcomes(
    cohort: pl.DataFrame,
    pitching: pl.DataFrame,
    *,
    origin: int,
    runs_per_win: float,
    horizon: int = HORIZON,
) -> pl.DataFrame:
    annual = (
        pl.DataFrame([
            {
                "path_player_id": int(player_id),
                "player_type": "pitcher",
                "outcome_tier_v2": "unknown",
                "career_role": "pitcher",
                "path_year": season - origin,
                "source_season": season,
                "adjusted_workload": 0.0,
                "annual_role": "inactive",
            }
            for player_id in cohort["player_id"].to_list()
            for season in range(origin + 1, origin + horizon + 1)
        ])
        .join(
            pitching.select(
                pl.col("player_id").alias("path_player_id"),
                pl.col("season").alias("source_season"),
                pl.col("pitching_bf").cast(pl.Float64).alias("raw_bf"),
            ),
            on=["path_player_id", "source_season"],
            how="left",
            validate="m:1",
        )
        .with_columns(
            pl.when(pl.col("source_season") == 2020)
            .then(pl.col("raw_bf").fill_null(0.0) * 2.7)
            .otherwise(pl.col("raw_bf").fill_null(0.0))
            .alias("adjusted_workload"),
            pl.when(pl.col("raw_bf").fill_null(0.0) > 0)
            .then(pl.lit("pitcher"))
            .otherwise(pl.lit("inactive"))
            .alias("annual_role"),
        )
        .drop("raw_bf")
    )
    return (
        build_historical_pitcher_performance_paths(
            annual, pitching, runs_per_win=runs_per_win, shortened_2020_scale=2.7
        )
        .group_by("path_player_id")
        .agg(
            pl.col("observed_component_war").sum().alias("later_component_war"),
            pl.col("adjusted_workload").sum().alias("later_mlb_workload"),
        )
        .rename({"path_player_id": "player_id"})
    )


def main() -> int:
    args = _args()
    generated = Path("reports/generated")
    history_root = generated / "opportunity-history-sources-v2/tables"
    stats = _history_stats(history_root)
    snapshots = pl.read_parquet(history_root / "pitcher_snapshots.parquet")
    membership = pl.read_parquet(
        generated / "opportunity-40man-history/tables/historical_40man_membership.parquet"
    )
    skill = pl.read_parquet(
        generated / "phase2-arrival-skill-source/tables/affiliated_pitching_components.parquet"
    )
    demographics = pl.read_parquet(
        generated / "player-demographics/tables/player-demographics.parquet"
    )
    debut = pl.read_parquet(
        generated / "career-mlb-outcome-inventory-2009-2025/tables/people-debut-dates.parquet"
    )
    pitching = pl.read_parquet(
        generated / "career-mlb-outcome-inventory-2009-2025/tables/mlb_pitching_2009_2025.parquet"
    )
    runs_per_win = float(
        json.loads(Path("docs/prospect-component-uncertainty-result.json").read_text())[
            "runs_per_win"
        ]
    )
    cohorts: dict[int, pl.DataFrame] = {}
    for origin in (2018, 2019, 2021):
        cohort = build_arrival_cohort(
            snapshots,
            stats,
            membership,
            skill,
            debut,
            snapshot_year=origin,
            horizon=HORIZON,
            player_type="pitcher",
            demographics=demographics,
        )
        cohorts[origin] = (
            cohort.join(
                primary_exact_level(
                    skill, season=origin, exposure="batters_faced"
                ),
                on="player_id",
                how="left",
                validate="1:1",
            )
            .with_columns(
                pl.col("primary_level_group").fill_null(pl.col("primary_level_tier")),
                pl.col("primary_exact_level_workload_share").fill_null(
                    pl.col("primary_level_workload_share")
                ),
            )
            .join(
                _outcomes(cohort, pitching, origin=origin, runs_per_win=runs_per_win),
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
    validation_by_count: dict[str, dict[str, object]] = {}
    for comparable_count in (25, 50, 100, 150, 250):
        validation = score_pitcher_comparables(
            validation_reference, cohorts[2021], comparable_count=comparable_count
        ).join(
            cohorts[2021].select(
                "player_id", "later_component_war", "later_mlb_workload"
            ),
            on="player_id",
            validate="1:1",
        )
        validation_by_count[str(comparable_count)] = _validation_summary(
            validation, validation_reference, rate_basis=800.0
        )
    conditional_prior_sensitivity: dict[str, dict[str, float | int]] = {}
    for prior_players in (0, 5, 10, 25, 50):
        validation = score_pitcher_comparables(
            validation_reference,
            cohorts[2021],
            comparable_count=DEFAULT_COMPARABLES,
            conditional_prior_players=float(prior_players),
        ).join(
            cohorts[2021].select(
                "player_id", "later_component_war", "later_mlb_workload"
            ),
            on="player_id",
            validate="1:1",
        )
        conditional_prior_sensitivity[str(prior_players)] = (
            _conditional_rate_metrics(
                validation, validation_reference, rate_basis=800.0
            )
        )

    selection_reference = cohorts[2018].join(
        cohorts[2019].select("player_id"), on="player_id", how="anti"
    )
    selection_prior_sensitivity: dict[str, dict[str, float | int]] = {}
    selection_support_sensitivity: dict[str, dict[str, float | int]] = {}
    for prior_players in (0, 5, 10, 25, 50):
        selection = score_pitcher_comparables(
            selection_reference,
            cohorts[2019],
            comparable_count=DEFAULT_COMPARABLES,
            conditional_prior_players=float(prior_players),
        ).join(
            cohorts[2019].select(
                "player_id", "later_component_war", "later_mlb_workload"
            ),
            on="player_id",
            validate="1:1",
        )
        selection_prior_sensitivity[str(prior_players)] = (
            _conditional_rate_metrics(
                selection, selection_reference, rate_basis=800.0
            )
        )
        if prior_players == 0:
            selection_support_sensitivity = _conditional_support_sensitivity(
                selection, selection_reference, rate_basis=800.0
            )

    reference = (
        pl.concat([cohorts[2018], cohorts[2019], cohorts[2021]], how="vertical_relaxed")
        .sort(["player_id", "origin_year"])
        .unique("player_id", keep="last", maintain_order=True)
    )
    current = pl.read_parquet(
        generated / "phase2-prospect-arrival" / args.as_of_date.isoformat()
        / "pitcher-arrival-probabilities.parquet"
    )
    current_skill = pl.read_parquet(
        generated / "affiliated-skill-source/tables/affiliated_pitching_components.parquet"
    )
    current = (
        current.join(
            primary_exact_level(
                current_skill,
                season=args.as_of_date.year,
                exposure="batters_faced",
            ),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .with_columns(
            pl.col("primary_level_group").fill_null(pl.col("primary_level_tier")),
            pl.col("primary_exact_level_workload_share").fill_null(
                pl.col("primary_level_workload_share")
            ),
        )
    )
    scored = score_pitcher_comparables(reference, current)
    output = args.output_root / args.as_of_date.isoformat()
    output.mkdir(parents=True, exist_ok=True)
    write_canonical_parquet(
        scored,
        output / "pitcher-comparables.parquet",
        table_name="prospect_pitcher_historical_comparables",
    )
    report = {
        "as_of_date": args.as_of_date.isoformat(),
        "status": "arrival_and_expected_outcome_validated_conditional_rate_rejected",
        "method": {
            "reference_origins": [2018, 2019, 2021],
            "one_row_per_reference_player": True,
            "horizon_years": HORIZON,
            "same_primary_exact_level": True,
            "comparable_count": DEFAULT_COMPARABLES,
            "rate_regression_bf": 200.0,
            "conditional_minimum_neighbor_arrivals": (
                CONDITIONAL_MINIMUM_NEIGHBOR_ARRIVALS
            ),
            "features": [
                "age", "primary exact level", "current workload",
                "strikeout rate", "walk rate", "home-run rate", "other outcomes",
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
            **validation_by_count[str(DEFAULT_COMPARABLES)],
            "comparable_count_sensitivity": validation_by_count,
            "conditional_prior_player_sensitivity": conditional_prior_sensitivity,
        },
        "time_ordered_2019_selection": {
            "players": cohorts[2019].height,
            "reference_origin": 2018,
            "same_player_overlap_removed": True,
            "conditional_prior_player_sensitivity": selection_prior_sensitivity,
            "conditional_support_sensitivity": selection_support_sensitivity,
        },
    }
    (output / "pitcher-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    Path("docs/prospect-pitcher-historical-comparables-result.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
