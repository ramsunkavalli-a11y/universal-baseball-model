#!/usr/bin/env python3
"""Validate the first multi-checkpoint Phase 1 replay sequence."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.sequential_replay import replay_value_checkpoints
from universal_baseball.storage import sha256_file, write_canonical_parquet


CHECKPOINT_DATES = ("2025-03-27", "2026-09-08")


def main() -> int:
    root = Path("reports/generated/phase1-sequential-replay")
    output = Path(
        "reports/generated/phase1-sequential-replay-sequence/"
        "2025-03-27_to_2026-09-08"
    )
    record_paths = tuple(root / day / "value-records.parquet" for day in CHECKPOINT_DATES)
    universe_paths = tuple(
        root / day / "frozen-universe.parquet" for day in CHECKPOINT_DATES
    )
    evidence_paths = tuple(
        root / day / "source-evidence.parquet" for day in CHECKPOINT_DATES
    )
    input_paths = record_paths + universe_paths + evidence_paths
    for path in input_paths:
        if not path.is_file():
            raise FileNotFoundError(path)

    result = replay_value_checkpoints(
        pl.concat([pl.read_parquet(path) for path in record_paths]),
        pl.concat([pl.read_parquet(path) for path in universe_paths]),
        pl.concat([pl.read_parquet(path) for path in evidence_paths]),
    )
    output.mkdir(parents=True, exist_ok=True)
    storage = {
        "value_records": write_canonical_parquet(
            result.records,
            output / "value-records.parquet",
            table_name="phase1_replay_sequence_value_records",
        ).as_record(),
        "checkpoint_summary": write_canonical_parquet(
            result.checkpoints,
            output / "checkpoint-summary.parquet",
            table_name="phase1_replay_sequence_checkpoint_summary",
        ).as_record(),
        "delta_ledger": write_canonical_parquet(
            result.deltas,
            output / "delta-ledger.parquet",
            table_name="phase1_replay_sequence_delta_ledger",
        ).as_record(),
    }
    reason_counts: dict[str, int] = {}
    for value in result.deltas.get_column("change_reasons"):
        for reason in str(value).split(","):
            if reason:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
    report = {
        "report_schema_version": "0.1",
        "gate": "phase1_first_multi_checkpoint_replay_sequence",
        "status": "mechanically_valid_not_comparable_model_stability_test",
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
        "boundary": {
            "same_model_version": False,
            "value_stability_inference_authorized": False,
            "mechanical_sequence_validation": True,
            "historical_checkpoint_interval": "point_only_not_calibrated",
        },
        "source_files": {
            path.as_posix(): sha256_file(path) for path in input_paths
        },
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "storage"},
            indent=2,
            sort_keys=True,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
