#!/usr/bin/env python3
"""Decompose the frozen Hitter v2 Stage 2 failure without fitting a candidate.

This is explicitly a post-result diagnostic over already-disclosed 2022-2024
targets.  It cannot select, promote, or score a new candidate and it never
opens the protected confirmation season.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.storage import write_canonical_parquet


FOLDS = ("V2022", "V2023", "V2024")
MODELS = {
    "B0_ONE_YEAR_EB": "b0_one_year_eb_predictions.parquet",
    "B1_MARCEL_345_K1200": "b1_marcel_345_k1200_predictions.parquet",
    "C0_NESTED_EB": "c0_nested_eb_predictions.parquet",
    "C1_HIERARCHICAL_PBP": "c1_hierarchical_pbp_predictions.parquet",
}
COMPARISONS = (
    ("C0_NESTED_EB", "B0_ONE_YEAR_EB"),
    ("C0_NESTED_EB", "B1_MARCEL_345_K1200"),
    ("C1_HIERARCHICAL_PBP", "C0_NESTED_EB"),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--final-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-final-validation"),
    )
    parser.add_argument(
        "--prescore-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-prescore/tables"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-failure-diagnostic"),
    )
    return parser.parse_args()


def _file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _component_deltas(
    target: pl.DataFrame,
    candidate: pl.DataFrame,
    comparator: pl.DataFrame,
    *,
    fold_id: str,
    candidate_id: str,
    comparator_id: str,
) -> list[dict[str, object]]:
    joined = target.join(candidate, on="player_id", how="inner").join(
        comparator, on="player_id", how="inner", suffix="_comparator"
    )
    pa = joined["hitter_talent_pa"].to_numpy().astype(float)
    if not len(pa) or np.any(pa <= 0):
        raise ValueError(f"{fold_id} has no positive-PA diagnostic overlap")
    total_pa = float(pa.sum())
    rows: list[dict[str, object]] = []
    for outcome in HITTER_TALENT_OUTCOMES:
        actual = joined[outcome].to_numpy().astype(float) / pa
        candidate_probability = np.clip(
            joined[f"p_{outcome}"].to_numpy().astype(float), 1e-12, 1.0
        )
        comparator_probability = np.clip(
            joined[f"p_{outcome}_comparator"].to_numpy().astype(float),
            1e-12,
            1.0,
        )
        log_delta = -actual * np.log(candidate_probability) + actual * np.log(
            comparator_probability
        )
        brier_delta = (
            candidate_probability**2
            - comparator_probability**2
            - 2.0 * actual * (candidate_probability - comparator_probability)
        )
        rows.append(
            {
                "fold_id": fold_id,
                "candidate_id": candidate_id,
                "comparator_id": comparator_id,
                "outcome": outcome,
                "evaluation_players": int(len(pa)),
                "evaluation_pa": int(total_pa),
                "pa_weighted_log_loss_delta": float(
                    np.sum(pa * log_delta) / total_pa
                ),
                "player_weighted_log_loss_delta": float(np.mean(log_delta)),
                "pa_weighted_brier_delta": float(
                    np.sum(pa * brier_delta) / total_pa
                ),
                "player_weighted_brier_delta": float(np.mean(brier_delta)),
            }
        )
    return rows


def _summaries(component_rows: pl.DataFrame) -> list[dict[str, object]]:
    totals = (
        component_rows.group_by("fold_id", "candidate_id", "comparator_id")
        .agg(
            pl.col("pa_weighted_log_loss_delta").sum(),
            pl.col("player_weighted_log_loss_delta").sum(),
            pl.col("pa_weighted_brier_delta").sum(),
            pl.col("player_weighted_brier_delta").sum(),
        )
        .sort("fold_id", "candidate_id", "comparator_id")
    )
    result: list[dict[str, object]] = []
    for total in totals.iter_rows(named=True):
        subset = component_rows.filter(
            (pl.col("fold_id") == total["fold_id"])
            & (pl.col("candidate_id") == total["candidate_id"])
            & (pl.col("comparator_id") == total["comparator_id"])
        )
        drivers = (
            subset.with_columns(
                pl.col("pa_weighted_log_loss_delta")
                .abs()
                .alias("absolute_log_delta")
            )
            .sort("absolute_log_delta", descending=True)
            .head(6)
            .select("outcome", "pa_weighted_log_loss_delta")
            .to_dicts()
        )
        result.append({**total, "largest_pa_log_loss_drivers": drivers})
    return result


def main() -> int:
    args = _parse_args()
    frozen_report_path = args.final_root / "report.json"
    frozen_report = json.loads(frozen_report_path.read_text(encoding="utf-8"))
    if frozen_report.get("status") != "pbp_candidates_failed_disclosed_validation":
        raise ValueError("diagnostic requires the frozen failed Stage 2 report")
    if frozen_report.get("protected_2026_opened") is not False:
        raise ValueError("protected confirmation boundary is not closed")

    rows: list[dict[str, object]] = []
    exact_identity: dict[str, object] = {}
    prediction_hashes: dict[str, dict[str, str]] = {}
    for fold_id in FOLDS:
        fold_root = args.final_root / "tables" / fold_id.lower()
        target = pl.read_parquet(
            args.prescore_root / fold_id.lower() / "target_players.parquet"
        )
        predictions = {
            model: pl.read_parquet(fold_root / filename)
            for model, filename in MODELS.items()
        }
        prediction_hashes[fold_id] = {
            model: _file_sha256(fold_root / filename)
            for model, filename in MODELS.items()
        }
        for candidate_id, comparator_id in COMPARISONS:
            rows.extend(
                _component_deltas(
                    target,
                    predictions[candidate_id],
                    predictions[comparator_id],
                    fold_id=fold_id,
                    candidate_id=candidate_id,
                    comparator_id=comparator_id,
                )
            )
        if fold_id == "V2022":
            joined = predictions["C0_NESTED_EB"].join(
                predictions["B0_ONE_YEAR_EB"],
                on="player_id",
                how="inner",
                suffix="_b0",
            )
            maximum = max(
                float(
                    joined.select(
                        (pl.col(f"p_{outcome}") - pl.col(f"p_{outcome}_b0"))
                        .abs()
                        .max()
                    ).item()
                )
                for outcome in HITTER_TALENT_OUTCOMES
            )
            exact_identity = {
                "players": joined.height,
                "maximum_absolute_probability_delta": maximum,
                "exact_probability_identity": maximum == 0.0,
                "interpretation": "With only 2021 history and the frozen defaults, C0 is exactly B0 and cannot strictly beat it in V2022.",
            }

    component_rows = pl.DataFrame(rows)
    artifact = write_canonical_parquet(
        component_rows,
        args.report_root / "tables" / "component_score_deltas.parquet",
        table_name="hitter_v2_stage2_failure_component_score_deltas",
    )
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": "2_post_failure_diagnostic",
        "status": "disclosed_failure_diagnosed_no_new_candidate_scored",
        "post_result_diagnostic": True,
        "candidate_fit": False,
        "new_candidate_scored": False,
        "protected_2026_opened": False,
        "frozen_final_validation_report": {
            "path": str(frozen_report_path),
            "sha256": _file_sha256(frozen_report_path),
        },
        "v2022_c0_b0_identity": exact_identity,
        "component_comparisons": _summaries(component_rows),
        "prediction_hashes": prediction_hashes,
        "component_delta_artifact": artifact.as_record(),
        "interpretation": [
            "C0 is exactly B0 in V2022, then improves proper scores in V2023 and V2024.",
            "C1 degradation is driven by contextual adjustments, especially probability movement among OTHER_OUT, UBB, ROE, and HBP; contact direction was not an input to the scored C1 implementation.",
            "These disclosed results may diagnose a new versioned family but cannot promote it or relax the failed v1 contract after the fact.",
        ],
    }
    args.report_root.mkdir(parents=True, exist_ok=True)
    (args.report_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
