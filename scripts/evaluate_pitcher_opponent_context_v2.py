#!/usr/bin/env python3
"""Test exact prior opponent quality in the clean-slate pitcher value model."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.historical_battery_support import (
    classify_battery_plate_appearances,
)
from universal_baseball.historical_matchup_profiles import (
    PROFILE_SPECS,
    add_matchup_outcomes,
    build_prior_profiles,
    build_prior_split_profiles,
)
from universal_baseball.hitter_target_architecture import (
    expanding_year_folds,
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.pitcher_model_tournament import run_pitcher_engine_fold
from universal_baseball.pitcher_opponent_context import (
    OPPONENT_CONTEXT_COLUMNS,
    add_neutral_opponent_context,
    aggregate_pitcher_opponent_context,
)
from universal_baseball.pitcher_value_panel import MODEL_ORIGINS, build_pitcher_value_panel
from universal_baseball.storage import write_canonical_parquet


BASE_ROOT = Path("reports/generated/pitcher-value-panel-v2")
PBP_ROOT = Path("data/working/pbp-opportunity-foundation-v1")
OUTPUT_ROOT = Path("reports/generated/pitcher-opponent-context-v2")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pbp-root", type=Path, default=PBP_ROOT)
    parser.add_argument("--base-root", type=Path, default=BASE_ROOT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--engines", default="ridge,catboost,lightgbm")
    return parser.parse_args()


def _load_terminal(root: Path) -> pl.DataFrame:
    paths = sorted(root.glob("season=*/level=*/terminal/*.parquet"))
    columns = [
        "season",
        "level",
        "source_asset",
        "game_pk",
        "at_bat_index",
        "batter",
        "pitcher",
        "fielder_2",
        "stand",
        "p_throws",
        "park_key",
        "bb_type",
        "pa_description",
        "terminal_outcome_group",
        "terminal_outcome_status",
    ]
    return (
        pl.concat(
            [pl.read_parquet(path, columns=columns) for path in paths],
            how="diagonal_relaxed",
        )
        .sort("game_pk", "at_bat_index", "source_asset")
        .unique(subset=["game_pk", "at_bat_index"], keep="first", maintain_order=True)
    )


def _score(panel: pl.DataFrame, engine: str) -> pl.DataFrame:
    folds = expanding_year_folds(
        panel["origin_year"].unique().to_list(), minimum_train_years=8
    )
    return pl.concat(
        [run_pitcher_engine_fold(panel, fold, engine)[0] for fold in folds]
    ).sort("origin_year", "player_id")


def _metrics(frame: pl.DataFrame, column: str) -> dict[str, float]:
    return regression_metrics(
        frame["actual_component_war"].to_numpy(), frame[column].to_numpy()
    )


def main() -> int:
    args = _args()
    print("building exact opponent-quality exposures", flush=True)
    events = add_matchup_outcomes(classify_battery_plate_appearances(_load_terminal(args.pbp_root)))
    years = sorted(events["season"].unique().to_list())
    overall = build_prior_profiles(
        events,
        player_column="batter_id",
        prefix="h",
        target_seasons=years,
    )
    split = build_prior_split_profiles(
        events,
        player_column="batter_id",
        split_column="pitcher_hand",
        prefix="hs",
        overall_profiles=overall,
        target_seasons=years,
    )
    context = aggregate_pitcher_opponent_context(events, overall, split)
    stat_features = pl.read_parquet(args.base_root / "tables/pitcher-stat-features.parquet")
    targets = pl.read_parquet(args.base_root / "tables/pitcher-value-targets.parquet")
    detailed_features = add_neutral_opponent_context(stat_features, context)
    base_panel = build_pitcher_value_panel(stat_features, targets, origins=MODEL_ORIGINS)
    context_panel = build_pitcher_value_panel(
        detailed_features, targets, origins=MODEL_ORIGINS
    )

    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    report: dict[str, Any] = {
        "schema_version": "0.1",
        "status": "pitcher_opponent_context_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "feature_block": list(OPPONENT_CONTEXT_COLUMNS),
        "profile_components": list(PROFILE_SPECS),
        "event_rows": events.height,
        "pitcher_context_seasons": context.height,
        "context_years": years,
        "engines": {},
    }
    for engine in [value.strip() for value in args.engines.split(",") if value.strip()]:
        print(f"starting exact-opponent engine {engine}", flush=True)
        base = _score(base_panel, engine)
        candidate = _score(context_panel, engine)
        comparison = base.select(
            "origin_year",
            "target_season",
            "player_id",
            "actual_component_war",
            "active_probability",
            pl.col("predicted_component_war").alias("prediction_base"),
        ).join(
            candidate.select(
                "origin_year",
                "target_season",
                "player_id",
                pl.col("predicted_conditional_war").alias("context_conditional_war"),
                pl.col("predicted_component_war").alias("prediction_context"),
            ),
            on=["origin_year", "target_season", "player_id"],
            validate="1:1",
        ).with_columns(
            (pl.col("active_probability") * pl.col("context_conditional_war")).alias(
                "prediction_context_conditional_only"
            )
        ).join(
            context_panel.select(
                "origin_year",
                "player_id",
                pl.col("lag0__opponent_context_available").alias("context_available"),
            ),
            on=["origin_year", "player_id"],
            validate="1:1",
        )
        modern = comparison.filter(pl.col("origin_year").is_in([2017, 2018, 2021, 2022, 2023, 2024]))
        actual = modern["actual_component_war"].to_numpy()
        report["engines"][engine] = {
            "rows": modern.height,
            "covered_rows": int(modern["context_available"].sum()),
            "base": _metrics(modern, "prediction_base"),
            "context": _metrics(modern, "prediction_context"),
            "context_conditional_only": _metrics(
                modern, "prediction_context_conditional_only"
            ),
            "context_minus_base": paired_cluster_rmse_delta(
                actual,
                modern["prediction_context"].to_numpy(),
                modern["prediction_base"].to_numpy(),
                modern["player_id"].to_numpy(),
                bootstrap_samples=5_000,
            ),
            "context_conditional_only_minus_base": paired_cluster_rmse_delta(
                actual,
                modern["prediction_context_conditional_only"].to_numpy(),
                modern["prediction_base"].to_numpy(),
                modern["player_id"].to_numpy(),
                bootstrap_samples=5_000,
            ),
        }
        write_canonical_parquet(
            comparison,
            table_root / f"{engine}-predictions.parquet",
            table_name=f"pitcher_opponent_context_v2_{engine}_predictions",
        )
    report["context_artifact"] = write_canonical_parquet(
        context,
        table_root / "pitcher-season-context.parquet",
        table_name="pitcher_opponent_context_v2_player_seasons",
    ).as_record()
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["engines"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
