"""Target-free matchup context for Hitter v2 terminal plate appearances."""

from __future__ import annotations

import polars as pl


MATCHUP_KEY = ("game_pk", "at_bat_index")


def _required(frame: pl.DataFrame, fields: set[str], label: str) -> None:
    missing = sorted(fields - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing fields: {missing}")


def build_terminal_matchup_sidecar(
    pitches: pl.DataFrame,
    terminal_authority: pl.DataFrame,
    *,
    season: int,
    level_group: str,
    source_system: str,
    capability_tier: str,
) -> pl.DataFrame:
    """Join terminal authority to its exact source pitch and preserve conflicts."""

    _required(
        pitches,
        {
            "game_pk",
            "at_bat_index",
            "pitch_number",
            "game_date",
            "source_batter_id",
            "pitcher_id",
            "batter_side",
            "pitcher_hand",
        },
        "matchup pitch source",
    )
    _required(
        terminal_authority,
        {
            "game_pk",
            "at_bat_index",
            "terminal_pitch_number",
            "player_id",
            "league_id",
            "participant_authority",
        },
        "terminal authority",
    )
    duplicate_authority = (
        terminal_authority.group_by(MATCHUP_KEY).len().filter(pl.col("len") != 1)
    )
    if not duplicate_authority.is_empty():
        raise ValueError("terminal authority is not unique at game/PA grain")

    source = pitches.select(
        pl.col("game_pk").cast(pl.Int64),
        pl.col("at_bat_index").cast(pl.Int64),
        pl.col("pitch_number").cast(pl.Int64),
        pl.col("game_date").cast(pl.Date, strict=False),
        pl.col("source_batter_id").cast(pl.Int64, strict=False),
        pl.col("pitcher_id").cast(pl.Int64, strict=False),
        pl.col("batter_side").cast(pl.String).str.to_uppercase(),
        pl.col("pitcher_hand").cast(pl.String).str.to_uppercase(),
    )
    terminal_rows = terminal_authority.select(
        "game_pk",
        "at_bat_index",
        "terminal_pitch_number",
    ).join(
        source,
        left_on=["game_pk", "at_bat_index", "terminal_pitch_number"],
        right_on=["game_pk", "at_bat_index", "pitch_number"],
        how="left",
        validate="1:m",
    )
    aggregated = terminal_rows.group_by(MATCHUP_KEY).agg(
        pl.col("game_date").drop_nulls().n_unique().alias("game_date_count"),
        pl.col("game_date").drop_nulls().first().alias("game_date"),
        pl.col("source_batter_id").drop_nulls().n_unique().alias("source_batter_count"),
        pl.col("source_batter_id").drop_nulls().first().alias("source_batter_id"),
        pl.col("pitcher_id").drop_nulls().n_unique().alias("pitcher_count"),
        pl.col("pitcher_id").drop_nulls().first().alias("pitcher_id"),
        pl.col("batter_side").drop_nulls().n_unique().alias("batter_side_count"),
        pl.col("batter_side").drop_nulls().first().alias("batter_side"),
        pl.col("pitcher_hand").drop_nulls().n_unique().alias("pitcher_hand_count"),
        pl.col("pitcher_hand").drop_nulls().first().alias("pitcher_hand"),
        pl.len().alias("raw_terminal_row_count"),
    )
    result = terminal_authority.join(
        aggregated, on=list(MATCHUP_KEY), how="left", validate="1:1"
    ).with_columns(
        pl.lit(int(season)).cast(pl.Int64).alias("season"),
        pl.lit(str(level_group)).alias("level_group"),
        pl.lit(str(source_system)).alias("source_system"),
        pl.lit(str(capability_tier)).alias("capability_tier"),
    )
    source_conflict = (
        (pl.col("game_date_count") != 1)
        | (pl.col("source_batter_count") != 1)
        | (pl.col("pitcher_count") != 1)
        | (pl.col("batter_side_count") != 1)
        | (pl.col("pitcher_hand_count") != 1)
    )
    valid_hands = pl.col("batter_side").is_in(["L", "R"]) & pl.col(
        "pitcher_hand"
    ).is_in(["L", "R"])
    identity_ready = (
        pl.col("player_id").is_not_null()
        & (pl.col("player_id") > 0)
        & pl.col("pitcher_id").is_not_null()
        & (pl.col("pitcher_id") > 0)
    )
    return (
        result.with_columns(
            source_conflict.alias("source_matchup_conflict"),
            (identity_ready & valid_hands & ~source_conflict).alias("matchup_ready"),
            pl.when(source_conflict)
            .then(pl.lit("conflicting_terminal_source_rows"))
            .when(pl.col("player_id").is_null() | (pl.col("player_id") <= 0))
            .then(pl.lit("unresolved_outcome_batter"))
            .when(pl.col("pitcher_id").is_null() | (pl.col("pitcher_id") <= 0))
            .then(pl.lit("unresolved_terminal_pitcher"))
            .when(~valid_hands)
            .then(pl.lit("missing_or_invalid_observed_handedness"))
            .otherwise(pl.lit("none"))
            .alias("matchup_fallback_reason"),
        )
        .select(
            "season",
            "game_date",
            "game_pk",
            "at_bat_index",
            "terminal_pitch_number",
            "league_id",
            "level_group",
            "player_id",
            "source_batter_id",
            "pitcher_id",
            "batter_side",
            "pitcher_hand",
            "participant_authority",
            "source_system",
            "capability_tier",
            "raw_terminal_row_count",
            "game_date_count",
            "source_batter_count",
            "pitcher_count",
            "batter_side_count",
            "pitcher_hand_count",
            "source_matchup_conflict",
            "matchup_ready",
            "matchup_fallback_reason",
        )
        .sort(["season", "game_date", "game_pk", "at_bat_index"])
    )


def add_strict_prior_pitcher_evidence(
    sidecar: pl.DataFrame,
    *,
    evidence_ready_column: str = "matchup_ready",
    output_column: str = "prior_pitcher_pa",
    date_count_column: str = "pitcher_pa_on_date",
) -> pl.DataFrame:
    """Attach pitcher PA counts from dates strictly before each matchup date."""

    _required(
        sidecar,
        {"game_date", "pitcher_id", evidence_ready_column, *MATCHUP_KEY},
        "matchup sidecar",
    )
    duplicate = sidecar.group_by(MATCHUP_KEY).len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError("matchup sidecar is not unique at game/PA grain")
    ready = sidecar.filter(
        pl.col(evidence_ready_column)
        & pl.col("pitcher_id").is_not_null()
        & pl.col("game_date").is_not_null()
    )
    pitcher_dates = ready.group_by(["pitcher_id", "game_date"]).agg(
        pl.len().cast(pl.Int64).alias(date_count_column)
    ).sort(["pitcher_id", "game_date"])
    pitcher_dates = pitcher_dates.with_columns(
        (
            pl.col(date_count_column).cum_sum().over("pitcher_id")
            - pl.col(date_count_column)
        )
        .cast(pl.Int64)
        .alias(output_column)
    )
    return (
        sidecar.join(
            pitcher_dates,
            on=["pitcher_id", "game_date"],
            how="left",
            validate="m:1",
        )
        .with_columns(
            pl.col(output_column).fill_null(0).cast(pl.Int64),
            pl.col(date_count_column).fill_null(0).cast(pl.Int64),
            pl.lit("strictly_before_game_date_same_day_excluded").alias(
                "prior_pitcher_chronology_policy"
            ),
        )
        .sort(["season", "game_date", "game_pk", "at_bat_index"])
    )


def reconcile_sidecar_to_player_games(
    sidecar: pl.DataFrame,
    player_games: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Fail closed unless PA-sidecar counts exactly match an accepted player-game."""

    game_key = ["season", "league_id", "game_id", "player_id"]
    _required(
        player_games,
        {*game_key, "accepted_terminal_pa", "source_status", "modeling_eligible"},
        "Hitter v2 player-game outcomes",
    )
    source_games = sidecar.group_by(
        ["season", "league_id", "game_pk", "player_id"]
    ).agg(
        pl.len().alias("sidecar_terminal_pa"),
        pl.col("matchup_ready").sum().alias("matchup_ready_pa"),
    ).rename({"game_pk": "game_id"})
    authority = player_games.select(
        *game_key,
        pl.col("accepted_terminal_pa").cast(pl.Int64),
        pl.col("source_status").alias("player_game_source_status"),
        pl.col("modeling_eligible").alias("player_game_modeling_eligible"),
    )
    reconciliation = authority.join(
        source_games, on=game_key, how="full", coalesce=True, validate="1:1"
    ).with_columns(
        pl.col("sidecar_terminal_pa").fill_null(0).cast(pl.Int64),
        pl.col("matchup_ready_pa").fill_null(0).cast(pl.Int64),
    )
    exact = pl.col("sidecar_terminal_pa") == pl.col("accepted_terminal_pa")
    accepted = pl.col("player_game_modeling_eligible").fill_null(False)
    reconciliation = reconciliation.with_columns(
        (exact & accepted).alias("sidecar_player_game_ready"),
        pl.when(pl.col("accepted_terminal_pa").is_null())
        .then(pl.lit("sidecar_without_player_game_authority"))
        .when(pl.col("sidecar_terminal_pa") == 0)
        .then(pl.lit("player_game_without_sidecar_pa"))
        .when(~exact)
        .then(pl.lit("terminal_pa_count_mismatch"))
        .when(~accepted)
        .then(pl.lit("player_game_failed_closed"))
        .otherwise(pl.lit("exact_accepted_player_game"))
        .alias("sidecar_reconciliation_status"),
    ).sort(game_key)
    attached = sidecar.join(
        reconciliation.select(
            *game_key,
            "player_game_source_status",
            "player_game_modeling_eligible",
            "sidecar_player_game_ready",
            "sidecar_reconciliation_status",
        ),
        left_on=["season", "league_id", "game_pk", "player_id"],
        right_on=game_key,
        how="left",
        validate="m:1",
    ).with_columns(
        (
            pl.col("matchup_ready")
            & pl.col("sidecar_player_game_ready").fill_null(False)
        ).alias("modeling_join_ready")
    )
    return attached.sort(["season", "game_date", "game_pk", "at_bat_index"]), reconciliation
