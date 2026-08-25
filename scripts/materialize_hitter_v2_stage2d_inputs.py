#!/usr/bin/env python3
"""Materialize chronology-safe, unfit J0 event-model inputs."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_v2_stage2d import (
    BINARY_CONTEXT_NODES,
    build_prior_pitcher_binary_feature,
    build_prior_pitcher_hit_composition_features,
)
from universal_baseball.storage import write_canonical_parquet


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--label-sidecar",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-terminal-outcome-label-sidecar/tables/"
            "hitter_v2_terminal_outcome_label_sidecar_2021_2024.parquet"
        ),
    )
    parser.add_argument(
        "--label-result",
        type=Path,
        default=Path("docs/hitter-v2-terminal-outcome-label-sidecar-result.json"),
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("docs/hitter-v2-stage2d-development-contract.json"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2d-inputs"),
    )
    return parser.parse_args()


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _node_coverage(frame: pl.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for node in BINARY_CONTEXT_NODES:
        eligible = frame.filter(pl.col(f"{node.name}_eligible"))
        prior_n = eligible[f"{node.name}_prior_pitcher_denominator"]
        residual = eligible[f"{node.name}_prior_pitcher_log_odds_residual"]
        rows.append(
            {
                "node": node.name,
                "eligible_pa": eligible.height,
                "prior_pitcher_1_pa": int((prior_n >= 1).sum()),
                "prior_pitcher_50_pa": int((prior_n >= 50).sum()),
                "prior_pitcher_100_pa": int((prior_n >= 100).sum()),
                "zero_evidence_pa": int((prior_n == 0).sum()),
                "residual_mean": float(residual.mean()),
                "residual_sd": float(residual.std()),
                "residual_min": float(residual.min()),
                "residual_max": float(residual.max()),
            }
        )
    eligible = frame.filter(pl.col("HIT_COMPOSITION_eligible"))
    prior_n = eligible["HIT_COMPOSITION_prior_pitcher_denominator"]
    rows.append(
        {
            "node": "HIT_COMPOSITION",
            "eligible_pa": eligible.height,
            "prior_pitcher_1_pa": int((prior_n >= 1).sum()),
            "prior_pitcher_50_pa": int((prior_n >= 50).sum()),
            "prior_pitcher_100_pa": int((prior_n >= 100).sum()),
            "zero_evidence_pa": int((prior_n == 0).sum()),
            "residual_2B_mean": float(
                eligible["HIT_COMPOSITION_prior_pitcher_alr_residual_2B"].mean()
            ),
            "residual_3B_mean": float(
                eligible["HIT_COMPOSITION_prior_pitcher_alr_residual_3B"].mean()
            ),
        }
    )
    return rows


def main() -> int:
    args = _parse_args()
    args.report_root.mkdir(parents=True, exist_ok=True)
    result = json.loads(args.label_result.read_text(encoding="utf-8"))
    expected_sidecar_sha = result["storage"]["sidecar"]["file_sha256"]
    if _sha256(args.label_sidecar) != expected_sidecar_sha:
        raise RuntimeError("label sidecar hash differs from certified source result")
    if _sha256(args.contract) != result["contract"]["sha256"]:
        raise RuntimeError("Stage 2d contract hash differs from certified source result")

    source = pl.read_parquet(args.label_sidecar).filter(
        pl.col("context_label_ready")
    ).select(
        "season",
        "game_date",
        "game_pk",
        "at_bat_index",
        "league_id",
        "level_group",
        "player_id",
        "pitcher_id",
        "batter_side",
        "pitcher_hand",
        "canonical_outcome",
        "context_label_ready",
        "source_system",
        "capability_tier",
    )
    if source.height != result["totals"]["context_label_ready_pa"]:
        raise RuntimeError("J0 input population differs from certified ready-PA total")
    if source.filter(pl.col("season") >= 2025).height:
        raise RuntimeError("J0 input materialization crossed the 2021-2024 boundary")

    keys = ["season", "game_pk", "at_bat_index"]
    materialized = source.with_columns(
        pl.concat_str(
            ["batter_side", "pitcher_hand"], separator="_vs_"
        ).alias("platoon_cell")
    )
    for node in BINARY_CONTEXT_NODES:
        feature = build_prior_pitcher_binary_feature(source, node.name)
        columns = [
            f"{node.name}_eligible",
            f"{node.name}_response",
            f"{node.name}_prior_pitcher_denominator",
            f"{node.name}_prior_context_rate",
            f"{node.name}_prior_pitcher_log_odds_residual",
            f"{node.name}_pitcher_feature_fallback",
        ]
        materialized = materialized.join(
            feature.select(*keys, *columns),
            on=keys,
            how="left",
            validate="1:1",
        )
        print(
            json.dumps(
                {
                    "node": node.name,
                    "rows": feature.height,
                    "eligible_pa": int(feature[f"{node.name}_eligible"].sum()),
                }
            ),
            flush=True,
        )
    composition = build_prior_pitcher_hit_composition_features(source)
    composition_columns = [
        "HIT_COMPOSITION_eligible",
        "HIT_COMPOSITION_response",
        "HIT_COMPOSITION_prior_pitcher_denominator",
        "HIT_COMPOSITION_prior_context_rate_1B",
        "HIT_COMPOSITION_prior_context_rate_2B",
        "HIT_COMPOSITION_prior_context_rate_3B",
        "HIT_COMPOSITION_prior_pitcher_alr_residual_1B",
        "HIT_COMPOSITION_prior_pitcher_alr_residual_2B",
        "HIT_COMPOSITION_prior_pitcher_alr_residual_3B",
        "HIT_COMPOSITION_pitcher_feature_fallback",
    ]
    materialized = materialized.join(
        composition.select(*keys, *composition_columns),
        on=keys,
        how="left",
        validate="1:1",
    )
    if materialized.height != source.height:
        raise RuntimeError("J0 feature joins changed the certified input cohort")
    residual_columns = [
        f"{node.name}_prior_pitcher_log_odds_residual"
        for node in BINARY_CONTEXT_NODES
    ] + [
        "HIT_COMPOSITION_prior_pitcher_alr_residual_1B",
        "HIT_COMPOSITION_prior_pitcher_alr_residual_2B",
        "HIT_COMPOSITION_prior_pitcher_alr_residual_3B",
    ]
    if materialized.select(
        pl.any_horizontal([pl.col(x).is_null() for x in residual_columns]).any()
    ).item():
        raise RuntimeError("J0 pitcher residual surface contains nulls")

    artifact = write_canonical_parquet(
        materialized,
        args.report_root / "tables" / "hitter_v2_stage2d_j0_event_inputs_2021_2024.parquet",
        table_name="hitter_v2_stage2d_j0_event_inputs",
    ).as_record()
    node_coverage = _node_coverage(materialized)
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "gate": "stage2d_J0_chronology_safe_input_materialization",
        "accepted": True,
        "source_seasons": [2021, 2022, 2023, 2024],
        "label_result_sha256": _sha256(args.label_result),
        "label_sidecar_sha256": expected_sidecar_sha,
        "contract_sha256": _sha256(args.contract),
        "chronology_policy": "strictly_before_game_date_same_day_excluded",
        "recency_half_life_seasons": 2.0,
        "input_pa": materialized.height,
        "platoon_cells": (
            materialized.group_by("platoon_cell")
            .len(name="pa")
            .sort("platoon_cell")
            .to_dicts()
        ),
        "node_coverage": node_coverage,
        "storage": {"event_inputs": artifact},
        "forecast_targets_loaded": False,
        "candidate_fit": False,
        "candidate_scored": False,
        "protected_2026_opened": False,
        "next_gate": "freeze_and_review_J0_real_data_fit_execution_package",
    }
    report_path = args.report_root / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "report": str(report_path),
                "sha256": _sha256(report_path),
                "input_pa": materialized.height,
                "artifact": artifact,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
