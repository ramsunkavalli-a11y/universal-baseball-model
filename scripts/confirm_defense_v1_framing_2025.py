#!/usr/bin/env python3
"""Run the frozen one-shot 2025 confirmation for repaired MLB catcher framing."""
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

EXPECTED_PARAMETER_HASH = "sha256:e75ebd58d868b6cb6d51f2d0e48d49c1735a4cfa80661b6280269311a7875086"
EXPECTED_HISTORICAL_RUN = 32148467330


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--predictor-root", type=Path, required=True)
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    params_report = json.loads(Path("docs/defense-v1-framing-repair-parameters.json").read_text())
    predictor_result = json.loads(Path("docs/defense-v1-2024-framing-predictor-source-result.json").read_text())
    target_result = json.loads(Path("docs/defense-v1-framing-2025-target-source-result.json").read_text())

    if params_report.get("parameter_hash") != EXPECTED_PARAMETER_HASH:
        raise RuntimeError(f"framing parameter hash changed: {params_report.get('parameter_hash')}")
    if _canonical_hash(params_report["parameters"]) != EXPECTED_PARAMETER_HASH:
        raise RuntimeError("framing canonical parameter payload hash mismatch")
    if params_report.get("decision", {}).get("repaired_pre_2025_framing_parameters_frozen") is not True:
        raise RuntimeError("repaired framing parameters are not frozen")
    if params_report.get("boundary", {}).get("2025_framing_target_accessed") is not False:
        raise RuntimeError("parameter freeze crossed 2025 target boundary")
    params = params_report["parameters"]
    if params.get("family") != "F1" or params.get("scope") != "MLB_only":
        raise RuntimeError("frozen framing family/scope changed")
    beta = [float(value) for value in params["coefficients"]]
    if len(beta) != 2 or not all(math.isfinite(value) for value in beta):
        raise RuntimeError("invalid frozen framing coefficients")

    if predictor_result.get("status") != "source_materialized":
        raise RuntimeError("2024 framing predictor source is not certified")
    pd = predictor_result.get("decision", {})
    pb = predictor_result.get("boundary", {})
    if pd.get("2024_mlb_framing_confirmation_predictor_materialized") is not True:
        raise RuntimeError("2024 framing predictor did not materialize")
    if pd.get("2025_framing_target_materialization_authorized_next") is not True:
        raise RuntimeError("2024 predictor did not authorize 2025 target step")
    if pb.get("2025_source_accessed") is not False or pb.get("2025_framing_target_accessed") is not False:
        raise RuntimeError("2024 framing predictor source crossed 2025 boundary")
    if pb.get("model_fit") is not False or pb.get("model_scoring_performed") is not False:
        raise RuntimeError("2024 framing predictor source was not source-only")

    if target_result.get("status") != "source_materialized":
        raise RuntimeError("2025 framing target source is not certified")
    td = target_result.get("decision", {})
    tb = target_result.get("boundary", {})
    if td.get("2025_framing_target_source_materialized") is not True:
        raise RuntimeError("2025 framing target source did not materialize")
    if td.get("2025_framing_confirmation_scoring_authorized_next") is not True:
        raise RuntimeError("2025 framing target source did not authorize scoring")
    if tb.get("model_fit") is not False or tb.get("model_scoring_performed") is not False:
        raise RuntimeError("2025 framing target source was not source-only")
    if tb.get("confirmation_interpreted") is not False:
        raise RuntimeError("2025 framing target source interpreted confirmation")

    predictor_path = _find_one(args.predictor_root, "tracked_framing_z_2024_mlb.parquet")
    predictor_expected = predictor_result["storage"]["tracked_framing_z"]["sha256"]
    if _sha_file(predictor_path) != predictor_expected:
        raise RuntimeError("2024 framing predictor artifact SHA mismatch")
    target_path = _find_one(args.target_root, "catcher_framing_targets_2025.parquet")
    target_expected = target_result["storage"]["target"]["sha256"]
    if _sha_file(target_path) != target_expected:
        raise RuntimeError("2025 framing target artifact SHA mismatch")

    predictor = pl.read_parquet(predictor_path)
    target = pl.read_parquet(target_path)
    predictor_map = {
        int(row["player_id"]): float(row["tracked_framing_z"])
        for row in predictor.select("player_id", "tracked_framing_z").iter_rows(named=True)
    }
    if len(predictor_map) != predictor.height:
        raise RuntimeError("duplicate 2024 framing predictor player IDs")
    target_map = {
        int(row["player_id"]): float(row["target_z"])
        for row in target.select("player_id", "target_z").iter_rows(named=True)
    }
    if len(target_map) != target.height:
        raise RuntimeError("duplicate 2025 framing target player IDs")

    _, historical_meta = _load_profiles(args.historical_root)
    catcher = historical_meta["catcher"]
    rows: list[dict[str, Any]] = []
    for row in catcher.filter(
        (pl.col("season") == 2024)
        & (pl.col("fielding_outs") >= 300)
    ).iter_rows(named=True):
        player_id = int(row["player_id"])
        z = predictor_map.get(player_id)
        y = target_map.get(player_id)
        if z is None or y is None:
            continue
        pred = beta[0] + beta[1] * z
        if not math.isfinite(pred) or not math.isfinite(z) or not math.isfinite(y):
            raise RuntimeError(f"nonfinite confirmation value player={player_id}")
        rows.append(
            {
                "component": "catcher_framing_F1",
                "player_id": player_id,
                "position": "C",
                "current_level_group": str(row["current_level_group"]),
                "fielding_outs_2024": int(row["fielding_outs"]),
                "tracked_framing_z_2024": z,
                "target_z": y,
                "b0_prediction": 0.0,
                "candidate_prediction": pred,
                "prior_used": False,
            }
        )

    if len({row["player_id"] for row in rows}) != len(rows):
        raise RuntimeError("duplicate player in 2025 framing confirmation population")
    gate = _catcher_gate(rows, minimum_count=30, mae_tolerance=0.075, minimum_spearman=0.10)
    passed = bool(gate["passed"])
    final_family = "F1_MLB" if passed else "F0_neutral"

    root = args.output_root
    table_root = root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)
    scored = pl.DataFrame(rows).sort("player_id") if rows else pl.DataFrame(
        schema={
            "component": pl.Utf8,
            "player_id": pl.Int64,
            "position": pl.Utf8,
            "current_level_group": pl.Utf8,
            "fielding_outs_2024": pl.Int64,
            "tracked_framing_z_2024": pl.Float64,
            "target_z": pl.Float64,
            "b0_prediction": pl.Float64,
            "candidate_prediction": pl.Float64,
            "prior_used": pl.Boolean,
        }
    )
    scored_path = table_root / "scored_framing_confirmation_rows.parquet"
    scored.write_parquet(scored_path, compression="zstd")

    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_repaired_framing_2025_one_shot_confirmation",
        "status": "confirmation_complete",
        "contract": "docs/defense-v1-framing-2025-confirmation-contract.md",
        "parameter_hash": EXPECTED_PARAMETER_HASH,
        "source": {
            "historical_run_id": EXPECTED_HISTORICAL_RUN,
            "parameter_freeze_run_id": params_report.get("freeze_run_id"),
            "parameter_freeze_sha": params_report.get("freeze_sha"),
            "predictor_source_run_id": predictor_result.get("source_run_id"),
            "predictor_source_sha": predictor_result.get("source_sha"),
            "target_source_run_id": target_result.get("source_run_id"),
            "target_source_sha": target_result.get("source_sha"),
        },
        "catcher_framing_F1_vs_F0": gate,
        "decision": {
            "mlb_framing_f1_confirmed": passed,
            "final_mlb_framing": final_family,
            "final_milb_framing": "F0_neutral_insufficient_transfer_evidence",
            "framing_confirmation_complete": True,
            "additional_framing_tuning_authorized": False,
            "run_value_conversion_authorized_after_defense_handoff_reconciled": True,
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
            "alternate_target": False,
            "alternate_feature": False,
            "tracked_milb_framing_reopened": False,
            "general_range_modified": False,
            "catcher_throwing_modified": False,
            "catcher_blocking_modified": False,
            "playing_time_v1_modified": False,
            "position_role_v1_modified": False,
            "run_value_conversion_performed": False,
            "war_value_calculated": False,
        },
    }
    (root / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"gate": gate, "final_mlb_framing": final_family}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())