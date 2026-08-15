"""Thin official-source projections used for certification.

The project intentionally does not flatten the full MLB Stats API feed here.
`python-mlb-statsapi` owns HTTP transport, retries, and error handling through
its stable public low-level adapter. We project only the plate-appearance,
pitch-event, and boxscore batting fields needed to verify reusable sources and
our own event aggregation.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from mlbstatsapi import MlbDataAdapter
import polars as pl


OFFICIAL_PA_COLUMNS = (
    "game_pk",
    "at_bat_number",
    "result_type",
    "event",
    "event_type",
    "description",
    "half_inning",
    "batting_side",
    "batter_id",
    "pitcher_id",
    "batter_side",
    "pitcher_hand",
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

OFFICIAL_TEAM_BATTING_COLUMNS = (
    "game_pk",
    "batting_side",
    "plate_appearances",
    "at_bats",
    "hits",
    "doubles",
    "triples",
    "home_runs",
    "base_on_balls",
    "intentional_walks",
    "hit_by_pitch",
    "strikeouts",
    "sac_bunts",
    "sac_flies",
    "catchers_interference",
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
            "half_inning": pl.String,
            "batting_side": pl.String,
            "batter_id": pl.Int64,
            "pitcher_id": pl.Int64,
            "batter_side": pl.String,
            "pitcher_hand": pl.String,
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


def _empty_team_batting_frame() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "game_pk": pl.String,
            "batting_side": pl.String,
            "plate_appearances": pl.Int64,
            "at_bats": pl.Int64,
            "hits": pl.Int64,
            "doubles": pl.Int64,
            "triples": pl.Int64,
            "home_runs": pl.Int64,
            "base_on_balls": pl.Int64,
            "intentional_walks": pl.Int64,
            "hit_by_pitch": pl.Int64,
            "strikeouts": pl.Int64,
            "sac_bunts": pl.Int64,
            "sac_flies": pl.Int64,
            "catchers_interference": pl.Int64,
        }
    )


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _batting_side_from_half_inning(value: Any) -> str | None:
    if value is None:
        return None
    label = str(value).strip().lower()
    if label == "top":
        return "away"
    if label == "bottom":
        return "home"
    return None


def project_official_play_by_play(
    game_id: int,
    payload: Mapping[str, Any],
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Project a raw MLB playByPlay payload into certification evidence.

    This deliberately extracts a tiny stable surface instead of mirroring the
    full feed schema. Missing optional nested fields remain null. In particular,
    MiLB can emit ``details.type={"description": "Unknown"}`` without a pitch
    type code; that is valid source data and must not make ingestion fail.

    Zero-pitch plate appearances (for example a signaled intentional walk) are
    retained in the PA table even though they have no corresponding pitch row.
    """

    pa_rows: list[dict[str, Any]] = []
    pitch_event_rows: list[dict[str, Any]] = []
    game_key = str(game_id)

    all_plays = payload.get("allPlays") or []
    if not isinstance(all_plays, list):
        all_plays = []

    for play_value in all_plays:
        play = _mapping(play_value)
        result = _mapping(play.get("result"))
        about = _mapping(play.get("about"))
        matchup = _mapping(play.get("matchup"))
        batter = _mapping(matchup.get("batter"))
        pitcher = _mapping(matchup.get("pitcher"))
        bat_side = _mapping(matchup.get("batSide"))
        pitch_hand = _mapping(matchup.get("pitchHand"))
        at_bat_index = play.get("atBatIndex")
        pa_key = None if at_bat_index is None else str(at_bat_index)
        half_inning = about.get("halfInning")

        play_events_value = play.get("playEvents") or []
        play_events = (
            play_events_value if isinstance(play_events_value, list) else []
        )
        current_pitch_events = [
            _mapping(event)
            for event in play_events
            if _mapping(event).get("isPitch") is True
        ]

        pa_rows.append(
            {
                "game_pk": game_key,
                "at_bat_number": pa_key,
                "result_type": result.get("type"),
                "event": result.get("event"),
                "event_type": result.get("eventType"),
                "description": result.get("description"),
                "half_inning": half_inning,
                "batting_side": _batting_side_from_half_inning(half_inning),
                "batter_id": _int_or_none(batter.get("id")),
                "pitcher_id": _int_or_none(pitcher.get("id")),
                "batter_side": bat_side.get("code"),
                "pitcher_hand": pitch_hand.get("code"),
                "official_pitch_count": len(current_pitch_events),
            }
        )

        for play_event in current_pitch_events:
            details = _mapping(play_event.get("details"))
            pitch_type = _mapping(details.get("type"))
            pitch_event_rows.append(
                {
                    "game_pk": game_key,
                    "at_bat_number": pa_key,
                    "event_index": _int_or_none(play_event.get("index")),
                    "pitch_number": _int_or_none(play_event.get("pitchNumber")),
                    "code": details.get("code"),
                    "event": details.get("event"),
                    "event_type": details.get("eventType"),
                    "description": details.get("description"),
                    "has_pitch_data": play_event.get("pitchData") is not None,
                    "pitch_type_code": pitch_type.get("code"),
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
                pl.col("batter_id").cast(pl.Int64),
                pl.col("pitcher_id").cast(pl.Int64),
                pl.col("official_pitch_count").cast(pl.Int64),
            ]
        )
    if pitch_event_rows:
        pitch_frame = pitch_frame.with_columns(
            [
                pl.col("game_pk").cast(pl.String),
                pl.col("at_bat_number").cast(pl.String),
                pl.col("event_index").cast(pl.Int64),
                pl.col("pitch_number").cast(pl.Int64),
            ]
        )

    return pa_frame, pitch_frame


