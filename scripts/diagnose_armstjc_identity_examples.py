#!/usr/bin/env python
"""Inspect exact reusable-source identity mismatches against raw official PBP."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from mlbstatsapi import MlbDataAdapter
import polars as pl

from universal_baseball.certification import download_file, read_quarantined_csv


SOURCE_COLUMNS = (
    "game_pk",
    "game_date",
    "at_bat_number",
    "pitch_number",
    "batter",
    "pitcher",
    "stand",
    "p_throws",
    "description",
    "type",
    "play_start_datetime",
    "play_end_datetime",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--asset-name", required=True)
    parser.add_argument(
        "--key",
        action="append",
        required=True,
        help="game_pk:at_bat_number; may be repeated",
    )
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    return parser.parse_args()


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _parse_keys(values: list[str]) -> list[tuple[int, int]]:
    keys: list[tuple[int, int]] = []
    for value in values:
        game_text, separator, at_bat_text = value.partition(":")
        if not separator:
            raise ValueError(f"key must be game_pk:at_bat_number, got {value!r}")
        keys.append((int(game_text), int(at_bat_text)))
    return keys


def _project_play_event(event_value: Any) -> dict[str, Any]:
    event = _mapping(event_value)
    details = _mapping(event.get("details"))
    player = _mapping(event.get("player"))
    position = _mapping(event.get("position"))
    pitch_type = _mapping(details.get("type"))
    return {
        "index": event.get("index"),
        "isPitch": event.get("isPitch"),
        "pitchNumber": event.get("pitchNumber"),
        "startTime": event.get("startTime"),
        "endTime": event.get("endTime"),
        "details_code": details.get("code"),
        "details_event": details.get("event"),
        "details_eventType": details.get("eventType"),
        "details_description": details.get("description"),
        "pitch_type_code": pitch_type.get("code"),
        "player_id": player.get("id"),
        "player_name": player.get("fullName"),
        "position_code": position.get("code"),
        "position_name": position.get("name"),
    }


def _project_official_play(play_value: Any) -> dict[str, Any]:
    play = _mapping(play_value)
    result = _mapping(play.get("result"))
    matchup = _mapping(play.get("matchup"))
    batter = _mapping(matchup.get("batter"))
    pitcher = _mapping(matchup.get("pitcher"))
    bat_side = _mapping(matchup.get("batSide"))
    pitch_hand = _mapping(matchup.get("pitchHand"))
    about = _mapping(play.get("about"))
    return {
        "atBatIndex": play.get("atBatIndex"),
        "result": {
            "type": result.get("type"),
            "event": result.get("event"),
            "eventType": result.get("eventType"),
            "description": result.get("description"),
        },
        "matchup": {
            "batter_id": batter.get("id"),
            "batter_name": batter.get("fullName"),
            "pitcher_id": pitcher.get("id"),
            "pitcher_name": pitcher.get("fullName"),
            "bat_side": bat_side.get("code"),
            "pitch_hand": pitch_hand.get("code"),
        },
        "about": {
            "inning": about.get("inning"),
            "halfInning": about.get("halfInning"),
            "startTime": about.get("startTime"),
            "endTime": about.get("endTime"),
        },
        "playEvents": [
            _project_play_event(event)
            for event in (play.get("playEvents") or [])
        ],
    }


def _fetch_raw_play(adapter: MlbDataAdapter, game_id: int, at_bat: int) -> dict[str, Any]:
    response = adapter.get(f"game/{game_id}/playByPlay")
    payload = response.data or {}
    for play in payload.get("allPlays") or []:
        play_mapping = _mapping(play)
        if play_mapping.get("atBatIndex") == at_bat:
            return _project_official_play(play_mapping)
    raise KeyError(f"official allPlays missing game {game_id} atBatIndex {at_bat}")


def _source_rows(frame: pl.DataFrame, game_id: int, at_bat: int) -> list[dict[str, Any]]:
    available = [column for column in SOURCE_COLUMNS if column in frame.columns]
    return (
        frame.filter(
            (pl.col("game_pk").cast(pl.String) == str(game_id))
            & (pl.col("at_bat_number").cast(pl.String) == str(at_bat))
        )
        .select(available)
        .unique()
        .sort("pitch_number")
        .to_dicts()
    )


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Reusable-source identity mismatch diagnostic",
        "",
        f"- Source asset: `{payload['source_asset']}`",
        f"- Source SHA-256: `{payload['source_sha256']}`",
        "",
    ]
    for item in payload["examples"]:
        key = item["key"]
        official = item["official"]
        lines.extend(
            [
                f"## Game {key['game_pk']} / atBatIndex {key['at_bat_number']}",
                "",
                f"- Official result: `{official['result']['eventType']}` — "
                f"{official['result']['description']}",
                f"- Official batter: `{official['matchup']['batter_id']}` "
                f"{official['matchup']['batter_name']}",
                f"- Official pitcher: `{official['matchup']['pitcher_id']}` "
                f"{official['matchup']['pitcher_name']}",
                "",
                "### Distinct source rows",
                "",
                "```json",
                json.dumps(item["source_rows"], indent=2, sort_keys=True),
                "```",
                "",
                "### Official play events",
                "",
                "```json",
                json.dumps(official["playEvents"], indent=2, sort_keys=True),
                "```",
                "",
            ]
        )
    lines.append(
        "This report is diagnostic evidence only. It does not select a winning identity or alter source data."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    keys = _parse_keys(args.key)
    source_path = args.work_dir / args.asset_name
    metadata = download_file(args.url, source_path)
    frame = read_quarantined_csv(source_path)

    examples: list[dict[str, Any]] = []
    adapter = MlbDataAdapter(ver="v1")
    try:
        for game_id, at_bat in keys:
            examples.append(
                {
                    "key": {"game_pk": game_id, "at_bat_number": at_bat},
                    "source_rows": _source_rows(frame, game_id, at_bat),
                    "official": _fetch_raw_play(adapter, game_id, at_bat),
                }
            )
    finally:
        adapter.close()

    payload = {
        "report_schema_version": 1,
        "source_asset": args.asset_name,
        "source_sha256": metadata["sha256"],
        "retrieved_at_utc": metadata["retrieved_at_utc"],
        "examples": examples,
    }
    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / "source_identity_diagnostic.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    summary = _markdown(payload)
    (args.report_dir / "source_identity_diagnostic.md").write_text(
        summary, encoding="utf-8"
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
