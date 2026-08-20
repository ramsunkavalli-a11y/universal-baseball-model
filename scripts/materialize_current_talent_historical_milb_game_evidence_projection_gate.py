#!/usr/bin/env python
"""Projection-gate orchestration for the certified 2024 Current Talent MiLB source run.

This wrapper fixes one plumbing edge only: when the existing fail-closed exact
source-residual quarantine proves that a player's sole positive-PA source game is
spurious, the target player/league slice can legitimately become empty. In that
specific proven case, do not call the base gameLog adjudicator, whose contract
requires positive-PA source evidence.

The quarantine proof itself is unchanged. Source authority, identity, league
assignment, outcome values, Current Talent/Projection model design, and temporal
scope are unchanged. No 2025 data is accessed here.
"""

from __future__ import annotations

from typing import Any

import polars as pl

import materialize_current_talent_historical_milb_game_evidence_with_exact_game_fallback as gate


_EVIDENCE_SCHEMA = {
    "player_id": pl.Int64,
    "league_id": pl.Int64,
    "game_id": pl.Int64,
    "field": pl.String,
    "source_value": pl.Int64,
    "official_value": pl.Int64,
    "action": pl.String,
    "source_game_date": pl.Date,
    "official_game_date": pl.Date,
    "retained_game_date": pl.Date,
    "game_date_authority": pl.String,
}

_ORIGINAL_QUARANTINE = gate.quarantine_single_source_only_exact_residual
_ORIGINAL_APPLY_OFFICIAL = gate.base.apply_official_game_log_outcome_authority
_PROVEN_QUARANTINED_SLICES: set[tuple[int, int]] = set()


def _tracked_exact_residual_quarantine(
    resolved_outcomes: pl.DataFrame,
    official_game_log: pl.DataFrame,
    season_comparison_row: dict[str, Any],
    *,
    player_id: int,
    league_id: int,
):
    corrected, metrics = _ORIGINAL_QUARANTINE(
        resolved_outcomes,
        official_game_log,
        season_comparison_row,
        player_id=player_id,
        league_id=league_id,
    )
    if metrics.get("applied"):
        _PROVEN_QUARANTINED_SLICES.add((int(player_id), int(league_id)))
    return corrected, metrics


def _apply_official_after_exact_quarantine(
    resolved_outcomes: pl.DataFrame,
    official_game_log: pl.DataFrame,
    *,
    player_id: int,
    league_id: int,
):
    key = (int(player_id), int(league_id))
    target_source = resolved_outcomes.filter(
        (pl.col("player_id") == int(player_id))
        & (pl.col("league_id") == int(league_id))
        & (pl.col("game_type") == "R")
        & pl.col("batting_PA").is_not_null()
        & (pl.col("batting_PA") > 0)
    )
    if not target_source.is_empty() or key not in _PROVEN_QUARANTINED_SLICES:
        return _ORIGINAL_APPLY_OFFICIAL(
            resolved_outcomes,
            official_game_log,
            player_id=player_id,
            league_id=league_id,
        )

    official_positive = official_game_log.filter(
        (pl.col("player_id") == int(player_id))
        & (pl.col("league_id") == int(league_id))
        & (pl.col("game_type") == "R")
        & pl.col("batting_PA").is_not_null()
        & (pl.col("batting_PA") > 0)
    )
    if not official_positive.is_empty():
        raise ValueError(
            "exact source-residual quarantine emptied a slice that still has official "
            f"positive-PA evidence: player={player_id} league={league_id}"
        )

    zero_totals = {
        field: 0
        for field in (
            "batting_PA",
            "batting_AB",
            "batting_BB",
            "batting_HBP",
            "batting_SO",
            "batting_SF",
            "batting_SH",
            "batting_CI",
        )
    }
    return (
        resolved_outcomes.sort(["game_id", "player_id"]),
        pl.DataFrame(schema=_EVIDENCE_SCHEMA),
        {
            "policy": "official_game_log_after_proven_exact_source_residual_quarantine_v1",
            "player_id": int(player_id),
            "league_id": int(league_id),
            "classification": "exact_source_residual_quarantine_resolves_empty_slice",
            "source_positive_pa_game_count": 0,
            "official_positive_pa_game_count": 0,
            "overlay_existing_game_count": 0,
            "insert_official_only_positive_pa_game_count": 0,
            "source_only_positive_pa_game_count": 0,
            "changed_field_count": 0,
            "source_totals": zero_totals,
            "official_totals": zero_totals,
            "corrected_totals": zero_totals,
            "retrospective_corrected_history": True,
            "vintage_information_set": False,
            "empty_slice_allowed_only_after_proven_exact_residual_quarantine": True,
        },
    )


gate.quarantine_single_source_only_exact_residual = _tracked_exact_residual_quarantine
gate.base.apply_official_game_log_outcome_authority = _apply_official_after_exact_quarantine


if __name__ == "__main__":
    raise SystemExit(gate.base.main())
