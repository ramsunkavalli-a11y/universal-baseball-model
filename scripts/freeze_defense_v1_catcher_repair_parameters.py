#!/usr/bin/env python3
"""Freeze repaired Defense v1 catcher parameters before any repaired 2025 access.

Only the two catcher components selected by the repaired, originally preregistered
development gate are refit. General Defense is not loaded or modified. The
corrected 2022-2024 targets and 2021-2023 predictor evidence are the only fitting
inputs.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import platform
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from develop_defense_v1_universal import (
    INPUT_BY_TARGET,
    _catcher_matrix,
    _fit_catcher_normalizer,
    _load_profiles,
    _ridge_fit,
)

TARGET_YEARS = (2022, 2023, 2024)
INPUT_YEARS = (2021, 2022, 2023)
EXPECTED_HISTORICAL_RUN = 32148467330
EXPECTED_REPAIRED_SOURCE_RUN = 32206603934
SELECTED = {
    "throwing": {"family": "C2", "feature": "caught_stealing_pct"},
    "blocking": {"family": "C2", "feature": "passed_balls_per_9"},
}


def _sha_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + sha256(payload).hexdigest()


def _find_one(root: Path, name: str) -> Path:
    matches = list(root.rglob(name))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {name} under {root}; observed={matches}")
    return matches[0]


def _load_targets(root: Path, source: dict[str, Any], kind: str) -> dict[int, pl.DataFrame]:
    out: dict[int, pl.DataFrame] = {}
    for year in TARGET_YEARS:
        path = _find_one(root, f"catcher_{kind}_targets_{year}.parquet")
        storage = source["storage"][f"targets_{kind}_{year}"]
        if _sha_file(path) != storage["sha256"]:
            raise RuntimeError(f"{kind} target SHA mismatch for {year}")
        frame = pl.read_parquet(path)
        if frame.height != int(storage["row_count"]):
            raise RuntimeError(f"{kind} target row-count mismatch for {year}")
        out[year] = frame.select("player_id", "target_raw", "target_z")
    return out


def _fit_component(
    catcher: pl.DataFrame,
    targets: dict[int, pl.DataFrame],
    kind: str,
    feature: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    normalizer = _fit_catcher_normalizer(catcher, set(INPUT_YEARS), feature, kind)
    x, y, meta = _catcher_matrix(
        catcher,
        targets,
        set(TARGET_YEARS),
        normalizer,
        "C2",
        kind,
    )
    if not len(y):
        raise RuntimeError(f"empty repaired {kind} C2 final training set")
    beta = _ridge_fit(x, y, 0.0)
    if not np.isfinite(beta).all():
        raise RuntimeError(f"nonfinite repaired {kind} coefficient")
    params = {
        "component": kind,
        "family": "C2",
        "feature": feature,
        "lambda": 0.0,
        "prior_season_recency_weight": 0.5,
        "exposure": "fielding_outs",
        "coefficients": [float(v) for v in beta],
        "normalization": {
            "feature": str(normalizer.feature),
            "mean": float(normalizer.moment.mean),
            "sd": float(normalizer.moment.sd),
            "count": int(normalizer.moment.count),
        },
        "training_row_count": int(len(y)),
    }
    rows = [
        {
            "component": kind,
            "player_id": int(item["player_id"]),
            "target_year": int(item["target_year"]),
            "input_year": int(INPUT_BY_TARGET[int(item["target_year"])]),
        }
        for item in meta
    ]
    return params, rows


def _fit_once(
    catcher: pl.DataFrame,
    throwing_targets: dict[int, pl.DataFrame],
    blocking_targets: dict[int, pl.DataFrame],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    throwing, throwing_rows = _fit_component(
        catcher, throwing_targets, "throwing", SELECTED["throwing"]["feature"]
    )
    blocking, blocking_rows = _fit_component(
        catcher, blocking_targets, "blocking", SELECTED["blocking"]["feature"]
    )
    return {
        "model_name": "defense_v1_repaired_catcher_pre_2025_parameter_package",
        "training_target_years": list(TARGET_YEARS),
        "training_input_years": list(INPUT_YEARS),
        "catcher_throwing": throwing,
        "catcher_blocking": blocking,
    }, throwing_rows + blocking_rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--repaired-source-root", type=Path, required=True)
    parser.add_argument("--repaired-source-result", type=Path, required=True)
    parser.add_argument("--repaired-development-result", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    source = json.loads(args.repaired_source_result.read_text())
    development = json.loads(args.repaired_development_result.read_text())
    if int(source.get("source_run_id")) != EXPECTED_REPAIRED_SOURCE_RUN:
        raise RuntimeError(f"repaired source run changed: {source.get('source_run_id')}")
    if source.get("boundary", {}).get("2025_catcher_target_accessed") is not False:
        raise RuntimeError("repaired source crossed 2025 boundary")
    decision = development.get("decision", {})
    for kind in ("throwing", "blocking"):
        if decision.get(f"catcher_{kind}_passed") is not True:
            raise RuntimeError(f"repaired {kind} did not pass development")
        if decision.get(f"catcher_{kind}_selected_family") != "C2":
            raise RuntimeError(f"repaired {kind} selection changed")
    if decision.get("repaired_pre_2025_catcher_refit_authorized_next") is not True:
        raise RuntimeError("repaired catcher refit not authorized")
    boundary = development.get("boundary", {})
    if boundary.get("2025_catcher_target_accessed") is not False:
        raise RuntimeError("development result crossed 2025 boundary")
    if boundary.get("general_range_modified") is not False:
        raise RuntimeError("general Defense boundary changed")

    _, profile_meta = _load_profiles(args.historical_root)
    catcher = profile_meta["catcher"]
    throwing_targets = _load_targets(args.repaired_source_root, source, "throwing")
    blocking_targets = _load_targets(args.repaired_source_root, source, "blocking")

    params, training_rows = _fit_once(catcher, throwing_targets, blocking_targets)
    reproduced, reproduced_rows = _fit_once(catcher, throwing_targets, blocking_targets)
    deterministic = params == reproduced and training_rows == reproduced_rows
    if not deterministic:
        raise RuntimeError("repaired catcher refit is not deterministically reproducible")

    root = args.output_root
    table_root = root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)
    training = pl.DataFrame(training_rows).sort(["component", "target_year", "player_id"])
    training_path = table_root / "training_rows.parquet"
    training.write_parquet(training_path, compression="zstd")

    parameter_hash = _canonical_hash(params)
    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_catcher_repair_pre_2025_parameter_freeze",
        "status": "repaired_catcher_parameters_frozen_ready_for_2025_source",
        "contract": "docs/defense-v1-catcher-source-repair-contract.md",
        "parameter_hash": parameter_hash,
        "parameters": params,
        "deterministic_reproduction": {
            "passed": deterministic,
            "comparison": "exact parameter and training-row object equality",
        },
        "source": {
            "historical_run_id": EXPECTED_HISTORICAL_RUN,
            "repaired_target_source_run_id": EXPECTED_REPAIRED_SOURCE_RUN,
            "repaired_target_source_sha": source.get("source_sha"),
            "repaired_development_run_id": development.get("development_run_id"),
            "repaired_development_sha": development.get("development_sha"),
            "target_rows": {
                "throwing": {str(y): int(throwing_targets[y].height) for y in TARGET_YEARS},
                "blocking": {str(y): int(blocking_targets[y].height) for y in TARGET_YEARS},
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
            "repaired_pre_2025_catcher_parameters_frozen": True,
            "repaired_2025_catcher_target_materialization_authorized_next": True,
            "repaired_2025_catcher_confirmation_authorized_after_source_certification": True,
            "general_range_reopened": False,
            "additional_catcher_development_authorized": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "2025_catcher_target_accessed": False,
            "2025_confirmation_residuals_used": False,
            "general_range_loaded_for_fit": False,
            "general_range_modified": False,
            "new_candidate_family_added": False,
            "development_threshold_changed": False,
            "war_calculated": False,
        },
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "parameter_hash": parameter_hash,
        "throwing": params["catcher_throwing"],
        "blocking": params["catcher_blocking"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
