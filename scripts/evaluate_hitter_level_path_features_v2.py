#!/usr/bin/env python3
"""Forward-test level tenure and terminal-level path features in the hitter model."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_level_path_features import (
    COMPACT_LEVEL_PATH_FEATURES,
    add_level_path_features,
    build_level_path_features,
    build_terminal_level_evidence,
)
from universal_baseball.hitter_model_tournament import run_engine_fold
from universal_baseball.hitter_target_architecture import (
    classification_metrics,
    expanding_year_folds,
    feature_columns,
    paired_cluster_rmse_delta,
    regression_metrics,
    run_lightgbm_architecture_fold,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


KEY = ["origin_year", "target_season", "player_id"]
ENGINES = ("xgboost", "ebm", "ridge")
HISTORY_YEARS = (2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024, 2025)
DEFAULT_GENERATED_ROOT = Path(
    "C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/"
    "universal-baseball-model/reports/generated"
)
DEFAULT_PANEL = Path(
    "reports/generated/hitter-value-panel-v2/tables/modeling-panel.parquet"
)
DEFAULT_BASELINE = Path(
    "reports/generated/hitter-model-finalist-tuning-v2/tables/"
    "finalist-ensemble-predictions.parquet"
)
DEFAULT_OUTPUT = Path("reports/generated/hitter-level-path-feature-ablation-v2")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-root", type=Path, default=DEFAULT_GENERATED_ROOT)
    parser.add_argument("--panel", type=Path, default=DEFAULT_PANEL)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--compact",
        action="store_true",
        help="retain only the nonredundant tenure and transition fields",
    )
    return parser.parse_args()


def _load_stats(root: Path) -> tuple[pl.DataFrame, list[Path]]:
    specifications = (
        (
            root / "affiliated-skill-source-2003-2007/tables/affiliated_hitting_components.parquet",
            range(2003, 2008),
        ),
        (
            root / "affiliated-skill-source-2008-2017/tables/affiliated_hitting_components.parquet",
            range(2008, 2018),
        ),
        (
            root / "affiliated-skill-source-2018-2022/tables/affiliated_hitting_components.parquet",
            (2018, 2019),
        ),
        (
            root / "phase2-arrival-skill-source/tables/affiliated_hitting_components.parquet",
            (2021, 2022, 2023, 2024, 2025),
        ),
    )
    frames = [
        pl.read_parquet(
            path,
            columns=["season", "player_id", "level_group", "plate_appearances"],
        ).filter(pl.col("season").is_in(list(years)))
        for path, years in specifications
    ]
    return pl.concat(frames, how="vertical_relaxed"), [path for path, _ in specifications]


def _load_contacts(root: Path) -> tuple[pl.DataFrame, list[Path]]:
    paths = [
        root / f"full-bip-context-{year}/tables/hitter_full_bip_event_outcomes.parquet"
        for year in HISTORY_YEARS
    ]
    columns = ["season", "game_pk", "at_bat_index", "player_id", "source_level"]
    return pl.concat(
        [pl.read_parquet(path, columns=columns) for path in paths],
        how="vertical_relaxed",
    ), paths


def _load_games(root: Path) -> tuple[pl.DataFrame, list[Path]]:
    paths = [
        root / "historical-affiliated-game-context/tables/historical-affiliated-game-context.parquet",
        root / "affiliated-game-context/tables/affiliated-game-context.parquet",
    ]
    return pl.concat(
        [pl.read_parquet(path, columns=["season", "game_pk", "game_date"]) for path in paths],
        how="vertical_relaxed",
    ), paths


def _add_stage(frame: pl.DataFrame, panel: pl.DataFrame) -> pl.DataFrame:
    stage = panel.select(
        "origin_year",
        "player_id",
        pl.col("lag0__highest_level").alias("current_highest_level"),
        pl.col("lag0__pa_level__MLB").alias("current_mlb_pa"),
    )
    return frame.join(stage, on=["origin_year", "player_id"], how="left").with_columns(
        pl.when(pl.col("current_mlb_pa") > 0)
        .then(pl.lit("current_mlb"))
        .when(pl.col("current_highest_level").is_in(["AA", "AAA"]))
        .then(pl.lit("upper_minors"))
        .otherwise(pl.lit("lower_minors"))
        .alias("player_stage")
    )


def _run_challenger(
    panel: pl.DataFrame,
) -> tuple[pl.DataFrame, list[dict[str, object]], dict[str, float]]:
    outputs: list[pl.DataFrame] = []
    fold_reports: list[dict[str, object]] = []
    direct_level_gain: defaultdict[str, float] = defaultdict(float)
    for fold in expanding_year_folds(panel["origin_year"].unique().to_list()):
        print(f"origin {fold.test_origin}: LightGBM architectures", flush=True)
        architecture, architecture_metrics, importance = run_lightgbm_architecture_fold(
            panel, fold, random_state=417
        )
        for name, gain in importance.items():
            if name.startswith("level_path__"):
                direct_level_gain[name] += float(gain)
        members = [
            architecture["prediction_direct"].to_numpy(),
            architecture["prediction_three_part"].to_numpy(),
        ]
        probabilities = [architecture["active_probability"].to_numpy()]
        engine_metrics: dict[str, object] = {}
        for engine in ENGINES:
            print(f"origin {fold.test_origin}: {engine}", flush=True)
            result, metrics = run_engine_fold(
                panel, fold, engine, random_state=417, variant="balanced"
            )
            members.append(result["predicted_component_war"].to_numpy())
            probabilities.append(result["active_probability"].to_numpy())
            engine_metrics[engine] = metrics
        outputs.append(
            architecture.select(*KEY, "actual_active", "actual_component_war").with_columns(
                pl.Series("challenger_prediction", np.mean(members, axis=0)),
                pl.Series(
                    "challenger_active_probability", np.mean(probabilities, axis=0)
                ),
            )
        )
        fold_reports.append(
            {
                "test_origin": fold.test_origin,
                "train_origins": list(fold.train_origins),
                "architecture_metrics": architecture_metrics,
                "engine_metrics": engine_metrics,
            }
        )
    return pl.concat(outputs).sort(KEY), fold_reports, dict(direct_level_gain)


def _metrics(frame: pl.DataFrame, prediction: str) -> dict[str, float]:
    return regression_metrics(
        frame["actual_component_war"].to_numpy(), frame[prediction].to_numpy()
    )


def _subgroups(frame: pl.DataFrame) -> dict[str, object]:
    expressions = {
        "current_mlb": pl.col("player_stage") == "current_mlb",
        "upper_minors": pl.col("player_stage") == "upper_minors",
        "lower_minors": pl.col("player_stage") == "lower_minors",
        "same_primary_repeat": pl.col("level_path__same_primary_as_prior") == 1,
        "substantial_same_level_repeat": pl.col("level_path__substantial_same_level_repeat") == 1,
        "third_or_later_at_level": pl.col("level_path__third_or_later_at_primary") == 1,
        "returned_after_partial_promotion": pl.col("level_path__returned_after_partial_promotion") == 1,
        "below_previous_peak": pl.col("level_path__below_previous_peak") == 1,
    }
    result: dict[str, object] = {}
    for label, expression in expressions.items():
        subset = frame.filter(expression)
        if subset.is_empty():
            continue
        result[label] = {
            "rows": subset.height,
            "players": subset["player_id"].n_unique(),
            "actual_active_rate": float(subset["actual_active"].mean()),
            "baseline_active_probability": float(subset["baseline_active_probability"].mean()),
            "challenger_active_probability": float(subset["challenger_active_probability"].mean()),
            "baseline": _metrics(subset, "baseline_prediction"),
            "challenger": _metrics(subset, "challenger_prediction"),
        }
    return result


def main() -> int:
    args = _args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    table_root.mkdir(exist_ok=True)

    stats, stat_paths = _load_stats(args.generated_root)
    contacts, contact_paths = _load_contacts(args.generated_root)
    games, game_paths = _load_games(args.generated_root)
    terminal = build_terminal_level_evidence(contacts, games)
    level_features = build_level_path_features(stats, terminal)
    base_panel = pl.read_parquet(args.panel)
    challenger_panel = add_level_path_features(base_panel, level_features)
    if args.compact:
        challenger_panel = challenger_panel.drop(
            column
            for column in challenger_panel.columns
            if column.startswith("level_path__")
            and column not in COMPACT_LEVEL_PATH_FEATURES
        )

    write_canonical_parquet(
        terminal,
        table_root / "terminal-level-evidence.parquet",
        table_name="hitter_level_path_v2_terminal_evidence",
    )
    feature_artifact = write_canonical_parquet(
        level_features,
        table_root / "level-path-features.parquet",
        table_name="hitter_level_path_v2_features",
    )
    panel_artifact = write_canonical_parquet(
        challenger_panel,
        table_root / "modeling-panel.parquet",
        table_name="hitter_level_path_v2_modeling_panel",
    )

    challenger, fold_reports, importance = _run_challenger(challenger_panel)
    baseline = (
        pl.read_parquet(args.baseline)
        .select(
            *KEY,
            "actual_active",
            "actual_component_war",
            pl.col("prediction_candidate_equal_mean").alias("baseline_prediction"),
            pl.col("prediction_candidate_mlb_active_probability").alias(
                "baseline_active_probability"
            ),
        )
        .sort(KEY)
    )
    comparison = challenger.join(
        baseline,
        on=KEY + ["actual_active", "actual_component_war"],
        how="inner",
        validate="1:1",
    )
    if comparison.height != baseline.height or comparison.height != challenger.height:
        raise ValueError("baseline and level-path challenger keys do not align")
    comparison = _add_stage(comparison, challenger_panel).join(
        challenger_panel.select(
            "origin_year",
            "player_id",
            *[
                column
                for column in challenger_panel.columns
                if column.startswith("level_path__")
            ],
        ),
        on=["origin_year", "player_id"],
        how="left",
        validate="1:1",
    )
    actual = comparison["actual_component_war"].to_numpy()
    challenger_prediction = comparison["challenger_prediction"].to_numpy()
    baseline_prediction = comparison["baseline_prediction"].to_numpy()
    paired = paired_cluster_rmse_delta(
        actual,
        challenger_prediction,
        baseline_prediction,
        comparison["player_id"].to_numpy(),
    )
    baseline_class = classification_metrics(
        comparison["actual_active"].to_numpy(),
        comparison["baseline_active_probability"].to_numpy(),
    )
    challenger_class = classification_metrics(
        comparison["actual_active"].to_numpy(),
        comparison["challenger_active_probability"].to_numpy(),
    )
    fold_metrics = {}
    for origin in comparison["origin_year"].unique().sort().to_list():
        subset = comparison.filter(pl.col("origin_year") == origin)
        fold_metrics[str(origin)] = {
            "baseline": _metrics(subset, "baseline_prediction"),
            "challenger": _metrics(subset, "challenger_prediction"),
        }

    prediction_artifact = write_canonical_parquet(
        comparison,
        table_root / "predictions.parquet",
        table_name="hitter_level_path_v2_predictions",
    )
    top_importance = [
        {"feature": name, "summed_direct_lightgbm_gain": gain}
        for name, gain in sorted(importance.items(), key=lambda item: item[1], reverse=True)
    ]
    report = {
        "schema_version": "0.1",
        "status": "chronological_level_path_evaluation_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "question": (
            "Do exposure-weighted years at level, terminal level, partial promotion, "
            "repeat, demotion, and advancement-speed features improve next-season "
            "zero-inclusive MLB batting-plus-replacement WAR?"
        ),
        "feature_variant": "compact" if args.compact else "full",
        "base_feature_count": len(feature_columns(base_panel)),
        "challenger_feature_count": len(feature_columns(challenger_panel)),
        "level_path_feature_count": len(
            [column for column in challenger_panel.columns if column.startswith("level_path__")]
        ),
        "terminal_evidence_rows": terminal.height,
        "level_feature_rows": level_features.height,
        "baseline": _metrics(comparison, "baseline_prediction"),
        "challenger": _metrics(comparison, "challenger_prediction"),
        "challenger_minus_baseline": paired,
        "active_probability": {
            "baseline": baseline_class,
            "challenger": challenger_class,
            "brier_delta": challenger_class["brier"] - baseline_class["brier"],
            "log_loss_delta": challenger_class["log_loss"] - baseline_class["log_loss"],
        },
        "folds": fold_metrics,
        "subgroups": _subgroups(comparison),
        "top_level_path_direct_lightgbm_importance": top_importance,
        "fold_fit_details": fold_reports,
        "decision_rule": (
            "Do not change the frozen 2026 forecast. Retain for the next development "
            "forecast only if pooled RMSE improves without being driven solely by one "
            "season, arrival scoring is not materially degraded, and repeat-player "
            "diagnostics behave sensibly."
        ),
        "sources": [
            {"path": str(path), "sha256": sha256_file(path)}
            for path in [*stat_paths, *contact_paths, *game_paths, args.panel, args.baseline]
        ],
        "artifacts": {
            "features": feature_artifact.as_record(),
            "panel": panel_artifact.as_record(),
            "predictions": prediction_artifact.as_record(),
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "baseline": report["baseline"],
                "challenger": report["challenger"],
                "challenger_minus_baseline": paired,
                "active_probability": report["active_probability"],
                "folds": fold_metrics,
                "subgroups": report["subgroups"],
                "top_level_path_importance": top_importance[:12],
            },
            indent=2,
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
