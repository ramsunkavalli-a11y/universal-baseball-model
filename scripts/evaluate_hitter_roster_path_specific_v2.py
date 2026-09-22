#!/usr/bin/env python3
"""Test roster evidence only on the arrival path, never the batting-skill path."""

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
from universal_baseball.storage import sha256_file, write_canonical_parquet


BASELINE_PATH = Path(
    "reports/generated/hitter-model-finalist-tuning-v2/tables/"
    "finalist-ensemble-predictions.parquet"
)
OLD_ARCHITECTURE_PATH = Path(
    "reports/generated/hitter-target-architecture-v1/tables/"
    "chronological_predictions.parquet"
)
OLD_ENGINE_ROOT = Path("reports/generated/hitter-model-engine-tournament-v2/tables")
NEW_ARCHITECTURE_PATH = Path(
    "reports/generated/hitter-roster-value-challenger-v2/engine-cache/"
    "architecture-lightgbm.parquet"
)
NEW_ENGINE_ROOT = Path(
    "reports/generated/hitter-roster-value-challenger-v2/engine-cache"
)
FULL_ROSTER_PATH = Path(
    "reports/generated/hitter-roster-value-challenger-v2/"
    "chronological-predictions.parquet"
)
PANEL_PATH = Path(
    "reports/generated/hitter-roster-feature-challenger-v2/"
    "modeling-panel-with-roster.parquet"
)
OUTPUT_ROOT = Path("reports/generated/hitter-roster-path-specific-v2")
KEY = ["origin_year", "target_season", "player_id"]
ENGINES = ("xgboost", "ebm", "ridge")


def _load(path: Path) -> pl.DataFrame:
    return pl.read_parquet(path).sort(KEY)


def _segment(frame: pl.DataFrame) -> dict[str, object]:
    actual = frame["actual_component_war"].to_numpy()
    return {
        "rows": frame.height,
        "baseline": regression_metrics(
            actual, frame["prediction_baseline_equal_mean"].to_numpy()
        ),
        "roster_all_paths": regression_metrics(
            actual, frame["prediction_roster_all_paths_equal_mean"].to_numpy()
        ),
        "roster_arrival_only": regression_metrics(
            actual, frame["prediction_roster_arrival_only_equal_mean"].to_numpy()
        ),
    }


