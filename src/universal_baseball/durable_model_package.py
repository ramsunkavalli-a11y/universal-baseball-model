"""Durably preserve a complete, hash-verified playing-time scoring package."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
from uuid import uuid4

import polars as pl

from universal_baseball.playing_time_confirmation import load_frozen_playing_time_fit
from universal_baseball.playing_time_model import (
    playing_time_continuous_features,
    playing_time_feature_names,
)
from universal_baseball.storage import sha256_file


PLAYING_TIME_REFIT_FILES = {
    "candidate_coefficients": "candidate_coefficients.parquet",
    "candidate_standardization": "candidate_standardization.parquet",
    "baseline0_coefficients": "baseline0_coefficients.parquet",
    "baseline0_standardization": "baseline0_standardization.parquet",
}


def _unique_file(root: Path, filename: str) -> Path:
    matches = sorted(path for path in root.rglob(filename) if path.is_file())
    if len(matches) != 1:
        raise ValueError(f"expected one {filename} under {root}, found {len(matches)}")
    return matches[0]


def _verify_source_file(path: Path, record: dict[str, object], label: str) -> None:
    expected_size = int(record["file_size_bytes"])
    expected_hash = str(record["file_sha256"])
    if path.stat().st_size != expected_size:
        raise ValueError(f"{label} size differs from refit report")
    if sha256_file(path) != expected_hash:
        raise ValueError(f"{label} hash differs from refit report")


def _validate_loadable_fit(
    report: dict[str, object], source_files: dict[str, Path]
) -> None:
    candidate_training = dict(report["candidate_training"])
    baseline_training = dict(report["baseline0_training"])
    load_frozen_playing_time_fit(
        pl.read_parquet(source_files["candidate_coefficients"]),
        pl.read_parquet(source_files["candidate_standardization"]),
        form=str(report["selected_form"]),
        expected_nb_alpha=float(report["candidate_nb_alpha"]),
        participation_training_players=int(
            candidate_training["training_observation_count"]
        ),
        positive_training_players=0,
    )
    load_frozen_playing_time_fit(
        pl.read_parquet(source_files["baseline0_coefficients"]),
        pl.read_parquet(source_files["baseline0_standardization"]),
        form=str(report["baseline0_form"]),
        expected_nb_alpha=float(report["baseline0_nb_alpha"]),
        participation_training_players=int(
            baseline_training["training_observation_count"]
        ),
        positive_training_players=0,
    )


def persist_playing_time_refit_package(
    refit_root: Path, destination_root: Path
) -> dict[str, object]:
    """Copy one complete refit into permanent storage after strict validation.

    Existing destinations are never overwritten. The report, all scoring tables,
    and a package manifest move into place together.
    """

    report_path = refit_root / "report.json"
    if not report_path.is_file():
        raise ValueError(f"playing-time refit report missing: {report_path}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("status") != "frozen_ready_for_2025_source_materialization":
        raise ValueError("playing-time refit is not in the frozen-ready state")
    if not bool(dict(report.get("decision", {})).get("parameters_frozen_before_2025")):
        raise ValueError("playing-time refit does not certify a pre-outcome freeze")
    if not report.get("source_run_id") or not report.get("source_sha"):
        raise ValueError("playing-time refit lacks pinned source identifiers")

    storage = dict(report.get("storage", {}))
    if set(storage) != set(PLAYING_TIME_REFIT_FILES):
        raise ValueError("playing-time refit storage does not contain the exact scoring set")
    source_files: dict[str, Path] = {}
    for key, filename in PLAYING_TIME_REFIT_FILES.items():
        record = dict(storage[key])
        source = _unique_file(refit_root, filename)
        _verify_source_file(source, record, key)
        source_files[key] = source
    _validate_loadable_fit(report, source_files)

    if destination_root.exists():
        raise FileExistsError(f"durable model package already exists: {destination_root}")
    destination_root.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination_root.with_name(
        f".{destination_root.name}.{uuid4().hex}.tmp"
    )
    try:
        table_root = temporary / "tables"
        table_root.mkdir(parents=True)
        shutil.copy2(report_path, temporary / "refit-report.json")
        files: dict[str, dict[str, object]] = {
            "refit-report.json": {
                "bytes": report_path.stat().st_size,
                "sha256": sha256_file(report_path),
            }
        }
        for key, filename in PLAYING_TIME_REFIT_FILES.items():
            target = table_root / filename
            shutil.copy2(source_files[key], target)
            files[f"tables/{filename}"] = {
                "bytes": target.stat().st_size,
                "sha256": sha256_file(target),
                "storage_key": key,
            }
        manifest: dict[str, object] = {
            "schema_version": "0.1",
            "package_type": "playing_time_hurdle_refit",
            "source_run_id": int(report["source_run_id"]),
            "source_sha": str(report["source_sha"]),
            "selected_form": str(report["selected_form"]),
            "baseline0_form": str(report["baseline0_form"]),
            "selected_feature_names": list(
                playing_time_feature_names(str(report["selected_form"]))
            ),
            "selected_continuous_features": list(
                playing_time_continuous_features(str(report["selected_form"]))
            ),
            "distribution_parameters": {
                "candidate_nb_alpha": float(report["candidate_nb_alpha"]),
                "baseline0_nb_alpha": float(report["baseline0_nb_alpha"]),
            },
            "training_target_years": list(report["training_target_years"]),
            "package_versions": dict(report["package_versions"]),
            "complete_scoring_package": True,
            "files": files,
        }
        (temporary / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary, destination_root)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return manifest
