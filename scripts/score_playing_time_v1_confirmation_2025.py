#!/usr/bin/env python3
"""Score the one-shot Playing Time / Role v1 2025 confirmation fold.

This script consumes only:
- the pre-2025 frozen predictor artifact,
- the isolated/persisted 2025 MLB-PA target artifact, and
- the pre-2025 frozen B0/candidate parameter artifact.

It reconstructs the frozen fits from persisted coefficients. It never calls a
fitting routine, changes a feature, changes a threshold, or tunes against 2025.
A failed candidate confirmation is a valid binding result and does not make the
workflow itself fail.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.playing_time_confirmation import (
    confirmation_decision,
    load_frozen_playing_time_fit,
    participation_calibration,
)
from universal_baseball.playing_time_model import (
    PT_FORM_B0,
    build_playing_time_design,
    playing_time_level_tier,
    score_playing_time_hurdle,
)
from universal_baseball.storage import write_canonical_parquet


REFIT_RESULT = Path("docs/playing-time-v1-confirmation-refit-result.json")
INPUT_RESULT = Path("docs/playing-time-v1-confirmation-inputs-result.json")
TARGET_RESULT = Path("docs/playing-time-v1-confirmation-target-result.json")
CONTRACT = "docs/playing-time-v1-confirmation-contract.md"
FOLD = "projection_2024_to_2025_confirmation"


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refit-root", type=Path, required=True)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/playing-time-v1-confirmation-2025"),
    )
    return parser.parse_args()


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_one(root: Path, filename: str) -> Path:
    matches = sorted(path for path in root.rglob(filename) if path.is_file())
    if len(matches) != 1:
        raise RuntimeError(f"expected one {filename} below {root}, found {len(matches)}: {matches}")
    return matches[0]


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_hash(path: Path, expected: str, label: str) -> None:
    observed = _sha256(path)
    if observed != expected:
        raise RuntimeError(f"{label} hash changed: expected={expected}, observed={observed}")


def _require_binding_state(
    refit: dict[str, Any], inputs: dict[str, Any], target: dict[str, Any]
) -> None:
    if refit.get("status") != "frozen_ready_for_2025_source_materialization":
        raise RuntimeError("pre-2025 refit is not frozen")
    if not refit.get("decision", {}).get("parameters_frozen_before_2025"):
        raise RuntimeError("parameter freeze is not binding")
    if refit.get("boundary", {}).get("2025_accessed"):
        raise RuntimeError("pre-2025 refit unexpectedly claims 2025 access")
    if inputs.get("status") != "ready_to_open_2025_confirmation_target":
        raise RuntimeError("confirmation predictor inputs are not frozen/ready")
    if inputs.get("2025_outcomes_accessed"):
        raise RuntimeError("pre-2025 predictor artifact unexpectedly claims 2025 access")
    if target.get("status") != "source_certified_target_materialized_unscored":
        raise RuntimeError("2025 target source is not certified and unscored")
    boundary = target.get("boundary", {})
    if not boundary.get("2025_outcomes_accessed") or not boundary.get("2025_target_materialized"):
        raise RuntimeError("2025 target was not materialized through the isolated source gate")
    if boundary.get("model_parameters_loaded") or boundary.get("model_predictions_computed"):
        raise RuntimeError("isolated 2025 target gate was contaminated by model access")
    if boundary.get("candidate_vs_baseline_scores_computed") or boundary.get("model_refit"):
        raise RuntimeError("isolated 2025 target gate already scored or refit")
    if int(inputs.get("predictor_player_count", -1)) != int(target.get("target_player_count", -2)):
        raise RuntimeError("binding predictor and target player counts differ")


def _require_package_versions(refit: dict[str, Any]) -> dict[str, str]:
    mapping = {
        "numpy": "numpy",
        "polars": "polars",
        "scikit_learn": "scikit-learn",
        "statsmodels": "statsmodels",
    }
    expected = refit.get("package_versions", {})
    observed: dict[str, str] = {}
    for key, distribution in mapping.items():
        observed[key] = importlib.metadata.version(distribution)
        if str(expected.get(key)) != observed[key]:
            raise RuntimeError(
                f"confirmation package version drift for {key}: "
                f"expected={expected.get(key)}, observed={observed[key]}"
            )
    return observed


def _strata(
    predictors: pl.DataFrame,
    baseline_scored: pl.DataFrame,
    candidate_scored: pl.DataFrame,
) -> pl.DataFrame:
    tier = predictors.select("player_id", "as_of_level_group").with_columns(
        pl.col("as_of_level_group")
        .map_elements(playing_time_level_tier, return_dtype=pl.String)
        .alias("as_of_level_tier")
    ).select("player_id", "as_of_level_tier")
    paired = (
        tier.join(
            baseline_scored.select(
                "player_id",
                "observed_any_mlb_pa",
                pl.col("full_negative_log_likelihood").alias("baseline0_full_nll"),
            ),
            on="player_id",
            how="inner",
        )
        .join(
            candidate_scored.select(
                "player_id",
                pl.col("full_negative_log_likelihood").alias("candidate_full_nll"),
            ),
            on="player_id",
            how="inner",
        )
    )
    return (
        paired.group_by("as_of_level_tier")
        .agg(
            pl.len().cast(pl.Int64).alias("snapshot_players"),
            pl.col("observed_any_mlb_pa").sum().cast(pl.Int64).alias("positive_players"),
            pl.col("baseline0_full_nll").mean().alias("baseline0_full_nll"),
            pl.col("candidate_full_nll").mean().alias("candidate_full_nll"),
        )
        .with_columns(
            (pl.col("candidate_full_nll") - pl.col("baseline0_full_nll")).alias(
                "candidate_minus_baseline0_full_nll"
            ),
            ((pl.col("snapshot_players") >= 100) & (pl.col("positive_players") >= 25)).alias(
                "meaningfully_supported"
            ),
        )
        .sort("as_of_level_tier")
    )


def main() -> int:
    args = _args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    refit = _json(REFIT_RESULT)
    inputs = _json(INPUT_RESULT)
    target_record = _json(TARGET_RESULT)
    _require_binding_state(refit, inputs, target_record)
    package_versions = _require_package_versions(refit)

    predictors_path = _find_one(args.input_root, "predictors.parquet")
    targets_path = _find_one(args.target_root, "next_year_mlb_pa_targets.parquet")
    b0_coef_path = _find_one(args.refit_root, "baseline0_coefficients.parquet")
    b0_std_path = _find_one(args.refit_root, "baseline0_standardization.parquet")
    candidate_coef_path = _find_one(args.refit_root, "candidate_coefficients.parquet")
    candidate_std_path = _find_one(args.refit_root, "candidate_standardization.parquet")

    _require_hash(predictors_path, inputs["predictor_storage"]["file_sha256"], "predictor table")
    _require_hash(targets_path, target_record["storage"]["file_sha256"], "2025 target table")
    _require_hash(b0_coef_path, refit["storage"]["baseline0_coefficients"]["file_sha256"], "B0 coefficients")
    _require_hash(b0_std_path, refit["storage"]["baseline0_standardization"]["file_sha256"], "B0 standardization")
    _require_hash(candidate_coef_path, refit["storage"]["candidate_coefficients"]["file_sha256"], "candidate coefficients")
    _require_hash(candidate_std_path, refit["storage"]["candidate_standardization"]["file_sha256"], "candidate standardization")

    predictors = pl.read_parquet(predictors_path)
    targets = pl.read_parquet(targets_path).select("player_id", "next_year_mlb_pa")
    if predictors.height != int(inputs["predictor_player_count"]):
        raise RuntimeError("predictor row count changed")
    if targets.height != int(target_record["target_player_count"]):
        raise RuntimeError("target row count changed")
    predictor_ids = set(int(v) for v in predictors.get_column("player_id").to_list())
    target_ids = set(int(v) for v in targets.get_column("player_id").to_list())
    if predictor_ids != target_ids:
        raise RuntimeError("2025 confirmation predictor/target coverage differs")

    b0_fit = load_frozen_playing_time_fit(
        pl.read_parquet(b0_coef_path),
        pl.read_parquet(b0_std_path),
        form=str(refit["baseline0_form"]),
        expected_nb_alpha=float(refit["baseline0_nb_alpha"]),
        participation_training_players=int(refit["baseline0_training"]["training_observation_count"]),
        positive_training_players=0,
    )
    candidate_fit = load_frozen_playing_time_fit(
        pl.read_parquet(candidate_coef_path),
        pl.read_parquet(candidate_std_path),
        form=str(refit["selected_form"]),
        expected_nb_alpha=float(refit["candidate_nb_alpha"]),
        participation_training_players=int(refit["candidate_training"]["training_observation_count"]),
        positive_training_players=0,
    )

    b0_design = build_playing_time_design(predictors, form=PT_FORM_B0)
    candidate_design = build_playing_time_design(predictors, form=str(refit["selected_form"]))
    b0_scored, b0_metrics = score_playing_time_hurdle(b0_fit, b0_design, targets)
    candidate_scored, candidate_metrics = score_playing_time_hurdle(
        candidate_fit, candidate_design, targets
    )
    coverage_identical = (
        b0_scored.height == candidate_scored.height == predictors.height
        and b0_scored.get_column("player_id").to_list()
        == candidate_scored.get_column("player_id").to_list()
    )
    b0_calibration = participation_calibration(b0_scored)
    candidate_calibration = participation_calibration(candidate_scored)
    decision = confirmation_decision(
        b0_metrics,
        candidate_metrics,
        baseline_calibration=b0_calibration,
        candidate_calibration=candidate_calibration,
        coverage_identical=coverage_identical,
    )
    strata = _strata(predictors, b0_scored, candidate_scored)

    storage = {
        "baseline0_scores": write_canonical_parquet(
            b0_scored,
            table_root / "baseline0_scores.parquet",
            table_name="playing_time_v1_2025_confirmation_baseline0_scores",
        ).as_record(),
        "candidate_scores": write_canonical_parquet(
            candidate_scored,
            table_root / "candidate_scores.parquet",
            table_name="playing_time_v1_2025_confirmation_candidate_scores",
        ).as_record(),
        "diagnostic_strata": write_canonical_parquet(
            strata,
            table_root / "diagnostic_level_strata.parquet",
            table_name="playing_time_v1_2025_confirmation_level_strata",
        ).as_record(),
    }

    delta_full_nll = float(candidate_metrics["mean_full_negative_log_likelihood"]) - float(
        b0_metrics["mean_full_negative_log_likelihood"]
    )
    report = {
        "report_schema_version": "0.1",
        "gate": "playing_time_v1_2025_confirmation_one_shot",
        "status": "confirmed_candidate" if decision["confirmed"] else "candidate_failed_confirmation_baseline0_retained",
        "confirmation_contract": CONTRACT,
        "fold": FOLD,
        "source_records": {
            "pre_2025_refit_run": int(refit["source_run_id"]),
            "pre_2025_inputs_run": int(inputs["source_run_id"]),
            "isolated_2025_target_run": int(target_record["source_run_id"]),
        },
        "forms": {
            "baseline0": str(refit["baseline0_form"]),
            "candidate": str(refit["selected_form"]),
        },
        "package_versions": package_versions,
        "scored_player_count": int(predictors.height),
        "positive_2025_player_count": int(targets.filter(pl.col("next_year_mlb_pa") > 0).height),
        "baseline0_metrics": b0_metrics,
        "candidate_metrics": candidate_metrics,
        "candidate_minus_baseline0_full_nll": delta_full_nll,
        "baseline0_participation_calibration": b0_calibration,
        "candidate_participation_calibration": candidate_calibration,
        "decision": decision,
        "storage": storage,
        "boundary": {
            "2025_outcomes_accessed": True,
            "2025_target_source_changed": False,
            "frozen_pre_2025_parameters_loaded": True,
            "model_refit": False,
            "form_reselected": False,
            "threshold_changed": False,
            "rescue_tuning": False,
            "batting_rate_modified": False,
            "level_strata_used_for_selection": False,
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Playing Time v1 — 2025 one-shot confirmation",
        "",
        f"- Candidate confirmed: {decision['confirmed']}",
        f"- Production model: {decision['production_model_decision']}",
        f"- Scored players: {predictors.height:,}",
        f"- 2025 MLB-PA-positive players: {report['positive_2025_player_count']:,}",
        f"- B0 full NLL: {float(b0_metrics['mean_full_negative_log_likelihood']):.6f}",
        f"- Candidate full NLL: {float(candidate_metrics['mean_full_negative_log_likelihood']):.6f}",
        f"- Candidate minus B0 full NLL: {delta_full_nll:+.6f}",
        f"- B0 PA MAE: {float(b0_metrics['unconditional_mlb_pa_mae']):.3f}",
        f"- Candidate PA MAE: {float(candidate_metrics['unconditional_mlb_pa_mae']):.3f}",
        "- Model refit after 2025 access: False",
        "",
        "## Binding gates",
    ]
    lines.extend(f"- {name}: {passed}" for name, passed in decision["gates"].items())
    (args.output_root / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