def main() -> None:
    baseline = _load(BASELINE_PATH)
    old_architecture = _load(OLD_ARCHITECTURE_PATH)
    new_architecture = _load(NEW_ARCHITECTURE_PATH)
    old_engines = {
        engine: _load(OLD_ENGINE_ROOT / f"{engine}-predictions.parquet")
        for engine in ENGINES
    }
    new_engines = {
        engine: _load(NEW_ENGINE_ROOT / f"two-part-{engine}.parquet")
        for engine in ENGINES
    }
    full_roster = _load(FULL_ROSTER_PATH)
    panel = pl.read_parquet(PANEL_PATH).select(
        "origin_year",
        "player_id",
        "roster_lag0__on_40man",
        pl.when(pl.col("lag0__pa_level__MLB") > 0)
        .then(pl.lit("current_mlb"))
        .when(pl.col("lag0__highest_level").is_in(["AAA", "AA"]))
        .then(pl.lit("upper_minors"))
        .otherwise(pl.lit("lower_minors"))
        .alias("player_stage"),
    )

    direct = old_architecture["prediction_direct"].to_numpy()
    old_arch_probability = np.clip(
        old_architecture["active_probability"].to_numpy(), 1e-8, 1.0
    )
    three_part_conditional_value = (
        old_architecture["prediction_three_part"].to_numpy()
        / old_arch_probability
    )
    members = {
        "direct_lightgbm": direct,
        "three_part_lightgbm": (
            new_architecture["active_probability"].to_numpy()
            * three_part_conditional_value
        ),
        **{
            f"two_part_{engine}": (
                new_engines[engine]["active_probability"].to_numpy()
                * old_engines[engine]["predicted_conditional_war"].to_numpy()
            )
            for engine in ENGINES
        },
    }
    arrival_only = np.mean(np.column_stack(list(members.values())), axis=1)
    arrival_probability = np.mean(
        np.column_stack(
            [
                new_architecture["active_probability"].to_numpy(),
                *[
                    new_engines[engine]["active_probability"].to_numpy()
                    for engine in ENGINES
                ],
            ]
        ),
        axis=1,
    )
    frame = (
        baseline.select(*KEY, "actual_active", "actual_component_war")
        .with_columns(
            baseline["prediction_candidate_equal_mean"].alias(
                "prediction_baseline_equal_mean"
            ),
            full_roster["prediction_roster_equal_mean"].alias(
                "prediction_roster_all_paths_equal_mean"
            ),
            pl.Series("prediction_roster_arrival_only_equal_mean", arrival_only),
            pl.Series("prediction_roster_arrival_probability", arrival_probability),
            *[
                pl.Series(f"prediction_arrival_only_member__{name}", prediction)
                for name, prediction in members.items()
            ],
        )
        .join(panel, on=["origin_year", "player_id"], how="left", validate="1:1")
        .sort(KEY)
    )
    actual = frame["actual_component_war"].to_numpy()
    baseline_prediction = frame["prediction_baseline_equal_mean"].to_numpy()
    all_paths = frame["prediction_roster_all_paths_equal_mean"].to_numpy()
    player_ids = frame["player_id"].to_numpy()
    by_origin = {
        str(origin): _segment(frame.filter(pl.col("origin_year") == origin))
        for origin in sorted(frame["origin_year"].unique().to_list())
    }
    by_stage = {
        stage: _segment(frame.filter(pl.col("player_stage") == stage))
        for stage in ("current_mlb", "upper_minors", "lower_minors")
    }
    by_membership = {
        "on_40man": _segment(frame.filter(pl.col("roster_lag0__on_40man") == 1)),
        "not_on_40man": _segment(
            frame.filter(pl.col("roster_lag0__on_40man") == 0)
        ),
    }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        frame,
        OUTPUT_ROOT / "chronological-predictions.parquet",
        table_name="hitter_roster_path_specific_v2_predictions",
    )
    report = {
        "schema_version": "0.1",
        "status": "hitter_roster_path_specific_test_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "population_rows": frame.height,
        "target": "next-season zero-inclusive MLB batting plus replacement WAR",
        "architecture": (
            "40-man features enter only each hurdle classifier; direct value and "
            "conditional batting-value estimates remain from the roster-blind model"
        ),
        "metrics": {
            "baseline": regression_metrics(actual, baseline_prediction),
            "roster_all_paths": regression_metrics(actual, all_paths),
            "roster_arrival_only": regression_metrics(actual, arrival_only),
        },
        "paired_comparisons": {
            "arrival_only_minus_baseline": paired_cluster_rmse_delta(
                actual,
                arrival_only,
                baseline_prediction,
                player_ids,
            ),
            "arrival_only_minus_all_paths": paired_cluster_rmse_delta(
                actual,
                arrival_only,
                all_paths,
                player_ids,
            ),
        },
        "active_probability": classification_metrics(
            frame["actual_active"].to_numpy(), arrival_probability
        ),
        "by_origin": by_origin,
        "by_player_stage": by_stage,
        "by_origin_40man_membership": by_membership,
        "sources": {
            "baseline": {"path": str(BASELINE_PATH), "sha256": sha256_file(BASELINE_PATH)},
            "old_architecture": {
                "path": str(OLD_ARCHITECTURE_PATH),
                "sha256": sha256_file(OLD_ARCHITECTURE_PATH),
            },
            "new_architecture": {
                "path": str(NEW_ARCHITECTURE_PATH),
                "sha256": sha256_file(NEW_ARCHITECTURE_PATH),
            },
            "full_roster_challenger": {
                "path": str(FULL_ROSTER_PATH),
                "sha256": sha256_file(FULL_ROSTER_PATH),
            },
        },
        "artifact": artifact.as_record(),
        "limitations": [
            "This is a path-specific reuse of already fitted models, not another tuning pass.",
            "The direct LightGBM member is intentionally roster-blind because it has no separate opportunity path.",
            "2026 outcomes remain sealed.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
