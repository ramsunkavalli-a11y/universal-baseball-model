#!/usr/bin/env python
"""Audit reusable-source base/out/score semantics and within-PA runner events.

This is intentionally a certification diagnostic, not a production state parser.
It answers two questions before RE24 work begins:

1. What do armstjc's repeated pitch-row state columns actually correspond to in
   the official Stats API feed?
2. How often does an official true PA contain runner movements before the
   terminal playEvent, making a naive PA-start -> PA-end transition contextual?

The second test follows the key decomposition precedent in baseballquery:
runner movements whose ``details.playIndex`` precedes the terminal playEvent are
separate state transitions rather than part of the terminal batter result.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any, Mapping

import polars as pl

from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.event_types import PLATE_APPEARANCE_EVENT_TYPES
from universal_baseball.official_capture import capture_official_json


BASE_URL = "https://github.com/armstjc/milb-data-repository/releases/download/pbp"
SAMPLES = {
    "2025_4_aaa_pbp.csv": [779882, 780248, 781453],
    "2024_6_rk_pbp.csv": [772320, 773530, 771821],
}


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


def _official_post_bases(play: Mapping[str, Any]) -> tuple[int | None, int | None, int | None]:
    matchup = _mapping(play.get("matchup"))
    return tuple(
        _int(_mapping(matchup.get(field)).get("id"))
        for field in ("postOnFirst", "postOnSecond", "postOnThird")
    )


def _source_consensus_int(rows: pl.DataFrame, column: str) -> tuple[int | None, bool]:
    if column not in rows.columns:
        return None, True
    values = sorted(
        {
            value
            for value in (_int(raw) for raw in rows.get_column(column).to_list())
            if value is not None
        }
    )
    if len(values) > 1:
        return None, False
    return (values[0] if values else None), True


def _source_sequence_state(rows: pl.DataFrame) -> dict[str, Any]:
    fields = (
        "on_1b",
        "on_2b",
        "on_3b",
        "bat_score",
        "fld_score",
        "post_bat_score",
        "post_fld_score",
    )
    result: dict[str, Any] = {"source_pitch_row_count": rows.unique().height}
    conflicts: list[str] = []
    for field in fields:
        value, clean = _source_consensus_int(rows, field)
        result[field] = value
        if not clean:
            conflicts.append(field)
    result["source_state_conflict_fields"] = conflicts
    return result


def _batting_scores(
    half_inning: str | None,
    *,
    away_score: int,
    home_score: int,
) -> tuple[int, int]:
    if (half_inning or "").lower() == "top":
        return away_score, home_score
    if (half_inning or "").lower() == "bottom":
        return home_score, away_score
    raise ValueError(f"unhandled half inning {half_inning!r}")


def _physical_pitch_out_map(play: Mapping[str, Any]) -> dict[int, int | None]:
    result: dict[int, int | None] = {}
    events = play.get("playEvents") or []
    if not isinstance(events, list):
        return result
    for raw_event in events:
        event = _mapping(raw_event)
        if event.get("isPitch") is not True:
            continue
        pitch_number = _int(event.get("pitchNumber"))
        if pitch_number is None:
            continue
        result[pitch_number] = _int(_mapping(event.get("count")).get("outs"))
    return result


def _preterminal_runner_movements(play: Mapping[str, Any]) -> list[dict[str, Any]]:
    events = play.get("playEvents") or []
    runners = play.get("runners") or []
    if not isinstance(events, list) or not isinstance(runners, list) or not events:
        return []
    terminal_index = len(events) - 1
    movements: list[dict[str, Any]] = []
    for raw_runner in runners:
        runner = _mapping(raw_runner)
        details = _mapping(runner.get("details"))
        play_index = _int(details.get("playIndex"))
        if play_index is None or play_index >= terminal_index:
            continue
        movement = _mapping(runner.get("movement"))
        movements.append(
            {
                "play_index": play_index,
                "event_type": _text(details.get("eventType")) or "<blank>",
                "event": _text(details.get("event")),
                "movement_reason": _text(details.get("movementReason")),
                "is_out": details.get("isOut") is True,
                "start": _text(movement.get("start")),
                "end": _text(movement.get("end")),
                "out_base": _text(movement.get("outBase")),
            }
        )
    return movements


def _compare_pitch_outs(
    source_rows: pl.DataFrame,
    play: Mapping[str, Any],
) -> tuple[int, int, list[dict[str, Any]]]:
    official = _physical_pitch_out_map(play)
    if "pitch_number" not in source_rows.columns or "outs_when_up" not in source_rows.columns:
        return 0, 0, []
    source_unique = source_rows.select(["pitch_number", "outs_when_up"]).unique()
    shared = 0
    mismatches: list[dict[str, Any]] = []
    for row in source_unique.to_dicts():
        pitch_number = _int(row.get("pitch_number"))
        if pitch_number is None or pitch_number not in official:
            continue
        shared += 1
        source_outs = _int(row.get("outs_when_up"))
        official_outs = official[pitch_number]
        if source_outs != official_outs:
            mismatches.append(
                {
                    "pitch_number": pitch_number,
                    "source_outs_when_up": source_outs,
                    "official_play_event_count_outs": official_outs,
                }
            )
    return shared, len(mismatches), mismatches


def _audit_game(asset: str, source: pl.DataFrame, game_id: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source_game = source.filter(pl.col("game_pk").cast(pl.Int64, strict=False) == game_id)
    capture = capture_official_json(f"game/{game_id}/playByPlay")
    if not isinstance(capture.data, Mapping):
        raise RuntimeError(f"official game {game_id} playByPlay is not an object")
    all_plays = capture.data.get("allPlays") or []
    if not isinstance(all_plays, list):
        raise RuntimeError(f"official game {game_id} allPlays is not a list")

    previous_away_score = 0
    previous_home_score = 0
    sequence_rows: list[dict[str, Any]] = []
    base_matches = 0
    base_compared = 0
    score_matches = 0
    score_compared = 0
    pitch_out_shared = 0
    pitch_out_mismatches = 0
    zero_pitch_true_pa_count = 0
    true_pa_count = 0
    preterminal_pa_count = 0
    preterminal_movement_count = 0
    preterminal_event_types: Counter[str] = Counter()
    source_state_conflict_count = 0

    for raw_play in all_plays:
        play = _mapping(raw_play)
        at_bat_index = _int(play.get("atBatIndex"))
        if at_bat_index is None:
            continue
        result = _mapping(play.get("result"))
        event_type = _text(result.get("eventType"))
        about = _mapping(play.get("about"))
        half_inning = _text(about.get("halfInning"))

        post_away_score = _int(result.get("awayScore"))
        post_home_score = _int(result.get("homeScore"))
        if post_away_score is None:
            post_away_score = previous_away_score
        if post_home_score is None:
            post_home_score = previous_home_score

        pre_bat, pre_fld = _batting_scores(
            half_inning,
            away_score=previous_away_score,
            home_score=previous_home_score,
        )
        post_bat, post_fld = _batting_scores(
            half_inning,
            away_score=post_away_score,
            home_score=post_home_score,
        )

        source_rows = source_game.filter(
            pl.col("at_bat_number").cast(pl.Int64, strict=False) == at_bat_index
        )
        source_state = _source_sequence_state(source_rows) if not source_rows.is_empty() else {
            "source_pitch_row_count": 0,
            "source_state_conflict_fields": [],
            "on_1b": None,
            "on_2b": None,
            "on_3b": None,
            "bat_score": None,
            "fld_score": None,
            "post_bat_score": None,
            "post_fld_score": None,
        }
        if source_state["source_state_conflict_fields"]:
            source_state_conflict_count += 1

        official_post_bases = _official_post_bases(play)
        if not source_rows.is_empty():
            source_bases = (
                source_state["on_1b"],
                source_state["on_2b"],
                source_state["on_3b"],
            )
            base_compared += 1
            if source_bases == official_post_bases:
                base_matches += 1

            source_scores = (
                source_state["bat_score"],
                source_state["fld_score"],
                source_state["post_bat_score"],
                source_state["post_fld_score"],
            )
            official_scores = (pre_bat, pre_fld, post_bat, post_fld)
            score_compared += 1
            if source_scores == official_scores:
                score_matches += 1

            shared, mismatches, mismatch_examples = _compare_pitch_outs(source_rows, play)
            pitch_out_shared += shared
            pitch_out_mismatches += mismatches
        else:
            mismatch_examples = []
            source_bases = (None, None, None)
            source_scores = (None, None, None, None)
            official_scores = (pre_bat, pre_fld, post_bat, post_fld)

        movements = _preterminal_runner_movements(play)
        is_true_pa = event_type in PLATE_APPEARANCE_EVENT_TYPES
        physical_pitch_count = sum(
            1
            for raw_event in (play.get("playEvents") or [])
            if _mapping(raw_event).get("isPitch") is True
        )
        if is_true_pa:
            true_pa_count += 1
            if physical_pitch_count == 0:
                zero_pitch_true_pa_count += 1
            if movements:
                preterminal_pa_count += 1
                preterminal_movement_count += len(movements)
                preterminal_event_types.update(
                    movement["event_type"] for movement in movements
                )

        if (
            movements
            or (not source_rows.is_empty() and source_bases != official_post_bases)
            or (not source_rows.is_empty() and source_scores != official_scores)
            or mismatch_examples
            or (is_true_pa and source_rows.is_empty())
        ):
            sequence_rows.append(
                {
                    "asset": asset,
                    "game_pk": game_id,
                    "at_bat_index": at_bat_index,
                    "official_event_type": event_type,
                    "is_true_pa": is_true_pa,
                    "physical_pitch_count": physical_pitch_count,
                    "source_pitch_row_count": source_state["source_pitch_row_count"],
                    "source_post_bases": list(source_bases),
                    "official_matchup_post_bases": list(official_post_bases),
                    "source_scores": list(source_scores),
                    "official_pre_post_scores": list(official_scores),
                    "preterminal_runner_movements": movements,
                    "pitch_out_mismatch_examples": mismatch_examples,
                    "source_state_conflict_fields": source_state["source_state_conflict_fields"],
                }
            )

        previous_away_score = post_away_score
        previous_home_score = post_home_score

    report = {
        "asset": asset,
        "game_pk": game_id,
        "true_pa_count": true_pa_count,
        "zero_pitch_true_pa_count": zero_pitch_true_pa_count,
        "source_sequence_state_compared_count": base_compared,
        "source_post_bases_match_official_count": base_matches,
        "source_post_bases_match_rate": base_matches / base_compared if base_compared else None,
        "source_score_state_compared_count": score_compared,
        "source_pre_post_scores_match_official_count": score_matches,
        "source_pre_post_scores_match_rate": score_matches / score_compared if score_compared else None,
        "shared_source_official_pitch_out_count": pitch_out_shared,
        "source_outs_when_up_vs_official_event_count_mismatch_count": pitch_out_mismatches,
        "true_pa_with_preterminal_runner_movement_count": preterminal_pa_count,
        "true_pa_with_preterminal_runner_movement_rate": preterminal_pa_count / true_pa_count if true_pa_count else None,
        "preterminal_runner_movement_count": preterminal_movement_count,
        "preterminal_runner_event_type_counts": dict(sorted(preterminal_event_types.items())),
        "source_state_conflict_sequence_count": source_state_conflict_count,
    }
    return report, sequence_rows


def main() -> int:
    work_dir = Path("data/quarantine/state-semantics-audit")
    report_dir = Path("reports/generated/state-semantics-audit")
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    game_reports: list[dict[str, Any]] = []
    diagnostic_sequences: list[dict[str, Any]] = []
    asset_hashes: dict[str, str] = {}

    for asset, game_ids in SAMPLES.items():
        path = work_dir / asset
        metadata = download_file(f"{BASE_URL}/{asset}", path, timeout_seconds=180)
        asset_hashes[asset] = str(metadata["sha256"])
        source = read_quarantined_csv(path)
        for game_id in game_ids:
            report, sequences = _audit_game(asset, source, game_id)
            game_reports.append(report)
            diagnostic_sequences.extend(sequences)

    totals = {
        "true_pa_count": sum(row["true_pa_count"] for row in game_reports),
        "zero_pitch_true_pa_count": sum(row["zero_pitch_true_pa_count"] for row in game_reports),
        "base_compared": sum(row["source_sequence_state_compared_count"] for row in game_reports),
        "base_matches": sum(row["source_post_bases_match_official_count"] for row in game_reports),
        "score_compared": sum(row["source_score_state_compared_count"] for row in game_reports),
        "score_matches": sum(row["source_pre_post_scores_match_official_count"] for row in game_reports),
        "pitch_out_shared": sum(row["shared_source_official_pitch_out_count"] for row in game_reports),
        "pitch_out_mismatches": sum(row["source_outs_when_up_vs_official_event_count_mismatch_count"] for row in game_reports),
        "preterminal_pa_count": sum(row["true_pa_with_preterminal_runner_movement_count"] for row in game_reports),
        "preterminal_movement_count": sum(row["preterminal_runner_movement_count"] for row in game_reports),
    }
    movement_types: Counter[str] = Counter()
    for row in game_reports:
        movement_types.update(row["preterminal_runner_event_type_counts"])

    payload = {
        "report_schema_version": 1,
        "asset_sha256": asset_hashes,
        "game_count": len(game_reports),
        "true_pa_count": totals["true_pa_count"],
        "zero_pitch_true_pa_count": totals["zero_pitch_true_pa_count"],
        "source_post_bases_compared_count": totals["base_compared"],
        "source_post_bases_match_official_count": totals["base_matches"],
        "source_post_bases_match_rate": totals["base_matches"] / totals["base_compared"] if totals["base_compared"] else None,
        "source_pre_post_scores_compared_count": totals["score_compared"],
        "source_pre_post_scores_match_official_count": totals["score_matches"],
        "source_pre_post_scores_match_rate": totals["score_matches"] / totals["score_compared"] if totals["score_compared"] else None,
        "shared_source_official_pitch_out_count": totals["pitch_out_shared"],
        "source_outs_when_up_vs_official_event_count_mismatch_count": totals["pitch_out_mismatches"],
        "true_pa_with_preterminal_runner_movement_count": totals["preterminal_pa_count"],
        "true_pa_with_preterminal_runner_movement_rate": totals["preterminal_pa_count"] / totals["true_pa_count"] if totals["true_pa_count"] else None,
        "preterminal_runner_movement_count": totals["preterminal_movement_count"],
        "preterminal_runner_event_type_counts": dict(sorted(movement_types.items())),
        "games": game_reports,
        "diagnostic_sequence_examples": diagnostic_sequences[:80],
        "interpretation": {
            "on_base_fields": "Expected to match official matchup.postOn*; they are post-sequence state, not PA/pitch-start state.",
            "outs_when_up": "Compared directly with official physical playEvent count.outs. Matching proves exported event-count semantics, not that the field is PA-start outs.",
            "score_fields": "bat_score/fld_score are compared with tracked official pre-sequence score; post_* with official result score.",
            "preterminal_runner_movements": "Lower-bound count of runner movements baseballquery-style decomposition would separate before the terminal PA result.",
        },
    }

    (report_dir / "state_semantics_audit.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# State semantics audit",
        "",
        f"- Games: {len(game_reports)}",
        f"- Official true PAs: {totals['true_pa_count']:,}",
        f"- Zero-pitch true PAs: {totals['zero_pitch_true_pa_count']:,}",
        f"- Source `on_*` sequences matching official `matchup.postOn*`: {totals['base_matches']:,}/{totals['base_compared']:,} "
        f"({totals['base_matches'] / totals['base_compared']:.2%})",
        f"- Source pre/post score tuples matching official tracked scores: {totals['score_matches']:,}/{totals['score_compared']:,} "
        f"({totals['score_matches'] / totals['score_compared']:.2%})",
        f"- Shared physical pitches for outs comparison: {totals['pitch_out_shared']:,}",
        f"- `outs_when_up` vs official physical-event `count.outs` mismatches: {totals['pitch_out_mismatches']:,}",
        f"- True PAs with a runner movement before terminal playEvent: {totals['preterminal_pa_count']:,}/{totals['true_pa_count']:,} "
        f"({totals['preterminal_pa_count'] / totals['true_pa_count']:.2%})",
        f"- Preterminal runner movement records: {totals['preterminal_movement_count']:,}",
        f"- Movement event types: `{dict(sorted(movement_types.items()))}`",
        "",
    ]
    for row in game_reports:
        lines.append(
            f"- Game `{row['game_pk']}` ({row['asset']}): "
            f"post bases {row['source_post_bases_match_official_count']}/{row['source_sequence_state_compared_count']}; "
            f"scores {row['source_pre_post_scores_match_official_count']}/{row['source_score_state_compared_count']}; "
            f"preterminal-runner PAs {row['true_pa_with_preterminal_runner_movement_count']}/{row['true_pa_count']}"
        )
    lines.extend(
        [
            "",
            "The audit does not promote a state parser. It establishes source-field semantics and quantifies the runner-event decomposition problem before a Chadwick/baseballquery-style transition POC is written.",
            "",
        ]
    )
    summary = "\n".join(lines)
    (report_dir / "state_semantics_audit.md").write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
