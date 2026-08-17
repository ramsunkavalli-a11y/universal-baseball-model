#!/usr/bin/env python3
"""Combine certified MiLB level artifacts and materialize one validation snapshot."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import polars as pl

from universal_baseball.current_talent_evidence import EvidenceWindow
from universal_baseball.current_talent_universal_evidence import (
    combine_universal_player_game_evidence,
)
from universal_baseball.current_talent_validation import FutureHorizon
from universal_baseball.current_talent_validation_dataset import (
    build_validation_snapshot_dataset,
)


FILENAME_LEVELS = ("aaa", "aa", "a+", "a", "rk")
TABLE_LEVEL_TOKEN = {
    "aaa": "aaa",
    "aa": "aa",
    "a+": "aplus",
    "a": "a",
    "rk": "rk",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--cutoff", type=str, required=True)
    parser.add_argument("--window-label", type=str, default="all_history")
    parser.add_argument("--lookback-days", type=int)
    parser.add_argument("--half-life-days", type=float)
    parser.add_argument("--horizon-label", type=str, default="future_90d")
    parser.add_argument("--horizon-days", type=int, default=90)
    parser.add_argument("--aggregate-pa-cap", type=int, default=200)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def _one(root: Path, pattern: str) -> Path:
    matches = sorted(root.rglob(pattern))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {pattern} under {root}, found {len(matches)}")
    return matches[0]


def _transition_counts(frame: pl.DataFrame) -> dict[str, int]:
    if frame.is_empty():
        return {}
    return {
        str(row["target_transition"]): int(row["len"])
        for row in frame.group_by("target_transition")
        .len()
        .sort("target_transition")
        .iter_rows(named=True)
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

    summaries: list[pl.DataFrame] = []
    profiles: list[pl.DataFrame] = []
    inputs: list[dict[str, str]] = []
    for level in FILENAME_LEVELS:
        table_level = TABLE_LEVEL_TOKEN[level]
        summary_path = _one(
            args.input_root,
            f"current_talent_game_summary_{args.season}_{table_level}.parquet",
        )
        profile_path = _one(
            args.input_root,
            f"current_talent_game_profile_{args.season}_{table_level}.parquet",
        )
        summaries.append(pl.read_parquet(summary_path))
        profiles.append(pl.read_parquet(profile_path))
        inputs.append(
            {
                "filename_level": level,
                "table_level_token": table_level,
                "summary": str(summary_path),
                "profile": str(profile_path),
            }
        )

    summary, profile, combination_metrics = combine_universal_player_game_evidence(
        summaries,
        profiles,
        expected_seasons={int(args.season)},
        require_all_universal_leagues=False,
    )
    observed_levels = set(summary.get_column("level_group").unique().to_list())
    expected_levels = {"AAA", "AA", "HIGH_A", "SINGLE_A", "ROOKIE_COMPLEX"}
    if observed_levels != expected_levels:
        raise ValueError(
            "multilevel MiLB validation surface level coverage mismatch: "
            f"observed={sorted(observed_levels)}, expected={sorted(expected_levels)}"
        )

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
        "scope": "affiliated_milb_five_level_combined",
        "season": int(args.season),
        "cutoff": cutoff.isoformat(),
        "temporal_semantics": "retrospective_event_cutoff_corrected_history_not_vintage_information_set",
        "inputs": inputs,
        "combined_evidence_metrics": combination_metrics,
        "validation_metrics": dataset.metrics,
        "transition_row_counts": _transition_counts(dataset.scoring_rows),
        "output_tables": output_tables,
        "horizon": {
            "label": horizon.label,
            "calendar_days": horizon.calendar_days,
            "aggregate_pa_cap": horizon.aggregate_pa_cap,
            "aggregate_pa_cap_applied": False,
            "aggregate_pa_cap_status": "requires_pa_grain_future_events",
        },
        "interpretation": (
            "Five-level affiliated-MiLB validation evidence. Cross-level future outcomes remain "
            "in the actual environment where they occurred. This artifact validates chronology "
            "and transition labeling only; it does not fit Current Talent or level translation."
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
