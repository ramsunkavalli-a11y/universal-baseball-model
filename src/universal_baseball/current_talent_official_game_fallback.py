"""Exact-game official fallback for sparse MiLB gameLog omissions.

Historical Current Talent outcome adjudication normally uses the official Stats
API hitting ``gameLog`` for only player x league season residuals.  A gameLog can
rarely omit a real game that is present in the reusable player-game source.

This module does not relax that authority rule generically.  It permits one
narrow fallback only when all of the following hold:

1. a positive-PA source game is absent from the player's official gameLog;
2. the exact official game ``playByPlay`` contains true plate appearances for
   the same batter ID;
3. those official PAs imply the complete PA/AB/BB/HBP/SO/SF/SH/CI vector; and
4. that complete vector exactly matches the resolved source game vector.

Only then is a synthetic gameLog-shaped row added to the official adjudication
surface.  The existing gameLog adjudicator and season-aggregate reconciliation
still run afterward unchanged.  Any missing or disagreeing exact-game evidence
fails closed.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from universal_baseball.current_talent_milb_evidence import OUTCOME_FIELDS
from universal_baseball.event_types import PLATE_APPEARANCE_EVENT_TYPES


WALK_EVENTS = frozenset({"walk", "intent_walk"})
HBP_EVENTS = frozenset({"hit_by_pitch"})
STRIKEOUT_EVENTS = frozenset(
    {"strikeout", "strike_out", "strikeout_double_play", "strikeout_triple_play"}
)
SAC_FLY_EVENTS = frozenset({"sac_fly", "sac_fly_double_play"})
SAC_BUNT_EVENTS = frozenset({"sac_bunt", "sac_bunt_double_play"})
CATCHER_INTERFERENCE_EVENTS = frozenset({"catcher_interf"})


def _positive_source_slice(
    resolved_outcomes: pl.DataFrame,
    *,
    player_id: int,
    league_id: int,
) -> pl.DataFrame:
    required = {"game_id", "player_id", "game_date", "game_type", "league_id", *OUTCOME_FIELDS}
    missing = sorted(required - set(resolved_outcomes.columns))
    if missing:
        raise ValueError(f"resolved outcomes missing exact-game fallback fields: {missing}")
    return resolved_outcomes.filter(
        (pl.col("player_id") == int(player_id))
        & (pl.col("league_id") == int(league_id))
        & (pl.col("game_type") == "R")
        & pl.col("batting_PA").is_not_null()
        & (pl.col("batting_PA") > 0)
    )


def source_only_positive_pa_games(
    resolved_outcomes: pl.DataFrame,
    official_game_log: pl.DataFrame,
    *,
    player_id: int,
    league_id: int,
) -> list[int]:
    """Return positive-PA source games missing from the official gameLog."""

    source = _positive_source_slice(
        resolved_outcomes,
        player_id=player_id,
        league_id=league_id,
    )
    official_required = {"game_id", "player_id", "game_type", "league_id", "batting_PA"}
    missing = sorted(official_required - set(official_game_log.columns))
    if missing:
        raise ValueError(f"official gameLog missing exact-game fallback fields: {missing}")
    official = official_game_log.filter(
        (pl.col("player_id") == int(player_id))
        & (pl.col("league_id") == int(league_id))
        & (pl.col("game_type") == "R")
        & pl.col("batting_PA").is_not_null()
        & (pl.col("batting_PA") > 0)
    )
    source_games = {int(value) for value in source.get_column("game_id").unique().to_list()}
    official_games = {int(value) for value in official.get_column("game_id").unique().to_list()}
    return sorted(source_games - official_games)


def project_official_pa_outcome_vectors(official_pa: pl.DataFrame) -> pl.DataFrame:
    """Aggregate exact-game official true PAs to the Current Talent outcome vector."""

    required = {"game_pk", "batter_id", "event_type"}
    missing = sorted(required - set(official_pa.columns))
    if missing:
        raise ValueError(f"official PA fallback missing fields: {missing}")
    if official_pa.is_empty():
        return pl.DataFrame(
            schema={
                "game_id": pl.Int64,
                "player_id": pl.Int64,
                **{field: pl.Int64 for field in OUTCOME_FIELDS},
            }
        )

    projected = official_pa.select(
        pl.col("game_pk").cast(pl.Int64, strict=False).alias("game_id"),
        pl.col("batter_id").cast(pl.Int64, strict=False).alias("player_id"),
        pl.col("event_type").cast(pl.String),
    )
    if projected.filter(pl.col("game_id").is_null() | pl.col("player_id").is_null()).height:
        raise ValueError("official PA fallback contains invalid game or batter identity")
    unknown = sorted(
        set(projected.get_column("event_type").unique().to_list())
        - set(PLATE_APPEARANCE_EVENT_TYPES)
    )
    if unknown:
        raise ValueError(f"official PA fallback contains non-PA/unknown result types: {unknown}")

    with_flags = projected.with_columns(
        pl.col("event_type").is_in(list(WALK_EVENTS)).cast(pl.Int64).alias("_bb"),
        pl.col("event_type").is_in(list(HBP_EVENTS)).cast(pl.Int64).alias("_hbp"),
        pl.col("event_type").is_in(list(STRIKEOUT_EVENTS)).cast(pl.Int64).alias("_so"),
        pl.col("event_type").is_in(list(SAC_FLY_EVENTS)).cast(pl.Int64).alias("_sf"),
        pl.col("event_type").is_in(list(SAC_BUNT_EVENTS)).cast(pl.Int64).alias("_sh"),
        pl.col("event_type")
        .is_in(list(CATCHER_INTERFERENCE_EVENTS))
        .cast(pl.Int64)
        .alias("_ci"),
    )
    aggregated = with_flags.group_by(["game_id", "player_id"]).agg(
        pl.len().cast(pl.Int64).alias("batting_PA"),
        pl.col("_bb").sum().cast(pl.Int64).alias("batting_BB"),
        pl.col("_hbp").sum().cast(pl.Int64).alias("batting_HBP"),
        pl.col("_so").sum().cast(pl.Int64).alias("batting_SO"),
        pl.col("_sf").sum().cast(pl.Int64).alias("batting_SF"),
        pl.col("_sh").sum().cast(pl.Int64).alias("batting_SH"),
        pl.col("_ci").sum().cast(pl.Int64).alias("batting_CI"),
    ).with_columns(
        (
            pl.col("batting_PA")
            - pl.col("batting_BB")
            - pl.col("batting_HBP")
            - pl.col("batting_SF")
            - pl.col("batting_SH")
            - pl.col("batting_CI")
        )
        .cast(pl.Int64)
        .alias("batting_AB")
    )
    if aggregated.filter(pl.col("batting_AB") < 0).height:
        raise ValueError("official PA fallback produced negative at-bats")
    return aggregated.select("game_id", "player_id", *OUTCOME_FIELDS).sort(
        ["game_id", "player_id"]
    )


def augment_game_log_with_exact_pa_fallback(
    resolved_outcomes: pl.DataFrame,
    official_game_log: pl.DataFrame,
    official_pa: pl.DataFrame,
    *,
    player_id: int,
    league_id: int,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Add only exact-PBP-confirmed gameLog omissions to the official surface."""

    source_only = source_only_positive_pa_games(
        resolved_outcomes,
        official_game_log,
        player_id=player_id,
        league_id=league_id,
    )
    if not source_only:
        return official_game_log, {
            "source_only_game_log_gap_count": 0,
            "exact_game_pbp_confirmed_count": 0,
            "confirmed_game_ids": [],
        }

    source = _positive_source_slice(
        resolved_outcomes,
        player_id=player_id,
        league_id=league_id,
    )
    vectors = project_official_pa_outcome_vectors(official_pa).filter(
        (pl.col("player_id") == int(player_id))
        & pl.col("game_id").is_in(source_only)
    )
    duplicate = vectors.group_by("game_id").len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError("exact-game official PA fallback is not unique by game")
    observed_games = {int(value) for value in vectors.get_column("game_id").to_list()}
    missing_games = sorted(set(source_only) - observed_games)
    if missing_games:
        raise ValueError(
            "gameLog-missing source games lack exact-game official PA evidence: "
            f"player={player_id}, games={missing_games}"
        )

    appended_rows: list[pl.DataFrame] = []
    for game_id in source_only:
        source_row = source.filter(pl.col("game_id") == game_id).row(0, named=True)
        official_row = vectors.filter(pl.col("game_id") == game_id).row(0, named=True)
        mismatches = {
            field: (int(source_row[field] or 0), int(official_row[field] or 0))
            for field in OUTCOME_FIELDS
            if int(source_row[field] or 0) != int(official_row[field] or 0)
        }
        if mismatches:
            raise ValueError(
                "gameLog-missing source game disagrees with exact-game official PA vector: "
                f"player={player_id}, game={game_id}, mismatches={mismatches}"
            )
        values: dict[str, Any] = {
            "game_id": int(game_id),
            "player_id": int(player_id),
            "game_date": source_row["game_date"],
            "game_type": "R",
            "league_id": int(league_id),
            "team_id": None,
            **{field: int(official_row[field] or 0) for field in OUTCOME_FIELDS},
        }
        expressions: list[pl.Expr] = []
        for column, dtype in official_game_log.schema.items():
            value = values.get(column)
            expressions.append(
                pl.lit(value, dtype=dtype).alias(column)
                if value is None
                else pl.lit(value).cast(dtype, strict=False).alias(column)
            )
        appended_rows.append(pl.select(expressions))

    augmented = pl.concat([official_game_log, *appended_rows], how="vertical").sort(
        ["game_id", "player_id", "league_id"]
    )
    return augmented, {
        "source_only_game_log_gap_count": len(source_only),
        "exact_game_pbp_confirmed_count": len(source_only),
        "confirmed_game_ids": source_only,
        "authority": "official_exact_game_play_by_play_true_pa_vector",
        "source_values_changed": False,
    }
