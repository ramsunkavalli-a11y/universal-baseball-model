#!/usr/bin/env python
"""Exercise the Chadwick/baseballquery-style state-transition POC on MiLB games."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any, Mapping

import polars as pl

from universal_baseball.canonical_schema import CANONICAL_SCHEMA_VERSION
from universal_baseball.event_types import PLATE_APPEARANCE_EVENT_TYPES
from universal_baseball.official_capture import capture_official_json
from universal_baseball.provenance import NormalizationDefinition, make_source_snapshot_id
from universal_baseball.state_transitions import (
    build_official_state_transitions,
    transition_quality_flags,
)


SAMPLES = {
    "AAA": [779882, 780248, 781453],
    "ACL/DSL/FCL": [772320, 773530, 771821],
}


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _quality_counts(frame: pl.DataFrame) -> Counter[str]:
    counts: Counter[str] = Counter()
    for raw in frame.get_column("quality_flags_json").to_list():
        for flag in json.loads(raw):
            counts[str(flag)] += 1
    return counts


def _official_true_pa_count(payload: Mapping[str, Any]) -> int:
    plays = payload.get("allPlays") or []
    if not isinstance(plays, list):
        return 0
    return sum(
        1
        for raw in plays
        if _text(_mapping(raw).get("result", {}).get("eventType"))
        in PLATE_APPEARANCE_EVENT_TYPES
    )


def _official_final_total_runs(payload: Mapping[str, Any]) -> int:
    plays = payload.get("allPlays") or []
    if not isinstance(plays, list) or not plays:
        return 0
    for raw in reversed(plays):
        result = _mapping(_mapping(raw).get("result"))
        away = result.get("awayScore")
        home = result.get("homeScore")
        if away is not None and home is not None:
            return int(away) + int(home)
    return 0


def _continuity_breaks(frame: pl.DataFrame) -> list[dict[str, Any]]:
    breaks: list[dict[str, Any]] = []
    if frame.is_empty():
        return breaks
    for _, half in frame.group_by(["inning", "half_inning"], maintain_order=True):
        ordered = half.sort(["at_bat_index", "transition_index"])
        rows = ordered.to_dicts()
        for previous, current in zip(rows, rows[1:]):
            if (
                previous["end_outs"] != current["start_outs"]
                or previous["end_bases_code"] != current["start_bases_code"]
                or previous["end_bat_score"] != current["start_bat_score"]
            ):
                breaks.append(
                    {
                        "previous": {
                            "at_bat_index": previous["at_bat_index"],
                            "transition_index": previous["transition_index"],
                            "end_outs": previous["end_outs"],
                            "end_bases_code": previous["end_bases_code"],
                            "end_bat_score": previous["end_bat_score"],
                        },
                        "current": {
                            "at_bat_index": current["at_bat_index"],
                            "transition_index": current["transition_index"],
                            "start_outs": current["start_outs"],
                            "start_bases_code": current["start_bases_code"],
                            "start_bat_score": current["start_bat_score"],
                        },
                    }
                )
    return breaks


def _audit_game(group: str, game_id: int) -> tuple[dict[str, Any], pl.DataFrame]:
    capture = capture_official_json(f"game/{game_id}/playByPlay")
    if not isinstance(capture.data, Mapping):
        raise RuntimeError(f"game {game_id} official PBP is not an object")
    snapshot_id = make_source_snapshot_id(
        source_name="mlb_stats_api",
        content_sha256=capture.content_sha256,
        upstream_version=capture.endpoint,
    )
    normalization = NormalizationDefinition.build(
        source_snapshot_id=snapshot_id,
        normalizer_name="build_official_state_transitions",
        normalizer_version="poc-v1",
        canonical_schema_version=CANONICAL_SCHEMA_VERSION,
    )
    transitions = build_official_state_transitions(
        game_id,
        capture.data,
        source_snapshot_id=snapshot_id,
        normalization_id=normalization.normalization_id,
    )
    quality = transition_quality_flags(transitions)
    quality_counts = _quality_counts(quality) if not quality.is_empty() else Counter()
    continuity = _continuity_breaks(transitions)
    true_pa_official = _official_true_pa_count(capture.data)
    true_pa_terminal = transitions.filter(pl.col("is_plate_appearance_result")).height
    preterminal = transitions.filter(~pl.col("is_terminal_sequence_result"))
    total_transition_runs = int(transitions.get_column("runs_scored").sum())
    official_total_runs = _official_final_total_runs(capture.data)

    report = {
        "group": group,
        "game_pk": game_id,
        "source_snapshot_sha256": capture.content_sha256,
        "transition_count": transitions.height,
        "terminal_transition_count": transitions.filter(
            pl.col("is_terminal_sequence_result")
        ).height,
        "official_true_pa_count": true_pa_official,
        "true_pa_terminal_transition_count": true_pa_terminal,
        "preterminal_transition_count": preterminal.height,
        "re24_candidate_transition_count": transitions.filter(
            pl.col("re24_state_event_candidate")
        ).height,
        "quality_flag_transition_count": quality.height,
        "quality_flag_counts": dict(sorted(quality_counts.items())),
        "continuity_break_count": len(continuity),
        "continuity_break_examples": continuity[:10],
        "transition_runs_scored": total_transition_runs,
        "official_final_total_runs": official_total_runs,
        "run_total_difference": total_transition_runs - official_total_runs,
        "preterminal_event_type_counts": {
            str(row["event_type"]): int(row["len"])
            for row in (
                preterminal.group_by("event_type")
                .len()
                .sort(["len", "event_type"], descending=[True, False])
                .to_dicts()
            )
        },
    }
    return report, transitions


def main() -> int:
    report_dir = Path("reports/generated/state-transition-replay")
    report_dir.mkdir(parents=True, exist_ok=True)

    reports: list[dict[str, Any]] = []
    all_transitions: list[pl.DataFrame] = []
    for group, game_ids in SAMPLES.items():
        for game_id in game_ids:
            report, transitions = _audit_game(group, game_id)
            reports.append(report)
            all_transitions.append(transitions.with_columns(pl.lit(group).alias("audit_group")))

    combined = pl.concat(all_transitions, how="vertical_relaxed")
    quality = transition_quality_flags(combined)
    quality_counts = _quality_counts(quality) if not quality.is_empty() else Counter()
    total_true_pa = sum(report["official_true_pa_count"] for report in reports)
    total_true_pa_terminal = sum(
        report["true_pa_terminal_transition_count"] for report in reports
    )
    total_runs = sum(report["transition_runs_scored"] for report in reports)
    total_official_runs = sum(report["official_final_total_runs"] for report in reports)
    total_continuity_breaks = sum(report["continuity_break_count"] for report in reports)

    payload = {
        "report_schema_version": 1,
        "game_count": len(reports),
        "transition_count": combined.height,
        "official_true_pa_count": total_true_pa,
        "true_pa_terminal_transition_count": total_true_pa_terminal,
        "preterminal_transition_count": combined.filter(
            ~pl.col("is_terminal_sequence_result")
        ).height,
        "re24_candidate_transition_count": combined.filter(
            pl.col("re24_state_event_candidate")
        ).height,
        "quality_flag_transition_count": quality.height,
        "quality_flag_counts": dict(sorted(quality_counts.items())),
        "continuity_break_count": total_continuity_breaks,
        "transition_runs_scored": total_runs,
        "official_final_total_runs": total_official_runs,
        "run_total_difference": total_runs - total_official_runs,
        "games": reports,
        "quality_examples": quality.head(50).to_dicts(),
        "interpretation": (
            "The replay never resets reconstructed bases/scores to official sequence-end values. "
            "Therefore a bad movement can propagate into subsequent state and is detectable through "
            "explicit sequence-end reconciliation flags or continuity breaks."
        ),
    }
    (report_dir / "state_transition_replay.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# Official state-transition replay audit",
        "",
        f"- Games: {len(reports)}",
        f"- State transitions: {combined.height:,}",
        f"- Official true PAs: {total_true_pa:,}",
        f"- True-PA terminal transitions: {total_true_pa_terminal:,}",
        f"- Preterminal transitions: {payload['preterminal_transition_count']:,}",
        f"- RE24 state-event candidates: {payload['re24_candidate_transition_count']:,}",
        f"- Transitions with quality flags: {quality.height:,}",
        f"- Quality flags: `{dict(sorted(quality_counts.items()))}`",
        f"- Continuity breaks: {total_continuity_breaks:,}",
        f"- Replayed runs vs official final runs: {total_runs:,} vs {total_official_runs:,}",
        "",
    ]
    for report in reports:
        lines.append(
            f"- Game `{report['game_pk']}` ({report['group']}): "
            f"{report['transition_count']} transitions; "
            f"PAs {report['true_pa_terminal_transition_count']}/{report['official_true_pa_count']}; "
            f"quality {report['quality_flag_transition_count']}; "
            f"continuity breaks {report['continuity_break_count']}; "
            f"runs {report['transition_runs_scored']}/{report['official_final_total_runs']}"
        )
    lines.extend(
        [
            "",
            "This is a state-replay certification POC, not yet a production RE24 table. A clean result would justify freezing the canonical state-transition schema and then validating the same semantics against Chadwick/Retrosheet MLB events.",
            "",
        ]
    )
    summary = "\n".join(lines)
    (report_dir / "state_transition_replay.md").write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
