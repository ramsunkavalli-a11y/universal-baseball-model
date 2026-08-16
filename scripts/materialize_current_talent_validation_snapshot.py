#!/usr/bin/env python3
"""Materialize one deterministic Current Talent predictor/target snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import date

import polars as pl

from universal_baseball.current_talent_evidence import EvidenceWindow
from universal_baseball.current_talent_validation import FutureHorizon
from universal_baseball.current_talent_validation_dataset import (
    build_validation_snapshot_dataset,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--cutoff", type=str, required=True)
    parser.add_argument("--window-label", type=str, default="all_history")
    parser.add_argument("--lookback-days", type=int)
    parser.add_argument("--half-life-days", type=float)
    parser.add_argument("--horizon-label", type=str, default="future_90d")
    parser.add_argument("--horizon-days", type=int, default=90)
    parser.add_argument("--aggregate-pa-cap", type=int, default=200)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def _transition_counts(frame: pl.DataFrame) -> dict[str, int]:
    if frame.is_empty() or "target_transition" not in frame.columns:
        return {}
    rows = frame.group_by("target_transition").len().sort("target_transition")
    return {
        str(row["target_transition"]): int(row["len"])
        for row in rows.iter_rows(named=True)
    }


def main() -> int:
    args = _parse_args()
    cutoff = date.fromisoformat(args.cutoff)
    window = EvidenceWindow(
        label=args.window_label,
        lookback_days=args.lookback_days,
        half_life_days=args.half_life_days,
    )
    horizon = FutureHorizon(
        label=args.horizon_label,
        calendar_days=int(args.horizon_days),
        aggregate_pa_cap=int(args.aggregate_pa_cap),
        primary=args.horizon_label == "future_90d" and int(args.horizon_days) == 90,
    )

    summary = pl.read_parquet(args.summary)
    profile = pl.read_parquet(args.profile)
    dataset = build_validation_snapshot_dataset(
        summary,
        profile,
        cutoff=cutoff,
        window=window,
        horizon=horizon,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    tables = {
        "predictor_summary": dataset.predictor_summary,
        "predictor_profile": dataset.predictor_profile,
        "target_summary": dataset.target_summary,
        "target_profile": dataset.target_profile,
        "scoring_rows": dataset.scoring_rows,
    }
    output_tables: dict[str, dict[str, object]] = {}
    for name, frame in tables.items():
        path = args.output_dir / f"{name}.parquet"
        frame.write_parquet(path, compression="zstd")
        output_tables[name] = {
            "path": str(path),
            "row_count": int(frame.height),
            "column_count": len(frame.columns),
        }

    report = {
        "report_schema_version": "0.1",
        "accepted": True,
        "temporal_semantics": "retrospective_event_cutoff_corrected_history_not_vintage_information_set",
        "source_summary": str(args.summary),
        "source_profile": str(args.profile),
        "cutoff": cutoff.isoformat(),
        "window": {
            "label": window.label,
            "lookback_days": window.lookback_days,
            "half_life_days": window.half_life_days,
        },
        "horizon": {
            "label": horizon.label,
            "calendar_days": horizon.calendar_days,
            "aggregate_pa_cap": horizon.aggregate_pa_cap,
            "aggregate_pa_cap_applied": False,
            "aggregate_pa_cap_status": "requires_pa_grain_future_events",
        },
        "metrics": dataset.metrics,
        "transition_row_counts": _transition_counts(dataset.scoring_rows),
        "output_tables": output_tables,
        "interpretation": (
            "Production-shaped validation evidence only. Future outcomes remain in their actual "
            "season/league/level environment. No Current Talent model, environment translation, "
            "or aggregate 200-PA diagnostic is fitted or claimed by this artifact."
        ),
    }
    (args.output_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
