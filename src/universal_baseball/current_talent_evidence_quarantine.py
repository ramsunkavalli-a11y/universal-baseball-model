"""Pure row quarantine helpers for already-proven source-authority failures."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import polars as pl


def quarantine_player_game_keys(
    frame: pl.DataFrame,
    keys: Iterable[tuple[int, int]],
    *,
    game_column: str,
    player_column: str,
    label: str,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Remove only explicitly supplied game/player keys from one evidence grain."""

    missing = sorted({game_column, player_column} - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing quarantine key fields: {missing}")
    normalized = sorted({(int(game), int(player)) for game, player in keys})
    if not normalized:
        return frame, {
            "label": label,
            "quarantined_key_count": 0,
            "quarantined_row_count": 0,
            "quarantined_keys": [],
        }
    predicate = pl.lit(False)
    for game_id, player_id in normalized:
        predicate = predicate | (
            (pl.col(game_column).cast(pl.Int64, strict=False) == game_id)
            & (pl.col(player_column).cast(pl.Int64, strict=False) == player_id)
        )
    removed = frame.filter(predicate)
    kept = frame.filter(~predicate)
    return kept, {
        "label": label,
        "quarantined_key_count": len(normalized),
        "quarantined_row_count": int(removed.height),
        "quarantined_keys": [list(key) for key in normalized],
    }


def quarantine_game_ids(
    frame: pl.DataFrame,
    game_ids: Iterable[int],
    *,
    game_column: str,
    label: str,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Remove only explicitly supplied unresolved whole-game IDs."""

    if game_column not in frame.columns:
        raise ValueError(f"{label} missing quarantine game field: {game_column}")
    normalized = sorted({int(game_id) for game_id in game_ids})
    if not normalized:
        return frame, {
            "label": label,
            "quarantined_game_count": 0,
            "quarantined_row_count": 0,
            "quarantined_game_ids": [],
        }
    predicate = pl.col(game_column).cast(pl.Int64, strict=False).is_in(normalized)
    removed = frame.filter(predicate)
    kept = frame.filter(~predicate)
    return kept, {
        "label": label,
        "quarantined_game_count": len(normalized),
        "quarantined_row_count": int(removed.height),
        "quarantined_game_ids": normalized,
    }
