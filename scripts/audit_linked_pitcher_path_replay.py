#!/usr/bin/env python3
"""Cutoff-safe four-year replay of linked pitcher performance/workload paths."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.conditional_war_rates import (
    build_pitcher_conditional_war_rates,
)
from universal_baseball.historical_pitcher_performance import (
    build_historical_pitcher_performance_paths,
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
PITCHER_COMPONENTS = ("so", "ubb", "hbp", "hr", "other")


def _history_stats(root: Path) -> pl.DataFrame:
    return pl.concat(
        [
            pl.read_parquet(path)
            for path in sorted(root.glob("*/affiliated_season_stats.parquet"))
        ],
        how="vertical_relaxed",
    )


def _four_year_probability(two_year: pl.Expr) -> pl.Expr:
    return 1.0 - (1.0 - two_year) ** 2


def _pitcher_components(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        pl.col("strike_outs").alias("so"),
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        pl.col("hit_batters").alias("hbp"),
        pl.col("home_runs").alias("hr"),
    ).with_columns(
        (
            pl.col("batters_faced")
            - pl.sum_horizontal(*PITCHER_COMPONENTS[:-1])
        ).alias("other")
    )


def _mlb_pitcher_history(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.select(
        "season",
        "player_id",
        pl.col("pitching_games").alias("pitching_games_played"),
        pl.col("pitching_starts").alias("pitching_games_started"),
        pl.col("pitching_bf").alias("pitching_batters_faced"),
        pl.col("pitching_so").alias("pitching_strike_outs"),
        pl.col("pitching_ubb").alias("pitching_base_on_balls"),
        pl.lit(0).cast(pl.Int64).alias("pitching_intentional_walks"),
        pl.col("pitching_hbp").alias("pitching_hit_batsmen"),
        pl.col("pitching_hr").alias("pitching_home_runs"),
    )


def _path_prefix_means(paths: pl.DataFrame) -> dict[str, dict[int, float]]:
    cutoff = paths.filter(pl.col("window_end_year") <= 2021)
    if cutoff.is_empty() or cutoff["window_end_year"].max() > 2021:
        raise ValueError("cutoff-specific pitcher path library is invalid")
    result = {}
    for tier in (*TIERS, "pooled"):
        tier_paths = (
            cutoff
            if tier == "pooled"
            else cutoff.filter(pl.col("outcome_tier_v2") == tier)
        )
        result[tier] = {}
        for years in range(1, 5):
            careers = (
                tier_paths.filter(pl.col("path_year") <= years)
                .group_by("path_player_id")
                .agg(pl.col("observed_component_war").sum().alias("war"))
            )
            result[tier][years] = float(careers["war"].mean())
    return result


def _path_year_workload_means(paths: pl.DataFrame) -> dict[str, dict[int, float]]:
    cutoff = paths.filter(pl.col("window_end_year") <= 2021)
    return {
        tier: {
            int(row["path_year"]): float(row["mean_adjusted_workload"])
            for row in cutoff.filter(pl.col("outcome_tier_v2") == tier)
            .group_by("path_year")
            .agg(pl.col("adjusted_workload").mean().alias("mean_adjusted_workload"))
            .iter_rows(named=True)
        }
        for tier in TIERS
    }


def _predict_war(
    row: dict[str, object], means: dict[str, dict[int, float]], *, horizon: int = 4
) -> float:
    arrival = float(row["four_year_arrival_probability"])
    if arrival <= 0.0:
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
        remaining = horizon - offset
        expected += arrival_at_offset * sum(
            masses[tier] / arrival * means[tier][remaining] for tier in TIERS
        )
    return expected


def _predict_pooled_war(
    row: dict[str, object], means: dict[str, dict[int, float]], *, horizon: int = 4
) -> float:
    arrival = float(row["four_year_arrival_probability"])
    if arrival <= 0.0:
        return 0.0
    hazard = 1.0 - (1.0 - arrival) ** (1.0 / horizon)
    return sum(
        (1.0 - hazard) ** offset * hazard * means["pooled"][horizon - offset]
        for offset in range(horizon)
    )


def _predict_incumbent_war(
    row: dict[str, object],
    workloads: dict[str, dict[int, float]],
    rates: dict[int, dict[int, float]],
    *,
    horizon: int = 4,
) -> float:
    arrival = float(row["four_year_arrival_probability"])
    if arrival <= 0.0:
        return 0.0
    player_rates = rates[int(row["player_id"])]
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
            conditional_tier_mass = masses[tier] / arrival
            for path_year in range(1, horizon + 1 - offset):
                season = 2021 + offset + path_year
                expected += (
                    arrival_at_offset
                    * conditional_tier_mass
                    * workloads[tier][path_year]
                    * player_rates[int(season)]
                    / 800.0
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
        "rmse": float((error.pow(2).mean()) ** 0.5),
    }


def _paired_bootstrap(
    frame: pl.DataFrame, candidate: str, baseline: str
) -> dict[str, float]:
    observed = frame["observed_four_year_component_war"].to_numpy()
    difference = (frame[candidate].to_numpy() - observed) ** 2 - (
        frame[baseline].to_numpy() - observed
    ) ** 2
    rng = np.random.default_rng(20260910)
    draws = np.asarray(
        [
            difference[rng.integers(0, len(difference), len(difference))].mean()
            for _ in range(2000)
        ]
    )
    return {
        "candidate_minus_baseline_mse": float(difference.mean()),
        "p025": float(np.quantile(draws, 0.025)),
        "p975": float(np.quantile(draws, 0.975)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--history-root",
        type=Path,
        default=Path("reports/generated/opportunity-history-sources-v2/tables"),
    )
    parser.add_argument(
        "--membership",
        type=Path,
        default=Path(
            "reports/generated/opportunity-40man-history/tables/historical_40man_membership.parquet"
        ),
    )
    parser.add_argument(
        "--skill",
        type=Path,
        default=Path(
            "reports/generated/phase2-arrival-skill-source/tables/affiliated_pitching_components.parquet"
        ),
    )
    parser.add_argument(
        "--demographics",
        type=Path,
        default=Path(
            "reports/generated/player-demographics/tables/player-demographics.parquet"
        ),
    )
    parser.add_argument(
        "--pitching",
        type=Path,
        default=Path(
            "reports/generated/career-mlb-outcome-inventory-2009-2025/tables/mlb_pitching_2009_2025.parquet"
        ),
    )
    parser.add_argument(
        "--performance-paths",
        type=Path,
        default=Path(
            "reports/generated/prospect-outcome-quality-2009-2025/post-debut-pitcher-performance-paths.parquet"
        ),
    )
    parser.add_argument(
        "--environment-report",
        type=Path,
        default=Path("docs/prospect-component-uncertainty-result.json"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/dependent-career-linked-pitcher-replay-result.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/dependent-career-linked-pitcher-replay-result.md"),
    )
    args = parser.parse_args()

    snapshot_path = args.history_root / "pitcher_snapshots.parquet"
    history_stat_paths = sorted(args.history_root.glob("*/affiliated_season_stats.parquet"))
    if not history_stat_paths:
        raise ValueError("history root contains no affiliated season-stat files")
    environment_report = json.loads(args.environment_report.read_text(encoding="utf-8"))
    runs_per_win = float(environment_report["runs_per_win"])
    snapshots = pl.read_parquet(snapshot_path)
    stats = _history_stats(args.history_root)
    membership = pl.read_parquet(args.membership)
    skill = pl.read_parquet(args.skill)
    demographics = pl.read_parquet(args.demographics)
    training = build_arrival_cohort(
        snapshots,
        stats,
        membership,
        skill,
        snapshot_year=2018,
        horizon=2,
        player_type="pitcher",
        demographics=demographics,
    )
    predictors = build_arrival_cohort(
        snapshots,
        stats,
        membership,
        skill,
        snapshot_year=2021,
        horizon=2,
        player_type="pitcher",
        demographics=demographics,
    )
    scored = predict_arrival(
        fit_arrival_model(training, player_type="pitcher", feature_set="core"),
        predictors,
    )
    scored = predict_arrival(
        fit_arrival_model(
            training.filter(pl.col("arrived_within_horizon") == 1),
            player_type="pitcher",
            target_column="meaningful_role_within_horizon",
            outcome_name="meaningful_given_arrival",
            feature_set="core",
        ),
        scored,
    )
    scored = (
        predict_arrival(
            fit_arrival_model(
                training.filter(pl.col("meaningful_role_within_horizon") == 1),
                player_type="pitcher",
                target_column="established_role_within_horizon",
                outcome_name="established_given_meaningful",
                feature_set="core",
            ),
            scored,
        )
        .with_columns(
            _four_year_probability(
                pl.col("predicted_two_year_arrival_probability")
            ).alias("four_year_arrival_probability"),
            _four_year_probability(
                pl.col("predicted_two_year_meaningful_given_arrival_probability")
            ).alias("four_year_meaningful_given_arrival_probability"),
            _four_year_probability(
                pl.col("predicted_two_year_established_given_meaningful_probability")
            ).alias("four_year_established_given_meaningful_probability"),
        )
        .with_columns(
            (
                pl.col("four_year_arrival_probability")
                * pl.col("four_year_meaningful_given_arrival_probability")
            ).alias("four_year_nested_meaningful_probability")
        )
        .with_columns(
            (
                pl.col("four_year_nested_meaningful_probability")
                * pl.col("four_year_established_given_meaningful_probability")
            ).alias("four_year_nested_established_probability")
        )
    )

    pitching = pl.read_parquet(args.pitching)
    component_skill = _pitcher_components(skill)
    cutoff_translation = fit_same_season_component_translation(
        component_skill,
        exposure_column="batters_faced",
        component_columns=PITCHER_COMPONENTS,
        completed_seasons=(2018, 2021),
        minimum_level_exposure=30,
    )
    incumbent_profiles = build_translated_affiliated_profiles(
        scored.select("player_id"),
        component_skill,
        cutoff_translation.offsets,
        exposure_column="batters_faced",
        component_columns=PITCHER_COMPONENTS,
        current_season=2021,
        reference_season=2021,
        regression_exposure=800.0,
    )
    incumbent_rates = build_pitcher_conditional_war_rates(
        scored.select("player_id", "age_years"),
        _mlb_pitcher_history(pitching),
        current_season=2021,
        forecast_seasons=(2022, 2023, 2024, 2025),
        reference_batters_faced=int(
            pitching.filter(pl.col("season") == 2021)["pitching_bf"].sum()
        ),
        runs_per_win=runs_per_win,
        evidence_anchor_season=2021,
        reference_season=2021,
        affiliated_profiles=incumbent_profiles,
    )
    incumbent_rate_lookup = {
        int(player_id): {
            int(row["season"]): float(row["conditional_war_per_800_bf"])
            for row in group.iter_rows(named=True)
        }
        for (player_id,), group in incumbent_rates.partition_by(
            "player_id", as_dict=True
        ).items()
    }
    player_years = (
        pl.DataFrame(
            [
                {
                    "path_player_id": int(player_id),
                    "player_type": "pitcher",
                    "outcome_tier_v2": "unknown",
                    "career_role": "unknown",
                    "path_year": year - 2021,
                    "source_season": year,
                    "adjusted_workload": 0.0,
                    "annual_role": "inactive",
                }
                for player_id in scored["player_id"].to_list()
                for year in range(2022, 2026)
            ]
        )
        .join(
            pitching.select(
                pl.col("player_id").alias("path_player_id"),
                pl.col("season").alias("source_season"),
                pl.col("pitching_bf").cast(pl.Float64).alias("observed_bf"),
            ),
            on=["path_player_id", "source_season"],
            how="left",
            validate="m:1",
        )
        .with_columns(
            pl.col("observed_bf").fill_null(0.0).alias("adjusted_workload"),
            pl.when(pl.col("observed_bf").fill_null(0.0) > 0)
            .then(pl.lit("unknown"))
            .otherwise(pl.lit("inactive"))
            .alias("annual_role"),
        )
        .drop("observed_bf")
    )
    observed_paths = build_historical_pitcher_performance_paths(
        player_years,
        pitching,
        runs_per_win=runs_per_win,
    )
    observed = (
        observed_paths.group_by("path_player_id")
        .agg(
            pl.col("observed_component_war")
            .sum()
            .alias("observed_four_year_component_war"),
            pl.col("adjusted_workload").sum().alias("observed_four_year_bf"),
        )
        .rename({"path_player_id": "player_id"})
    )
    performance_paths = pl.read_parquet(args.performance_paths)
    means = _path_prefix_means(performance_paths)
    workload_means = _path_year_workload_means(performance_paths)
    evaluated = (
        scored.with_columns(
            pl.struct(
                "four_year_arrival_probability",
                "four_year_nested_meaningful_probability",
                "four_year_nested_established_probability",
            )
            .map_elements(lambda row: _predict_war(row, means), return_dtype=pl.Float64)
            .alias("linked_predicted_war"),
            pl.struct("four_year_arrival_probability")
            .map_elements(
                lambda row: _predict_pooled_war(row, means),
                return_dtype=pl.Float64,
            )
            .alias("arrival_only_pooled_path_prediction"),
            pl.struct(
                "player_id",
                "four_year_arrival_probability",
                "four_year_nested_meaningful_probability",
                "four_year_nested_established_probability",
            )
            .map_elements(
                lambda row: _predict_incumbent_war(
                    row, workload_means, incumbent_rate_lookup
                ),
                return_dtype=pl.Float64,
            )
            .alias("historical_incumbent_prediction"),
        )
        .join(observed, on="player_id", how="left", validate="1:1")
        .with_columns(
            pl.col("observed_four_year_component_war").fill_null(0.0),
            pl.col("observed_four_year_bf").fill_null(0.0),
            pl.lit(0.0).alias("zero_prediction"),
        )
        .with_columns(
            pl.when(pl.col("observed_four_year_bf") > 0)
            .then(pl.lit("arrived"))
            .otherwise(pl.lit("did_not_arrive"))
            .alias("observed_arrival_group")
        )
    )
    ordered = evaluated.sort("four_year_arrival_probability").with_row_index(
        "probability_order"
    )
    evaluated = ordered.with_columns(
        (pl.col("probability_order") * 5 // evaluated.height)
        .clip(upper_bound=4)
        .cast(pl.String)
        .alias("arrival_probability_quintile")
    ).drop("probability_order")
    subgroup = []
    for group in (
        "level_tier",
        "role_tier",
        "pitch_hand",
        "observed_arrival_group",
        "arrival_probability_quintile",
    ):
        for key, cell in evaluated.partition_by(group, as_dict=True).items():
            if cell.height < 100:
                continue
            incumbent_cell = _metrics(cell, "historical_incumbent_prediction")
            linked_cell = _metrics(cell, "linked_predicted_war")
            pooled_cell = _metrics(cell, "arrival_only_pooled_path_prediction")
            subgroup.append(
                {
                    "group": group,
                    "value": str(key[0]),
                    "players": cell.height,
                    "observed_mean": linked_cell["observed_mean"],
                    "incumbent_predicted_mean": incumbent_cell["predicted_mean"],
                    "linked_predicted_mean": linked_cell["predicted_mean"],
                    "arrival_only_predicted_mean": pooled_cell["predicted_mean"],
                    "incumbent_rmse": incumbent_cell["rmse"],
                    "linked_rmse": linked_cell["rmse"],
                    "arrival_only_rmse": pooled_cell["rmse"],
                }
            )
    linked_metrics = _metrics(evaluated, "linked_predicted_war")
    pooled_metrics = _metrics(evaluated, "arrival_only_pooled_path_prediction")
    incumbent_metrics = _metrics(evaluated, "historical_incumbent_prediction")
    paired = _paired_bootstrap(
        evaluated, "linked_predicted_war", "arrival_only_pooled_path_prediction"
    )
    pooled_vs_zero = _paired_bootstrap(
        evaluated, "arrival_only_pooled_path_prediction", "zero_prediction"
    )
    pooled_vs_incumbent = _paired_bootstrap(
        evaluated,
        "arrival_only_pooled_path_prediction",
        "historical_incumbent_prediction",
    )
    linked_vs_incumbent = _paired_bootstrap(
        evaluated, "linked_predicted_war", "historical_incumbent_prediction"
    )
    observed_values = evaluated["observed_four_year_component_war"].to_numpy()
    incumbent_values = evaluated["historical_incumbent_prediction"].to_numpy()
    pooled_values = evaluated["arrival_only_pooled_path_prediction"].to_numpy()
    continuous_paired = paired_continuous_bootstrap_difference(
        observed_values, incumbent_values, pooled_values
    )
    continuous_incumbent = continuous_scores(observed_values, incumbent_values)
    continuous_pooled = continuous_scores(observed_values, pooled_values)
    continuous_validation = {
        "cohort_fingerprint": common_continuous_cohort_fingerprint(
            evaluated["player_id"].to_numpy(),
            observed_values,
            {
                "historical_incumbent": incumbent_values,
                "arrival_only_pooled_path": pooled_values,
                "tier_linked_path": evaluated["linked_predicted_war"].to_numpy(),
            },
        ),
        "incumbent": continuous_incumbent,
        "candidate": continuous_pooled,
        "paired_difference": continuous_paired,
        "promotion_gate": continuous_promotion_gate(
            continuous_incumbent,
            continuous_pooled,
            continuous_paired,
            subgroup_review_passed=False,
            fresh_confirmation=False,
        ),
    }
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
                    lambda row, h=horizon: _predict_pooled_war(
                        row, means, horizon=h
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
                    lambda row, h=horizon: _predict_incumbent_war(
                        row,
                        workload_means,
                        incumbent_rate_lookup,
                        horizon=h,
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
                    seed=20260910 + horizon,
                ),
            }
        )
    report = {
        "report_schema_version": 1,
        "as_of_date": args.as_of_date.isoformat(),
        "status": "development_replay_complete_not_promoted",
        "training_snapshot": 2018,
        "forecast_snapshot": 2021,
        "outcome_seasons": [2022, 2023, 2024, 2025],
        "path_library_cutoff": "window_end_year <= 2021",
        "runs_per_win": runs_per_win,
        "sources": {
            path.as_posix(): sha256_file(path)
            for path in [
                snapshot_path,
                *history_stat_paths,
                args.membership,
                args.skill,
                args.demographics,
                args.pitching,
                args.performance_paths,
                args.environment_report,
            ]
        },
        "path_prefix_means": means,
        "linked": linked_metrics,
        "arrival_only_pooled_path": pooled_metrics,
        "historical_incumbent": incumbent_metrics,
        "linked_vs_arrival_only_paired": paired,
        "arrival_only_vs_zero_paired": pooled_vs_zero,
        "arrival_only_vs_historical_incumbent_paired": pooled_vs_incumbent,
        "linked_vs_historical_incumbent_paired": linked_vs_incumbent,
        "continuous_validation_harness": continuous_validation,
        "horizon_sensitivity": horizon_sensitivity,
        "zero_baseline": _metrics(evaluated, "zero_prediction"),
        "subgroups": subgroup,
        "decision": "promising_not_proven_no_promotion",
        "limits": [
            "The 2021 cohort and hurdle have appeared in prior development work; this is chronology-safe but not fresh confirmation.",
            "This scores component WAR only, not defense-independent official WAR or trade value.",
            "The constant-hazard four-year hurdle is tested as deployed and is already known to be optimistic.",
            "All non-arrivals remain as zero observed WAR.",
            "The historical incumbent uses cutoff-fitted level translations, the deployed 800-BF regression and Tango aging, but an analytic expected workload rather than Monte Carlo draws.",
            "Subgroups are prespecified diagnostics; no subgroup is used as a separate promotion opportunity.",
        ],
        "model_effect": "none",
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    markdown = f"""# Linked pitcher path replay

