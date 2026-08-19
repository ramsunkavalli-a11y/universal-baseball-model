#!/usr/bin/env python3
"""Run the one-shot repaired Defense v1 catcher throwing/blocking 2025 confirmation.

This scorer performs no fitting, reselection, recalibration, or live source query.
It uses the frozen repaired C2 coefficients and the exact preregistered C2 feature
construction from develop_defense_v1_universal.py. The frozen parameter package's
throwing `exposure` label is known metadata-only drift: the fitted C2 implementation
weights throwing seasons by steal_attempts, not fielding_outs.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import platform
from typing import Any

import numpy as np
import polars as pl

from confirm_defense_v1_2025 import _catcher_gate
from develop_defense_v1_universal import _load_profiles

EXPECTED_PARAMETER_HASH = "sha256:f4790bc1cb4df63d2ba65757455a4b6753e98d25fe552208d893958bdd19f328"
EXPECTED_HISTORICAL_RUN = 32148467330
EXPECTED_2025_SOURCE_RUN = 32207093006


def _sha_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + sha256(payload).hexdigest()


def _find_one(root: Path, name: str) -> Path:
    matches = list(root.rglob(name))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {name} under {root}; observed={matches}")
    return matches[0]


def _load_target(root: Path, source: dict[str, Any], kind: str) -> dict[int, float]:
    path = _find_one(root, f"catcher_{kind}_targets_2025.parquet")
    storage = source["storage"][f"targets_{kind}"]
    if _sha_file(path) != storage["sha256"]:
        raise RuntimeError(f"repaired 2025 {kind} target SHA mismatch")
    frame = pl.read_parquet(path)
    if frame.height != int(storage["row_count"]):
        raise RuntimeError(f"repaired 2025 {kind} target row-count mismatch")
    needed = {"target_year", "player_id", "target_z"}
    missing = sorted(needed - set(frame.columns))
    if missing:
        raise RuntimeError(f"repaired 2025 {kind} target missing {missing}")
    canonical = (
        frame.with_columns(
            pl.col("target_year").cast(pl.Int64, strict=False),
            pl.col("player_id").cast(pl.Int64, strict=False),
            pl.col("target_z").cast(pl.Float64, strict=False),
        )
        .filter(
            (pl.col("target_year") == 2025)
            & pl.col("player_id").is_not_null()
            & pl.col("target_z").is_not_null()
            & pl.col("target_z").is_finite()
        )
        .select("player_id", "target_z")
    )
    mapping = {
        int(row["player_id"]): float(row["target_z"])
        for row in canonical.iter_rows(named=True)
    }
    if len(mapping) != canonical.height or canonical.height != frame.height:
        raise RuntimeError(f"invalid repaired 2025 {kind} target keys/coverage")
    return mapping


def _score_component(
    catcher: pl.DataFrame,
    target_map: dict[int, float],
    params: dict[str, Any],
    kind: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if params.get("family") != "C2" or float(params.get("lambda", -1)) != 0.0:
        raise RuntimeError(f"unexpected frozen {kind} family")
    feature = str(params["feature"])
    expected_feature = "caught_stealing_pct" if kind == "throwing" else "passed_balls_per_9"
    if feature != expected_feature:
        raise RuntimeError(f"unexpected frozen {kind} feature: {feature}")
    prior_weight = float(params["prior_season_recency_weight"])
    if prior_weight != 0.5:
        raise RuntimeError(f"unexpected frozen {kind} prior weight: {prior_weight}")
    mean = float(params["normalization"]["mean"])
    sd = float(params["normalization"]["sd"])
    beta = [float(value) for value in params["coefficients"]]
    if len(beta) != 2 or not all(math.isfinite(value) for value in [mean, sd, *beta]) or sd <= 1e-12:
        raise RuntimeError(f"invalid frozen {kind} parameters")

    index = {
        (int(row["season"]), int(row["player_id"])): row
        for row in catcher.iter_rows(named=True)
    }
    current_rows = catcher.filter(
        (pl.col("season") == 2024)
        & (pl.col("fielding_outs") >= 300)
        & pl.col(feature).is_not_null()
    )
    if kind == "throwing":
        current_rows = current_rows.filter(pl.col("steal_attempts") >= 10)

    rows: list[dict[str, Any]] = []
    for row in current_rows.iter_rows(named=True):
        player_id = int(row["player_id"])
        target = target_map.get(player_id)
        if target is None:
            continue
        current_value = float(row[feature])
        current_z = (current_value - mean) / sd
        if not math.isfinite(current_z):
            raise RuntimeError(f"nonfinite current {kind} z player={player_id}")

        c2_feature = current_z
        prior_used = False
        prior = index.get((2023, player_id))
        if prior is not None and int(prior["fielding_outs"]) >= 300 and prior[feature] is not None:
            prior_eligible = kind != "throwing" or int(prior["steal_attempts"]) >= 10
            if prior_eligible:
                prior_z = (float(prior[feature]) - mean) / sd
                if kind == "throwing":
                    current_exposure = float(row["steal_attempts"])
                    prior_exposure = float(prior["steal_attempts"])
                else:
                    current_exposure = float(row["fielding_outs"])
                    prior_exposure = float(prior["fielding_outs"])
                denominator = current_exposure + prior_weight * prior_exposure
                if denominator <= 0 or not all(math.isfinite(v) for v in (prior_z, current_exposure, prior_exposure, denominator)):
                    raise RuntimeError(f"invalid {kind} C2 prior construction player={player_id}")
                c2_feature = (
                    current_exposure * current_z
                    + prior_weight * prior_exposure * prior_z
                ) / denominator
                prior_used = True

        pred = beta[0] + beta[1] * c2_feature
        if not all(math.isfinite(v) for v in (target, c2_feature, pred)):
            raise RuntimeError(f"nonfinite repaired {kind} confirmation value player={player_id}")
        rows.append(
            {
                "component": f"catcher_{kind}_C2",
                "player_id": player_id,
                "position": "C",
                "current_level_group": str(row["current_level_group"]),
                "fielding_outs_2024": int(row["fielding_outs"]),
                "steal_attempts_2024": int(row["steal_attempts"]),
                "feature_z": float(c2_feature),
                "target_z": float(target),
                "b0_prediction": 0.0,
                "candidate_prediction": float(pred),
                "prior_used": prior_used,
            }
        )

    if len({row["player_id"] for row in rows}) != len(rows):
        raise RuntimeError(f"duplicate player in repaired {kind} confirmation population")
    gate = _catcher_gate(rows, minimum_count=30, mae_tolerance=0.075, minimum_spearman=0.10)
    return gate, rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    params_report = json.loads(Path("docs/defense-v1-catcher-repair-parameters.json").read_text())
    source = json.loads(Path("docs/defense-v1-catcher-repair-2025-source-result.json").read_text())
    contract_text = Path("docs/defense-v1-catcher-source-repair-contract.md").read_text()

    if params_report.get("parameter_hash") != EXPECTED_PARAMETER_HASH:
        raise RuntimeError("repaired catcher parameter hash changed")
    if _canonical_hash(params_report["parameters"]) != EXPECTED_PARAMETER_HASH:
        raise RuntimeError("repaired catcher canonical parameter payload hash mismatch")
    if params_report.get("decision", {}).get("repaired_pre_2025_catcher_parameters_frozen") is not True:
        raise RuntimeError("repaired catcher parameters are not frozen")
    if params_report.get("boundary", {}).get("2025_catcher_target_accessed") is not False:
        raise RuntimeError("repaired parameter freeze crossed 2025 target boundary")

    required_contract = [
        "fewer than 30 scored catchers -> insufficient evidence",
        "candidate MSE must be below B0",
        "candidate MAE may be at most 7.5% worse than B0",
        "Spearman must be >=0.10",
        "No refit, reselection, recalibration, threshold movement, or rescue",
    ]
    missing_contract = [item for item in required_contract if item not in contract_text]
    if missing_contract:
        raise RuntimeError(f"repair confirmation contract changed/missing terms: {missing_contract}")

    if int(source.get("source_run_id", -1)) != EXPECTED_2025_SOURCE_RUN:
        raise RuntimeError(f"unexpected repaired 2025 source run: {source.get('source_run_id')}")
    if source.get("status") != "repaired_2025_catcher_source_certified_ready_for_confirmation":
        raise RuntimeError("repaired 2025 catcher source is not certified")
    if source.get("repaired_parameter_hash") != EXPECTED_PARAMETER_HASH:
        raise RuntimeError("2025 source was not materialized against frozen repaired parameter hash")
    if source.get("decision", {}).get("repaired_catcher_confirmation_authorized_next") is not True:
        raise RuntimeError("repaired catcher confirmation not authorized")
    boundary = source.get("boundary", {})
    for key in ("model_fit", "model_scoring", "confirmation_interpreted", "general_range_accessed", "general_range_modified", "war_calculated"):
        if boundary.get(key) is not False:
            raise RuntimeError(f"repaired 2025 source boundary violation {key}={boundary.get(key)}")

    _, meta = _load_profiles(args.historical_root)
    catcher = meta["catcher"]
    throwing_target = _load_target(args.target_root, source, "throwing")
    blocking_target = _load_target(args.target_root, source, "blocking")
    params = params_report["parameters"]

    throwing_gate, throwing_rows = _score_component(
        catcher, throwing_target, params["catcher_throwing"], "throwing"
    )
    blocking_gate, blocking_rows = _score_component(
        catcher, blocking_target, params["catcher_blocking"], "blocking"
    )

    throwing_pass = bool(throwing_gate["passed"])
    blocking_pass = bool(blocking_gate["passed"])
    root = args.output_root
    table_root = root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)
    scored = pl.DataFrame(throwing_rows + blocking_rows).sort(["component", "player_id"])
    scored_path = table_root / "scored_repaired_catcher_confirmation_rows.parquet"
    scored.write_parquet(scored_path, compression="zstd")

    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_repaired_catcher_2025_one_shot_confirmation",
        "status": "confirmation_complete",
        "contract": "docs/defense-v1-catcher-source-repair-contract.md",
        "parameter_hash": EXPECTED_PARAMETER_HASH,
        "source": {
            "historical_run_id": EXPECTED_HISTORICAL_RUN,
            "parameter_freeze_run_id": params_report.get("freeze_run_id"),
            "parameter_freeze_sha": params_report.get("freeze_sha"),
            "target_source_run_id": source.get("source_run_id"),
            "target_source_sha": source.get("source_sha"),
        },
        "implementation_audit": {
            "throwing_parameter_exposure_label": params["catcher_throwing"].get("exposure"),
            "throwing_fitted_c2_exposure_actually_used": "steal_attempts",
            "blocking_fitted_c2_exposure_actually_used": "fielding_outs",
            "parameter_hash_modified_after_2025_access": False,
            "scoring_construction": "exact preregistered develop_defense_v1_universal._catcher_matrix C2 semantics",
        },
        "catcher_throwing_C2_vs_B0": throwing_gate,
        "catcher_blocking_C2_vs_B0": blocking_gate,
        "decision": {
            "repaired_throwing_c2_confirmed": throwing_pass,
            "repaired_blocking_c2_confirmed": blocking_pass,
            "final_catcher_throwing": "C2" if throwing_pass else "B0_neutral",
            "final_catcher_blocking": "C2" if blocking_pass else "B0_neutral",
            "repaired_catcher_confirmation_complete": True,
            "catcher_source_repair_complete": True,
            "additional_catcher_tuning_authorized": False,
            "catcher_run_conversion_authorized_after_defense_handoff_reconciled": True,
            "war_value_authorized": False,
        },
        "storage": {
            "scored_rows": {
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
            "rescue_attempted": False,
            "general_range_modified": False,
            "framing_modified": False,
            "playing_time_v1_modified": False,
            "position_role_v1_modified": False,
            "run_value_conversion_performed": False,
            "war_value_calculated": False,
        },
    }
    (root / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "throwing": throwing_gate,
        "blocking": blocking_gate,
        "final_throwing": report["decision"]["final_catcher_throwing"],
        "final_blocking": report["decision"]["final_catcher_blocking"],
    }, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
