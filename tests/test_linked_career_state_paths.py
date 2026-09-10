import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_mlb_progression import SIMULATED_STATE_CODES
from universal_baseball.storage import sha256_file


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "model_artifacts/prospect-linked-career-state-paths-2009-2025"


def test_linked_career_state_paths_are_complete_and_hash_bound() -> None:
    report = json.loads((PACKAGE / "report.json").read_text(encoding="utf-8"))
    assert report["current_2026_used"] is False
    assert report["production_changed"] is False
    assert sha256_file(ROOT / report["runner_path"]) == report["runner_sha256"]
    for path, expected in report["sources"].items():
        assert sha256_file(ROOT / path) == expected
    record = report["storage"]
    path = ROOT / record["path"]
    assert sha256_file(path) == record["file_sha256"]
    frame = pl.read_parquet(path)
    assert frame.height == report["annual_rows"]
    assert frame.group_by("path_player_id", "player_type").len()["len"].unique().to_list() == [6]
    assert report["players_with_age_evidence"] + report["players_without_age_evidence"] == report["players"]
    assert frame.filter(~pl.col("age_evidence_available"))["season_age_years"].is_null().all()


def test_linked_career_state_paths_are_monotone_and_keep_2020_scales_separate() -> None:
    frame = pl.read_parquet(PACKAGE / "annual-state-paths.parquet")
    assert frame.with_columns(
        pl.col("from_state").replace_strict(SIMULATED_STATE_CODES).alias("f"),
        pl.col("to_state").replace_strict(SIMULATED_STATE_CODES).alias("t"),
    ).filter(pl.col("t") < pl.col("f")).is_empty()
    shortened = frame.filter(pl.col("source_season") == 2020)
    assert shortened.height > 0
    assert (
        shortened["adjusted_workload"]
        >= shortened["raw_workload"]
    ).all()
