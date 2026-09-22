#!/usr/bin/env python3
"""Test pitch-rate evidence as a chronology-safe MLB-arrival stack only."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression

from universal_baseball.hitter_target_architecture import classification_metrics
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--incumbent",
        type=Path,
        default=Path(
            "reports/generated/hitter-model-finalist-tuning-v2/tables/"
            "finalist-ensemble-predictions.parquet"
        ),
    )
    parser.add_argument(
        "--lightgbm-rates",
        type=Path,
        default=Path(
            "reports/generated/hitter-pitch-game-ablation-v1/tables/"
            "lightgbm-base_plus_sequence_rates-predictions.parquet"
        ),
    )
    parser.add_argument(
        "--xgboost-rates",
        type=Path,
        default=Path(
            "reports/generated/hitter-pitch-game-engine-check-v1/tables/"
            "xgboost-base_plus_sequence_rates-predictions.parquet"
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/hitter-pitch-arrival-stack-v1"),
    )
    return parser.parse_args()


def _logit(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(values, 1e-5, 1.0 - 1e-5)
    return np.log(clipped / (1.0 - clipped))


def _fit_probability(
    train: pl.DataFrame, test: pl.DataFrame, columns: list[str]
) -> np.ndarray:
    x_train = np.column_stack([_logit(train[column].to_numpy()) for column in columns])
    x_test = np.column_stack([_logit(test[column].to_numpy()) for column in columns])
    model = LogisticRegression(C=0.10, max_iter=1_000, random_state=417)
    model.fit(x_train, train["actual_active"].to_numpy())
    return model.predict_proba(x_test)[:, 1]


def _cluster_loss_delta(
    actual: np.ndarray,
    challenger: np.ndarray,
    reference: np.ndarray,
    clusters: np.ndarray,
    *,
    loss: str,
    samples: int = 2_000,
) -> dict[str, float]:
    if loss == "brier":
        difference = np.square(challenger - actual) - np.square(reference - actual)
    elif loss == "log_loss":
        challenger = np.clip(challenger, 1e-6, 1.0 - 1e-6)
        reference = np.clip(reference, 1e-6, 1.0 - 1e-6)
        challenger_loss = -(
            actual * np.log(challenger) + (1.0 - actual) * np.log(1.0 - challenger)
        )
        reference_loss = -(
            actual * np.log(reference) + (1.0 - actual) * np.log(1.0 - reference)
        )
        difference = challenger_loss - reference_loss
    else:
        raise ValueError(f"unsupported loss: {loss}")
    labels, inverse = np.unique(clusters, return_inverse=True)
    sums = np.bincount(inverse, weights=difference)
    counts = np.bincount(inverse)
    rng = np.random.default_rng(417)
    draws = np.empty(samples)
    for index in range(samples):
        selected = rng.integers(0, labels.size, size=labels.size)
        draws[index] = sums[selected].sum() / counts[selected].sum()
    return {
        "loss_delta": float(np.mean(difference)),
        "ci95_low": float(np.quantile(draws, 0.025)),
        "ci95_high": float(np.quantile(draws, 0.975)),
        "player_clusters": int(labels.size),
        "bootstrap_samples": samples,
    }


def _load(args: argparse.Namespace) -> pl.DataFrame:
    keys = ["origin_year", "target_season", "player_id"]
    incumbent = pl.read_parquet(args.incumbent).select(
        *keys,
        "actual_active",
        "actual_component_war",
        pl.col("prediction_candidate_equal_mean").alias("incumbent_expected_war"),
        pl.col("prediction_candidate_mlb_active_probability").alias(
            "incumbent_probability"
        ),
        "player_stage",
    )
    lightgbm = pl.read_parquet(args.lightgbm_rates).select(
        *keys,
        pl.col("active_probability").alias("lightgbm_rate_probability"),
    )
    xgboost = pl.read_parquet(args.xgboost_rates).select(
        *keys,
        pl.col("active_probability").alias("xgboost_rate_probability"),
    )
    result = incumbent.join(lightgbm, on=keys, validate="1:1").join(
        xgboost, on=keys, validate="1:1"
    )
    if result.height != incumbent.height:
        raise ValueError("arrival prediction sources do not cover identical rows")
    return result.sort("origin_year", "player_id")


def main() -> int:
    args = _args()
    data = _load(args)
    predictions = []
    coefficients = []
    origins = sorted(data["origin_year"].unique().to_list())
    for origin in origins:
        train = data.filter(pl.col("origin_year") < origin)
        test = data.filter(pl.col("origin_year") == origin)
        if train.is_empty():
            recalibrated = test["incumbent_probability"].to_numpy()
            stacked = recalibrated.copy()
            method = "incumbent_fallback_no_prior_oof_origin"
        else:
            recalibrated = _fit_probability(
                train, test, ["incumbent_probability"]
            )
            stacked = _fit_probability(
                train,
                test,
                [
                    "incumbent_probability",
                    "lightgbm_rate_probability",
                    "xgboost_rate_probability",
                ],
            )
            method = "regularized_logistic_stack_fit_on_strictly_earlier_oof_origins"
            x_train = np.column_stack(
                [
                    _logit(train[column].to_numpy())
                    for column in (
                        "incumbent_probability",
                        "lightgbm_rate_probability",
                        "xgboost_rate_probability",
                    )
                ]
            )
            model = LogisticRegression(C=0.10, max_iter=1_000, random_state=417)
            model.fit(x_train, train["actual_active"].to_numpy())
            coefficients.append(
                {
                    "test_origin": origin,
                    "train_origins": sorted(train["origin_year"].unique().to_list()),
                    "intercept": float(model.intercept_[0]),
                    "incumbent_logit_weight": float(model.coef_[0, 0]),
                    "lightgbm_rate_logit_weight": float(model.coef_[0, 1]),
                    "xgboost_rate_logit_weight": float(model.coef_[0, 2]),
                }
            )
        predictions.append(
            test.with_columns(
                pl.Series("recalibrated_incumbent_probability", recalibrated),
                pl.Series("stacked_rate_probability", stacked),
                pl.lit(method).alias("stack_method"),
            )
        )
    combined = pl.concat(predictions)
    actual = combined["actual_active"].to_numpy()
    incumbent_probability = combined["incumbent_probability"].to_numpy()
    recalibrated_probability = combined[
        "recalibrated_incumbent_probability"
    ].to_numpy()
    stacked_probability = combined["stacked_rate_probability"].to_numpy()
    report = {
        "schema_version": "1.0",
        "status": "chronological_arrival_stack_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "rows": combined.height,
        "origins": origins,
        "metrics": {
            "incumbent_raw": classification_metrics(actual, incumbent_probability),
            "incumbent_chronologically_recalibrated": classification_metrics(
                actual, recalibrated_probability
            ),
            "pitch_rate_stack": classification_metrics(actual, stacked_probability),
        },
        "paired_player_cluster_deltas_vs_raw_incumbent": {
            "recalibrated_brier": _cluster_loss_delta(
                actual,
                recalibrated_probability,
                incumbent_probability,
                combined["player_id"].to_numpy(),
                loss="brier",
            ),
            "recalibrated_log_loss": _cluster_loss_delta(
                actual,
                recalibrated_probability,
                incumbent_probability,
                combined["player_id"].to_numpy(),
                loss="log_loss",
            ),
            "pitch_rate_stack_brier": _cluster_loss_delta(
                actual,
                stacked_probability,
                incumbent_probability,
                combined["player_id"].to_numpy(),
                loss="brier",
            ),
            "pitch_rate_stack_log_loss": _cluster_loss_delta(
                actual,
                stacked_probability,
                incumbent_probability,
                combined["player_id"].to_numpy(),
                loss="log_loss",
            ),
        },
        "fold_metrics": {
            str(origin): {
                "incumbent_raw": classification_metrics(
                    combined.filter(pl.col("origin_year") == origin)[
                        "actual_active"
                    ].to_numpy(),
                    combined.filter(pl.col("origin_year") == origin)[
                        "incumbent_probability"
                    ].to_numpy(),
                ),
                "pitch_rate_stack": classification_metrics(
                    combined.filter(pl.col("origin_year") == origin)[
                        "actual_active"
                    ].to_numpy(),
                    combined.filter(pl.col("origin_year") == origin)[
                        "stacked_rate_probability"
                    ].to_numpy(),
                ),
            }
            for origin in origins
        },
        "stack_coefficients": coefficients,
        "decision_boundary": (
            "This stack may replace only the reported MLB-arrival probability. "
            "It does not alter the expected-WAR forecast unless separately validated."
        ),
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        combined,
        args.output_root / "tables" / "arrival-stack-predictions.parquet",
        table_name="hitter_pitch_arrival_stack_predictions_v1",
    )
    report["artifact"] = artifact.as_record()
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["metrics"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
