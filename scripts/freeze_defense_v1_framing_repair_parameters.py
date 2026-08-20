#!/usr/bin/env python3
"""Freeze repaired Defense v1 MLB catcher-framing F1 parameters before 2025 target access."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import platform
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from audit_defense_v1_tracked_challenger import (
    _find_one,
    _framing_rows_for_year,
    _z_framing,
)
from develop_defense_v1_universal import _load_profiles, _ridge_fit

TARGET_YEARS = (2022, 2023, 2024)
EXPECTED_HISTORICAL_RUN = 32148467330
EXPECTED_TRACKED_RUN = 32182019495
EXPECTED_TRACKED_SHA = "5438e905d24e2167432a52253320ccbc978186b8"
EXPECTED_TRACKED_FRAMING_SHA = "1071b9d8209d6e9ba9d8c2b42ac7b99e3329387704e2910797b58f1a148cbc79"
EXPECTED_REPAIRED_TARGET_RUN = 32208273343
CONFIRMATION_CONTRACT = Path("docs/defense-v1-framing-2025-confirmation-contract.md")


def _sha_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + sha256(payload).hexdigest()


def _load_targets(root: Path, source: dict[str, Any]) -> dict[int, pl.DataFrame]:
    targets: dict[int, pl.DataFrame] = {}
    for year in TARGET_YEARS:
        path = _find_one(root, f"catcher_framing_targets_{year}.parquet")
        expected = source["storage"][f"targets_{year}"]["sha256"]
        if _sha_file(path) != expected:
            raise RuntimeError(f"repaired framing target SHA mismatch for {year}")
        frame = pl.read_parquet(path)
        if frame.height != int(source["storage"][f"targets_{year}"]["row_count"]):
            raise RuntimeError(f"repaired framing target row-count mismatch for {year}")
        needed = {"target_year", "player_id", "target_z"}
        missing = sorted(needed - set(frame.columns))
        if missing:
            raise RuntimeError(f"repaired framing target {year} missing {missing}")
        years = {
            int(value)
            for value in frame.get_column("target_year").cast(pl.Int64, strict=False).drop_nulls().unique().to_list()
        }
        if years != {year}:
            raise RuntimeError(f"repaired framing target {year} contains years={sorted(years)}")
        targets[year] = frame.select(
            pl.col("player_id").cast(pl.Int64),
            pl.col("target_z").cast(pl.Float64),
        ).sort("player_id")
    return targets


def _fit_once(
    catcher: pl.DataFrame,
    targets: dict[int, pl.DataFrame],
    framing_z: dict[tuple[int, str, int], float],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    catcher_index = {
        (int(row["season"]), int(row["player_id"])): row
        for row in catcher.iter_rows(named=True)
    }
    z_parts: list[np.ndarray] = []
    y_parts: list[np.ndarray] = []
    training_rows: list[dict[str, Any]] = []
    for target_year in TARGET_YEARS:
        z, y, player_ids = _framing_rows_for_year(
            target_year,
            targets,
            framing_z,
            catcher_index,
            mode="MLB",
        )
        if not len(y):
            raise RuntimeError(f"empty framing F1 full-development rows for target_year={target_year}")
        if len(z) != len(y) or len(player_ids) != len(y):
            raise RuntimeError(f"framing F1 row alignment mismatch for target_year={target_year}")
        z_parts.append(z)
        y_parts.append(y)
        input_year = target_year - 1
        for player_id, predictor, target in zip(player_ids, z, y, strict=True):
            training_rows.append(
                {
                    "player_id": int(player_id),
                    "input_year": int(input_year),
                    "target_year": int(target_year),
                    "tracked_framing_z": float(predictor),
                    "target_z": float(target),
                }
            )

    z_all = np.concatenate(z_parts)
    y_all = np.concatenate(y_parts)
    beta = _ridge_fit(z_all.reshape(-1, 1), y_all, 0.0)
    if not np.isfinite(beta).all():
        raise RuntimeError("nonfinite repaired framing F1 frozen coefficient")

    params = {
        "model_name": "defense_v1_repaired_framing_pre_2025_parameter_package",
        "component": "catcher_framing",
        "family": "F1",
        "scope": "MLB_only",
        "lambda": 0.0,
        "predictor": "tracked_framing_z",
        "coefficients": [float(value) for value in beta],
        "training_target_years": list(TARGET_YEARS),
        "training_input_years": [2021, 2022, 2023],
        "training_row_count": int(len(y_all)),
        "predictor_construction": {
            "source_feature": "tracked_framing_per_1000_takes",
            "minimum_takes": 500,
            "standardization": "within source season x level_group; population sd ddof=0",
            "minimum_standardization_cell_count": 15,
            "eligible_levels_for_f1": ["MLB"],
            "input_catcher_minimum_fielding_outs": 300,
        },
        "target_construction": {
            "source": "repaired Baseball Savant catcher-framing year-specific leaderboard",
            "minimum_pitches": 1000,
            "raw_target": "1000 * rv_tot / pitches",
            "standardization": "within target season; population sd ddof=0",
        },
        "coverage_fallback": {
            "eligible_mlb_with_tracking": "F1",
            "mlb_without_eligible_tracking": "F0_neutral",
            "affiliated_milb": "F0_neutral",
            "tracked_milb_f1": "closed_for_v1_insufficient_transfer_evidence",
        },
    }
    return params, training_rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--tracked-root", type=Path, required=True)
    parser.add_argument("--repaired-source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    tracked_source = json.loads(Path("docs/defense-v1-tracked-source-result.json").read_text())
    repaired_source = json.loads(Path("docs/defense-v1-framing-repair-development-source-result.json").read_text())
    repaired_dev = json.loads(Path("docs/defense-v1-framing-repair-development-result.json").read_text())

    if tracked_source.get("source_run_id") != EXPECTED_TRACKED_RUN:
        raise RuntimeError(f"tracked source run changed: {tracked_source.get('source_run_id')}")
    if tracked_source.get("source_sha") != EXPECTED_TRACKED_SHA:
        raise RuntimeError("tracked source SHA changed")
    if tracked_source.get("decision", {}).get("tracked_source_materialized") is not True:
        raise RuntimeError("tracked source is not certified")
    if tracked_source.get("boundary", {}).get("2025_source_accessed") is not False:
        raise RuntimeError("tracked source crossed 2025 boundary")

    if int(repaired_source.get("source_run_id")) != EXPECTED_REPAIRED_TARGET_RUN:
        raise RuntimeError(f"repaired framing target run changed: {repaired_source.get('source_run_id')}")
    if repaired_source.get("decision", {}).get("year_specific_source_certified") is not True:
        raise RuntimeError("repaired framing targets are not certified")
    if repaired_source.get("boundary", {}).get("2025_framing_target_accessed") is not False:
        raise RuntimeError("repaired framing target source crossed 2025 boundary")

    decision = repaired_dev.get("decision", {})
    required = {
        "tier_a_tracked_framing_passed": True,
        "tier_b_tracked_framing_transfer_passed": False,
        "mlb_framing_family_after_repair": "F1",
        "framing_repair_development_closed": True,
        "framing_parameter_freeze_authorized_next": True,
        "2025_framing_confirmation_authorized": False,
        "additional_framing_development_challenger_authorized": False,
        "war_value_authorized": False,
    }
    for key, expected in required.items():
        if decision.get(key) != expected:
            raise RuntimeError(f"repaired framing development {key}={decision.get(key)!r}; expected {expected!r}")
    boundary = repaired_dev.get("boundary", {})
    if boundary.get("2025_defensive_targets_accessed") is not False:
        raise RuntimeError("repaired framing development crossed 2025 boundary")
    if boundary.get("tracked_framing_predictor_modified") is not False:
        raise RuntimeError("tracked framing predictor changed during repair")

    contract_text = CONFIRMATION_CONTRACT.read_text()
    required_contract = [
        "Before any 2025 framing target access",
        "takes >= 500",
        "fielding outs >= 300",
        "F1 MSE is strictly lower than F0 MSE",
        "F1 Spearman correlation with the 2025 target is at least 0.10",
    ]
    missing_contract = [item for item in required_contract if item not in contract_text]
    if missing_contract:
        raise RuntimeError(f"confirmation contract missing frozen terms: {missing_contract}")

    _, historical_meta = _load_profiles(args.historical_root)
    catcher = historical_meta["catcher"]
    targets = _load_targets(args.repaired_source_root, repaired_source)

    framing_path = _find_one(args.tracked_root, "tracked_framing_proxy_2021_2023.parquet")
    if _sha_file(framing_path) != EXPECTED_TRACKED_FRAMING_SHA:
        raise RuntimeError("tracked framing artifact SHA changed")
    framing_frame = pl.read_parquet(framing_path)
    framing_z = _z_framing(framing_frame)
    if not framing_z:
        raise RuntimeError("no eligible tracked framing predictor values")

    params, rows = _fit_once(catcher, targets, framing_z)
    reproduced, reproduced_rows = _fit_once(catcher, targets, framing_z)
    deterministic = params == reproduced and rows == reproduced_rows
    if not deterministic:
        raise RuntimeError("repaired framing parameter freeze is not deterministic")

    root = args.output_root
    table_root = root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)
    training = pl.DataFrame(rows).sort(["target_year", "player_id"])
    training_path = table_root / "training_rows.parquet"
    training.write_parquet(training_path, compression="zstd")

    parameter_hash = _canonical_hash(params)
    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_framing_repair_pre_2025_parameter_freeze",
        "status": "repaired_framing_parameters_frozen_ready_for_2024_predictor_source",
        "contract": str(CONFIRMATION_CONTRACT),
        "parameter_hash": parameter_hash,
        "parameters": params,
        "deterministic_reproduction": {
            "passed": deterministic,
            "comparison": "exact parameter and training-row object equality",
        },
        "source": {
            "historical_run_id": EXPECTED_HISTORICAL_RUN,
            "tracked_source_run_id": EXPECTED_TRACKED_RUN,
            "tracked_source_sha": EXPECTED_TRACKED_SHA,
            "tracked_framing_sha256": EXPECTED_TRACKED_FRAMING_SHA,
            "repaired_target_source_run_id": EXPECTED_REPAIRED_TARGET_RUN,
            "repaired_target_source_sha": repaired_source.get("source_sha"),
            "repaired_target_combined_sha256": repaired_source.get("storage", {}).get("all_targets", {}).get("sha256"),
            "repaired_development_run_id": repaired_dev.get("development_run_id"),
            "repaired_development_sha": repaired_dev.get("development_sha"),
            "target_rows": {
                str(year): int(repaired_source["storage"][f"targets_{year}"]["row_count"])
                for year in TARGET_YEARS
            },
        },
        "storage": {
            "training_rows": {
                "path": str(training_path).replace("\\", "/"),
                "row_count": int(training.height),
                "file_size_bytes": training_path.stat().st_size,
                "sha256": _sha_file(training_path),
            }
        },
        "package_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "polars": pl.__version__,
        },
        "decision": {
            "repaired_pre_2025_framing_parameters_frozen": True,
            "2024_framing_confirmation_predictor_materialization_authorized_next": True,
            "2025_framing_target_materialization_authorized": False,
            "2025_framing_confirmation_authorized_after_source_certification": True,
            "tracked_milb_framing_authorized": False,
            "additional_framing_development_authorized": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "live_source_query_performed": False,
            "2025_framing_target_accessed": False,
            "2025_confirmation_residuals_used": False,
            "tracked_framing_predictor_redefined": False,
            "general_range_modified": False,
            "catcher_throwing_modified": False,
            "catcher_blocking_modified": False,
            "new_candidate_family_added": False,
            "development_threshold_changed": False,
            "run_value_conversion_performed": False,
            "war_calculated": False,
        },
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(
        {
            "parameter_hash": parameter_hash,
            "training_row_count": params["training_row_count"],
            "coefficients": params["coefficients"],
        },
        indent=2,
        sort_keys=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())