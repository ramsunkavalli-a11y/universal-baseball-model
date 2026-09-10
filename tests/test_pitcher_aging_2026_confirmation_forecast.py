import json
from pathlib import Path

import polars as pl

from universal_baseball.storage import sha256_file


ROOT = Path(__file__).parents[1]
ARTIFACT = ROOT / "model_artifacts/pitcher-aging-2026-confirmation-forecast-2026-09-10"


def test_pitcher_aging_confirmation_is_frozen_and_denominators_match() -> None:
    report = json.loads((ARTIFACT / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "frozen_before_2026_outcome_access"
    assert report["2026_outcomes_read"] is False
    assert sha256_file(ROOT / report["runner_path"]) == report["runner_sha256"]
    assert sha256_file(ROOT / report["contract_path"]) == report["contract_sha256"]
    tango = pl.read_parquet(ARTIFACT / "tango-aging.parquet")
    no_aging = pl.read_parquet(ARTIFACT / "no-aging.parquet")
    assert tango.height == no_aging.height == report["players"]
    assert tango.get_column("player_id").equals(no_aging.get_column("player_id"))
    assert tango.get_column("expected_mlb_bf").equals(no_aging.get_column("expected_mlb_bf"))
    assert tango.get_column("expected_war").sum() != no_aging.get_column("expected_war").sum()
