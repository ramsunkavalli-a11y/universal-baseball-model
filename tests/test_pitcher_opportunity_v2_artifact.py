import json
from pathlib import Path

import polars as pl

from universal_baseball.playing_time_confirmation import load_frozen_playing_time_fit
from universal_baseball.storage import sha256_file


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "model_artifacts" / "pitcher-opportunity-v2-development-2026-09-09"


def test_pitcher_opportunity_v2_package_is_hash_bound_and_loadable() -> None:
    manifest = json.loads((PACKAGE / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((PACKAGE / "report.json").read_text(encoding="utf-8"))
    for relative_path, record in manifest["files"].items():
        path = PACKAGE / relative_path
        assert path.stat().st_size == record["bytes"]
        assert sha256_file(path) == record["sha256"]

    fit = load_frozen_playing_time_fit(
        pl.read_parquet(PACKAGE / "tables" / "selected_coefficients.parquet"),
        pl.read_parquet(PACKAGE / "tables" / "selected_standardization.parquet"),
        form=report["selected_form"],
        expected_nb_alpha=report["selected_nb_alpha"],
        participation_training_players=report["final_training_players"],
        positive_training_players=report["final_positive_players"],
    )
    assert fit.form == manifest["model_form"]
    assert manifest["complete_scoring_package"] is True
    assert manifest["production_confirmed"] is False
    assert report["metric_unit"] == "batters_faced"
    assert report["boundary"]["protected_2026_outcomes_used"] is False

