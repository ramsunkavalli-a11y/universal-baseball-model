#!/usr/bin/env python3
"""Materialize and fit Hitter v2 Stage 2f H0 without evaluation access."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.chadwick import (
    build_mlbam_age_as_of,
    read_chadwick_people_archive,
)
from universal_baseball.hitter_v2_stage2f_fit import (
    H0FitSurfaces,
    apply_surfaces_to_predictions,
    build_calibration_origins,
    fit_h0_surfaces,
    latest_player_context,
    materialize_h0_fit_sources,
    wrap_baseline_predictions,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


FOLDS = {"V2022": 2022, "V2023": 2023, "V2024": 2024}
FIT_ONLY_SENTINEL = {
    "component_prior_pa": 800.0,
    "translation_prior_mover_pa": 1000.0,
    "development_prior_sd": 0.05,
    "calibration_prior_sd": 0.1,
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
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
        "--prescore-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-prescore/tables"),
    )
    parser.add_argument(
        "--c1-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-c1-prescore/tables"),
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
        default=Path("reports/generated/hitter-v2-stage2f-H0-fit"),
    )
    return parser.parse_args()


def _historical_ages(people: pl.DataFrame, player_games: pl.DataFrame) -> pl.DataFrame:
    frames = []
    for season in sorted(int(value) for value in player_games["season"].unique()):
        players = (
            player_games.filter(pl.col("season") == season)["player_id"]
            .unique()
            .to_list()
        )
        frames.append(
            build_mlbam_age_as_of(
                people, players, as_of_date=date(season, 7, 1)
            ).with_columns(pl.lit(season).alias("season"))
        )
    return pl.concat(frames, how="vertical_relaxed").select(
        "player_id", "season", "birth_date", "age_years", "age_source_status"
    )


def _write(
    frame: pl.DataFrame,
    root: Path,
    fold: str,
    name: str,
) -> dict[str, str | int]:
    artifact = write_canonical_parquet(
        frame,
        root / "tables" / fold.lower() / f"{name}.parquet",
        table_name=f"hitter_v2_stage2f_{fold.lower()}_{name}",
    )
    return artifact.as_record()


def _probability_health(frame: pl.DataFrame) -> dict[str, object]:
    columns = [column for column in frame.columns if column.startswith("p_")]
    sums = frame.select(pl.sum_horizontal(*columns).alias("probability_sum"))[
        "probability_sum"
    ]
    return {
        "rows": frame.height,
        "all_finite": all(
            frame.select(pl.col(column).is_finite().all() for column in columns).row(0)
        ),
        "all_nonnegative": all(
            frame.select((pl.col(column) >= 0.0).all() for column in columns).row(0)
        ),
        "maximum_simplex_error": float((sums - 1.0).abs().max()),
    }


def main() -> int:
    args = _parse_args()
    player_games_all = pl.read_parquet(args.player_games).filter(
        pl.col("modeling_eligible")
    )
    park_context_all = pl.read_parquet(args.park_context)
    people = read_chadwick_people_archive(args.register_archive)
    prior_precal: pl.DataFrame | None = None
    prior_surfaces: H0FitSurfaces | None = None
    prior_target_season: int | None = None
    fold_reports: list[dict[str, object]] = []

    for fold_id, target_season in FOLDS.items():
        cutoff = target_season - 1
        slug = fold_id.lower()
        training_path = (
            args.prescore_root / slug / "training_player_league_seasons.parquet"
        )
        forecast_path = args.prescore_root / slug / "forecast_population.parquet"
        age_path = args.age_root / slug / "forecast_player_ages.parquet"
        park_offsets_path = args.c1_root / slug / "park_offsets.parquet"
        base_paths = {
            model: args.c1_root / slug / f"{model}_unscored_predictions.parquet"
            for model in ("b0", "b1", "c0")
        }

        training = pl.read_parquet(training_path)
        forecast = pl.read_parquet(forecast_path)
        forecast_ages = pl.read_parquet(age_path)
        player_games = player_games_all.filter(pl.col("season") <= cutoff)
        park_context = park_context_all.filter(pl.col("season") <= cutoff)
        park_offsets = pl.read_parquet(park_offsets_path)
        historical_ages = _historical_ages(people, player_games)
        sources = materialize_h0_fit_sources(
            training,
            player_games,
            park_context,
            park_offsets,
            historical_ages,
            predictor_cutoff_season=cutoff,
            component_prior_pa=FIT_ONLY_SENTINEL["component_prior_pa"],
        )
        calibration_origins = None
        if (
            prior_precal is not None
            and prior_surfaces is not None
            and prior_surfaces.translation is not None
            and prior_target_season is not None
        ):
            calibration_origins = build_calibration_origins(
                prior_precal,
                sources.player_seasons,
                prior_surfaces.translation,
                target_season=prior_target_season,
            )
        surfaces = fit_h0_surfaces(
            sources,
            predictor_cutoff_season=cutoff,
            translation_prior_mover_pa=FIT_ONLY_SENTINEL["translation_prior_mover_pa"],
            development_prior_sd=FIT_ONLY_SENTINEL["development_prior_sd"],
            calibration_prior_sd=FIT_ONLY_SENTINEL["calibration_prior_sd"],
            calibration_origins=calibration_origins,
        )
        context = latest_player_context(sources.player_seasons)
        c0 = pl.read_parquet(base_paths["c0"])
        if set(c0["player_id"].to_list()) != set(forecast["player_id"].to_list()):
            raise ValueError(
                "C0 fit population differs from frozen forecast population"
            )
        precal = apply_surfaces_to_predictions(
            c0,
            context,
            forecast_ages,
            surfaces,
            include_calibration=False,
            model_id="H0_NEUTRAL_HIERARCHICAL_OUTCOMES_PRECAL",
        )
        h0 = apply_surfaces_to_predictions(
            c0,
            context,
            forecast_ages,
            surfaces,
            include_calibration=True,
            model_id="H0_NEUTRAL_HIERARCHICAL_OUTCOMES",
        )
        wrapped = {
            model: wrap_baseline_predictions(
                pl.read_parquet(path),
                context,
                surfaces.translation,
                model_id=f"REFERENCE_WRAPPED_{model.upper()}",
            )
            for model, path in base_paths.items()
        }

        artifacts = {
            "player_seasons": _write(
                sources.player_seasons, args.report_root, fold_id, "player_seasons"
            ),
            "adjacent_pairs": _write(
                sources.adjacent_pairs, args.report_root, fold_id, "adjacent_pairs"
            ),
            "translation_pairs": _write(
                sources.translation_pairs,
                args.report_root,
                fold_id,
                "translation_pairs",
            ),
            "h0_precal_predictions": _write(
                precal, args.report_root, fold_id, "h0_precal_predictions"
            ),
            "h0_predictions": _write(h0, args.report_root, fold_id, "h0_predictions"),
            **{
                f"reference_wrapped_{model}": _write(
                    frame,
                    args.report_root,
                    fold_id,
                    f"reference_wrapped_{model}",
                )
                for model, frame in wrapped.items()
            },
        }
        if surfaces.translation is not None:
            artifacts.update(
                {
                    "translation_edges": _write(
                        surfaces.translation.edges,
                        args.report_root,
                        fold_id,
                        "translation_edges",
                    ),
                    "translation_offsets": _write(
                        surfaces.translation.offsets,
                        args.report_root,
                        fold_id,
                        "translation_offsets",
                    ),
                    "development_pairs": _write(
                        surfaces.development_pairs,
                        args.report_root,
                        fold_id,
                        "development_pairs",
                    ),
                    "development_coefficients": _write(
                        surfaces.development.coefficients,
                        args.report_root,
                        fold_id,
                        "development_coefficients",
                    ),
                    "development_transforms": _write(
                        surfaces.development.transforms,
                        args.report_root,
                        fold_id,
                        "development_transforms",
                    ),
                }
            )
        if surfaces.calibration is not None:
            artifacts.update(
                {
                    "calibration_origins": _write(
                        surfaces.calibration_origins,
                        args.report_root,
                        fold_id,
                        "calibration_origins",
                    ),
                    "calibration_coefficients": _write(
                        surfaces.calibration.coefficients,
                        args.report_root,
                        fold_id,
                        "calibration_coefficients",
                    ),
                }
            )

        path_counts = (
            h0.group_by("translation_path_quality")
            .len()
            .sort("translation_path_quality")
            .to_dicts()
        )
        fold_reports.append(
            {
                "fold_id": fold_id,
                "target_season_label_only": target_season,
                "predictor_cutoff_season": cutoff,
                "predictor_max_season": int(training["season"].max()),
                "forecast_players": forecast.height,
                "player_seasons": sources.player_seasons.height,
                "adjacent_pairs": sources.adjacent_pairs.height,
                "translation_pair_rows": sources.translation_pairs.height,
                "development_pair_rows": surfaces.development_pairs.height,
                "calibration_origin_rows": surfaces.calibration_origins.height,
                "translation_fitted": surfaces.translation is not None,
                "development_fitted": surfaces.development is not None,
                "calibration_fitted": surfaces.calibration is not None,
                "translation_path_counts": path_counts,
                "probability_health": _probability_health(h0),
                "forecast_population_unchanged": set(h0["player_id"].to_list())
                == set(forecast["player_id"].to_list()),
                "inputs": {
                    "training_sha256": sha256_file(training_path),
                    "forecast_population_sha256": sha256_file(forecast_path),
                    "forecast_ages_sha256": sha256_file(age_path),
                    "park_offsets_sha256": sha256_file(park_offsets_path),
                    **{
                        f"{model}_predictions_sha256": sha256_file(path)
                        for model, path in base_paths.items()
                    },
                },
                "artifacts": artifacts,
                "validation_outcomes_loaded": False,
                "candidate_metrics_computed": False,
            }
        )
        prior_precal = precal
        prior_surfaces = surfaces
        prior_target_season = target_season

    report = {
        "schema_version": "0.1",
        "program": "hitter_v2",
        "stage": "2f_H0_fit_only",
        "status": "real_historical_predictor_sources_materialized_and_sentinel_fit_complete",
        "configuration_role": "non_decisional_conservative_fit_sentinel",
        "configuration": FIT_ONLY_SENTINEL,
        "source_audit": {
            "player_games_path": str(args.player_games),
            "player_games_sha256": sha256_file(args.player_games),
            "park_context_path": str(args.park_context),
            "park_context_sha256": sha256_file(args.park_context),
            "register_archive_sha256": sha256_file(args.register_archive),
            "source_reacquired": False,
        },
        "folds": fold_reports,
        "validation_outcomes_loaded": False,
        "candidate_metrics_computed": False,
        "candidate_comparators_scored": False,
        "protected_2026_opened": False,
        "H1_fit": False,
        "next_gate": "review_fit_only_checkpoint_then_explicitly_authorize_training_origin_configuration_selection_and_final_parameter_freeze_without_validation_outcome_loading",
    }
    args.report_root.mkdir(parents=True, exist_ok=True)
    report_path = args.report_root / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"report": str(report_path), "folds": len(fold_reports)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
