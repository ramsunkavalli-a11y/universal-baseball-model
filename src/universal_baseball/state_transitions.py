"""Minimal official Stats API state-transition replay.

This module intentionally solves only the state surface needed for future RE24
work. It follows the public Chadwick/baseballquery event model rather than
flattening the complete feed:

- runner movements attached to an earlier ``playIndex`` become separate state
  transitions;
- the terminal play-sequence result becomes its own transition;
- start/end base occupancy, outs, and runs are explicit;
- official post-sequence bases/scores are reconciliation targets, not silently
  substituted into the reconstructed state.

This is still a POC contract. Responsibility, fielding credit, and full
Retrosheet event typing remain out of scope.
"""

from __future__ import annotations

from collections import defaultdict
import json
from typing import Any, Mapping

import polars as pl

from universal_baseball.event_types import PLATE_APPEARANCE_EVENT_TYPES


STATE_TRANSITION_SCHEMA: dict[str, pl.DataType] = {
    "normalization_id": pl.String,
    "source_snapshot_id": pl.String,
    "game_pk": pl.Int64,
    "inning": pl.Int64,
    "half_inning": pl.String,
    "at_bat_index": pl.Int64,
    "transition_index": pl.Int64,
    "play_event_index": pl.Int64,
    "is_terminal_sequence_result": pl.Boolean,
    "is_plate_appearance_result": pl.Boolean,
    "event_type": pl.String,
    "runner_event_types_json": pl.String,
    "start_outs": pl.Int64,
    "end_outs": pl.Int64,
    "event_outs": pl.Int64,
    "start_bases_code": pl.Int64,
    "end_bases_code": pl.Int64,
    "runs_scored": pl.Int64,
    "start_bat_score": pl.Int64,
    "end_bat_score": pl.Int64,
    "state_changed": pl.Boolean,
    "re24_state_event_candidate": pl.Boolean,
    "quality_flags_json": pl.String,
}

_BASES = ("1B", "2B", "3B")
_BASE_TO_BIT = {"1B": 1, "2B": 2, "3B": 4}
_ADMIN_EVENT_TYPES = frozenset(
    {
        "game_advisory",
        "mound_visit",
        "batter_timeout",
        "pitcher_step_off",
        "pitching_substitution",
        "offensive_substitution",
        "defensive_substitution",
        "defensive_switch",
        "umpire_substitution",
        "pitcher_switch",
        "injury",
        "ejection",
        "at_bat_start",
        "no_pitch",
    }
)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _base_label(value: Any) -> str | None:
    text = _text(value)
    if text in _BASES:
        return text
    if text in {"1", "2", "3"}:
        return f"{text}B"
    return None


def base_state_code(occupied: set[str]) -> int:
    return sum(_BASE_TO_BIT[base] for base in occupied if base in _BASE_TO_BIT)


def official_post_base_state_code(play: Mapping[str, Any]) -> int:
    matchup = _mapping(play.get("matchup"))
    occupied: set[str] = set()
    for field, base in (
        ("postOnFirst", "1B"),
        ("postOnSecond", "2B"),
        ("postOnThird", "3B"),
    ):
        if _mapping(matchup.get(field)).get("id") is not None:
            occupied.add(base)
    return base_state_code(occupied)


def _batting_score(
    half_inning: str,
    *,
    away_score: int,
    home_score: int,
) -> int:
    return away_score if half_inning.lower() == "top" else home_score


