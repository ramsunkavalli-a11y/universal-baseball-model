#!/usr/bin/env python
"""Validate the Stats API state replay against independent Retrosheet plays.

Retrosheet's parsed seasonal play-by-play exposes explicit pre/post outs,
pre/post baserunners, runs, and PA flags. This audit compares those independent
state transitions with the accepted Stats API replay rather than validating one
Stats API representation against another.
"""

from __future__ import annotations

from collections import defaultdict
import csv
from io import TextIOWrapper
import json
from pathlib import Path
from typing import Any, Iterable, Mapping
from zipfile import ZipFile

import polars as pl

from universal_baseball.canonical_schema import CANONICAL_SCHEMA_VERSION
from universal_baseball.certification import download_file
from universal_baseball.official_capture import capture_official_json
from universal_baseball.provenance import NormalizationDefinition, make_source_snapshot_id
from universal_baseball.state_transitions_v2 import build_official_state_transitions_v2


RETROSHEET_URL = "https://www.retrosheet.org/downloads/plays/2025plays.zip"
SAMPLES = (
    {"game_pk": 777522, "retrosheet_gid": "LAN202506130", "date": "2025-06-13"},
    {"game_pk": 777506, "retrosheet_gid": "LAN202506140", "date": "2025-06-14"},
    {"game_pk": 777498, "retrosheet_gid": "LAN202506150", "date": "2025-06-15"},
)


def _int(value: Any, default: int = 0) -> int:
    if value is None or str(value).strip() == "":
        return default
    return int(float(str(value)))


def _occupied(row: Mapping[str, Any], suffix: str) -> int:
    code = 0
    for bit, base in ((1, "br1"), (2, "br2"), (4, "br3")):
        value = row.get(f"{base}_{suffix}")
        if value is not None and str(value).strip():
            code += bit
    return code


def _retrosheet_half(row: Mapping[str, Any]) -> str:
    return "top" if str(row.get("top_bot", "")).strip() == "0" else "bottom"


def _retrosheet_candidate(row: Mapping[str, Any]) -> bool:
    start_outs = _int(row.get("outs_pre"))
    end_outs = _int(row.get("outs_post"))
    start_bases = _occupied(row, "pre")
    end_bases = _occupied(row, "post")
    runs = _int(row.get("runs"))
    is_pa = _int(row.get("pa")) == 1
    return bool(
        is_pa
        or start_outs != end_outs
        or start_bases != end_bases
        or runs != 0
    )


def _retrosheet_state(row: Mapping[str, Any]) -> dict[str, Any]:
    half = _retrosheet_half(row)
    runs = _int(row.get("runs"))
    start_bat_score = _int(row.get("score_v")) if half == "top" else _int(row.get("score_h"))
    return {
        "inning": _int(row.get("inning")),
        "half_inning": half,
        "play_number": _int(row.get("pn")),
        "is_plate_appearance": _int(row.get("pa")) == 1,
        "start_outs": _int(row.get("outs_pre")),
        "end_outs": _int(row.get("outs_post")),
        "start_bases_code": _occupied(row, "pre"),
        "end_bases_code": _occupied(row, "post"),
        "runs_scored": runs,
        "start_bat_score": start_bat_score,
        "end_bat_score": start_bat_score + runs,
        "event": str(row.get("event") or ""),
    }


