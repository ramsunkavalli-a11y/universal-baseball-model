#!/usr/bin/env python3
"""Run the frozen broad-history regressed skill-rate tail test."""

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
    MODERN_ORIGINS,
    OLD_ORIGINS,
    RUNS_PER_WIN_SOURCE,
    THRESHOLD,
    TRAIN_ORIGINS,
    _cluster_bootstrap,
    _cohort,
    _design,
    _feature_names,
    _read_history,
    _score,
    _subgroups,
)
from universal_baseball.prospect_arrival_validation import proper_scores
from universal_baseball.storage import sha256_file


PLAN_PATH = Path("docs/prospect-broad-history-skill-tail-plan.md")
SOURCE_AUDIT_PATH = Path("docs/prospect-broad-history-skill-source-audit.md")
REGRESSION_OPPORTUNITIES = 200.0
RATE_NAMES = ("rate_1", "rate_2", "rate_3", "rate_4")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--generated-root", type=Path, default=Path("reports/generated"))
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/prospect-broad-history-skill-tail-result.json"),
    )
    parser.add_argument(
        "--output-md", type=Path,
        default=Path("docs/prospect-broad-history-skill-tail-result.md"),
    )
    return parser.parse_args()


def _rate_counts(skill: pl.DataFrame, *, player_type: str, origin: int) -> pl.DataFrame:
    current = skill.filter((pl.col("season") == origin) & (pl.col("sport_id") != 1))
    if player_type == "hitter":
        workload = "plate_appearances"
        expressions = (
            (pl.col("base_on_balls") - pl.col("intentional_walks")).sum().alias("event_1"),
            pl.col("strike_outs").sum().alias("event_2"),
            pl.col("home_runs").sum().alias("event_3"),
            (pl.col("doubles") + pl.col("triples") + pl.col("home_runs")).sum().alias("event_4"),
        )
    else:
        workload = "batters_faced"
        expressions = (
            pl.col("strike_outs").sum().alias("event_1"),
            (pl.col("base_on_balls") - pl.col("intentional_walks")).sum().alias("event_2"),
            pl.col("hit_batters").sum().alias("event_3"),
            pl.col("home_runs").sum().alias("event_4"),
        )
    return current.group_by("player_id").agg(
        pl.col(workload).sum().cast(pl.Float64).alias("rate_workload"), *expressions
    )


def _attach_counts(
    cohort: pl.DataFrame, skill: pl.DataFrame, *, player_type: str, origin: int
) -> pl.DataFrame:
    return cohort.join(
        _rate_counts(skill, player_type=player_type, origin=origin),
        on="player_id", how="left", validate="1:1",
    ).with_columns(
        pl.col("rate_workload").fill_null(0.0),
        *(pl.col(f"event_{index}").fill_null(0.0) for index in range(1, 5)),
    )


def _priors(training: pl.DataFrame) -> tuple[float, float, float, float]:
    workload = float(training["rate_workload"].sum())
    if workload <= 0:
        raise ValueError("training skill workload is empty")
    return tuple(float(training[f"event_{index}"].sum()) / workload for index in range(1, 5))


def _rich_design(
    frame: pl.DataFrame, *, player_type: str, priors: tuple[float, float, float, float]
) -> np.ndarray:
    basic = _design(frame, player_type=player_type)
    workload = frame["rate_workload"].to_numpy()
    rates = np.column_stack([
        (frame[f"event_{index}"].to_numpy() + REGRESSION_OPPORTUNITIES * prior)
        / (workload + REGRESSION_OPPORTUNITIES)
        for index, prior in enumerate(priors, start=1)
    ])
    return np.column_stack([basic, rates])


def _fit(
    training: pl.DataFrame, *, player_type: str
) -> tuple[float, tuple[float, ...], StandardScaler, LogisticRegression, StandardScaler, LogisticRegression]:
    counts = training.group_by("player_id").len().rename({"len": "player_rows"})
    training = training.join(counts, on="player_id", validate="m:1").with_columns(
        (1 / pl.col("player_rows")).alias("weight")
    )
    y = training["positive_tail"].cast(pl.Int64).to_numpy()
    weights = training["weight"].to_numpy()
    constant = float(np.average(y, weights=weights))
    priors = _priors(training)
    basic_scaler = StandardScaler().fit(_design(training, player_type=player_type), sample_weight=weights)
    basic = LogisticRegression(C=LOGISTIC_C, max_iter=2000).fit(
        basic_scaler.transform(_design(training, player_type=player_type)), y, sample_weight=weights
    )
    rich_scaler = StandardScaler().fit(_rich_design(training, player_type=player_type, priors=priors), sample_weight=weights)
    rich = LogisticRegression(C=LOGISTIC_C, max_iter=2000).fit(
        rich_scaler.transform(_rich_design(training, player_type=player_type, priors=priors)), y, sample_weight=weights
    )
    return constant, priors, basic_scaler, basic, rich_scaler, rich


