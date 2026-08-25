#!/usr/bin/env python3
"""Fit authorized Stage 2e J0R folds without loading evaluation targets."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import numpy as np
import polars as pl

from universal_baseball.hitter_v2_stage2d import BINARY_CONTEXT_NODES
from universal_baseball.hitter_v2_stage2e import (
    Stage2eFitError,
    Stage2eNodeFit,
    apply_j0r_to_predictions,
    fit_matched_binary_j0r,
    fit_matched_hit_composition_j0r,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


EXPECTED = {
    "contract": "a475bc153b1e062976cb796a4983c6244d934b4755218475e961c4ae6e5f7026",
    "certification": "5544cb386623610b0104c0060b6b15770b9ebc99febc30d68837dfd8facd248d",
    "implementation": "0beb260b149e74a226dfe841b79b3b1e4ef897d801bbf56db332ee99847999ed",
    "event_input": "a6cd82a5ac8c9382dc474a968bad6b5e6b48599b7ccfc1c6cfbe7a9a1cba515d",
}
FOLDS = {
    "V2022": {
        "cutoff": 2021,
        "base_sha256": "1d751597de8c6f6df5fc17f22762d70135eb507ce209554074d141f88a133872",
    },
    "V2023": {
        "cutoff": 2022,
        "base_sha256": "0913b053d66d1a43bcd4e2f3d8bd54880dd01411cf9aba0dd6cbf10e770980a8",
    },
    "V2024": {
        "cutoff": 2023,
        "base_sha256": "096872097d30b72e59f5cc0c0c5980e2ff3e78d86eefc4ebe3f6175541eed476",
    },
}
KEY_COLUMNS = ["season", "game_pk", "at_bat_index"]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("docs/hitter-v2-stage2e-development-contract.json"),
    )
    parser.add_argument(
        "--authorization",
        type=Path,
        default=Path("docs/hitter-v2-stage2e-fit-authorization.json"),
    )
    parser.add_argument(
        "--certification",
        type=Path,
        default=Path("docs/hitter-v2-stage2e-certification-result.json"),
    )
    parser.add_argument(
        "--implementation",
        type=Path,
        default=Path("src/universal_baseball/hitter_v2_stage2e.py"),
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
        "--base-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-final-validation/tables"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2e-j0r-fit"),
    )
    return parser.parse_args()


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def verify_fit_boundary(
    authorization: dict[str, object],
    certification: dict[str, object],
    hashes: dict[str, str],
) -> None:
    """Fail closed unless certification passed and every later gate is closed."""

    for key, expected in EXPECTED.items():
        if hashes[key] != expected:
            raise ValueError(f"Stage 2e frozen {key} hash changed")
    gate = authorization["current_gate"]
    if gate["chronology_safe_v2022_v2023_v2024_fit_open"] is not True:
        raise ValueError("Stage 2e chronology-safe fit gate is not open")
    if gate["forecast_targets_open"] is not False:
        raise ValueError("Stage 2e fit runner cannot load targets")
    if gate["candidate_scoring_open"] is not False:
        raise ValueError("Stage 2e fit runner cannot score")
    if certification["accepted"] is not True:
        raise ValueError("Stage 2e numerical certification did not pass")
    if certification["real_outcomes_loaded"] is not False:
        raise ValueError("Stage 2e certification boundary was violated")
    if authorization["certification_result_sha256"] != hashes["certification"]:
        raise ValueError("Stage 2e fit authorization points to another result")
    if any(authorization["immutable_boundaries"].values()):
        raise ValueError("Stage 2e fit authorization opened a later gate")


def _key_sha256(events: pl.DataFrame) -> str:
    row_hashes = events.select(KEY_COLUMNS).hash_rows(
        seed=0, seed_1=1, seed_2=2, seed_3=3
    )
    return sha256(np.sort(row_hashes.to_numpy()).tobytes()).hexdigest()


def _long_outputs(
    node: str, fit: Stage2eNodeFit
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    if node != "HIT_COMPOSITION":
        increments = fit.context_increments.select(
            "player_id",
            pl.lit(node).alias("node"),
            pl.lit("LOGIT").alias("contrast"),
            pl.col("context_increment").alias("value"),
        )
        effects = fit.contextual_batter_effects.join(
            fit.uncontextual_batter_effects,
            on="player_id",
            validate="1:1",
        ).select(
            "player_id",
            pl.lit(node).alias("node"),
            pl.lit("LOGIT").alias("contrast"),
            pl.col("contextual_batter_effect").alias("contextual_value"),
            pl.col("uncontextual_batter_effect").alias("uncontextual_value"),
        )
    else:
        increments = pl.concat(
            [
                fit.context_increments.select(
                    "player_id",
                    pl.lit(node).alias("node"),
                    pl.lit(contrast).alias("contrast"),
                    pl.col(f"context_increment_{contrast}").alias("value"),
                )
                for contrast in ("2B", "3B")
            ]
        )
        joined = fit.contextual_batter_effects.join(
            fit.uncontextual_batter_effects,
            on="player_id",
            validate="1:1",
        )
        effects = pl.concat(
            [
                joined.select(
                    "player_id",
                    pl.lit(node).alias("node"),
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
    fixed = fit.fixed_effects.with_columns(pl.lit(node).alias("node")).select(
        "node", "effect_type", "effect_key", "contextual_value", "uncontextual_value"
    )
    return increments, effects, fixed


def _fit_fold(events: pl.DataFrame) -> dict[str, Stage2eNodeFit]:
    fits = {
        node.name: fit_matched_binary_j0r(events, node.name)
        for node in BINARY_CONTEXT_NODES
    }
    fits["HIT_COMPOSITION"] = fit_matched_hit_composition_j0r(events)
    return fits


def _artifact(frame: pl.DataFrame, path: Path, *, table_name: str) -> dict[str, object]:
    return write_canonical_parquet(frame, path, table_name=table_name).as_record()


def main() -> int:
    args = _parse_args()
    hashes = {
        "contract": sha256_file(args.contract),
        "authorization": sha256_file(args.authorization),
        "certification": sha256_file(args.certification),
        "implementation": sha256_file(args.implementation),
        "event_input": sha256_file(args.event_input),
    }
    authorization = json.loads(args.authorization.read_text(encoding="utf-8"))
    certification = json.loads(args.certification.read_text(encoding="utf-8"))
    verify_fit_boundary(authorization, certification, hashes)
    events = pl.read_parquet(args.event_input)
    if events.select(KEY_COLUMNS).n_unique() != events.height:
        raise ValueError("Stage 2e event input is not unique at PA grain")
    if events.filter(pl.col("season") >= 2025).height:
        raise ValueError("Stage 2e fit input crossed the protected boundary")

    started = perf_counter()
    folds: list[dict[str, object]] = []
    try:
        for fold_id, specification in FOLDS.items():
            fold_started = perf_counter()
            cutoff = int(specification["cutoff"])
            training = events.filter(pl.col("season") <= cutoff)
            if int(training["season"].max()) != cutoff:
                raise ValueError(f"{fold_id} lacks its cutoff season")
            base_path = (
                args.base_root
                / fold_id.lower()
                / "b1_marcel_345_k1200_predictions.parquet"
            )
            if sha256_file(base_path) != specification["base_sha256"]:
                raise ValueError(f"{fold_id} frozen Marcel base hash changed")
            base = pl.read_parquet(base_path)
            if base["predictor_cutoff_season"].unique().to_list() != [cutoff]:
                raise ValueError(f"{fold_id} base has another chronology cutoff")
            fits = _fit_fold(training)
            predictions = apply_j0r_to_predictions(base, fits)
            if predictions.height != base.height:
                raise ValueError(f"{fold_id} changed forecast membership")
            if predictions.select("player_id").n_unique() != predictions.height:
                raise ValueError(f"{fold_id} prediction grain is not unique")
            probability_columns = [
                column for column in predictions.columns if column.startswith("p_")
            ]
            simplex_delta = float(
                predictions.select(
                    pl.sum_horizontal(*probability_columns).sub(1.0).abs().max()
                ).item()
            )
            if simplex_delta > 1e-12:
                raise ValueError(f"{fold_id} probabilities left the simplex")

            increment_frames: list[pl.DataFrame] = []
            effect_frames: list[pl.DataFrame] = []
            fixed_frames: list[pl.DataFrame] = []
            for node, fit in fits.items():
                increment, effect, fixed = _long_outputs(node, fit)
                increment_frames.append(increment)
                effect_frames.append(effect)
                fixed_frames.append(fixed)
            table_root = args.report_root / "tables" / fold_id.lower()
            artifacts = {
                "predictions": _artifact(
                    predictions.sort("player_id"),
                    table_root / "j0r_fixed_information_shrinkage_predictions.parquet",
                    table_name=f"hitter_v2_stage2e_{fold_id.lower()}_predictions",
                ),
                "context_increments": _artifact(
                    pl.concat(increment_frames).sort("node", "contrast", "player_id"),
                    table_root / "context_increments.parquet",
                    table_name=f"hitter_v2_stage2e_{fold_id.lower()}_context_increments",
                ),
                "batter_effects": _artifact(
                    pl.concat(effect_frames).sort("node", "contrast", "player_id"),
                    table_root / "batter_effects.parquet",
                    table_name=f"hitter_v2_stage2e_{fold_id.lower()}_batter_effects",
                ),
                "fixed_effects": _artifact(
                    pl.concat(fixed_frames).sort("node", "effect_type", "effect_key"),
                    table_root / "fixed_effects.parquet",
                    table_name=f"hitter_v2_stage2e_{fold_id.lower()}_fixed_effects",
                ),
            }
            folds.append(
                {
                    "fold_id": fold_id,
                    "predictor_cutoff_season": cutoff,
                    "training_rows": training.height,
                    "training_key_sha256": _key_sha256(training),
                    "base_prediction_sha256": specification["base_sha256"],
                    "forecast_players": predictions.height,
                    "simplex_max_abs_delta": simplex_delta,
                    "node_diagnostics": {
                        node: fit.diagnostics for node, fit in fits.items()
                    },
                    "artifacts": artifacts,
                    "elapsed_seconds": perf_counter() - fold_started,
                }
            )
    except Stage2eFitError as error:
        _atomic_json(
            args.report_root / "incident.json",
            {
                "status": "failed_closed",
                "node": error.node,
                "phase": error.phase,
                "exception": str(error),
                "trace": error.trace,
                "completed_folds": folds,
                "candidate_scored": False,
                "forecast_targets_loaded": False,
                "protected_2026_opened": False,
            },
        )
        raise

    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": "2e_J0R_chronology_safe_fit",
        "accepted": True,
        "candidate_fit": True,
        "candidate_scored": False,
        "forecast_targets_loaded": False,
        "protected_2026_opened": False,
        "hashes": hashes,
        "event_rows": events.height,
        "folds": folds,
        "elapsed_seconds": perf_counter() - started,
        "next_gate": "freeze_exact_scorer_and_fit_hashes_before_loading_targets",
    }
    _atomic_json(args.report_root / "report.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
