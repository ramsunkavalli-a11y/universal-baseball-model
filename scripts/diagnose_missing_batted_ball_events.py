#!/usr/bin/env python
"""Diagnose BIP evidence dropped by pitch-only reusable-source parsing.

This is a source-evaluation diagnostic, not production ingestion. It tests the
specific structural difference between armstjc's parser (which skips
``isPitch == false`` events) and baseballr's documented ``mlb_pbp()`` approach
(which flattens all ``playEvents``): whether the BIP-expected PAs missing from
our reusable pitch table carry their contact/hitData on non-pitch play events.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any, Mapping

import polars as pl

from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.official_capture import capture_official_json
from universal_baseball.performance_events import BIP_EXPECTED_EVENT_TYPES


BASE_URL = "https://github.com/armstjc/milb-data-repository/releases/download/pbp"
SAMPLES = {
    "2025_4_aaa_pbp.csv": [779882, 780248, 781453],
    "2024_6_rk_pbp.csv": [772320, 773530, 771821],
}


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _source_sequence_profile(source_game: pl.DataFrame, at_bat_index: int) -> dict[str, Any]:
    rows = source_game.filter(
        pl.col("at_bat_number").cast(pl.Int64, strict=False) == at_bat_index
    )
    if rows.is_empty():
        return {
            "source_pitch_row_count": 0,
            "source_type_x_count": 0,
            "source_bb_type_nonblank_count": 0,
            "source_bb_types": [],
            "source_type_values": [],
        }

    def values(column: str) -> list[str]:
        if column not in rows.columns:
            return []
        return sorted(
            {
                str(value).strip()
                for value in rows.get_column(column).to_list()
                if value is not None and str(value).strip()
            }
        )

    type_values = values("type")
    bb_types = values("bb_type")
    source_type_x_count = (
        rows.filter(pl.col("type").cast(pl.String, strict=False) == "X").height
        if "type" in rows.columns
        else 0
    )
    source_bb_type_nonblank_count = (
        rows.filter(
            pl.col("bb_type").cast(pl.String, strict=False).fill_null("").str.strip_chars() != ""
        ).height
        if "bb_type" in rows.columns
        else 0
    )
    return {
        "source_pitch_row_count": rows.unique().height,
        "source_type_x_count": source_type_x_count,
        "source_bb_type_nonblank_count": source_bb_type_nonblank_count,
        "source_bb_types": bb_types,
        "source_type_values": type_values,
    }


def _official_event_profile(play: Mapping[str, Any]) -> dict[str, Any]:
    events = play.get("playEvents") or []
    if not isinstance(events, list):
        events = []

    event_rows: list[dict[str, Any]] = []
    for raw in events:
        event = _mapping(raw)
        details = _mapping(event.get("details"))
        hit_data = _mapping(event.get("hitData"))
        coords = _mapping(hit_data.get("coordinates"))
        has_hit_data = bool(hit_data)
        is_in_play = details.get("isInPlay") is True
        has_contact_payload = is_in_play or has_hit_data
        event_rows.append(
            {
                "index": event.get("index"),
                "pitch_number": event.get("pitchNumber"),
                "is_pitch": event.get("isPitch") is True,
                "is_in_play": is_in_play,
                "has_hit_data": has_hit_data,
                "has_contact_payload": has_contact_payload,
                "details_code": _text(details.get("code")),
                "details_event": _text(details.get("event")),
                "details_event_type": _text(details.get("eventType")),
                "details_description": _text(details.get("description")),
                "trajectory": _text(hit_data.get("trajectory")),
                "location": _text(hit_data.get("location")),
                "coord_x": coords.get("coordX"),
                "coord_y": coords.get("coordY"),
            }
        )

    contact = [row for row in event_rows if row["has_contact_payload"]]
    pitch_contact = [row for row in contact if row["is_pitch"]]
    action_contact = [row for row in contact if not row["is_pitch"]]
    return {
        "official_play_event_count": len(event_rows),
        "official_pitch_event_count": sum(row["is_pitch"] for row in event_rows),
        "official_contact_event_count": len(contact),
        "official_pitch_contact_event_count": len(pitch_contact),
        "official_action_contact_event_count": len(action_contact),
        "official_contact_events": contact,
    }


def _classify_pattern(source: dict[str, Any], official: dict[str, Any]) -> str:
    source_has_bip = source["source_type_x_count"] > 0 or source["source_bb_type_nonblank_count"] > 0
    pitch_contact = official["official_pitch_contact_event_count"]
    action_contact = official["official_action_contact_event_count"]
    if source_has_bip:
        return "source_has_contact"
    if action_contact > 0 and pitch_contact == 0:
        return "missing_source_action_contact_only"
    if action_contact > 0 and pitch_contact > 0:
        return "missing_source_action_and_pitch_contact"
    if pitch_contact > 0:
        return "missing_source_pitch_contact_only"
    return "missing_source_no_official_contact_payload"


def main() -> int:
    work_dir = Path("data/quarantine/missing-batted-ball-diagnostic")
    report_dir = Path("reports/generated/missing-batted-ball-diagnostic")
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict[str, Any]] = []
    per_game: list[dict[str, Any]] = []

    for asset, game_ids in SAMPLES.items():
        path = work_dir / asset
        metadata = download_file(f"{BASE_URL}/{asset}", path, timeout_seconds=180)
        source = read_quarantined_csv(path)

        for game_id in game_ids:
            source_game = source.filter(
                pl.col("game_pk").cast(pl.Int64, strict=False) == game_id
            )
            capture = capture_official_json(f"game/{game_id}/playByPlay")
            if not isinstance(capture.data, Mapping):
                raise RuntimeError(f"official game {game_id} PBP is not a JSON object")
            plays = capture.data.get("allPlays") or []
            if not isinstance(plays, list):
                raise RuntimeError(f"official game {game_id} allPlays is not a list")

            game_rows: list[dict[str, Any]] = []
            for raw_play in plays:
                play = _mapping(raw_play)
                result = _mapping(play.get("result"))
                event_type = _text(result.get("eventType"))
                if event_type not in BIP_EXPECTED_EVENT_TYPES:
                    continue
                try:
                    at_bat_index = int(play["atBatIndex"])
                except (KeyError, TypeError, ValueError):
                    continue

                source_profile = _source_sequence_profile(source_game, at_bat_index)
                official_profile = _official_event_profile(play)
                pattern = _classify_pattern(source_profile, official_profile)
                row = {
                    "asset": asset,
                    "asset_sha256": metadata["sha256"],
                    "game_pk": game_id,
                    "at_bat_index": at_bat_index,
                    "official_event_type": event_type,
                    "official_result_event": _text(result.get("event")),
                    "pattern": pattern,
                    **source_profile,
                    **official_profile,
                }
                all_rows.append(row)
                game_rows.append(row)

            game_counts = Counter(row["pattern"] for row in game_rows)
            per_game.append(
                {
                    "asset": asset,
                    "game_pk": game_id,
                    "bip_expected_pa_count": len(game_rows),
                    "pattern_counts": dict(sorted(game_counts.items())),
                }
            )

    pattern_counts = Counter(row["pattern"] for row in all_rows)
    missing_rows = [row for row in all_rows if row["pattern"] != "source_has_contact"]
    missing_pattern_counts = Counter(row["pattern"] for row in missing_rows)
    missing_event_type_counts = Counter(row["official_event_type"] for row in missing_rows)

    action_recovery_count = sum(
        1
        for row in missing_rows
        if row["official_action_contact_event_count"] > 0
    )
    any_official_recovery_count = sum(
        1
        for row in missing_rows
        if row["official_contact_event_count"] > 0
    )
    action_with_trajectory_count = sum(
        1
        for row in missing_rows
        if any(
            event.get("trajectory") is not None
            for event in row["official_contact_events"]
            if not event["is_pitch"]
        )
    )
    action_with_coordinates_count = sum(
        1
        for row in missing_rows
        if any(
            event.get("coord_x") is not None and event.get("coord_y") is not None
            for event in row["official_contact_events"]
            if not event["is_pitch"]
        )
    )

    payload = {
        "report_schema_version": 1,
        "sample_game_count": len(per_game),
        "bip_expected_pa_count": len(all_rows),
        "pattern_counts": dict(sorted(pattern_counts.items())),
        "source_missing_bip_pa_count": len(missing_rows),
        "source_missing_pattern_counts": dict(sorted(missing_pattern_counts.items())),
        "source_missing_event_type_counts": dict(sorted(missing_event_type_counts.items())),
        "missing_pa_with_any_official_contact_payload_count": any_official_recovery_count,
        "missing_pa_with_non_pitch_contact_payload_count": action_recovery_count,
        "missing_pa_with_non_pitch_trajectory_count": action_with_trajectory_count,
        "missing_pa_with_non_pitch_coordinates_count": action_with_coordinates_count,
        "missing_pa_any_official_contact_recovery_rate": (
            any_official_recovery_count / len(missing_rows) if missing_rows else None
        ),
        "missing_pa_non_pitch_contact_recovery_rate": (
            action_recovery_count / len(missing_rows) if missing_rows else None
        ),
        "per_game": per_game,
        "missing_examples": missing_rows[:30],
        "interpretation": (
            "If missing PAs overwhelmingly carry contact payloads on isPitch=false "
            "playEvents, an all-playEvents parser such as baseballr's mlb_pbp() "
            "preserves the needed evidence while armstjc's pitch-only export cannot."
        ),
    }

    (report_dir / "missing_batted_ball_events.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    lines = [
        "# Missing batted-ball event diagnostic",
        "",
        f"- Sample games: {len(per_game)}",
        f"- BIP-expected official PAs: {len(all_rows):,}",
        f"- PAs with no reusable-source contact evidence: {len(missing_rows):,}",
        f"- Missing PAs with any official contact payload: {any_official_recovery_count:,}",
        f"- Missing PAs with non-pitch contact payload: {action_recovery_count:,}",
        f"- Missing PAs with non-pitch trajectory: {action_with_trajectory_count:,}",
        f"- Missing PAs with non-pitch coordinates: {action_with_coordinates_count:,}",
        f"- Missing pattern counts: `{dict(sorted(missing_pattern_counts.items()))}`",
        f"- Missing official event types: `{dict(sorted(missing_event_type_counts.items()))}`",
        "",
    ]
    for game in per_game:
        lines.append(
            f"- `{game['game_pk']}` ({game['asset']}): {game['bip_expected_pa_count']} BIP-expected PAs; "
            f"patterns `{game['pattern_counts']}`"
        )
    lines.extend(
        [
            "",
            "This report deliberately does not promote a new production parser. It only tests whether preserving all Stats API playEvents—rather than only physical pitches—closes the observed contact-evidence gap.",
            "",
        ]
    )
    summary = "\n".join(lines)
    (report_dir / "missing_batted_ball_events.md").write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
