#!/usr/bin/env python3
"""Score affiliated level translation on later MLB component outcomes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.level_component_translation import (
    build_translated_affiliated_profiles,
    fit_same_season_component_translation,
    score_component_profiles,
)


HITTER_COMPONENTS = ("ubb", "hbp", "single", "double", "triple", "hr", "other")
PITCHER_COMPONENTS = ("so", "ubb", "hbp", "hr", "other")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-root", type=Path,
        default=Path("reports/generated/affiliated-skill-source/tables"),
    )
    parser.add_argument("--targets", default="2024,2025")
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/affiliated-level-translation-score"),
    )
    return parser.parse_args()


def _hitter_components(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        (pl.col("hits") - pl.col("doubles") - pl.col("triples") - pl.col("home_runs")).alias("single"),
        pl.col("doubles").alias("double"), pl.col("triples").alias("triple"),
        pl.col("home_runs").alias("hr"), pl.col("hit_by_pitch").alias("hbp"),
    ).with_columns(
        (pl.col("plate_appearances") - pl.sum_horizontal(*HITTER_COMPONENTS[:-1])).alias("other")
    )


def _pitcher_components(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        pl.col("strike_outs").alias("so"),
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        pl.col("hit_batters").alias("hbp"), pl.col("home_runs").alias("hr"),
    ).with_columns(
        (pl.col("batters_faced") - pl.sum_horizontal(*PITCHER_COMPONENTS[:-1])).alias("other")
    )


def _prior_predictions(
    players: pl.DataFrame,
    source: pl.DataFrame,
    *,
    cutoff: int,
    exposure: str,
    components: tuple[str, ...],
) -> pl.DataFrame:
    reference = source.filter(
        (pl.col("season") == cutoff) & (pl.col("level_group") == "MLB")
    )
    total = float(reference.get_column(exposure).sum())
    rates = {component: float(reference.get_column(component).sum()) / total for component in components}
    return players.with_columns(*(pl.lit(rates[value]).alias(f"p_{value}") for value in components))


def _score_fold(
    source: pl.DataFrame,
    *,
    target_season: int,
    exposure: str,
    components: tuple[str, ...],
    regression_exposure: float,
) -> dict[str, object]:
    cutoff = target_season - 1
    fit_seasons = tuple(
        int(value) for value in source.filter(pl.col("season") <= cutoff)
        .get_column("season").unique().sort().to_list()
    )
    fit = fit_same_season_component_translation(
        source, exposure_column=exposure, component_columns=components,
        completed_seasons=fit_seasons, minimum_level_exposure=30,
    )
    prior_evidence = source.filter(pl.col("season") <= cutoff)
    player_evidence = prior_evidence.group_by("player_id").agg(
        pl.col(exposure).sum().alias("all_exposure"),
        pl.col(exposure).filter(pl.col("level_group") == "MLB").sum().alias("mlb_exposure"),
    )
    players = player_evidence.filter(
        (pl.col("all_exposure") > 0) & (pl.col("mlb_exposure") == 0)
    ).select("player_id")
    translated = build_translated_affiliated_profiles(
        players, prior_evidence, fit.offsets,
        exposure_column=exposure, component_columns=components,
        current_season=cutoff, reference_season=cutoff,
        regression_exposure=regression_exposure,
    )
    zero_offsets = fit.offsets.with_columns(pl.lit(0.0).alias("clr_environment_effect"))
    untranslated = build_translated_affiliated_profiles(
        players, prior_evidence, zero_offsets,
        exposure_column=exposure, component_columns=components,
        current_season=cutoff, reference_season=cutoff,
        regression_exposure=regression_exposure,
    )
    prior = _prior_predictions(
        players, source, cutoff=cutoff, exposure=exposure, components=components
    )
    target = source.filter(
        (pl.col("season") == target_season) & (pl.col("level_group") == "MLB")
    )
    scores = {
        "translated": score_component_profiles(
            translated, target, exposure_column=exposure, component_columns=components
        ),
        "same_regression_no_translation": score_component_profiles(
            untranslated, target, exposure_column=exposure, component_columns=components
        ),
        "mlb_population_prior": score_component_profiles(
            prior, target, exposure_column=exposure, component_columns=components
        ),
    }
    return {
        "target_season": target_season,
        "predictor_cutoff": cutoff,
        "fit_seasons": list(fit_seasons),
        "forecast_population_players": players.height,
        "target_membership_used_as_predictor": False,
        "translation_fit": fit.metrics,
        "scores": scores,
        "translated_minus_no_translation_log_loss": (
            float(scores["translated"]["component_log_loss"])
            - float(scores["same_regression_no_translation"]["component_log_loss"])
        ),
    }


def main() -> int:
    args = _args()
    targets = tuple(sorted({int(value.strip()) for value in args.targets.split(",") if value.strip()}))
    hitters = _hitter_components(
        pl.read_parquet(args.source_root / "affiliated_hitting_components.parquet")
    )
    pitchers = _pitcher_components(
        pl.read_parquet(args.source_root / "affiliated_pitching_components.parquet")
    )
    hitter_folds = [
        _score_fold(
            hitters, target_season=target, exposure="plate_appearances",
            components=HITTER_COMPONENTS, regression_exposure=1200.0,
        )
        for target in targets
    ]
    pitcher_folds = [
        _score_fold(
            pitchers, target_season=target, exposure="batters_faced",
            components=PITCHER_COMPONENTS, regression_exposure=800.0,
        )
        for target in targets
    ]
    report = {
        "report_schema_version": "0.1",
        "gate": "affiliated_translation_future_mlb_diagnostic",
        "targets": list(targets),
        "current_2026_used": False,
        "intended_population": "players with prior affiliated exposure and zero prior MLB exposure",
        "hitter_folds": hitter_folds,
        "pitcher_folds": pitcher_folds,
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    compact = {
        "gate": report["gate"],
        "hitter_log_loss_delta": [fold["translated_minus_no_translation_log_loss"] for fold in hitter_folds],
        "pitcher_log_loss_delta": [fold["translated_minus_no_translation_log_loss"] for fold in pitcher_folds],
    }
    print(json.dumps(compact, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
