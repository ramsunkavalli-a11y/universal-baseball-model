"""Frozen age-for-level and throwing-hand adjustment for affiliated pitchers."""

from __future__ import annotations

import numpy as np
import polars as pl

from universal_baseball.level_component_translation import LEVEL_ORDER


PITCHER_DEMOGRAPHIC_ADJUSTMENT_ID = (
    "pitcher_affiliated_age_level_hand_2024fit_2025point_confirmed_v1"
)
COMPONENTS = ("so", "ubb", "hbp", "hr", "other")
FEATURES = ("age_relative", "left_handed", "age_x_left")
# The fifth component, other, is the reference and therefore has coefficient zero.
COEFFICIENTS = np.asarray(
    [
        [-0.03220875623896729, 0.021574974873708533,
         0.010055053563950643, 0.020388956344013564],
        [-0.02129610538959265, -0.06946851219070378,
         -0.042360373464979076, -0.08793925106520148],
        [0.014463434204266302, -0.016779553802126486,
         0.042296373525489386, -0.007306224430271762],
    ],
    dtype=float,
)


def build_pitcher_age_level_features(
    history: pl.DataFrame,
    demographics: pl.DataFrame,
    players: pl.DataFrame,
    *,
    current_season: int,
) -> pl.DataFrame:
    """Build historical reported-age and stable-hand features at the current cutoff."""

    required_history = {
        "season", "player_id", "level_group", "reported_age", "batters_faced",
    }
    if missing := sorted(required_history - set(history.columns)):
        raise ValueError(f"pitcher age-level history missing columns: {missing}")
    if set(players.columns) != {"player_id"}:
        raise ValueError("pitcher demographic feature players require only player_id")
    if {"player_id", "pitch_hand"} - set(demographics.columns):
        raise ValueError("pitcher demographics require player_id and pitch_hand")
    eligible = history.filter(
        (pl.col("season") <= current_season) & (pl.col("level_group") != "MLB")
    )
    latest = eligible.group_by("player_id").agg(
        pl.col("season").max().alias("season")
    )
    current = (
        eligible.join(latest, on=["player_id", "season"], how="inner")
        .group_by("player_id", "season", "level_group", "reported_age")
        .agg(pl.col("batters_faced").sum())
        .with_columns(
            pl.col("level_group").replace_strict(LEVEL_ORDER).alias("level_order")
        )
        .sort(
            ["player_id", "batters_faced", "level_order"],
            descending=[False, True, True],
        )
        .unique("player_id", keep="first")
    )
    reference = (
        eligible.group_by("season", "player_id", "level_group", "reported_age")
        .agg(pl.col("batters_faced").sum())
        .filter(pl.col("batters_faced") >= 30)
        .group_by("season", "level_group")
        .agg(pl.col("reported_age").median().alias("level_median_age"))
    )
    return (
        players.join(current, on="player_id", how="left", validate="1:1")
        .join(reference, on=["season", "level_group"], how="left", validate="m:1")
        .join(
            demographics.select("player_id", "pitch_hand"),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .with_columns(
            (
                pl.col("reported_age").is_not_null()
                & pl.col("level_median_age").is_not_null()
            ).alias("age_level_feature_available"),
            ((pl.col("reported_age") - pl.col("level_median_age")) / 3.0)
            .fill_null(0.0)
            .clip(-2.0, 2.0)
            .alias("age_relative"),
            (pl.col("pitch_hand") == "L")
            .fill_null(False)
            .cast(pl.Float64)
            .alias("left_handed"),
        )
        .with_columns(
            (pl.col("age_relative") * pl.col("left_handed")).alias("age_x_left")
        )
        .select(
            "player_id", "age_relative", "left_handed", "age_x_left",
            "age_level_feature_available", "level_group",
        )
        .sort("player_id")
    )


def apply_pitcher_demographic_adjustment(
    profiles: pl.DataFrame, features: pl.DataFrame
) -> pl.DataFrame:
    """Adjust coherent component profiles; missing age evidence stays unchanged."""

    required_profiles = {
        "player_id", "weighted_affiliated_exposure",
        *(f"p_{component}" for component in COMPONENTS),
    }
    if missing := sorted(required_profiles - set(profiles.columns)):
        raise ValueError(f"pitcher affiliated profiles missing columns: {missing}")
    required_features = {"player_id", *FEATURES, "age_level_feature_available"}
    if missing := sorted(required_features - set(features.columns)):
        raise ValueError(f"pitcher demographic features missing columns: {missing}")
    source = profiles.join(
        features.select(*sorted(required_features)),
        on="player_id",
        how="left",
        validate="1:1",
    )
    rows = []
    for row in source.sort("player_id").iter_rows(named=True):
        applicable = bool(row.get("age_level_feature_available")) and float(
            row.get("weighted_affiliated_exposure") or 0.0
        ) > 0
        probabilities = np.asarray(
            [float(row[f"p_{component}"]) for component in COMPONENTS]
        )
        if applicable:
            x = np.asarray([float(row.get(feature) or 0.0) for feature in FEATURES])
            adjustment = np.append(x @ COEFFICIENTS, 0.0)
            logits = np.log(probabilities) + adjustment
            probabilities = np.exp(logits - logits.max())
            probabilities /= probabilities.sum()
        rows.append(
            {
                **{column: row[column] for column in profiles.columns},
                **{
                    f"p_{component}": float(probabilities[index])
                    for index, component in enumerate(COMPONENTS)
                },
                "pitcher_demographic_adjustment_applied": applicable,
                "pitcher_demographic_adjustment_id": (
                    PITCHER_DEMOGRAPHIC_ADJUSTMENT_ID if applicable else None
                ),
            }
        )
    result = pl.DataFrame(rows, infer_schema_length=None).sort("player_id")
    probability_sum = pl.sum_horizontal(
        *(pl.col(f"p_{component}") for component in COMPONENTS)
    )
    if result.filter((probability_sum - 1.0).abs() > 1e-9).height:
        raise ValueError("adjusted pitcher component profiles do not sum to one")
    return result
