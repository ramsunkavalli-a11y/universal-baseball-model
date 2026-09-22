#!/usr/bin/env python3
"""Estimate dated ball-flight environments from affiliated air-contact outcomes."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from universal_baseball.hitter_ball_environment import (
    aggregate_player_ball_features,
    apply_crossfit_regime_adjustments,
    binary_metrics,
    prepare_air_contact_history,
)
from universal_baseball.hitter_contact_neutralization import prepare_terminal_contacts
from universal_baseball.storage import sha256_file, write_canonical_parquet


SEASONS = (2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024)
TERMINAL_COLUMNS = (
    "season",
    "level",
    "game_pk",
    "at_bat_index",
    "terminal_pitch_number",
    "league_id",
    "batter",
    "pitcher",
    "inning",
    "outs_when_up",
    "on_1b",
    "on_2b",
    "on_3b",
    "bat_score",
    "fld_score",
    "inning_top_bot",
    "stand",
    "p_throws",
    "bb_type",
    "hc_x",
    "hc_y",
    "terminal_outcome_group",
    "defense_team",
    "is_batted_ball",
)
CATEGORICAL_FEATURES = (
    "level",
    "league_id",
    "core_bin",
    "stand",
    "p_throws",
    "venue_id",
    "day_night",
    "turf_type",
    "roof_type",
    "weather_condition",
    "wind_direction",
)
NUMERIC_FEATURES = (
    "spray_angle",
    "temperature_f",
    "wind_mph",
    "venue_latitude",
    "venue_longitude",
    "left_field_line_ft",
    "center_field_ft",
    "right_field_line_ft",
    "first_pitch_hour_utc",
    "prior_hitter_air_hr_log_odds_residual",
    "prior_pitcher_air_hr_log_odds_residual",
    "prior_hitter_air_contacts",
    "prior_pitcher_air_contacts",
)
COMPACT_EVENT_COLUMNS = (
    "season",
    "league_id",
    "level",
    "game_date",
    "game_pk",
    "at_bat_index",
    "player_id",
    "pitcher",
    "core_bin",
    "is_hr",
    "ball_window",
    "ball_regime_key",
    "ball_crossfit_fold",
    "base_hr_probability",
    "ball_regime_log_odds",
    "regime_hr_probability",
    "ball_probability_effect",
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--terminal-root",
        type=Path,
        default=Path("data/working/pbp-opportunity-foundation-v1"),
    )
    parser.add_argument(
        "--game-context",
        type=Path,
        default=Path(
            "reports/generated/defensive-venue-context-v1/"
            "affiliated-game-context.parquet"
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/hitter-ball-environment-v1"),
    )
    parser.add_argument("--window-days", type=int, default=14)
    parser.add_argument("--regime-prior", type=float, default=1_000.0)
    return parser.parse_args()


def _load_terminal(root: Path, season: int) -> pl.DataFrame:
    paths = sorted(root.glob(f"season={season}/level=*/terminal/*.parquet"))
    if not paths:
        raise FileNotFoundError(f"no terminal PBP partitions found for {season}")
    return pl.concat(
        [pl.read_parquet(path, columns=list(TERMINAL_COLUMNS)) for path in paths],
        how="diagonal_relaxed",
    )


def _encode_matrix(frame: pl.DataFrame) -> tuple[np.ndarray, list[int]]:
    arrays: list[np.ndarray] = []
    categorical_indices: list[int] = []
    for index, column in enumerate(CATEGORICAL_FEATURES):
        values = frame[column].cast(pl.String).fill_null("__MISSING__").to_numpy()
        _, inverse = np.unique(values, return_inverse=True)
        arrays.append(inverse.astype(np.float32))
        categorical_indices.append(index)
    for column in NUMERIC_FEATURES:
        values = frame[column].cast(pl.Float32, strict=False).to_numpy().copy()
        values[~np.isfinite(values)] = np.nan
        arrays.append(values)
    return np.column_stack(arrays).astype(np.float32, copy=False), categorical_indices


def _base_probabilities(events: pl.DataFrame) -> np.ndarray:
    from lightgbm import LGBMClassifier

    matrix, categorical = _encode_matrix(events)
    labels = events["is_hr"].to_numpy()
    folds = events["ball_crossfit_fold"].to_numpy()
    probability = np.full(events.height, np.nan, dtype=np.float64)
    for target_fold in (0, 1):
        train = folds != target_fold
        test = folds == target_fold
        model = LGBMClassifier(
            objective="binary",
            n_estimators=160,
            learning_rate=0.05,
            num_leaves=31,
            max_depth=6,
            min_child_samples=500,
            colsample_bytree=0.85,
            reg_alpha=0.25,
            reg_lambda=5.0,
            random_state=417 + target_fold,
            n_jobs=-1,
            verbosity=-1,
        )
        print(
            f"base contact model: training game fold {1 - target_fold}, "
            f"scoring fold {target_fold}",
            flush=True,
        )
        model.fit(
            matrix[train],
            labels[train],
            categorical_feature=categorical,
        )
        probability[test] = model.predict_proba(matrix[test])[:, 1]
    if not np.isfinite(probability).all():
        raise RuntimeError("base air-contact probabilities are incomplete")
    return probability


def _metric_slices(events: pl.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for label, columns in {
        "season": ("season",),
        "level": ("level",),
        "season_level": ("season", "level"),
    }.items():
        rows: dict[str, Any] = {}
        for key, group in events.partition_by(list(columns), as_dict=True).items():
            values = key if isinstance(key, tuple) else (key,)
            name = "|".join(str(value) for value in values)
            rows[name] = {
                "events": group.height,
                "base": binary_metrics(
                    group["is_hr"].to_numpy(),
                    group["base_hr_probability"].to_numpy(),
                ),
                "with_ball_regime": binary_metrics(
                    group["is_hr"].to_numpy(),
                    group["regime_hr_probability"].to_numpy(),
                ),
            }
        result[label] = rows
    return result


def _annual_environment(events: pl.DataFrame) -> pl.DataFrame:
    return (
        events.group_by("season", "level")
        .agg(
            pl.len().alias("air_contacts"),
            pl.col("is_hr").mean().alias("raw_air_hr_rate"),
            pl.col("base_hr_probability").mean().alias("base_expected_hr_rate"),
            pl.col("regime_hr_probability").mean().alias("regime_expected_hr_rate"),
            pl.col("ball_regime_log_odds").mean().alias("mean_ball_regime_log_odds"),
            pl.col("ball_probability_effect")
            .mean()
            .alias("mean_ball_probability_effect"),
        )
        .sort(["season", "level"])
    )


def main() -> int:
    args = _args()
    if args.window_days <= 0 or args.regime_prior <= 0:
        raise ValueError("window length and regime prior must be positive")
    context = pl.read_parquet(args.game_context).filter(pl.col("season").is_in(SEASONS))
    if context.filter(pl.col("season") >= 2026).height:
        raise ValueError("protected 2026 game context is not allowed")

    frames: list[pl.DataFrame] = []
    coverage: dict[str, Any] = {}
    for season in SEASONS:
        print(f"{season}: loading and preparing contacts", flush=True)
        terminal = _load_terminal(args.terminal_root, season)
        prepared = prepare_terminal_contacts(
            terminal, context.filter(pl.col("season") == season)
        )
        dated = prepared.filter(pl.col("game_date").is_not_null())
        air = prepare_air_contact_history(
            dated,
            window_days=args.window_days,
        )
        coverage[str(season)] = {
            "terminal_rows": terminal.height,
            "eligible_contacts": prepared.height,
            "dated_contacts": dated.height,
            "air_contacts": air.height,
            "dated_contact_rate": float(dated.height / prepared.height),
        }
        frames.append(air)
        print(f"  air contacts={air.height:,}", flush=True)
    events = pl.concat(frames, how="vertical_relaxed").sort(
        ["game_date", "game_pk", "at_bat_index"]
    )
    base_probability = _base_probabilities(events)
    events = events.with_columns(pl.Series("base_hr_probability", base_probability))
    adjusted, adjustments = apply_crossfit_regime_adjustments(
        events,
        prior_exposure=args.regime_prior,
    )
    annual_players = aggregate_player_ball_features(adjusted)
    annual_environment = _annual_environment(adjusted)
    output = args.output_root
    table_root = output / "tables"
    output.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "events": write_canonical_parquet(
            adjusted.select(*COMPACT_EVENT_COLUMNS),
            table_root / "air-contact-ball-adjustments.parquet",
            table_name="hitter_ball_environment_air_contact_adjustments_v1",
        ).as_record(),
        "regimes": write_canonical_parquet(
            adjustments,
            table_root / "ball-regime-adjustments.parquet",
            table_name="hitter_ball_environment_regimes_v1",
        ).as_record(),
        "player_features": write_canonical_parquet(
            annual_players,
            table_root / "player-season-features.parquet",
            table_name="hitter_ball_environment_player_seasons_v1",
        ).as_record(),
        "annual_environment": write_canonical_parquet(
            annual_environment,
            table_root / "annual-level-environment.parquet",
            table_name="hitter_ball_environment_annual_level_v1",
        ).as_record(),
    }
    base = binary_metrics(
        adjusted["is_hr"].to_numpy(), adjusted["base_hr_probability"].to_numpy()
    )
    with_regime = binary_metrics(
        adjusted["is_hr"].to_numpy(), adjusted["regime_hr_probability"].to_numpy()
    )
    report = {
        "schema_version": "0.1",
        "status": "affiliated_ball_environment_materialized",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "seasons": list(SEASONS),
        "missing_2020_milb_season_expected": True,
        "scope": (
            "affiliated minor-league air-contact results; MLB drag data is not "
            "present in the local event source"
        ),
        "method": {
            "base": (
                "two-fold game-held-out LightGBM HR expectation from contact shape, "
                "spray, handedness, venue, weather, dimensions, and strictly-prior "
                "hitter/pitcher air-contact HR history"
            ),
            "regime": (
                f"level by {args.window_days}-day period; estimated on the opposite "
                f"game fold with a {args.regime_prior:g}-contact neutral prior"
            ),
            "forecast_role": (
                "descriptive environment and candidate historical neutralization; "
                "never a player skill label or assumed future ball"
            ),
        },
        "events": adjusted.height,
        "players": adjusted["player_id"].n_unique(),
        "coverage": coverage,
        "base": base,
        "with_ball_regime": with_regime,
        "regime_minus_base": {
            key: with_regime[key] - base[key] for key in ("log_loss", "brier")
        },
        "metrics": _metric_slices(adjusted),
        "sources": {
            "game_context": {
                "path": str(args.game_context),
                "sha256": sha256_file(args.game_context),
            },
            "terminal_root": str(args.terminal_root),
        },
        "artifacts": artifacts,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "events": report["events"],
                "base": base,
                "with_ball_regime": with_regime,
                "regime_minus_base": report["regime_minus_base"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
