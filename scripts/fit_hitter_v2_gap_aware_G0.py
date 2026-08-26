#!/usr/bin/env python3
"""Fit G0 from predictor history only; target outcomes are never loaded."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_v2_gap_aware import assemble_gap_aware_history
from universal_baseball.hitter_v2_model import NESTED_NODES, predict_c0_nested_eb
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.storage import sha256_file, write_canonical_parquet


FOLDS = {"V2022": 2021, "V2023": 2022, "V2024": 2023}


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prescore-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-prescore/tables"),
    )
    parser.add_argument(
        "--c0-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-final-validation/tables"),
    )
    parser.add_argument(
        "--milb-2019",
        type=Path,
        default=Path("reports/generated/hitter-v2-historical-materialization/milb/tables/hitter_v2_player_season_outcomes_2019_milb.parquet"),
    )
    parser.add_argument(
        "--mlb-2019-2020",
        type=Path,
        default=Path("reports/generated/hitter-v2-gap-aware-history/mlb/tables/hitter_v2_historical_mlb_outcomes_2019_2020.parquet"),
    )
    parser.add_argument(
        "--selection-record",
        type=Path,
        default=Path("docs/hitter-v2-stage2-component-selection-result.json"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-gap-aware-G0-fit"),
    )
    return parser.parse_args()


def _parameters(record: dict[str, object], fold: str) -> tuple[dict[str, float], dict[str, float]]:
    row = record["folds"][fold]
    node_names = [node.name for node in NESTED_NODES]
    if "selected" not in row:
        default = row["all_components"]
        return (
            {name: float(default["half_life_seasons"]) for name in node_names},
            {name: float(default["component_prior_pa"]) for name in node_names},
        )
    selected = row["selected"]
    return (
        {name: float(selected[name]["half_life_seasons"]) for name in node_names},
        {name: float(selected[name]["component_prior_pa"]) for name in node_names},
    )


def _probability_health(frame: pl.DataFrame) -> dict[str, object]:
    columns = [f"p_{outcome}" for outcome in HITTER_TALENT_OUTCOMES]
    sums = frame.select(pl.sum_horizontal(*columns).alias("sum"))["sum"]
    return {
        "rows": frame.height,
        "all_finite": all(frame.select(pl.col(c).is_finite().all() for c in columns).row(0)),
        "all_nonnegative": all(frame.select((pl.col(c) >= 0).all() for c in columns).row(0)),
        "maximum_simplex_error": float((sums - 1.0).abs().max()),
    }


def main() -> int:
    args = _args()
    milb = pl.read_parquet(args.milb_2019)
    mlb = pl.read_parquet(args.mlb_2019_2020)
    selection = json.loads(args.selection_record.read_text(encoding="utf-8"))
    fold_reports = []
    for fold, cutoff in FOLDS.items():
        slug = fold.lower()
        base_path = args.prescore_root / slug / "training_player_league_seasons.parquet"
        forecast_path = args.prescore_root / slug / "forecast_population.parquet"
        frozen_c0_path = args.c0_root / slug / "c0_nested_eb_predictions.parquet"
        base = pl.read_parquet(base_path)
        forecast = pl.read_parquet(forecast_path)
        frozen_c0 = pl.read_parquet(frozen_c0_path).sort("player_id")
        history = assemble_gap_aware_history(
            base, milb, mlb, predictor_cutoff_season=cutoff
        )
        half_lives, priors = _parameters(selection, fold)
        recomputed_c0 = predict_c0_nested_eb(
            base,
            forecast["player_id"].to_list(),
            predictor_cutoff_season=cutoff,
            half_life_seasons=half_lives,
            component_prior_pa=priors,
        ).sort("player_id")
        probability_columns = [f"p_{outcome}" for outcome in HITTER_TALENT_OUTCOMES]
        baseline_delta = recomputed_c0.join(
            frozen_c0.select("player_id", *probability_columns),
            on="player_id",
            how="inner",
            suffix="_frozen",
        ).select(
            pl.max_horizontal(
                *[
                    (pl.col(column) - pl.col(f"{column}_frozen")).abs()
                    for column in probability_columns
                ]
            ).max().alias("delta")
        ).item()
        if float(baseline_delta) > 1e-12:
            raise RuntimeError(f"{fold} recomputed C0 differs from frozen C0")
        g0 = predict_c0_nested_eb(
            history,
            forecast["player_id"].to_list(),
            predictor_cutoff_season=cutoff,
            half_life_seasons=half_lives,
            component_prior_pa=priors,
        ).with_columns(pl.lit("G0_GAP_AWARE_HISTORICAL_C0").alias("model_id"))
        if set(g0["player_id"]) != set(forecast["player_id"]):
            raise RuntimeError(f"{fold} G0 changed the frozen forecast population")
        fold_root = args.report_root / "tables" / slug
        history_artifact = write_canonical_parquet(
            history,
            fold_root / "gap_aware_training_history.parquet",
            table_name=f"hitter_v2_{slug}_gap_aware_training_history",
        ).as_record()
        prediction_artifact = write_canonical_parquet(
            g0.sort("player_id"),
            fold_root / "g0_unscored_predictions.parquet",
            table_name=f"hitter_v2_{slug}_g0_unscored_predictions",
        ).as_record()
        support = (
            history.group_by("history_source")
            .agg(
                pl.col("player_id").n_unique().alias("players"),
                pl.col("hitter_talent_pa").sum().alias("hitter_talent_pa"),
            )
            .sort("history_source")
            .to_dicts()
        )
        fold_reports.append(
            {
                "fold": fold,
                "predictor_cutoff_season": cutoff,
                "forecast_players": forecast.height,
                "history_support": support,
                "2020_milb_rows": history.filter(
                    (pl.col("season") == 2020) & (pl.col("level_group") != "MLB")
                ).height,
                "recomputed_C0_maximum_probability_delta": float(baseline_delta),
                "probability_health": _probability_health(g0),
                "parameters": {"half_life_seasons": half_lives, "component_prior_pa": priors},
                "storage": {
                    "history": history_artifact,
                    "predictions": prediction_artifact,
                },
            }
        )
    report = {
        "report_schema_version": "0.1",
        "status": "G0_target_free_fit_complete_unscored",
        "model_id": "G0_GAP_AWARE_HISTORICAL_C0",
        "candidate_fit": True,
        "candidate_scored": False,
        "target_outcomes_loaded": False,
        "protected_2026_opened": False,
        "hyperparameter_search": False,
        "sources": {
            "milb_2019": {"path": str(args.milb_2019), "sha256": sha256_file(args.milb_2019)},
            "mlb_2019_2020": {"path": str(args.mlb_2019_2020), "sha256": sha256_file(args.mlb_2019_2020)},
            "selection_record": {"path": str(args.selection_record), "sha256": sha256_file(args.selection_record)},
        },
        "folds": fold_reports,
        "next_gate": "freeze_implementation_and_one_shot_disclosed_scorer_before_scoring",
    }
    args.report_root.mkdir(parents=True, exist_ok=True)
    (args.report_root / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
