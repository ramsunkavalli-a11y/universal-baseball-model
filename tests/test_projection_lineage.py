from __future__ import annotations

import json
from pathlib import Path

import pytest

from universal_baseball.projection_lineage import (
    validate_opportunity_source,
    validate_recorded_opportunity_source,
)


def _source(tmp_path: Path, model_id: str = "latest") -> Path:
    tables = tmp_path / "build" / "tables"
    tables.mkdir(parents=True)
    (tables / "hitter_opportunity_paths.parquet").write_bytes(b"hitters")
    (tables / "pitcher_opportunity_paths.parquet").write_bytes(b"pitchers")
    (tables.parent / "report.json").write_text(
        json.dumps({"gate": "workload", "model_id": model_id}),
        encoding="utf-8",
    )
    return tables


def test_validate_opportunity_source_records_exact_artifacts(tmp_path: Path) -> None:
    source = validate_opportunity_source(
        _source(tmp_path), expected_model_id="latest"
    )
    assert source["source_model_id"] == "latest"
    assert source["source_gate"] == "workload"
    assert len(source["hitter_sha256"]) == 64
    assert source["hitter_sha256"] != source["pitcher_sha256"]


def test_validate_opportunity_source_rejects_stale_model(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="lineage mismatch"):
        validate_opportunity_source(
            _source(tmp_path, model_id="stale"), expected_model_id="latest"
        )


def test_validate_recorded_source_rejects_changed_artifact(tmp_path: Path) -> None:
    tables = _source(tmp_path)
    recorded = validate_opportunity_source(tables, expected_model_id="latest")
    (tables / "pitcher_opportunity_paths.parquet").write_bytes(b"changed")
    with pytest.raises(ValueError, match="artifact hash mismatch"):
        validate_recorded_opportunity_source(
            recorded, expected_model_id="latest"
        )
