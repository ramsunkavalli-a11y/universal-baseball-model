#!/usr/bin/env python3
"""Execute the authorized, frozen Stage 2d J0 fit without scoring it."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_v2_stage2d import (
    BINARY_CONTEXT_NODES,
    apply_j0_context_increment,
    fit_matched_binary_context_models,
    fit_matched_hit_composition_context_models,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


EXPECTED_CONTRACT_SHA256 = (
    "5d0ef4898b3a59103d5e7138efa18aca63eea8672df5d1dfbdc36b063af38806"
)
EXPECTED_MODULE_SHA256 = (
    "fb87a41d41fb8fe33406935efb73546f49a0196bf075ffd06050aae7a3b554a1"
)
KEY_COLUMNS = ["season", "game_pk", "at_bat_index"]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("docs/hitter-v2-stage2d-j0-fit-execution-contract.json"),
    )
    parser.add_argument(
        "--authorization",
        type=Path,
        default=Path("docs/hitter-v2-stage2d-j0-fit-authorization.json"),
    )
    parser.add_argument(
        "--event-input",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage2d-inputs/tables/"
            "hitter_v2_stage2d_j0_event_inputs_2021_2024.parquet"
        ),
    )
    parser.add_argument(
        "--implementation",
        type=Path,
        default=Path("src/universal_baseball/hitter_v2_stage2d.py"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2d-j0-fit"),
    )
    return parser.parse_args()


def verify_execution_boundary(
    contract: dict[str, object],
    authorization: dict[str, object],
    *,
    contract_sha256: str,
    implementation_sha256: str,
    event_input_sha256: str,
) -> None:
    """Fail closed unless fit-only authorization matches every frozen artifact."""

    if contract_sha256 != EXPECTED_CONTRACT_SHA256:
        raise ValueError("J0 execution contract hash changed after freeze")
    if implementation_sha256 != EXPECTED_MODULE_SHA256:
        raise ValueError("J0 implementation hash changed after freeze")
    if contract.get("status") != "frozen_before_real_data_fit_or_score":
        raise ValueError("J0 execution contract is not in its frozen state")
    if contract.get("candidate_scoring_authorized") is not False:
        raise ValueError("J0 fit runner cannot execute under scoring authorization")
    if authorization.get("J0_real_data_fit_authorized") is not True:
        raise ValueError("J0 real-data fit has not been authorized")
    closed = (
        "candidate_scoring_authorized",
        "post_fit_tuning_authorized",
        "J1_authorized",
        "protected_2026_access_authorized",
        "tracking_authorized",
        "stage3_authorized",
        "full_war_authorized",
    )
    if any(authorization.get(key) is not False for key in closed):
        raise ValueError("J0 authorization improperly opens a later scientific gate")
    if authorization.get("fit_execution_contract_sha256") != contract_sha256:
        raise ValueError("J0 authorization points to a different execution contract")
    if authorization.get("event_input_sha256") != event_input_sha256:
        raise ValueError("J0 authorization points to a different event input")
    provenance = contract.get("provenance", {})
    if provenance.get("event_input_sha256") != event_input_sha256:
        raise ValueError("J0 event input hash differs from frozen provenance")
    if provenance.get("implementation_sha256") != implementation_sha256:
        raise ValueError("J0 module hash differs from frozen provenance")


def _key_sha256(events: pl.DataFrame) -> str:
    row_hashes = events.select(KEY_COLUMNS).hash_rows(
        seed=0, seed_1=1, seed_2=2, seed_3=3
    )
    ordered = np.sort(row_hashes.to_numpy())
    return sha256(ordered.tobytes()).hexdigest()


def _binary_outputs(node_name: str, fit: object) -> tuple[pl.DataFrame, ...]:
    increments = fit.context_increments.select(
        "player_id",
        pl.lit(node_name).alias("node"),
        pl.lit("LOGIT").alias("contrast"),
        pl.col("context_increment").alias("value"),
    )
    effects = fit.contextual_batter_effects.join(
        fit.uncontextual_batter_effects,
        on="player_id",
        how="inner",
        validate="1:1",
    ).select(
        "player_id",
        pl.lit(node_name).alias("node"),
        pl.lit("LOGIT").alias("contrast"),
        pl.col("contextual_batter_effect").alias("contextual_value"),
        pl.col("uncontextual_batter_effect").alias("uncontextual_value"),
    )
    fixed = fit.fixed_effects.with_columns(pl.lit(node_name).alias("node")).select(
        "node", "effect_type", "effect_key", "contextual_value", "uncontextual_value"
    )
    return increments, effects, fixed


def _composition_outputs(fit: object) -> tuple[pl.DataFrame, ...]:
    increments = pl.concat(
        [
            fit.context_increments.select(
                "player_id",
                pl.lit("HIT_COMPOSITION").alias("node"),
                pl.lit(contrast).alias("contrast"),
                pl.col(f"context_increment_{contrast}").alias("value"),
            )
            for contrast in ("2B", "3B")
        ]
    )
    joined = fit.contextual_batter_effects.join(
        fit.uncontextual_batter_effects,
        on="player_id",
        how="inner",
        validate="1:1",
    )
    effects = pl.concat(
        [
            joined.select(
                "player_id",
                pl.lit("HIT_COMPOSITION").alias("node"),
                pl.lit(contrast).alias("contrast"),
                pl.col(f"contextual_batter_effect_{contrast}").alias(
                    "contextual_value"
                ),
                pl.col(f"uncontextual_batter_effect_{contrast}").alias(
                    "uncontextual_value"
                ),
            )
            for contrast in ("2B", "3B")
        ]
    )
    fixed = fit.fixed_effects.with_columns(
        pl.lit("HIT_COMPOSITION").alias("node")
    ).select(
        "node", "effect_type", "effect_key", "contextual_value", "uncontextual_value"
    )
    return increments, effects, fixed


def main() -> int:
    args = _parse_args()
    contract_sha = sha256_file(args.contract)
    implementation_sha = sha256_file(args.implementation)
    input_sha = sha256_file(args.event_input)
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    authorization = json.loads(args.authorization.read_text(encoding="utf-8"))
    verify_execution_boundary(
        contract,
        authorization,
        contract_sha256=contract_sha,
        implementation_sha256=implementation_sha,
        event_input_sha256=input_sha,
    )

    events = pl.read_parquet(args.event_input)
    expected_rows = int(contract["cohort"]["rows"])
    if events.height != expected_rows:
        raise ValueError("J0 event input row count changed after freeze")
    if events.filter(pl.col("season") >= 2025).height:
        raise ValueError("J0 fit input crossed the protected season boundary")
    if events.select(KEY_COLUMNS).n_unique() != events.height:
        raise ValueError("J0 fit input is not unique at the frozen PA key")

    increments: list[pl.DataFrame] = []
    effects: list[pl.DataFrame] = []
    fixed_effects: list[pl.DataFrame] = []
    metrics: list[dict[str, object]] = []
    for node in BINARY_CONTEXT_NODES:
        fit = fit_matched_binary_context_models(events, node.name)
        node_increments, node_effects, node_fixed = _binary_outputs(node.name, fit)
        increments.append(node_increments)
        effects.append(node_effects)
        fixed_effects.append(node_fixed)
        metrics.append(fit.metrics)

    composition_fit = fit_matched_hit_composition_context_models(events)
    composition_outputs = _composition_outputs(composition_fit)
    increments.append(composition_outputs[0])
    effects.append(composition_outputs[1])
    fixed_effects.append(composition_outputs[2])
    metrics.append(composition_fit.metrics)

    increment_frame = pl.concat(increments).sort("node", "contrast", "player_id")
    effect_frame = pl.concat(effects).sort("node", "contrast", "player_id")
    fixed_frame = pl.concat(fixed_effects).sort("node", "effect_type", "effect_key")
    if increment_frame.filter(~pl.col("value").is_finite()).height:
        raise ValueError("J0 fit produced a nonfinite context increment")
    artifacts = {
        "context_increments": write_canonical_parquet(
            increment_frame,
            args.report_root / "tables" / "j0_context_increments.parquet",
            table_name="hitter_v2_stage2d_j0_context_increments",
        ).as_record(),
        "batter_effects": write_canonical_parquet(
            effect_frame,
            args.report_root / "tables" / "j0_batter_effects.parquet",
            table_name="hitter_v2_stage2d_j0_batter_effects",
        ).as_record(),
        "fixed_effects": write_canonical_parquet(
            fixed_frame,
            args.report_root / "tables" / "j0_fixed_effects.parquet",
            table_name="hitter_v2_stage2d_j0_fixed_effects",
        ).as_record(),
    }
    base = {
        "K": 0.25,
        "UBB": 0.08,
        "HBP": 0.01,
        "HR": 0.04,
        "3B": 0.005,
        "2B": 0.045,
        "1B": 0.15,
        "ROE": 0.02,
        "FC_REACH": 0.01,
        "SF": 0.02,
        "MULTI_OUT": 0.03,
        "OTHER_OUT": 0.34,
    }
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "gate": "stage2d_J0_real_data_fit",
        "accepted": True,
        "candidate_fit": True,
        "candidate_scored": False,
        "forecast_targets_loaded": False,
        "protected_2026_opened": False,
        "contract_sha256": contract_sha,
        "authorization_sha256": sha256_file(args.authorization),
        "implementation_sha256": implementation_sha,
        "event_input_sha256": input_sha,
        "event_key_sha256": _key_sha256(events),
        "event_count": events.height,
        "event_key_unique_count": events.height,
        "matched_cohort_invariant": all(
            bool(record["identical_event_rows"]) for record in metrics
        ),
        "exact_empty_increment_B1_fallback": (
            apply_j0_context_increment(base, None) == base
            and apply_j0_context_increment(base, {}) == base
        ),
        "node_metrics": metrics,
        "artifacts": artifacts,
        "next_gate": "audit_fit_then_freeze_scoring_package_before_any_score",
    }
    args.report_root.mkdir(parents=True, exist_ok=True)
    report_path = args.report_root / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
