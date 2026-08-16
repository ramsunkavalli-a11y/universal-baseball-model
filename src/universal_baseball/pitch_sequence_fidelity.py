"""Diagnostics for whether official MiLB playEvents represent real pitch sequences.

This module is intentionally descriptive. A plate-appearance outcome can be
reliable even when intermediate pitch events are compressed or synthetically
entered. The functions below summarize official Stats API ``allPlays`` without
assuming that every recorded ``isPitch`` event corresponds to a complete real
pitch sequence.

The main signatures are designed to expose outcome-minimal entry patterns:

- strikeouts represented by exactly three recorded pitch events;
- unintentional walks represented by exactly four recorded pitch events;
- batted-ball PAs represented by exactly one recorded pitch event;
- gaps between recorded event count and the largest official ``pitchNumber``.

No threshold in this module promotes or rejects a league. Certification policy
belongs in the audit/report layer after comparing complex/Rookie leagues with a
known higher-level control.
"""

from __future__ import annotations

from collections import Counter
from statistics import mean, median
from typing import Any, Mapping, Sequence

from universal_baseball.event_types import PLATE_APPEARANCE_EVENT_TYPES


STRIKEOUT_EVENT_TYPES = frozenset(
    {"strikeout", "strike_out", "strikeout_double_play", "strikeout_triple_play"}
)
WALK_EVENT_TYPES = frozenset({"walk"})
INTENTIONAL_WALK_EVENT_TYPES = frozenset({"intent_walk"})
HBP_EVENT_TYPES = frozenset({"hit_by_pitch"})
SPECIAL_NON_BIP_EVENT_TYPES = frozenset(
    {"catcher_interf", "batter_interference", "os_ruling_pending_primary"}
)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not number.is_integer():
        return None
    return int(number)


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def outcome_group(event_type: str) -> str:
    """Map an official true-PA event type to a pitch-fidelity outcome group."""

    if event_type in STRIKEOUT_EVENT_TYPES:
        return "strikeout"
    if event_type in WALK_EVENT_TYPES:
        return "walk"
    if event_type in INTENTIONAL_WALK_EVENT_TYPES:
        return "intentional_walk"
    if event_type in HBP_EVENT_TYPES:
        return "hit_by_pitch"
    if event_type in SPECIAL_NON_BIP_EVENT_TYPES:
        return "special_non_bip"
    return "batted_ball"


def summarize_game_pitch_sequences(
    game_pk: int,
    payload: Mapping[str, Any],
    *,
    season: int | None = None,
    league_id: int | None = None,
    league_name: str | None = None,
) -> list[dict[str, Any]]:
    """Return one diagnostic row per official true PA in a Stats API game."""

    rows: list[dict[str, Any]] = []
    for raw_play in payload.get("allPlays") or []:
        play = _mapping(raw_play)
        result = _mapping(play.get("result"))
        event_type = _text(result.get("eventType"))
        if event_type not in PLATE_APPEARANCE_EVENT_TYPES:
            continue
        at_bat_index = _int(play.get("atBatIndex"))
        if at_bat_index is None:
            continue

        pitch_events = [
            _mapping(event)
            for event in (play.get("playEvents") or [])
            if _mapping(event).get("isPitch") is True
        ]
        pitch_numbers = [
            value
            for value in (_int(event.get("pitchNumber")) for event in pitch_events)
            if value is not None
        ]
        codes: list[str] = []
        ball_flags: list[bool] = []
        strike_flags: list[bool] = []
        has_pitch_data: list[bool] = []
        for event in pitch_events:
            details = _mapping(event.get("details"))
            code = _text(details.get("code"))
            if code is not None:
                codes.append(code)
            ball_flags.append(details.get("isBall") is True)
            strike_flags.append(details.get("isStrike") is True)
            has_pitch_data.append(bool(_mapping(event.get("pitchData"))))

        pitch_count = len(pitch_events)
        max_pitch_number = max(pitch_numbers) if pitch_numbers else None
        pitch_number_gap = (
            max(max_pitch_number - pitch_count, 0)
            if max_pitch_number is not None
            else None
        )
        group = outcome_group(event_type)
        rows.append(
            {
                "game_pk": int(game_pk),
                "season": season,
                "league_id": league_id,
                "league_name": league_name,
                "at_bat_index": at_bat_index,
                "event_type": event_type,
                "outcome_group": group,
                "description": _text(result.get("description")),
                "recorded_pitch_event_count": pitch_count,
                "pitch_numbers": pitch_numbers,
                "max_pitch_number": max_pitch_number,
                "pitch_number_gap": pitch_number_gap,
                "ball_flag_count": sum(ball_flags),
                "strike_flag_count": sum(strike_flags),
                "neutral_flag_count": sum(
                    not ball and not strike
                    for ball, strike in zip(ball_flags, strike_flags, strict=True)
                ),
                "pitch_data_event_count": sum(has_pitch_data),
                "pitch_codes": codes,
                "exact_minimum_pitch_count": (
                    (group == "strikeout" and pitch_count == 3)
                    or (group == "walk" and pitch_count == 4)
                    or (group == "batted_ball" and pitch_count == 1)
                ),
                "outcome_minimal_clean_signature": (
                    (group == "strikeout" and pitch_count == 3 and sum(ball_flags) == 0)
                    or (
                        group == "walk"
                        and pitch_count == 4
                        and sum(strike_flags) == 0
                    )
                    or (group == "batted_ball" and pitch_count == 1)
                ),
            }
        )
    return rows