Status: **development replay complete; not promoted**.

The replay fits the hurdle on the 2018 snapshot, forecasts every eligible 2021
pre-MLB pitcher, uses only six-year career paths complete by the 2021 cutoff, and
scores actual 2022-2025 MLB component WAR. Non-arrivals remain zero.

| Players | Observed mean WAR | Incumbent predicted | Linked predicted | Incumbent RMSE | Linked RMSE | Arrival-only RMSE | Zero RMSE |
|---:|---:|---:|---:|---:|---:|---:|---:|
| {linked_metrics["players"]:,} | {linked_metrics["observed_mean"]:.3f} | {incumbent_metrics["predicted_mean"]:.3f} | {linked_metrics["predicted_mean"]:.3f} | {incumbent_metrics["rmse"]:.3f} | {linked_metrics["rmse"]:.3f} | {pooled_metrics["rmse"]:.3f} | {report["zero_baseline"]["rmse"]:.3f} |

The linked construction is directionally coherent and its broad scale is plausible in
this replay: predicted mean WAR is close to observed and it beats predicting zero.
The tiered path changes MSE versus an arrival-only pooled path by
{paired["candidate_minus_baseline_mse"]:+.6f}, with a 95% interval of
[{paired["p025"]:+.6f}, {paired["p975"]:+.6f}]. This cohort and hurdle have already
been used in development, so this is not fresh confirmation. No current player value
or rank changes.

