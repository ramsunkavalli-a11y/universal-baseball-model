#!/usr/bin/env python3
"""Fit and materialize unscored Hitter v2 C1 sentinel predictions.

The command never reads target-season outcomes or evaluation membership.  Its
sentinel configuration is non-decisional and exists only to exercise the frozen
implementation and scientific invariants before the scoring gate opens.
"""

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
from universal_baseball.hitter_v2_c1 import (
    adjust_multi_out_for_gidp,
    apply_log_probability_offsets,
    estimate_player_gidp_rates,
    fit_c1_adjustments,
    predict_c1_hierarchical_pbp,
    require_probability_columns,
)
from universal_baseball.hitter_v2_model import (
    predict_b0_one_year_eb,
    predict_b1_marcel_345_k1200,
    predict_c0_nested_eb,
)
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.storage import sha256_file, write_canonical_parquet


FOLDS = {"V2022": 2022, "V2023": 2023, "V2024": 2024}
SENTINEL_PARAMETERS = {
    "half_life_seasons": 1.0,
    "component_prior_pa": 800.0,
    "park_prior_pa": 2000.0,
    "movement_prior_pa": 500.0,
    "ridge_penalty": 100.0,
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
        default=Path("reports/generated/hitter-v2-stage2-c1-prescore"),
    )
    return parser.parse_args()


def _historical_ages(
    people: pl.DataFrame,
    player_games: pl.DataFrame,
) -> pl.DataFrame:
    frames = []
    for season in sorted(int(value) for value in player_games["season"].unique()):
        player_ids = (
            player_games.filter(pl.col("season") == season)["player_id"]
            .unique()
            .to_list()
        )
        frames.append(
            build_mlbam_age_as_of(
                people,
                player_ids,
                as_of_date=date(season, 7, 1),
            ).with_columns(pl.lit(season).alias("season"))
        )
    return pl.concat(frames, how="vertical_relaxed").select(
        "player_id", "season", "birth_date", "age_years", "age_source_status"
    )


def _target_age_contexts(
    fitted_player_seasons: pl.DataFrame,
    forecast_ages: pl.DataFrame,
    *,
    predictor_cutoff_season: int,
) -> dict[int, tuple[float, float] | None]:
    latest = (
        fitted_player_seasons.sort(
            ["player_id", "season", "hitter_talent_pa", "league_id"],
            descending=[False, True, True, False],
        )
        .unique("player_id", keep="first", maintain_order=True)
        .select(
            "player_id", "season", "context_median_age"
        )
    )
    joined = forecast_ages.select("player_id", "age_years").join(
        latest, on="player_id", how="left", validate="1:1"
    )
    result: dict[int, tuple[float, float] | None] = {}
    for row in joined.iter_rows(named=True):
        target_age = row["age_years"]
        median = row["context_median_age"]
        last_season = row["season"]
        if target_age is None or median is None or last_season is None:
            result[int(row["player_id"])] = None
            continue
        extrapolated_median = float(median) + (
            predictor_cutoff_season - int(last_season)
        )
        result[int(row["player_id"])] = (float(target_age), extrapolated_median)
    return result


def _probability_invariants(frame: pl.DataFrame) -> dict[str, object]:
    require_probability_columns(frame)
    probability_columns = [f"p_{outcome}" for outcome in HITTER_TALENT_OUTCOMES]
    sums = frame.select(pl.sum_horizontal(*probability_columns).alias("sum"))["sum"]
    values = frame.select(probability_columns)
    finite = all(values.select(pl.all().is_finite().all()).row(0))
    nonnegative = all(values.select((pl.all() >= 0.0).all()).row(0))
    return {
        "rows": frame.height,
        "finite": finite,
        "nonnegative": nonnegative,
        "maximum_simplex_error": float((sums - 1.0).abs().max()),
    }


def _fallback_gidp_is_exact(predictions: pl.DataFrame) -> bool:
    fallback = predictions.filter(pl.col("gidp_fallback_reason").is_not_null())
    if fallback.is_empty():
        return True
    return all(
        fallback.select(
            *[
                (pl.col(f"p_{outcome}") == pl.col(f"pre_gidp_p_{outcome}")).all()
                for outcome in HITTER_TALENT_OUTCOMES
            ]
        ).row(0)
    )


