import json
from pathlib import Path

import polars as pl

from universal_baseball.storage import sha256_file


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "model_artifacts/prospect-post-arrival-progression-2025"


def test_progression_artifact_is_complete_and_hash_bound() -> None:
    report = json.loads((PACKAGE / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "validated_equations_materialized_not_integrated"
    assert report["production_changed"] is False
    assert sha256_file(ROOT / report["runner_path"]) == report["runner_sha256"]
    for path, expected in report["sources"].items():
        assert sha256_file(ROOT / path) == expected
    for record in report["storage"].values():
        path = ROOT / record["path"]
        assert path.stat().st_size == record["file_size_bytes"]
        assert sha256_file(path) == record["file_sha256"]


def test_progression_artifact_uses_workload_only_for_supported_transition() -> None:
    coefficients = pl.read_parquet(PACKAGE / "coefficients.parquet")
    support = pl.read_parquet(PACKAGE / "support.parquet")
    assert support.height == 4
    assert support["maximum_outcome_year"].to_list() == [2025] * 4
    fringe = coefficients.filter(pl.col("origin_state") == "FRINGE_MLB")
    meaningful = coefficients.filter(pl.col("origin_state") == "MEANINGFUL_MLB")
    assert fringe.filter(pl.col("term") == "prior_mlb_active").height == 2
    assert meaningful.filter(pl.col("term") == "prior_mlb_active").is_empty()
    assert coefficients.filter(pl.col("term").str.contains("role")).is_empty()
