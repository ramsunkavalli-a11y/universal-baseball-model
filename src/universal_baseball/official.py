"""Thin official-source projections used for certification.

The project intentionally does not flatten the full MLB Stats API feed here.
`python-mlb-statsapi` owns transport and response modeling; we project only the
plate-appearance fields needed to verify a reusable pitch-level source.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import mlbstatsapi
import polars as pl


OFFICIAL_PA_COLUMNS = (
    "game_pk",
    "at_bat_number",
    "result_type",
    "event",
    "event_type",
    "description",
    "official_pitch_count",
)


def fetch_official_pa_results(game_ids: Iterable[int]) -> pl.DataFrame:
    """Fetch one row per official play/PA for selected game IDs."""

    rows: list[dict[str, Any]] = []

    with mlbstatsapi.Mlb() as mlb:
        for game_id in game_ids:
            plays = mlb.get_game_play_by_play(int(game_id))
            if plays is None:
                continue

            for play in plays.all_plays:
                rows.append(
                    {
                        "game_pk": str(game_id),
                        "at_bat_number": str(play.at_bat_index),
                        "result_type": play.result.type,
                        "event": play.result.event,
                        "event_type": play.result.event_type,
                        "description": play.result.description,
                        "official_pitch_count": len(play.pitch_index),
                    }
                )

    if not rows:
        return pl.DataFrame(
            schema={
                "game_pk": pl.String,
                "at_bat_number": pl.String,
                "result_type": pl.String,
                "event": pl.String,
                "event_type": pl.String,
                "description": pl.String,
                "official_pitch_count": pl.Int64,
            }
        )

    return pl.DataFrame(rows).with_columns(
        [
            pl.col("game_pk").cast(pl.String),
            pl.col("at_bat_number").cast(pl.String),
        ]
    )
