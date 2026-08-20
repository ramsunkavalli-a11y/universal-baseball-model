#!/usr/bin/env python
"""Materialize the required Baseball-Reference positional sensitivity."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import polars as pl

from universal_baseball.player_value_positional_adjustment import (
    BREF_POSITIONAL_RUNS_PER_150,
    BREF_SENSITIVITY_SCHEDULE_ID,
    DEFENSIVE_POSITIONS,
    POSITIONAL_RUNS_PER_162,
    SCHEDULE_ID,
    calculate_bref_positional_sensitivity,
    calculate_v1_positional_adjustment,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--position-allocation", type=Path, required=True)
    parser.add_argument("--dh-exposure", type=Path, required=True)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/player-value-v1-positional-adjustment-sensitivity-2024.json"),
    )
    parser.add_argument(
        "--output-table",
        type=Path,
        default=Path("reports/generated/player-value-v1-positional-adjustment-sensitivity-2024.parquet"),
    )
    args = parser.parse_args()

    position = pl.read_parquet(args.position_allocation).filter(
        (pl.col("current_season") == 2023) & (pl.col("next_season") == 2024)
    )
    dh = pl.read_parquet(args.dh_exposure).filter(
        (pl.col("source_year") == 2023) & (pl.col("target_year") == 2024)
    )
    if position.height != 3046 or dh.height != 3046:
        raise ValueError("frozen 2024 positional sensitivity surface must contain 3,046 rows")
    if position.get_column("player_id").n_unique() != position.height:
        raise ValueError("position allocation contains duplicate players")
    if dh.get_column("player_id").n_unique() != dh.height:
        raise ValueError("DH exposure contains duplicate players")
    joined = position.join(
        dh.select("player_id", "B0_raw_dh_role_event_persistence"),
        on="player_id",
        how="inner",
    ).sort("player_id")
    if joined.height != 3046:
        raise ValueError("position and DH sensitivity surfaces do not reconcile")

    rows: list[dict[str, object]] = []
    for row in joined.iter_rows(named=True):
        outs = {
            position_name: float(row[f"S0_predicted_outs_{position_name}"])
            for position_name in DEFENSIVE_POSITIONS
        }
        dh_events = float(row["B0_raw_dh_role_event_persistence"])
        binding = calculate_v1_positional_adjustment(
            outs, projected_dh_role_events=dh_events
        )
        sensitivity = calculate_bref_positional_sensitivity(
            outs, projected_dh_role_events=dh_events
        )
        rows.append(
            {
                "player_id": int(row["player_id"]),
                "fangraphs_positional_runs": binding.total_runs,
                "baseball_reference_sensitivity_positional_runs": sensitivity.total_runs,
                "sensitivity_minus_binding_runs": sensitivity.total_runs - binding.total_runs,
            }
        )
    result = pl.DataFrame(rows).sort("player_id")
    differences = result.get_column("sensitivity_minus_binding_runs")
    largest = (
        result.with_columns(differences.abs().alias("absolute_difference"))
        .sort("absolute_difference", descending=True)
        .head(10)
        .drop("absolute_difference")
        .to_dicts()
    )
    payload = {
        "schema_version": "0.1",
        "status": "player_value_v1_positional_adjustment_sensitivity_2024_frozen_verified",
        "contract": "docs/player-value-v1-positional-adjustment-contract.md",
        "reference_season": 2024,
        "source_commit": str(os.environ.get("GITHUB_SHA") or "").strip() or None,
        "actions_run_id": int(os.environ["GITHUB_RUN_ID"]) if os.environ.get("GITHUB_RUN_ID") else None,
        "inputs": {
            "position_allocation": {"run_id": 32266007594, "artifact_id": 9370211679},
            "dh_exposure": {"run_id": 32270141291, "artifact_id": 9371840453},
            "player_count": result.height,
        },
        "binding_schedule": {
            "schedule_id": SCHEDULE_ID,
            "values": dict(POSITIONAL_RUNS_PER_162),
        },
        "sensitivity_schedule": {
            "schedule_id": BREF_SENSITIVITY_SCHEDULE_ID,
            "values": dict(BREF_POSITIONAL_RUNS_PER_150),
        },
        "aggregate": {
            "fangraphs_positional_runs": float(result.get_column("fangraphs_positional_runs").sum()),
            "baseball_reference_sensitivity_positional_runs": float(
                result.get_column("baseball_reference_sensitivity_positional_runs").sum()
            ),
            "sensitivity_minus_binding_runs": float(differences.sum()),
        },
        "difference_distribution_runs": {
            "minimum": float(differences.min()),
            "p05": float(differences.quantile(0.05, interpolation="linear")),
            "median": float(differences.median()),
            "mean": float(differences.mean()),
            "p95": float(differences.quantile(0.95, interpolation="linear")),
            "maximum": float(differences.max()),
            "mean_absolute": float(differences.abs().mean()),
        },
        "largest_absolute_player_differences": largest,
        "boundary": {
            "binding_schedule_changed": False,
            "exposure_refit": False,
            "league_centering_applied": False,
            "war_calculated": False,
        },
    }
    args.output_table.parent.mkdir(parents=True, exist_ok=True)
    result.write_parquet(args.output_table)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload["aggregate"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