def _load_retrosheet_games(zip_path: Path, gids: set[str]) -> dict[str, list[dict[str, str]]]:
    rows: dict[str, list[dict[str, str]]] = {gid: [] for gid in gids}
    found_csv = False
    with ZipFile(zip_path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if not members:
            raise RuntimeError("Retrosheet season archive contains no CSV member")
        for member in members:
            with archive.open(member) as raw, TextIOWrapper(
                raw, encoding="utf-8-sig", errors="replace", newline=""
            ) as text:
                reader = csv.DictReader(text)
                if reader.fieldnames is None or "gid" not in reader.fieldnames:
                    continue
                found_csv = True
                for row in reader:
                    gid = str(row.get("gid") or "")
                    if gid in rows:
                        rows[gid].append(row)
    if not found_csv:
        raise RuntimeError("Retrosheet archive CSV has no gid column")
    missing = [gid for gid, game_rows in rows.items() if not game_rows]
    if missing:
        raise RuntimeError(f"Retrosheet archive missing target games: {missing}")
    return rows


def _official_transitions(game_pk: int) -> tuple[pl.DataFrame, str]:
    capture = capture_official_json(f"game/{game_pk}/playByPlay")
    if not isinstance(capture.data, Mapping):
        raise RuntimeError(f"official game {game_pk} playByPlay is not an object")
    snapshot_id = make_source_snapshot_id(
        source_name="mlb_stats_api",
        content_sha256=capture.content_sha256,
        upstream_version=capture.endpoint,
    )
    normalization = NormalizationDefinition.build(
        source_snapshot_id=snapshot_id,
        normalizer_name="build_official_state_transitions",
        normalizer_version="poc-v2",
        canonical_schema_version=CANONICAL_SCHEMA_VERSION,
    )
    frame = build_official_state_transitions_v2(
        game_pk,
        capture.data,
        source_snapshot_id=snapshot_id,
        normalization_id=normalization.normalization_id,
    ).filter(pl.col("re24_state_event_candidate"))
    return frame, capture.content_sha256


def _stats_state(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "inning": int(row["inning"]),
        "half_inning": str(row["half_inning"]),
        "at_bat_index": int(row["at_bat_index"]),
        "transition_index": int(row["transition_index"]),
        "is_plate_appearance": bool(row["is_plate_appearance_result"]),
        "start_outs": int(row["start_outs"]),
        "end_outs": int(row["end_outs"]),
        "start_bases_code": int(row["start_bases_code"]),
        "end_bases_code": int(row["end_bases_code"]),
        "runs_scored": int(row["runs_scored"]),
        "start_bat_score": int(row["start_bat_score"]),
        "end_bat_score": int(row["end_bat_score"]),
        "event_type": str(row["event_type"]),
    }


def _state_tuple(row: Mapping[str, Any]) -> tuple[int, int, int, int, int, int, int]:
    return (
        int(row["start_outs"]),
        int(row["end_outs"]),
        int(row["start_bases_code"]),
        int(row["end_bases_code"]),
        int(row["runs_scored"]),
        int(row["start_bat_score"]),
        int(row["end_bat_score"]),
    )


def _group_half(rows: Iterable[dict[str, Any]]) -> dict[tuple[int, str], list[dict[str, Any]]]:
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(int(row["inning"]), str(row["half_inning"]))].append(row)
    return grouped


def _compare_game(
    sample: Mapping[str, Any],
    retrosheet_rows: list[dict[str, str]],
) -> dict[str, Any]:
    stats_frame, stats_sha = _official_transitions(int(sample["game_pk"]))
    stats_rows = [_stats_state(row) for row in stats_frame.to_dicts()]
    retro_rows = [
        _retrosheet_state(row)
        for row in retrosheet_rows
        if _retrosheet_candidate(row)
    ]

    stats_halves = _group_half(stats_rows)
    retro_halves = _group_half(retro_rows)
    half_keys = sorted(set(stats_halves) | set(retro_halves))
    count_mismatch_halves: list[dict[str, Any]] = []
    state_mismatches: list[dict[str, Any]] = []
    shared_transition_count = 0

    for key in half_keys:
        left = stats_halves.get(key, [])
        right = retro_halves.get(key, [])
        if len(left) != len(right):
            count_mismatch_halves.append(
                {
                    "inning": key[0],
                    "half_inning": key[1],
                    "stats_transition_count": len(left),
                    "retrosheet_transition_count": len(right),
                }
            )
        for ordinal, (stats_row, retro_row) in enumerate(zip(left, right)):
            shared_transition_count += 1
            differences = {
                field: {
                    "stats_api": stats_row[field],
                    "retrosheet": retro_row[field],
                }
                for field in (
                    "is_plate_appearance",
                    "start_outs",
                    "end_outs",
                    "start_bases_code",
                    "end_bases_code",
                    "runs_scored",
                    "start_bat_score",
                    "end_bat_score",
                )
                if stats_row[field] != retro_row[field]
            }
            if differences:
                state_mismatches.append(
                    {
                        "inning": key[0],
                        "half_inning": key[1],
                        "ordinal_in_half": ordinal,
                        "differences": differences,
                        "stats_api": stats_row,
                        "retrosheet": retro_row,
                    }
                )

    stats_pa = sum(row["is_plate_appearance"] for row in stats_rows)
    retro_pa = sum(row["is_plate_appearance"] for row in retro_rows)
    stats_runs = sum(row["runs_scored"] for row in stats_rows)
    retro_runs = sum(row["runs_scored"] for row in retro_rows)
    return {
        **dict(sample),
        "stats_api_snapshot_sha256": stats_sha,
        "stats_transition_count": len(stats_rows),
        "retrosheet_transition_count": len(retro_rows),
        "shared_position_transition_count": shared_transition_count,
        "stats_plate_appearance_count": stats_pa,
        "retrosheet_plate_appearance_count": retro_pa,
        "stats_runs_scored": stats_runs,
        "retrosheet_runs_scored": retro_runs,
        "count_mismatch_half_count": len(count_mismatch_halves),
        "count_mismatch_halves": count_mismatch_halves,
        "state_mismatch_transition_count": len(state_mismatches),
        "state_mismatch_examples": state_mismatches[:30],
        "exact_ordered_state_match": (
            not count_mismatch_halves
            and not state_mismatches
            and len(stats_rows) == len(retro_rows)
        ),
    }