def _markdown(report: dict[str, object]) -> str:
    lines = [
        "# Prospect broad-history skill-tail result", "",
        f"**Decision:** `{report['decision']}`", "",
        "The fixed candidate adds strongly regressed current-season component rates to the basic model. Negative differences favor the skill candidate.", "",
        "| Type | Era | Origins better | Brier difference (95% interval) | Log-loss difference (95% interval) | Candidate beats constant |", "|---|---|---:|---:|---:|---:|",
    ]
    for player_type in ("hitter", "pitcher"):
        result = report["results"][player_type]
        for era, origins in (("old", OLD_ORIGINS), ("modern", MODERN_ORIGINS)):
            pooled = result["pooled"][era]
            wins = sum(result["by_origin"][str(origin)]["both_scores_improved"] for origin in origins)
            brier = pooled["brier"]
            logloss = pooled["log_loss"]
            lines.append(f"| {player_type} | {era} | {wins} | {brier['difference']:.4f} ({brier['ci_low']:.4f}, {brier['ci_high']:.4f}) | {logloss['difference']:.4f} ({logloss['ci_low']:.4f}, {logloss['ci_high']:.4f}) | {result['candidate_beats_constant'][era]} |")
    lines += ["", "The production model was not changed.", "", "## Why", ""]
    lines.extend(f"- {reason}" for reason in report["decision_reasons"])
    return "\n".join(lines) + "\n"