def _compact_runner_movements(
    runner_rows: list[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Collapse multi-step same-runner movements attached to one playIndex.

    Stats API can record an SB and subsequent error for the same runner at the
    same play index. Mirroring baseballquery's longest-advance treatment, the
    state transition should remove the runner once from the first origin and
    place him once at the final destination.
    """

    by_runner: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    quality: list[str] = []
    for ordinal, row in enumerate(runner_rows):
        details = _mapping(row.get("details"))
        runner = _mapping(details.get("runner"))
        runner_id = _text(runner.get("id"))
        if runner_id is None:
            runner_id = f"unknown:{ordinal}"
            quality.append("runner_id_missing")
        by_runner[runner_id].append(row)

    compacted: list[dict[str, Any]] = []
    for runner_id, rows in by_runner.items():
        first = rows[0]
        last = rows[-1]
        first_movement = _mapping(first.get("movement"))
        last_movement = _mapping(last.get("movement"))
        origin = _base_label(
            first_movement.get("originBase") or first_movement.get("start")
        )
        end_raw = last_movement.get("end")
        end = _base_label(end_raw)
        scoring = any(
            _mapping(row.get("details")).get("isScoringEvent") is True
            or str(_mapping(row.get("movement")).get("end") or "").lower()
            in {"score", "home"}
            for row in rows
        )
        is_out = bool(
            last_movement.get("isOut") is True
            or _mapping(last.get("details")).get("isOut") is True
        )
        compacted.append(
            {
                "runner_id": runner_id,
                "origin": origin,
                "end": end,
                "scoring": scoring,
                "is_out": is_out,
                "event_types": sorted(
                    {
                        event_type
                        for row in rows
                        if (event_type := _text(_mapping(row.get("details")).get("eventType")))
                    }
                ),
            }
        )
    return compacted, sorted(set(quality))


def _apply_runner_movements(
    occupied: set[str],
    runner_rows: list[Mapping[str, Any]],
) -> tuple[set[str], int, list[str], list[str]]:
    compacted, quality = _compact_runner_movements(runner_rows)
    result = set(occupied)
    event_types: set[str] = set()

    # Remove all origins before adding destinations so double steals/advances do
    # not overwrite one another in the occupancy state.
    for movement in compacted:
        origin = movement["origin"]
        if origin is not None:
            result.discard(origin)
        event_types.update(movement["event_types"])

    runs = 0
    for movement in compacted:
        if movement["scoring"]:
            runs += 1
            continue
        if movement["is_out"]:
            continue
        end = movement["end"]
        if end is not None:
            result.add(end)

    return result, runs, sorted(event_types), quality


def _event_outs(event: Mapping[str, Any]) -> int | None:
    return _int(_mapping(event.get("count")).get("outs"))


def _runner_placed_base(event: Mapping[str, Any]) -> str | None:
    details = _mapping(event.get("details"))
    if _text(details.get("eventType")) != "runner_placed":
        return None
    return _base_label(event.get("base"))


def _transition_row(
    *,
    normalization_id: str,
    source_snapshot_id: str,
    game_pk: int,
    inning: int,
    half_inning: str,
    at_bat_index: int,
    transition_index: int,
    play_event_index: int,
    terminal: bool,
    event_type: str,
    runner_event_types: list[str],
    start_outs: int,
    end_outs: int,
    start_bases: set[str],
    end_bases: set[str],
    runs_scored: int,
    start_bat_score: int,
    end_bat_score: int,
    quality_flags: list[str],
) -> dict[str, Any]:
    if end_outs < start_outs or end_outs > 3:
        quality_flags = [*quality_flags, "invalid_out_transition"]
    event_outs = max(end_outs - start_outs, 0)
    if end_outs >= 3:
        end_bases = set()
    start_code = base_state_code(start_bases)
    end_code = base_state_code(end_bases)
    state_changed = (
        start_code != end_code
        or start_outs != end_outs
        or runs_scored != 0
    )
    is_pa = terminal and event_type in PLATE_APPEARANCE_EVENT_TYPES
    candidate = is_pa or (state_changed and event_type not in _ADMIN_EVENT_TYPES)
    return {
        "normalization_id": normalization_id,
        "source_snapshot_id": source_snapshot_id,
        "game_pk": game_pk,
        "inning": inning,
        "half_inning": half_inning,
        "at_bat_index": at_bat_index,
        "transition_index": transition_index,
        "play_event_index": play_event_index,
        "is_terminal_sequence_result": terminal,
        "is_plate_appearance_result": is_pa,
        "event_type": event_type,
        "runner_event_types_json": json.dumps(
            runner_event_types, separators=(",", ":")
        ),
        "start_outs": start_outs,
        "end_outs": end_outs,
        "event_outs": event_outs,
        "start_bases_code": start_code,
        "end_bases_code": end_code,
        "runs_scored": runs_scored,
        "start_bat_score": start_bat_score,
        "end_bat_score": end_bat_score,
        "state_changed": state_changed,
        "re24_state_event_candidate": candidate,
        "quality_flags_json": json.dumps(
            sorted(set(quality_flags)), separators=(",", ":")
        ),
    }


def build_official_state_transitions(
    game_pk: int,
    payload: Mapping[str, Any],
    *,
    source_snapshot_id: str,
    normalization_id: str,
) -> pl.DataFrame:
    """Replay official allPlays into a minimal ordered state-transition table."""

    all_plays = payload.get("allPlays") or []
    if not isinstance(all_plays, list):
        raise ValueError("official playByPlay allPlays must be a list")

    occupied: set[str] = set()
    current_outs = 0
    away_score = 0
    home_score = 0
    current_half: tuple[int, str] | None = None
    rows: list[dict[str, Any]] = []

    for raw_play in all_plays:
        play = _mapping(raw_play)
        at_bat_index = _int(play.get("atBatIndex"))
        about = _mapping(play.get("about"))
        inning = _int(about.get("inning"))
        half_inning = (_text(about.get("halfInning")) or "").lower()
        if at_bat_index is None or inning is None or half_inning not in {"top", "bottom"}:
            continue

        half_key = (inning, half_inning)
        if half_key != current_half:
            occupied = set()
            current_outs = 0
            current_half = half_key

        events_value = play.get("playEvents") or []
        events = events_value if isinstance(events_value, list) else []
        runners_value = play.get("runners") or []
        runners = runners_value if isinstance(runners_value, list) else []
        terminal_index = len(events) - 1 if events else 0

        runner_by_index: dict[int, list[Mapping[str, Any]]] = defaultdict(list)
        out_of_range_runner_index = False
        for raw_runner in runners:
            runner = _mapping(raw_runner)
            play_index = _int(_mapping(runner.get("details")).get("playIndex"))
            if play_index is None:
                continue
            if events and play_index > terminal_index:
                out_of_range_runner_index = True
                continue
            runner_by_index[play_index].append(runner)

        state_event_indices = {
            index for index in runner_by_index if index < terminal_index
        }
        for index, raw_event in enumerate(events):
            if index >= terminal_index:
                continue
            if _runner_placed_base(_mapping(raw_event)) is not None:
                state_event_indices.add(index)

        result = _mapping(play.get("result"))
        terminal_event_type = _text(result.get("eventType")) or "<blank>"
        transition_index = 0

        for play_index in sorted(state_event_indices):
            event = _mapping(events[play_index]) if play_index < len(events) else {}
            details = _mapping(event.get("details"))
            event_type = _text(details.get("eventType")) or "<blank>"
            start_bases = set(occupied)
            start_outs = current_outs
            start_score = _batting_score(
                half_inning, away_score=away_score, home_score=home_score
            )
            quality: list[str] = []
            occupied, runs, runner_event_types, movement_quality = _apply_runner_movements(
                occupied, runner_by_index.get(play_index, [])
            )
            quality.extend(movement_quality)

            placed_base = _runner_placed_base(event)
            if placed_base is not None:
                occupied.add(placed_base)
                if event_type not in runner_event_types:
                    runner_event_types.append(event_type)

            end_outs = _event_outs(event)
            if end_outs is None:
                end_outs = current_outs + sum(
                    1
                    for movement in runner_by_index.get(play_index, [])
                    if _mapping(movement.get("movement")).get("isOut") is True
                )
                quality.append("outs_inferred_from_runner_movements")
            current_outs = end_outs
            if half_inning == "top":
                away_score += runs
            else:
                home_score += runs
            end_score = _batting_score(
                half_inning, away_score=away_score, home_score=home_score
            )

            rows.append(
                _transition_row(
                    normalization_id=normalization_id,
                    source_snapshot_id=source_snapshot_id,
                    game_pk=game_pk,
                    inning=inning,
                    half_inning=half_inning,
                    at_bat_index=at_bat_index,
                    transition_index=transition_index,
                    play_event_index=play_index,
                    terminal=False,
                    event_type=event_type,
                    runner_event_types=sorted(set(runner_event_types)),
                    start_outs=start_outs,
                    end_outs=end_outs,
                    start_bases=start_bases,
                    end_bases=set(occupied),
                    runs_scored=runs,
                    start_bat_score=start_score,
                    end_bat_score=end_score,
                    quality_flags=quality,
                )
            )
            transition_index += 1

        # Terminal result. Runner movements at the terminal index belong to the
        # terminal event; preterminal movements have already updated the live state.
        terminal_event = _mapping(events[terminal_index]) if events else {}
        start_bases = set(occupied)
        start_outs = current_outs
        start_score = _batting_score(
            half_inning, away_score=away_score, home_score=home_score
        )
        quality = ["runner_play_index_out_of_range"] if out_of_range_runner_index else []
        occupied, runs, runner_event_types, movement_quality = _apply_runner_movements(
            occupied, runner_by_index.get(terminal_index, [])
        )
        quality.extend(movement_quality)

        placed_base = _runner_placed_base(terminal_event)
        if placed_base is not None:
            occupied.add(placed_base)
            if terminal_event_type not in runner_event_types:
                runner_event_types.append(terminal_event_type)

        end_outs = _event_outs(terminal_event)
        if end_outs is None:
            runner_outs = sum(
                1
                for movement in runner_by_index.get(terminal_index, [])
                if _mapping(movement.get("movement")).get("isOut") is True
            )
            result_is_out = result.get("isOut") is True
            end_outs = current_outs + runner_outs
            if result_is_out and runner_outs == 0:
                end_outs += 1
            quality.append("terminal_outs_inferred")
        current_outs = end_outs

        if half_inning == "top":
            away_score += runs
        else:
            home_score += runs
        end_score = _batting_score(
            half_inning, away_score=away_score, home_score=home_score
        )

        official_away = _int(result.get("awayScore"))
        official_home = _int(result.get("homeScore"))
        if official_away is not None and official_home is not None:
            if (away_score, home_score) != (official_away, official_home):
                quality.append("sequence_end_score_mismatch")

        reconstructed_end_bases = base_state_code(set() if end_outs >= 3 else occupied)
        official_end_bases = official_post_base_state_code(play)
        if reconstructed_end_bases != official_end_bases:
            quality.append("sequence_end_bases_mismatch")

        rows.append(
            _transition_row(
                normalization_id=normalization_id,
                source_snapshot_id=source_snapshot_id,
                game_pk=game_pk,
                inning=inning,
                half_inning=half_inning,
                at_bat_index=at_bat_index,
                transition_index=transition_index,
                play_event_index=terminal_index,
                terminal=True,
                event_type=terminal_event_type,
                runner_event_types=sorted(set(runner_event_types)),
                start_outs=start_outs,
                end_outs=end_outs,
                start_bases=start_bases,
                end_bases=set(occupied),
                runs_scored=runs,
                start_bat_score=start_score,
                end_bat_score=end_score,
                quality_flags=quality,
            )
        )

        # Preserve our replayed state rather than resetting to official end state;
        # otherwise a mismatch would be hidden and could not propagate into the
        # next continuity check. At inning end the next half explicitly resets.
        if current_outs >= 3:
            occupied = set()

    if not rows:
        return pl.DataFrame(schema=STATE_TRANSITION_SCHEMA)
    return (
        pl.from_dicts(rows, schema=STATE_TRANSITION_SCHEMA, strict=True)
        .sort(["game_pk", "inning", "half_inning", "at_bat_index", "transition_index"])
    )


def transition_quality_flags(frame: pl.DataFrame) -> pl.DataFrame:
    """Return transitions carrying one or more explicit replay quality flags."""

    if "quality_flags_json" not in frame.columns:
        raise ValueError("state transition table missing quality_flags_json")
    return frame.filter(pl.col("quality_flags_json") != "[]")
