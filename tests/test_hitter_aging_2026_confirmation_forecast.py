import json
from pathlib import Path

import polars as pl

from universal_baseball.storage import sha256_file


ROOT = Path(__file__).parents[1]
ARTIFACT = ROOT / "model_artifacts/hitter-aging-2026-confirmation-forecast-2026-09-10"


def test_hitter_aging_confirmation_is_frozen_and_denominators_match() -> None:
    report = json.loads((ARTIFACT / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "frozen_before_2026_outcome_access"
    assert report["2026_outcomes_read"] is False
    assert sha256_file(ROOT / report["runner_path"]) == report["runner_sha256"]
    assert sha256_file(ROOT / report["contract_path"]) == report["contract_sha256"]
    marcel = pl.read_parquet(ARTIFACT / "marcel-aging.parquet")
    no_aging = pl.read_parquet(ARTIFACT / "no-aging.parquet")
    assert marcel.height == no_aging.height == report["players"]
    assert marcel.get_column("player_id").equals(no_aging.get_column("player_id"))
    assert marcel.get_column("expected_mlb_pa").equals(no_aging.get_column("expected_mlb_pa"))
    assert marcel.get_column("expected_war").sum() != no_aging.get_column("expected_war").sum()
