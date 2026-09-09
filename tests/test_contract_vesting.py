import json
from pathlib import Path

import polars as pl
import pytest

from universal_baseball.contract_vesting import evaluate_vesting_triggers


ROOT = Path(__file__).resolve().parents[1]


def _triggers() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "player_id": [1, 2, 3],
            "player_name": ["One", "Two", "Three"],
            "organization_id": [100, 100, 100],
            "option_season": [2027, 2027, 2027],
            "trigger_season": [2026, 2026, 2026],
            "metric": ["pitching_outs", "plate_appearances", "pitching_outs"],
            "threshold_count": [120, 500, 510],
            "other_conditions": ["clean physical", "", ""],
            "vested_contract_effect": ["guaranteed", "guaranteed", "player option"],
            "unvested_contract_effect": ["mutual option", "club option", "free agent"],
            "source_url": ["https://example.test"] * 3,
            "source_snapshot_id": ["test"] * 3,
        }
    )


def test_thresholds_resolve_only_when_evidence_is_final_or_irreversible() -> None:
    observations = pl.DataFrame(
        {
            "player_id": [1, 2, 3],
            "season": [2026, 2026, 2026],
            "metric": ["pitching_outs", "plate_appearances", "pitching_outs"],
            "observed_count": [130, 450, 400],
            "season_complete": [False, False, True],
        }
    )
    result = evaluate_vesting_triggers(_triggers(), observations)
    assert result.rows.get_column("trigger_status").to_list() == [
        "stat_threshold_met_other_conditions_pending",
        "pending",
        "not_vested",
    ]
    assert result.coverage["pending_rows"] == 2
    assert result.coverage["not_vested_rows"] == 1


def test_simple_threshold_can_vest_before_season_end() -> None:
    observations = pl.DataFrame(
        {
            "player_id": [2],
            "season": [2026],
            "metric": ["plate_appearances"],
            "observed_count": [500],
            "season_complete": [False],
        }
    )
    result = evaluate_vesting_triggers(_triggers().filter(pl.col("player_id") == 2), observations)
    assert result.rows.item(0, "trigger_status") == "vested"


def test_invalid_or_duplicate_trigger_fails_closed() -> None:
    triggers = _triggers().filter(pl.col("player_id") == 1)
    empty_observations = pl.DataFrame(
        schema={
            "player_id": pl.Int64,
            "season": pl.Int64,
            "metric": pl.String,
            "observed_count": pl.Int64,
            "season_complete": pl.Boolean,
        }
    )
    with pytest.raises(ValueError, match="grain"):
        evaluate_vesting_triggers(pl.concat([triggers, triggers]), empty_observations)
    with pytest.raises(ValueError, match="invalid threshold"):
        evaluate_vesting_triggers(
            triggers.with_columns(pl.lit("innings").alias("metric")),
            empty_observations,
        )


def test_repo_trigger_inventory_is_valid_and_missing_evidence_stays_missing() -> None:
    payload = json.loads(
        (ROOT / "config/contract-vesting-triggers-2026-09-09.json").read_text(
            encoding="utf-8"
        )
    )
    triggers = pl.DataFrame(payload["triggers"]).with_columns(
        pl.lit(payload["snapshot_id"]).alias("source_snapshot_id")
    )
    observations = pl.DataFrame(
        schema={
            "player_id": pl.Int64,
            "season": pl.Int64,
            "metric": pl.String,
            "observed_count": pl.Int64,
            "season_complete": pl.Boolean,
        }
    )
    result = evaluate_vesting_triggers(triggers, observations)
    assert result.coverage == {
        "trigger_rows": 4,
        "observed_rows": 0,
        "vested_rows": 0,
        "not_vested_rows": 0,
        "pending_rows": 0,
        "missing_evidence_rows": 4,
    }
