#!/usr/bin/env python3
"""Route stats-only arrival probabilities into detailed-contact value models."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_target_architecture import (
    classification_metrics,
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.storage import write_canonical_parquet


KEY = ["origin_year", "target_season", "player_id"]
ROOT = Path("reports/generated/hitter-feature-routing-v1")
BASELINE_PATH = Path(
    "reports/generated/hitter-model-finalist-tuning-v2/tables/"
    "finalist-ensemble-predictions.parquet"
)
ARCHITECTURE_PATH = Path(
    "reports/generated/hitter-target-architecture-v1/tables/"
    "chronological_predictions.parquet"
)
ENGINE_ROOT = Path("reports/generated/hitter-model-engine-tournament-v2/tables")
STATS_ONLY_PATH = Path(
    "reports/generated/hitter-contact-block-ensemble-v2/tables/"
    "stats_only-predictions.parquet"
)


def _load(path: Path) -> pl.DataFrame:
    return pl.read_parquet(path).sort(KEY)


def _paired_score_delta(
    challenger_loss: np.ndarray,
    reference_loss: np.ndarray,
    players: np.ndarray,
    *,
    samples: int = 2_000,
    seed: int = 417,
) -> dict[str, float]:
    unique_players, inverse = np.unique(players, return_inverse=True)
    difference = challenger_loss - reference_loss
    totals = np.bincount(inverse, weights=difference)
    counts = np.bincount(inverse)
    rng = np.random.default_rng(seed)
    draws = np.empty(samples)
    for index in range(samples):
        sampled = rng.integers(0, unique_players.size, size=unique_players.size)
        draws[index] = totals[sampled].sum() / counts[sampled].sum()
    return {
        "mean_delta": float(np.mean(difference)),
        "ci95_low": float(np.quantile(draws, 0.025)),
        "ci95_high": float(np.quantile(draws, 0.975)),
        "player_clusters": int(unique_players.size),
        "bootstrap_samples": samples,
    }


def _metric_bundle(frame: pl.DataFrame, prediction: str, probability: str) -> dict:
    result = {
        "rows": frame.height,
        "players": frame["player_id"].n_unique(),
        "total_value": regression_metrics(
            frame["actual_component_war"].to_numpy(), frame[prediction].to_numpy()
        ),
        "active_probability": classification_metrics(
            frame["actual_active"].to_numpy(), frame[probability].to_numpy()
        ),
        "folds": {},
        "subgroups": {},
    }
    for origin in frame["origin_year"].unique().sort().to_list():
        subset = frame.filter(pl.col("origin_year") == origin)
        result["folds"][str(origin)] = regression_metrics(
            subset["actual_component_war"].to_numpy(), subset[prediction].to_numpy()
        )
    for stage in ("current_mlb", "upper_minors", "lower_minors"):
        subset = frame.filter(pl.col("player_stage") == stage)
        result["subgroups"][stage] = {
            "rows": subset.height,
            **regression_metrics(
                subset["actual_component_war"].to_numpy(),
                subset[prediction].to_numpy(),
            ),
        }
    return result


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "tables").mkdir(exist_ok=True)
    baseline = _load(BASELINE_PATH)
    architecture = _load(ARCHITECTURE_PATH)
    stats_only = _load(STATS_ONLY_PATH)
    engines = {name: _load(ENGINE_ROOT / f"{name}-predictions.parquet") for name in ("xgboost", "ebm", "ridge")}

    joined = baseline.select(
        *KEY,
        "actual_active",
        "actual_component_war",
        "player_stage",
        pl.col("prediction_candidate_equal_mean").alias("current_prediction"),
        pl.col("prediction_candidate_mlb_active_probability").alias(
            "current_active_probability"
        ),
        pl.col("prediction_member__direct_lightgbm").alias("direct_prediction"),
    ).join(
        stats_only.select(
            *KEY,
            pl.col("ensemble_active_probability").alias(
                "stats_only_active_probability"
            ),
        ),
        on=KEY,
        how="inner",
    ).join(
        architecture.select(
            *KEY,
            "predicted_conditional_pa",
            "predicted_conditional_rate_per_600",
        ),
        on=KEY,
        how="inner",
    )
    for name, frame in engines.items():
        joined = joined.join(
            frame.select(
                *KEY,
                pl.col("predicted_conditional_war").alias(
                    f"{name}_conditional_war"
                ),
            ),
            on=KEY,
            how="inner",
        )
    if joined.height != baseline.height:
        raise ValueError("source prediction artifacts do not align")

    probability = joined["stats_only_active_probability"].to_numpy()
    three_part_conditional = (
        np.clip(joined["predicted_conditional_pa"].to_numpy(), 0.0, 750.0)
        * np.clip(
            joined["predicted_conditional_rate_per_600"].to_numpy(), -5.0, 10.0
        )
        / 600.0
    )
    routed_members = [
        joined["direct_prediction"].to_numpy(),
        probability * three_part_conditional,
        *[
            probability * joined[f"{name}_conditional_war"].to_numpy()
            for name in ("xgboost", "ebm", "ridge")
        ],
    ]
    joined = joined.with_columns(
        pl.Series("routed_prediction", np.mean(routed_members, axis=0))
    )

    actual = joined["actual_component_war"].to_numpy()
    players = joined["player_id"].to_numpy()
    active = joined["actual_active"].to_numpy()
    current_probability = np.clip(
        joined["current_active_probability"].to_numpy(), 1e-6, 1.0 - 1e-6
    )
    routed_probability = np.clip(probability, 1e-6, 1.0 - 1e-6)
    comparison = paired_cluster_rmse_delta(
        actual,
        joined["routed_prediction"].to_numpy(),
        joined["current_prediction"].to_numpy(),
        players,
    )
    comparison["brier"] = _paired_score_delta(
        np.square(routed_probability - active),
        np.square(current_probability - active),
        players,
    )
    comparison["log_loss"] = _paired_score_delta(
        -(active * np.log(routed_probability) + (1 - active) * np.log(1 - routed_probability)),
        -(active * np.log(current_probability) + (1 - active) * np.log(1 - current_probability)),
        players,
    )

    report = {
        "schema_version": "1.0",
        "status": "chronological_evaluation_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "routing_rule": (
            "Keep the direct detailed-contact model unchanged. For the four "
            "decomposed ensemble members, replace their detailed-contact arrival "
            "probabilities with the stats-only ensemble arrival probability while "
            "retaining their detailed-contact conditional-value estimates."
        ),
        "current": _metric_bundle(
            joined, "current_prediction", "current_active_probability"
        ),
        "routed": _metric_bundle(
            joined, "routed_prediction", "stats_only_active_probability"
        ),
        "routed_minus_current": comparison,
    }
    artifact = write_canonical_parquet(
        joined,
        ROOT / "tables" / "routed-predictions.parquet",
        table_name="hitter_feature_routing_v1_predictions",
    )
    report["artifact"] = artifact.as_record()
    (ROOT / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "current_rmse": report["current"]["total_value"]["rmse"],
                "routed_rmse": report["routed"]["total_value"]["rmse"],
                "comparison": comparison,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
