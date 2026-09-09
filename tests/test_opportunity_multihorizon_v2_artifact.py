import json
from pathlib import Path

import polars as pl

from universal_baseball.playing_time_confirmation import load_frozen_playing_time_fit
from universal_baseball.storage import sha256_file


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "model_artifacts/opportunity-multihorizon-v2-development-2026-09-09"


def test_multihorizon_v2_package_is_hash_bound_and_loadable() -> None:
    manifest = json.loads((PACKAGE / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((PACKAGE / "report.json").read_text(encoding="utf-8"))
    for relative_path, record in manifest["files"].items():
        path = PACKAGE / relative_path
        assert path.stat().st_size == record["bytes"]
        assert sha256_file(path) == record["sha256"]

    selections = {
        (row["component"], row["horizon"]): row for row in report["selection"]
    }
    for component in manifest["selected_components"]:
        for horizon in manifest["selected_horizons"]:
            selection = selections[(component, horizon)]
            package = PACKAGE / "tables" / component / f"horizon-{horizon}"
            fit = load_frozen_playing_time_fit(
                pl.read_parquet(package / "selected_coefficients.parquet"),
                pl.read_parquet(package / "selected_standardization.parquet"),
                form=selection["selected_model"],
                expected_nb_alpha=selection["selected_nb_alpha"],
                participation_training_players=selection["final_training_players"],
                positive_training_players=selection["final_positive_players"],
            )
            assert fit.form == selection["selected_model"]
    assert report["source_gate_failed_horizons"] == {
        "5": "only one chronology-safe evaluation fold",
        "6": "no chronology-safe evaluation fold",
    }
    assert manifest["production_confirmed"] is False

