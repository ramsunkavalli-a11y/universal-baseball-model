import json
from pathlib import Path

import polars as pl

from universal_baseball.storage import sha256_file


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "model_artifacts/opportunity-v2-2026-confirmation-forecast-2026-09-09"


def test_confirmation_forecast_is_hash_bound_and_has_identical_component_rows() -> None:
    manifest = json.loads((PACKAGE / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((PACKAGE / "report.json").read_text(encoding="utf-8"))
    for relative_path, record in manifest["files"].items():
        path = PACKAGE / relative_path
        assert path.stat().st_size == record["bytes"]
        assert sha256_file(path) == record["sha256"]

    for component, expected_rows in (
        ("hitter", report["hitter_players"]),
        ("pitcher", report["pitcher_players"]),
    ):
        frames = [
            pl.read_parquet(PACKAGE / f"{component}-{model}.parquet")
            for model in ("selected", "parametric-baseline", "incumbent")
        ]
        ids = [frame.get_column("player_id").to_list() for frame in frames]
        assert all(frame.height == expected_rows for frame in frames)
        assert ids[0] == ids[1] == ids[2]

    assert report["target_status"] == (
        "not_read_waiting_for_completed_regular_season"
    )
    assert report["boundary"]["any_2026_outcome_file_read"] is False
    assert manifest["target_outcomes_included"] is False
    assert manifest["immutable_confirmation_input"] is True

