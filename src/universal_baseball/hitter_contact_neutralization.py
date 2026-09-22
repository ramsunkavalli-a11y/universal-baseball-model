"""Cross-fitted context neutralization for historical hitter contact outcomes.

The event model is deliberately descriptive, not a player forecast.  It asks
what normally happened to a batted ball with the same observable contact shape
and, in the full version, the same game environment and opposition.  A batter's
feature is the held-out difference between the observed result and that
expectation.  Holding complete batters out of the event fit prevents a player's
own outcomes from teaching the model how to score that player.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import numpy as np
import polars as pl

from universal_baseball.batted_ball_direction import (
    batted_ball_direction_expr,
    field_spray_angle_expr,
)
from universal_baseball.hitter_gradient_materialization import (
    CONTACT_BINS,
    CONTACT_OUTCOMES,
)


PHYSICAL_CATEGORICAL = (
    "level",
    "core_bin",
    "stand",
    "p_throws",
    "inning_top_bot",
)
PHYSICAL_NUMERIC = (
    "spray_angle",
    "inning",
    "outs_when_up",
    "on_1b_present",
    "on_2b_present",
    "on_3b_present",
    "score_difference",
)
CONTEXT_CATEGORICAL = (
    "venue_id",
    "day_night",
    "turf_type",
    "roof_type",
    "weather_condition",
    "wind_direction",
    "game_month",
)
OPPONENT_CATEGORICAL = ("defense_team", "pitcher")
CONTEXT_NUMERIC = (
    "temperature_f",
    "wind_mph",
    "venue_latitude",
    "venue_longitude",
    "left_field_line_ft",
    "center_field_ft",
    "right_field_line_ft",
    "first_pitch_hour_utc",
)


@dataclass(frozen=True)
class EncodedContactMatrix:
    """A dense event matrix plus indices LightGBM should treat categorically."""

    values: np.ndarray
    feature_names: tuple[str, ...]
    categorical_indices: tuple[int, ...]


def _require(frame: pl.DataFrame, columns: set[str], label: str) -> None:
    if missing := sorted(columns - set(frame.columns)):
        raise ValueError(f"{label} missing fields: {missing}")


def prepare_terminal_contacts(
    terminal: pl.DataFrame, game_context: pl.DataFrame
) -> pl.DataFrame:
    """Create one eligible, context-enriched row per historical batted ball."""

    _require(
        terminal,
        {
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
        },
        "terminal PBP",
    )
    _require(
        game_context,
        {
            "season",
            "game_pk",
            "game_date",
            "first_pitch_datetime_utc",
            "day_night",
            "venue_id",
            "venue_latitude",
            "venue_longitude",
            "turf_type",
            "roof_type",
            "left_field_line_ft",
            "center_field_ft",
            "right_field_line_ft",
            "weather_condition",
            "temperature_f",
            "wind_mph",
            "wind_direction",
        },
        "game context",
    )
    if terminal.filter(pl.col("season") >= 2026).height:
        raise ValueError("protected 2026 events are not allowed")

    direction = batted_ball_direction_expr(
        pl.col("hc_x"), pl.col("hc_y"), pl.col("stand")
    )
    direction_prefix = (
        pl.when(direction == "pull")
        .then(pl.lit("PULL"))
        .when(direction == "center")
        .then(pl.lit("CENTER"))
        .when(direction == "opposite")
        .then(pl.lit("OPPO"))
        .otherwise(pl.lit(None, dtype=pl.String))
    )
    trajectory = (
        pl.when(pl.col("bb_type") == "ground_ball")
        .then(pl.lit("GB"))
        .when(pl.col("bb_type") == "line_drive")
        .then(pl.lit("LD"))
        .when(pl.col("bb_type") == "fly_ball")
        .then(pl.lit("OFFB"))
        .when(pl.col("bb_type") == "popup")
        .then(pl.lit("IFFB"))
        .otherwise(pl.lit(None, dtype=pl.String))
    )
    core_bin = (
        pl.when(trajectory == "IFFB")
        .then(pl.lit("IFFB"))
        .when(trajectory.is_in(["GB", "LD", "OFFB"]) & direction_prefix.is_not_null())
        .then(pl.concat_str([direction_prefix, trajectory], separator="_"))
        .otherwise(pl.lit(None, dtype=pl.String))
    )
    outcome = (
        pl.when(pl.col("terminal_outcome_group") == "OUT")
        .then(pl.lit("OTHER_OUT"))
        .otherwise(pl.col("terminal_outcome_group"))
    )
    contacts = (
        terminal.filter(pl.col("is_batted_ball").fill_null(False))
        .with_columns(
            field_spray_angle_expr(pl.col("hc_x"), pl.col("hc_y")).alias("spray_angle"),
            core_bin.alias("core_bin"),
            outcome.alias("canonical_outcome"),
            pl.col("on_1b").is_not_null().cast(pl.Int8).alias("on_1b_present"),
            pl.col("on_2b").is_not_null().cast(pl.Int8).alias("on_2b_present"),
            pl.col("on_3b").is_not_null().cast(pl.Int8).alias("on_3b_present"),
            (pl.col("bat_score") - pl.col("fld_score")).alias("score_difference"),
        )
        .filter(
            pl.col("batter").is_not_null()
            & pl.col("core_bin").is_in(CONTACT_BINS)
            & pl.col("canonical_outcome").is_in(CONTACT_OUTCOMES)
            & pl.col("stand").is_in(["L", "R"])
            & pl.col("p_throws").is_in(["L", "R"])
        )
    )
    context = game_context.select(
        "season",
        "game_pk",
        pl.col("game_date").alias("_context_game_date"),
        pl.col("first_pitch_datetime_utc").alias("_context_first_pitch_utc"),
        "day_night",
        "venue_id",
        "venue_latitude",
        "venue_longitude",
        "turf_type",
        "roof_type",
        "left_field_line_ft",
        "center_field_ft",
        "right_field_line_ft",
        "weather_condition",
        "temperature_f",
        "wind_mph",
        "wind_direction",
    )
    duplicates = context.group_by("season", "game_pk").len().filter(pl.col("len") > 1)
    if not duplicates.is_empty():
        raise ValueError("game context must be unique by season/game_pk")
    return (
        contacts.join(
            context,
            on=["season", "game_pk"],
            how="left",
            validate="m:1",
        )
        .with_columns(
            pl.col("_context_game_date").dt.month().alias("game_month"),
            pl.col("_context_first_pitch_utc")
            .dt.hour()
            .cast(pl.Float32)
            .alias("first_pitch_hour_utc"),
        )
        .select(
            "season",
            "league_id",
            "level",
            pl.col("_context_game_date").alias("game_date"),
            "game_pk",
            "at_bat_index",
            "terminal_pitch_number",
            pl.col("batter").alias("player_id"),
            "pitcher",
            "defense_team",
            "venue_id",
            "core_bin",
            "canonical_outcome",
            "spray_angle",
            "stand",
            "p_throws",
            "inning_top_bot",
            "inning",
            "outs_when_up",
            "on_1b_present",
            "on_2b_present",
            "on_3b_present",
            "score_difference",
            *CONTEXT_CATEGORICAL[1:],
            *CONTEXT_NUMERIC[:-1],
            "first_pitch_hour_utc",
        )
        .sort("game_pk", "at_bat_index")
    )


def encode_contact_matrix(
    frame: pl.DataFrame,
    *,
    include_context: bool,
    include_opponent_ids: bool = True,
) -> EncodedContactMatrix:
    """Encode a full season once so cross-fit folds share category identities."""

    categorical = list(PHYSICAL_CATEGORICAL)
    numeric = list(PHYSICAL_NUMERIC)
    if include_context:
        categorical.extend(CONTEXT_CATEGORICAL)
        if include_opponent_ids:
            categorical.extend(OPPONENT_CATEGORICAL)
        numeric.extend(CONTEXT_NUMERIC)
    _require(frame, set(categorical + numeric), "contact model frame")
    arrays: list[np.ndarray] = []
    categorical_indices: list[int] = []
    names = tuple(categorical + numeric)
    for index, column in enumerate(categorical):
        values = frame[column].cast(pl.String).fill_null("__MISSING__").to_numpy()
        _, inverse = np.unique(values, return_inverse=True)
        arrays.append(inverse.astype(np.float32))
        categorical_indices.append(index)
    for column in numeric:
        values = frame[column].cast(pl.Float32, strict=False).to_numpy().copy()
        values[~np.isfinite(values)] = np.nan
        arrays.append(values)
    return EncodedContactMatrix(
        values=np.column_stack(arrays).astype(np.float32, copy=False),
        feature_names=names,
        categorical_indices=tuple(categorical_indices),
    )


def player_crossfit_fold(player_ids: np.ndarray, folds: int = 2) -> np.ndarray:
    """Assign every event for a player to one deterministic held-out fold."""

    if folds < 2:
        raise ValueError("at least two cross-fit folds are required")
    ids = np.asarray(player_ids, dtype=np.int64)
    return np.mod(ids * 1_000_003 + 97, folds).astype(np.int8)


def _contact_classifier(random_state: int) -> Any:
    from lightgbm import LGBMClassifier

    return LGBMClassifier(
        objective="multiclass",
        num_class=len(CONTACT_OUTCOMES),
        n_estimators=120,
        learning_rate=0.05,
        num_leaves=31,
        max_depth=6,
        min_child_samples=250,
        colsample_bytree=0.80,
        reg_alpha=0.25,
        reg_lambda=5.0,
        random_state=random_state,
        n_jobs=-1,
        verbosity=-1,
    )


def crossfit_contact_probabilities(
    frame: pl.DataFrame,
    *,
    folds: int = 2,
    random_state: int = 417,
    include_opponent_ids: bool = True,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Return held-out physical and full-context probabilities for every event."""

    if frame.is_empty():
        raise ValueError("contact frame is empty")
    seasons = frame["season"].unique().to_list()
    if len(seasons) != 1:
        raise ValueError("cross-fitting must be run one source season at a time")
    if int(seasons[0]) >= 2026:
        raise ValueError("protected 2026 events are not allowed")
    outcome_to_index = {value: index for index, value in enumerate(CONTACT_OUTCOMES)}
    labels = np.array(
        [outcome_to_index[value] for value in frame["canonical_outcome"].to_list()],
        dtype=np.int8,
    )
    assignments = player_crossfit_fold(frame["player_id"].to_numpy(), folds)
    physical = encode_contact_matrix(frame, include_context=False)
    context = encode_contact_matrix(
        frame,
        include_context=True,
        include_opponent_ids=include_opponent_ids,
    )
    physical_probability = np.full(
        (frame.height, len(CONTACT_OUTCOMES)), np.nan, dtype=np.float32
    )
    context_probability = np.full_like(physical_probability, np.nan)
    importances = np.zeros(len(context.feature_names), dtype=np.float64)
    fold_rows: list[dict[str, int]] = []
    for fold in range(folds):
        test = assignments == fold
        train = ~test
        if not test.any() or not train.any():
            raise ValueError(f"empty cross-fit partition {fold}")
        for matrix, destination, offset in (
            (physical, physical_probability, 0),
            (context, context_probability, 10_000),
        ):
            model = _contact_classifier(random_state + offset + fold)
            model.fit(
                matrix.values[train],
                labels[train],
                categorical_feature=list(matrix.categorical_indices),
            )
            predicted = model.predict_proba(matrix.values[test])
            aligned = np.zeros((test.sum(), len(CONTACT_OUTCOMES)), dtype=np.float32)
            aligned[:, np.asarray(model.classes_, dtype=np.int64)] = predicted
            destination[test] = aligned
            if matrix is context:
                importances += model.booster_.feature_importance(importance_type="gain")
        fold_rows.append(
            {
                "fold": fold,
                "training_events": int(train.sum()),
                "evaluation_events": int(test.sum()),
                "evaluation_players": int(
                    frame.filter(pl.Series(test))["player_id"].n_unique()
                ),
            }
        )
    if (
        not np.isfinite(physical_probability).all()
        or not np.isfinite(context_probability).all()
    ):
        raise ValueError("cross-fit probabilities are incomplete")
    report = {
        "season": int(seasons[0]),
        "events": frame.height,
        "players": frame["player_id"].n_unique(),
        "context_scope": (
            "park_weather_and_raw_opponent_ids"
            if include_opponent_ids
            else "park_and_weather_only"
        ),
        "folds": fold_rows,
        "physical_metrics": multinomial_metrics(labels, physical_probability),
        "context_metrics": multinomial_metrics(labels, context_probability),
        "context_gain_importance": {
            name: float(value / folds)
            for name, value in zip(context.feature_names, importances, strict=True)
        },
    }
    return physical_probability, context_probability, report


