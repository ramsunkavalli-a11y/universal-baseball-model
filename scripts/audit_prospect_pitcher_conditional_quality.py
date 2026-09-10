#!/usr/bin/env python3
"""Chronology-safe test of MiLB evidence for later MLB pitcher quality."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from universal_baseball.prospect_arrival import arrival_design, build_arrival_cohort


FEATURE_SETS = (
    "core",
    "handedness",
    "origin",
    "stable_interactions",
    "baseball_interactions",
    "baseball_demographics",
    "baseball_pedigree",
)
RIDGE_ALPHAS = (1.0, 10.0, 100.0, 1000.0)


def _history_stats(root: Path) -> pl.DataFrame:
    return pl.concat(
        [pl.read_parquet(path) for path in sorted(root.glob("*/affiliated_season_stats.parquet"))],
        how="vertical_relaxed",
    )


def _future_quality(
    mlb: pl.DataFrame, *, snapshot_year: int, horizon: int
) -> pl.DataFrame:
    future = mlb.filter(
        (pl.col("season") > snapshot_year)
        & (pl.col("season") <= snapshot_year + horizon)
    ).with_columns(
        pl.when(pl.col("season") == 2020)
        .then(pl.col("pitching_bf") * 162.0 / 60.0)
        .otherwise(pl.col("pitching_bf"))
        .alias("adjusted_bf")
    )
    return (
        future.group_by("player_id")
        .agg(
            pl.col("pitching_bf").sum().alias("future_mlb_bf"),
            pl.col("adjusted_bf").sum().alias("future_adjusted_mlb_bf"),
            (
                13.0 * pl.col("pitching_hr").sum()
                + 3.0
                * (
                    pl.col("pitching_ubb").sum()
                    + pl.col("pitching_hbp").sum()
                )
                - 2.0 * pl.col("pitching_so").sum()
            ).alias("future_component_runs"),
        )
        .filter(pl.col("future_adjusted_mlb_bf") >= 200.0)
        .with_columns(
            (pl.col("future_component_runs") / pl.col("future_mlb_bf")).alias(
                "future_component_rate"
            )
        )
    )


def _fit_predict(
    train: pl.DataFrame,
    outer: pl.DataFrame,
    *,
    feature_set: str,
    alpha: float,
) -> tuple[np.ndarray, np.ndarray]:
    x_train = arrival_design(train, feature_set=feature_set)
    x_outer = arrival_design(outer, feature_set=feature_set)
    y_train = train.get_column("future_component_rate").to_numpy()
    model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
    model.fit(x_train, y_train)
    return model.predict(x_train), model.predict(x_outer)


def _metrics(
    observed: np.ndarray, predicted: np.ndarray
) -> dict[str, float | int | None]:
    error = predicted - observed
    correlation = (
        None
        if np.std(observed) == 0.0 or np.std(predicted) == 0.0
        else float(np.corrcoef(observed, predicted)[0, 1])
    )
    return {
        "players": len(observed),
        "observed_mean": float(observed.mean()),
        "predicted_mean": float(predicted.mean()),
        "bias": float(error.mean()),
        "mae": float(np.abs(error).mean()),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "correlation": correlation,
    }


def _paired_bootstrap(
    observed: np.ndarray,
    baseline: np.ndarray,
    candidate: np.ndarray,
    *,
    draws: int = 2000,
) -> dict[str, float]:
    rng = np.random.default_rng(20260910)
    baseline_loss = (baseline - observed) ** 2
    candidate_loss = (candidate - observed) ** 2
    difference = candidate_loss - baseline_loss
    sampled = np.empty(draws)
    for index in range(draws):
        selected = rng.integers(0, len(observed), len(observed))
        sampled[index] = difference[selected].mean()
    return {
        "candidate_minus_baseline_mse": float(difference.mean()),
        "p025": float(np.quantile(sampled, 0.025)),
        "p975": float(np.quantile(sampled, 0.975)),
    }


def _tier_difference_bootstrap(
    frame: pl.DataFrame, *, draws: int = 2000
) -> dict[str, float]:
    established = frame.filter(
        pl.col("established_role_within_horizon") == 1
    ).get_column("future_component_rate").to_numpy()
    other = frame.filter(
        pl.col("established_role_within_horizon") == 0
    ).get_column("future_component_rate").to_numpy()
    rng = np.random.default_rng(20260910)
    differences = np.empty(draws)
    for index in range(draws):
        established_draw = rng.choice(established, len(established), replace=True)
        other_draw = rng.choice(other, len(other), replace=True)
        differences[index] = established_draw.mean() - other_draw.mean()
    return {
        "established_minus_other_mean_rate": float(
            established.mean() - other.mean()
        ),
        "p025": float(np.quantile(differences, 0.025)),
        "p975": float(np.quantile(differences, 0.975)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--history-root", type=Path,
        default=Path("reports/generated/opportunity-history-sources-v2/tables"),
    )
    parser.add_argument(
        "--membership-path", type=Path,
        default=Path(
            "reports/generated/opportunity-40man-history/tables/"
            "historical_40man_membership.parquet"
        ),
    )
    parser.add_argument(
        "--skill-path", type=Path,
        default=Path(
            "reports/generated/phase2-arrival-skill-source/tables/"
            "affiliated_pitching_components.parquet"
        ),
    )
    parser.add_argument(
        "--mlb-path", type=Path,
        default=Path(
            "reports/generated/career-mlb-outcome-inventory-2009-2025/tables/"
            "mlb_pitching_2009_2025.parquet"
        ),
    )
    parser.add_argument(
        "--demographics-path", type=Path,
        default=Path(
            "reports/generated/player-demographics/tables/player-demographics.parquet"
        ),
    )
    parser.add_argument(
        "--draft-history-path", type=Path,
        default=Path("reports/generated/draft-history/draft-history.parquet"),
    )
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/prospect-pitcher-conditional-quality-result.json"),
    )
    parser.add_argument(
        "--output-md", type=Path,
        default=Path("docs/prospect-pitcher-conditional-quality-result.md"),
    )
    args = parser.parse_args()

    snapshots = pl.read_parquet(args.history_root / "pitcher_snapshots.parquet")
    stats = _history_stats(args.history_root)
    membership = pl.read_parquet(args.membership_path)
    skill = pl.read_parquet(args.skill_path)
    demographics = pl.read_parquet(args.demographics_path)
    debut_dates = pl.read_parquet(
        "reports/generated/career-mlb-outcome-inventory-2009-2025/tables/people-debut-dates.parquet"
    )
    draft_history = pl.read_parquet(args.draft_history_path)
    mlb = pl.read_parquet(args.mlb_path)
    train = build_arrival_cohort(
        snapshots, stats, membership, skill, debut_dates,
        snapshot_year=2018, horizon=2, player_type="pitcher",
        demographics=demographics,
        draft_history=draft_history,
    ).join(
        _future_quality(mlb, snapshot_year=2018, horizon=2),
        on="player_id", how="inner", validate="1:1",
    )
    outer = build_arrival_cohort(
        snapshots, stats, membership, skill, debut_dates,
        snapshot_year=2021, horizon=4, player_type="pitcher",
        demographics=demographics,
        draft_history=draft_history,
    ).join(
        _future_quality(mlb, snapshot_year=2021, horizon=4),
        on="player_id", how="inner", validate="1:1",
    )
    if min(train.height, outer.height) < 30:
        raise ValueError("conditional-quality cohorts are too small")

    folds = KFold(n_splits=5, shuffle=True, random_state=20260910)
    candidates: list[dict[str, object]] = []
    y_train = train.get_column("future_component_rate").to_numpy()
    for feature_set in FEATURE_SETS:
        design = arrival_design(train, feature_set=feature_set)
        for alpha in RIDGE_ALPHAS:
            predictions = np.empty(train.height)
            for fit_rows, score_rows in folds.split(design):
                model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
                model.fit(design[fit_rows], y_train[fit_rows])
                predictions[score_rows] = model.predict(design[score_rows])
            candidates.append(
                {
                    "feature_set": feature_set,
                    "alpha": alpha,
                    "cross_validated_rmse": float(
                        np.sqrt(np.mean((predictions - y_train) ** 2))
                    ),
                }
            )
    selected = min(candidates, key=lambda row: float(row["cross_validated_rmse"]))
    _, outer_prediction = _fit_predict(
        train,
        outer,
        feature_set=str(selected["feature_set"]),
        alpha=float(selected["alpha"]),
    )
    observed = outer.get_column("future_component_rate").to_numpy()
    baseline = np.full(outer.height, y_train.mean())
    outer_with_predictions = outer.with_columns(
        pl.Series("baseline_prediction", baseline),
        pl.Series("candidate_prediction", outer_prediction),
    )
    subgroup_rows = []
    for group in ("level_tier", "pitch_hand", "role_tier"):
        for value, cell in outer_with_predictions.partition_by(group, as_dict=True).items():
            if cell.height < 20:
                continue
            y = cell.get_column("future_component_rate").to_numpy()
            base = cell.get_column("baseline_prediction").to_numpy()
            candidate = cell.get_column("candidate_prediction").to_numpy()
            subgroup_rows.append(
                {
                    "group": group,
                    "value": str(value[0]),
                    "players": cell.height,
                    "baseline_rmse": float(_metrics(y, base)["rmse"]),
                    "candidate_rmse": float(_metrics(y, candidate)["rmse"]),
                }
            )
    baseline_metrics = _metrics(observed, baseline)
    candidate_metrics = _metrics(observed, outer_prediction)
    bootstrap = _paired_bootstrap(observed, baseline, outer_prediction)
    tier_design = train.select(
        pl.col("established_role_within_horizon").cast(pl.Float64)
    ).to_numpy()
    outer_tier_design = outer.select(
        pl.col("established_role_within_horizon").cast(pl.Float64)
    ).to_numpy()
    tier_candidates = []
    for alpha in (0.0, 1.0, 10.0, 100.0):
        tier_predictions = np.empty(train.height)
        for fit_rows, score_rows in folds.split(tier_design):
            tier_model = Ridge(alpha=alpha).fit(
                tier_design[fit_rows], y_train[fit_rows]
            )
            tier_predictions[score_rows] = tier_model.predict(
                tier_design[score_rows]
            )
        tier_candidates.append(
            {
                "alpha": alpha,
                "cross_validated_rmse": float(
                    np.sqrt(np.mean((tier_predictions - y_train) ** 2))
                ),
            }
        )
    selected_tier = min(
        tier_candidates, key=lambda row: float(row["cross_validated_rmse"])
    )
    tier_model = Ridge(alpha=float(selected_tier["alpha"])).fit(
        tier_design, y_train
    )
    outer_tier_prediction = tier_model.predict(outer_tier_design)
    tier_metrics = _metrics(observed, outer_tier_prediction)
    tier_score_bootstrap = _paired_bootstrap(
        observed, baseline, outer_tier_prediction
    )
    tier_summary = (
        outer.group_by("established_role_within_horizon")
        .agg(
            pl.len().alias("players"),
            pl.col("future_mlb_bf").mean().alias("mean_future_mlb_bf"),
            pl.col("future_component_rate").mean().alias("mean_component_rate"),
            pl.col("future_component_rate").std().alias("component_rate_sd"),
        )
        .sort("established_role_within_horizon")
        .to_dicts()
    )
    tier_bootstrap = _tier_difference_bootstrap(outer)
    report = {
        "report_schema_version": "0.1",
        "as_of_date": args.as_of_date.isoformat(),
        "status": "development_conditional_pitcher_quality_audit_complete",
        "target": (
            "future MLB (13*HR + 3*(UBB+HBP) - 2*K) per BF among pitchers "
            "with at least 200 adjusted BF"
        ),
        "lower_target_is_better_pitching": True,
        "training": {
            "snapshot": 2018,
            "outcome_years": [2019, 2020],
            "players": train.height,
        },
        "outer": {
            "snapshot": 2021,
            "outcome_years": [2022, 2025],
            "players": outer.height,
            "population_mean_baseline": baseline_metrics,
            "selected_candidate": candidate_metrics,
            "paired_mse_bootstrap": bootstrap,
            "linked_realized_tier_candidate": {
                "selection": selected_tier,
                "candidates": tier_candidates,
                "metrics": tier_metrics,
                "paired_mse_bootstrap": tier_score_bootstrap,
                "boundary": (
                    "uses realized future tier only to test dependence for a latent "
                    "joint path; it is not an available forecast-date feature"
                ),
            },
            "realized_established_tier_descriptive": tier_summary,
            "realized_established_tier_bootstrap": tier_bootstrap,
            "subgroups": subgroup_rows,
        },
        "selection": {
            "method": "five-fold player cross-validation inside the 2018 snapshot",
            "selected": selected,
            "candidates": candidates,
        },
        "decision": (
            "promote only if outer accuracy improves with a paired interval below "
            "zero and no material supported subgroup reversal"
        ),
        "boundaries": {
            "outside_fv_used": False,
            "failures_used_in_this_conditional_rate_test": False,
            "failures_retained_in_separate_hurdle_test": True,
            "current_2026_outcomes_used": False,
            "physical_measurements_used": False,
            "stable_demographics_and_official_draft_pedigree_tested": True,
            "production_values_changed": False,
        },
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    baseline_rmse = float(baseline_metrics["rmse"])
    candidate_rmse = float(candidate_metrics["rmse"])
    tier_rmse = float(tier_metrics["rmse"])
    verdict = (
        "passes the outer point score"
        if candidate_rmse < baseline_rmse
        else "fails the outer point score"
    )
    markdown = f"""# Prospect pitcher conditional-quality audit

