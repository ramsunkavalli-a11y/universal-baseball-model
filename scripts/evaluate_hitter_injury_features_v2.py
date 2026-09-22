#!/usr/bin/env python3
"""Test offseason injury history above the roster-aware hitter workload model."""

from __future__ import annotations

from datetime import UTC, date, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.historical_injury_features import (
    FEATURE_COLUMNS,
    build_historical_injury_features,
    load_injury_events,
)
from universal_baseball.hitter_target_architecture import (
    classification_metrics,
    expanding_year_folds,
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.hitter_workload import run_workload_fold
from universal_baseball.storage import sha256_file, write_canonical_parquet


PANEL_PATH = Path(
    "reports/generated/hitter-roster-feature-challenger-v2/"
    "modeling-panel-with-roster.parquet"
)
BASELINE_PATH = Path(
    "reports/generated/hitter-roster-feature-challenger-v2/"
    "chronological-predictions.parquet"
)
SOURCE_ROOT = Path("reports/generated/hitter-injury-history-v2/source")
SOURCE_2015_ROOT = Path("reports/generated/hitter-injury-history-v2/source-2015")
OUTPUT_ROOT = Path("reports/generated/hitter-injury-feature-challenger-v2")
ENGINES = ("lightgbm", "xgboost", "ebm", "ridge")
KEY = ["origin_year", "target_season", "player_id"]


def _capture_paths() -> list[Path]:
    paths = sorted((SOURCE_ROOT / "captures").glob("transactions-*.json"))
    paths.extend(sorted((SOURCE_2015_ROOT / "captures").glob("transactions-*.json")))
    years = {int(path.stem.rsplit("-", 1)[1]) for path in paths}
    expected = set(range(2015, 2025))
    if years != expected:
        raise RuntimeError(
            f"injury transaction capture years differ: missing={sorted(expected - years)}"
        )
    return sorted(paths)


def _augment(panel: pl.DataFrame, features: pl.DataFrame) -> pl.DataFrame:
    first_source = date(2015, 1, 1)
    result = panel.join(
        features,
        on=["origin_year", "player_id"],
        how="left",
        validate="1:1",
    ).with_columns(
        *[pl.col(column).fill_null(0).cast(pl.Int64) for column in FEATURE_COLUMNS]
    )
    return result.with_columns(
        pl.col("origin_year")
        .map_elements(
            lambda year: min(
                730,
                (date(int(year), 10, 15) - first_source).days + 1,
            ),
            return_dtype=pl.Int64,
        )
        .alias("injury__history_days_available"),
        pl.lit(1, dtype=pl.Int8).alias("injury__source_available"),
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
                f"fitting injury workload {engine} origin {fold.test_origin}",
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
            [frame["active_probability"].to_numpy() for frame in engine_predictions.values()]
        ),
        axis=1,
    )
    output = reference.select(KEY + ["actual_active", "actual_pa"]).with_columns(
        pl.Series("prediction_injury_expected_pa", expected_pa),
        pl.Series("prediction_injury_active_probability", active_probability),
        *[
            pl.Series(f"prediction_injury_member__{name}", prediction)
            for name, prediction in members.items()
        ],
    )
    return output, engine_reports


def _segment_metrics(frame: pl.DataFrame) -> dict[str, object]:
    actual = frame["actual_pa"].to_numpy()
    baseline = frame["prediction_roster_expected_pa"].to_numpy()
    challenger = frame["prediction_injury_expected_pa"].to_numpy()
    return {
        "rows": frame.height,
        "actual_active_rate": float(frame["actual_active"].mean()),
        "baseline": regression_metrics(actual, baseline),
        "injury_challenger": regression_metrics(actual, challenger),
        "challenger_minus_baseline_rmse": (
            regression_metrics(actual, challenger)["rmse"]
            - regression_metrics(actual, baseline)["rmse"]
        ),
    }


