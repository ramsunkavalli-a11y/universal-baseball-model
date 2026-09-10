"""Chronology-stable country features for pitcher development audits."""

from __future__ import annotations

import polars as pl

from universal_baseball.player_demographics import normalize_birth_country


def add_pitcher_country_features(
    features: pl.DataFrame, demographics: pl.DataFrame
) -> pl.DataFrame:
    """Add fixed coarse country indicators without physical measurements."""

    if {"player_id", "age_relative"} - set(features.columns):
        raise ValueError("pitcher features require player_id and age_relative")
    if {"player_id", "birth_country"} - set(demographics.columns):
        raise ValueError("pitcher demographics require player_id and birth_country")
    countries = demographics.select("player_id", "birth_country").with_columns(
        pl.col("birth_country")
        .map_elements(normalize_birth_country, return_dtype=pl.String)
        .alias("country")
    )
    result = features.join(countries, on="player_id", how="left", validate="1:1")
    result = result.with_columns(
        (pl.col("country") == "USA").fill_null(False).cast(pl.Float64).alias(
            "country_usa"
        ),
        (pl.col("country") == "Dominican Republic")
        .fill_null(False)
        .cast(pl.Float64)
        .alias("country_dominican"),
        (pl.col("country") == "Venezuela")
        .fill_null(False)
        .cast(pl.Float64)
        .alias("country_venezuela"),
    )
    return result.with_columns(
        (pl.col("age_relative") * pl.col("country_usa")).alias("age_x_usa"),
        (pl.col("age_relative") * pl.col("country_dominican")).alias(
            "age_x_dominican"
        ),
        (pl.col("age_relative") * pl.col("country_venezuela")).alias(
            "age_x_venezuela"
        ),
    )