The simpler arrival-only path changes MSE versus zero by
{pooled_vs_zero["candidate_minus_baseline_mse"]:+.6f}, with a 95% interval of
[{pooled_vs_zero["p025"]:+.6f}, {pooled_vs_zero["p975"]:+.6f}].

Against the cutoff-reconstructed incumbent, the arrival-only path changes MSE by
{pooled_vs_incumbent["candidate_minus_baseline_mse"]:+.6f}, with a 95% interval of
[{pooled_vs_incumbent["p025"]:+.6f}, {pooled_vs_incumbent["p975"]:+.6f}]. The incumbent
uses only information available through 2021, including level translations fit on
2018 and 2021, the deployed 800-BF regression, and Tango component aging.

The common-cohort guardrail also shows that the small RMSE gain is not a broad error
gain: MAE worsens from {continuous_incumbent['mae']:.3f} to
{continuous_pooled['mae']:.3f}, and its paired interval is entirely unfavorable.
The path remains rejected pending a candidate that handles arrivals without adding
too much value to the much larger non-arrival group.

This tradeoff persists at every tested prefix from one through four years: candidate
MAE is worse at all four horizons, and no horizon has a reliably favorable paired MSE
interval. The failure is not caused only by extending two-year odds to four years.
"""
    args.output_md.write_text(markdown, encoding="utf-8")
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
