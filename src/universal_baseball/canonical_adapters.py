"""Narrow source adapters into canonical observation tables.

These adapters intentionally project only fields already justified by source
certification. They do not flatten the complete MLB feed or attempt to recreate
a general-purpose baseball parser.
"""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Mapping

import polars as pl

from universal_baseball.canonical_schema import (
    PITCH_OBSERVATION_SCHEMA,
    PLAY_SEQUENCE_OBSERVATION_SCHEMA,
    validate_pitch_observation,
    validate_play_sequence_observation,
)
from universal_baseball.event_types import (
    KNOWN_EVENT_TYPES,
    PLATE_APPEARANCE_EVENT_TYPES,
)


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if isfinite(value) else None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return str(value)


def stable_payload_hash(value: Mapping[str, Any]) -> str:
    """Hash a source payload deterministically without depending on row order."""

    payload = json.dumps(
        _json_safe(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def current_event_semantics_snapshot_id() -> str:
    """Fingerprint the exact MLB event→plate-appearance semantics in use."""

    semantics = [
        {"event_type": event_type, "plate_appearance": event_type in PLATE_APPEARANCE_EVENT_TYPES}
        for event_type in sorted(KNOWN_EVENT_TYPES)
    ]
    payload = json.dumps(semantics, separators=(",", ":"), sort_keys=True)
    return sha256(payload.encode("utf-8")).hexdigest()


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _float(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if isfinite(parsed) else None


def _utc_datetime(value: Any) -> datetime | None:
    text = _text(value)
    if text is None:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(UTC)


def normalize_armstjc_pitch_observations(
    frame: pl.DataFrame,
    *,
    source_snapshot_id: str,
    normalization_id: str,
) -> pl.DataFrame:
    """Project reusable armstjc pitch rows into canonical pitch observations.

    Full raw source rows are hashed before projection, so two upstream payload
    variants remain distinct even if the currently canonical subset happens to
    agree. Byte/row-identical source duplicates compact into
    ``duplicate_row_count``. The known source batter mutation is preserved as
    ``source_batter_mlbam_id`` rather than corrected here.

    The canonical schema is supplied to Polars at construction time. Sparse
    source columns must never let inference choose a narrower type before a
    later valid value appears in the same asset.
    """

    required = {"game_pk", "at_bat_number", "pitch_number"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"armstjc frame missing pitch key columns: {missing}")

    accumulator: dict[tuple[int, int, int, str], dict[str, Any]] = {}
    for raw_row in frame.to_dicts():
        game_pk = _int(raw_row.get("game_pk"))
        at_bat_index = _int(raw_row.get("at_bat_number"))
        pitch_number = _int(raw_row.get("pitch_number"))
        if game_pk is None or at_bat_index is None or pitch_number is None:
            raise ValueError("armstjc physical pitch row has null/invalid natural key")

        payload_hash = stable_payload_hash(raw_row)
        key = (game_pk, at_bat_index, pitch_number, payload_hash)
        if key in accumulator:
            accumulator[key]["duplicate_row_count"] += 1
            continue

        pitch_code = _text(raw_row.get("type"))
        accumulator[key] = {
            "normalization_id": normalization_id,
            "source_snapshot_id": source_snapshot_id,
            "game_pk": game_pk,
            "at_bat_index": at_bat_index,
            "pitch_number": pitch_number,
            "payload_hash": payload_hash,
            "duplicate_row_count": 1,
            "source_batter_mlbam_id": _int(raw_row.get("batter")),
            "source_pitcher_mlbam_id": _int(raw_row.get("pitcher")),
            "batter_side": _text(raw_row.get("stand")),
            "pitcher_hand": _text(raw_row.get("p_throws")),
            "pitch_code": pitch_code,
            "is_in_play": pitch_code == "X" if pitch_code is not None else None,
            "bb_type": _text(raw_row.get("bb_type")),
            "hit_location": _int(raw_row.get("hit_location")),
            "hc_x": _float(raw_row.get("hc_x")),
            "hc_y": _float(raw_row.get("hc_y")),
            "pitch_type": _text(raw_row.get("pitch_type")),
            "pitch_name": _text(raw_row.get("pitch_name")),
            "release_speed": _float(raw_row.get("release_speed")),
            "release_pos_x": _float(raw_row.get("release_pos_x")),
            "release_pos_y": _float(raw_row.get("release_pos_y")),
            "release_pos_z": _float(raw_row.get("release_pos_z")),
            "plate_x": _float(raw_row.get("plate_x")),
            "plate_z": _float(raw_row.get("plate_z")),
            "pfx_x": _float(raw_row.get("pfx_x")),
            "pfx_z": _float(raw_row.get("pfx_z")),
            "release_spin_rate": _float(raw_row.get("release_spin_rate")),
            "spin_axis": _float(raw_row.get("spin_axis")),
            "release_extension": _float(raw_row.get("release_extension")),
            "launch_speed": _float(raw_row.get("launch_speed")),
            "launch_angle": _float(raw_row.get("launch_angle")),
            "hit_distance": _float(raw_row.get("hit_distance_sc")),
        }

    rows = list(accumulator.values())
    canonical = pl.from_dicts(
        rows,
        schema=PITCH_OBSERVATION_SCHEMA,
        strict=True,
    )
    return validate_pitch_observation(canonical)


def normalize_official_play_sequence_observations(
    game_id: int,
    payload: Mapping[str, Any],
    *,
    source_snapshot_id: str,
    normalization_id: str,
    event_semantics_snapshot_id: str | None = None,
) -> pl.DataFrame:
    """Project official Stats API ``allPlays`` into canonical sequence observations."""

    semantics_id = event_semantics_snapshot_id or current_event_semantics_snapshot_id()
    all_plays = payload.get("allPlays") or []
    if not isinstance(all_plays, list):
        raise ValueError("official playByPlay allPlays must be a list")

    accumulator: dict[tuple[int, int, str], dict[str, Any]] = {}
    for play_value in all_plays:
        play = _mapping(play_value)
        at_bat_index = _int(play.get("atBatIndex"))
        if at_bat_index is None:
            raise ValueError(f"official game {game_id} contains allPlays row without atBatIndex")

        result = _mapping(play.get("result"))
        event_type = _text(result.get("eventType"))
        if event_type is None:
            raise ValueError(
                f"official game {game_id} sequence {at_bat_index} has blank eventType"
            )
        if event_type not in KNOWN_EVENT_TYPES:
            raise ValueError(
                f"official game {game_id} sequence {at_bat_index} has unknown "
                f"eventType {event_type!r}"
            )

        matchup = _mapping(play.get("matchup"))
        batter = _mapping(matchup.get("batter"))
        pitcher = _mapping(matchup.get("pitcher"))
        bat_side = _mapping(matchup.get("batSide"))
        pitch_hand = _mapping(matchup.get("pitchHand"))
        about = _mapping(play.get("about"))
        play_events = play.get("playEvents") or []
        if not isinstance(play_events, list):
            play_events = []
        physical_pitch_count = sum(
            1 for event in play_events if _mapping(event).get("isPitch") is True
        )

        is_pa = event_type in PLATE_APPEARANCE_EVENT_TYPES
        payload_hash = stable_payload_hash(play)
        key = (int(game_id), at_bat_index, payload_hash)
        if key in accumulator:
            accumulator[key]["duplicate_row_count"] += 1
            continue

        accumulator[key] = {
            "normalization_id": normalization_id,
            "source_snapshot_id": source_snapshot_id,
            "game_pk": int(game_id),
            "at_bat_index": at_bat_index,
            "payload_hash": payload_hash,
            "duplicate_row_count": 1,
            "classification_status": "official_true_pa" if is_pa else "official_non_pa",
            "result_event_type": event_type,
            "result_event": _text(result.get("event")),
            "result_description": _text(result.get("description")),
            "is_plate_appearance": is_pa,
            "event_semantics_snapshot_id": semantics_id,
            "batter_mlbam_id": _int(batter.get("id")),
            "pitcher_mlbam_id": _int(pitcher.get("id")),
            "batter_side": _text(bat_side.get("code")),
            "pitcher_hand": _text(pitch_hand.get("code")),
            "inning": _int(about.get("inning")),
            "half_inning": _text(about.get("halfInning")),
            "sequence_start_time": _utc_datetime(about.get("startTime")),
            "sequence_end_time": _utc_datetime(about.get("endTime")),
            "official_physical_pitch_count": physical_pitch_count,
        }

    rows = list(accumulator.values())
    if not rows:
        raise ValueError(f"official game {game_id} playByPlay contains no sequences")
    canonical = pl.from_dicts(
        rows,
        schema=PLAY_SEQUENCE_OBSERVATION_SCHEMA,
        strict=True,
    )
    return validate_play_sequence_observation(canonical)
