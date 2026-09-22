#!/usr/bin/env python3
"""Run the once-only protected 2026 hitter-gradient confirmation."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_gradient_confirmation import (
    add_confirmation_strata,
    outcome_metrics,
    score_confirmation_rows,
)
from universal_baseball.hitter_gradient_materialization import CONTACT_OUTCOMES
from universal_baseball.projection_bootstrap import paired_player_cluster_bootstrap
from universal_baseball.storage import sha256_file, write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--completed-2026-targets", type=Path, required=True)
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--season-complete",
        action="store_true",
        help="Required explicit declaration that protected 2026 collection is complete.",
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("docs/hitter-gradient-2026-confirmation-contract.json"),
    )
    parser.add_argument(
        "--forecast",
        type=Path,
        default=Path(
            "model_artifacts/hitter-gradient-2026-confirmation-forecast-2026-09-19/"
            "forecast-2026.parquet"
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/hitter-gradient-2026-confirmation"),
    )
    return parser.parse_args()


def _matrix(frame: pl.DataFrame, prefix: str):
    return frame.select(*(f"{prefix}{value}" for value in CONTACT_OUTCOMES)).to_numpy()


def main() -> int:
    args = _args()
    # Refuse before opening the target file. This keeps an accidental invocation
    # from exposing protected rows to the evaluator process.
    if not args.season_complete:
        raise RuntimeError("refusing to open 2026 targets without --season-complete")
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if args.as_of_date < date.fromisoformat(contract["earliest_evaluation_date"]):
        raise RuntimeError("confirmation date precedes the locked evaluation date")
    if sha256_file(args.forecast) != contract["forecast_sha256"]:
        raise RuntimeError("frozen forecast hash does not match the contract")

    forecast = pl.read_parquet(args.forecast)
    targets = pl.read_parquet(args.completed_2026_targets)
    required_targets = {
        "player_id",
        "source_level",
        "contacts",
        *(f"overall__{value}" for value in CONTACT_OUTCOMES),
    }
    if missing := sorted(required_targets - set(targets.columns)):
        raise ValueError(f"completed 2026 targets missing fields: {missing}")
    minimum = int(contract["minimum_target_contacts"])
    target = targets.filter(pl.col("contacts") >= minimum).select(
        "player_id",
        pl.col("source_level").alias("target_source_level"),
        pl.col("contacts").alias("target_contacts"),
        *(pl.col(f"overall__{value}").alias(f"actual__{value}") for value in CONTACT_OUTCOMES),
    )
    rows = (
        forecast.join(target, on="player_id", how="inner", validate="1:1")
        .select(
            "player_id",
            "source_level",
            "target_source_level",
            "contacts",
            "target_contacts",
            *(f"actual__{value}" for value in CONTACT_OUTCOMES),
            *(pl.col(f"contact_only__overall__{value}").alias(f"contact_only__{value}") for value in CONTACT_OUTCOMES),
            *(pl.col(f"gradient__overall__{value}").alias(f"gradient__{value}") for value in CONTACT_OUTCOMES),
        )
        .sort("player_id")
    )
    if rows.height < int(contract["minimum_matched_players"]):
        raise RuntimeError("completed confirmation has too few matched players")
    rows = add_confirmation_strata(rows)
    overall = score_confirmation_rows(rows)
    bootstrap = paired_player_cluster_bootstrap(
        player_ids=rows["player_id"].to_numpy(),
        actual=_matrix(rows, "actual__"),
        baseline=_matrix(rows, "contact_only__"),
        candidate=_matrix(rows, "gradient__"),
        weights=rows["target_contacts"].to_numpy().astype(float),
        repetitions=int(contract["bootstrap_repetitions"]),
        seed=int(contract["bootstrap_seed"]),
    )
    subgroup_rows = []
    for group_type, column in (
        ("source_workload", "source_workload_group"),
        ("level_transition", "level_transition"),
        ("source_level", "source_level"),
    ):
        for group in sorted(str(value) for value in rows[column].unique()):
            selected = rows.filter(pl.col(column) == group)
            result = score_confirmation_rows(selected)
            subgroup_rows.append({"group_type": group_type, "group": group, **result})
    outcomes = outcome_metrics(rows)
    thresholds = contract["promotion_thresholds"]
    supported_harm = [
        row
        for row in subgroup_rows
        if row["players"] >= int(contract["minimum_supported_subgroup_players"])
        and row["gradient_vs_contact_only"]["rate_rmse"]
        > float(thresholds["material_subgroup_rmse_harm"])
        and row["gradient_vs_contact_only"]["multinomial_log_loss"] > 0
    ]
    catastrophic_outcomes = [
        row
        for row in outcomes
        if row["rate_rmse_delta"] > float(thresholds["catastrophic_outcome_rmse_harm"])
    ]
    delta = overall["gradient_vs_contact_only"]
    gates = {
        "overall_rmse_improved": delta["rate_rmse"] < 0,
        "overall_log_loss_improved": delta["multinomial_log_loss"] < 0,
        "overall_brier_improved": delta["multinomial_brier"] < 0,
        "rmse_paired_interval_below_zero": bootstrap["rate_rmse"]["upper_95"] < 0,
        "no_supported_material_subgroup_harm": not supported_harm,
        "no_catastrophic_outcome_harm": not catastrophic_outcomes,
    }
    promoted = all(gates.values())
    args.output_root.mkdir(parents=True, exist_ok=True)
    scored_artifact = write_canonical_parquet(
        rows,
        args.output_root / "scored-players.parquet",
        table_name="hitter_gradient_2026_confirmation_scored_players",
    ).as_record()
    report = {
        "schema_version": "1.0",
        "status": "2026_confirmation_complete",
        "as_of_date": args.as_of_date.isoformat(),
        "forecast_sha256": contract["forecast_sha256"],
        "target_sha256": sha256_file(args.completed_2026_targets),
        "forecast_players": forecast.height,
        "matched_players": rows.height,
        "overall": overall,
        "paired_player_bootstrap": bootstrap,
        "subgroups": subgroup_rows,
        "outcomes": outcomes,
        "supported_material_harm": supported_harm,
        "catastrophic_outcome_harm": catastrophic_outcomes,
        "promotion_gates": gates,
        "production_promoted": promoted,
        "artifact": scored_artifact,
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if promoted else 2


if __name__ == "__main__":
    raise SystemExit(main())