def main() -> None:
    capture_paths = _capture_paths()
    events = load_injury_events(capture_paths)
    base_panel = pl.read_parquet(PANEL_PATH)
    features = build_historical_injury_features(
        events,
        origin_years=base_panel["origin_year"].unique().to_list(),
    )
    panel = _augment(base_panel, features)
    predictions, engine_reports = _fit_candidate(panel)
    baseline = pl.read_parquet(BASELINE_PATH).select(
        *KEY,
        "prediction_roster_expected_pa",
        "prediction_roster_active_probability",
    )
    context = panel.select(
        "origin_year",
        "player_id",
        *FEATURE_COLUMNS,
        "injury__history_days_available",
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
        raise RuntimeError("injury challenger and roster baseline populations differ")

    actual_pa = frame["actual_pa"].to_numpy()
    actual_active = frame["actual_active"].to_numpy()
    old_pa = frame["prediction_roster_expected_pa"].to_numpy()
    new_pa = frame["prediction_injury_expected_pa"].to_numpy()
    old_active = frame["prediction_roster_active_probability"].to_numpy()
    new_active = frame["prediction_injury_active_probability"].to_numpy()
    by_origin = {
        str(origin): _segment_metrics(frame.filter(pl.col("origin_year") == origin))
        for origin in sorted(frame["origin_year"].unique().to_list())
    }
    by_stage = {
        stage: _segment_metrics(frame.filter(pl.col("player_stage") == stage))
        for stage in ("current_mlb", "upper_minors", "lower_minors")
    }
    by_history = {
        "any_injury_last_730_days": _segment_metrics(
            frame.filter(pl.col("injury__days_730") > 0)
        ),
        "no_injury_last_730_days": _segment_metrics(
            frame.filter(pl.col("injury__days_730") == 0)
        ),
        "on_injury_list_at_cutoff": _segment_metrics(
            frame.filter(pl.col("injury__on_list_at_cutoff") == 1)
        ),
        "not_on_injury_list_at_cutoff": _segment_metrics(
            frame.filter(pl.col("injury__on_list_at_cutoff") == 0)
        ),
    }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        frame,
        OUTPUT_ROOT / "chronological-predictions.parquet",
        table_name="hitter_injury_feature_challenger_v2_predictions",
    )
    panel_artifact = write_canonical_parquet(
        panel,
        OUTPUT_ROOT / "modeling-panel-with-injury.parquet",
        table_name="hitter_value_panel_v2_with_roster_and_injury",
    )
    events_artifact = write_canonical_parquet(
        events,
        OUTPUT_ROOT / "historical-injury-events-2015-2024.parquet",
        table_name="historical_injury_events_2015_2024",
    )
    report = {
        "schema_version": "0.1",
        "status": "hitter_offseason_injury_feature_test_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "population_rows": frame.height,
        "target": "next-season zero-inclusive MLB plate appearances and MLB participation",
        "baseline": "selected roster-aware workload model",
        "features": list(FEATURE_COLUMNS)
        + ["injury__history_days_available", "injury__source_available"],
        "playing_time": {
            "roster_baseline": regression_metrics(actual_pa, old_pa),
            "injury_challenger": regression_metrics(actual_pa, new_pa),
            "paired_challenger_minus_baseline": paired_cluster_rmse_delta(
                actual_pa,
                new_pa,
                old_pa,
                frame["player_id"].to_numpy(),
            ),
        },
        "active_probability": {
            "roster_baseline": classification_metrics(actual_active, old_active),
            "injury_challenger": classification_metrics(actual_active, new_active),
        },
        "by_origin": by_origin,
        "by_player_stage": by_stage,
        "by_injury_history": by_history,
        "coverage": {
            "recognized_events": events.height,
            "players_with_recognized_events": events["player_id"].n_unique(),
            "prediction_rows_with_injury_days_730": int(
                frame.filter(pl.col("injury__days_730") > 0).height
            ),
            "prediction_rows_on_list_at_cutoff": int(
                frame.filter(pl.col("injury__on_list_at_cutoff") == 1).height
            ),
            "disabled_list_era_supported": True,
            "injured_list_era_supported": True,
        },
        "engine_fold_reports": engine_reports,
        "sources": {
            "panel": {"path": str(PANEL_PATH), "sha256": sha256_file(PANEL_PATH)},
            "baseline": {
                "path": str(BASELINE_PATH),
                "sha256": sha256_file(BASELINE_PATH),
            },
            "transaction_captures": [
                {"path": str(path), "sha256": sha256_file(path)}
                for path in capture_paths
            ],
        },
        "artifacts": {
            "predictions": artifact.as_record(),
            "augmented_panel": panel_artifact.as_record(),
            "events": events_artifact.as_record(),
        },
        "limitations": [
            "Features use broad injured-list placement, transfer, and activation semantics; diagnosis is not inferred.",
            "The 2015 origin has only January-to-October history; explicit history-availability days distinguish it from later origins.",
            "An open spell is capped at calendar-year end so offseason days are not counted as injured playing days.",
            "Transactions can miss non-affiliated or unrecorded injuries; missing events mean no public transaction evidence, not proof of perfect health.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "playing_time": report["playing_time"],
                "active_probability": report["active_probability"],
                "coverage": report["coverage"],
                "by_injury_history": by_history,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