def main() -> int:
    work_dir = Path("data/quarantine/retrosheet-state-validation")
    report_dir = Path("reports/generated/retrosheet-state-validation")
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    zip_path = work_dir / "2025plays.zip"
    download_meta = download_file(RETROSHEET_URL, zip_path, timeout_seconds=240)
    target_gids = {str(sample["retrosheet_gid"]) for sample in SAMPLES}
    retrosheet = _load_retrosheet_games(zip_path, target_gids)

    reports = [
        _compare_game(sample, retrosheet[str(sample["retrosheet_gid"])])
        for sample in SAMPLES
    ]
    payload = {
        "report_schema_version": 1,
        "retrosheet_url": RETROSHEET_URL,
        "retrosheet_archive_sha256": download_meta["sha256"],
        "game_count": len(reports),
        "exact_match_game_count": sum(report["exact_ordered_state_match"] for report in reports),
        "total_stats_transitions": sum(report["stats_transition_count"] for report in reports),
        "total_retrosheet_transitions": sum(report["retrosheet_transition_count"] for report in reports),
        "total_state_mismatch_transitions": sum(report["state_mismatch_transition_count"] for report in reports),
        "total_count_mismatch_halves": sum(report["count_mismatch_half_count"] for report in reports),
        "games": reports,
        "comparison_fields": [
            "PA flag",
            "start/end outs",
            "start/end base occupancy",
            "runs on event",
            "batting-team score before/after event",
        ],
        "alignment": "within inning/half, ordered state-changing event / PA candidate",
    }
    (report_dir / "retrosheet_state_validation.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# Retrosheet external state validation",
        "",
        f"- Retrosheet archive SHA-256: `{download_meta['sha256']}`",
        f"- Games: {len(reports)}",
        f"- Exact ordered state-match games: {payload['exact_match_game_count']}/{len(reports)}",
        f"- Stats API replay candidate transitions: {payload['total_stats_transitions']:,}",
        f"- Retrosheet candidate plays: {payload['total_retrosheet_transitions']:,}",
        f"- Half-innings with transition-count mismatch: {payload['total_count_mismatch_halves']:,}",
        f"- Shared-position transitions with state mismatch: {payload['total_state_mismatch_transitions']:,}",
        "",
    ]
    for report in reports:
        lines.append(
            f"- `{report['retrosheet_gid']}` / MLB `{report['game_pk']}`: "
            f"transitions {report['stats_transition_count']}/{report['retrosheet_transition_count']}; "
            f"PA {report['stats_plate_appearance_count']}/{report['retrosheet_plate_appearance_count']}; "
            f"runs {report['stats_runs_scored']}/{report['retrosheet_runs_scored']}; "
            f"count-mismatch halves {report['count_mismatch_half_count']}; "
            f"state mismatches {report['state_mismatch_transition_count']}"
        )
    lines.extend(
        [
            "",
            "Retrosheet is an independent event-account source. A mismatch is evidence to investigate, not permission to alter either source silently. This gate intentionally compares state semantics rather than event-description strings or player IDs.",
            "",
            "Retrosheet attribution: The information used here was obtained free of charge from and is copyrighted by Retrosheet. Interested parties may contact Retrosheet at 20 Sunset Rd., Newark, DE 19711.",
            "",
        ]
    )
    summary = "\n".join(lines)
    (report_dir / "retrosheet_state_validation.md").write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
