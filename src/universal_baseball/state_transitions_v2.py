"""Second state-transition replay POC with correct terminal-outs semantics.

This version preserves the v1 movement algorithm but adopts the exact public
baseballquery distinction discovered during live certification:

- preterminal runner/action transition outs come from that playEvent's count;
- the terminal/top-level transition outs come from allPlay.count.outs.

The implementation intentionally imports the already-tested v1 helper functions
rather than cloning their movement semantics while this gate is still a POC.
After live validation the two modules can be consolidated into the canonical
state-transition implementation.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping

import polars as pl

from universal_baseball.state_transitions import (
    STATE_TRANSITION_SCHEMA,
    _apply_runner_movements,
    _batting_score,
    _event_outs,
    _int,
    _mapping,
    _runner_placed_base,
    _text,
    _transition_row,
    official_post_base_state_code,
)


def build_official_state_transitions_v2(
    game_pk: int,
    payload: Mapping[str, Any],
    *,
    source_snapshot_id: str,
    normalization_id: str,
) -> pl.DataFrame:
    """Replay official allPlays with top-level terminal outs semantics."""

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

        # Runner/action subevents use their individual playEvent count, matching
        # the established baseballquery/Chadwick reconstruction pattern.
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

        # Crucial v2 rule: the terminal/top-level outs state belongs to the
        # allPlay count. The terminal playEvent count can still reflect the
        # pre-result state.
        end_outs = _int(_mapping(play.get("count")).get("outs"))
        if end_outs is None:
            end_outs = _event_outs(terminal_event)
            quality.append("terminal_outs_fell_back_to_play_event")
        if end_outs is None:
            runner_outs = sum(
                1
                for movement in runner_by_index.get(terminal_index, [])
                if _mapping(movement.get("movement")).get("isOut") is True
            )
            end_outs = current_outs + runner_outs
            if result.get("isOut") is True and runner_outs == 0:
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

        reconstructed_end_bases = 0 if end_outs >= 3 else sum(
            1 << index for index, base in enumerate(("1B", "2B", "3B")) if base in occupied
        )
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

        # Do not repair from official postOn. The next event sees reconstructed
        # state, so any non-inning-ending movement mistake can propagate and be
        # caught by later reconciliation. Third outs naturally reset next half.
        if current_outs >= 3:
            occupied = set()

    if not rows:
        return pl.DataFrame(schema=STATE_TRANSITION_SCHEMA)
    return (
        pl.from_dicts(rows, schema=STATE_TRANSITION_SCHEMA, strict=True)
        .sort(["game_pk", "inning", "half_inning", "at_bat_index", "transition_index"])
    )
