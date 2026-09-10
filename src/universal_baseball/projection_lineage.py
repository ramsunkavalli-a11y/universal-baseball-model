"""Build-lineage checks for projection artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from universal_baseball.storage import sha256_file


PLAYABLE_OPPORTUNITY_MODEL_ID = "phase2_prior_mlb_workload_anchor_v1"


def validate_opportunity_source(
    tables_root: Path,
    *,
    expected_model_id: str | None = None,
) -> dict[str, Any]:
    """Describe and, when requested, enforce the opportunity model lineage."""

    hitter_path = tables_root / "hitter_opportunity_paths.parquet"
    pitcher_path = tables_root / "pitcher_opportunity_paths.parquet"
    report_path = tables_root.parent / "report.json"
    if not report_path.exists():
        if expected_model_id is not None:
            raise ValueError(
                "expected opportunity model lineage cannot be checked because "
                f"{report_path} is missing"
            )
        report = None
    else:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    source_model_id = None if report is None else report.get("model_id")
    if expected_model_id is not None and source_model_id != expected_model_id:
        raise ValueError(
            "opportunity model lineage mismatch: expected "
            f"{expected_model_id!r}, found {source_model_id!r}"
        )
    return {
        "tables_root": tables_root.as_posix(),
        "hitter_sha256": sha256_file(hitter_path),
        "pitcher_sha256": sha256_file(pitcher_path),
        "source_gate": None if report is None else report.get("gate"),
        "source_model_id": source_model_id,
    }


def validate_recorded_opportunity_source(
    recorded: dict[str, Any],
    *,
    expected_model_id: str,
) -> dict[str, Any]:
    """Require a downstream report to match its exact opportunity artifacts."""

    if recorded.get("source_model_id") != expected_model_id:
        raise ValueError(
            "recorded opportunity model lineage mismatch: expected "
            f"{expected_model_id!r}, found {recorded.get('source_model_id')!r}"
        )
    tables_root = Path(str(recorded.get("tables_root", "")))
    actual = validate_opportunity_source(
        tables_root, expected_model_id=expected_model_id
    )
    for key in ("hitter_sha256", "pitcher_sha256"):
        if recorded.get(key) != actual[key]:
            raise ValueError(f"recorded opportunity artifact hash mismatch: {key}")
    return actual


def validate_arrival_source(
    dated_root: Path,
    *,
    expected_model_id: str,
) -> dict[str, Any]:
    """Describe and enforce the exact prospect-arrival model artifacts."""

    report_path = dated_root / "report.json"
    if not report_path.exists():
        raise ValueError(
            "expected arrival model lineage cannot be checked because "
            f"{report_path} is missing"
        )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    source_model_id = report.get("model_id")
    if source_model_id != expected_model_id:
        raise ValueError(
            "arrival model lineage mismatch: expected "
            f"{expected_model_id!r}, found {source_model_id!r}"
        )
    return {
        "dated_root": dated_root.as_posix(),
        "hitter_sha256": sha256_file(
            dated_root / "hitter-arrival-probabilities.parquet"
        ),
        "pitcher_sha256": sha256_file(
            dated_root / "pitcher-arrival-probabilities.parquet"
        ),
        "source_gate": report.get("gate"),
        "source_model_id": source_model_id,
    }


def validate_recorded_arrival_source(
    recorded: dict[str, Any],
    *,
    expected_model_id: str,
) -> dict[str, Any]:
    """Require a downstream report to match its exact arrival artifacts."""

    if recorded.get("source_model_id") != expected_model_id:
        raise ValueError(
            "recorded arrival model lineage mismatch: expected "
            f"{expected_model_id!r}, found {recorded.get('source_model_id')!r}"
        )
    dated_root = Path(str(recorded.get("dated_root", "")))
    actual = validate_arrival_source(
        dated_root, expected_model_id=expected_model_id
    )
    for key in ("hitter_sha256", "pitcher_sha256"):
        if recorded.get(key) != actual[key]:
            raise ValueError(f"recorded arrival artifact hash mismatch: {key}")
    return actual
