#!/usr/bin/env python3
"""Cutoff-safe four-year replay of linked hitter performance/workload paths."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.conditional_war_rates import build_hitter_conditional_war_rates
from universal_baseball.historical_hitter_performance import (
    build_historical_hitter_performance_paths,
)
from universal_baseball.level_component_translation import (
    build_translated_affiliated_profiles,
    fit_same_season_component_translation,
)
from universal_baseball.prospect_arrival import (
    build_arrival_cohort,
    fit_arrival_model,
    predict_arrival,
)
from universal_baseball.prospect_arrival_validation import (
    common_continuous_cohort_fingerprint,
    continuous_promotion_gate,
    continuous_scores,
    paired_continuous_bootstrap_difference,
)
from universal_baseball.storage import sha256_file


TIERS = ("fringe", "meaningful_only", "established")
COMPONENTS = ("ubb", "hbp", "single", "double", "triple", "hr", "other")


def _history_stats(root: Path) -> tuple[pl.DataFrame, list[Path]]:
    paths = sorted(root.glob("*/affiliated_season_stats.parquet"))
    if not paths:
        raise ValueError("history root contains no affiliated season-stat files")
    return pl.concat([pl.read_parquet(path) for path in paths], how="vertical_relaxed"), paths


def _components(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        pl.col("hit_by_pitch").alias("hbp"),
        (
            pl.col("hits")
            - pl.col("doubles")
            - pl.col("triples")
            - pl.col("home_runs")
        ).alias("single"),
        pl.col("doubles").alias("double"),
        pl.col("triples").alias("triple"),
        pl.col("home_runs").alias("hr"),
    ).with_columns(
        (pl.col("plate_appearances") - pl.sum_horizontal(*COMPONENTS[:-1])).alias("other")
    )


def _probability(two_year: pl.Expr) -> pl.Expr:
    return 1.0 - (1.0 - two_year) ** 2


def _path_means(paths: pl.DataFrame, column: str) -> dict[str, dict[int, float]]:
    cutoff = paths.filter(pl.col("window_end_year") <= 2021)
    result = {}
    for tier in (*TIERS, "pooled"):
        source = cutoff if tier == "pooled" else cutoff.filter(pl.col("outcome_tier_v2") == tier)
        result[tier] = {
            years: float(
                source.filter(pl.col("path_year") <= years)
                .group_by("path_player_id")
                .agg(pl.col(column).sum().alias("total"))["total"]
                .mean()
            )
            for years in range(1, 5)
        }
    return result


def _predict_path(
    row: dict[str, object],
    means: dict[str, dict[int, float]],
    *,
    pooled: bool,
    horizon: int = 4,
) -> float:
    arrival = float(row["four_year_arrival_probability"])
    if arrival <= 0:
        return 0.0
    meaningful = float(row["four_year_nested_meaningful_probability"])
    established = float(row["four_year_nested_established_probability"])
    masses = {
        "fringe": max(0.0, arrival - meaningful),
        "meaningful_only": max(0.0, meaningful - established),
        "established": max(0.0, established),
    }
    hazard = 1.0 - (1.0 - arrival) ** (1.0 / horizon)
    expected = 0.0
    for offset in range(horizon):
        arrival_at_offset = (1.0 - hazard) ** offset * hazard
        if pooled:
            expected += arrival_at_offset * means["pooled"][horizon - offset]
        else:
            expected += arrival_at_offset * sum(
                masses[tier] / arrival * means[tier][horizon - offset]
                for tier in TIERS
            )
    return expected


def _predict_incumbent(
    row: dict[str, object],
    workloads: dict[str, dict[int, float]],
    rates: dict[int, dict[int, float]],
    *,
    horizon: int = 4,
) -> float:
    arrival = float(row["four_year_arrival_probability"])
    if arrival <= 0:
        return 0.0
    meaningful = float(row["four_year_nested_meaningful_probability"])
    established = float(row["four_year_nested_established_probability"])
    masses = {
        "fringe": max(0.0, arrival - meaningful),
        "meaningful_only": max(0.0, meaningful - established),
        "established": max(0.0, established),
    }
    hazard = 1.0 - (1.0 - arrival) ** (1.0 / horizon)
    expected = 0.0
    for offset in range(horizon):
        arrival_at_offset = (1.0 - hazard) ** offset * hazard
        for tier in TIERS:
            for path_year in range(1, horizon + 1 - offset):
                expected += (
                    arrival_at_offset
                    * masses[tier]
                    / arrival
                    * workloads[tier][path_year]
                    * rates[int(row["player_id"])][2021 + offset + path_year]
                    / 600.0
                )
    return expected


def _metrics(frame: pl.DataFrame, prediction: str) -> dict[str, float | int]:
    error = frame[prediction] - frame["observed_four_year_component_war"]
    return {
        "players": frame.height,
        "observed_mean": float(frame["observed_four_year_component_war"].mean()),
        "predicted_mean": float(frame[prediction].mean()),
        "bias": float(error.mean()),
        "mae": float(error.abs().mean()),
        "rmse": float(error.pow(2).mean() ** 0.5),
    }


def _bootstrap(frame: pl.DataFrame, candidate: str, baseline: str) -> dict[str, float]:
    observed = frame["observed_four_year_component_war"].to_numpy()
    difference = (frame[candidate].to_numpy() - observed) ** 2 - (
        frame[baseline].to_numpy() - observed
    ) ** 2
    rng = np.random.default_rng(20260910)
    draws = np.asarray(
        [difference[rng.integers(0, len(difference), len(difference))].mean() for _ in range(2000)]
    )
    return {
        "candidate_minus_baseline_mse": float(difference.mean()),
        "p025": float(np.quantile(draws, 0.025)),
        "p975": float(np.quantile(draws, 0.975)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--history-root", type=Path, default=Path("reports/generated/opportunity-history-sources-v2/tables"))
    parser.add_argument("--membership", type=Path, default=Path("reports/generated/opportunity-40man-history/tables/historical_40man_membership.parquet"))
    parser.add_argument("--skill", type=Path, default=Path("reports/generated/phase2-arrival-skill-source/tables/affiliated_hitting_components.parquet"))
    parser.add_argument("--demographics", type=Path, default=Path("reports/generated/player-demographics/tables/player-demographics.parquet"))
    parser.add_argument("--hitting", type=Path, default=Path("reports/generated/career-mlb-outcome-inventory-2009-2025/tables/mlb_hitting_components_2009_2025.parquet"))
    parser.add_argument("--performance-paths", type=Path, default=Path("reports/generated/prospect-outcome-quality-2009-2025/post-debut-hitter-performance-paths.parquet"))
    parser.add_argument("--environment-report", type=Path, default=Path("docs/prospect-component-uncertainty-result.json"))
    parser.add_argument("--output-json", type=Path, default=Path("docs/dependent-career-linked-hitter-replay-result.json"))
    parser.add_argument("--output-md", type=Path, default=Path("docs/dependent-career-linked-hitter-replay-result.md"))
    args = parser.parse_args()

    snapshot_path = args.history_root / "hitter_snapshots.parquet"
    snapshots = pl.read_parquet(snapshot_path)
    stats, stat_paths = _history_stats(args.history_root)
    membership = pl.read_parquet(args.membership)
    skill = pl.read_parquet(args.skill)
    demographics = pl.read_parquet(args.demographics)
    debut_dates = pl.read_parquet("reports/generated/career-mlb-outcome-inventory-2009-2025/tables/people-debut-dates.parquet")
    train = build_arrival_cohort(snapshots, stats, membership, skill, debut_dates, snapshot_year=2018, horizon=2, player_type="hitter", demographics=demographics)
    scored = build_arrival_cohort(snapshots, stats, membership, skill, debut_dates, snapshot_year=2021, horizon=2, player_type="hitter", demographics=demographics)
    for target, outcome, condition in (
        ("arrived_within_horizon", "arrival", None),
        ("meaningful_role_within_horizon", "meaningful_given_arrival", "arrived_within_horizon"),
        ("established_role_within_horizon", "established_given_meaningful", "meaningful_role_within_horizon"),
    ):
        fit_data = train if condition is None else train.filter(pl.col(condition) == 1)
        scored = predict_arrival(
            fit_arrival_model(fit_data, player_type="hitter", target_column=target, outcome_name=outcome, feature_set="core"),
            scored,
        )
    scored = scored.with_columns(
        _probability(pl.col("predicted_two_year_arrival_probability")).alias("four_year_arrival_probability"),
        _probability(pl.col("predicted_two_year_meaningful_given_arrival_probability")).alias("four_year_meaningful_given_arrival_probability"),
        _probability(pl.col("predicted_two_year_established_given_meaningful_probability")).alias("four_year_established_given_meaningful_probability"),
    ).with_columns(
        (pl.col("four_year_arrival_probability") * pl.col("four_year_meaningful_given_arrival_probability")).alias("four_year_nested_meaningful_probability")
    ).with_columns(
        (pl.col("four_year_nested_meaningful_probability") * pl.col("four_year_established_given_meaningful_probability")).alias("four_year_nested_established_probability")
    )

    hitting = pl.read_parquet(args.hitting)
    runs_per_win = float(json.loads(args.environment_report.read_text(encoding="utf-8"))["runs_per_win"])
    component_skill = _components(skill)
    offsets = fit_same_season_component_translation(
        component_skill,
        exposure_column="plate_appearances",
        component_columns=COMPONENTS,
        completed_seasons=(2018, 2021),
        minimum_level_exposure=30,
    ).offsets
    profiles = build_translated_affiliated_profiles(
        scored.select("player_id"), component_skill, offsets,
        exposure_column="plate_appearances", component_columns=COMPONENTS,
        current_season=2021, reference_season=2021, regression_exposure=1200.0,
    )
    rates = build_hitter_conditional_war_rates(
        scored.select("player_id", "age_years").with_columns(pl.lit("").alias("position_code")),
        hitting,
        current_season=2021,
        forecast_seasons=(2022, 2023, 2024, 2025),
        reference_plate_appearances=int(hitting.filter(pl.col("season") == 2021)["batting_plate_appearances"].sum()),
        runs_per_win=runs_per_win,
        evidence_anchor_season=2021,
        reference_season=2021,
        affiliated_profiles=profiles,
    )
    rate_lookup = {
        int(player_id): {int(row["season"]): float(row["conditional_war_per_600_pa"]) for row in group.iter_rows(named=True)}
        for (player_id,), group in rates.partition_by("player_id", as_dict=True).items()
    }
    paths = pl.read_parquet(args.performance_paths)
    performance_means = _path_means(paths, "observed_component_war")
    workload_means = _path_means(paths, "adjusted_workload")
    observed_years = (
        pl.DataFrame(
            [
                {
                    "path_player_id": int(player_id),
                    "player_type": "hitter",
                    "outcome_tier_v2": "unknown",
                    "career_role": "hitter",
                    "path_year": season - 2021,
                    "source_season": season,
                    "adjusted_workload": 0.0,
                    "annual_role": "inactive",
                }
                for player_id in scored["player_id"].to_list()
                for season in range(2022, 2026)
            ]
        )
        .join(
            hitting.select(
                pl.col("player_id").alias("path_player_id"),
                pl.col("season").alias("source_season"),
                pl.col("batting_plate_appearances").cast(pl.Float64).alias("observed_pa"),
            ),
            on=["path_player_id", "source_season"],
            how="left",
            validate="m:1",
        )
        .with_columns(
            pl.col("observed_pa").fill_null(0.0).alias("adjusted_workload"),
            pl.when(pl.col("observed_pa").fill_null(0.0) > 0)
            .then(pl.lit("hitter"))
            .otherwise(pl.lit("inactive"))
            .alias("annual_role"),
        )
        .drop("observed_pa")
    )
    observed_paths = build_historical_hitter_performance_paths(
        observed_years, hitting, runs_per_win=runs_per_win
    )
    observed = observed_paths.group_by("path_player_id").agg(
        pl.col("observed_component_war").sum().alias("observed_four_year_component_war"),
        pl.col("adjusted_workload").sum().alias("observed_four_year_pa"),
    ).rename({"path_player_id": "player_id"})
    evaluated = scored.with_columns(
        pl.struct("four_year_arrival_probability", "four_year_nested_meaningful_probability", "four_year_nested_established_probability").map_elements(lambda row: _predict_path(row, performance_means, pooled=False), return_dtype=pl.Float64).alias("tier_linked_prediction"),
        pl.struct("four_year_arrival_probability", "four_year_nested_meaningful_probability", "four_year_nested_established_probability").map_elements(lambda row: _predict_path(row, performance_means, pooled=True), return_dtype=pl.Float64).alias("arrival_only_prediction"),
        pl.struct("player_id", "four_year_arrival_probability", "four_year_nested_meaningful_probability", "four_year_nested_established_probability").map_elements(lambda row: _predict_incumbent(row, workload_means, rate_lookup), return_dtype=pl.Float64).alias("historical_incumbent_prediction"),
    ).join(observed, on="player_id", how="left", validate="1:1").with_columns(
        pl.col("observed_four_year_component_war").fill_null(0.0),
        pl.col("observed_four_year_pa").fill_null(0.0),
        pl.lit(0.0).alias("zero_prediction"),
    ).with_columns(
        pl.when(pl.col("observed_four_year_pa") > 0)
        .then(pl.lit("arrived"))
        .otherwise(pl.lit("did_not_arrive"))
        .alias("observed_arrival_group")
    ).sort("four_year_arrival_probability").with_row_index("probability_order")
    evaluated = evaluated.with_columns(
        (pl.col("probability_order") * 5 // evaluated.height)
        .clip(upper_bound=4)
        .cast(pl.String)
        .alias("arrival_probability_quintile")
    ).drop("probability_order")
    metrics = {name: _metrics(evaluated, column) for name, column in {
        "historical_incumbent": "historical_incumbent_prediction",
        "tier_linked": "tier_linked_prediction",
        "arrival_only": "arrival_only_prediction",
        "zero": "zero_prediction",
    }.items()}
    comparisons = {
        "arrival_only_vs_incumbent": _bootstrap(evaluated, "arrival_only_prediction", "historical_incumbent_prediction"),
        "tier_linked_vs_incumbent": _bootstrap(evaluated, "tier_linked_prediction", "historical_incumbent_prediction"),
        "tier_linked_vs_arrival_only": _bootstrap(evaluated, "tier_linked_prediction", "arrival_only_prediction"),
        "arrival_only_vs_zero": _bootstrap(evaluated, "arrival_only_prediction", "zero_prediction"),
    }
    observed_values = evaluated["observed_four_year_component_war"].to_numpy()
    incumbent_values = evaluated["historical_incumbent_prediction"].to_numpy()
    candidate_values = evaluated["arrival_only_prediction"].to_numpy()
    continuous_paired = paired_continuous_bootstrap_difference(
        observed_values, incumbent_values, candidate_values
    )
    continuous_incumbent = continuous_scores(observed_values, incumbent_values)
    continuous_candidate = continuous_scores(observed_values, candidate_values)
    continuous_validation = {
        "cohort_fingerprint": common_continuous_cohort_fingerprint(
            evaluated["player_id"].to_numpy(),
            observed_values,
            {
                "historical_incumbent": incumbent_values,
                "arrival_only_path": candidate_values,
                "tier_linked_path": evaluated["tier_linked_prediction"].to_numpy(),
            },
        ),
        "incumbent": continuous_incumbent,
        "candidate": continuous_candidate,
        "paired_difference": continuous_paired,
        "promotion_gate": continuous_promotion_gate(
            continuous_incumbent,
            continuous_candidate,
            continuous_paired,
            subgroup_review_passed=False,
            fresh_confirmation=False,
        ),
    }
    blend_sensitivity = []
    for linked_weight in (0.25, 0.5, 0.75):
        blended = (
            (1.0 - linked_weight) * incumbent_values
            + linked_weight * candidate_values
        )
        blend_sensitivity.append(
            {
                "linked_weight": linked_weight,
                "scores": continuous_scores(observed_values, blended),
                "paired_difference_vs_incumbent": (
                    paired_continuous_bootstrap_difference(
                        observed_values,
                        incumbent_values,
                        blended,
                        seed=20260940 + int(linked_weight * 100),
                    )
                ),
                "status": "exposed_cohort_sensitivity_not_candidate",
            }
        )
    horizon_sensitivity = []
    for horizon in range(1, 5):
        horizon_scored = scored.with_columns(
            (
                1.0
                - (1.0 - pl.col("predicted_two_year_arrival_probability"))
                ** (horizon / 2.0)
            ).alias("four_year_arrival_probability"),
            (
                1.0
                - (
                    1.0
                    - pl.col(
                        "predicted_two_year_meaningful_given_arrival_probability"
                    )
                )
                ** (horizon / 2.0)
            ).alias("four_year_meaningful_given_arrival_probability"),
            (
                1.0
                - (
                    1.0
                    - pl.col(
                        "predicted_two_year_established_given_meaningful_probability"
                    )
                )
                ** (horizon / 2.0)
            ).alias("four_year_established_given_meaningful_probability"),
        ).with_columns(
            (
                pl.col("four_year_arrival_probability")
                * pl.col("four_year_meaningful_given_arrival_probability")
            ).alias("four_year_nested_meaningful_probability")
        ).with_columns(
            (
                pl.col("four_year_nested_meaningful_probability")
                * pl.col("four_year_established_given_meaningful_probability")
            ).alias("four_year_nested_established_probability")
        )
        horizon_observed = (
            observed_paths.filter(pl.col("path_year") <= horizon)
            .group_by("path_player_id")
            .agg(
                pl.col("observed_component_war")
                .sum()
                .alias("observed_horizon_component_war")
            )
            .rename({"path_player_id": "player_id"})
        )
        horizon_frame = (
            horizon_scored.with_columns(
                pl.struct(
                    "four_year_arrival_probability",
                    "four_year_nested_meaningful_probability",
                    "four_year_nested_established_probability",
                )
                .map_elements(
                    lambda row, h=horizon: _predict_path(
                        row, performance_means, pooled=True, horizon=h
                    ),
                    return_dtype=pl.Float64,
                )
                .alias("candidate_prediction"),
                pl.struct(
                    "player_id",
                    "four_year_arrival_probability",
                    "four_year_nested_meaningful_probability",
                    "four_year_nested_established_probability",
                )
                .map_elements(
                    lambda row, h=horizon: _predict_incumbent(
                        row, workload_means, rate_lookup, horizon=h
                    ),
                    return_dtype=pl.Float64,
                )
                .alias("incumbent_prediction"),
            )
            .join(horizon_observed, on="player_id", how="left", validate="1:1")
            .with_columns(pl.col("observed_horizon_component_war").fill_null(0.0))
        )
        horizon_y = horizon_frame["observed_horizon_component_war"].to_numpy()
        horizon_incumbent = horizon_frame["incumbent_prediction"].to_numpy()
        horizon_candidate = horizon_frame["candidate_prediction"].to_numpy()
        horizon_sensitivity.append(
            {
                "horizon_years": horizon,
                "incumbent": continuous_scores(horizon_y, horizon_incumbent),
                "arrival_only_candidate": continuous_scores(
                    horizon_y, horizon_candidate
                ),
                "paired_difference": paired_continuous_bootstrap_difference(
                    horizon_y,
                    horizon_incumbent,
                    horizon_candidate,
                    seed=20260920 + horizon,
                ),
            }
        )
    subgroups = []
    for group in (
        "level_tier",
        "bat_side",
        "observed_arrival_group",
        "arrival_probability_quintile",
    ):
        for key, cell in evaluated.partition_by(group, as_dict=True).items():
            if cell.height < 100:
                continue
            incumbent_cell = _metrics(cell, "historical_incumbent_prediction")
            tier_cell = _metrics(cell, "tier_linked_prediction")
            pooled_cell = _metrics(cell, "arrival_only_prediction")
            subgroups.append(
                {
                    "group": group,
                    "value": str(key[0]),
                    "players": cell.height,
                    "observed_mean": incumbent_cell["observed_mean"],
                    "incumbent_predicted_mean": incumbent_cell["predicted_mean"],
                    "tier_linked_predicted_mean": tier_cell["predicted_mean"],
                    "arrival_only_predicted_mean": pooled_cell["predicted_mean"],
                    "incumbent_rmse": incumbent_cell["rmse"],
                    "tier_linked_rmse": tier_cell["rmse"],
                    "arrival_only_rmse": pooled_cell["rmse"],
                }
            )
    report = {
        "report_schema_version": 1,
        "as_of_date": args.as_of_date.isoformat(),
        "status": "development_replay_complete_not_promoted",
        "scope": "batting_plus_replacement_only",
        "training_snapshot": 2018,
        "forecast_snapshot": 2021,
        "outcome_seasons": [2022, 2023, 2024, 2025],
        "path_library_cutoff": "window_end_year <= 2021",
        "metrics": metrics,
        "paired_mse_bootstrap": comparisons,
        "continuous_validation_harness": continuous_validation,
        "blend_sensitivity": blend_sensitivity,
        "horizon_sensitivity": horizon_sensitivity,
        "subgroups": subgroups,
        "decision": "reject_linked_hitter_replacement_retain_incumbent",
        "boundaries": {
            "defense_used": False,
            "baserunning_used": False,
            "position_used": False,
            "outside_fv_used": False,
            "production_values_changed": False,
            "subgroups_used_for_selection": False,
        },
        "sources": {path.as_posix(): sha256_file(path) for path in [snapshot_path, *stat_paths, args.membership, args.skill, args.demographics, args.hitting, args.performance_paths, args.environment_report]},
    }
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    incumbent = metrics["historical_incumbent"]
    linked = metrics["arrival_only"]
    comparison = comparisons["arrival_only_vs_incumbent"]
    markdown = f"""# Linked hitter path replay

