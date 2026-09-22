#!/usr/bin/env python3
"""Carry certified roster features into the selected hitter value ensemble."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_model_tournament import run_engine_fold
from universal_baseball.hitter_target_architecture import (
    classification_metrics,
    expanding_year_folds,
    paired_cluster_rmse_delta,
    regression_metrics,
    run_lightgbm_architecture_fold,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


PANEL_PATH = Path(
    "reports/generated/hitter-roster-feature-challenger-v2/"
    "modeling-panel-with-roster.parquet"
)
BASELINE_PATH = Path(
    "reports/generated/hitter-model-finalist-tuning-v2/tables/"
    "finalist-ensemble-predictions.parquet"
)
OUTPUT_ROOT = Path("reports/generated/hitter-roster-value-challenger-v2")
KEY = ["origin_year", "target_season", "player_id"]
TWO_PART_ENGINES = ("xgboost", "ebm", "ridge")
MEMBER_NAMES = (
    "direct_lightgbm",
    "three_part_lightgbm",
    "two_part_xgboost",
    "two_part_ebm",
    "two_part_ridge",
)


def _architecture(panel: pl.DataFrame) -> pl.DataFrame:
    cache = OUTPUT_ROOT / "engine-cache" / "architecture-lightgbm.parquet"
    if cache.exists():
        return pl.read_parquet(cache).sort(KEY)
    frames: list[pl.DataFrame] = []
    for fold in expanding_year_folds(panel["origin_year"].unique().to_list()):
        print(f"fitting roster value architecture origin {fold.test_origin}", flush=True)
        predictions, _, _ = run_lightgbm_architecture_fold(panel, fold)
        frames.append(predictions)
    output = pl.concat(frames).sort(KEY)
    cache.parent.mkdir(parents=True, exist_ok=True)
    output.write_parquet(cache, compression="zstd")
    return output


def _two_part(panel: pl.DataFrame, engine: str) -> pl.DataFrame:
    cache = OUTPUT_ROOT / "engine-cache" / f"two-part-{engine}.parquet"
    if cache.exists():
        return pl.read_parquet(cache).sort(KEY)
    frames: list[pl.DataFrame] = []
    for fold in expanding_year_folds(panel["origin_year"].unique().to_list()):
        print(
            f"fitting roster value two-part {engine} origin {fold.test_origin}",
            flush=True,
        )
        predictions, _ = run_engine_fold(panel, fold, engine)
        frames.append(predictions)
    output = pl.concat(frames).sort(KEY)
    cache.parent.mkdir(parents=True, exist_ok=True)
    output.write_parquet(cache, compression="zstd")
    return output


def _segment(frame: pl.DataFrame) -> dict[str, object]:
    actual = frame["actual_component_war"].to_numpy()
    baseline = frame["prediction_baseline_equal_mean"].to_numpy()
    challenger = frame["prediction_roster_equal_mean"].to_numpy()
    return {
        "rows": frame.height,
        "baseline": regression_metrics(actual, baseline),
        "roster_challenger": regression_metrics(actual, challenger),
        "challenger_minus_baseline_rmse": (
            regression_metrics(actual, challenger)["rmse"]
            - regression_metrics(actual, baseline)["rmse"]
        ),
    }


def main() -> None:
    panel = pl.read_parquet(PANEL_PATH)
    architecture = _architecture(panel)
    engines = {engine: _two_part(panel, engine) for engine in TWO_PART_ENGINES}
    baseline = pl.read_parquet(BASELINE_PATH).sort(KEY)
    members = {
        "direct_lightgbm": architecture["prediction_direct"].to_numpy(),
        "three_part_lightgbm": architecture["prediction_three_part"].to_numpy(),
        **{
            f"two_part_{engine}": predictions[
                "predicted_component_war"
            ].to_numpy()
            for engine, predictions in engines.items()
        },
    }
    challenger = np.mean(np.column_stack(list(members.values())), axis=1)
    active_probability = np.mean(
        np.column_stack(
            [
                architecture["active_probability"].to_numpy(),
                *[
                    predictions["active_probability"].to_numpy()
                    for predictions in engines.values()
                ],
            ]
        ),
        axis=1,
    )
    context = panel.select(
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
    frame = (
        architecture.select(*KEY, "actual_active", "actual_component_war")
        .with_columns(
            pl.Series("prediction_roster_equal_mean", challenger),
            pl.Series("prediction_roster_mlb_active_probability", active_probability),
            *[
                pl.Series(f"prediction_roster_member__{name}", prediction)
                for name, prediction in members.items()
            ],
        )
        .join(
            baseline.select(
                *KEY,
                pl.col("prediction_candidate_equal_mean").alias(
                    "prediction_baseline_equal_mean"
                ),
                pl.col("prediction_candidate_mlb_active_probability").alias(
                    "prediction_baseline_mlb_active_probability"
                ),
            ),
            on=KEY,
            how="inner",
            validate="1:1",
        )
        .join(context, on=["origin_year", "player_id"], how="left", validate="1:1")
        .sort(KEY)
    )
    if frame.height != architecture.height or frame.height != baseline.height:
        raise ValueError("roster value challenger and baseline populations differ")

    actual = frame["actual_component_war"].to_numpy()
    baseline_prediction = frame["prediction_baseline_equal_mean"].to_numpy()
    player_ids = frame["player_id"].to_numpy()
    member_metrics = {
        name: regression_metrics(actual, prediction)
        for name, prediction in members.items()
    }
    leave_one_out = {
        f"without_{omitted}": regression_metrics(
            actual,
            np.mean(
                np.column_stack(
                    [members[name] for name in MEMBER_NAMES if name != omitted]
                ),
                axis=1,
            ),
        )
        for omitted in MEMBER_NAMES
    }
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
        table_name="hitter_roster_value_challenger_v2_predictions",
    )
    report = {
        "schema_version": "0.1",
        "status": "hitter_roster_value_challenger_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "population_rows": frame.height,
        "target": "next-season zero-inclusive MLB batting plus replacement WAR",
        "members": list(MEMBER_NAMES),
        "total_value": {
            "baseline": regression_metrics(actual, baseline_prediction),
            "roster_challenger": regression_metrics(actual, challenger),
            "paired_challenger_minus_baseline": paired_cluster_rmse_delta(
                actual,
                challenger,
                baseline_prediction,
                player_ids,
            ),
        },
        "active_probability": {
            "baseline": classification_metrics(
                frame["actual_active"].to_numpy(),
                frame["prediction_baseline_mlb_active_probability"].to_numpy(),
            ),
            "roster_challenger": classification_metrics(
                frame["actual_active"].to_numpy(), active_probability
            ),
        },
        "member_metrics": member_metrics,
        "leave_one_member_out": leave_one_out,
        "by_origin": by_origin,
        "by_player_stage": by_stage,
        "by_origin_40man_membership": by_membership,
        "sources": {
            "augmented_panel": {
                "path": str(PANEL_PATH),
                "sha256": sha256_file(PANEL_PATH),
            },
            "baseline": {
                "path": str(BASELINE_PATH),
                "sha256": sha256_file(BASELINE_PATH),
            },
        },
        "artifact": artifact.as_record(),
        "limitations": [
            "This isolates roster-feature value; it does not retune engines or ensemble weights.",
            "The five-member structure and equal weights are identical to the selected baseline.",
            "2026 outcomes remain sealed.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
