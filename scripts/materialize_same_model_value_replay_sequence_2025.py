#!/usr/bin/env python3
"""Compare March and October 2025 value checkpoints under one Phase 1 method."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.sequential_replay import replay_value_checkpoints
from universal_baseball.storage import sha256_file, write_canonical_parquet


CHECKPOINT_DATES = ("2025-03-27", "2025-10-15")


def main() -> int:
    root = Path("reports/generated/phase1-sequential-replay")
    output = Path(
        "reports/generated/phase1-sequential-replay-sequence/"
        "2025-03-27_to_2025-10-15"
    )
    record_paths = tuple(root / day / "value-records.parquet" for day in CHECKPOINT_DATES)
    universe_paths = tuple(
        root / day / "frozen-universe.parquet" for day in CHECKPOINT_DATES
    )
    evidence_paths = tuple(
        root / day / "source-evidence.parquet" for day in CHECKPOINT_DATES
    )
    input_paths = record_paths + universe_paths + evidence_paths
    result = replay_value_checkpoints(
        pl.concat([pl.read_parquet(path) for path in record_paths]),
        pl.concat([pl.read_parquet(path) for path in universe_paths]),
        pl.concat([pl.read_parquet(path) for path in evidence_paths]),
    )

    records = result.records
    earlier = records.filter(pl.col("checkpoint_id").str.contains("opening-day")).select(
        "player_id",
        pl.col("calculation_status").alias("earlier_status"),
        pl.col("transferable_value_dollars").alias("earlier_value"),
    )
    later = records.filter(pl.col("checkpoint_id").str.contains("postseason")).select(
        "player_id",
        pl.col("calculation_status").alias("later_status"),
        pl.col("transferable_value_dollars").alias("later_value"),
    )
    shared_available = earlier.join(later, on="player_id", how="inner").filter(
        (pl.col("earlier_status") == "available")
        & (pl.col("later_status") == "available")
    ).with_columns(
        (pl.col("later_value") - pl.col("earlier_value")).alias("value_delta")
    )
    reason_counts: dict[str, int] = {}
    for value in result.deltas.get_column("change_reasons"):
        for reason in str(value).split(","):
            if reason:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1

    output.mkdir(parents=True, exist_ok=True)
    storage = {
        "value_records": write_canonical_parquet(
            result.records,
            output / "value-records.parquet",
            table_name="phase1_same_model_value_sequence_records",
        ).as_record(),
        "checkpoint_summary": write_canonical_parquet(
            result.checkpoints,
            output / "checkpoint-summary.parquet",
            table_name="phase1_same_model_value_sequence_summary",
        ).as_record(),
        "delta_ledger": write_canonical_parquet(
            result.deltas,
            output / "delta-ledger.parquet",
            table_name="phase1_same_model_value_sequence_deltas",
        ).as_record(),
        "shared_available": write_canonical_parquet(
            shared_available,
            output / "shared-available-value-changes.parquet",
            table_name="phase1_same_model_shared_available_values",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "phase1_same_model_value_replay_sequence",
        "status": "mechanically_valid_same_method_update_not_accuracy_score",
        "checkpoint_dates": list(CHECKPOINT_DATES),
        "checkpoints": result.checkpoints.to_dicts(),
        "delta_rows": result.deltas.height,
        "material_value_delta_rows": result.deltas.filter(
            pl.col("is_material_value_change")
        ).height,
        "unexplained_material_delta_rows": result.deltas.filter(
            pl.col("delta_status") != "available"
        ).height,
        "change_reason_counts": dict(sorted(reason_counts.items())),
        "shared_available_players": shared_available.height,
        "shared_value_correlation": float(
            shared_available.select(pl.corr("earlier_value", "later_value")).item()
        ),
        "shared_mean_absolute_value_change_dollars": float(
            shared_available.get_column("value_delta").abs().mean()
        ),
        "shared_median_absolute_value_change_dollars": float(
            shared_available.get_column("value_delta").abs().median()
        ),
        "shared_total_value_change_dollars": float(
            shared_available.get_column("value_delta").sum()
        ),
        "boundary": {
            "same_model_version": True,
            "opportunity_fit_refit": False,
            "completed_2025_season_removed_from_remaining_value": True,
            "projection_and_rights_evidence_updated": True,
            "contract_term_table_frozen": True,
            "forecast_horizon_rolls_forward": True,
            "value_stability_inference": "descriptive_same_method_update_only",
            "accuracy_inference_authorized": False,
            "historical_checkpoint_interval": "point_only_not_calibrated",
        },
        "source_files": {path.as_posix(): sha256_file(path) for path in input_paths},
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in report.items() if key != "storage"}, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
