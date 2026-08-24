#!/usr/bin/env python3
"""Materialize Stage 2c PBP features and zero-increment invariants only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_stage2c import (
    E1_MODEL_ID,
    E2_MODEL_ID,
    E3_MODEL_ID,
    FEATURES,
    GROUND_MODE,
    HR_MODE,
    XBH_MODE,
    apply_stage2c_residual,
    build_stage2c_features,
    zero_stage2c_fit,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


FOLDS = {"V2022": 2021, "V2023": 2022, "V2024": 2023}
MODES = {
    HR_MODE: E1_MODEL_ID,
    XBH_MODE: E2_MODEL_ID,
    GROUND_MODE: E3_MODEL_ID,
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
        default=Path("docs/hitter-v2-stage2c-development-contract.json"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2c-unscored"),
    )
    return parser.parse_args()


def _probabilities(frame: pl.DataFrame) -> list[list[float]]:
    return frame.sort("player_id").select(
        *[f"p_{value}" for value in HITTER_TALENT_OUTCOMES]
    ).rows()


def main() -> int:
    args = _parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract.get("contract_schema_version") != "0.4":
        raise ValueError("Stage 2c materializer requires contract schema 0.4")
    if contract.get("implementation_state", {}).get("scoring_authorized") is not False:
        raise ValueError("Stage 2c schema 0.4 must remain unscored at this gate")
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
        mode_records: dict[str, object] = {}
        zero_ladder_base = base
        for mode, model_id in MODES.items():
            features = build_stage2c_features(
                history,
                player_ids,
                predictor_cutoff_season=cutoff,
                mode=mode,
            ).sort("player_id")
            features_cut = build_stage2c_features(
                history.filter(pl.col("season") <= cutoff),
                player_ids,
                predictor_cutoff_season=cutoff,
                mode=mode,
            ).sort("player_id")
            if not features.equals(features_cut):
                raise ValueError(f"{fold_id} {mode} features depend on future rows")
            zero = apply_stage2c_residual(
                zero_ladder_base,
                features,
                zero_stage2c_fit(mode),
                model_id=model_id,
            )
            if _probabilities(base) != _probabilities(zero):
                raise ValueError(f"{fold_id} {mode} zero increment changed base")
            zero_ladder_base = zero
            artifact = write_canonical_parquet(
                features,
                args.report_root / "tables" / fold_id.lower() / f"{mode}.parquet",
                table_name=f"hitter_v2_stage2c_{fold_id.lower()}_{mode}_features",
            ).as_record()
            component_records = {}
            for name, _, _ in FEATURES[mode]:
                evidence = features[f"shape_evidence_{name}"]
                reliability = features[f"shape_reliability_{name}"]
                if features.height and (
                    reliability.min() < 0.0 or reliability.max() >= 1.0
                ):
                    raise ValueError(f"{fold_id} {name} reliability out of bounds")
                component_records[name] = {
                    "positive_evidence_players": features.filter(evidence > 0.0).height,
                    "minimum_evidence": float(evidence.min()) if features.height else None,
                    "maximum_evidence": float(evidence.max()) if features.height else None,
                    "minimum_reliability": (
                        float(reliability.min()) if features.height else None
                    ),
                    "maximum_reliability": (
                        float(reliability.max()) if features.height else None
                    ),
                }
            mode_records[mode] = {
                "forecast_players": base.height,
                "supported_players": features.height,
                "fallback_players": base.height - features.height,
                "coverage_rate": features.height / base.height,
                "chronology_future_row_invariance": True,
                "zero_increment_exact_base_fallback": True,
                "components": component_records,
                "feature_artifact": artifact,
            }
        fold_records.append(
            {
                "fold_id": fold_id,
                "predictor_cutoff_season": cutoff,
                "base_prediction_path": base_path.as_posix(),
                "base_prediction_sha256": sha256_file(base_path),
                "modes": mode_records,
            }
        )

    report = {
        "report_schema_version": "0.2",
        "program": "hitter_v2",
        "stage": "2c",
        "status": "implementation_and_unscored_features_materialized",
        "candidate_fit": False,
        "candidate_scored": False,
        "target_outcomes_loaded": False,
        "protected_2026_opened": False,
        "tracking_loaded": False,
        "development_contract_sha256": sha256_file(args.contract),
        "contact_shape_source_sha256": sha256_file(args.shape_history),
        "folds": fold_records,
        "scientific_invariants": {
            "future_shape_rows_cannot_affect_prior_cutoff_features": True,
            "zero_increment_exact_base_fallback": True,
            "missing_shape_is_omitted_not_zero_filled": True,
            "beta_posterior_not_multiplied_by_reliability_twice": True,
            "e1_changes_only_hr_contrast": "covered_by_synthetic_test",
            "e2_changes_only_xbh_contrast": "covered_by_synthetic_test",
            "e2_requires_e1_base": "covered_by_synthetic_test",
            "ground_changes_only_non_hr_reach_contrast": "covered_by_synthetic_test",
            "e3_requires_passing_air_base": "covered_by_synthetic_test",
            "probabilities_exhaustive_and_normalized": "covered_by_synthetic_test",
        },
        "next_step": "review_schema_0_4_unscored_implementation_before_any_scorer_is_frozen_or_run",
    }
    args.report_root.mkdir(parents=True, exist_ok=True)
    (args.report_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
