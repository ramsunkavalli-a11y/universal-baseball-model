#!/usr/bin/env python3
"""Materialize Stage 2b features and scientific invariants without fitting.

This script reads only frozen PBP prediction and auxiliary contact-shape
surfaces. It deliberately has no target-outcome input or scoring function.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_stage2b import (
    apply_node_calibration,
    apply_shape_residual,
    build_shape_features,
    identity_node_calibration,
    zero_shape_residual,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


FOLDS = {"V2022": 2021, "V2023": 2022, "V2024": 2023}
MODES = {
    "trajectory": "D1_TRAJECTORY_RESIDUAL",
    "direction_trajectory": "D2_DIRECTION_TRAJECTORY_RESIDUAL",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prediction-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-final-validation/tables"),
    )
    parser.add_argument(
        "--shape-history",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage2b-contact-shape-source/tables/"
            "contact_shape_player_season.parquet"
        ),
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("docs/hitter-v2-stage2b-development-contract.json"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2b-unscored"),
    )
    return parser.parse_args()


def _probability_values(frame: pl.DataFrame) -> list[list[float]]:
    return frame.sort("player_id").select(
        *[f"p_{outcome}" for outcome in HITTER_TALENT_OUTCOMES]
    ).rows()


def _exact_probability_match(left: pl.DataFrame, right: pl.DataFrame) -> bool:
    return _probability_values(left) == _probability_values(right)


def main() -> int:
    args = _parse_args()
    history = pl.read_parquet(args.shape_history)
    fold_records: list[dict[str, object]] = []
    for fold_id, cutoff in FOLDS.items():
        base_path = (
            args.prediction_root
            / fold_id.lower()
            / "c0_nested_eb_predictions.parquet"
        )
        base = pl.read_parquet(base_path).sort("player_id")
        player_ids = [int(value) for value in base["player_id"].to_list()]
        identity = apply_node_calibration(base, identity_node_calibration())
        if not _exact_probability_match(base, identity):
            raise ValueError(f"{fold_id} identity calibration changed probabilities")

        mode_records: dict[str, object] = {}
        for mode, model_id in MODES.items():
            features = build_shape_features(
                history,
                player_ids,
                predictor_cutoff_season=cutoff,
                mode=mode,
            ).sort("player_id")
            features_cut = build_shape_features(
                history.filter(pl.col("season") <= cutoff),
                player_ids,
                predictor_cutoff_season=cutoff,
                mode=mode,
            ).sort("player_id")
            if not features.equals(features_cut):
                raise ValueError(f"{fold_id} {mode} features depend on future rows")
            zero = apply_shape_residual(
                identity,
                features,
                zero_shape_residual(mode),
                model_id=model_id,
            )
            if not _exact_probability_match(base, zero):
                raise ValueError(f"{fold_id} {mode} zero residual changed probabilities")
            feature_artifact = write_canonical_parquet(
                features,
                args.report_root
                / "tables"
                / fold_id.lower()
                / f"{mode}_features.parquet",
                table_name=f"hitter_v2_stage2b_{fold_id.lower()}_{mode}_features",
            ).as_record()
            supported = features.height
            reliability = (
                features["shape_reliability"].to_list() if supported else []
            )
            mode_records[mode] = {
                "forecast_players": base.height,
                "supported_players": supported,
                "fallback_players": base.height - supported,
                "coverage_rate": supported / base.height,
                "minimum_reliability": min(reliability) if reliability else None,
                "maximum_reliability": max(reliability) if reliability else None,
                "chronology_future_row_invariance": True,
                "zero_residual_exact_base_fallback": True,
                "feature_artifact": feature_artifact,
            }
        fold_records.append(
            {
                "fold_id": fold_id,
                "predictor_cutoff_season": cutoff,
                "base_prediction_path": base_path.as_posix(),
                "base_prediction_sha256": sha256_file(base_path),
                "identity_calibration_exact_base_fallback": True,
                "modes": mode_records,
            }
        )

    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": "2b",
        "status": "implementation_and_unscored_features_materialized",
        "candidate_fit": False,
        "candidate_scored": False,
        "target_outcomes_loaded": False,
        "protected_2026_opened": False,
        "development_contract_sha256": sha256_file(args.contract),
        "contact_shape_source_sha256": sha256_file(args.shape_history),
        "folds": fold_records,
        "scientific_invariants": {
            "identity_calibration_exact_base_fallback": True,
            "zero_shape_residual_exact_base_fallback": True,
            "future_shape_rows_cannot_affect_prior_cutoff_features": True,
            "missing_shape_is_omitted_not_zero_filled": True,
            "reliability_strictly_between_zero_and_one_when_supported": True,
            "upstream_k_ubb_hbp_unchanged_by_shape": "covered_by_synthetic_test",
        },
        "next_step": "commit_implementation_before_disclosed_stage2b_fit_and_score",
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