def multinomial_metrics(
    labels: np.ndarray, probability: np.ndarray
) -> dict[str, float]:
    """Event-weighted multiclass log loss and Brier score."""

    rows = np.arange(labels.size)
    clipped = np.clip(probability, 1e-7, 1.0)
    one_hot = np.eye(probability.shape[1], dtype=np.float32)[labels]
    return {
        "log_loss": float(-np.mean(np.log(clipped[rows, labels]))),
        "brier": float(np.mean(np.sum(np.square(probability - one_hot), axis=1))),
    }


def _normalize_probability(probability: np.ndarray) -> np.ndarray:
    clipped = np.clip(probability, 1e-6, None)
    return (clipped / clipped.sum(axis=1, keepdims=True)).astype(np.float32, copy=False)


def _group_log_probability_adjustment(
    frame: pl.DataFrame,
    train_mask: np.ndarray,
    test_mask: np.ndarray,
    train_actual: np.ndarray,
    train_probability: np.ndarray,
    keys: tuple[str, ...],
    prior: float,
) -> np.ndarray:
    """Estimate a shrunk multiplicative probability adjustment by context."""

    actual_columns = [f"_actual_{index}" for index in range(len(CONTACT_OUTCOMES))]
    probability_columns = [
        f"_probability_{index}" for index in range(len(CONTACT_OUTCOMES))
    ]
    adjustment_columns = [
        f"_adjustment_{index}" for index in range(len(CONTACT_OUTCOMES))
    ]
    training = (
        frame.filter(pl.Series(train_mask))
        .select(*keys)
        .with_columns(
            *(
                pl.Series(column, train_actual[:, index])
                for index, column in enumerate(actual_columns)
            ),
            *(
                pl.Series(column, train_probability[:, index])
                for index, column in enumerate(probability_columns)
            ),
        )
    )
    global_probability = train_probability.mean(axis=0)
    adjustment = training.group_by(*keys).agg(
        *(
            (
                (
                    (
                        pl.col(actual_columns[index]).sum()
                        + prior * global_probability[index]
                    )
                    / (
                        pl.col(probability_columns[index]).sum()
                        + prior * global_probability[index]
                    )
                )
                .log()
                .clip(-0.75, 0.75)
                .alias(adjustment_columns[index])
            )
            for index in range(len(CONTACT_OUTCOMES))
        )
    )
    test = (
        frame.filter(pl.Series(test_mask))
        .select(*keys)
        .with_row_index("_row")
        .join(adjustment, on=list(keys), how="left", validate="m:1")
        .sort("_row")
    )
    return np.column_stack(
        [test[column].fill_null(0.0).to_numpy() for column in adjustment_columns]
    ).astype(np.float32, copy=False)


