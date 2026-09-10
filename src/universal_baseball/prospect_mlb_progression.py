"""Cutoff-safe post-arrival MLB career-state progression helpers."""

from __future__ import annotations

from dataclasses import dataclass
from math import log1p
from typing import Sequence

import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression

from universal_baseball.prospect_career_state import CAREER_STATE_ORDER


ORIGINS = ("FRINGE_MLB", "MEANINGFUL_MLB")


@dataclass(frozen=True, slots=True)
class ProgressionFit:
    origin_state: str
    feature_set: str
    regularization_c: float
    model: LogisticRegression


def build_post_arrival_progression_rows(
    transition_frames: Sequence[pl.DataFrame],
    mlb_workload: pl.DataFrame,
) -> pl.DataFrame:
    """Deduplicate transition years and attach only prior-season MLB workload."""

    required = {
        "player_id",
        "snapshot_year",
        "elapsed_year",
        "outcome_year",
        "from_state",
        "to_state",
        "age_years",
    }
    if not transition_frames:
        raise ValueError("post-arrival progression requires transition frames")
    for frame in transition_frames:
        if missing := sorted(required - set(frame.columns)):
            raise ValueError(f"transition rows missing fields: {missing}")
    if missing := sorted({"season", "player_id", "mlb_workload"} - set(mlb_workload.columns)):
        raise ValueError(f"MLB workload rows missing fields: {missing}")
    role_columns = {"pitching_games", "pitching_starts"}
    has_pitcher_role = role_columns <= set(mlb_workload.columns)
    if bool(role_columns & set(mlb_workload.columns)) and not has_pitcher_role:
        raise ValueError("pitcher role requires both games and starts")
    aggregations = [pl.col("mlb_workload").sum()]
    if has_pitcher_role:
        aggregations.extend(
            [pl.col("pitching_games").sum(), pl.col("pitching_starts").sum()]
        )
    workload = mlb_workload.group_by("season", "player_id").agg(aggregations)
    if workload.filter(pl.col("mlb_workload") < 0).height:
        raise ValueError("MLB workload cannot be negative")
    if has_pitcher_role and workload.filter(
        (pl.col("pitching_games") < 0)
        | (pl.col("pitching_starts") < 0)
        | (pl.col("pitching_starts") > pl.col("pitching_games"))
        | ((pl.col("mlb_workload") > 0) & (pl.col("pitching_games") == 0))
    ).height:
        raise ValueError("invalid pitcher role workload")
    environment = workload.filter(pl.col("mlb_workload") > 0).group_by("season").agg(
        pl.col("mlb_workload").mean().alias("active_mean_workload")
    )
    rows = (
        pl.concat(list(transition_frames), how="vertical_relaxed")
        .sort(
            ["player_id", "outcome_year", "snapshot_year"],
            descending=[False, False, True],
        )
        .unique(["player_id", "outcome_year"], keep="first", maintain_order=True)
        .filter(
            pl.col("from_state").is_in(ORIGINS) & (pl.col("outcome_year") != 2020)
        )
        .with_columns((pl.col("outcome_year") - 1).alias("prior_season"))
        .join(
            workload.rename({"season": "prior_season"}),
            on=["player_id", "prior_season"],
            how="left",
            validate="m:1",
        )
        .join(
            environment.rename({"season": "prior_season"}),
            on="prior_season",
            how="left",
            validate="m:1",
        )
        .with_columns(pl.col("mlb_workload").fill_null(0.0))
        .with_columns(
            (pl.col("mlb_workload") > 0).cast(pl.Int64).alias("prior_mlb_active"),
            (pl.col("mlb_workload") / pl.col("active_mean_workload")).alias(
                "prior_workload_vs_active_mean"
            ),
            (
                pl.col("to_state").replace_strict(CAREER_STATE_ORDER)
                > pl.col("from_state").replace_strict(CAREER_STATE_ORDER)
            )
            .cast(pl.Int64)
            .alias("advanced"),
            (pl.col("age_years") + pl.col("elapsed_year") - 1).alias(
                "transition_age_years"
            ),
        )
    )
    if has_pitcher_role:
        rows = rows.with_columns(
            pl.col("pitching_games").fill_null(0),
            pl.col("pitching_starts").fill_null(0),
        ).with_columns(
            pl.when(pl.col("pitching_games") > 0)
            .then(pl.col("pitching_starts") / pl.col("pitching_games"))
            .otherwise(0.0)
            .alias("prior_start_share"),
            pl.when(pl.col("pitching_games") > 0)
            .then(pl.col("mlb_workload") / pl.col("pitching_games"))
            .otherwise(0.0)
            .alias("prior_bf_per_game"),
        )
    if rows.filter(
        pl.col("active_mean_workload").is_null()
        | pl.col("prior_workload_vs_active_mean").is_nan()
        | pl.col("prior_workload_vs_active_mean").is_infinite()
    ).height:
        raise ValueError("post-arrival progression lacks a prior-season MLB environment")
    return rows.sort("outcome_year", "from_state", "player_id")


