#!/usr/bin/env python
"""Validate and persist the frozen event semantics used by the foundation POC."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.event_semantics_registry import (
    current_event_semantics_frame,
    validate_sequence_semantics_links,
)
from universal_baseball.storage import write_canonical_parquet


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--canonical-dir",
        type=Path,
        default=Path("data/canonical/foundation-poc"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/foundation-poc"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sequence_path = args.canonical_dir / "play_sequence_observation.parquet"
    if not sequence_path.exists():
        raise FileNotFoundError(sequence_path)

    sequences = pl.read_parquet(sequence_path)
    semantics = current_event_semantics_frame()
    validate_sequence_semantics_links(sequences, semantics)

    artifact = write_canonical_parquet(
        semantics,
        args.canonical_dir / "event_semantics.parquet",
        table_name="event_semantics",
    )
    snapshot_id = semantics.get_column("event_semantics_snapshot_id")[0]
    classified = sequences.filter(
        pl.col("classification_status").is_in(["official_true_pa", "official_non_pa"])
    )
    payload = {
        "report_schema_version": 1,
        "event_semantics_snapshot_id": snapshot_id,
        "event_semantics_definition_count": semantics.height,
        "classified_sequence_count": classified.height,
        "unclassified_sequence_count": sequences.height - classified.height,
        "artifact": artifact.as_record(),
    }

    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / "event_semantics_poc.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    markdown = "\n".join(
        [
            "# Foundation event-semantics validation",
            "",
            f"- Semantics snapshot: `{snapshot_id}`",
            f"- Registered event definitions: {semantics.height}",
            f"- Classified play sequences checked: {classified.height}",
            f"- Unclassified source sequences in official sequence table: {sequences.height - classified.height}",
            "- Every classified sequence matched its registered PA/non-PA definition: **true**",
            "",
        ]
    )
    (args.report_dir / "event_semantics_poc.md").write_text(
        markdown, encoding="utf-8"
    )
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