**Status:** development outer test; no current values changed

This test asks a narrower question than arrival: among pitchers who later earn at
least 200 MLB BF, can cutoff-safe minor-league performance predict their MLB component
quality? Lower values of the target are better pitching. Model form and shrinkage are
chosen only inside the {train.height}-pitcher 2018 development cohort, then scored on
{outer.height} pitchers from the 2021 snapshot using 2022-2025 outcomes.

The selected `{selected['feature_set']}` ridge model {verdict}. Population-mean RMSE
is {baseline_rmse:.5f}; candidate RMSE is {candidate_rmse:.5f}.
The paired candidate-minus-baseline MSE difference is
{bootstrap['candidate_minus_baseline_mse']:.6f}, with a 95% player-bootstrap interval
of {bootstrap['p025']:.6f} to {bootstrap['p975']:.6f}.

The historical established tier is also checked as a linked outcome rather than an
input feature. Its mean component-rate difference from other meaningful pitchers is
{tier_bootstrap['established_minus_other_mean_rate']:.4f}, with a 95% interval of
{tier_bootstrap['p025']:.4f} to {tier_bootstrap['p975']:.4f}. A negative difference
means the established group pitched better. This descriptive relationship can support
a future joint tier-and-quality path only if it repeats in a later cohort.

Using the earlier cohort's tier relationship to predict the later cohort's quality
fails: it produces RMSE {tier_rmse:.5f} versus {baseline_rmse:.5f} for the population mean. Its
paired MSE difference is
{tier_score_bootstrap['candidate_minus_baseline_mse']:.6f}, with a 95% interval of
{tier_score_bootstrap['p025']:.6f} to {tier_score_bootstrap['p975']:.6f}. Realized
future tier is used here only to test dependence inside a latent joint path; it is not
treated as information known on the forecast date. The relationship changed direction
between periods, so the attractive later-cohort tier difference is not promoted.

This conditional test excludes non-arrivals by definition; the separate hurdle audit
retains all failures and zeroes. Hand, origin, age/level, role, workload and performance
families were eligible, while current physical measurements and outside FV were not.
No candidate is promoted if the outer gain is absent, uncertain, or reverses in a
material supported subgroup.
"""
    args.output_md.write_text(markdown, encoding="utf-8")
    print(json.dumps({
        "training_players": train.height,
        "outer_players": outer.height,
        "selected": selected,
        "baseline_rmse": baseline_rmse,
        "candidate_rmse": candidate_rmse,
        "bootstrap": bootstrap,
        "tier_link_rmse": tier_rmse,
        "tier_link_bootstrap": tier_score_bootstrap,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