def _quantile(values: Sequence[int], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return float(ordered[lower] * (1 - fraction) + ordered[upper] * fraction)


def summarize_outcome_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Summarize a homogeneous outcome-group slice of PA diagnostic rows."""

    if not rows:
        return {
            "pa_count": 0,
            "mean_recorded_pitch_events": None,
            "median_recorded_pitch_events": None,
            "p25_recorded_pitch_events": None,
            "p75_recorded_pitch_events": None,
            "exact_minimum_pitch_count_rate": None,
            "outcome_minimal_clean_signature_rate": None,
            "any_pitch_number_gap_rate": None,
            "mean_pitch_number_gap": None,
            "any_ball_flag_rate": None,
            "any_strike_flag_rate": None,
            "full_pitch_data_rate": None,
            "recorded_pitch_count_distribution": {},
        }

    pitch_counts = [int(row["recorded_pitch_event_count"]) for row in rows]
    gaps = [
        int(row["pitch_number_gap"])
        for row in rows
        if row.get("pitch_number_gap") is not None
    ]
    distribution = Counter(pitch_counts)
    return {
        "pa_count": len(rows),
        "mean_recorded_pitch_events": mean(pitch_counts),
        "median_recorded_pitch_events": median(pitch_counts),
        "p25_recorded_pitch_events": _quantile(pitch_counts, 0.25),
        "p75_recorded_pitch_events": _quantile(pitch_counts, 0.75),
        "exact_minimum_pitch_count_rate": sum(
            bool(row.get("exact_minimum_pitch_count")) for row in rows
        )
        / len(rows),
        "outcome_minimal_clean_signature_rate": sum(
            bool(row.get("outcome_minimal_clean_signature")) for row in rows
        )
        / len(rows),
        "any_pitch_number_gap_rate": (
            sum(gap > 0 for gap in gaps) / len(gaps) if gaps else None
        ),
        "mean_pitch_number_gap": mean(gaps) if gaps else None,
        "any_ball_flag_rate": sum(int(row.get("ball_flag_count") or 0) > 0 for row in rows)
        / len(rows),
        "any_strike_flag_rate": sum(
            int(row.get("strike_flag_count") or 0) > 0 for row in rows
        )
        / len(rows),
        "full_pitch_data_rate": sum(
            int(row.get("pitch_data_event_count") or 0)
            == int(row.get("recorded_pitch_event_count") or 0)
            and int(row.get("recorded_pitch_event_count") or 0) > 0
            for row in rows
        )
        / len(rows),
        "recorded_pitch_count_distribution": {
            str(key): int(value) for key, value in sorted(distribution.items())
        },
    }


def summarize_league(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Summarize one league's PA diagnostics by outcome group."""

    groups = ("strikeout", "walk", "batted_ball", "intentional_walk", "hit_by_pitch")
    return {
        "pa_count": len(rows),
        "game_count": len({int(row["game_pk"]) for row in rows}),
        "outcomes": {
            group: summarize_outcome_rows(
                [row for row in rows if row.get("outcome_group") == group]
            )
            for group in groups
        },
    }
