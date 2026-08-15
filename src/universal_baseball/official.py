"""Thin official-source projections used for certification.

The project intentionally does not flatten the full MLB Stats API feed here.
`python-mlb-statsapi` owns transport and response modeling; we project only the
plate-appearance and pitch-event fields needed to verify reusable sources.
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

OFFICIAL_PITCH_EVENT_COLUMNS = (
    "game_pk",
    "at_bat_number",
    "event_index",
    "pitch_number",
    "code",
    "event",
    "event_type",
    "description",
    "has_pitch_data",
    "pitch_type_code",
)


def _empty_pa_frame() -> pl.DataFrame:
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


def _empty_pitch_event_frame() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "game_pk": pl.String,
            "at_bat_number": pl.String,
            "event_index": pl.Int64,
            "pitch_number": pl.Int64,
            "code": pl.String,
            "event": pl.String,
            "event_type": pl.String,
            "description": pl.String,
            "has_pitch_data": pl.Boolean,
            "pitch_type_code": pl.String,
        }
    )


def fetch_official_game_evidence(
    game_ids: Iterable[int],
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Fetch PA rows plus current official events marked as pitches.

    `python-mlb-statsapi` owns HTTP transport and response modeling. We retain
    enough pitch-event detail to explain disagreements with a reused historical
    source without building our own MLB feed parser.

    The live-feed `pitchIndex` array is deliberately not used as a pitch count.
    In real MiLB games it can contain more references than there are current
    `playEvents` marked `isPitch=true` (for example after feed revisions). The
    current `playEvents` collection is the evidence we actually compare.
    """

    pa_rows: list[dict[str, Any]] = []
    pitch_event_rows: list[dict[str, Any]] = []

    with mlbstatsapi.Mlb() as mlb:
        for game_id in game_ids:
            plays = mlb.get_game_play_by_play(int(game_id))
            if plays is None:
                continue

            for play in plays.all_plays:
                game_key = str(game_id)
                pa_key = str(play.at_bat_index)
                current_pitch_events = [
                    play_event
                    for play_event in play.play_events
                    if play_event.is_pitch
                ]

                pa_rows.append(
                    {
                        "game_pk": game_key,
                        "at_bat_number": pa_key,
                        "result_type": play.result.type,
                        "event": play.result.event,
                        "event_type": play.result.event_type,
                        "description": play.result.description,
                        "official_pitch_count": len(current_pitch_events),
                    }
                )

                for play_event in current_pitch_events:
                    details = play_event.details
                    pitch_type = details.type if details is not None else None
                    pitch_event_rows.append(
                        {
                            "game_pk": game_key,
                            "at_bat_number": pa_key,
                            "event_index": play_event.index,
                            "pitch_number": play_event.pitch_number,
                            "code": None if details is None else details.code,
                            "event": None if details is None else details.event,
                            "event_type": None if details is None else details.event_type,
                            "description": None if details is None else details.description,
                            "has_pitch_data": play_event.pitch_data is not None,
                            "pitch_type_code": None
                            if pitch_type is None
                            else pitch_type.code,
                        }
                    )

    pa_frame = pl.DataFrame(pa_rows) if pa_rows else _empty_pa_frame()
    pitch_frame = (
        pl.DataFrame(pitch_event_rows)
        if pitch_event_rows
        else _empty_pitch_event_frame()
    )

    if pa_rows:
        pa_frame = pa_frame.with_columns(
            [
                pl.col("game_pk").cast(pl.String),
                pl.col("at_bat_number").cast(pl.String),
            ]
        )
    if pitch_event_rows:
        pitch_frame = pitch_frame.with_columns(
            [
                pl.col("game_pk").cast(pl.String),
                pl.col("at_bat_number").cast(pl.String),
            ]
        )

    return pa_frame, pitch_frame


def fetch_official_pa_results(game_ids: Iterable[int]) -> pl.DataFrame:
    """Fetch one row per official play/PA for selected game IDs."""

    pa_frame, _ = fetch_official_game_evidence(game_ids)
    return pa_frame
