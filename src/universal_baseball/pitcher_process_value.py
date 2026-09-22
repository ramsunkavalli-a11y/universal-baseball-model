"""High-minors pitch-process features for whole-value pitcher tests."""

from __future__ import annotations

import polars as pl


PROCESS_COLUMNS = (
    "process_whiff",
    "process_strike",
    "process_swing",
    "process_ppbf",
)


def build_pitcher_process_features(process: pl.DataFrame) -> pl.DataFrame:
    """Shrink level-relative pitch-call rates and aggregate to player-season."""

    required = {
        "season",
        "player_id",
        "level_group",
        "bf",
        "pitches",
        "swings",
        "whiffs",
        "strikes",
        "balls",
    }
    if missing := sorted(required - set(process.columns)):
        raise ValueError(f"pitch-process source missing fields: {missing}")
    rows = process.group_by("season", "player_id", "level_group").agg(
        pl.col("bf", "pitches", "swings", "whiffs", "strikes", "balls").sum()
    )
    if rows.filter(
        (pl.col("bf") < 0)
        | (pl.col("whiffs") > pl.col("swings"))
        | (pl.col("swings") > pl.col("pitches"))
        | (pl.col("strikes") + pl.col("balls") != pl.col("pitches"))
    ).height:
        raise ValueError("invalid pitch-process accounting")
    eligible = rows.filter(
        (pl.col("bf") >= 30) & (pl.col("pitches") > 0) & (pl.col("swings") > 0)
    ).with_columns(
        (
            pl.col("whiffs").sum().over(["season", "level_group"])
            / pl.col("swings").sum().over(["season", "level_group"])
        ).alias("prior_whiff"),
        (
            pl.col("strikes").sum().over(["season", "level_group"])
            / pl.col("pitches").sum().over(["season", "level_group"])
        ).alias("prior_strike"),
        (
            pl.col("swings").sum().over(["season", "level_group"])
            / pl.col("pitches").sum().over(["season", "level_group"])
        ).alias("prior_swing"),
        (
            pl.col("pitches").sum().over(["season", "level_group"])
            / pl.col("bf").sum().over(["season", "level_group"])
        ).alias("prior_ppbf"),
    )
    level = eligible.with_columns(
        (
            (pl.col("whiffs") + 200 * pl.col("prior_whiff"))
            / (pl.col("swings") + 200)
            - pl.col("prior_whiff")
        ).alias("process_whiff"),
        (
            (pl.col("strikes") + 500 * pl.col("prior_strike"))
            / (pl.col("pitches") + 500)
            - pl.col("prior_strike")
        ).alias("process_strike"),
        (
            (pl.col("swings") + 500 * pl.col("prior_swing"))
            / (pl.col("pitches") + 500)
            - pl.col("prior_swing")
        ).alias("process_swing"),
        (
            (pl.col("pitches") + 100 * pl.col("prior_ppbf"))
            / (pl.col("bf") + 100)
            - pl.col("prior_ppbf")
        ).alias("process_ppbf"),
    )
    return (
        level.group_by("season", "player_id")
        .agg(
            pl.col("bf").sum().alias("process_bf"),
            *(
                (
                    (pl.col(column) * pl.col("bf")).sum()
                    / pl.col("bf").sum()
                ).alias(column)
                for column in PROCESS_COLUMNS
            ),
            pl.col("level_group").n_unique().alias("process_level_count"),
        )
        .with_columns(pl.lit(1).cast(pl.Int8).alias("process_available"))
        .sort("season", "player_id")
    )


def add_neutral_process_features(
    stat_features: pl.DataFrame, process_features: pl.DataFrame
) -> pl.DataFrame:
    """Join optional process evidence; unavailable evidence is exactly neutral."""

    joined = stat_features.join(
        process_features, on=["season", "player_id"], how="left", validate="1:1"
    )
    return joined.with_columns(
        *(pl.col(column).fill_null(0.0) for column in PROCESS_COLUMNS),
        pl.col("process_bf").fill_null(0.0),
        pl.col("process_level_count").fill_null(0),
        pl.col("process_available").fill_null(0),
    )
