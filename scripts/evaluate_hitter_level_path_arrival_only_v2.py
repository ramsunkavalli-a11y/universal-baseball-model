#!/usr/bin/env python3
"""Use level-path evidence for arrival only while freezing hitting-strength estimates."""

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
ROOT = Path("reports/generated")
OUTPUT_ROOT = ROOT / "hitter-level-path-arrival-only-v2"


def _load(path: Path) -> pl.DataFrame:
    return pl.read_parquet(path).sort(KEY)


def _safe_conditional(total: np.ndarray, probability: np.ndarray) -> np.ndarray:
    return np.divide(
        total,
        probability,
        out=np.zeros_like(total, dtype=np.float64),
        where=probability > 1e-8,
    )


def _metrics(
    actual: np.ndarray, prediction: np.ndarray
) -> dict[str, float]:
    return regression_metrics(actual, prediction)


def main() -> int:
    incumbent = _load(
        ROOT
        / "hitter-model-finalist-tuning-v2/tables/finalist-ensemble-predictions.parquet"
    )
    architecture = _load(
        ROOT / "hitter-target-architecture-v1/tables/chronological_predictions.parquet"
    )
    engines = {
        engine: _load(
            ROOT
            / f"hitter-model-engine-tournament-v2/tables/{engine}-predictions.parquet"
        )
        for engine in ("xgboost", "ebm", "ridge")
    }
    path = _load(
        ROOT / "hitter-level-path-compact-ablation-v2/tables/predictions.parquet"
    )
    for label, frame in {
        "architecture": architecture,
        **engines,
        "path": path,
    }.items():
        if not frame.select(KEY).equals(incumbent.select(KEY)):
            raise ValueError(f"{label} prediction keys do not align")

    actual = incumbent["actual_component_war"].to_numpy()
    active = incumbent["actual_active"].to_numpy()
    incumbent_prediction = incumbent["prediction_candidate_equal_mean"].to_numpy()
    incumbent_probability = incumbent[
        "prediction_candidate_mlb_active_probability"
    ].to_numpy()
    path_probability = path["challenger_active_probability"].to_numpy()
    direct = incumbent["prediction_member__direct_lightgbm"].to_numpy()
    conditional_members = [
        _safe_conditional(
            architecture["prediction_three_part"].to_numpy(),
            architecture["active_probability"].to_numpy(),
        ),
        *(engines[engine]["predicted_conditional_war"].to_numpy() for engine in engines),
    ]
    conditional_sum = np.column_stack(conditional_members).sum(axis=1)
    incumbent_consensus = (direct + incumbent_probability * conditional_sum) / 5.0
    path_arrival_only = (direct + path_probability * conditional_sum) / 5.0

    output = incumbent.select(
        *KEY, "actual_active", "actual_component_war", "player_stage"
    ).with_columns(
        pl.Series("incumbent_prediction", incumbent_prediction),
        pl.Series("incumbent_probability", incumbent_probability),
        pl.Series("incumbent_consensus_probability_prediction", incumbent_consensus),
        pl.Series("path_probability", path_probability),
        pl.Series("path_arrival_only_prediction", path_arrival_only),
    )
    comparisons = {
        "path_arrival_only_minus_incumbent": paired_cluster_rmse_delta(
            actual,
            path_arrival_only,
            incumbent_prediction,
            incumbent["player_id"].to_numpy(),
        ),
        "path_probability_minus_incumbent_consensus_probability": paired_cluster_rmse_delta(
            actual,
            path_arrival_only,
            incumbent_consensus,
            incumbent["player_id"].to_numpy(),
        ),
    }
    folds = {}
    for origin in output["origin_year"].unique().sort().to_list():
        mask = output["origin_year"].to_numpy() == origin
        folds[str(origin)] = {
            "incumbent": _metrics(actual[mask], incumbent_prediction[mask]),
            "incumbent_consensus_probability": _metrics(
                actual[mask], incumbent_consensus[mask]
            ),
            "path_arrival_only": _metrics(actual[mask], path_arrival_only[mask]),
        }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        output,
        OUTPUT_ROOT / "predictions.parquet",
        table_name="hitter_level_path_arrival_only_v2_predictions",
    )
    report = {
        "schema_version": "0.1",
        "status": "level_path_arrival_only_evaluation_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "design": (
            "Freeze the incumbent direct and conditional hitting-value estimates. "
            "Replace only the shared MLB-active probability with the probability "
            "from the compact level-path challenger."
        ),
        "incumbent": _metrics(actual, incumbent_prediction),
        "incumbent_consensus_probability": _metrics(actual, incumbent_consensus),
        "path_arrival_only": _metrics(actual, path_arrival_only),
        "arrival_probability": {
            "incumbent": classification_metrics(active, incumbent_probability),
            "path": classification_metrics(active, path_probability),
        },
        "comparisons": comparisons,
        "folds": folds,
        "decision_rule": (
            "Treat as development evidence only. Retain the path fields as an arrival "
            "challenger only if their probability scores improve and the resulting "
            "expected-value RMSE gain is stable enough to matter."
        ),
        "artifact": artifact.as_record(),
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