def progression_design(frame: pl.DataFrame, *, feature_set: str) -> np.ndarray:
    """Create the frozen age/time or age/time/workload progression design."""

    if feature_set not in {
        "age_elapsed",
        "age_elapsed_prior_workload",
        "age_elapsed_prior_workload_role",
    }:
        raise ValueError("unsupported progression feature set")
    elapsed = frame.get_column("elapsed_year").to_numpy().astype(float)
    values = [
        (frame.get_column("transition_age_years").to_numpy() - 25.0) / 5.0,
        (elapsed - 1.0) / 3.0,
        (elapsed >= 3).astype(float),
    ]
    if feature_set in {
        "age_elapsed_prior_workload",
        "age_elapsed_prior_workload_role",
    }:
        relative = frame.get_column("prior_workload_vs_active_mean").to_numpy()
        values.extend(
            [
                frame.get_column("prior_mlb_active").to_numpy().astype(float),
                np.asarray([log1p(float(value)) for value in relative]),
            ]
        )
    if feature_set == "age_elapsed_prior_workload_role":
        values.extend(
            [
                frame.get_column("prior_start_share").to_numpy().astype(float),
                frame.get_column("prior_bf_per_game").to_numpy().astype(float) / 25.0,
            ]
        )
    return np.column_stack(values)


def fit_progression(
    frame: pl.DataFrame,
    *,
    origin_state: str,
    feature_set: str,
    regularization_c: float,
) -> ProgressionFit:
    """Fit one binary advancement hazard for a nonterminal MLB state."""

    if origin_state not in ORIGINS or regularization_c <= 0:
        raise ValueError("invalid progression origin or regularization")
    cell = frame.filter(pl.col("from_state") == origin_state)
    if cell.is_empty() or cell.get_column("advanced").n_unique() != 2:
        raise ValueError(f"progression fit lacks both outcomes for {origin_state}")
    model = LogisticRegression(C=regularization_c, max_iter=2000).fit(
        progression_design(cell, feature_set=feature_set),
        cell.get_column("advanced").to_numpy(),
    )
    return ProgressionFit(origin_state, feature_set, regularization_c, model)


def score_progression(fit: ProgressionFit, frame: pl.DataFrame) -> pl.DataFrame:
    """Return player-level log-loss and Brier losses for one origin state."""

    cell = frame.filter(pl.col("from_state") == fit.origin_state)
    truth = cell.get_column("advanced").to_numpy().astype(float)
    probability = fit.model.predict_proba(
        progression_design(cell, feature_set=fit.feature_set)
    )[:, 1]
    chosen = np.where(truth == 1, probability, 1 - probability)
    return cell.select("player_id", "outcome_year", "advanced").with_columns(
        pl.Series("predicted_advance_probability", probability),
        pl.Series("log_loss", -np.log(np.clip(chosen, 1e-12, 1))),
        pl.Series("brier", (probability - truth) ** 2),
    )
