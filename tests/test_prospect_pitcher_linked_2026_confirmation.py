import json
from pathlib import Path

import polars as pl

from universal_baseball.storage import sha256_file


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "model_artifacts/prospect-pitcher-linked-2026-confirmation-forecast-2026-09-10"


def test_prospect_pitcher_linked_confirmation_is_frozen_and_hash_bound() -> None:
    report = json.loads((PACKAGE / "report.json").read_text(encoding="utf-8"))
    assert report["2026_outcomes_read"] is False
    assert sha256_file(ROOT / report["contract_path"]) == report["contract_sha256"]
    assert sha256_file(ROOT / report["runner_path"]) == report["runner_sha256"]
    for record in report["storage"].values():
        path = ROOT / record["path"]
        assert path.stat().st_size == record["file_size_bytes"]
        assert sha256_file(path) == record["file_sha256"]
    prospects = pl.read_parquet(PACKAGE / "prospect-forecast-inputs.parquet")
    paths = pl.read_parquet(PACKAGE / "linked-positive-paths.parquet")
    assert prospects.height == report["prospect_pitchers"]
    assert prospects.get_column("player_id").n_unique() == prospects.height
    assert paths.height == report["linked_positive_paths"]
    assert paths.get_column("adjusted_workload").min() > 0
