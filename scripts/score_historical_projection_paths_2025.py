#!/usr/bin/env python3
"""Score the frozen 2025 historical opportunity paths without refitting."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.historical_projection_scoring import (
    score_historical_workload_projection,
    workload_comparator_metrics,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


def _mlb_workload(
    stats: pl.DataFrame, *, stat_group: str, source_column: str, output_column: str
) -> pl.DataFrame:
    return (
        stats.filter(
            (pl.col("stat_group") == stat_group) & (pl.col("sport_id") == 1)
        )
        .group_by("player_id")
        .agg(pl.col(source_column).sum().alias(output_column))
        .sort("player_id")
    )


def main() -> int:
    projection_root = Path("reports/generated/historical-projection-paths/2025-03-27")
    source_root = Path("reports/generated/opportunity-history-sources-v2/tables")
    opening_path = Path(
        "reports/generated/fangraphs-opening-day-workbooks/2025/"
        "opening-day-projections.parquet"
    )
    hitter_path = projection_root / "tables/hitter-expected-war-paths.parquet"
    pitcher_path = projection_root / "tables/pitcher-expected-war-paths.parquet"
    prior_path = source_root / "2024/affiliated_season_stats.parquet"
    outcome_path = source_root / "2025/affiliated_season_stats.parquet"
    output = Path("reports/generated/historical-projection-score/2025-03-27")

    hitter = pl.read_parquet(hitter_path).filter(pl.col("season") == 2025)
    pitcher = pl.read_parquet(pitcher_path).filter(pl.col("season") == 2025)
    prior = pl.read_parquet(prior_path)
    outcomes = pl.read_parquet(outcome_path)
    opening = pl.read_parquet(opening_path)
    projection_report = json.loads(
        (projection_root / "report.json").read_text(encoding="utf-8")
    )
    if projection_report["boundaries"]["2025_outcomes_used"]:
        raise ValueError("historical projection artifact claims 2025 outcome use")

    hitter_outcomes = _mlb_workload(
        outcomes,
        stat_group="hitting",
        source_column="plate_appearances",
        output_column="observed_mlb_pa",
    )
    pitcher_outcomes = _mlb_workload(
        outcomes,
        stat_group="pitching",
        source_column="batters_faced",
        output_column="observed_mlb_bf",
    )
    hitter_prior = _mlb_workload(
        prior,
        stat_group="hitting",
        source_column="plate_appearances",
        output_column="prior_mlb_workload",
    )
    pitcher_prior = _mlb_workload(
        prior,
        stat_group="pitching",
        source_column="batters_faced",
        output_column="prior_mlb_workload",
    )
    hitter_scores, hitter_metrics = score_historical_workload_projection(
        hitter,
        hitter_outcomes,
        hitter_prior,
        predicted_workload_column="expected_mlb_pa",
        participation_probability_column="mlb_active_probability",
        observed_workload_column="observed_mlb_pa",
    )
    pitcher_scores, pitcher_metrics = score_historical_workload_projection(
        pitcher,
        pitcher_outcomes,
        pitcher_prior,
        predicted_workload_column="expected_mlb_bf",
        participation_probability_column="mlb_active_probability",
        observed_workload_column="observed_mlb_bf",
    )

    bf_per_ip = float(
        projection_report["fangraphs_opportunity_comparison"][
            "pitcher_bf_per_ip_conversion"
        ]
    )
    hitter_scores = hitter_scores.join(
        opening.select(
            "player_id", pl.col("projected_pa").alias("fangraphs_projected_pa")
        ),
        on="player_id",
        how="left",
        validate="1:1",
    )
    pitcher_scores = pitcher_scores.join(
        opening.select(
            "player_id",
            (pl.col("projected_ip") * bf_per_ip).alias(
                "fangraphs_implied_projected_bf"
            ),
        ),
        on="player_id",
        how="left",
        validate="1:1",
    )
    hitter_fangraphs = workload_comparator_metrics(
        hitter_scores,
        observed_column="observed_mlb_pa",
        model_column="expected_mlb_pa",
        comparator_column="fangraphs_projected_pa",
    )
    pitcher_fangraphs = workload_comparator_metrics(
        pitcher_scores,
        observed_column="observed_mlb_bf",
        model_column="expected_mlb_bf",
        comparator_column="fangraphs_implied_projected_bf",
    )

    output.mkdir(parents=True, exist_ok=True)
    storage = {
        "hitter_scores": write_canonical_parquet(
            hitter_scores,
            output / "hitter-opportunity-scores.parquet",
            table_name="historical_2025_hitter_opportunity_scores",
        ).as_record(),
        "pitcher_scores": write_canonical_parquet(
            pitcher_scores,
            output / "pitcher-opportunity-scores.parquet",
            table_name="historical_2025_pitcher_opportunity_scores",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "historical_2025_frozen_opportunity_score",
        "checkpoint_date": "2025-03-27",
        "target_season": 2025,
        "hitter": hitter_metrics,
        "pitcher": pitcher_metrics,
        "fangraphs_same_player_comparison": {
            "role": "external_comparator_not_model_input",
            "hitter": hitter_fangraphs,
            "pitcher": pitcher_fangraphs,
        },
        "boundaries": {
            "projection_refit_after_outcome_access": False,
            "model_form_changed": False,
            "threshold_changed": False,
            "fanGraphs_used_as_model_input": False,
            "outcome_absence_treated_as_zero": True,
            "scope": "opportunity_only_skill_and_value_accuracy_not_yet_scored",
        },
        "source_files": {
            path.as_posix(): sha256_file(path)
            for path in (
                hitter_path,
                pitcher_path,
                prior_path,
                outcome_path,
                opening_path,
                projection_root / "report.json",
            )
        },
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "storage"},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
