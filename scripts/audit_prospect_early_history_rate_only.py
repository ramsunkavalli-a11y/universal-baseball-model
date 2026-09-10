#!/usr/bin/env python3
"""Run the frozen untouched 2006-2007 aggregate rate-only tail test."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from audit_prospect_broad_history_positive_tail import (
    HORIZON,
    LOGISTIC_C,
    RUNS_PER_WIN_SOURCE,
    THRESHOLD,
    _cluster_bootstrap,
    _cohort,
    _score,
    _subgroups,
)
from audit_prospect_broad_history_skill_tail import (
    RATE_NAMES,
    REGRESSION_OPPORTUNITIES,
    _attach_counts,
    _priors,
)
from universal_baseball.storage import sha256_file


TRAIN_ORIGIN = 2003
EVALUATION_ORIGINS = (2006, 2007)
PLAN_PATH = Path("docs/prospect-early-history-rate-only-plan.md")
COHORT_CORRECTION_PATH = Path(
    "docs/prospect-broad-history-pre-mlb-cohort-correction.md"
)
DEBUT_REPORT_PATH = Path("docs/early-career-debut-date-source-result.json")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--generated-root", type=Path, default=Path("reports/generated"))
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/prospect-early-history-rate-only-result.json"),
    )
    parser.add_argument(
        "--output-md", type=Path,
        default=Path("docs/prospect-early-history-rate-only-result.md"),
    )
    return parser.parse_args()


def _rate_design(
    frame: pl.DataFrame, priors: tuple[float, float, float, float]
) -> np.ndarray:
    workload = frame["rate_workload"].to_numpy()
    return np.column_stack([
        (frame[f"event_{index}"].to_numpy() + REGRESSION_OPPORTUNITIES * prior)
        / (workload + REGRESSION_OPPORTUNITIES)
        for index, prior in enumerate(priors, start=1)
    ])


def _markdown(report: dict[str, object]) -> str:
    lines = [
        "# Prospect early-history rate-only result", "",
        f"**Decision:** `{report['decision']}`", "",
        "A rate-only model was fitted on 2003 and applied unchanged to untouched 2006 and 2007 cohorts. Negative differences favor the candidate.", "",
        "| Type | Origin | Players | Brier difference | Log-loss difference | Both improve |", "|---|---:|---:|---:|---:|---:|",
    ]
    for player_type in ("hitter", "pitcher"):
        for origin, score in report["results"][player_type]["by_origin"].items():
            brier = score["candidate"]["brier"] - score["baseline"]["brier"]
            logloss = score["candidate"]["log_loss"] - score["baseline"]["log_loss"]
            lines.append(f"| {player_type} | {origin} | {score['players']} | {brier:.4f} | {logloss:.4f} | {score['both_scores_improved']} |")
    lines += ["", "## Why", ""]
    lines.extend(f"- {reason}" for reason in report["decision_reasons"])
    lines += ["", "The production model was not changed.", ""]
    return "\n".join(lines)


def main() -> int:
    args = _args()
    root = args.generated_root
    opportunity_root = root / "opportunity-history-sources-2003-2007"
    skill_root = root / "affiliated-skill-source-2003-2007"
    outcome_root = root / "career-mlb-outcome-inventory-2004-2009"
    stat_paths = [
        opportunity_root / "tables" / str(year) / "affiliated_season_stats.parquet"
        for year in range(2003, 2008)
    ]
    stats = pl.concat([pl.read_parquet(path) for path in stat_paths], how="vertical_relaxed")
    debut_path = outcome_root / "tables/people-debut-dates.parquet"
    debut_dates = pl.read_parquet(debut_path)
    if debut_dates["mlb_debut_date"].null_count() or debut_dates["player_id"].n_unique() != debut_dates.height:
        raise ValueError("early official debut coverage is incomplete")
    runs_per_win = float(json.loads(RUNS_PER_WIN_SOURCE.read_text(encoding="utf-8"))["runs_per_win"])
    skill_paths = {
        "hitter": skill_root / "tables/affiliated_hitting_components.parquet",
        "pitcher": skill_root / "tables/affiliated_pitching_components.parquet",
    }
    component_paths = {
        "hitter": outcome_root / "tables/mlb_hitting_components_2004_2009.parquet",
        "pitcher": outcome_root / "tables/mlb_pitching_2004_2009.parquet",
    }
    results = {}
    reasons = []
    overall = True
    sources = [PLAN_PATH, COHORT_CORRECTION_PATH, DEBUT_REPORT_PATH, RUNS_PER_WIN_SOURCE, opportunity_root / "report.json", skill_root / "report.json", outcome_root / "report.json", debut_path, *stat_paths]
    for player_type in ("hitter", "pitcher"):
        snapshot_path = opportunity_root / "tables" / f"{player_type}_snapshots.parquet"
        snapshots = pl.read_parquet(snapshot_path)
        skill = pl.read_parquet(skill_paths[player_type])
        components = pl.read_parquet(component_paths[player_type])
        sources.extend([snapshot_path, skill_paths[player_type], component_paths[player_type]])
        cohorts = {}
        for origin in (TRAIN_ORIGIN, *EVALUATION_ORIGINS):
            cohort = _cohort(
                snapshots, stats, components, debut_dates,
                player_type=player_type, origin=origin, runs_per_win=runs_per_win,
            )
            cohorts[origin] = _attach_counts(
                cohort, skill, player_type=player_type, origin=origin
            )
        priors = _priors(cohorts[TRAIN_ORIGIN])
        training = cohorts[TRAIN_ORIGIN].filter(pl.col("arrived"))
        y_train = training["positive_tail"].cast(pl.Int64).to_numpy()
        baseline_rate = float(y_train.mean())
        scaler = StandardScaler().fit(_rate_design(training, priors))
        model = LogisticRegression(C=LOGISTIC_C, max_iter=2000).fit(
            scaler.transform(_rate_design(training, priors)), y_train
        )
        by_origin = {}
        scored = []
        for origin in EVALUATION_ORIGINS:
            frame = cohorts[origin].filter(pl.col("arrived")).with_columns(
                pl.lit(baseline_rate).alias("baseline_probability"),
                pl.Series(
                    "candidate_probability",
                    model.predict_proba(scaler.transform(_rate_design(cohorts[origin].filter(pl.col("arrived")), priors)))[:, 1],
                ),
            )
            scored.append(frame)
            by_origin[str(origin)] = _score(frame, seed=20262000 + origin)
        pooled_frame = pl.concat(scored)
        pooled = _cluster_bootstrap(pooled_frame, seed=20262010)
        subgroup_rows = _subgroups(pooled_frame)
        wins = sum(row["both_scores_improved"] for row in by_origin.values())
        intervals = all(pooled[metric]["ci_high"] < 0 for metric in ("brier", "log_loss"))
        reversals = [row for row in subgroup_rows if row["material_reversal"]]
        passed = wins == len(EVALUATION_ORIGINS) and intervals and not reversals
        overall &= passed
        if not passed:
            reasons.append(f"{player_type}: {wins}/2 origins improve both scores; pooled_interval_pass={intervals}; supported_reversals={len(reversals)}")
        results[player_type] = {
            "training": {"players": training.height, "positive_players": int(y_train.sum()), "baseline_rate": baseline_rate, "rate_priors": dict(zip(RATE_NAMES, priors, strict=True)), "regression_opportunities": REGRESSION_OPPORTUNITIES},
            "standardized_coefficients": [{"feature": name, "coefficient": float(value)} for name, value in zip(RATE_NAMES, model.coef_[0], strict=True)],
            "by_origin": by_origin, "pooled": pooled, "subgroups": subgroup_rows,
            "gate_passed": passed,
        }
    if overall:
        reasons = ["Both types passed the frozen old-era support gate; modern fresh confirmation and a complete path remain required."]
    report = {
        "status": "prospect_early_history_rate_only_tested",
        "as_of_date": args.as_of_date.isoformat(),
        "decision": "support_rate_only_old_era_but_do_not_promote" if overall else "reject_rate_only_family",
        "decision_reasons": reasons,
        "production_changed": False,
        "protocol": {"training_origin": TRAIN_ORIGIN, "unused_gap_origins": [2004, 2005], "evaluation_origins": list(EVALUATION_ORIGINS), "horizon_years": HORIZON, "threshold_component_war": THRESHOLD, "logistic_c": LOGISTIC_C, "regression_opportunities": REGRESSION_OPPORTUNITIES, "frozen_plan_sha256": sha256_file(PLAN_PATH)},
        "law_checks": {"training_outcomes_end_before_first_evaluation_snapshot": TRAIN_ORIGIN + HORIZON < min(EVALUATION_ORIGINS), "gap_origins_unused": True, "official_debut_coverage_complete": debut_dates["mlb_debut_date"].null_count() == 0, "rate_means_and_scaler_training_only": True, "no_evaluation_refit": True, "negative_component_war_retained": all(results[player_type]["by_origin"][str(origin)]["negative_war_players"] > 0 for player_type in ("hitter", "pitcher") for origin in EVALUATION_ORIGINS), "no_basic_or_demographic_features": True, "no_outside_fv": True, "production_unchanged": True},
        "results": results,
        "sources": [{"path": str(path), "sha256": sha256_file(path)} for path in sorted(set(sources), key=str)],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps({"decision": report["decision"], "reasons": reasons}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
