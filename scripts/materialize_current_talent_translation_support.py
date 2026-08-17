#!/usr/bin/env python3
"""Materialize matched-environment support from certified multilevel game evidence."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import polars as pl

from universal_baseball.current_talent_translation import (
    build_training_environment_transition_evidence,
)
from universal_baseball.current_talent_universal_evidence import (
    combine_universal_player_game_evidence,
)


FILENAME_LEVEL_TOKENS = {
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
    parser.add_argument("--training-end", type=str, required=True)
    parser.add_argument("--min-core-events-per-stint", type=int, default=20)
    parser.add_argument("--max-gap-days", type=int, default=365)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def _one(root: Path, pattern: str) -> Path:
    matches = sorted(root.rglob(pattern))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {pattern} under {root}, found {len(matches)}")
    return matches[0]


def _support_rows(frame: pl.DataFrame) -> list[dict[str, object]]:
    if frame.is_empty():
        return []
    grouped = (
        frame.group_by(["from_level_group", "to_level_group", "transition"])
        .agg(
            pl.len().cast(pl.Int64).alias("pair_count"),
            pl.col("player_id").n_unique().cast(pl.Int64).alias("player_count"),
            pl.col("pair_precision_weight").sum().alias("pair_precision_weight"),
            pl.col("from_core_events").sum().cast(pl.Int64).alias("from_core_events"),
            pl.col("to_core_events").sum().cast(pl.Int64).alias("to_core_events"),
        )
        .sort(["from_level_group", "to_level_group", "transition"])
    )
    return [dict(row) for row in grouped.iter_rows(named=True)]


def main() -> int:
    args = _parse_args()
    training_end = date.fromisoformat(args.training_end)

    summaries: list[pl.DataFrame] = []
    profiles: list[pl.DataFrame] = []
    inputs: list[dict[str, str]] = []
    for filename_level, token in FILENAME_LEVEL_TOKENS.items():
        summary_path = _one(
            args.input_root,
            f"current_talent_game_summary_{args.season}_{token}.parquet",
        )
        profile_path = _one(
            args.input_root,
            f"current_talent_game_profile_{args.season}_{token}.parquet",
        )
        summaries.append(pl.read_parquet(summary_path))
        profiles.append(pl.read_parquet(profile_path))
        inputs.append(
            {
                "filename_level": filename_level,
                "file_token": token,
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
            "translation support diagnostic level coverage mismatch: "
            f"observed={sorted(observed_levels)}, expected={sorted(expected_levels)}"
        )

    evidence = build_training_environment_transition_evidence(
        summary,
        profile,
        training_end=training_end,
        min_core_events_per_stint=int(args.min_core_events_per_stint),
        max_gap_days=int(args.max_gap_days),
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    tables = {
        "stint_summary": evidence.stint_summary,
        "stint_profile": evidence.stint_profile,
        "pair_summary": evidence.pair_summary,
        "pair_profile": evidence.pair_profile,
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

    eligible = evidence.pair_summary.filter(pl.col("translation_pair_eligible"))
    eligible_cross_level = eligible.filter(pl.col("from_level_group") != pl.col("to_level_group"))
    observed_pair_levels = sorted(
        set(eligible_cross_level.get_column("from_level_group").to_list())
        | set(eligible_cross_level.get_column("to_level_group").to_list())
    ) if not eligible_cross_level.is_empty() else []

    report = {
        "report_schema_version": "0.1",
        "accepted": True,
        "scope": "affiliated_milb_translation_support_only",
        "season": int(args.season),
        "training_end_exclusive": training_end.isoformat(),
        "temporal_semantics": "retrospective_event_cutoff_corrected_history_not_vintage_information_set",
        "inputs": inputs,
        "combined_evidence_metrics": combination_metrics,
        "translation_evidence_metrics": evidence.metrics,
        "eligible_pair_support": _support_rows(eligible),
        "eligible_cross_level_pair_support": _support_rows(eligible_cross_level),
        "eligible_cross_level_levels": observed_pair_levels,
        "mlb_anchor_fit_status": "not_attempted_affiliated_milb_only",
        "output_tables": output_tables,
        "interpretation": (
            "Support diagnostic for the candidate matched-adjacent-stint translation layer. "
            "No level offsets are fitted because this artifact contains affiliated MiLB only; "
            "an MLB-connected training graph is required before MLB-anchor translation is claimed."
        ),
    }
    report_path = args.output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
