#!/usr/bin/env python3
"""Select C1 park, movement, and age grids from earlier origins only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from materialize_hitter_v2_stage2_c1_prescore import (
    _historical_ages,
    _target_age_contexts,
)
from universal_baseball.chadwick import read_chadwick_people_archive
from universal_baseball.hitter_v2_c1 import (
    estimate_player_gidp_rates,
    fit_c1_adjustments,
    predict_c1_hierarchical_pbp,
    select_c1_adjustment_hyperparameters,
)
from universal_baseball.hitter_v2_evaluation import score_hitter_predictions
from universal_baseball.hitter_v2_model import predict_c0_nested_eb
from universal_baseball.storage import sha256_file, write_canonical_parquet


FOLDS = ("V2022", "V2023", "V2024")
PARK_PRIOR_GRID = (500.0, 1000.0, 2000.0)
MOVEMENT_PRIOR_GRID = (100.0, 250.0, 500.0)
RIDGE_GRID = (1.0, 10.0, 100.0)
NO_ORIGIN_DEFAULT = {
    "park_prior_pa": 2000.0,
    "movement_prior_pa": 500.0,
    "ridge_penalty": 100.0,
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--component-selection",
        type=Path,
        default=Path("docs/hitter-v2-stage2-component-selection-result.json"),
    )
    parser.add_argument(
        "--player-games",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage1-universal/tables/"
            "hitter_v2_player_game_outcomes_2021_2023.parquet"
        ),
    )
    parser.add_argument(
        "--park-context",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage2-park-context/tables/"
            "hitter_v2_player_game_park_context_2021_2023.parquet"
        ),
    )
    parser.add_argument(
        "--gidp-history",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage2-gidp-opportunities/tables/"
            "hitter_v2_player_game_gidp_opportunities_2021_2024.parquet"
        ),
    )
    parser.add_argument(
        "--prescore-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-prescore/tables"),
    )
    parser.add_argument(
        "--age-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-age/tables"),
    )
    parser.add_argument(
        "--register-archive",
        type=Path,
        default=Path(
            "data/quarantine/hitter-v2-stage2-age/"
            "register-2e8e73355f9c77b963115377bd98c784cfeec10f.zip"
        ),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-c1-adjustment-selection"),
    )
    return parser.parse_args()


def _component_parameters(
    selection: dict[str, object], fold_id: str
) -> tuple[dict[str, float], dict[str, float]]:
    fold = selection["folds"][fold_id]
    if "all_components" in fold:
        value = fold["all_components"]
        names = (
            "plate_appearance", "non_k", "non_k_non_ubb", "contact",
            "non_hr_contact", "reach", "hit_in_play", "non_hit_reach",
            "non_reach",
        )
        selected = {name: value for name in names}
    else:
        selected = fold["selected"]
    half_lives = {
        name: float(value["half_life_seasons"])
        for name, value in selected.items()
    }
    priors = {
        name: float(value["component_prior_pa"])
        for name, value in selected.items()
    }
    return half_lives, priors


def main() -> int:
    args = _parse_args()
    selection = json.loads(args.component_selection.read_text(encoding="utf-8"))
    all_games = pl.read_parquet(args.player_games).filter(pl.col("modeling_eligible"))
    all_park = pl.read_parquet(args.park_context)
    all_gidp = pl.read_parquet(args.gidp_history)
    people = read_chadwick_people_archive(args.register_archive)
    origin_cache = {}
    for fold_id in FOLDS:
        root = args.prescore_root / fold_id.lower()
        training = pl.read_parquet(root / "training_player_league_seasons.parquet")
        forecast = pl.read_parquet(root / "forecast_population.parquet")
        target = pl.read_parquet(root / "target_players.parquet")
        forecast_ages = pl.read_parquet(
            args.age_root / fold_id.lower() / "forecast_player_ages.parquet"
        )
        cutoff = int(training["season"].max())
        half_lives, component_priors = _component_parameters(selection, fold_id)
        player_ids = [int(value) for value in forecast["player_id"].to_list()]
        c0 = predict_c0_nested_eb(
            training,
            player_ids,
            predictor_cutoff_season=cutoff,
            half_life_seasons=half_lives,
            component_prior_pa=component_priors,
        )
        games = all_games.filter(pl.col("season") <= cutoff)
        historical_ages = _historical_ages(people, games)
        gidp_rates = estimate_player_gidp_rates(
            all_gidp.filter(pl.col("season") <= cutoff),
            player_ids,
            predictor_cutoff_season=cutoff,
            half_life_seasons=half_lives["non_reach"],
            prior_pa=component_priors["non_reach"],
        )
        origin_cache[fold_id] = {
            "training": training,
            "target": target,
            "forecast_ages": forecast_ages,
            "cutoff": cutoff,
            "c0": c0,
            "games": games,
            "park": all_park.filter(pl.col("season") <= cutoff),
            "historical_ages": historical_ages,
            "gidp_rates": gidp_rates,
            "component_priors": component_priors,
        }

    fold_reports = []
    for index, fold_id in enumerate(FOLDS):
        earlier = FOLDS[:index]
        if not earlier:
            fold_reports.append(
                {
                    "fold_id": fold_id,
                    "earlier_origin_folds": [],
                    "selection_source": "no_earlier_origin_literal_tie_default",
                    "grid_rows": 0,
                    "selected": {**NO_ORIGIN_DEFAULT, "event_log_loss": None},
                    "grid_artifact": None,
                }
            )
            continue
        rows = []
        for park_prior in PARK_PRIOR_GRID:
            for movement_prior in MOVEMENT_PRIOR_GRID:
                for ridge in RIDGE_GRID:
                    weighted_loss = 0.0
                    total_pa = 0
                    details = []
                    for origin in earlier:
                        cached = origin_cache[origin]
                        fit = fit_c1_adjustments(
                            cached["games"],
                            cached["park"],
                            cached["historical_ages"],
                            predictor_cutoff_season=cached["cutoff"],
                            component_prior_pa=cached["component_priors"],
                            park_prior_pa=park_prior,
                            movement_prior_pa=movement_prior,
                            ridge_penalty=ridge,
                        )
                        age_contexts = _target_age_contexts(
                            fit.player_seasons,
                            cached["forecast_ages"],
                            predictor_cutoff_season=cached["cutoff"],
                        )
                        prediction = predict_c1_hierarchical_pbp(
                            cached["c0"],
                            cached["training"],
                            fit,
                            cached["gidp_rates"],
                            target_age_contexts=age_contexts,
                        )
                        score = score_hitter_predictions(
                            prediction, cached["target"], weighting="pa"
                        )
                        pa = int(score["target_hitter_talent_pa"])
                        loss = float(score["terminal_log_loss"])
                        weighted_loss += loss * pa
                        total_pa += pa
                        details.append(
                            {"origin_fold": origin, "pa": pa, "event_log_loss": loss}
                        )
                    rows.append(
                        {
                            "park_prior_pa": park_prior,
                            "movement_prior_pa": movement_prior,
                            "ridge_penalty": ridge,
                            "selection_pa": total_pa,
                            "event_log_loss": weighted_loss / total_pa,
                            "origin_detail_json": json.dumps(
                                details, separators=(",", ":"), sort_keys=True
                            ),
                        }
                    )
        scores = pl.DataFrame(rows)
        selected = select_c1_adjustment_hyperparameters(scores)
        artifact = write_canonical_parquet(
            scores,
            args.report_root / "tables" / fold_id.lower() / "c1_adjustment_grid_scores.parquet",
            table_name=f"hitter_v2_{fold_id.lower()}_c1_adjustment_grid_scores",
        ).as_record()
        fold_reports.append(
            {
                "fold_id": fold_id,
                "earlier_origin_folds": list(earlier),
                "selection_source": "earlier_origin_pa_weighted_terminal_log_loss",
                "grid_rows": scores.height,
                "selected": selected,
                "grid_artifact": artifact,
            }
        )

    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": 2,
        "status": "c1_adjustment_training_origin_selection_complete",
        "candidate_scored_on_training_origins": True,
        "final_validation_scored": False,
        "protected_2026_opened": False,
        "component_selection_sha256": sha256_file(args.component_selection),
        "grid": {
            "park_prior_pa": list(PARK_PRIOR_GRID),
            "movement_prior_pa": list(MOVEMENT_PRIOR_GRID),
            "ridge_penalty": list(RIDGE_GRID),
        },
        "folds": fold_reports,
    }
    args.report_root.mkdir(parents=True, exist_ok=True)
    report_path = args.report_root / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