def project_official_boxscore(
    game_id: int,
    payload: Mapping[str, Any],
) -> pl.DataFrame:
    """Project official team batting totals from a Stats API boxscore payload.

    The field names mirror the Stats API's simple hitting-stat surface already
    represented by ``python-mlb-statsapi``. We still use the low-level payload
    here so an optional or irregular MiLB field cannot invalidate the full game.
    """

    teams = _mapping(payload.get("teams"))
    rows: list[dict[str, Any]] = []

    source_fields = {
        "plate_appearances": "plateAppearances",
        "at_bats": "atBats",
        "hits": "hits",
        "doubles": "doubles",
        "triples": "triples",
        "home_runs": "homeRuns",
        "base_on_balls": "baseOnBalls",
        "intentional_walks": "intentionalWalks",
        "hit_by_pitch": "hitByPitch",
        "strikeouts": "strikeOuts",
        "sac_bunts": "sacBunts",
        "sac_flies": "sacFlies",
        "catchers_interference": "catchersInterference",
    }

    for side in ("away", "home"):
        team = _mapping(teams.get(side))
        team_stats = _mapping(team.get("teamStats"))
        batting = _mapping(team_stats.get("batting"))
        if not batting:
            continue

        row: dict[str, Any] = {
            "game_pk": str(game_id),
            "batting_side": side,
        }
        for target, source in source_fields.items():
            row[target] = _int_or_none(batting.get(source))
        rows.append(row)

    if not rows:
        return _empty_team_batting_frame()

    return pl.DataFrame(rows).select(list(OFFICIAL_TEAM_BATTING_COLUMNS)).with_columns(
        [
            pl.col("game_pk").cast(pl.String),
            *[
                pl.col(column).cast(pl.Int64)
                for column in OFFICIAL_TEAM_BATTING_COLUMNS
                if column not in {"game_pk", "batting_side"}
            ],
        ]
    )


def fetch_official_game_evidence(
    game_ids: Iterable[int],
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Fetch official PAs and current pitch events for selected games.

    The stable public ``MlbDataAdapter`` supplies transport/retries, while the
    project owns only the narrow projection in :func:`project_official_play_by_play`.
    This avoids depending on stricter third-party object models for irregular
    but valid MiLB payloads.
    """

    pa_frames: list[pl.DataFrame] = []
    pitch_frames: list[pl.DataFrame] = []
    adapter = MlbDataAdapter(ver="v1")
    try:
        for game_id in game_ids:
            response = adapter.get(f"game/{int(game_id)}/playByPlay")
            if not response.data:
                continue
            pa_frame, pitch_frame = project_official_play_by_play(
                int(game_id), response.data
            )
            pa_frames.append(pa_frame)
            pitch_frames.append(pitch_frame)
    finally:
        adapter.close()

    pa_frame = (
        pl.concat(pa_frames, how="vertical_relaxed")
        if pa_frames
        else _empty_pa_frame()
    )
    pitch_frame = (
        pl.concat(pitch_frames, how="vertical_relaxed")
        if pitch_frames
        else _empty_pitch_event_frame()
    )
    return pa_frame, pitch_frame


def fetch_official_team_batting(game_ids: Iterable[int]) -> pl.DataFrame:
    """Fetch official home/away team batting totals for selected games."""

    frames: list[pl.DataFrame] = []
    adapter = MlbDataAdapter(ver="v1")
    try:
        for game_id in game_ids:
            response = adapter.get(f"game/{int(game_id)}/boxscore")
            if not response.data:
                continue
            frame = project_official_boxscore(int(game_id), response.data)
            if not frame.is_empty():
                frames.append(frame)
    finally:
        adapter.close()

    return (
        pl.concat(frames, how="vertical_relaxed")
        if frames
        else _empty_team_batting_frame()
    )


def fetch_official_pa_results(game_ids: Iterable[int]) -> pl.DataFrame:
    """Fetch one row per official play/PA for selected game IDs."""

    pa_frame, _ = fetch_official_game_evidence(game_ids)
    return pa_frame
