#!/usr/bin/env python3
"""Test certified 40-man history as a hitter workload/arrival feature."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_target_architecture import (
    classification_metrics,
    expanding_year_folds,
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.hitter_workload import run_workload_fold
from universal_baseball.storage import sha256_file, write_canonical_parquet


OLD_ROOT = Path(
    "C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/"
    "universal-baseball-model/reports/generated"
)
PANEL_PATH = Path("reports/generated/hitter-value-panel-v2/tables/modeling-panel.parquet")
BASELINE_PATH = Path(
    "reports/generated/hitter-workload-model-v2/chronological-predictions.parquet"
)
PRE_2020_PATH = (
    OLD_ROOT
    / "opportunity-40man-pre2020/tables/historical_40man_membership.parquet"
)
MODERN_PATH = (
    OLD_ROOT
    / "opportunity-40man-history/tables/historical_40man_membership.parquet"
)
OUTPUT_ROOT = Path("reports/generated/hitter-roster-feature-challenger-v2")
ENGINES = ("lightgbm", "xgboost", "ebm", "ridge")
KEY = ["origin_year", "target_season", "player_id"]


def _membership() -> pl.DataFrame:
    frame = (
        pl.concat(
            [
                pl.read_parquet(PRE_2020_PATH),
                pl.read_parquet(MODERN_PATH),
            ],
            how="vertical_relaxed",
        )
        .filter(pl.col("season").is_between(2015, 2024))
        .select(
            pl.col("season").cast(pl.Int64),
            pl.col("player_id").cast(pl.Int64),
            pl.col("on_40man").cast(pl.Int8),
        )
        .unique(["season", "player_id"])
        .sort("season", "player_id")
    )
    if frame.group_by("season", "player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("40-man membership violates player-season grain")
    if frame.filter(pl.col("on_40man") != 1).height:
        raise ValueError("certified membership table contains a nonmember row")
    return frame


def _augment(panel: pl.DataFrame, membership: pl.DataFrame) -> pl.DataFrame:
    available_seasons = set(membership["season"].unique().to_list())
    result = panel
    lag_columns: list[str] = []
    available_columns: list[str] = []
    for lag in range(3):
        member_column = f"roster_lag{lag}__on_40man"
        available_column = f"roster_lag{lag}__snapshot_available"
        lookup = membership.rename(
            {"season": "membership_season", "on_40man": member_column}
        )
        result = (
            result.with_columns(
                (pl.col("origin_year") - lag).alias("membership_season")
            )
            .join(
                lookup,
                on=["membership_season", "player_id"],
                how="left",
                validate="m:1",
            )
            .with_columns(
                pl.col(member_column).fill_null(0).cast(pl.Int8),
                pl.col("membership_season")
                .is_in(sorted(available_seasons))
                .cast(pl.Int8)
                .alias(available_column),
            )
            .drop("membership_season")
        )
        lag_columns.append(member_column)
        available_columns.append(available_column)
    return result.with_columns(
        pl.sum_horizontal(*[pl.col(column) for column in lag_columns])
        .cast(pl.Int8)
        .alias("roster__on_40man_last3_count"),
        (
            pl.col(lag_columns[0])
            + pl.col(lag_columns[0]) * pl.col(lag_columns[1])
            + pl.col(lag_columns[0])
            * pl.col(lag_columns[1])
            * pl.col(lag_columns[2])
        )
        .cast(pl.Int8)
        .alias("roster__on_40man_streak"),
        pl.sum_horizontal(*[pl.col(column) for column in available_columns])
        .cast(pl.Int8)
        .alias("roster__snapshot_count"),
    )


def _fit_candidate(panel: pl.DataFrame) -> tuple[pl.DataFrame, dict[str, object]]:
    folds = expanding_year_folds(panel["origin_year"].unique().to_list())
    cache_root = OUTPUT_ROOT / "engine-cache"
    cache_root.mkdir(parents=True, exist_ok=True)
    engine_predictions: dict[str, pl.DataFrame] = {}
    engine_reports: dict[str, object] = {}
    for engine in ENGINES:
        cache_path = cache_root / f"{engine}.parquet"
        report_path = cache_root / f"{engine}.json"
        if cache_path.exists() and report_path.exists():
            engine_predictions[engine] = pl.read_parquet(cache_path).sort(KEY)
            engine_reports[engine] = json.loads(report_path.read_text(encoding="utf-8"))
            continue
        frames: list[pl.DataFrame] = []
        reports: list[dict[str, object]] = []
        for fold in folds:
            print(
                f"fitting roster workload {engine} origin {fold.test_origin}",
                flush=True,
            )
            result, metrics = run_workload_fold(
                panel,
                fold,
                engine,
                include_direct=engine == "lightgbm",
            )
            frames.append(result)
            reports.append({"test_origin": fold.test_origin, "metrics": metrics})
        engine_predictions[engine] = pl.concat(frames).sort(KEY)
        engine_reports[engine] = {"folds": reports}
        engine_predictions[engine].write_parquet(cache_path, compression="zstd")
        report_path.write_text(
            json.dumps(engine_reports[engine], indent=2, sort_keys=True),
            encoding="utf-8",
        )

    reference = engine_predictions["lightgbm"]
    members = {
        "direct_lightgbm": reference["predicted_direct_pa"].to_numpy(),
        **{
            f"hurdle_{engine}": frame["predicted_hurdle_pa"].to_numpy()
            for engine, frame in engine_predictions.items()
        },
    }
    expected_pa = np.mean(np.column_stack(list(members.values())), axis=1)
    active_probability = np.mean(
        np.column_stack(
            [
                frame["active_probability"].to_numpy()
                for frame in engine_predictions.values()
            ]
        ),
        axis=1,
    )
    output = reference.select(KEY + ["actual_active", "actual_pa"]).with_columns(
        pl.Series("prediction_roster_expected_pa", expected_pa),
        pl.Series("prediction_roster_active_probability", active_probability),
        *[
            pl.Series(f"prediction_roster_member__{name}", prediction)
            for name, prediction in members.items()
        ],
    )
    return output, engine_reports


def _segment_metrics(frame: pl.DataFrame) -> dict[str, object]:
    actual = frame["actual_pa"].to_numpy()
    baseline = frame["prediction_candidate_expected_pa"].to_numpy()
    challenger = frame["prediction_roster_expected_pa"].to_numpy()
    return {
        "rows": frame.height,
        "actual_active_rate": float(frame["actual_active"].mean()),
        "baseline": regression_metrics(actual, baseline),
        "roster_challenger": regression_metrics(actual, challenger),
        "challenger_minus_baseline_rmse": (
            regression_metrics(actual, challenger)["rmse"]
            - regression_metrics(actual, baseline)["rmse"]
        ),
    }


def main() -> None:
    base_panel = pl.read_parquet(PANEL_PATH)
    membership = _membership()
    panel = _augment(base_panel, membership)
    predictions, engine_reports = _fit_candidate(panel)
    baseline = pl.read_parquet(BASELINE_PATH).select(
        *KEY,
        "prediction_candidate_expected_pa",
        "prediction_candidate_active_probability",
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
        predictions.join(baseline, on=KEY, how="inner", validate="1:1")
        .join(context, on=["origin_year", "player_id"], how="left", validate="1:1")
        .sort(KEY)
    )
    if frame.height != predictions.height or frame.height != baseline.height:
        raise ValueError("roster challenger and baseline populations differ")

    actual_pa = frame["actual_pa"].to_numpy()
    actual_active = frame["actual_active"].to_numpy()
    old_pa = frame["prediction_candidate_expected_pa"].to_numpy()
    new_pa = frame["prediction_roster_expected_pa"].to_numpy()
    old_active = frame["prediction_candidate_active_probability"].to_numpy()
    new_active = frame["prediction_roster_active_probability"].to_numpy()
    by_fold = {
        str(origin): _segment_metrics(frame.filter(pl.col("origin_year") == origin))
        for origin in sorted(frame["origin_year"].unique().to_list())
    }
    by_stage = {
        stage: _segment_metrics(frame.filter(pl.col("player_stage") == stage))
        for stage in ("current_mlb", "upper_minors", "lower_minors")
    }
    by_membership = {
        "on_40man": _segment_metrics(frame.filter(pl.col("roster_lag0__on_40man") == 1)),
        "not_on_40man": _segment_metrics(
            frame.filter(pl.col("roster_lag0__on_40man") == 0)
        ),
    }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        frame,
        OUTPUT_ROOT / "chronological-predictions.parquet",
        table_name="hitter_roster_feature_challenger_v2_predictions",
    )
    panel_artifact = write_canonical_parquet(
        panel,
        OUTPUT_ROOT / "modeling-panel-with-roster.parquet",
        table_name="hitter_value_panel_v2_with_roster",
    )
    report = {
        "schema_version": "0.1",
        "status": "hitter_roster_feature_challenger_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "population_rows": frame.height,
        "target": "next-season zero-inclusive MLB plate appearances and MLB participation",
        "features": [
            "40-man membership at the October 15 forecast-origin snapshot",
            "membership at the two preceding available October 15 snapshots",
            "three-snapshot membership count and current membership streak",
            "explicit snapshot-availability indicators, including the missing 2020 snapshot",
        ],
        "playing_time": {
            "baseline": regression_metrics(actual_pa, old_pa),
            "roster_challenger": regression_metrics(actual_pa, new_pa),
            "paired_challenger_minus_baseline": paired_cluster_rmse_delta(
                actual_pa,
                new_pa,
                old_pa,
                frame["player_id"].to_numpy(),
            ),
        },
        "active_probability": {
            "baseline": classification_metrics(actual_active, old_active),
            "roster_challenger": classification_metrics(actual_active, new_active),
        },
        "by_origin": by_fold,
        "by_player_stage": by_stage,
        "by_origin_40man_membership": by_membership,
        "engine_fold_reports": engine_reports,
        "membership_coverage": {
            "origin_on_40man_rows": int(frame["roster_lag0__on_40man"].sum()),
            "origin_on_40man_rate": float(frame["roster_lag0__on_40man"].mean()),
        },
        "sources": {
            "panel": {"path": str(PANEL_PATH), "sha256": sha256_file(PANEL_PATH)},
            "baseline": {
                "path": str(BASELINE_PATH),
                "sha256": sha256_file(BASELINE_PATH),
            },
            "pre_2020_membership": {
                "path": str(PRE_2020_PATH),
                "sha256": sha256_file(PRE_2020_PATH),
            },
            "modern_membership": {
                "path": str(MODERN_PATH),
                "sha256": sha256_file(MODERN_PATH),
            },
        },
        "artifacts": {
            "predictions": artifact.as_record(),
            "augmented_panel": panel_artifact.as_record(),
        },
        "limitations": [
            "Membership is a binary fact at October 15; row-level status, options, injuries, and future team are not inferred.",
            "The 2020 snapshot is unavailable and is represented as unavailable rather than as a real nonmembership observation.",
            "This challenger changes only workload and arrival models; batting-value models remain untouched until the feature earns inclusion.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
