#!/usr/bin/env python3
"""Execute the frozen one-shot J0R comparison on disclosed V2022-V2024 targets."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from uuid import uuid4

import polars as pl

from universal_baseball.hitter_v2_evaluation import score_hitter_predictions
from universal_baseball.hitter_v2_validation import (
    build_evaluation_subgroups,
    build_player_scoring_surface,
    level_aggregate_calibration,
    paired_player_bootstrap_rmse_delta,
    predicted_woba_decile_calibration,
    score_subgroup,
    summarize_scoring_surface,
    terminal_component_calibration,
)
from universal_baseball.storage import sha256_file


FOLDS = ("V2022", "V2023", "V2024")
BASELINES = ("B0_ONE_YEAR_EB", "B1_MARCEL_345_K1200", "C0_NESTED_EB")
CANDIDATE = "J0R_FIXED_INFORMATION_SHRINKAGE"
MODELS = (*BASELINES, CANDIDATE)
GATE_METRICS = (
    "terminal_log_loss",
    "terminal_brier_score",
    "woba_rmse",
    "runs_per_600_rmse",
)
POOLED_RELATIVE = {
    "terminal_log_loss": 0.0025,
    "terminal_brier_score": 0.0025,
    "woba_rmse": 0.01,
    "runs_per_600_rmse": 0.01,
}
CORRELATIONS = (
    "woba_pearson",
    "woba_spearman",
    "runs_per_600_pearson",
    "runs_per_600_spearman",
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("docs/hitter-v2-stage2e-scoring-contract.json"),
    )
    parser.add_argument(
        "--fit-result",
        type=Path,
        default=Path("docs/hitter-v2-stage2e-fit-result.json"),
    )
    parser.add_argument(
        "--fit-report",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2e-j0r-fit/report.json"),
    )
    parser.add_argument(
        "--fit-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2e-j0r-fit/tables"),
    )
    parser.add_argument(
        "--baseline-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-final-validation/tables"),
    )
    parser.add_argument(
        "--target-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-prescore/tables"),
    )
    parser.add_argument(
        "--age-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-age/tables"),
    )
    parser.add_argument(
        "--event-input",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage2d-inputs/tables/"
            "hitter_v2_stage2d_j0_event_inputs_2021_2024.parquet"
        ),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2e-j0r-comparison"),
    )
    return parser.parse_args()


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def verify_scoring_boundary(contract: dict[str, object], *, runner: Path) -> None:
    if contract["status"] != "frozen_before_first_target_access":
        raise ValueError("Stage 2e scoring contract is not frozen")
    if sha256_file(runner) != contract["runner_sha256"]:
        raise ValueError("Stage 2e scoring runner changed after freeze")
    if contract["candidate_scoring_authorized"] is not True:
        raise ValueError("Stage 2e disclosed comparison is not authorized")
    for boundary in (
        "post_result_tuning_authorized",
        "protected_2026_access_authorized",
        "J1_authorized",
        "tracking_authorized",
        "stage3_authorized",
        "full_war_authorized",
    ):
        if contract[boundary] is not False:
            raise ValueError(f"Stage 2e scoring contract improperly opened {boundary}")


def _strongest(metrics: dict[str, dict[str, object]], metric: str) -> tuple[str, float]:
    model = min(BASELINES, key=lambda item: float(metrics[item][metric]))
    return model, float(metrics[model][metric])


def _primary_gate(metrics: dict[str, dict[str, object]]) -> dict[str, object]:
    rows = {}
    for metric in GATE_METRICS:
        baseline, value = _strongest(metrics, metric)
        candidate = float(metrics[CANDIDATE][metric])
        rows[metric] = {
            "candidate": candidate,
            "comparator": baseline,
            "comparator_value": value,
            "candidate_minus_comparator": candidate - value,
            "pass": candidate - value < -1e-8,
        }
    return {"metrics": rows, "pass": all(row["pass"] for row in rows.values())}


def _subgroup_gate(scores: dict[str, dict[str, object]]) -> dict[str, object]:
    deltas = {}
    for metric in GATE_METRICS:
        baseline = min(float(scores[model]["metrics"][metric]) for model in BASELINES)
        deltas[metric] = float(scores[CANDIDATE]["metrics"][metric]) - baseline
    rate_reversal = deltas["woba_rmse"] > 0.002 and deltas["runs_per_600_rmse"] > 0.5
    proper_reversal = (
        deltas["terminal_log_loss"] > 0.0005 and deltas["terminal_brier_score"] > 0.0005
    )
    return {
        "candidate_minus_metric_wise_comparator": deltas,
        "rate_reversal": rate_reversal,
        "proper_score_reversal": proper_reversal,
        "pass": not rate_reversal and not proper_reversal,
    }


def _dominant_label(events: pl.DataFrame, column: str, output: str) -> pl.DataFrame:
    return (
        events.group_by("player_id", column)
        .len(name="events")
        .sort(["player_id", "events", column], descending=[False, True, False])
        .unique("player_id", keep="first", maintain_order=True)
        .select("player_id", pl.col(column).cast(pl.String).alias(output))
    )


def _context_subgroups(events: pl.DataFrame) -> pl.DataFrame:
    ready = (
        events.group_by("player_id")
        .agg(
            pl.col("context_label_ready").mean().alias("ready_fraction"),
            pl.col("K_prior_pitcher_denominator").median().alias("median_pitcher_pa"),
        )
        .with_columns(
            pl.when(pl.col("ready_fraction") >= 0.5)
            .then(pl.lit("context_ready"))
            .otherwise(pl.lit("context_fallback"))
            .alias("context_readiness"),
            pl.when(pl.col("median_pitcher_pa") <= 0)
            .then(pl.lit("0"))
            .when(pl.col("median_pitcher_pa") < 50)
            .then(pl.lit("1_49"))
            .when(pl.col("median_pitcher_pa") < 100)
            .then(pl.lit("50_99"))
            .when(pl.col("median_pitcher_pa") < 200)
            .then(pl.lit("100_199"))
            .otherwise(pl.lit("200_plus"))
            .alias("pitcher_evidence_band"),
        )
    )
    return (
        ready.join(
            _dominant_label(events, "platoon_cell", "dominant_platoon_cell"),
            on="player_id",
        )
        .join(
            _dominant_label(events, "source_system", "dominant_source_system"),
            on="player_id",
        )
        .select(
            "player_id",
            "context_readiness",
            "pitcher_evidence_band",
            "dominant_platoon_cell",
            "dominant_source_system",
        )
    )


def _subgroups(
    predictions: dict[str, pl.DataFrame],
    target: pl.DataFrame,
    standard: pl.DataFrame,
    context: pl.DataFrame,
) -> tuple[list[dict[str, object]], bool]:
    joined = standard.join(context, on="player_id", how="left", validate="1:1")
    definitions = {
        "level": ("primary_target_level_group", 100, 10_000),
        "age": ("age_band", 50, 5_000),
        "evidence": ("evidence_band", 50, 5_000),
        "movement": ("movement_band", 50, 5_000),
        "K": ("k_band", 50, 5_000),
        "power": ("hr_power_band", 50, 5_000),
        "context_readiness": ("context_readiness", 50, 5_000),
        "platoon": ("dominant_platoon_cell", 50, 5_000),
        "pitcher_evidence": ("pitcher_evidence_band", 50, 5_000),
        "source": ("dominant_source_system", 50, 5_000),
    }
    rows: list[dict[str, object]] = []
    all_pass = True
    for dimension, (column, minimum_players, minimum_pa) in definitions.items():
        for label in sorted(
            str(value) for value in joined[column].drop_nulls().unique()
        ):
            player_ids = joined.filter(pl.col(column) == label)["player_id"].to_list()
            model_scores = {
                model: score_subgroup(predictions[model], target, player_ids)
                for model in MODELS
            }
            players = int(model_scores[CANDIDATE]["players"])
            target_pa = int(model_scores[CANDIDATE]["target_pa"])
            supported = players >= minimum_players and target_pa >= minimum_pa
            gates = (
                {
                    weighting: _subgroup_gate(
                        {
                            model: {
                                "metrics": model_scores[model]["metrics"][weighting]
                            }
                            for model in MODELS
                        }
                    )
                    for weighting in ("player", "pa")
                }
                if supported
                else {}
            )
            if supported:
                all_pass = all_pass and all(gate["pass"] for gate in gates.values())
            rows.append(
                {
                    "dimension": dimension,
                    "label": label,
                    "players": players,
                    "target_pa": target_pa,
                    "supported": supported,
                    "model_scores": model_scores,
                    "gates": gates,
                }
            )
    return rows, all_pass


def _ablation(fold: dict[str, object], table_root: Path) -> dict[str, object]:
    effects = pl.read_parquet(table_root / "batter_effects.parquet")
    fixed = pl.read_parquet(table_root / "fixed_effects.parquet")
    results = {}
    for node, diagnostics in fold["node_diagnostics"].items():
        node_effects = effects.filter(pl.col("node") == node)
        node_fixed = fixed.filter(pl.col("node") == node)
        sd = diagnostics["derived_batter_sd"]
        contrasts = ["LOGIT"] if node != "HIT_COMPOSITION" else ["2B", "3B"]
        penalties = {"contextual": 0.0, "uncontextual": 0.0}
        for phase, value_column in (
            ("contextual", "contextual_value"),
            ("uncontextual", "uncontextual_value"),
        ):
            penalties[phase] += float(
                node_fixed.filter(
                    pl.col("effect_type").str.starts_with("league_season_level")
                )
                .select((pl.col(value_column) ** 2).sum())
                .item()
            ) / (2 * 0.35**2)
            for index, contrast in enumerate(contrasts):
                scale = float(sd if node != "HIT_COMPOSITION" else sd[index])
                penalties[phase] += float(
                    node_effects.filter(pl.col("contrast") == contrast)
                    .select((pl.col(value_column) ** 2).sum())
                    .item()
                ) / (2 * scale**2)
            if phase == "contextual":
                penalties[phase] += float(
                    node_fixed.filter(pl.col("effect_type").str.starts_with("platoon"))
                    .select((pl.col(value_column) ** 2).sum())
                    .item()
                ) / (2 * 0.20**2)
                pitcher = node_fixed.filter(
                    pl.col("effect_type") == "pitcher_coefficient"
                )
                penalties[phase] += float(
                    pitcher.select(((pl.col(value_column) - 1.0) ** 2).sum()).item()
                ) / (2 * 0.25**2)
        count = int(diagnostics["event_count"])
        losses = {
            phase: (
                float(diagnostics[phase]["final_penalized_objective"])
                - penalties[phase]
            )
            / count
            for phase in ("contextual", "uncontextual")
        }
        results[node] = {
            "event_count": count,
            "contextual_log_loss": losses["contextual"],
            "uncontextual_log_loss": losses["uncontextual"],
            "contextual_minus_uncontextual": losses["contextual"]
            - losses["uncontextual"],
            "pass": losses["contextual"] - losses["uncontextual"] < -1e-8,
        }
    return {"nodes": results, "pass": all(row["pass"] for row in results.values())}


def main() -> int:
    args = _args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    verify_scoring_boundary(contract, runner=Path(__file__))
    if sha256_file(args.fit_result) != contract["fit_result_sha256"]:
        raise ValueError("Stage 2e frozen fit result changed")
    if sha256_file(args.fit_report) != contract["fit_report_sha256"]:
        raise ValueError("Stage 2e generated fit report changed")
    if sha256_file(args.event_input) != contract["event_input_sha256"]:
        raise ValueError("Stage 2e context subgroup input changed")
    fit_report = json.loads(args.fit_report.read_text(encoding="utf-8"))
    events = pl.read_parquet(args.event_input)
    fold_reports = []
    pooled: dict[str, list[pl.DataFrame]] = {model: [] for model in MODELS}
    for fold_id in FOLDS:
        slug = fold_id.lower()
        frozen = contract["folds"][fold_id]
        paths = {
            "B0_ONE_YEAR_EB": args.baseline_root
            / slug
            / "b0_one_year_eb_predictions.parquet",
            "B1_MARCEL_345_K1200": args.baseline_root
            / slug
            / "b1_marcel_345_k1200_predictions.parquet",
            "C0_NESTED_EB": args.baseline_root
            / slug
            / "c0_nested_eb_predictions.parquet",
            CANDIDATE: args.fit_root
            / slug
            / "j0r_fixed_information_shrinkage_predictions.parquet",
        }
        target_path = args.target_root / slug / "target_players.parquet"
        training_path = (
            args.target_root / slug / "training_player_league_seasons.parquet"
        )
        age_path = args.age_root / slug / "forecast_player_ages.parquet"
        for model, path in paths.items():
            if sha256_file(path) != frozen["prediction_sha256"][model]:
                raise ValueError(f"{fold_id} {model} prediction hash changed")
        for key, path in (
            ("target", target_path),
            ("training", training_path),
            ("age", age_path),
        ):
            if sha256_file(path) != frozen[f"{key}_sha256"]:
                raise ValueError(f"{fold_id} frozen {key} hash changed")
        predictions = {model: pl.read_parquet(path) for model, path in paths.items()}
        target = pl.read_parquet(target_path)
        training = pl.read_parquet(training_path)
        ages = pl.read_parquet(age_path)
        metrics = {
            model: {
                weighting: score_hitter_predictions(frame, target, weighting=weighting)
                for weighting in ("player", "pa")
            }
            for model, frame in predictions.items()
        }
        surfaces = {
            model: build_player_scoring_surface(
                frame, target, model_id=model, fold_id=fold_id
            )
            for model, frame in predictions.items()
        }
        for model, surface in surfaces.items():
            pooled[model].append(surface)
        primary = {
            weighting: _primary_gate(
                {model: metrics[model][weighting] for model in MODELS}
            )
            for weighting in ("player", "pa")
        }
        correlations = {}
        for weighting in ("player", "pa"):
            correlations[weighting] = {}
            for metric in CORRELATIONS:
                comparator = max(
                    float(metrics[model][weighting][metric]) for model in BASELINES
                )
                candidate = float(metrics[CANDIDATE][weighting][metric])
                correlations[weighting][metric] = {
                    "candidate": candidate,
                    "comparator": comparator,
                    "decline": comparator - candidate,
                    "pass": comparator - candidate <= 0.01,
                }
        component = {
            weighting: terminal_component_calibration(
                predictions[CANDIDATE], target, weighting=weighting
            )
            for weighting in ("player", "pa")
        }
        deciles = predicted_woba_decile_calibration(surfaces[CANDIDATE])
        levels = level_aggregate_calibration(predictions[CANDIDATE], target)
        calibration_pass = (
            all(
                abs(float(metrics[CANDIDATE][view]["woba_calibration_intercept"]))
                <= 0.005
                and 0.90
                <= float(metrics[CANDIDATE][view]["woba_calibration_slope"])
                <= 1.10
                for view in ("player", "pa")
            )
            and all(
                row["slope_guardrail_pass"] is not False
                for rows in component.values()
                for row in rows
            )
            and all(row["guardrail_pass"] for row in deciles)
            and all(row["guardrail_pass"] is not False for row in levels)
        )
        standard = build_evaluation_subgroups(training, target, ages)
        cutoff = int(training["season"].max())
        subgroup_rows, subgroup_pass = _subgroups(
            predictions,
            target,
            standard,
            _context_subgroups(events.filter(pl.col("season") <= cutoff)),
        )
        fit_fold = next(row for row in fit_report["folds"] if row["fold_id"] == fold_id)
        ablation = _ablation(fit_fold, args.fit_root / slug)
        fold_reports.append(
            {
                "fold_id": fold_id,
                "predictor_cutoff_season": cutoff,
                "target_season": cutoff + 1,
                "metrics": metrics,
                "primary_gate": primary,
                "primary_gate_pass": all(row["pass"] for row in primary.values()),
                "correlation_guardrails": correlations,
                "correlation_guardrails_pass": all(
                    row["pass"]
                    for view in correlations.values()
                    for row in view.values()
                ),
                "terminal_component_calibration": component,
                "predicted_woba_deciles": deciles,
                "level_aggregate_calibration": levels,
                "calibration_pass": calibration_pass,
                "subgroups": subgroup_rows,
                "subgroup_reversal_pass": subgroup_pass,
                "matched_context_ablation": ablation,
            }
        )
    pooled_surfaces = {
        model: pl.concat(frames, how="vertical_relaxed")
        for model, frames in pooled.items()
    }
    pooled_metrics = {
        model: {
            weighting: summarize_scoring_surface(surface, weighting=weighting)
            for weighting in ("player", "pa")
        }
        for model, surface in pooled_surfaces.items()
    }
    pooled_gates = {}
    for weighting in ("player", "pa"):
        pooled_gates[weighting] = {}
        for metric in GATE_METRICS:
            baseline, value = _strongest(
                {model: pooled_metrics[model][weighting] for model in MODELS}, metric
            )
            candidate = float(pooled_metrics[CANDIDATE][weighting][metric])
            improvement = (value - candidate) / value
            pooled_gates[weighting][metric] = {
                "candidate": candidate,
                "comparator": baseline,
                "comparator_value": value,
                "relative_improvement": improvement,
                "required": POOLED_RELATIVE[metric],
                "pass": improvement >= POOLED_RELATIVE[metric],
            }
    bootstrap = {}
    for error, metric in (
        ("woba_error", "woba_rmse"),
        ("runs_per_600_error", "runs_per_600_rmse"),
    ):
        comparator = min(
            BASELINES, key=lambda model: float(pooled_metrics[model]["player"][metric])
        )
        bootstrap[error] = {
            "comparator": comparator,
            **paired_player_bootstrap_rmse_delta(
                pooled_surfaces[CANDIDATE],
                pooled_surfaces[comparator],
                error_column=error,
                seed=20260824,
            ),
        }
    promotion = (
        all(fold["primary_gate_pass"] for fold in fold_reports)
        and all(row["pass"] for view in pooled_gates.values() for row in view.values())
        and all(fold["correlation_guardrails_pass"] for fold in fold_reports)
        and all(fold["calibration_pass"] for fold in fold_reports)
        and all(fold["subgroup_reversal_pass"] for fold in fold_reports)
        and all(fold["matched_context_ablation"]["pass"] for fold in fold_reports)
    )
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": "2e_J0R_disclosed_comparison",
        "status": "passed" if promotion else "failed",
        "candidate_scored": True,
        "promotion_pass": promotion,
        "post_result_tuning_authorized": False,
        "protected_2026_opened": False,
        "contract_sha256": sha256_file(args.contract),
        "fit_result_sha256": sha256_file(args.fit_result),
        "folds": fold_reports,
        "pooled_metrics": pooled_metrics,
        "pooled_relative_gates": pooled_gates,
        "paired_bootstrap": bootstrap,
        "next_gate": (
            "review_pass_before_any_confirmation_package"
            if promotion
            else "document_final_J0R_failure_and_stop_without_J1_or_WAR"
        ),
    }
    _atomic_json(args.report_root / "report.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
