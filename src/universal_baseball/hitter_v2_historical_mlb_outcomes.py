"""Historical MLB terminal outcomes for the gap-aware Hitter v2 core."""

from __future__ import annotations

import polars as pl

from universal_baseball.current_talent_mlb_evidence import (
    _with_official_outcome_batter,
)
from universal_baseball.hitter_v2_outcomes import (
    HITTER_TALENT_OUTCOMES,
    MLB_EVENT_OUTCOME,
    TERMINAL_OUTCOMES,
)


def summarize_historical_mlb_terminal_outcomes(savant: pl.DataFrame) -> pl.DataFrame:
    """Project certified Savant terminal rows to player-league-season outcomes."""

    required = {
        "game_year",
        "game_pk",
        "at_bat_index",
        "pitch_number",
        "league_id",
        "batter_mlbam_id",
        "events",
        "is_plate_appearance_terminal",
        "pitch_result_code",
        "result_description",
    }
    missing = sorted(required - set(savant.columns))
    if missing:
        raise ValueError(f"historical MLB outcomes missing fields: {missing}")
    attributed = _with_official_outcome_batter(savant)
    terminal = attributed.filter(pl.col("is_plate_appearance_terminal"))
    unknown = sorted(
        set(terminal.get_column("events").drop_nulls().unique().to_list())
        - set(MLB_EVENT_OUTCOME)
    )
    if unknown:
        raise ValueError(f"unsupported historical MLB terminal events: {unknown}")
    interference_error = (
        (pl.col("events") == "field_error")
        & pl.col("result_description")
        .cast(pl.String)
        .str.to_lowercase()
        .str.contains(r"\binterference error\b")
        .fill_null(False)
    )
    labeled = terminal.with_columns(
        pl.when(interference_error)
        .then(pl.lit("SH_OR_SPECIAL"))
        .otherwise(pl.col("events").replace_strict(MLB_EVENT_OUTCOME))
        .alias("terminal_outcome")
    )
    counts = (
        labeled.group_by(
            pl.col("game_year").cast(pl.Int32).alias("season"),
            pl.col("league_id").cast(pl.Int64),
            pl.col("_outcome_player_id").cast(pl.Int64).alias("player_id"),
            "terminal_outcome",
        )
        .len(name="count")
        .pivot(
            on="terminal_outcome",
            index=["season", "league_id", "player_id"],
            values="count",
            aggregate_function="sum",
        )
    )
    for outcome in TERMINAL_OUTCOMES:
        if outcome not in counts.columns:
            counts = counts.with_columns(pl.lit(0, dtype=pl.Int64).alias(outcome))
    return (
        counts.with_columns(
            *[pl.col(outcome).fill_null(0).cast(pl.Int64) for outcome in TERMINAL_OUTCOMES]
        )
        .with_columns(
            pl.sum_horizontal(*HITTER_TALENT_OUTCOMES).alias("hitter_talent_pa"),
            pl.sum_horizontal(*TERMINAL_OUTCOMES).alias("terminal_pa"),
            pl.lit("MLB").alias("level_group"),
            pl.lit("mlb_savant_terminal_outcomes_v1").alias("source_capability_tier"),
            pl.lit("accepted_exact_certified_source").alias("source_status"),
            pl.lit(True).alias("modeling_eligible"),
        )
        .select(
            "season",
            "league_id",
            "player_id",
            "level_group",
            "source_capability_tier",
            *TERMINAL_OUTCOMES,
            "terminal_pa",
            "hitter_talent_pa",
            "modeling_eligible",
            "source_status",
        )
        .sort("season", "league_id", "player_id")
    )
