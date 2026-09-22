#!/usr/bin/env python3
"""Freeze the selected full hitter stack before opening 2026 outcomes."""

from __future__ import annotations

import argparse
from dataclasses import fields
from datetime import UTC, date, datetime
import gzip
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.current_baserunning import (
    build_advancement_history,
    build_current_baserunning_rates,
    build_steal_history,
)
from universal_baseball.hitter_model_tournament import make_engine_models
from universal_baseball.hitter_target_architecture import (
    _lgbm_classifier,
    _lgbm_regressor,
    feature_columns,
    matrix_from_panel,
)
from universal_baseball.hitter_value_panel import (
    build_hitter_contact_features,
    build_hitter_forecast_panel,
)
from universal_baseball.player_value_baserunning_runs import BaserunningReference
from universal_baseball.player_value_baserunning_sources import (
    parse_savant_baserunning_csv,
)
from universal_baseball.player_value_positional_adjustment import (
    POSITIONAL_RUNS_PER_162,
)
from universal_baseball.position_role_profile import (
    BATTING_ROLE_POSITIONS,
    build_batting_role_profiles,
)
from universal_baseball.position_role_transition import (
    transition_smoothed_prediction,
    validate_role_vector,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


SOURCE_SEASON = 2025
TARGET_SEASON = 2026
RUNS_PER_WIN = 10.0
RANDOM_STATE = 417
ENGINES = ("xgboost", "ebm", "ridge")
HISTORY_YEARS = (2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024, 2025)
PANEL_PATH = Path("reports/generated/hitter-value-panel-v2/tables/modeling-panel.parquet")
STAT_FEATURE_PATH = Path(
    "reports/generated/hitter-value-panel-v2/tables/hitter-stat-features.parquet"
)
CONTACT_FEATURE_PATH = Path(
    "reports/generated/hitter-value-panel-v2/tables/hitter-contact-features.parquet"
)
VALUE_TARGET_PATH = Path(
    "reports/generated/hitter-value-panel-v2/tables/hitter-value-targets.parquet"
)
OPPORTUNITY_ROOT = Path(
    "model_artifacts/opportunity-v2-2026-confirmation-forecast-2026-09-09"
)
CATCHER_HISTORY_PATH = Path(
    "reports/generated/hitter-catcher-defense-value-v2/"
    "public-catcher-history-2022-2025.parquet"
)
CATCHER_RESIDUAL_PATH = Path(
    "reports/generated/hitter-catcher-defense-value-v2/"
    "chronological-predictions.parquet"
)
POSITION_PARAMETER_PATH = Path("docs/position-role-confirmation-parameters.json")
DEFENSE_CONVERSION_PATH = Path(
    "docs/player-value-v1-defense-native-run-conversion-parameters.json"
)
BASERUNNING_REFERENCE_PATH = Path(
    "docs/player-value-v1-baserunning-run-conversion-2024.json"
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-root", type=Path, required=True)
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(
            "model_artifacts/hitter-full-2026-confirmation-forecast-2026-09-20"
        ),
    )
    return parser.parse_args()


def _is_contact_feature(column: str) -> bool:
    if not column.startswith(("lag0__", "lag1__", "lag2__")):
        return False
    field = column.split("__", 1)[1]
    return (
        field
        in {
            "contact_events",
            "log_contact_events",
            "contact_highest_level",
            "contact_feature_available",
        }
        or field.startswith("contacts_level__")
        or field.startswith("contact_cell_rate__")
    )


def _load_ages(root: Path) -> tuple[pl.DataFrame, list[Path]]:
    paths = [
        root / f"hitter-multiyear-age-level-base/tables/annual-{year}.parquet"
        for year in HISTORY_YEARS
    ]
    frames = [
        pl.read_parquet(path)
        .select("player_id", "age", "relative_age", "age_missing")
        .with_columns(pl.lit(year).alias("season"))
        for year, path in zip(HISTORY_YEARS, paths, strict=True)
    ]
    return pl.concat(frames, how="vertical_relaxed"), paths


def _forecast_panel(root: Path) -> tuple[pl.DataFrame, list[Path]]:
    stats = pl.read_parquet(STAT_FEATURE_PATH)
    historical_contacts = pl.read_parquet(CONTACT_FEATURE_PATH).filter(
        pl.col("season") < SOURCE_SEASON
    )
    official_path = (
        root
        / "official-full-bip-context-2025/tables/"
        "hitter_full_bip_event_outcomes.parquet"
    )
    official_contacts = build_hitter_contact_features(pl.read_parquet(official_path))
    contacts = pl.concat(
        [historical_contacts, official_contacts], how="vertical_relaxed"
    )
    ages, age_paths = _load_ages(root)
    panel = build_hitter_forecast_panel(
        stats, contacts, ages, origin=SOURCE_SEASON
    )
    return panel, [STAT_FEATURE_PATH, CONTACT_FEATURE_PATH, official_path, *age_paths]


def _fit_two_part(
    engine: str,
    x_train: np.ndarray,
    x_score: np.ndarray,
    active: np.ndarray,
    war: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    models = make_engine_models(engine, RANDOM_STATE, "balanced")
    models.classifier.fit(x_train, active)
    probability = models.classifier.predict_proba(x_score)[:, 1]
    models.regressor.fit(x_train[active == 1], war[active == 1])
    conditional = models.regressor.predict(x_score)
    return np.clip(probability, 0.0, 1.0), np.asarray(conditional)


def _fit_active_probability(
    engine: str,
    x_train: np.ndarray,
    x_score: np.ndarray,
    active: np.ndarray,
) -> np.ndarray:
    models = make_engine_models(engine, RANDOM_STATE, "balanced")
    models.classifier.fit(x_train, active)
    return np.clip(models.classifier.predict_proba(x_score)[:, 1], 0.0, 1.0)


def _batting_predictions(
    training: pl.DataFrame, scoring: pl.DataFrame
) -> tuple[pl.DataFrame, float]:
    columns = feature_columns(training)
    missing = sorted(set(columns) - set(scoring.columns))
    if missing:
        raise ValueError(f"forecast panel lacks training features: {missing}")
    x_train = matrix_from_panel(training, columns)
    x_score = matrix_from_panel(scoring, columns)
    active = training["target_mlb_active"].to_numpy().astype(np.int8)
    war = training["target_component_war"].to_numpy()
    target_pa = training["target_mlb_pa"].to_numpy()
    active_rows = active == 1

    active_lgbm = _lgbm_classifier(RANDOM_STATE)
    active_lgbm.fit(x_train, active)
    probability_lgbm = active_lgbm.predict_proba(x_score)[:, 1]
    direct = _lgbm_regressor(RANDOM_STATE + 1)
    direct.fit(x_train, war)
    direct_prediction = direct.predict(x_score)
    pa_model = _lgbm_regressor(RANDOM_STATE + 3)
    pa_model.fit(x_train[active_rows], target_pa[active_rows])
    conditional_pa = pa_model.predict(x_score)
    rate_model = _lgbm_regressor(RANDOM_STATE + 4)
    rate_model.fit(
        x_train[active_rows],
        training["target_conditional_component_war_per_600"].to_numpy()[
            active_rows
        ],
        sample_weight=np.sqrt(np.maximum(target_pa[active_rows], 1.0)),
    )
    conditional_rate = rate_model.predict(x_score)
    conditional_three_part = (
        np.clip(conditional_pa, 0.0, 750.0)
        * np.clip(conditional_rate, -5.0, 10.0)
        / 600.0
    )
    three_part = probability_lgbm * conditional_three_part

    probabilities = {"lightgbm": probability_lgbm}
    conditionals = {"three_part_lightgbm": conditional_three_part}
    members = {
        "direct_lightgbm": direct_prediction,
        "three_part_lightgbm": three_part,
    }
    for engine in ENGINES:
        probability, conditional = _fit_two_part(
            engine, x_train, x_score, active, war
        )
        probabilities[engine] = probability
        conditionals[f"two_part_{engine}"] = conditional
        members[f"two_part_{engine}"] = probability * conditional

    stats_columns = [column for column in columns if not _is_contact_feature(column)]
    stats_train = matrix_from_panel(training, stats_columns)
    stats_score = matrix_from_panel(scoring, stats_columns)
    stats_lgbm = _lgbm_classifier(RANDOM_STATE)
    stats_lgbm.fit(stats_train, active)
    stats_probabilities = [stats_lgbm.predict_proba(stats_score)[:, 1]]
    for engine in ENGINES:
        stats_probabilities.append(
            _fit_active_probability(engine, stats_train, stats_score, active)
        )
    stats_probability = np.mean(stats_probabilities, axis=0)
    routed_members = [
        direct_prediction,
        stats_probability * conditionals["three_part_lightgbm"],
        *[
            stats_probability * conditionals[f"two_part_{engine}"]
            for engine in ENGINES
        ],
    ]
    selected = np.mean(list(members.values()), axis=0)
    routed = np.mean(routed_members, axis=0)
    frame = scoring.select(
        "player_id",
        "lag0__highest_level",
        "lag0__plate_appearances",
        "lag0__pa_level__MLB",
        "lag0__contact_feature_available",
        "lag0__contact_events",
    ).with_columns(
        pl.lit("five_model_detailed_contact").alias("batting_evidence_tier"),
        pl.Series("prediction_batting_replacement_war", selected),
        pl.Series("prediction_routed_batting_replacement_war", routed),
        pl.Series("prediction_model_active_probability", np.mean(list(probabilities.values()), axis=0)),
        pl.Series("prediction_stats_only_active_probability", stats_probability),
        *[
            pl.Series(f"prediction_member__{name}", prediction)
            for name, prediction in members.items()
        ],
    )
    prior_rate = float(war.sum() / np.maximum(target_pa.sum(), 1.0) * 600.0)
    return frame, prior_rate


def _position_components(root: Path, players: pl.DataFrame) -> tuple[pl.DataFrame, Path]:
    path = (
        root
        / "position-capacity-source/2025/reports/generated/"
        "position-role-2025-confirmation-source/tables/"
        "position_role_2025_fielding_usage.parquet"
    )
    fielding = pl.read_parquet(path)
    built = build_batting_role_profiles(fielding)
    profiles: dict[int, np.ndarray] = {}
    for row in built.profile.select(
        "player_id", "position_abbreviation", "role_probability"
    ).iter_rows(named=True):
        vector = profiles.setdefault(
            int(row["player_id"]), np.zeros(len(BATTING_ROLE_POSITIONS))
        )
        vector[BATTING_ROLE_POSITIONS.index(str(row["position_abbreviation"]))] = float(
            row["role_probability"]
        )
    summaries = {
        int(row["player_id"]): (
            str(row["primary_position"]),
            float(row["primary_role_share"]),
        )
        for row in built.player_season.select(
            "player_id", "primary_position", "primary_role_share"
        ).iter_rows(named=True)
    }
    payload = json.loads(POSITION_PARAMETER_PATH.read_text(encoding="utf-8"))
    parameters = payload["parameters"]
    threshold = float(parameters["primary_share_threshold"])
    destinations = {
        source: validate_role_vector(
            np.array(
                [
                    float(details["probabilities"][destination])
                    for destination in BATTING_ROLE_POSITIONS
                ]
            )
        )
        for source, details in parameters["destination_means"].items()
    }
    rows = []
    for player_id in players["player_id"].to_list():
        player_id = int(player_id)
        current = profiles.get(player_id)
        summary = summaries.get(player_id)
        if current is None or summary is None:
            rows.append(
                {
                    "player_id": player_id,
                    "position_profile_available": 0,
                    "prediction_position_runs_per_600": 0.0,
                }
            )
            continue
        current = validate_role_vector(current)
        primary, share = summary
        predicted = (
            transition_smoothed_prediction(
                current,
                primary_share=share,
                destination_mean=destinations[primary],
            )
            if share >= threshold
            else current
        )
        rate = sum(
            predicted[index] * POSITIONAL_RUNS_PER_162[position]
            for index, position in enumerate(BATTING_ROLE_POSITIONS)
        )
        rows.append(
            {
                "player_id": player_id,
                "position_profile_available": 1,
                "prediction_position_runs_per_600": float(rate),
            }
        )
    return pl.DataFrame(rows), path


def _baserunning_reference() -> BaserunningReference:
    payload = json.loads(BASERUNNING_REFERENCE_PATH.read_text(encoding="utf-8"))
    values = payload["reference"]
    return BaserunningReference(
        **{field.name: values[field.name] for field in fields(BaserunningReference)}
    )


def _baserunning_components(
    root: Path, players: pl.DataFrame
) -> tuple[pl.DataFrame, list[Path]]:
    component_path = (
        root / "phase2-arrival-skill-source/tables/affiliated_hitting_components.parquet"
    )
    components = pl.read_parquet(component_path).filter(
        pl.col("season").is_between(2023, SOURCE_SEASON)
    )
    steal_history, _ = build_steal_history(components)
    raw_root = root / "current-baserunning-rates/2026-09-08/raw"
    raw_paths = [raw_root / f"savant-baserunning-{year}.csv.gz" for year in range(2023, 2026)]
    rows_by_season = {
        year: parse_savant_baserunning_csv(
            gzip.decompress(path.read_bytes()).decode("utf-8-sig")
        )
        for year, path in zip(range(2023, 2026), raw_paths, strict=True)
    }
    advancement_history = build_advancement_history(rows_by_season)
    rates = build_current_baserunning_rates(
        players.select("player_id"),
        steal_history,
        advancement_history,
        forecast_seasons=(TARGET_SEASON,),
        reference=_baserunning_reference(),
    ).drop("season")
    return rates, [component_path, *raw_paths]


def _catcher_components(players: pl.DataFrame) -> pl.DataFrame:
    history = pl.read_parquet(CATCHER_HISTORY_PATH)
    source = history.filter(pl.col("season") == SOURCE_SEASON)
    conversion = json.loads(DEFENSE_CONVERSION_PATH.read_text(encoding="utf-8"))
    rows = []
    for component in ("throwing", "blocking", "framing"):
        component_history = history.filter(pl.col("component") == component)
        earlier = component_history.select(
            pl.col("season").alias("origin_year"),
            "player_id",
            pl.col("skill_z").alias("source_skill"),
        ).join(
            component_history.select(
                (pl.col("season") - 1).alias("origin_year"),
                "player_id",
                pl.col("skill_z").alias("target_skill"),
            ),
            on=["origin_year", "player_id"],
            how="inner",
        ).filter(pl.col("origin_year") < SOURCE_SEASON)
        x = earlier["source_skill"].to_numpy()
        y = earlier["target_skill"].to_numpy()
        denominator = float(np.dot(x, x))
        slope = 0.0 if denominator <= 1e-12 else float(np.dot(x, y) / denominator)
        slope = float(np.clip(slope, 0.0, 1.0))
        rate = float(conversion[f"catcher_{component}"]["run_rate_per_z_opportunity"])
        rows.append(
            source.filter(pl.col("component") == component).select(
                "player_id",
                pl.lit(component).alias("component"),
                pl.col("opportunity").alias("source_opportunity"),
                (pl.col("skill_z") * slope).alias("prediction_skill_z"),
                pl.lit(rate).alias("run_rate_per_z_opportunity"),
                pl.lit(slope).alias("chronological_skill_slope"),
            )
        )
    evidence = pl.concat(rows, how="vertical_relaxed")
    expanded = players.select(
        "player_id", "prediction_expected_mlb_pa", "source_mlb_pa"
    ).join(
        pl.DataFrame({"component": ["throwing", "blocking", "framing"]}),
        how="cross",
    ).join(evidence, on=["player_id", "component"], how="left")
    return (
        expanded.with_columns(
            pl.col("source_opportunity").fill_null(0.0),
            pl.col("prediction_skill_z").fill_null(0.0),
            pl.col("run_rate_per_z_opportunity").fill_null(0.0),
        )
        .with_columns(
            pl.when(pl.col("source_mlb_pa") > 0)
            .then(
                pl.col("source_opportunity")
                * pl.col("prediction_expected_mlb_pa")
                / pl.col("source_mlb_pa")
            )
            .otherwise(0.0)
            .alias("prediction_native_opportunity")
        )
        .with_columns(
            (
                pl.col("prediction_skill_z")
                * pl.col("prediction_native_opportunity")
                * pl.col("run_rate_per_z_opportunity")
            ).alias("prediction_catcher_runs")
        )
        .group_by("player_id")
        .agg(
            pl.col("prediction_catcher_runs").sum(),
            (pl.col("source_opportunity") > 0).any().cast(pl.Int8).alias(
                "catcher_evidence_available"
            ),
        )
    )


def _interval_offsets() -> pl.DataFrame:
    source = pl.read_parquet(CATCHER_RESIDUAL_PATH).filter(
        pl.col("origin_year") == 2024
    )
    source = source.with_columns(
        (
            pl.col("actual_partial_war_with_catcher")
            - pl.col("prediction_total_chronological_skill_pa_scaled_opportunity")
        ).alias("residual")
    )
    rows = []
    for stage in ("current_mlb", "upper_minors", "lower_minors"):
        residual = source.filter(pl.col("player_stage") == stage)["residual"]
        for confidence in (0.5, 0.8, 0.9):
            tail = (1.0 - confidence) / 2.0
            rows.append(
                {
                    "player_stage": stage,
                    "confidence": confidence,
                    "calibration_rows": residual.len(),
                    "lower_residual_offset": float(residual.quantile(tail)),
                    "upper_residual_offset": float(residual.quantile(1.0 - tail)),
                }
            )
    all_residual = source["residual"]
    for confidence in (0.5, 0.8, 0.9):
        tail = (1.0 - confidence) / 2.0
        rows.append(
            {
                "player_stage": "no_2025_record",
                "confidence": confidence,
                "calibration_rows": all_residual.len(),
                "lower_residual_offset": float(all_residual.quantile(tail)),
                "upper_residual_offset": float(all_residual.quantile(1.0 - tail)),
            }
        )
    return pl.DataFrame(rows)


def _add_intervals(frame: pl.DataFrame, offsets: pl.DataFrame) -> pl.DataFrame:
    result = frame
    for confidence, label in ((0.5, "50"), (0.8, "80"), (0.9, "90")):
        selected = offsets.filter(pl.col("confidence") == confidence).select(
            "player_stage", "lower_residual_offset", "upper_residual_offset"
        )
        result = result.join(selected, on="player_stage", how="left").with_columns(
            (
                pl.col("prediction_selected_partial_war")
                + pl.col("lower_residual_offset")
            ).alias(f"selected_lower_{label}"),
            (
                pl.col("prediction_selected_partial_war")
                + pl.col("upper_residual_offset")
            ).alias(f"selected_upper_{label}"),
        ).drop("lower_residual_offset", "upper_residual_offset")
    return result


def main() -> int:
    args = _args()
    if args.as_of_date.year != TARGET_SEASON:
        raise ValueError("the 2026 freeze requires a 2026 packaging date")
    training = pl.read_parquet(PANEL_PATH)
    forecast_panel, panel_inputs = _forecast_panel(args.generated_root)
    batting, prior_rate = _batting_predictions(training, forecast_panel)

    opportunity = pl.read_parquet(OPPORTUNITY_ROOT / "hitter-selected.parquet").select(
        "player_id",
        pl.col("predicted_any_mlb_pa_probability").alias(
            "prediction_mlb_active_probability"
        ),
        pl.col("predicted_positive_mlb_pa_mean").alias(
            "prediction_positive_mlb_pa"
        ),
        pl.col("predicted_expected_mlb_pa").alias("prediction_expected_mlb_pa"),
        pl.col("model_id").alias("opportunity_model_id"),
    )
    incumbent = pl.read_parquet(OPPORTUNITY_ROOT / "hitter-incumbent.parquet").select(
        "player_id",
        pl.col("predicted_any_mlb_pa_probability").alias(
            "benchmark_incumbent_active_probability"
        ),
        pl.col("predicted_expected_mlb_pa").alias(
            "benchmark_incumbent_expected_mlb_pa"
        ),
    )
    parametric = pl.read_parquet(
        OPPORTUNITY_ROOT / "hitter-parametric-baseline.parquet"
    ).select(
        "player_id",
        pl.col("predicted_any_mlb_pa_probability").alias(
            "benchmark_parametric_active_probability"
        ),
        pl.col("predicted_expected_mlb_pa").alias(
            "benchmark_parametric_expected_mlb_pa"
        ),
    )
    frame = opportunity.join(incumbent, on="player_id", validate="1:1").join(
        parametric, on="player_id", validate="1:1"
    ).join(batting, on="player_id", how="left", validate="1:1")
    frame = frame.with_columns(
        pl.when(pl.col("lag0__pa_level__MLB") > 0)
        .then(pl.lit("current_mlb"))
        .when(pl.col("lag0__highest_level").is_in(["AA", "AAA"]))
        .then(pl.lit("upper_minors"))
        .when(pl.col("lag0__highest_level").is_not_null())
        .then(pl.lit("lower_minors"))
        .otherwise(pl.lit("no_2025_record"))
        .alias("player_stage")
    ).with_columns(
        pl.when(pl.col("prediction_batting_replacement_war").is_null())
        .then(pl.col("prediction_expected_mlb_pa") * prior_rate / 600.0)
        .otherwise(pl.col("prediction_batting_replacement_war"))
        .alias("prediction_batting_replacement_war"),
        pl.when(pl.col("prediction_routed_batting_replacement_war").is_null())
        .then(pl.col("prediction_expected_mlb_pa") * prior_rate / 600.0)
        .otherwise(pl.col("prediction_routed_batting_replacement_war"))
        .alias("prediction_routed_batting_replacement_war"),
        pl.when(pl.col("batting_evidence_tier").is_null())
        .then(pl.lit("opportunity_scaled_population_rate_prior"))
        .otherwise(pl.col("batting_evidence_tier"))
        .alias("batting_evidence_tier"),
        pl.col("lag0__pa_level__MLB").fill_null(0.0).alias("source_mlb_pa"),
    )
    member_columns = [
        column for column in frame.columns if column.startswith("prediction_member__")
    ]
    frame = frame.with_columns(
        *[
            pl.col(column)
            .fill_null(pl.col("prediction_batting_replacement_war"))
            .alias(column)
            for column in member_columns
        ],
        pl.col("prediction_model_active_probability").fill_null(
            pl.col("prediction_mlb_active_probability")
        ),
        pl.col("prediction_stats_only_active_probability").fill_null(
            pl.col("prediction_mlb_active_probability")
        ),
    )

    position, position_path = _position_components(args.generated_root, frame)
    baserunning, baserunning_inputs = _baserunning_components(
        args.generated_root, frame
    )
    frame = frame.join(position, on="player_id", how="left", validate="1:1").join(
        baserunning, on="player_id", how="left", validate="1:1"
    )
    catcher = _catcher_components(frame)
    frame = frame.join(catcher, on="player_id", how="left", validate="1:1").with_columns(
        (
            pl.col("prediction_expected_mlb_pa")
            / 600.0
            * pl.col("prediction_position_runs_per_600")
            / RUNS_PER_WIN
        ).alias("prediction_position_war"),
        (
            pl.col("prediction_expected_mlb_pa")
            / 600.0
            * pl.col("steal_runs_per_600")
            / RUNS_PER_WIN
        ).alias("prediction_steal_war"),
        (
            pl.col("prediction_expected_mlb_pa")
            / 600.0
            * pl.col("advancement_runs_per_600")
            / RUNS_PER_WIN
        ).alias("prediction_advancement_war"),
        (pl.col("prediction_catcher_runs") / RUNS_PER_WIN).alias(
            "prediction_catcher_defense_war"
        ),
    ).with_columns(
        (pl.col("prediction_steal_war") + pl.col("prediction_advancement_war")).alias(
            "prediction_baserunning_war"
        )
    ).with_columns(
        (
            pl.col("prediction_batting_replacement_war")
            + pl.col("prediction_position_war")
            + pl.col("prediction_baserunning_war")
            + pl.col("prediction_catcher_defense_war")
        ).alias("prediction_selected_partial_war"),
        (
            pl.col("prediction_routed_batting_replacement_war")
            + pl.col("prediction_position_war")
            + pl.col("prediction_baserunning_war")
            + pl.col("prediction_catcher_defense_war")
        ).alias("prediction_routed_partial_war"),
        pl.lit(0.0).alias("prediction_general_defense_war"),
        pl.lit(SOURCE_SEASON).alias("source_season"),
        pl.lit(TARGET_SEASON).alias("forecast_season"),
    )

    previous = pl.read_parquet(VALUE_TARGET_PATH).filter(
        pl.col("season") == SOURCE_SEASON
    ).select(
        "player_id",
        pl.col("component_war").alias("benchmark_previous_batting_replacement_war"),
    )
    frame = frame.join(previous, on="player_id", how="left").with_columns(
        pl.col("benchmark_previous_batting_replacement_war").fill_null(0.0),
        pl.lit(float(training["target_component_war"].mean())).alias(
            "benchmark_training_mean_batting_replacement_war"
        ),
        pl.lit(0.0).alias("benchmark_zero_batting_replacement_war"),
    )
    offsets = _interval_offsets()
    frame = _add_intervals(frame, offsets).sort("player_id")
    if frame.height != opportunity.height or frame["player_id"].n_unique() != frame.height:
        raise RuntimeError("frozen full hitter population changed or duplicated")
    protected_names = [
        column
        for column in frame.columns
        if column.startswith("actual_") or column.startswith("target_")
    ]
    if protected_names:
        raise RuntimeError(f"protected outcomes entered forecast: {protected_names}")

    args.output_root.mkdir(parents=True, exist_ok=True)
    forecast_artifact = write_canonical_parquet(
        frame,
        args.output_root / "forecast-2026.parquet",
        table_name="hitter_full_2026_frozen_forecast",
    ).as_record()
    input_artifact = write_canonical_parquet(
        forecast_panel,
        args.output_root / "forecast-inputs-2025.parquet",
        table_name="hitter_full_2026_forecast_inputs",
    ).as_record()
    offset_artifact = write_canonical_parquet(
        offsets,
        args.output_root / "interval-offsets.parquet",
        table_name="hitter_full_2026_interval_offsets",
    ).as_record()
    sources = [
        PANEL_PATH,
        VALUE_TARGET_PATH,
        *panel_inputs,
        OPPORTUNITY_ROOT / "hitter-selected.parquet",
        OPPORTUNITY_ROOT / "hitter-incumbent.parquet",
        OPPORTUNITY_ROOT / "hitter-parametric-baseline.parquet",
        position_path,
        POSITION_PARAMETER_PATH,
        *baserunning_inputs,
        BASERUNNING_REFERENCE_PATH,
        CATCHER_HISTORY_PATH,
        DEFENSE_CONVERSION_PATH,
        CATCHER_RESIDUAL_PATH,
    ]
    manifest = {
        "schema_version": "1.0",
        "status": "frozen_before_2026_evaluation",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "packaging_as_of_date": args.as_of_date.isoformat(),
        "source_season": SOURCE_SEASON,
        "forecast_season": TARGET_SEASON,
        "protected_2026_participants_or_outcomes_opened": False,
        "population": {
            "rows": frame.height,
            "five_model_batting_rows": int(
                (frame["batting_evidence_tier"] == "five_model_detailed_contact").sum()
            ),
            "population_prior_rows": int(
                (
                    frame["batting_evidence_tier"]
                    == "opportunity_scaled_population_rate_prior"
                ).sum()
            ),
            "contact_available_rows": int(
                (frame["lag0__contact_feature_available"].fill_null(0) == 1).sum()
            ),
        },
        "selected_stack": {
            "batting_plus_replacement": (
                "equal mean of direct LightGBM, three-part LightGBM, "
                "two-part XGBoost, two-part EBM, and two-part ridge"
            ),
            "opportunity": "frozen opportunity-v2 selected hitter forecast",
            "position": "frozen role transition scaled by expected MLB PA",
            "baserunning": "B2_k5 attempts, B2_k45 success, A2_k25 advancement",
            "catcher_defense": (
                "chronologically shrunk throwing, blocking, and framing skill "
                "with PA-scaled native opportunity"
            ),
            "general_defense": "neutral zero; rejected development component",
            "intervals": (
                "stage-specific empirical residual quantiles from the exposed "
                "2025 full-stack forecast"
            ),
        },
        "challengers_and_benchmarks": {
            "routed": (
                "stats-only arrival probability with detailed-contact conditional value"
            ),
            "opportunity": ["parametric level baseline", "incumbent cohort"],
            "batting": ["previous-season WAR", "training mean", "zero"],
        },
        "fallback": {
            "rows": int(
                (
                    frame["batting_evidence_tier"]
                    == "opportunity_scaled_population_rate_prior"
                ).sum()
            ),
            "rule": (
                "players in the locked opportunity universe without a 2025 batting "
                "record receive frozen expected PA times the development-population "
                "batting-plus-replacement WAR rate per 600"
            ),
            "war_rate_per_600": prior_rate,
        },
        "artifacts": {
            "forecast": forecast_artifact,
            "forecast_inputs": input_artifact,
            "interval_offsets": offset_artifact,
        },
        "input_files": [
            {"path": str(path), "sha256": sha256_file(path)} for path in sources
        ],
        "scoring_lock": (
            "Do not evaluate, refit, select, or alter this forecast using any 2026 "
            "participant or outcome evidence until the regular season is complete "
            "and the separate confirmation contract authorizes one evaluation."
        ),
    }
    (args.output_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