def main() -> int:
    args = _args()
    root = args.generated_root
    stats, stat_paths = _read_history(root)
    old_snapshots = root / "opportunity-history-sources-pre2020/tables"
    modern_snapshots = root / "opportunity-history-sources-v2/tables"
    old_skill_root = root / "affiliated-skill-source-2008-2017"
    modern_skill_root = root / "phase2-arrival-skill-source"
    old_skill_paths = {
        "hitter": old_skill_root / "tables/affiliated_hitting_components.parquet",
        "pitcher": old_skill_root / "tables/affiliated_pitching_components.parquet",
    }
    modern_skill_paths = {
        "hitter": modern_skill_root / "tables/affiliated_hitting_components.parquet",
        "pitcher": modern_skill_root / "tables/affiliated_pitching_components.parquet",
    }
    component_paths = {
        "hitter": root / "career-mlb-outcome-inventory-2009-2025/tables/mlb_hitting_components_2009_2025.parquet",
        "pitcher": root / "career-mlb-outcome-inventory-2009-2025/tables/mlb_pitching_2009_2025.parquet",
    }
    runs_per_win = float(json.loads(RUNS_PER_WIN_SOURCE.read_text(encoding="utf-8"))["runs_per_win"])
    results = {}
    reasons = []
    overall = True
    sources = [PLAN_PATH, SOURCE_AUDIT_PATH, RUNS_PER_WIN_SOURCE, old_skill_root / "report.json", modern_skill_root / "report.json", *stat_paths]
    for player_type in ("hitter", "pitcher"):
        snapshot_paths = [old_snapshots / f"{player_type}_snapshots.parquet", modern_snapshots / f"{player_type}_snapshots.parquet"]
        snapshots = pl.concat([pl.read_parquet(path) for path in snapshot_paths], how="vertical_relaxed")
        old_skill = pl.read_parquet(old_skill_paths[player_type])
        modern_skill = pl.read_parquet(modern_skill_paths[player_type])
        components = pl.read_parquet(component_paths[player_type])
        sources.extend([*snapshot_paths, old_skill_paths[player_type], modern_skill_paths[player_type], component_paths[player_type]])
        cohorts = {}
        for origin in (*TRAIN_ORIGINS, *OLD_ORIGINS, *MODERN_ORIGINS):
            base = _cohort(snapshots, stats, components, player_type=player_type, origin=origin, runs_per_win=runs_per_win)
            skill = old_skill if origin <= 2017 else modern_skill
            cohorts[origin] = _attach_counts(base, skill, player_type=player_type, origin=origin)
        training = pl.concat([cohorts[origin].filter(pl.col("arrived")) for origin in TRAIN_ORIGINS])
        constant, priors, basic_scaler, basic, rich_scaler, rich = _fit(training, player_type=player_type)
        by_origin = {}
        scored = {}
        for origin in (*OLD_ORIGINS, *MODERN_ORIGINS):
            frame = cohorts[origin].filter(pl.col("arrived"))
            basic_probability = basic.predict_proba(basic_scaler.transform(_design(frame, player_type=player_type)))[:, 1]
            rich_probability = rich.predict_proba(rich_scaler.transform(_rich_design(frame, player_type=player_type, priors=priors)))[:, 1]
            frame = frame.with_columns(
                pl.lit(constant).alias("constant_probability"),
                pl.Series("baseline_probability", basic_probability),
                pl.Series("candidate_probability", rich_probability),
            )
            scored[origin] = frame
            by_origin[str(origin)] = _score(frame, seed=20261900 + origin)
        pooled = {}
        pooled_scores = {}
        subgroups = {}
        candidate_beats_constant = {}
        for era, origins in (("old", OLD_ORIGINS), ("modern", MODERN_ORIGINS)):
            frame = pl.concat([scored[origin] for origin in origins])
            pooled[era] = _cluster_bootstrap(frame, seed=20261900 + (0 if era == "old" else 1))
            subgroups[era] = _subgroups(frame)
            y = frame["positive_tail"].cast(pl.Float64).to_numpy()
            candidate_score = proper_scores(y, frame["candidate_probability"].to_numpy())
            basic_score = proper_scores(y, frame["baseline_probability"].to_numpy())
            constant_score = proper_scores(y, frame["constant_probability"].to_numpy())
            pooled_scores[era] = {
                "constant": constant_score,
                "basic": basic_score,
                "candidate": candidate_score,
            }
            candidate_beats_constant[era] = bool(candidate_score["brier"] < constant_score["brier"] and candidate_score["log_loss"] < constant_score["log_loss"])
        old_wins = sum(by_origin[str(origin)]["both_scores_improved"] for origin in OLD_ORIGINS)
        modern_wins = sum(by_origin[str(origin)]["both_scores_improved"] for origin in MODERN_ORIGINS)
        intervals = all(pooled[era][metric]["ci_high"] < 0 for era in ("old", "modern") for metric in ("brier", "log_loss"))
        reversals = [row for rows in subgroups.values() for row in rows if row["material_reversal"]]
        passed = old_wins >= 4 and modern_wins >= 2 and intervals and not reversals and all(candidate_beats_constant.values())
        overall &= passed
        if not passed:
            reasons.append(f"{player_type}: {old_wins}/5 old and {modern_wins}/3 modern origins beat basic; pooled_interval_pass={intervals}; supported_reversals={len(reversals)}; beats_constant={candidate_beats_constant}")
        rich_names = (*_feature_names(player_type), *RATE_NAMES)
        results[player_type] = {
            "training": {"rows": training.height, "players": training["player_id"].n_unique(), "rate_priors": dict(zip(RATE_NAMES, priors, strict=True)), "regression_opportunities": REGRESSION_OPPORTUNITIES},
            "standardized_coefficients": [{"feature": name, "coefficient": float(value)} for name, value in zip(rich_names, rich.coef_[0], strict=True)],
            "by_origin": by_origin, "pooled": pooled, "subgroups": subgroups,
            "pooled_scores": pooled_scores,
            "candidate_beats_constant": candidate_beats_constant, "gate_passed": passed,
        }
    if overall:
        reasons = ["Both types passed every frozen condition; the result remains research-only pending a complete path and fresh confirmation."]
    report = {
        "status": "prospect_broad_history_skill_tail_tested",
        "as_of_date": args.as_of_date.isoformat(),
        "decision": "support_skill_tail_but_do_not_promote" if overall else "reject_aggregate_skill_tail",
        "decision_reasons": reasons,
        "production_changed": False,
        "protocol": {"training_origins": list(TRAIN_ORIGINS), "old_evaluation_origins": list(OLD_ORIGINS), "modern_evaluation_origins": list(MODERN_ORIGINS), "horizon_years": HORIZON, "threshold_component_war": THRESHOLD, "logistic_c": LOGISTIC_C, "regression_opportunities": REGRESSION_OPPORTUNITIES, "frozen_plan_sha256": sha256_file(PLAN_PATH)},
        "law_checks": {"training_outcomes_end_before_first_evaluation_snapshot": max(TRAIN_ORIGINS) + HORIZON < min(OLD_ORIGINS), "rates_regressed_to_training_only": True, "no_evaluation_refit": True, "negative_component_war_retained": all(results[player_type]["by_origin"][str(origin)]["negative_war_players"] > 0 for player_type in ("hitter", "pitcher") for origin in (*OLD_ORIGINS, *MODERN_ORIGINS)), "no_outside_fv": True, "no_demographic_talent_effect": True, "no_organization_effect": True, "production_unchanged": True},
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
