#!/usr/bin/env python3
"""Run target-free Stage 2e synthetic and source-shape certification."""

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

from universal_baseball.hitter_v2_stage2e import (
    Stage2eFitError,
    Stage2eNodeFit,
    certify_grouped_event_binary_equivalence,
    fit_matched_binary_j0r,
    fit_matched_hit_composition_j0r,
)
from universal_baseball.storage import sha256_file


BINARY_RATES = {
    "K": (0.25, 1.00),
    "UBB": (0.10, 0.75),
    "HBP": (0.01, 0.65),
    "HR": (0.04, 0.65),
    "NON_HR_REACH": (0.32, 0.60),
}
BASE_COLUMNS = [
    "season",
    "game_pk",
    "at_bat_index",
    "league_id",
    "level_group",
    "player_id",
    "platoon_cell",
]
RESIDUAL_COLUMNS = [
    *[f"{node}_prior_pitcher_log_odds_residual" for node in BINARY_RATES],
    "HIT_COMPOSITION_prior_pitcher_alr_residual_2B",
    "HIT_COMPOSITION_prior_pitcher_alr_residual_3B",
]
PLATOON_EFFECT = {"L_vs_L": 0.12, "L_vs_R": -0.04, "R_vs_L": 0.07, "R_vs_R": -0.02}
RATE_REGIMES = (0.01, 0.05, 0.25, 0.60)


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
        default=Path("docs/hitter-v2-stage2e-authorization.json"),
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
        default=Path("src/universal_baseball/hitter_v2_stage2e.py"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2e-numerical-certification"),
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


def write_incident(
    path: Path,
    error: Stage2eFitError,
    *,
    phase: str,
    hashes: dict[str, str],
) -> None:
    _atomic_json(
        path,
        {
            "status": "failed_closed",
            "certification_phase": phase,
            "node": error.node,
            "optimizer_phase": error.phase,
            "exception": str(error),
            "trace": error.trace,
            "hashes": hashes,
            "candidate_artifact_published": False,
            "real_outcomes_loaded": False,
            "forecast_targets_loaded": False,
            "protected_2026_opened": False,
        },
    )


def _design_frame(path: Path) -> pl.DataFrame:
    return pl.scan_parquet(path).select(*BASE_COLUMNS, *RESIDUAL_COLUMNS).collect()


def _player_effect(frame: pl.DataFrame) -> np.ndarray:
    return ((frame["player_id"].to_numpy() % 17) - 8).astype(float) * 0.06


def _platoon_effect(frame: pl.DataFrame) -> np.ndarray:
    return np.asarray([PLATOON_EFFECT[str(value)] for value in frame["platoon_cell"]])


def _simulate_binary(
    design: pl.DataFrame,
    node: str,
    *,
    seed: int,
    rate_override: float | None = None,
    eligibility_rate_override: float | None = None,
) -> pl.DataFrame:
    rate, eligibility_rate = BINARY_RATES[node]
    if rate_override is not None:
        rate = rate_override
    if eligibility_rate_override is not None:
        eligibility_rate = eligibility_rate_override
    rng = np.random.default_rng(seed)
    eligible = rng.random(design.height) < eligibility_rate
    residual = design[f"{node}_prior_pitcher_log_odds_residual"].to_numpy()
    intercept = np.log(rate / (1.0 - rate))
    eta = intercept + _player_effect(design) + _platoon_effect(design) + 0.8 * residual
    probability = 1.0 / (1.0 + np.exp(-np.clip(eta, -35.0, 35.0)))
    response = (rng.random(design.height) < probability).astype(np.int8)
    return design.select(
        *BASE_COLUMNS, f"{node}_prior_pitcher_log_odds_residual"
    ).with_columns(
        pl.Series(f"{node}_eligible", eligible),
        pl.Series(f"{node}_response", response).cast(pl.Int8),
    )


def _evidence_recovery(
    events: pl.DataFrame,
    fit: Stage2eNodeFit,
    node: str,
) -> dict[str, object]:
    estimates = fit.contextual_batter_effects.join(
        events.filter(pl.col(f"{node}_eligible"))
        .group_by("player_id")
        .len(name="eligible_events"),
        on="player_id",
        how="left",
    ).with_columns(
        (((pl.col("player_id") % 17) - 8).cast(pl.Float64) * 0.06).alias(
            "true_batter_effect"
        )
    )

    def summarize(frame: pl.DataFrame) -> dict[str, object]:
        correlation = frame.select(
            pl.corr("contextual_batter_effect", "true_batter_effect")
        ).item()
        return {
            "players": frame.height,
            "correlation": None if correlation is None else float(correlation),
            "rmse": float(
                frame.select(
                    (
                        (
                            pl.col("contextual_batter_effect")
                            - pl.col("true_batter_effect")
                        )
                        ** 2
                    )
                    .mean()
                    .sqrt()
                ).item()
            ),
        }

    low = summarize(estimates.filter(pl.col("eligible_events") <= 25))
    high = summarize(estimates.filter(pl.col("eligible_events") >= 200))
    passed = (
        low["players"] >= 20
        and high["players"] >= 20
        and low["correlation"] is not None
        and high["correlation"] is not None
        and float(low["correlation"]) > 0.0
        and float(high["correlation"]) >= 0.50
        and float(high["rmse"]) < float(low["rmse"])
    )
    return {"low_evidence": low, "high_evidence": high, "passed": passed}


def _simulate_composition(design: pl.DataFrame, *, seed: int) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    eligible = rng.random(design.height) < 0.18
    r2 = design["HIT_COMPOSITION_prior_pitcher_alr_residual_2B"].to_numpy()
    r3 = design["HIT_COMPOSITION_prior_pitcher_alr_residual_3B"].to_numpy()
    player = _player_effect(design)
    platoon = _platoon_effect(design)
    logits = np.column_stack(
        (
            np.zeros(design.height),
            -1.0 + 0.35 * player + platoon + 0.8 * r2,
            -2.6 + 0.20 * player - 0.5 * platoon + 0.8 * r3,
        )
    )
    shifted = logits - logits.max(axis=1, keepdims=True)
    probability = np.exp(shifted)
    probability /= probability.sum(axis=1, keepdims=True)
    draw = rng.random(design.height)
    category = np.where(
        draw < probability[:, 0],
        "1B",
        np.where(draw < probability[:, 0] + probability[:, 1], "2B", "3B"),
    )
    return design.select(
        *BASE_COLUMNS,
        "HIT_COMPOSITION_prior_pitcher_alr_residual_2B",
        "HIT_COMPOSITION_prior_pitcher_alr_residual_3B",
    ).with_columns(
        pl.Series("HIT_COMPOSITION_eligible", eligible),
        pl.Series("HIT_COMPOSITION_response", category),
    )


def _frame_hash(frame: pl.DataFrame) -> str:
    material = frame.sort(frame.columns[0]).write_json()
    return sha256(material.encode("utf-8")).hexdigest()


def main() -> int:
    args = _parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    authorization = json.loads(args.authorization.read_text(encoding="utf-8"))
    hashes = {
        "contract": sha256_file(args.contract),
        "authorization": sha256_file(args.authorization),
        "event_input": sha256_file(args.event_input),
        "implementation": sha256_file(args.implementation),
    }
    if authorization["contract_sha256"] != hashes["contract"]:
        raise ValueError("Stage 2e authorization contract hash mismatch")
    if authorization["current_gate"]["numerical_certification_authorized"] is not True:
        raise ValueError("Stage 2e numerical certification is not authorized")
    if authorization["current_gate"]["real_data_fit_open"] is not False:
        raise ValueError("Stage 2e certification cannot run with real fit open")
    if (
        contract["numerical_certification_before_real_fit"]["real_outcomes_loaded"]
        is not False
    ):
        raise ValueError("Stage 2e certification contract is not target-free")

    started = perf_counter()
    design = _design_frame(args.event_input)
    if design.height != int(contract["source_and_chronology"]["certified_input_pa"]):
        raise ValueError("Stage 2e source-shape row count differs from contract")
    if any(
        "response" in column or column == "canonical_outcome"
        for column in design.columns
    ):
        raise ValueError(
            "real response column entered Stage 2e numerical certification"
        )
    platoon_cells = sorted(str(value) for value in design["platoon_cell"].unique())
    if platoon_cells != sorted(PLATOON_EFFECT):
        raise ValueError("Stage 2e source shape lacks a frozen platoon cell")

    node_results: list[dict[str, object]] = []
    evidence_recovery: dict[str, object] | None = None
    try:
        for index, node in enumerate(BINARY_RATES):
            events = _simulate_binary(design, node, seed=20260824 + index)
            node_started = perf_counter()
            fit = fit_matched_binary_j0r(events, node)
            if node == "K":
                evidence_recovery = _evidence_recovery(events, fit, node)
            pitcher = fit.fixed_effects.filter(
                pl.col("effect_type") == "pitcher_coefficient"
            )["contextual_value"].item()
            node_results.append(
                {
                    "node": node,
                    "elapsed_seconds": perf_counter() - node_started,
                    "simulated_response_rate": float(
                        events.filter(pl.col(f"{node}_eligible"))[
                            f"{node}_response"
                        ].mean()
                    ),
                    "fitted_pitcher_coefficient": float(pitcher),
                    "diagnostics": fit.diagnostics,
                }
            )
        composition = _simulate_composition(design, seed=20260825)
        composition_started = perf_counter()
        composition_fit = fit_matched_hit_composition_j0r(composition)
        node_results.append(
            {
                "node": "HIT_COMPOSITION",
                "elapsed_seconds": perf_counter() - composition_started,
                "diagnostics": composition_fit.diagnostics,
            }
        )
    except Stage2eFitError as error:
        write_incident(
            args.report_root / "incident.json",
            error,
            phase="source_shape_synthetic_response_fit",
            hashes=hashes,
        )
        raise

    subset = _simulate_binary(design.head(50_000), "K", seed=20260824)
    first = fit_matched_binary_j0r(subset, "K")
    second = fit_matched_binary_j0r(subset, "K")
    deterministic = _frame_hash(first.context_increments) == _frame_hash(
        second.context_increments
    )
    equivalence = certify_grouped_event_binary_equivalence(subset, "K")
    rate_regime_results: list[dict[str, object]] = []
    for index, rate in enumerate(RATE_REGIMES):
        regime_events = _simulate_binary(
            design.head(50_000),
            "K",
            seed=20260900 + index,
            rate_override=rate,
            eligibility_rate_override=1.0,
        )
        regime_fit = fit_matched_binary_j0r(regime_events, "K")
        regime_pitcher = regime_fit.fixed_effects.filter(
            pl.col("effect_type") == "pitcher_coefficient"
        )["contextual_value"].item()
        rate_regime_results.append(
            {
                "requested_rate": rate,
                "realized_rate": float(regime_events["K_response"].mean()),
                "fitted_pitcher_coefficient": float(regime_pitcher),
                "converged": all(
                    regime_fit.diagnostics[phase]["converged"] is True
                    for phase in ("uncontextual", "contextual")
                ),
            }
        )
    try:
        fit_matched_binary_j0r(
            subset.head(2_000), "K", max_iterations=1, tolerance=1e-20
        )
    except Stage2eFitError as intentional:
        intentional_failure = {
            "node": intentional.node,
            "phase": intentional.phase,
            "trace_rows": len(intentional.trace),
            "candidate_artifact_published": False,
        }
    else:
        raise ValueError("Stage 2e intentional nonconvergence did not fail")

    all_converged = all(
        result["diagnostics"][phase]["converged"] is True
        for result in node_results
        for phase in ("uncontextual", "contextual")
    )
    coefficient_recovery = all(
        0.5 <= float(result["fitted_pitcher_coefficient"]) <= 1.1
        for result in node_results
        if result["node"] != "HIT_COMPOSITION"
    )
    equivalence_pass = all(
        equivalence[key] <= threshold
        for key, threshold in {
            "intercept_max_abs_delta": 1e-10,
            "lsl_max_abs_delta": 1e-10,
            "batter_max_abs_delta": 1e-10,
            "objective_abs_delta": 1e-7,
        }.items()
    )
    rate_regime_pass = all(
        result["converged"] is True
        and 0.4 <= float(result["fitted_pitcher_coefficient"]) <= 1.2
        for result in rate_regime_results
    )
    evidence_recovery_pass = bool(
        evidence_recovery is not None and evidence_recovery["passed"] is True
    )
    accepted = (
        all_converged
        and coefficient_recovery
        and deterministic
        and equivalence_pass
        and rate_regime_pass
        and evidence_recovery_pass
    )
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": "2e_numerical_certification",
        "accepted": accepted,
        "source_shape_rows": design.height,
        "source_shape_columns": design.columns,
        "real_outcomes_loaded": False,
        "forecast_targets_loaded": False,
        "protected_2026_opened": False,
        "platoon_cells": platoon_cells,
        "hashes": hashes,
        "node_results": node_results,
        "deterministic_repeat_hash_equality": deterministic,
        "grouped_event_equivalence": equivalence,
        "grouped_event_equivalence_pass": equivalence_pass,
        "intentional_failure": intentional_failure,
        "all_nodes_converged": all_converged,
        "pitcher_coefficient_recovery_pass": coefficient_recovery,
        "event_rate_regime_results": rate_regime_results,
        "event_rate_regime_recovery_pass": rate_regime_pass,
        "player_evidence_recovery": evidence_recovery,
        "player_evidence_recovery_pass": evidence_recovery_pass,
        "elapsed_seconds": perf_counter() - started,
        "candidate_fit": False,
        "candidate_scored": False,
        "real_data_fit_authorized": False,
        "next_gate": "review_certification_then_open_real_data_fold_fit_only",
    }
    _atomic_json(args.report_root / "report.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