Status: **development replay complete; not promoted**.

This scores batting plus replacement only. Defense, baserunning and position are
excluded from both predictions and outcomes because matching historical components
are not available at the required player-season grain.

| Players | Observed mean WAR | Incumbent mean | Linked mean | Incumbent RMSE | Linked RMSE | Zero RMSE |
|---:|---:|---:|---:|---:|---:|---:|
| {incumbent['players']:,} | {incumbent['observed_mean']:.3f} | {incumbent['predicted_mean']:.3f} | {linked['predicted_mean']:.3f} | {incumbent['rmse']:.3f} | {linked['rmse']:.3f} | {metrics['zero']['rmse']:.3f} |

The arrival-only linked path changes MSE versus the cutoff-reconstructed incumbent by
{comparison['candidate_minus_baseline_mse']:+.6f}, with a player-bootstrap 95% interval
of [{comparison['p025']:+.6f}, {comparison['p975']:+.6f}]. The 2021 cohort has already
been used in development, so this cannot promote a model or change current values.

The common-cohort guardrail finds the opposite metric tradeoff from pitchers: MAE
improves from {continuous_incumbent['mae']:.3f} to
{continuous_candidate['mae']:.3f}, but RMSE and absolute mean bias worsen. The path
mostly improves the large non-arrival group while underpredicting the smaller group
that reaches MLB, so it remains rejected.

The same pattern persists from one through four years: candidate RMSE is worse at
every prefix. MAE improves after year one because forecasts move toward zero, not
because the model captures the positive MLB tail.

A fixed 25% linked / 75% incumbent blend is promising development evidence: RMSE
improves {incumbent['rmse']:.3f} to {blend_sensitivity[0]['scores']['rmse']:.3f}, MAE
improves {incumbent['mae']:.3f} to {blend_sensitivity[0]['scores']['mae']:.3f}, and
absolute bias improves. Its paired MSE interval still crosses zero, and the exposed
cohort was used to view the weight, so it is not promoted or used in current values.
"""
    args.output_md.write_text(markdown, encoding="utf-8")
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
