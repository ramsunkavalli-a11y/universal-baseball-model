#!/usr/bin/env python3
"""Materialize the fixed 2024 MLB centering membership and projected-PA anchor."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import polars as pl

from universal_baseball.player_value_mlb_centering_assembly import (
    EXPECTED_2024_MLB_REFERENCE_PLAYER_COUNT,
    PlayingTimeReferenceCandidate,
    select_fixed_2024_mlb_reference_members,
    summarize_fixed_mlb_reference_membership,
)

EXPECTED_2024_OBSERVED_MLB_PA = 182_449.0
PLAYING_TIME_PROJECTED_PA_COLUMN = "predicted_expected_mlb_pa"
REQUIRED_COLUMNS = {
    "player_id",
    "observed_mlb_pa",
    PLAYING_TIME_PROJECTED_PA_COLUMN,
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--playing-time-scored", type=Path, required=True)
    parser.add_argument("--output-membership-parquet", type=Path, required=True)
    parser.add_argument("--output-summary-json", type=Path, required=True)
    parser.add_argument("--playing-time-run-id", type=int, required=True)
    parser.add_argument("--playing-time-artifact-id", type=int, required=True)
    parser.add_argument("--playing-time-artifact-digest", required=True)
    parser.add_argument("--playing-time-source-sha", required=True)
    parser.add_argument("--materialization-run-id", type=int, required=True)
    parser.add_argument("--materialization-source-sha", required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    frame = pl.read_parquet(args.playing_time_scored)
    missing = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing:
        raise ValueError(f"Playing Time scored table missing columns: {missing}")

    source = frame.select(
        pl.col("player_id"),
        pl.col("observed_mlb_pa").cast(pl.Float64),
        pl.col(PLAYING_TIME_PROJECTED_PA_COLUMN)
        .cast(pl.Float64)
        .alias("projected_expected_mlb_pa"),
    )
    rows = [
        PlayingTimeReferenceCandidate(
            player_id=row["player_id"],
            observed_mlb_pa=row["observed_mlb_pa"],
            projected_expected_mlb_pa=row["projected_expected_mlb_pa"],
        )
        for row in source.iter_rows(named=True)
    ]
    members = select_fixed_2024_mlb_reference_members(rows)
    summary = summarize_fixed_mlb_reference_membership(members)

    observed_reference = source.filter(pl.col("observed_mlb_pa") > 0.0)
    observed_reference_pa = float(observed_reference["observed_mlb_pa"].sum())
    if not math.isclose(
        observed_reference_pa,
        EXPECTED_2024_OBSERVED_MLB_PA,
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        raise ValueError(
            "2024 observed MLB PA anchor mismatch: "
            f"expected {EXPECTED_2024_OBSERVED_MLB_PA}, got {observed_reference_pa}"
        )

    membership = pl.DataFrame(
        {
            "player_id": [row.player_id for row in members],
            "projected_expected_mlb_pa": [
                row.projected_expected_mlb_pa for row in members
            ],
        }
    ).sort("player_id")
    if membership["player_id"].n_unique() != EXPECTED_2024_MLB_REFERENCE_PLAYER_COUNT:
        raise ValueError("materialized membership is not unique by player_id")

    args.output_membership_parquet.parent.mkdir(parents=True, exist_ok=True)
    args.output_summary_json.parent.mkdir(parents=True, exist_ok=True)
    membership.write_parquet(args.output_membership_parquet)

    result = {
        "schema_version": "0.1",
        "status": "player_value_v1_mlb_centering_2024_membership_verified",
        "centering_id": "fixed_2024_mlb_projected_component_reference_v1",
        "reference_season": 2024,
        "membership_definition": "positive official observed 2024 MLB PA; pooled AL/NL",
        "reference_player_count": summary.reference_player_count,
        "aggregate_observed_mlb_pa_membership_anchor": observed_reference_pa,
        "aggregate_projected_mlb_pa": summary.aggregate_projected_mlb_pa,
        "playing_time_input_row_count": source.height,
        "playing_time_projected_pa_input_column": PLAYING_TIME_PROJECTED_PA_COLUMN,
        "centering_projected_pa_output_field": "projected_expected_mlb_pa",
        "playing_time_source": {
            "run_id": args.playing_time_run_id,
            "artifact_id": args.playing_time_artifact_id,
            "artifact_digest": args.playing_time_artifact_digest,
            "source_sha": args.playing_time_source_sha,
            "scored_table_sha256": _sha256(args.playing_time_scored),
        },
        "materialization": {
            "run_id": args.materialization_run_id,
            "source_sha": args.materialization_source_sha,
        },
        "verification": {
            "expected_reference_player_count": EXPECTED_2024_MLB_REFERENCE_PLAYER_COUNT,
            "player_count_matches": summary.reference_player_count
            == EXPECTED_2024_MLB_REFERENCE_PLAYER_COUNT,
            "expected_observed_mlb_pa": EXPECTED_2024_OBSERVED_MLB_PA,
            "observed_mlb_pa_matches": math.isclose(
                observed_reference_pa,
                EXPECTED_2024_OBSERVED_MLB_PA,
                rel_tol=0.0,
                abs_tol=1e-9,
            ),
            "membership_unique_by_player_id": membership["player_id"].n_unique()
            == membership.height,
            "projected_mlb_pa_nonnegative_and_finite": bool(
                membership.select(
                    (
                        pl.col("projected_expected_mlb_pa").is_finite()
                        & (pl.col("projected_expected_mlb_pa") >= 0.0)
                    ).all()
                ).item()
            ),
            "aggregate_projected_mlb_pa_positive": summary.aggregate_projected_mlb_pa
            > 0.0,
            "realized_pa_used_for_exposure": False,
            "numerical_centering_constant_materialized": False,
        },
    }
    args.output_summary_json.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
