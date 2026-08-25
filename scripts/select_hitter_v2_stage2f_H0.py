#!/usr/bin/env python3
"""Select and freeze Hitter v2 Stage 2f H0 on earlier origins only."""

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
from universal_baseball.hitter_v2_model import (
    NESTED_NODES,
    predict_b0_one_year_eb,
    predict_b1_marcel_345_k1200,
    predict_c0_nested_eb,
    select_component_hyperparameters,
)
from universal_baseball.hitter_v2_stage2f_fit import (
    H0FitSources,
    apply_surfaces_to_predictions,
    fit_h0_surfaces,
    latest_player_context,
    materialize_h0_fit_sources,
    wrap_baseline_predictions,
)
from universal_baseball.hitter_v2_stage2f_selection import (
    aggregate_training_origin_target,
    backtranslate_predictions_to_scoring_level,
    build_reference_calibration_rows,
    nested_selection_scores,
    select_surface_configuration,
    selected_component_maps,
    translate_training_origin_target,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


FOLDS = {"V2022": 2022, "V2023": 2023, "V2024": 2024}
HALF_LIFE_GRID = (1.0, 2.0, 3.0)
COMPONENT_PRIOR_GRID = (100.0, 200.0, 400.0, 800.0)
TRANSLATION_PRIOR_GRID = (250.0, 500.0, 1000.0)
DEVELOPMENT_PRIOR_GRID = (0.05, 0.1)
CALIBRATION_PRIOR_GRID = (0.1, 0.2)
NO_ORIGIN_COMPONENT_DEFAULT = {
    "half_life_seasons": 3.0,
    "component_prior_pa": 800.0,
    "event_log_loss": None,
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
        default=Path("reports/generated/hitter-v2-stage2f-H0-selection"),
    )
    return parser.parse_args()


def _historical_ages(people: pl.DataFrame, player_games: pl.DataFrame) -> pl.DataFrame:
    frames = []
    for season in sorted(int(value) for value in player_games["season"].unique()):
        player_ids = (
            player_games.filter(pl.col("season") == season)["player_id"]
            .unique()
            .to_list()
        )
        frames.append(
            build_mlbam_age_as_of(
                people, player_ids, as_of_date=date(season, 7, 1)
            ).with_columns(pl.lit(season).alias("season"))
        )
    return pl.concat(frames, how="vertical_relaxed").select(
        "player_id", "season", "birth_date", "age_years", "age_source_status"
    )


def _write(
    frame: pl.DataFrame, root: Path, fold_id: str, name: str
) -> dict[str, str | int]:
    return write_canonical_parquet(
        frame,
        root / "tables" / fold_id.lower() / f"{name}.parquet",
        table_name=f"hitter_v2_stage2f_{fold_id.lower()}_{name}",
    ).as_record()


def _eligible_origins(training: pl.DataFrame, cutoff: int) -> list[int]:
    minimum = int(training["season"].min())
    return list(range(minimum + 1, cutoff + 1))


def _origin_parts(
    training: pl.DataFrame, origin: int
) -> tuple[pl.DataFrame, set[int], pl.DataFrame]:
    history = training.filter(pl.col("season") < origin)
    if history.is_empty() or history.filter(pl.col("season") >= origin).height:
        raise ValueError("inner-origin history violates chronology")
    players = {int(value) for value in history["player_id"].unique().to_list()}
    target = aggregate_training_origin_target(
        training.filter(pl.col("season") <= origin),
        origin_season=origin,
        eligible_player_ids=players,
    )
    return history, players, target


def _select_components(
    training: pl.DataFrame, origins: list[int]
) -> tuple[dict[str, dict[str, float | None]], pl.DataFrame]:
    if not origins:
        return (
            {node.name: dict(NO_ORIGIN_COMPONENT_DEFAULT) for node in NESTED_NODES},
            pl.DataFrame(),
        )
    rows: list[dict[str, object]] = []
    for half_life in HALF_LIFE_GRID:
        for prior_pa in COMPONENT_PRIOR_GRID:
            totals = {node.name: [0.0, 0] for node in NESTED_NODES}
            details: dict[str, list[dict[str, object]]] = {
                node.name: [] for node in NESTED_NODES
            }
            for origin in origins:
                history, players, target = _origin_parts(training, origin)
                predictions = predict_c0_nested_eb(
                    history,
                    sorted(players),
                    predictor_cutoff_season=origin - 1,
                    half_life_seasons=half_life,
                    component_prior_pa={node.name: prior_pa for node in NESTED_NODES},
                )
                scores, _, _ = nested_selection_scores(predictions, target)
                for score in scores:
                    component = str(score["component"])
                    events = int(score["events"])
                    loss = float(score["event_log_loss"])
                    totals[component][0] += loss * events
                    totals[component][1] += events
                    details[component].append(
                        {
                            "origin_season": origin,
                            "events": events,
                            "event_log_loss": loss,
                        }
                    )
            for node in NESTED_NODES:
                weighted_loss, events = totals[node.name]
                rows.append(
                    {
                        "component": node.name,
                        "half_life_seasons": half_life,
                        "component_prior_pa": prior_pa,
                        "selection_events": events,
                        "event_log_loss": weighted_loss / events,
                        "origin_detail_json": json.dumps(
                            details[node.name], separators=(",", ":"), sort_keys=True
                        ),
                    }
                )
    scores = pl.DataFrame(rows)
    return select_component_hyperparameters(scores), scores


def _source_for_cutoff(
    training: pl.DataFrame,
    player_games_all: pl.DataFrame,
    park_context_all: pl.DataFrame,
    people: pl.DataFrame,
    c1_root: Path,
    *,
    cutoff: int,
    component_priors: dict[str, float],
) -> H0FitSources:
    target_year = cutoff + 1
    fold_slug = f"v{target_year}"
    player_games = player_games_all.filter(pl.col("season") <= cutoff)
    park_context = park_context_all.filter(pl.col("season") <= cutoff)
    ages = _historical_ages(people, player_games)
    park_offsets = pl.read_parquet(c1_root / fold_slug / "park_offsets.parquet")
    return materialize_h0_fit_sources(
        training.filter(pl.col("season") <= cutoff),
        player_games,
        park_context,
        park_offsets,
        ages,
        predictor_cutoff_season=cutoff,
        component_prior_pa=component_priors,
    )


def _surface_grid(
    training: pl.DataFrame,
    origins: list[int],
    half_lives: dict[str, float],
    component_priors: dict[str, float],
    player_games_all: pl.DataFrame,
    park_context_all: pl.DataFrame,
    people: pl.DataFrame,
    c1_root: Path,
    age_root: Path,
) -> tuple[dict[str, float], pl.DataFrame]:
    origin_inputs: dict[
        int, tuple[H0FitSources, pl.DataFrame, pl.DataFrame, pl.DataFrame]
    ] = {}
    for origin in origins:
        history, players, target = _origin_parts(training, origin)
        source = _source_for_cutoff(
            history,
            player_games_all,
            park_context_all,
            people,
            c1_root,
            cutoff=origin - 1,
            component_priors=component_priors,
        )
        base = predict_c0_nested_eb(
            history,
            sorted(players),
            predictor_cutoff_season=origin - 1,
            half_life_seasons=half_lives,
            component_prior_pa=component_priors,
        )
        ages = pl.read_parquet(age_root / f"v{origin}" / "forecast_player_ages.parquet")
        origin_inputs[origin] = (source, base, ages, target)

    rows: list[dict[str, object]] = []
    for translation_prior in TRANSLATION_PRIOR_GRID:
        for development_prior in DEVELOPMENT_PRIOR_GRID:
            for calibration_prior in CALIBRATION_PRIOR_GRID:
                weighted_loss = 0.0
                total_events = 0
                details = []
                for origin in origins:
                    source, base, ages, raw_target = origin_inputs[origin]
                    surfaces = fit_h0_surfaces(
                        source,
                        predictor_cutoff_season=origin - 1,
                        translation_prior_mover_pa=translation_prior,
                        development_prior_sd=development_prior,
                        calibration_prior_sd=calibration_prior,
                    )
                    predictions = apply_surfaces_to_predictions(
                        base,
                        latest_player_context(source.player_seasons),
                        ages,
                        surfaces,
                        include_calibration=False,
                        model_id="H0_TRAINING_ORIGIN_SELECTION",
                    )
                    scoring_predictions = backtranslate_predictions_to_scoring_level(
                        predictions, raw_target, surfaces.translation
                    )
                    _, loss, events = nested_selection_scores(
                        scoring_predictions, raw_target
                    )
                    weighted_loss += loss * events
                    total_events += events
                    details.append(
                        {
                            "origin_season": origin,
                            "events": events,
                            "event_log_loss": loss,
                            "translation_fitted": surfaces.translation is not None,
                        }
                    )
                rows.append(
                    {
                        "translation_prior_mover_pa": translation_prior,
                        "development_prior_sd": development_prior,
                        "calibration_prior_sd": calibration_prior,
                        "selection_events": total_events,
                        "event_log_loss": (
                            weighted_loss / total_events if total_events else 0.0
                        ),
                        "origin_detail_json": json.dumps(
                            details, separators=(",", ":"), sort_keys=True
                        ),
                    }
                )
    scores = pl.DataFrame(rows)
    return select_surface_configuration(scores), scores


def _probability_health(frame: pl.DataFrame) -> dict[str, object]:
    columns = [column for column in frame.columns if column.startswith("p_")]
    sums = frame.select(pl.sum_horizontal(*columns).alias("sum"))["sum"]
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
    prior_translation = None
    prior_target_season: int | None = None
    fold_reports: list[dict[str, object]] = []

    for fold_id, outer_target in FOLDS.items():
        cutoff = outer_target - 1
        slug = fold_id.lower()
        training_path = (
            args.prescore_root / slug / "training_player_league_seasons.parquet"
        )
        forecast_path = args.prescore_root / slug / "forecast_population.parquet"
        age_path = args.age_root / slug / "forecast_player_ages.parquet"
        training = pl.read_parquet(training_path)
        forecast = pl.read_parquet(forecast_path)
        forecast_ages = pl.read_parquet(age_path)
        origins = _eligible_origins(training, cutoff)

        selected_components, component_scores = _select_components(training, origins)
        half_lives, component_priors = selected_component_maps(selected_components)
        selected_surface, surface_scores = _surface_grid(
            training,
            origins,
            half_lives,
            component_priors,
            player_games_all,
            park_context_all,
            people,
            args.c1_root,
            args.age_root,
        )
        sources = _source_for_cutoff(
            training,
            player_games_all,
            park_context_all,
            people,
            args.c1_root,
            cutoff=cutoff,
            component_priors=component_priors,
        )
        calibration_origins = None
        if (
            prior_precal is not None
            and prior_translation is not None
            and prior_target_season is not None
        ):
            history_players = {
                int(value)
                for value in training.filter(pl.col("season") < prior_target_season)[
                    "player_id"
                ]
                .unique()
                .to_list()
            }
            raw_origin = aggregate_training_origin_target(
                training.filter(pl.col("season") <= prior_target_season),
                origin_season=prior_target_season,
                eligible_player_ids=history_players,
            )
            reference_origin = translate_training_origin_target(
                raw_origin, prior_translation
            )
            calibration_origins = build_reference_calibration_rows(
                prior_precal,
                reference_origin,
                target_season=prior_target_season,
            )
        surfaces = fit_h0_surfaces(
            sources,
            predictor_cutoff_season=cutoff,
            translation_prior_mover_pa=selected_surface["translation_prior_mover_pa"],
            development_prior_sd=selected_surface["development_prior_sd"],
            calibration_prior_sd=selected_surface["calibration_prior_sd"],
            calibration_origins=calibration_origins,
        )
        player_ids = [int(value) for value in forecast["player_id"].to_list()]
        c0 = predict_c0_nested_eb(
            training,
            player_ids,
            predictor_cutoff_season=cutoff,
            half_life_seasons=half_lives,
            component_prior_pa=component_priors,
        )
        b0 = predict_b0_one_year_eb(
            training,
            player_ids,
            predictor_cutoff_season=cutoff,
            component_prior_pa=component_priors,
        )
        age_map = {
            int(row["player_id"]): row["age_years"]
            for row in forecast_ages.iter_rows(named=True)
        }
        b1 = predict_b1_marcel_345_k1200(
            training,
            player_ids,
            predictor_cutoff_season=cutoff,
            ages_at_target=age_map,
        )
        context = latest_player_context(sources.player_seasons)
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
            name: wrap_baseline_predictions(
                frame,
                context,
                surfaces.translation,
                model_id=f"REFERENCE_WRAPPED_{name.upper()}",
            )
            for name, frame in {"b0": b0, "b1": b1, "c0": c0}.items()
        }

        artifacts: dict[str, dict[str, str | int] | None] = {
            "component_grid_scores": (
                _write(
                    component_scores,
                    args.report_root,
                    fold_id,
                    "component_grid_scores",
                )
                if not component_scores.is_empty()
                else None
            ),
            "surface_grid_scores": _write(
                surface_scores, args.report_root, fold_id, "surface_grid_scores"
            ),
            "h0_precal_predictions": _write(
                precal, args.report_root, fold_id, "h0_precal_predictions"
            ),
            "h0_predictions": _write(h0, args.report_root, fold_id, "h0_predictions"),
            **{
                f"reference_wrapped_{name}": _write(
                    frame,
                    args.report_root,
                    fold_id,
                    f"reference_wrapped_{name}",
                )
                for name, frame in wrapped.items()
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
        fold_reports.append(
            {
                "fold_id": fold_id,
                "outer_target_season_label_only": outer_target,
                "predictor_cutoff_season": cutoff,
                "training_origin_seasons": origins,
                "selected_components": selected_components,
                "selected_surface": selected_surface,
                "forecast_players": h0.height,
                "probability_health": _probability_health(h0),
                "forecast_population_unchanged": set(h0["player_id"].to_list())
                == set(forecast["player_id"].to_list()),
                "translation_fitted": surfaces.translation is not None,
                "development_fitted": surfaces.development is not None,
                "calibration_fitted": surfaces.calibration is not None,
                "artifacts": artifacts,
                "inputs": {
                    "training_sha256": sha256_file(training_path),
                    "forecast_population_sha256": sha256_file(forecast_path),
                    "forecast_ages_sha256": sha256_file(age_path),
                },
                "disclosed_validation_outcomes_loaded": False,
                "disclosed_validation_metrics_computed": False,
            }
        )
        prior_precal = precal
        prior_translation = surfaces.translation
        prior_target_season = outer_target

    report = {
        "schema_version": "0.1",
        "program": "hitter_v2",
        "stage": "2f_H0_training_origin_selection",
        "status": "configuration_selected_and_final_parameters_frozen_before_disclosed_scoring",
        "frozen_grid": {
            "component_half_life_seasons": list(HALF_LIFE_GRID),
            "component_prior_pa": list(COMPONENT_PRIOR_GRID),
            "translation_prior_mover_pa": list(TRANSLATION_PRIOR_GRID),
            "development_prior_sd": list(DEVELOPMENT_PRIOR_GRID),
            "calibration_prior_sd": list(CALIBRATION_PRIOR_GRID),
        },
        "selection_metric": "component_event_log_loss_on_strictly_earlier_training_origins",
        "tie_tolerance": 1e-8,
        "tie_rule": "larger_shrinkage_then_simpler_effect_structure_then_longer_half_life",
        "folds": fold_reports,
        "source_audit": {
            "player_games_sha256": sha256_file(args.player_games),
            "park_context_sha256": sha256_file(args.park_context),
            "register_archive_sha256": sha256_file(args.register_archive),
            "source_reacquired": False,
        },
        "stage2_target_tables_loaded": False,
        "evaluation_player_tables_loaded": False,
        "disclosed_validation_metrics_computed": False,
        "promotion_decision_made": False,
        "protected_2026_opened": False,
        "next_gate": "review_then_explicitly_authorize_frozen_disclosed_validation_scoring_without_retuning",
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