def _apply_log_adjustment(
    probability: np.ndarray, adjustment: np.ndarray
) -> np.ndarray:
    log_probability = np.log(np.clip(probability, 1e-7, 1.0)) + adjustment
    log_probability -= log_probability.max(axis=1, keepdims=True)
    return _normalize_probability(np.exp(log_probability))


def crossfit_shrunk_context_probabilities(
    frame: pl.DataFrame,
    *,
    folds: int = 2,
    random_state: int = 417,
    park_prior: float = 400.0,
    defense_prior: float = 800.0,
    pitcher_prior: float = 300.0,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Layer conservative park and opponent corrections over contact expectations.

    The correction for a held-out batter is learned only from other batters.
    Raw high-cardinality identifiers never enter a tree.  Instead, each context
    receives a zero-centered outcome residual that is shrunk toward no effect.
    """

    if frame.is_empty():
        raise ValueError("contact frame is empty")
    seasons = frame["season"].unique().to_list()
    if len(seasons) != 1:
        raise ValueError("cross-fitting must be run one source season at a time")
    if int(seasons[0]) >= 2026:
        raise ValueError("protected 2026 events are not allowed")
    if any(
        not math.isfinite(value) or value <= 0
        for value in (park_prior, defense_prior, pitcher_prior)
    ):
        raise ValueError("context priors must be finite and positive")
    outcome_to_index = {value: index for index, value in enumerate(CONTACT_OUTCOMES)}
    labels = np.array(
        [outcome_to_index[value] for value in frame["canonical_outcome"].to_list()],
        dtype=np.int8,
    )
    one_hot = np.eye(len(CONTACT_OUTCOMES), dtype=np.float32)[labels]
    assignments = player_crossfit_fold(frame["player_id"].to_numpy(), folds)
    physical = encode_contact_matrix(frame, include_context=False)
    context_stages = ("park", "park_defense", "park_defense_pitcher")
    weights = (0.25, 0.50, 1.0)
    stage_names = ("physical",) + tuple(
        stage if weight == 1.0 else f"{stage}_w{int(weight * 100):03d}"
        for stage in context_stages
        for weight in weights
    )
    probabilities = {
        stage: np.full((frame.height, len(CONTACT_OUTCOMES)), np.nan, dtype=np.float32)
        for stage in stage_names
    }
    fold_rows: list[dict[str, int]] = []
    for fold in range(folds):
        test = assignments == fold
        train = ~test
        model = _contact_classifier(random_state + fold)
        model.fit(
            physical.values[train],
            labels[train],
            categorical_feature=list(physical.categorical_indices),
        )
        test_raw = model.predict_proba(physical.values[test])
        train_raw = model.predict_proba(physical.values[train])
        test_physical = np.zeros((test.sum(), len(CONTACT_OUTCOMES)), dtype=np.float32)
        train_physical = np.zeros(
            (train.sum(), len(CONTACT_OUTCOMES)), dtype=np.float32
        )
        class_indices = np.asarray(model.classes_, dtype=np.int64)
        test_physical[:, class_indices] = test_raw
        train_physical[:, class_indices] = train_raw
        park = _group_log_probability_adjustment(
            frame,
            train,
            test,
            one_hot[train],
            train_physical,
            ("venue_id", "core_bin", "stand"),
            park_prior,
        )
        defense = _group_log_probability_adjustment(
            frame,
            train,
            test,
            one_hot[train],
            train_physical,
            ("defense_team", "core_bin", "stand"),
            defense_prior,
        )
        pitcher = _group_log_probability_adjustment(
            frame,
            train,
            test,
            one_hot[train],
            train_physical,
            ("pitcher", "core_bin"),
            pitcher_prior,
        )
        probabilities["physical"][test] = test_physical
        corrections = {
            "park": park,
            "park_defense": park + defense,
            "park_defense_pitcher": park + defense + pitcher,
        }
        for stage, correction in corrections.items():
            for weight in weights:
                name = stage if weight == 1.0 else f"{stage}_w{int(weight * 100):03d}"
                probabilities[name][test] = _apply_log_adjustment(
                    test_physical, weight * correction
                )
        fold_rows.append(
            {
                "fold": fold,
                "training_events": int(train.sum()),
                "evaluation_events": int(test.sum()),
                "evaluation_players": int(
                    frame.filter(pl.Series(test))["player_id"].n_unique()
                ),
            }
        )
    for stage, probability in probabilities.items():
        if not np.isfinite(probability).all():
            raise ValueError(f"cross-fit probabilities are incomplete for {stage}")
    report = {
        "season": int(seasons[0]),
        "events": frame.height,
        "players": frame["player_id"].n_unique(),
        "folds": fold_rows,
        "method": "shrunk_residual_context",
        "priors": {
            "park": park_prior,
            "defense": defense_prior,
            "pitcher": pitcher_prior,
        },
        "stage_metrics": {
            stage: multinomial_metrics(labels, probability)
            for stage, probability in probabilities.items()
        },
    }
    return probabilities, report


def aggregate_neutralized_contact_features(
    frame: pl.DataFrame,
    context_probability: np.ndarray,
    *,
    cell_prior: float = 100.0,
    overall_prior: float = 250.0,
    shape_prior: float = 100.0,
) -> pl.DataFrame:
    """Aggregate cross-fitted event residuals to one hitter/source-season row."""

    if any(
        not math.isfinite(value) or value <= 0
        for value in (cell_prior, overall_prior, shape_prior)
    ):
        raise ValueError("aggregation priors must be finite and positive")
    if context_probability.shape != (frame.height, len(CONTACT_OUTCOMES)):
        raise ValueError("probability shape does not match contact events")
    outcome_to_index = {value: index for index, value in enumerate(CONTACT_OUTCOMES)}
    labels = np.array(
        [outcome_to_index[value] for value in frame["canonical_outcome"].to_list()],
        dtype=np.int8,
    )
    one_hot = np.eye(len(CONTACT_OUTCOMES), dtype=np.float32)[labels]
    residual = one_hot - context_probability
    working = frame.select("season", "player_id", "level", "core_bin").with_columns(
        pl.Series(f"_residual__{outcome}", residual[:, index])
        for index, outcome in enumerate(CONTACT_OUTCOMES)
    )
    players = working.select("season", "player_id").unique()
    total = working.group_by("season", "player_id").agg(
        pl.len().alias("neutral_contact_events"),
        pl.col("level").n_unique().alias("neutral_contact_levels"),
        *(
            (pl.col(f"_residual__{outcome}").sum() / (pl.len() + overall_prior)).alias(
                f"neutral_overall__{outcome}"
            )
            for outcome in CONTACT_OUTCOMES
        ),
    )
    cell = working.group_by("season", "player_id", "core_bin").agg(
        pl.len().alias("_bin_n"),
        *(
            (pl.col(f"_residual__{outcome}").sum() / (pl.len() + cell_prior)).alias(
                outcome
            )
            for outcome in CONTACT_OUTCOMES
        ),
    )
    cell_long = cell.unpivot(
        index=["season", "player_id", "core_bin", "_bin_n"],
        on=list(CONTACT_OUTCOMES),
        variable_name="outcome",
        value_name="residual",
    ).with_columns(pl.concat_str("core_bin", "outcome", separator="__").alias("cell"))
    cell_wide = (
        cell_long.select("season", "player_id", "cell", "residual")
        .pivot(on="cell", index=["season", "player_id"], values="residual")
        .rename(
            {
                f"{contact_bin}__{outcome}": (f"neutral_cell__{contact_bin}__{outcome}")
                for contact_bin in CONTACT_BINS
                for outcome in CONTACT_OUTCOMES
                if f"{contact_bin}__{outcome}" in cell_long["cell"].unique().to_list()
            }
        )
    )
    observed_shape = working.group_by("season", "player_id", "core_bin").len(
        name="_bin_n"
    )
    season_shape = working.group_by("season", "core_bin").len(name="_season_bin_n")
    season_total = working.group_by("season").len(name="_season_n")
    shape_prior_frame = season_shape.join(season_total, on="season").with_columns(
        (pl.col("_season_bin_n") / pl.col("_season_n")).alias("_shape_prior")
    )
    shape_grid = (
        players.join(pl.DataFrame({"core_bin": list(CONTACT_BINS)}), how="cross")
        .join(
            observed_shape,
            on=["season", "player_id", "core_bin"],
            how="left",
            validate="1:1",
        )
        .join(
            shape_prior_frame.select("season", "core_bin", "_shape_prior"),
            on=["season", "core_bin"],
            how="left",
            validate="m:1",
        )
        .join(
            total.select("season", "player_id", "neutral_contact_events"),
            on=["season", "player_id"],
            validate="m:1",
        )
        .with_columns(pl.col("_bin_n").fill_null(0))
        .with_columns(
            (
                (pl.col("_bin_n") + shape_prior * pl.col("_shape_prior").fill_null(0.0))
                / (pl.col("neutral_contact_events") + shape_prior)
            ).alias("shape_rate"),
        )
    )
    shape_wide = (
        shape_grid.select("season", "player_id", "core_bin", "shape_rate")
        .pivot(on="core_bin", index=["season", "player_id"], values="shape_rate")
        .rename(
            {
                value: f"neutral_shape__{value}"
                for value in CONTACT_BINS
                if value in shape_grid["core_bin"].unique().to_list()
            }
        )
    )

    expected_cell_columns = [
        f"neutral_cell__{contact_bin}__{outcome}"
        for contact_bin in CONTACT_BINS
        for outcome in CONTACT_OUTCOMES
    ]
    result = total.join(
        cell_wide, on=["season", "player_id"], how="left", validate="1:1"
    ).join(shape_wide, on=["season", "player_id"], how="left", validate="1:1")
    missing_cells = [column for column in expected_cell_columns if column not in result]
    if missing_cells:
        result = result.with_columns(
            pl.lit(0.0).alias(column) for column in missing_cells
        )
    return (
        result.with_columns(
            *(pl.col(column).fill_null(0.0) for column in expected_cell_columns)
        )
        .select(
            "season",
            "player_id",
            "neutral_contact_events",
            "neutral_contact_levels",
            *(f"neutral_shape__{value}" for value in CONTACT_BINS),
            *(f"neutral_overall__{value}" for value in CONTACT_OUTCOMES),
            *expected_cell_columns,
        )
        .sort("season", "player_id")
    )


def attach_neutralized_lags(
    panel: pl.DataFrame,
    annual_features: pl.DataFrame,
    *,
    lags: tuple[int, ...] = (0, 1, 2),
) -> pl.DataFrame:
    """Attach historical player features to the existing next-year value panel."""

    _require(panel, {"origin_year", "player_id"}, "hitter value panel")
    _require(annual_features, {"season", "player_id"}, "annual contact features")
    if panel.filter(pl.col("target_season") >= 2026).height:
        raise ValueError("protected 2026 target rows are not allowed")
    feature_columns = [
        column
        for column in annual_features.columns
        if column not in {"season", "player_id"}
    ]
    result = panel
    for lag in lags:
        renamed = (
            annual_features.rename(
                {
                    column: f"contact_neutral_lag{lag}__{column}"
                    for column in feature_columns
                }
            )
            .with_columns((pl.col("season") + lag).alias("origin_year"))
            .drop("season")
        )
        result = result.join(
            renamed,
            on=["origin_year", "player_id"],
            how="left",
            validate="m:1",
        )
        result = result.with_columns(
            pl.col(f"contact_neutral_lag{lag}__neutral_contact_events")
            .is_not_null()
            .cast(pl.Int8)
            .alias(f"contact_neutral_lag{lag}__available")
        )
    return result.sort("origin_year", "player_id")
