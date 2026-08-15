#!/usr/bin/env python
"""Audit SportsDataverse against known edge-case MiLB games.

This is a source-selection experiment, not a production dependency. It asks
whether SportsDataverse can read official MLB Stats API PBP where the stricter
`python-mlb-statsapi` typed model fails, and inspects zero-pitch PAs that a
pitch-grain historical table cannot represent.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sportsdataverse.mlb import mlb_play_by_play


GAME_IDS = [779653, 780856]
OUTPUT_DIR = Path("reports/generated/armstjc")


def _summarize_play(play: dict[str, Any]) -> dict[str, Any]:
    result = play.get("result") or {}
    events = play.get("playEvents") or []
    pitch_events = [event for event in events if event.get("isPitch") is True]
    return {
        "at_bat_index": play.get("atBatIndex"),
        "event": result.get("event"),
        "event_type": result.get("eventType"),
        "description": result.get("description"),
        "play_event_count": len(events),
        "pitch_event_count": len(pitch_events),
        "play_events": [
            {
                "index": event.get("index"),
                "is_pitch": event.get("isPitch"),
                "pitch_number": event.get("pitchNumber"),
                "details_code": (event.get("details") or {}).get("code"),
                "details_event_type": (event.get("details") or {}).get("eventType"),
                "details_description": (event.get("details") or {}).get("description"),
                "pitch_type": (event.get("details") or {}).get("type"),
                "has_pitch_data": event.get("pitchData") is not None,
            }
            for event in events
        ],
    }


def audit_game(game_id: int) -> dict[str, Any]:
    parsed = mlb_play_by_play(game_pk=game_id)
    raw = mlb_play_by_play(game_pk=game_id, return_parsed=False)
    plays = raw.get("allPlays") or []

    zero_pitch_pas = []
    unknown_pitch_types = []
    for play in plays:
        summary = _summarize_play(play)
        if summary["pitch_event_count"] == 0:
            zero_pitch_pas.append(summary)

        for event in play.get("playEvents") or []:
            pitch_type = (event.get("details") or {}).get("type")
            if isinstance(pitch_type, dict) and pitch_type.get("code") is None:
                unknown_pitch_types.append(
                    {
                        "at_bat_index": play.get("atBatIndex"),
                        "event_index": event.get("index"),
                        "is_pitch": event.get("isPitch"),
                        "pitch_number": event.get("pitchNumber"),
                        "pitch_type": pitch_type,
                        "details_description": (event.get("details") or {}).get(
                            "description"
                        ),
                    }
                )

    result_columns = [
        column
        for column in parsed.columns
        if "result" in column.lower() or "event" in column.lower()
    ]
    return {
        "game_pk": game_id,
        "sportsdataverse_parsed_rows": int(parsed.height),
        "sportsdataverse_parsed_columns": int(parsed.width),
        "result_or_event_columns": result_columns,
        "raw_all_plays": len(plays),
        "zero_pitch_pa_count": len(zero_pitch_pas),
        "zero_pitch_pas": zero_pitch_pas,
        "pitch_type_without_code_count": len(unknown_pitch_types),
        "pitch_type_without_code_examples": unknown_pitch_types[:20],
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report = {"games": []}
    for game_id in GAME_IDS:
        try:
            report["games"].append({"status": "success", **audit_game(game_id)})
        except Exception as exc:
            report["games"].append(
                {
                    "game_pk": game_id,
                    "status": "failure",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )

    json_path = OUTPUT_DIR / "sportsdataverse_official_client_audit.json"
    md_path = OUTPUT_DIR / "sportsdataverse_official_client_audit.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    lines = ["# SportsDataverse official-client audit", ""]
    for game in report["games"]:
        lines.append(f"## Game {game['game_pk']}")
        lines.append("")
        lines.append(f"- Status: {game['status']}")
        if game["status"] == "success":
            lines.append(f"- Parsed PAs: {game['sportsdataverse_parsed_rows']}")
            lines.append(f"- Raw PAs: {game['raw_all_plays']}")
            lines.append(f"- Zero-pitch PAs: {game['zero_pitch_pa_count']}")
            lines.append(
                "- Pitch-type objects missing code: "
                f"{game['pitch_type_without_code_count']}"
            )
            for pa in game["zero_pitch_pas"]:
                lines.append(
                    "- Zero-pitch PA: "
                    f"atBatIndex={pa['at_bat_index']}, "
                    f"event_type={pa['event_type']}, description={pa['description']}"
                )
        else:
            lines.append(f"- Error: {game['error_type']}: {game['error']}")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
