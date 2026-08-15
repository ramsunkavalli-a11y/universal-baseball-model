"""Terminal-outs correction for the state-transition POC.

baseballquery's public Stats API -> Chadwick reconstruction uses the top-level
``allPlay.count.outs`` for a terminal/top-level event, while it uses individual
``playEvent.count.outs`` for runner subevents. The first replay POC used the
terminal playEvent count for both, which can remain at two outs on an
inning-ending play.

This module applies that already-established distinction conservatively. It
refuses to paper over any discrepancy that would continue within the same half
inning; only an official terminal count of three may differ from the provisional
playEvent-based replay. That makes the correction safe without resetting later
reconstructed state from official end values.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

import polars as pl

from universal_baseball.state_transitions import official_post_base_state_code


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def apply_terminal_allplay_outs(
    transitions: pl.DataFrame,
    payload: Mapping[str, Any],
) -> pl.DataFrame:
    """Use top-level allPlay outs for terminal transitions.

    A non-third-out disagreement is treated as a structural error because the
    provisional replay would then have carried the wrong outs state into a later
    event in the same half inning. Third-out corrections are safe because the
    next half inning resets the live state.
    """

    if transitions.is_empty():
        return transitions
    required = {
        "at_bat_index",
        "is_terminal_sequence_result",
        "start_outs",
        "end_outs",
        "event_outs",
        "start_bases_code",
        "end_bases_code",
        "runs_scored",
        "state_changed",
        "quality_flags_json",
    }
    missing = sorted(required - set(transitions.columns))
    if missing:
        raise ValueError(f"state transitions missing terminal-outs fields: {missing}")

    all_plays = payload.get("allPlays") or []
    if not isinstance(all_plays, list):
        raise ValueError("official playByPlay allPlays must be a list")

    terminal_semantics: dict[int, tuple[int | None, int]] = {}
    for raw_play in all_plays:
        play = _mapping(raw_play)
        at_bat_index = _int(play.get("atBatIndex"))
        if at_bat_index is None:
            continue
        terminal_semantics[at_bat_index] = (
            _int(_mapping(play.get("count")).get("outs")),
            official_post_base_state_code(play),
        )

    rows: list[dict[str, Any]] = []
    for row in transitions.to_dicts():
        if not row["is_terminal_sequence_result"]:
            rows.append(row)
            continue

        at_bat_index = int(row["at_bat_index"])
        official_outs, official_end_bases = terminal_semantics.get(
            at_bat_index, (None, row["end_bases_code"])
        )
        flags = list(json.loads(row["quality_flags_json"]))

        if official_outs is not None and official_outs != row["end_outs"]:
            if official_outs != 3:
                raise ValueError(
                    "terminal playEvent outs disagree with top-level allPlay outs "
                    "before inning end: "
                    f"at_bat_index={at_bat_index}, provisional={row['end_outs']}, "
                    f"official={official_outs}"
                )
            row["end_outs"] = 3
            row["event_outs"] = 3 - int(row["start_outs"])
            row["end_bases_code"] = 0

        # Re-evaluate the provisional base-state reconciliation after applying
        # the authoritative inning-ending outs. Do not remove any other flag.
        if row["end_bases_code"] == official_end_bases:
            flags = [flag for flag in flags if flag != "sequence_end_bases_mismatch"]
        elif "sequence_end_bases_mismatch" not in flags:
            flags.append("sequence_end_bases_mismatch")

        row["state_changed"] = bool(
            row["start_outs"] != row["end_outs"]
            or row["start_bases_code"] != row["end_bases_code"]
            or row["runs_scored"] != 0
        )
        row["quality_flags_json"] = json.dumps(
            sorted(set(flags)), separators=(",", ":")
        )
        rows.append(row)

    return pl.DataFrame(rows, schema=transitions.schema, strict=True).sort(
        ["game_pk", "inning", "half_inning", "at_bat_index", "transition_index"]
    )
