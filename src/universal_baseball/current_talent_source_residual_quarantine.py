"""Fail-closed quarantine for exact source-only player-game residuals.

A reusable player-game row may be quarantined only when it is the *single*
positive-PA source game absent from the official player gameLog for that
player/league and two independent accounting checks both prove the row is the
entire residual:

1. its PA/BB/HBP/SO vector exactly equals the already-observed difference between
   resolved player-game totals and the independent season-player aggregate; and
2. removing its complete PA/AB/BB/HBP/SO/SF/SH/CI vector makes the remaining
   player-game totals exactly equal the official gameLog aggregate.

Anything less remains unresolved.  This helper does not guess identity, league,
or outcome values and does not modify model logic.
"""

from __future__ import annotations

from typing import Any, Mapping

import polars as pl

from universal_baseball.current_talent_milb_evidence import OUTCOME_FIELDS
from universal_baseball.current_talent_official_game_fallback import (
    source_only_positive_pa_games,
)

SEASON_RESIDUAL_FIELD = {
    "batting_PA": "plate_appearances_difference",
    "batting_BB": "walks_difference",
    "batting_HBP": "hit_by_pitch_difference",
    "batting_SO": "strikeouts_difference",
}


def _target_positive(
    frame: pl.DataFrame,
    *,
    player_id: int,
    league_id: int,
) -> pl.DataFrame:
    required = {"game_id", "player_id", "game_type", "league_id", "batting_PA", *OUTCOME_FIELDS}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"source-residual quarantine missing fields: {missing}")
    return frame.filter(
        (pl.col("player_id") == int(player_id))
        & (pl.col("league_id") == int(league_id))
        & (pl.col("game_type") == "R")
        & pl.col("batting_PA").is_not_null()
        & (pl.col("batting_PA") > 0)
    )


def _sum_vector(frame: pl.DataFrame) -> dict[str, int]:
    if frame.is_empty():
        return {field: 0 for field in OUTCOME_FIELDS}
    row = frame.select(
        *[pl.col(field).fill_null(0).sum().cast(pl.Int64).alias(field) for field in OUTCOME_FIELDS]
    ).row(0, named=True)
    return {field: int(row[field] or 0) for field in OUTCOME_FIELDS}


def quarantine_single_source_only_exact_residual(
    resolved_outcomes: pl.DataFrame,
    official_game_log: pl.DataFrame,
    season_comparison_row: Mapping[str, Any],
    *,
    player_id: int,
    league_id: int,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Remove one source-only game only when both independent ledgers prove it."""

    source_only = source_only_positive_pa_games(
        resolved_outcomes,
        official_game_log,
        player_id=player_id,
        league_id=league_id,
    )
    base_metrics: dict[str, Any] = {
        "policy": "single_source_only_exact_season_and_official_residual_v1",
        "player_id": int(player_id),
        "league_id": int(league_id),
        "source_only_positive_pa_game_ids": source_only,
        "applied": False,
        "quarantined_game_ids": [],
    }
    if len(source_only) != 1:
        return resolved_outcomes, {
            **base_metrics,
            "reason": "requires_exactly_one_source_only_positive_pa_game",
        }

    game_id = int(source_only[0])
    source = _target_positive(
        resolved_outcomes,
        player_id=player_id,
        league_id=league_id,
    )
    suspect = source.filter(pl.col("game_id") == game_id)
    if suspect.height != 1:
        raise ValueError(
            "single source-only residual candidate is not unique in resolved outcomes: "
            f"player={player_id}, game={game_id}, rows={suspect.height}"
        )
    row = suspect.row(0, named=True)
    if any(row[field] is None for field in OUTCOME_FIELDS):
        raise ValueError("source-only residual candidate has incomplete outcome vector")
    source_vector = {field: int(row[field] or 0) for field in OUTCOME_FIELDS}

    missing_residual = sorted(
        field for field in SEASON_RESIDUAL_FIELD.values() if field not in season_comparison_row
    )
    if missing_residual:
        raise ValueError(f"season comparison row missing residual fields: {missing_residual}")
    season_residual = {
        source_field: int(season_comparison_row[diff_field] or 0)
        for source_field, diff_field in SEASON_RESIDUAL_FIELD.items()
    }
    season_exact = all(
        source_vector[source_field] == season_residual[source_field]
        for source_field in SEASON_RESIDUAL_FIELD
    )

    official_required = {"player_id", "game_type", "league_id", "batting_PA", *OUTCOME_FIELDS}
    missing_official = sorted(official_required - set(official_game_log.columns))
    if missing_official:
        raise ValueError(f"official gameLog missing source-residual fields: {missing_official}")
    official = official_game_log.filter(
        (pl.col("player_id") == int(player_id))
        & (pl.col("league_id") == int(league_id))
        & (pl.col("game_type") == "R")
        & pl.col("batting_PA").is_not_null()
        & (pl.col("batting_PA") > 0)
    )
    source_totals = _sum_vector(source)
    after_totals = {
        field: int(source_totals[field] - source_vector[field]) for field in OUTCOME_FIELDS
    }
    official_totals = _sum_vector(official)
    official_exact = after_totals == official_totals

    metrics = {
        **base_metrics,
        "candidate_game_id": game_id,
        "candidate_source_vector": source_vector,
        "season_residual_vector": season_residual,
        "season_residual_exact": bool(season_exact),
        "source_totals_before": source_totals,
        "source_totals_after_candidate_removal": after_totals,
        "official_game_log_totals": official_totals,
        "official_full_vector_exact_after_removal": bool(official_exact),
    }
    if not (season_exact and official_exact):
        return resolved_outcomes, {
            **metrics,
            "reason": "independent_residual_checks_not_both_exact",
        }

    corrected = resolved_outcomes.filter(
        ~(
            (pl.col("game_id") == game_id)
            & (pl.col("player_id") == int(player_id))
            & (pl.col("league_id") == int(league_id))
        )
    )
    return corrected, {
        **metrics,
        "applied": True,
        "quarantined_game_ids": [game_id],
        "quarantined_player_game_key": [game_id, int(player_id)],
        "reason": "single_source_only_game_exactly_equals_season_residual_and_removal_matches_official_gamelog",
        "source_values_reassigned": False,
    }
