#!/usr/bin/env python3
"""Score the frozen one-shot Defense v1 confirmation on certified 2025 targets.

This script performs no fitting, tuning, recalibration, or live source query.
Predictions are reconstructed only from docs/defense-v1-confirmation-parameters.json
and certified source artifacts created under the frozen confirmation contract.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import platform
from typing import Any, Mapping

import numpy as np
import polars as pl

from develop_defense_v1_universal import _load_profiles


EXPECTED_PARAMETER_HASH = "sha256:cba6b7ebe4b2598db2c4d9ef360b0784f23a94ad61385f87149b08c46e0390d5"
EXPECTED_CONTRACT_SHA256 = "5229fb29730f29ab5421978dfe580f5a426e9f6c7b4740d3ab7ffad54bb831aa"
EXPECTED_HISTORICAL_RUN = 32148467330
EXPECTED_HISTORICAL_ARTIFACT = "position-role-historical-source-2021-2024"
GENERAL_POSITIONS = {"1B", "2B", "3B", "SS", "LF", "CF", "RF"}
GENERAL_FEATURES = ("fielding_pct", "range_factor_per_9", "errors_per_9", "throwing_errors_per_9")


def _sha_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + sha256(payload).hexdigest()


def _find_one(root: Path, name: str) -> Path:
    matches = list(root.rglob(name))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {name} under {root}; observed={matches}")
    return matches[0]


def _tree_manifest(root: Path, pattern: str) -> dict[str, Any]:
    paths = sorted(root.rglob(pattern))
    if not paths:
        raise RuntimeError(f"no {pattern} files under {root}")
    rows = []
    total = 0
    for path in paths:
        size = path.stat().st_size
        total += size
        rows.append(
            {
                "path": str(path.relative_to(root)).replace("\\", "/"),
                "size_bytes": size,
                "sha256": _sha_file(path),
            }
        )
    return {
        "file_count": len(rows),
        "total_size_bytes": total,
        "manifest_sha256": _canonical_hash(rows),
    }


def _rankdata(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    i = 0
    while i < len(values):
        j = i + 1
        while j < len(values) and values[order[j]] == values[order[i]]:
            j += 1
        ranks[order[i:j]] = (i + 1 + j) / 2.0
        i = j
    return ranks


def _corr(x: np.ndarray, y: np.ndarray) -> float | None:
    if len(x) < 2 or np.std(x) <= 1e-12 or np.std(y) <= 1e-12:
        return None
    value = float(np.corrcoef(x, y)[0, 1])
    return value if math.isfinite(value) else None


def _metrics(y: np.ndarray, pred: np.ndarray) -> dict[str, Any]:
    if len(y) != len(pred):
        raise ValueError("target/prediction length mismatch")
    if not len(y):
        return {
            "player_count": 0,
            "mse": None,
            "mae": None,
            "pearson": None,
            "spearman": None,
            "calibration_intercept": None,
            "calibration_slope": None,
        }
    residual = y - pred
    pearson = _corr(pred, y)
    spearman = _corr(_rankdata(pred), _rankdata(y))
    if np.std(pred) > 1e-12:
        design = np.column_stack([np.ones(len(pred)), pred])
        beta, *_ = np.linalg.lstsq(design, y, rcond=None)
        cal_intercept, cal_slope = float(beta[0]), float(beta[1])
    else:
        cal_intercept = None
        cal_slope = None
    return {
        "player_count": int(len(y)),
        "mse": float(np.mean(residual**2)),
        "mae": float(np.mean(np.abs(residual))),
        "pearson": pearson,
        "spearman": spearman,
        "calibration_intercept": cal_intercept,
        "calibration_slope": cal_slope,
    }


def _candidate_metrics_finite(metrics: Mapping[str, Any]) -> bool:
    required = ("mse", "mae", "pearson", "spearman")
    if not all(metrics.get(key) is not None and math.isfinite(float(metrics[key])) for key in required):
        return False
    for key in ("calibration_intercept", "calibration_slope"):
        value = metrics.get(key)
        if value is not None and not math.isfinite(float(value)):
            return False
    return True


def _predict(beta: list[float], features: list[float]) -> float:
    if len(beta) != len(features) + 1:
        raise RuntimeError(f"coefficient width {len(beta)} incompatible with {len(features)} features")
    value = float(beta[0]) + sum(float(coef) * float(feature) for coef, feature in zip(beta[1:], features, strict=True))
    if not math.isfinite(value):
        raise RuntimeError("nonfinite frozen Defense prediction")
    return value


def _normalization_lookups(parameters: Mapping[str, Any]) -> tuple[dict[tuple[str, str, str], tuple[float, float]], dict[tuple[str, str], tuple[float, float]], dict[str, tuple[float, float]]]:
    norm = parameters["general"]["normalization"]
    cell: dict[tuple[str, str, str], tuple[float, float]] = {}
    position: dict[tuple[str, str], tuple[float, float]] = {}
    global_: dict[str, tuple[float, float]] = {}
    for row in norm["cell"]:
        cell[(str(row["feature"]), str(row["position"]), str(row["level_group"]))] = (float(row["mean"]), float(row["sd"]))
    for row in norm["position"]:
        position[(str(row["feature"]), str(row["position"]))] = (float(row["mean"]), float(row["sd"]))
    for row in norm["global"]:
        global_[str(row["feature"])] = (float(row["mean"]), float(row["sd"]))
    return cell, position, global_


def _general_z(
    row: Mapping[str, Any],
    feature: str,
    lookups: tuple[dict[tuple[str, str, str], tuple[float, float]], dict[tuple[str, str], tuple[float, float]], dict[str, tuple[float, float]]],
) -> float:
    cell, position, global_ = lookups
    pos = str(row["position"])
    level = str(row["current_level_group"])
    moment = cell.get((feature, pos, level)) or position.get((feature, pos)) or global_.get(feature)
    if moment is None:
        raise RuntimeError(f"missing frozen normalizer for feature={feature} position={pos} level={level}")
    mean, sd = moment
    if not math.isfinite(sd) or sd <= 1e-12:
        raise RuntimeError(f"degenerate frozen normalizer for feature={feature} position={pos} level={level}")
    value = (float(row[feature]) - mean) / sd
    if not math.isfinite(value):
        raise RuntimeError("nonfinite frozen general z-score")
    return value


def _assert_parameter_package(report: Mapping[str, Any], contract_path: Path) -> Mapping[str, Any]:
    if report.get("parameter_hash") != EXPECTED_PARAMETER_HASH:
        raise RuntimeError(f"parameter hash changed: {report.get('parameter_hash')}")
    actual_hash = _canonical_hash(report["parameters"])
    if actual_hash != EXPECTED_PARAMETER_HASH:
        raise RuntimeError(f"canonical parameter payload hash mismatch: {actual_hash}")
    actual_contract_sha = _sha_file(contract_path)
    if actual_contract_sha != EXPECTED_CONTRACT_SHA256 or report.get("contract_sha256") != EXPECTED_CONTRACT_SHA256:
        raise RuntimeError("frozen confirmation contract hash changed")
    decision = report.get("decision", {})
    if decision.get("pre_2025_parameters_frozen") is not True:
        raise RuntimeError("pre-2025 parameters are not frozen")
    if decision.get("additional_development_challenger_authorized") is not False:
        raise RuntimeError("development challenger boundary changed")
    if decision.get("war_value_authorized") is not False:
        raise RuntimeError("WAR/value boundary changed before Defense confirmation")
    return report["parameters"]


def _assert_source_results(tracking: Mapping[str, Any], targets: Mapping[str, Any]) -> None:
    if tracking.get("status") != "source_materialized":
        raise RuntimeError(f"2024 tracking source not certified: {tracking.get('status')}")
    if tracking.get("decision", {}).get("2024_mlb_tracking_confirmation_predictor_materialized") is not True:
        raise RuntimeError("2024 tracking predictor did not materialize")
    if tracking.get("boundary", {}).get("2025_source_accessed") is not False:
        raise RuntimeError("2024 tracking source crossed 2025 source boundary")
    if tracking.get("boundary", {}).get("model_fit") is not False:
        raise RuntimeError("2024 tracking source performed model fitting")

    if targets.get("status") != "certified_source_ready_for_confirmation_scoring":
        raise RuntimeError(f"2025 target source not certified: {targets.get('status')}")
    if targets.get("decision", {}).get("target_source_certified") is not True:
        raise RuntimeError("2025 target source did not certify")
    boundary = targets.get("boundary", {})
    if boundary.get("2025_target_source_materialized") is not True:
        raise RuntimeError("2025 target source materialization flag missing")
    if boundary.get("model_fit") is not False or boundary.get("model_scoring") is not False:
        raise RuntimeError("2025 target source was not source-only")
    if boundary.get("confirmation_interpreted") is not False:
        raise RuntimeError("2025 target source interpreted confirmation outcomes")
    if boundary.get("war_value_authorized") is not False:
        raise RuntimeError("WAR/value boundary changed in target source")


def _verify_source_files(
    historical_root: Path,
    tracking_root: Path,
    target_root: Path,
    parameter_report: Mapping[str, Any],
    tracking_result: Mapping[str, Any],
    target_result: Mapping[str, Any],
) -> tuple[Path, Path, Path, Path]:
    historical_manifest = _tree_manifest(historical_root, "fielding_offset_*.json")
    frozen_historical = parameter_report["source"]["historical"]
    if frozen_historical.get("run_id") != EXPECTED_HISTORICAL_RUN or frozen_historical.get("artifact_name") != EXPECTED_HISTORICAL_ARTIFACT:
        raise RuntimeError("historical source identity changed")
    for key in ("file_count", "total_size_bytes", "manifest_sha256"):
        if historical_manifest[key] != frozen_historical[key]:
            raise RuntimeError(f"historical source manifest mismatch for {key}: {historical_manifest[key]} != {frozen_historical[key]}")

    tracking_path = _find_one(tracking_root, "tracked_range_z_2024_mlb.parquet")
    expected_tracking_sha = tracking_result["storage"]["tracked_range_z"]["sha256"]
    if _sha_file(tracking_path) != expected_tracking_sha:
        raise RuntimeError("2024 tracked-range-z artifact hash mismatch")

    general_path = _find_one(target_root, "general_range_targets_2025.parquet")
    throwing_path = _find_one(target_root, "catcher_throwing_targets_2025.parquet")
    blocking_path = _find_one(target_root, "catcher_blocking_targets_2025.parquet")
    checks = (
        (general_path, target_result["storage"]["general_targets"]["sha256"]),
        (throwing_path, target_result["storage"]["throwing_targets"]["sha256"]),
        (blocking_path, target_result["storage"]["blocking_targets"]["sha256"]),
    )
    for path, expected_sha in checks:
        if _sha_file(path) != expected_sha:
            raise RuntimeError(f"2025 target artifact hash mismatch: {path.name}")
    return tracking_path, general_path, throwing_path, blocking_path


def _eligible_general_2024(primary: pl.DataFrame) -> pl.DataFrame:
    return primary.filter(
        (pl.col("season") == 2024)
        & pl.col("position").is_in(sorted(GENERAL_POSITIONS))
        & (pl.col("fielding_outs") >= 300)
        & (pl.col("chances") >= 100)
        & pl.all_horizontal([pl.col(feature).is_not_null() for feature in GENERAL_FEATURES])
        & pl.col("current_level_group").is_not_null()
    )


def _score_general(
    primary: pl.DataFrame,
    targets: pl.DataFrame,
    tracking: pl.DataFrame,
    parameters: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    lookups = _normalization_lookups(parameters)
    beta_u1 = [float(v) for v in parameters["general"]["universal"]["coefficients"]]
    beta_t1 = [float(v) for v in parameters["general"]["tracked_mlb"]["coefficients"]]
    if not all(math.isfinite(v) for v in [*beta_u1, *beta_t1]):
        raise RuntimeError("nonfinite frozen general coefficient")

    target_map = {
        (int(row["player_id"]), str(row["position"])): float(row["range_target_z"])
        for row in targets.iter_rows(named=True)
    }
    tracking_map = {
        (int(row["player_id"]), str(row["position_abbreviation"])): float(row["tracked_range_z"])
        for row in tracking.iter_rows(named=True)
    }
    if len(target_map) != targets.height:
        raise RuntimeError("2025 general target keys are not unique")
    if len(tracking_map) != tracking.height:
        raise RuntimeError("2024 tracking keys are not unique")

    rows: list[dict[str, Any]] = []
    for row in _eligible_general_2024(primary).iter_rows(named=True):
        player_id = int(row["player_id"])
        position = str(row["position"])
        target = target_map.get((player_id, position))
        if target is None:
            continue
        features = [_general_z(row, feature, lookups) for feature in GENERAL_FEATURES]
        u1_pred = _predict(beta_u1, features)
        tracked_z = tracking_map.get((player_id, position)) if str(row["current_level_group"]) == "MLB" else None
        rows.append(
            {
                "component": "general_range",
                "player_id": player_id,
                "position": position,
                "current_level_group": str(row["current_level_group"]),
                "target_z": target,
                "b0_prediction": 0.0,
                "u1_prediction": u1_pred,
                "tracked_range_z": tracked_z,
                "t1_prediction": None if tracked_z is None else _predict(beta_t1, [*features, float(tracked_z)]),
            }
        )

    if not rows:
        raise RuntimeError("empty frozen U1 2025 confirmation population")
    y = np.asarray([row["target_z"] for row in rows], dtype=float)
    u1_pred = np.asarray([row["u1_prediction"] for row in rows], dtype=float)
    b0_pred = np.zeros(len(rows), dtype=float)
    u1_metrics = _metrics(y, u1_pred)
    b0_metrics = _metrics(y, b0_pred)
    u1_finite = bool(np.isfinite(y).all() and np.isfinite(u1_pred).all() and _candidate_metrics_finite(u1_metrics))
    u1_passed = bool(
        u1_finite
        and float(u1_metrics["mse"]) < float(b0_metrics["mse"])
        and float(u1_metrics["mae"]) <= 1.05 * float(b0_metrics["mae"])
        and float(u1_metrics["spearman"]) >= 0.10
    )

    tracked_rows = [row for row in rows if row["tracked_range_z"] is not None and row["t1_prediction"] is not None]
    if not u1_passed:
        t1 = {
            "status": "not_attempted_u1_failed",
            "player_count": len(tracked_rows),
            "passed": False,
        }
    elif len(tracked_rows) < 75:
        t1 = {
            "status": "insufficient_confirmation_evidence",
            "player_count": len(tracked_rows),
            "minimum_player_count": 75,
            "passed": False,
        }
    else:
        tracked_y = np.asarray([row["target_z"] for row in tracked_rows], dtype=float)
        tracked_u1 = np.asarray([row["u1_prediction"] for row in tracked_rows], dtype=float)
        tracked_t1 = np.asarray([row["t1_prediction"] for row in tracked_rows], dtype=float)
        u1_tracked_metrics = _metrics(tracked_y, tracked_u1)
        t1_metrics = _metrics(tracked_y, tracked_t1)
        t1_finite = bool(
            np.isfinite(tracked_y).all()
            and np.isfinite(tracked_u1).all()
            and np.isfinite(tracked_t1).all()
            and _candidate_metrics_finite(u1_tracked_metrics)
            and _candidate_metrics_finite(t1_metrics)
        )
        t1_passed = bool(
            t1_finite
            and float(t1_metrics["mse"]) < float(u1_tracked_metrics["mse"])
            and float(t1_metrics["mae"]) <= 1.05 * float(u1_tracked_metrics["mae"])
            and float(t1_metrics["spearman"]) >= float(u1_tracked_metrics["spearman"]) - 0.005
        )
        t1 = {
            "status": "confirmed" if t1_passed else "failed",
            "player_count": len(tracked_rows),
            "u1": u1_tracked_metrics,
            "t1": t1_metrics,
            "finite": t1_finite,
            "passed": t1_passed,
        }

    return {
        "u1_vs_b0": {
            "status": "confirmed" if u1_passed else "failed",
            "player_count": len(rows),
            "b0": b0_metrics,
            "u1": u1_metrics,
            "finite": u1_finite,
            "coverage_identical": True,
            "passed": u1_passed,
        },
        "t1_vs_u1": t1,
    }, rows


def _catcher_target_map(frame: pl.DataFrame, target_column: str) -> dict[int, float]:
    mapping = {int(row["player_id"]): float(row[target_column]) for row in frame.iter_rows(named=True)}
    if len(mapping) != frame.height:
        raise RuntimeError(f"duplicate catcher target player IDs in {target_column}")
    return mapping


def _score_catcher(
    catcher: pl.DataFrame,
    throwing_targets: pl.DataFrame,
    blocking_targets: pl.DataFrame,
    parameters: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    catcher_index = {
        (int(row["season"]), int(row["player_id"])): row
        for row in catcher.iter_rows(named=True)
    }
    throwing_map = _catcher_target_map(throwing_targets, "throwing_target_z")
    blocking_map = _catcher_target_map(blocking_targets, "blocking_target_z")
    scored_rows: list[dict[str, Any]] = []
    result: dict[str, Any] = {}

    throw_params = parameters["catcher_throwing"]
    throw_mean = float(throw_params["normalization"]["mean"])
    throw_sd = float(throw_params["normalization"]["sd"])
    throw_beta = [float(v) for v in throw_params["coefficients"]]
    throwing_rows = []
    for row in catcher.filter(
        (pl.col("season") == 2024)
        & (pl.col("fielding_outs") >= 300)
        & (pl.col("steal_attempts") >= 10)
        & pl.col("caught_stealing_pct").is_not_null()
    ).iter_rows(named=True):
        player_id = int(row["player_id"])
        target = throwing_map.get(player_id)
        if target is None:
            continue
        z = (float(row["caught_stealing_pct"]) - throw_mean) / throw_sd
        pred = _predict(throw_beta, [z])
        item = {
            "component": "catcher_throwing",
            "player_id": player_id,
            "position": "C",
            "current_level_group": str(row["current_level_group"]),
            "target_z": target,
            "b0_prediction": 0.0,
            "candidate_prediction": pred,
            "feature_z": z,
            "prior_used": False,
        }
        throwing_rows.append(item)
        scored_rows.append(item)

    result["catcher_throwing_C1_vs_B0"] = _catcher_gate(throwing_rows, minimum_count=30, mae_tolerance=0.075, minimum_spearman=0.10)

    block_params = parameters["catcher_blocking"]
    block_mean = float(block_params["normalization"]["mean"])
    block_sd = float(block_params["normalization"]["sd"])
    block_beta = [float(v) for v in block_params["coefficients"]]
    prior_weight = float(block_params["prior_season_recency_weight"])
    blocking_rows = []
    for row in catcher.filter(
        (pl.col("season") == 2024)
        & (pl.col("fielding_outs") >= 300)
        & pl.col("passed_balls_per_9").is_not_null()
    ).iter_rows(named=True):
        player_id = int(row["player_id"])
        target = blocking_map.get(player_id)
        if target is None:
            continue
        current_z = (float(row["passed_balls_per_9"]) - block_mean) / block_sd
        feature = current_z
        prior_used = False
        prior = catcher_index.get((2023, player_id))
        if prior is not None and int(prior["fielding_outs"]) >= 300 and prior["passed_balls_per_9"] is not None:
            prior_z = (float(prior["passed_balls_per_9"]) - block_mean) / block_sd
            current_exposure = float(row["fielding_outs"])
            prior_exposure = float(prior["fielding_outs"])
            feature = (current_exposure * current_z + prior_weight * prior_exposure * prior_z) / (
                current_exposure + prior_weight * prior_exposure
            )
            prior_used = True
        pred = _predict(block_beta, [feature])
        item = {
            "component": "catcher_blocking",
            "player_id": player_id,
            "position": "C",
            "current_level_group": str(row["current_level_group"]),
            "target_z": target,
            "b0_prediction": 0.0,
            "candidate_prediction": pred,
            "feature_z": feature,
            "prior_used": prior_used,
        }
        blocking_rows.append(item)
        scored_rows.append(item)

    result["catcher_blocking_C2_vs_B0"] = _catcher_gate(blocking_rows, minimum_count=30, mae_tolerance=0.075, minimum_spearman=0.10)
    return result, scored_rows


def _catcher_gate(rows: list[dict[str, Any]], *, minimum_count: int, mae_tolerance: float, minimum_spearman: float) -> dict[str, Any]:
    if len(rows) < minimum_count:
        return {
            "status": "insufficient_confirmation_evidence",
            "player_count": len(rows),
            "minimum_player_count": minimum_count,
            "passed": False,
        }
    y = np.asarray([row["target_z"] for row in rows], dtype=float)
    pred = np.asarray([row["candidate_prediction"] for row in rows], dtype=float)
    b0 = np.zeros(len(rows), dtype=float)
    candidate_metrics = _metrics(y, pred)
    b0_metrics = _metrics(y, b0)
    finite = bool(np.isfinite(y).all() and np.isfinite(pred).all() and _candidate_metrics_finite(candidate_metrics))
    passed = bool(
        finite
        and float(candidate_metrics["mse"]) < float(b0_metrics["mse"])
        and float(candidate_metrics["mae"]) <= (1.0 + mae_tolerance) * float(b0_metrics["mae"])
        and float(candidate_metrics["spearman"]) >= minimum_spearman
    )
    return {
        "status": "confirmed" if passed else "failed",
        "player_count": len(rows),
        "b0": b0_metrics,
        "candidate": candidate_metrics,
        "finite": finite,
        "coverage_identical": True,
        "passed": passed,
    }


def _scored_table(general_rows: list[dict[str, Any]], catcher_rows: list[dict[str, Any]]) -> pl.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in general_rows:
        rows.append(
            {
                "component": "general_range_U1",
                "player_id": row["player_id"],
                "position": row["position"],
                "current_level_group": row["current_level_group"],
                "target_z": row["target_z"],
                "baseline_prediction": row["b0_prediction"],
                "candidate_prediction": row["u1_prediction"],
                "tracked_range_z": None,
                "prior_used": False,
            }
        )
        if row["t1_prediction"] is not None:
            rows.append(
                {
                    "component": "general_range_T1_MLB",
                    "player_id": row["player_id"],
                    "position": row["position"],
                    "current_level_group": row["current_level_group"],
                    "target_z": row["target_z"],
                    "baseline_prediction": row["u1_prediction"],
                    "candidate_prediction": row["t1_prediction"],
                    "tracked_range_z": row["tracked_range_z"],
                    "prior_used": False,
                }
            )
    for row in catcher_rows:
        rows.append(
            {
                "component": "catcher_throwing_C1" if row["component"] == "catcher_throwing" else "catcher_blocking_C2",
                "player_id": row["player_id"],
                "position": row["position"],
                "current_level_group": row["current_level_group"],
                "target_z": row["target_z"],
                "baseline_prediction": row["b0_prediction"],
                "candidate_prediction": row["candidate_prediction"],
                "tracked_range_z": None,
                "prior_used": bool(row["prior_used"]),
            }
        )
    return pl.DataFrame(rows).sort(["component", "player_id", "position"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--tracking-root", type=Path, required=True)
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument("--parameter-result", type=Path, required=True)
    parser.add_argument("--tracking-result", type=Path, required=True)
    parser.add_argument("--target-result", type=Path, required=True)
    parser.add_argument("--confirmation-contract", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("reports/generated/defense-v1-2025-confirmation"))
    args = parser.parse_args()

    parameter_report = json.loads(args.parameter_result.read_text())
    tracking_result = json.loads(args.tracking_result.read_text())
    target_result = json.loads(args.target_result.read_text())
    parameters = _assert_parameter_package(parameter_report, args.confirmation_contract)
    _assert_source_results(tracking_result, target_result)
    tracking_path, general_path, throwing_path, blocking_path = _verify_source_files(
        args.historical_root,
        args.tracking_root,
        args.target_root,
        parameter_report,
        tracking_result,
        target_result,
    )

    primary, profile_meta = _load_profiles(args.historical_root)
    catcher = profile_meta["catcher"]
    tracking = pl.read_parquet(tracking_path)
    general_targets = pl.read_parquet(general_path)
    throwing_targets = pl.read_parquet(throwing_path)
    blocking_targets = pl.read_parquet(blocking_path)

    general_result, general_rows = _score_general(primary, general_targets, tracking, parameters)
    catcher_result, catcher_rows = _score_catcher(catcher, throwing_targets, blocking_targets, parameters)

    u1_passed = bool(general_result["u1_vs_b0"]["passed"])
    t1_passed = bool(general_result["t1_vs_u1"]["passed"])
    throwing_passed = bool(catcher_result["catcher_throwing_C1_vs_B0"]["passed"])
    blocking_passed = bool(catcher_result["catcher_blocking_C2_vs_B0"]["passed"])

    if not u1_passed:
        general_final = "B0_neutral_position_relative"
    elif t1_passed:
        general_final = "T1_for_eligible_MLB_tracking__U1_elsewhere"
    else:
        general_final = "U1_for_all_eligible_general_range"

    scored = _scored_table(general_rows, catcher_rows)
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)
    scored_path = table_root / "scored_confirmation_rows.parquet"
    scored.write_parquet(scored_path, compression="zstd")

    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_2025_one_shot_confirmation",
        "contract": str(args.confirmation_contract).replace("\\", "/"),
        "contract_sha256": EXPECTED_CONTRACT_SHA256,
        "parameter_hash": EXPECTED_PARAMETER_HASH,
        "status": "confirmation_complete_defense_v1_frozen",
        "source": {
            "historical_run_id": EXPECTED_HISTORICAL_RUN,
            "tracking_source_run_id": tracking_result.get("source_run_id"),
            "tracking_source_sha": tracking_result.get("source_sha"),
            "target_source_run_id": target_result.get("source_run_id"),
            "target_source_sha": target_result.get("source_sha"),
        },
        "general_range": general_result,
        "catcher": catcher_result,
        "decision": {
            "u1_confirmed": u1_passed,
            "t1_mlb_confirmed": t1_passed,
            "catcher_throwing_c1_confirmed": throwing_passed,
            "catcher_blocking_c2_confirmed": blocking_passed,
            "final_general_range": general_final,
            "final_catcher_throwing": "C1" if throwing_passed else "B0_neutral",
            "final_catcher_blocking": "C2" if blocking_passed else "B0_neutral",
            "tracked_framing": "closed_not_retained",
            "tracked_milb_t1": "closed_not_retained",
            "defense_v1_final_confirmation_complete": True,
            "defense_v1_frozen": True,
            "additional_defense_v1_tuning_authorized": False,
            "run_value_conversion_authorized_next": True,
            "war_value_authorized": False,
        },
        "storage": {
            "scored_rows": {
                "table_name": "defense_v1_2025_confirmation_scored_rows",
                "path": str(scored_path).replace("\\", "/"),
                "row_count": int(scored.height),
                "file_size_bytes": scored_path.stat().st_size,
                "sha256": _sha_file(scored_path),
            }
        },
        "package_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "polars": pl.__version__,
        },
        "boundary": {
            "live_source_query_performed_by_scorer": False,
            "model_fit": False,
            "model_reselection": False,
            "recalibration": False,
            "threshold_movement": False,
            "age_reopened": False,
            "traditional_feature_search_reopened": False,
            "tracked_framing_reopened": False,
            "tracked_milb_t1_reopened": False,
            "playing_time_v1_modified": False,
            "position_role_v1_modified": False,
            "run_value_conversion_performed": False,
            "war_value_calculated": False,
        },
    }
    report_path = args.output_root / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
