#!/usr/bin/env python3
"""Freeze the winning hitter-gradient recipe into 2026 forecasts using 2025 only."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge

from audit_hitter_gradient_ablation import _design, _families
from materialize_hitter_gradient_dataset import (
    PARK_PRIOR_EXPOSURE,
    PLAYER_CELL_PRIOR,
    _hitter_components,
    _pitcher_as_hitter_components,
)
from score_hitter_gradient_challenger_v1 import TREE_PARAMETERS, _normalize
from universal_baseball.affiliated_component_park_factor import (
    build_component_park_observations,
    build_schedule_opponent_adjustments,
    fit_component_park_factors,
)
from universal_baseball.hitter_gradient_materialization import (
    CONTACT_OUTCOMES,
    PARK_COMPONENTS,
    PITCHER_CONTEXT_COLUMNS,
    PITCHER_SUPPORT_COLUMNS,
    attach_as_of_park_features,
    build_player_season_features,
    join_contact_context_events,
    make_park_vintage,
)
from universal_baseball.hitter_postfreeze_context import (
    build_postfreeze_prior_pitcher_binary_feature,
    build_postfreeze_prior_pitcher_hit_composition_features,
)
from universal_baseball.hitter_v2_stage2d import (
    build_prior_pitcher_binary_feature,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


SOURCE_SEASON = 2025
TARGET_SEASON = 2026
ANNUAL_MIN_CONTACTS = 30
RIDGE_ALPHA = 300.0
TRANSITION_ORIGINS = (2016, 2017, 2018, 2021, 2022, 2023, 2024)
LEVELS = ("rk", "a-", "a", "a+", "aa", "aaa")
BASE_COLUMNS = tuple(f"overall__{value}" for value in CONTACT_OUTCOMES)
SHARE_COLUMNS = (
    "share__PULL_GB",
    "share__CENTER_GB",
    "share__OPPO_GB",
    "share__PULL_LD",
    "share__CENTER_LD",
    "share__OPPO_LD",
    "share__PULL_OFFB",
    "share__CENTER_OFFB",
    "share__OPPO_OFFB",
    "share__IFFB",
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-root", type=Path, required=True)
    parser.add_argument("--historical-context", type=Path, required=True)
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--development-rows",
        type=Path,
        default=Path(
            "reports/generated/hitter-gradient-dataset-v1/tables/modeling-rows.parquet"
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(
            "model_artifacts/hitter-gradient-2026-confirmation-forecast-2026-09-19"
        ),
    )
    return parser.parse_args()


def _transition(current: pl.DataFrame, future: pl.DataFrame, origin: int) -> pl.DataFrame:
    target = future.filter(pl.col("contacts") >= ANNUAL_MIN_CONTACTS).select(
        "player_id",
        pl.col("contacts").alias("target_contacts"),
        *(pl.col(value).alias(f"target__{value}") for value in BASE_COLUMNS),
    )
    return (
        current.filter(pl.col("contacts") >= ANNUAL_MIN_CONTACTS)
        .join(target, on="player_id", how="inner", validate="1:1")
        .with_columns(pl.lit(origin).alias("origin_year"))
        .sort("player_id")
    )


def _contact_only_design(
    training: pl.DataFrame, evaluation: pl.DataFrame
) -> tuple[np.ndarray, np.ndarray]:
    numeric = (*BASE_COLUMNS, "log_contacts", *SHARE_COLUMNS)
    train = training.select(numeric).to_numpy().astype(float)
    score = evaluation.select(numeric).to_numpy().astype(float)
    center, scale = train.mean(axis=0), train.std(axis=0)
    scale[scale < 1e-12] = 1.0
    train = np.clip((train - center) / scale, -6.0, 6.0)
    score = np.clip((score - center) / scale, -6.0, 6.0)
    train_level = training["source_level"].to_numpy()
    score_level = evaluation["source_level"].to_numpy()
    train = np.column_stack([train, *[train_level == level for level in LEVELS]])
    score = np.column_stack([score, *[score_level == level for level in LEVELS]])
    return train.astype(float), score.astype(float)


def _contact_only_forecast(root: Path) -> tuple[pl.DataFrame, list[Path]]:
    annual_root = root / "hitter-multiyear-age-level-base/tables"
    years = sorted({*TRANSITION_ORIGINS, *(year + 1 for year in TRANSITION_ORIGINS), 2025})
    paths = [annual_root / f"annual-{year}.parquet" for year in years]
    annual = {year: pl.read_parquet(path) for year, path in zip(years, paths, strict=True)}
    training = pl.concat(
        [
            _transition(annual[origin], annual[origin + 1], origin)
            for origin in TRANSITION_ORIGINS
        ],
        how="vertical_relaxed",
    )
    evaluation = annual[SOURCE_SEASON].filter(
        pl.col("contacts") >= ANNUAL_MIN_CONTACTS
    ).sort("player_id")
    x_train, x_score = _contact_only_design(training, evaluation)
    target = training.select(
        *(f"target__{value}" for value in BASE_COLUMNS)
    ).to_numpy()
    model = Ridge(alpha=RIDGE_ALPHA).fit(
        x_train,
        target,
        sample_weight=training["target_contacts"].to_numpy().astype(float),
    )
    prediction = _normalize(model.predict(x_score))
    return evaluation.select("player_id", "source_level", "contacts").with_columns(
        *(
            pl.Series(f"contact_only__overall__{outcome}", prediction[:, index])
            for index, outcome in enumerate(CONTACT_OUTCOMES)
        )
    ), paths


def _latest_pitcher_prior(
    historical: pl.DataFrame, node: str
) -> pl.DataFrame:
    feature = build_prior_pitcher_binary_feature(historical, node)
    return (
        feature.sort("game_date")
        .group_by("pitcher_id")
        .agg(
            pl.col(f"{node}_prior_pitcher_denominator").last(),
            pl.col(f"{node}_prior_pitcher_log_odds_residual").last(),
        )
    )


def _context_2025(
    contacts: pl.DataFrame,
    games: pl.DataFrame,
    demographics: pl.DataFrame,
    historical_path: Path,
) -> pl.DataFrame:
    historical = pl.read_parquet(historical_path).filter(
        pl.col("context_label_ready")
    )
    current = (
        contacts.join(
            games.select("season", "game_pk", "game_date"),
            on=["season", "game_pk"],
            how="left",
            validate="m:1",
        )
        .join(
            demographics.select(
                pl.col("player_id").alias("source_pitcher_id"), "pitch_hand"
            ),
            on="source_pitcher_id",
            how="left",
            validate="m:1",
        )
        .select(
            "season",
            "game_date",
            "game_pk",
            "at_bat_index",
            "league_id",
            pl.col("source_level").alias("level_group"),
            "player_id",
            pl.col("source_pitcher_id").alias("pitcher_id"),
            "batter_side",
            pl.col("pitch_hand").alias("pitcher_hand"),
            "canonical_outcome",
        )
        .with_columns(
            (
                pl.col("game_date").is_not_null()
                & pl.col("batter_side").is_in(["L", "R"])
                & pl.col("pitcher_hand").is_in(["L", "R"])
            ).alias("context_label_ready")
        )
    )
    history_columns = current.columns
    combined = pl.concat(
        [historical.select(history_columns), current], how="vertical_relaxed"
    )
    result = current
    for node in ("K", "UBB", "HBP"):
        result = result.join(
            _latest_pitcher_prior(historical, node),
            on="pitcher_id",
            how="left",
            validate="m:1",
        )
    for node in ("HR", "NON_HR_REACH"):
        feature = build_postfreeze_prior_pitcher_binary_feature(
            combined, node, protected_season=TARGET_SEASON
        ).filter(pl.col("season") == SOURCE_SEASON)
        result = result.join(
            feature.select(
                "season",
                "game_pk",
                "at_bat_index",
                f"{node}_prior_pitcher_denominator",
                f"{node}_prior_pitcher_log_odds_residual",
            ),
            on=["season", "game_pk", "at_bat_index"],
            how="left",
            validate="1:1",
        )
    composition = build_postfreeze_prior_pitcher_hit_composition_features(
        combined, protected_season=TARGET_SEASON
    ).filter(pl.col("season") == SOURCE_SEASON)
    result = result.join(
        composition.select(
            "season",
            "game_pk",
            "at_bat_index",
            "HIT_COMPOSITION_prior_pitcher_denominator",
            "HIT_COMPOSITION_prior_pitcher_alr_residual_1B",
            "HIT_COMPOSITION_prior_pitcher_alr_residual_2B",
            "HIT_COMPOSITION_prior_pitcher_alr_residual_3B",
        ),
        on=["season", "game_pk", "at_bat_index"],
        how="left",
        validate="1:1",
    )
    return result.with_columns(
        *(pl.col(value).fill_nan(0.0).fill_null(0.0) for value in (*PITCHER_CONTEXT_COLUMNS, *PITCHER_SUPPORT_COLUMNS))
    )


def _park_2025(root: Path) -> pl.DataFrame:
    split_root = root / "affiliated-home-away-components/tables"
    hitters = _hitter_components(
        pl.read_parquet(split_root / "affiliated-hitter-home-away.parquet")
    ).filter(pl.col("season").is_between(2021, SOURCE_SEASON))
    pitchers = _pitcher_as_hitter_components(
        pl.read_parquet(split_root / "affiliated-pitcher-home-away.parquet")
    ).filter(pl.col("season").is_between(2021, SOURCE_SEASON))
    games = pl.read_parquet(
        root / "affiliated-game-context/tables/affiliated-game-context.parquet"
    ).filter(pl.col("season").is_between(2021, SOURCE_SEASON))
    teams = pl.read_parquet(
        root / "affiliated-team-context/tables/affiliated-team-context.parquet"
    ).filter(pl.col("season").is_between(2021, SOURCE_SEASON))
    adjustment = build_schedule_opponent_adjustments(
        games,
        pitchers,
        exposure_column="batters_faced",
        component_columns=PARK_COMPONENTS,
    )
    observations = build_component_park_observations(
        hitters,
        teams,
        exposure_column="plate_appearances",
        component_columns=PARK_COMPONENTS,
        opponent_adjustments=adjustment,
    )
    factors = fit_component_park_factors(
        observations,
        through_season=SOURCE_SEASON,
        component_columns=PARK_COMPONENTS,
        prior_exposure=PARK_PRIOR_EXPOSURE,
    )
    return make_park_vintage(
        factors,
        source_season=SOURCE_SEASON,
        prior_exposure=PARK_PRIOR_EXPOSURE,
    )


def _gradient_forecast(
    training: pl.DataFrame,
    evaluation: pl.DataFrame,
    columns: list[str],
) -> np.ndarray:
    x_train, x_score = _design(training, evaluation, columns)
    actual = training.select(
        *(f"target__overall__{value}" for value in CONTACT_OUTCOMES)
    ).to_numpy()
    base_train = training.select(
        *(f"contact_only__overall__{value}" for value in CONTACT_OUTCOMES)
    ).to_numpy()
    base_score = evaluation.select(
        *(f"contact_only__overall__{value}" for value in CONTACT_OUTCOMES)
    ).to_numpy()
    residual = actual - base_train
    weights = training["target_contacts"].to_numpy().astype(float)
    corrections = []
    for index in range(len(CONTACT_OUTCOMES)):
        model = HistGradientBoostingRegressor(**TREE_PARAMETERS).fit(
            x_train, residual[:, index], sample_weight=weights
        )
        corrections.append(model.predict(x_score))
    return _normalize(base_score + np.column_stack(corrections))


def main() -> int:
    args = _args()
    if args.as_of_date.year != TARGET_SEASON:
        raise ValueError("2026 freeze requires a 2026 as-of date")
    root = args.generated_root
    contact_path = (
        root
        / "official-full-bip-context-2025/tables/hitter_full_bip_event_outcomes.parquet"
    )
    game_path = root / "affiliated-game-context/tables/affiliated-game-context.parquet"
    demographic_path = root / "player-demographics/tables/player-demographics.parquet"
    annual_path = root / "hitter-multiyear-age-level-base/tables/annual-2025.parquet"
    contacts = pl.read_parquet(contact_path)
    games = pl.read_parquet(game_path).filter(pl.col("season") == SOURCE_SEASON)
    demographics = pl.read_parquet(demographic_path)
    context = _context_2025(contacts, games, demographics, args.historical_context)
    events = join_contact_context_events(contacts, context, games)
    events = attach_as_of_park_features(events, _park_2025(root))
    annual = pl.read_parquet(annual_path).with_columns(
        pl.lit(SOURCE_SEASON).alias("season")
    )
    features = build_player_season_features(
        events, annual, player_prior=PLAYER_CELL_PRIOR
    )
    baseline, baseline_inputs = _contact_only_forecast(root)
    evaluation = baseline.join(
        features, on="player_id", how="inner", validate="1:1", suffix="__feature"
    )
    if evaluation.height != baseline.height:
        raise ValueError("2025 gradient features do not cover the forecast universe")
    rename = {
        "source_level__feature": "_drop_source_level",
        "contacts__feature": "_drop_contacts",
    }
    # The joined baseline owns source_level/contacts. Rename the annual copies and
    # then restore the exact development-table feature names expected by the recipe.
    evaluation = evaluation.rename(rename).with_columns(
        pl.col("contacts").alias("contacts__feature"),
        *(
            pl.col(f"overall__{outcome}").alias(
                f"overall__{outcome}__feature"
            )
            for outcome in CONTACT_OUTCOMES
        ),
    ).drop(
        "_drop_source_level",
        "_drop_contacts",
        *(f"overall__{value}" for value in CONTACT_OUTCOMES),
    )
    training = pl.read_parquet(args.development_rows)
    families = _families(training)
    feature_columns = families["plus_park"]
    missing = sorted(set(feature_columns) - set(evaluation.columns))
    if missing:
        raise ValueError(f"2025 forecast inputs lack frozen features: {missing}")
    prediction = _gradient_forecast(training, evaluation, feature_columns)
    forecast = evaluation.select(
        "player_id", "source_level", "contacts"
    ).with_columns(
        pl.lit(SOURCE_SEASON).alias("source_season"),
        pl.lit(TARGET_SEASON).alias("forecast_season"),
        *(
            evaluation[f"contact_only__overall__{outcome}"].alias(
                f"contact_only__overall__{outcome}"
            )
            for outcome in CONTACT_OUTCOMES
        ),
        *(
            pl.Series(f"gradient__overall__{outcome}", prediction[:, index])
            for index, outcome in enumerate(CONTACT_OUTCOMES)
        ),
    ).sort("player_id")
    if forecast.select(
        pl.sum_horizontal(
            *(f"gradient__overall__{value}" for value in CONTACT_OUTCOMES)
        ).alias("probability_sum")
    ).filter((pl.col("probability_sum") - 1.0).abs() > 1e-9).height:
        raise ValueError("frozen gradient probabilities do not sum to one")

    args.output_root.mkdir(parents=True, exist_ok=True)
    feature_artifact = write_canonical_parquet(
        evaluation,
        args.output_root / "forecast-inputs-2025.parquet",
        table_name="hitter_gradient_2026_forecast_inputs",
    ).as_record()
    forecast_artifact = write_canonical_parquet(
        forecast,
        args.output_root / "forecast-2026.parquet",
        table_name="hitter_gradient_2026_frozen_forecast",
    ).as_record()
    inputs = [
        args.development_rows,
        args.historical_context,
        contact_path,
        game_path,
        demographic_path,
        annual_path,
        *baseline_inputs,
        root
        / "affiliated-home-away-components/tables/affiliated-hitter-home-away.parquet",
        root
        / "affiliated-home-away-components/tables/affiliated-pitcher-home-away.parquet",
        root / "affiliated-team-context/tables/affiliated-team-context.parquet",
    ]
    manifest = {
        "schema_version": "1.0",
        "status": "frozen",
        "as_of_date": args.as_of_date.isoformat(),
        "source_season": SOURCE_SEASON,
        "forecast_season": TARGET_SEASON,
        "protected_2026_participants_or_outcomes_opened": False,
        "forecast_players": forecast.height,
        "minimum_source_contacts": ANNUAL_MIN_CONTACTS,
        "recipe": {
            "base": "contact-only ridge, alpha 300",
            "challenger": "nine fixed histogram gradient trees on residuals",
            "tree_parameters": TREE_PARAMETERS,
            "feature_family": "plus_park",
            "feature_count": len(feature_columns),
            "feature_columns": feature_columns,
            "contact_cell_prior": PLAYER_CELL_PRIOR,
            "park_prior_exposure": PARK_PRIOR_EXPOSURE,
        },
        "opponent_context_2025": {
            "HR_NON_HR_REACH_hit_composition": (
                "strictly prior through each 2025 game, seeded by 2021-2024"
            ),
            "K_UBB_HBP": "latest strictly-prior pitcher residual through 2024",
            "reason": "2025 terminal contact source is complete; full non-contact PA sidecar was not available",
        },
        "coverage": {
            "contact_events": events.height,
            "exact_opponent_context": float(events["opponent_context_known"].mean()),
            "venue": float(events["venue_known"].mean()),
            "park_factor_known": float(events["park_factor_known"].mean()),
        },
        "input_files": [
            {"path": str(path), "sha256": sha256_file(path)} for path in inputs
        ],
        "artifacts": {
            "forecast_inputs": feature_artifact,
            "forecast": forecast_artifact,
        },
        "scoring_lock": (
            "Do not evaluate, refit, select, or alter this forecast using 2026 "
            "participants or outcomes until the protected season is declared complete."
        ),
    }
    (args.output_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