def main() -> int:
    args = _parse_args()
    all_player_games = pl.read_parquet(args.player_games).filter(
        pl.col("modeling_eligible")
    )
    all_park = pl.read_parquet(args.park_context)
    all_gidp = pl.read_parquet(args.gidp_history)
    people = read_chadwick_people_archive(args.register_archive)
    fold_reports = []
    for fold_id, target_season in FOLDS.items():
        cutoff = target_season - 1
        slug = fold_id.lower()
        forecast_path = args.prescore_root / slug / "forecast_population.parquet"
        training_path = (
            args.prescore_root / slug / "training_player_league_seasons.parquet"
        )
        age_path = args.age_root / slug / "forecast_player_ages.parquet"
        forecast = pl.read_parquet(forecast_path)
        player_ids = [int(value) for value in forecast["player_id"].to_list()]
        training = pl.read_parquet(training_path)
        player_games = all_player_games.filter(pl.col("season") <= cutoff)
        park = all_park.filter(pl.col("season") <= cutoff)
        gidp = all_gidp.filter(pl.col("season") <= cutoff)
        historical_ages = _historical_ages(people, player_games)
        forecast_ages = pl.read_parquet(age_path)
        target_age_map = {
            int(row["player_id"]): row["age_years"]
            for row in forecast_ages.iter_rows(named=True)
        }

        c0 = predict_c0_nested_eb(
            training,
            player_ids,
            predictor_cutoff_season=cutoff,
            half_life_seasons=SENTINEL_PARAMETERS["half_life_seasons"],
            component_prior_pa={
                name: SENTINEL_PARAMETERS["component_prior_pa"]
                for name in (
                    "plate_appearance", "non_k", "non_k_non_ubb", "contact",
                    "non_hr_contact", "reach", "hit_in_play", "non_hit_reach",
                    "non_reach",
                )
            },
        )
        b0 = predict_b0_one_year_eb(
            training,
            player_ids,
            predictor_cutoff_season=cutoff,
            component_prior_pa={
                name: SENTINEL_PARAMETERS["component_prior_pa"]
                for name in (
                    "plate_appearance", "non_k", "non_k_non_ubb", "contact",
                    "non_hr_contact", "reach", "hit_in_play", "non_hit_reach",
                    "non_reach",
                )
            },
        )
        b1 = predict_b1_marcel_345_k1200(
            training,
            player_ids,
            predictor_cutoff_season=cutoff,
            ages_at_target=target_age_map,
        )
        fit = fit_c1_adjustments(
            player_games,
            park,
            historical_ages,
            predictor_cutoff_season=cutoff,
            component_prior_pa=SENTINEL_PARAMETERS["component_prior_pa"],
            park_prior_pa=SENTINEL_PARAMETERS["park_prior_pa"],
            movement_prior_pa=SENTINEL_PARAMETERS["movement_prior_pa"],
            ridge_penalty=SENTINEL_PARAMETERS["ridge_penalty"],
        )
        gidp_rates = estimate_player_gidp_rates(
            gidp,
            player_ids,
            predictor_cutoff_season=cutoff,
            half_life_seasons=SENTINEL_PARAMETERS["half_life_seasons"],
            prior_pa=SENTINEL_PARAMETERS["component_prior_pa"],
        )
        age_contexts = _target_age_contexts(
            fit.player_seasons,
            forecast_ages,
            predictor_cutoff_season=cutoff,
        )
        c1 = predict_c1_hierarchical_pbp(
            c0,
            training,
            fit,
            gidp_rates,
            target_age_contexts=age_contexts,
        )

        output_dir = args.report_root / "tables" / slug
        artifacts = {}
        for name, frame in (
            ("b0_unscored_predictions", b0),
            ("b1_unscored_predictions", b1),
            ("c0_unscored_predictions", c0),
            ("c1_unscored_predictions", c1),
            ("park_offsets", fit.park_offsets),
            ("first_pass_level_offsets", fit.first_pass_level_offsets),
            ("age_coefficients", fit.age_coefficients),
            ("final_level_offsets", fit.final_level_offsets),
        ):
            artifacts[name] = write_canonical_parquet(
                frame,
                output_dir / f"{name}.parquet",
                table_name=f"hitter_v2_{slug}_{name}",
            ).as_record()
        zero = {outcome: 0.0 for outcome in HITTER_TALENT_OUTCOMES}
        first_c0 = c0.row(0, named=True)
        synthetic = {
            outcome: float(first_c0[f"p_{outcome}"])
            for outcome in HITTER_TALENT_OUTCOMES
        }
        zero_identity = apply_log_probability_offsets(synthetic, zero) == synthetic
        gidp_identity = adjust_multi_out_for_gidp(
            synthetic,
            opportunity_rate=None,
            conversion_rate=None,
            non_gidp_multi_out_rate=None,
        )[0] == synthetic
        fold_reports.append(
            {
                "fold_id": fold_id,
                "target_season": target_season,
                "predictor_cutoff_season": cutoff,
                "predictor_max_season": int(training["season"].max()),
                "forecast_players": len(player_ids),
                "target_outcomes_loaded": False,
                "evaluation_membership_loaded": False,
                "movement_pairs": fit.movement_observations.height,
                "age_fit_fallback_reason": fit.age_fit_fallback_reason,
                "fallback_counts": {
                    "park": c1.height - c1["park_fallback_reason"].null_count(),
                    "translation": c1.height
                    - c1["translation_fallback_reason"].null_count(),
                    "age": c1.height - c1["age_fallback_reason"].null_count(),
                    "gidp": c1.height - c1["gidp_fallback_reason"].null_count(),
                },
                "invariants": {
                    "c0": _probability_invariants(c0),
                    "c1": _probability_invariants(c1),
                    "zero_offsets_exact_c0": zero_identity,
                    "missing_gidp_exact_pre_gidp": _fallback_gidp_is_exact(c1),
                    "synthetic_missing_gidp_exact": gidp_identity,
                    "mlb_anchor_exact_zero": all(
                        fit.final_level_offsets.filter(pl.col("level_group") == "MLB")
                        .select(
                            *[
                                (pl.col(f"level_log_offset_{outcome}") == 0.0).all()
                                for outcome in HITTER_TALENT_OUTCOMES
                            ]
                        )
                        .row(0)
                    ),
                    "forecast_ids_equal_predeclared_population": c1["player_id"].to_list()
                    == sorted(player_ids),
                },
                "inputs": {
                    "forecast_population_sha256": sha256_file(forecast_path),
                    "training_sha256": sha256_file(training_path),
                    "forecast_ages_sha256": sha256_file(age_path),
                },
                "artifacts": artifacts,
            }
        )
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": 2,
        "status": "c1_unscored_prescore_invariants_materialized",
        "candidate_fit": True,
        "candidate_scored": False,
        "protected_2026_opened": False,
        "configuration_role": "non_decisional_sentinel",
        "sentinel_parameters": SENTINEL_PARAMETERS,
        "target_data_policy": (
            "target outcomes and evaluation membership are not accepted as inputs"
        ),
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
