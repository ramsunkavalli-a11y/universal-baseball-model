#!/usr/bin/env python3
"""Audit tracked-BBE source semantics from retained Savant CSV bytes.

This is a source-only diagnostic. It does not build Baseline 2, fit residual
coefficients, inspect future target outcomes, or score a richer model. Its purpose
is to make the corrected result-producing/non-bunt BBE definition reproducible
against certified raw source caches before historical model evaluation.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import polars as pl

from universal_baseball.current_talent_batted_ball_quality import (
    build_batted_ball_quality_features,
    project_complete_tracked_bbe,
)


SOURCE_COLUMNS = (
    "game_date",
    "game_pk",
    "batter",
    "at_bat_number",
    "pitch_number",
    "events",
    "type",
    "des",
    "description",
    "launch_speed",
    "launch_angle",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--cutoff", type=date.fromisoformat, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    return parser.parse_args()


def _read_retained_savant(raw_root: Path) -> tuple[pl.DataFrame, list[Path]]:
    paths = sorted(raw_root.rglob("*.csv"))
    if not paths:
        raise ValueError(f"no retained Savant CSV files found under {raw_root}")
    frames = [
        pl.read_csv(
            path,
            columns=list(SOURCE_COLUMNS),
            infer_schema=False,
            null_values=["", "null", "NA"],
            ignore_errors=False,
        )
        for path in paths
    ]
    return pl.concat(frames, how="vertical_relaxed"), paths


def _mean_or_none(frame: pl.DataFrame, column: str) -> float | None:
    if frame.is_empty():
        return None
    value = frame.get_column(column).mean()
    return None if value is None else float(value)


def _median_or_none(frame: pl.DataFrame, column: str) -> float | None:
    if frame.is_empty():
        return None
    value = frame.get_column(column).median()
    return None if value is None else float(value)


def build_source_semantics_report(raw: pl.DataFrame, *, cutoff: date) -> dict[str, object]:
    dated = raw.with_columns(
        pl.col("game_date").cast(pl.String).str.to_date(strict=False).alias("_game_date")
    ).filter(pl.col("_game_date") < pl.lit(cutoff))

    ev = pl.col("launch_speed").cast(pl.Float64, strict=False)
    la = pl.col("launch_angle").cast(pl.Float64, strict=False)
    complete = ev.is_not_null() & la.is_not_null()
    result_type = pl.col("type").cast(pl.String).str.strip_chars().str.to_uppercase()
    event_nonblank = pl.col("events").is_not_null() & (
        pl.col("events").cast(pl.String).str.strip_chars() != ""
    )
    bunt = (
        pl.col("des")
        .cast(pl.String)
        .fill_null("")
        .str.to_lowercase()
        .str.contains(r"\bbunt\b")
    )
    foul = (
        pl.col("description")
        .cast(pl.String)
        .fill_null("")
        .str.strip_chars()
        .str.to_lowercase()
        == "foul"
    )

    complete_contact_rows = dated.filter(complete).height
    complete_foul_rows = dated.filter(complete & foul).height
    complete_result_bbe_before_bunt = dated.filter(
        complete & (result_type == "X") & event_nonblank
    ).height
    complete_result_bunts = dated.filter(
        complete & (result_type == "X") & event_nonblank & bunt
    ).height

    tracked_bbe = project_complete_tracked_bbe(raw)
    features = build_batted_ball_quality_features(tracked_bbe, cutoff=cutoff)
    eligible = features.filter(pl.col("tracked_bbe_eligible"))

    return {
        "report_schema_version": "0.1",
        "scope": "tracked_batted_ball_source_semantics_only",
        "cutoff": cutoff.isoformat(),
        "retrospective_event_cutoff": True,
        "model_scoring_performed": False,
        "residual_coefficients_fit": False,
        "raw_pre_cutoff_rows": int(dated.height),
        "complete_ev_la_contact_rows": int(complete_contact_rows),
        "complete_ev_la_foul_rows": int(complete_foul_rows),
        "complete_result_bbe_before_bunt_exclusion": int(complete_result_bbe_before_bunt),
        "complete_result_bunts_excluded": int(complete_result_bunts),
        "canonical_result_non_bunt_bbe": int(
            tracked_bbe.filter(pl.col("game_date") < pl.lit(cutoff)).height
        ),
        "player_with_pre_cutoff_bbe_count": int(features.height),
        "player_ge20_bbe_count": int(eligible.height),
        "eligible_median_raw_complete_tracked_bbe": _median_or_none(
            eligible, "raw_complete_tracked_bbe"
        ),
        "eligible_median_effective_complete_tracked_bbe": _median_or_none(
            eligible, "effective_complete_tracked_bbe"
        ),
        "eligible_mean_weighted_exit_velocity": _mean_or_none(
            eligible, "recency_weighted_mean_exit_velocity"
        ),
        "eligible_mean_weighted_sweet_spot_share": _mean_or_none(
            eligible, "recency_weighted_sweet_spot_share"
        ),
        "canonical_key": "game_pk+player_id+at_bat_number+pitch_number",
        "canonical_bbe_definition": (
            "type_X_plus_terminal_event_plus_complete_EV_LA_minus_explicit_bunt"
        ),
    }


def main() -> int:
    args = _parse_args()
    raw, paths = _read_retained_savant(args.raw_root)
    report = build_source_semantics_report(raw, cutoff=args.cutoff)
    report["raw_csv_file_count"] = len(paths)
    report["raw_root"] = str(args.raw_root)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
