#!/usr/bin/env python
"""Test whether reusable PBP can supply batter identity without all-game overlay.

The upstream parser initializes ``batter`` from the official top-level matchup,
but later overwrites that variable for every ``offensive_substitution`` play
event. That can mutate subsequent pitch rows when the substitution is for a
baserunner rather than the batter.

This audit compares three source-only sequence identities with current official
Stats API matchup identity:

- first physical-pitch batter ID;
- last physical-pitch batter ID;
- terminal in-play pitch batter ID when a reusable BIP is present.

If first-pitch identity is materially more stable, historical contact events can
be assigned to that sequence participant rather than trusting the mutable
per-pitch batter field. Zero-pitch PAs are outside this test and remain handled
by the aggregate/official PA layer.
"""

from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
from typing import Any, Mapping

import polars as pl

from universal_baseball.armstjc_schema import normalize_known_schema_aliases
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.event_types import PLATE_APPEARANCE_EVENT_TYPES
from universal_baseball.official_capture import capture_official_json, new_official_session
from universal_baseball.sampling import select_game_ids_by_group


BASE_URL = "https://github.com/armstjc/milb-data-repository/releases/download/pbp"
ASSETS = (
    "2025_4_aaa_pbp.csv",
    "2025_4_aa_pbp.csv",
    "2025_4_a+_pbp.csv",
    "2025_4_a_pbp.csv",
    "2024_6_rk_pbp.csv",
)
GAMES_PER_LEAGUE = 20
IN_PLAY_CODES = frozenset({"D", "E", "X"})


def _int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return int(numeric) if numeric.is_integer() else None


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _source_is_in_play(row: Mapping[str, Any]) -> bool:
    code = str(row.get("type") or "").strip()
    if code in IN_PLAY_CODES:
        return True
    return any(
        row.get(column) not in (None, "")
        for column in ("bb_type", "hit_location", "hc_x", "hc_y", "hit_distance_sc")
    )


def _source_sequence_rows(frame: pl.DataFrame, game_pk: int) -> dict[int, dict[str, Any]]:
    subset = frame.filter(pl.col("game_pk").cast(pl.Int64, strict=False) == game_pk)
    result: dict[int, dict[str, Any]] = {}
    for (at_bat_number,), group in subset.group_by("at_bat_number", maintain_order=False):
        at_bat_index = _int(at_bat_number)
        if at_bat_index is None:
            continue
        rows = group.to_dicts()
        rows.sort(
            key=lambda row: (
                _int(row.get("pitch_number")) if _int(row.get("pitch_number")) is not None else 10**9,
                str(row.get("play_start_datetime") or ""),
            )
        )
        ids = [
            value
            for value in (_int(row.get("batter")) for row in rows)
            if value is not None
        ]
        bip_ids = [
            _int(row.get("batter"))
            for row in rows
            if _source_is_in_play(row) and _int(row.get("batter")) is not None
        ]
        result[at_bat_index] = {
            "source_row_count": len(rows),
            "source_batter_ids": sorted(set(ids)),
            "source_unique_batter_count": len(set(ids)),
            "source_first_batter_id": ids[0] if ids else None,
            "source_last_batter_id": ids[-1] if ids else None,
            "source_bip_batter_ids": sorted(set(bip_ids)),
            "source_bip_batter_id": bip_ids[-1] if len(set(bip_ids)) == 1 and bip_ids else None,
            "has_source_bip": bool(bip_ids),
        }
    return result


def _official_sequences(payload: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for raw in _mapping(payload.get("allPlays") and {"allPlays": payload.get("allPlays")}).get("allPlays") or []:
        play = _mapping(raw)
        at_bat_index = _int(play.get("atBatIndex"))
        if at_bat_index is None:
            continue
        event_type = str(_mapping(play.get("result")).get("eventType") or "").strip()
        batter_id = _int(_mapping(_mapping(play.get("matchup")).get("batter")).get("id"))
        result[at_bat_index] = {
            "official_event_type": event_type or None,
            "official_true_pa": event_type in PLATE_APPEARANCE_EVENT_TYPES,
            "official_batter_id": batter_id,
        }
    return result


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    comparable = [row for row in rows if row["official_batter_id"] is not None]
    first_comparable = [row for row in comparable if row["source_first_batter_id"] is not None]
    last_comparable = [row for row in comparable if row["source_last_batter_id"] is not None]
    bip_comparable = [
        row for row in comparable
        if row["has_source_bip"] and row["source_bip_batter_id"] is not None
    ]

    def count_mismatch(items: list[dict[str, Any]], source_field: str) -> int:
        return sum(row[source_field] != row["official_batter_id"] for row in items)

    hard = [
        row for row in comparable
        if row["source_batter_ids"]
        and row["official_batter_id"] not in row["source_batter_ids"]
    ]
    multiple = [row for row in comparable if row["source_unique_batter_count"] > 1]
    return {
        "source_sequence_count": len(rows),
        "official_batter_comparable_count": len(comparable),
        "multiple_source_batter_id_sequence_count": len(multiple),
        "multiple_source_batter_id_rate": len(multiple) / len(comparable) if comparable else None,
        "official_id_absent_from_all_source_ids_count": len(hard),
        "official_id_absent_from_all_source_ids_rate": len(hard) / len(comparable) if comparable else None,
        "first_pitch_comparable_count": len(first_comparable),
        "first_pitch_mismatch_count": count_mismatch(first_comparable, "source_first_batter_id"),
        "first_pitch_mismatch_rate": (
            count_mismatch(first_comparable, "source_first_batter_id") / len(first_comparable)
            if first_comparable else None
        ),
        "last_pitch_comparable_count": len(last_comparable),
        "last_pitch_mismatch_count": count_mismatch(last_comparable, "source_last_batter_id"),
        "last_pitch_mismatch_rate": (
            count_mismatch(last_comparable, "source_last_batter_id") / len(last_comparable)
            if last_comparable else None
        ),
        "bip_comparable_count": len(bip_comparable),
        "bip_pitch_mismatch_count": count_mismatch(bip_comparable, "source_bip_batter_id"),
        "bip_pitch_mismatch_rate": (
            count_mismatch(bip_comparable, "source_bip_batter_id") / len(bip_comparable)
            if bip_comparable else None
        ),
    }


def main() -> int:
    work_dir = Path("data/quarantine/source-batter-identity-fidelity")
    report_dir = Path("reports/generated/source-batter-identity-fidelity")
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    selected_games: list[dict[str, Any]] = []
    frames: dict[str, pl.DataFrame] = {}
    asset_meta: dict[str, Any] = {}
    for asset in ASSETS:
        path = work_dir / asset
        metadata = download_file(f"{BASE_URL}/{asset}", path, timeout_seconds=240)
        raw = read_quarantined_csv(path)
        frame, schema_report = normalize_known_schema_aliases(raw)
        frames[asset] = frame
        asset_meta[asset] = {"sha256": metadata["sha256"], "schema": schema_report}
        groups = select_game_ids_by_group(frame, "league_id", per_group=GAMES_PER_LEAGUE)
        for league_id_text, game_ids in sorted(groups.items(), key=lambda pair: int(float(pair[0]))):
            if len(game_ids) < GAMES_PER_LEAGUE:
                raise RuntimeError(
                    f"{asset} league {league_id_text} has only {len(game_ids)} selected games"
                )
            league_id = int(float(league_id_text))
            league_names = (
                frame.filter(pl.col("league_id").cast(pl.Int64, strict=False) == league_id)
                .get_column("league_name")
                .drop_nulls()
                .cast(pl.String)
                .unique()
                .sort()
                .to_list()
            )
            for game_pk in game_ids:
                selected_games.append(
                    {
                        "asset": asset,
                        "league_id": league_id,
                        "league_name": " / ".join(league_names),
                        "game_pk": int(game_pk),
                    }
                )

    rows: list[dict[str, Any]] = []
    session = new_official_session()
    try:
        for game in sorted(selected_games, key=lambda row: (row["league_id"], row["game_pk"])):
            source = _source_sequence_rows(frames[game["asset"]], game["game_pk"])
            capture = capture_official_json(
                f"game/{game['game_pk']}/playByPlay", session=session
            )
            if not isinstance(capture.data, Mapping):
                raise RuntimeError(f"official PBP is not an object for game {game['game_pk']}")
            official = _official_sequences(capture.data)
            for at_bat_index, source_row in source.items():
                official_row = official.get(at_bat_index, {})
                if not bool(official_row.get("official_true_pa")):
                    continue
                rows.append(
                    {
                        **game,
                        "at_bat_index": at_bat_index,
                        **source_row,
                        "official_event_type": official_row.get("official_event_type"),
                        "official_batter_id": official_row.get("official_batter_id"),
                        "official_snapshot_sha256": capture.content_sha256,
                    }
                )
    finally:
        session.close()

    by_league: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_league[int(row["league_id"])].append(row)
    league_summaries = {
        str(league_id): {
            "league_name": next(iter(group))["league_name"],
            "game_count": len({row["game_pk"] for row in group}),
            **_summary(group),
        }
        for league_id, group in sorted(by_league.items())
    }
    overall = _summary(rows)

    mismatch_examples = [
        row for row in rows
        if (
            row["source_first_batter_id"] != row["official_batter_id"]
            or row["source_last_batter_id"] != row["official_batter_id"]
            or (
                row["has_source_bip"]
                and row["source_bip_batter_id"] is not None
                and row["source_bip_batter_id"] != row["official_batter_id"]
            )
        )
    ][:50]

    payload = {
        "report_schema_version": 1,
        "status": "source_batter_identity_fidelity_audit",
        "games_per_actual_league": GAMES_PER_LEAGUE,
        "assets": asset_meta,
        "selected_game_count": len(selected_games),
        "overall": overall,
        "league_summaries": league_summaries,
        "mismatch_examples": mismatch_examples,
        "interpretation_guardrail": (
            "This audit tests pitch-bearing official true PAs only. Zero-pitch PAs are not "
            "evidence against source participant identity because they have no reusable pitch row. "
            "A first-pitch rule is promoted only if its official mismatch behavior is materially "
            "safer than mutable terminal/per-pitch identity across the sampled leagues."
        ),
    }
    (report_dir / "source_batter_identity_fidelity.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    lines = [
        "# Reusable PBP batter-identity fidelity audit",
        "",
        f"- Games per actual league: {GAMES_PER_LEAGUE}",
        f"- Selected games: {len(selected_games)}",
        f"- Comparable pitch-bearing true PAs: {overall['official_batter_comparable_count']:,}",
        f"- Multiple source batter IDs within sequence: {overall['multiple_source_batter_id_sequence_count']:,} ({overall['multiple_source_batter_id_rate']:.4%})",
        f"- Official batter absent from every source ID: {overall['official_id_absent_from_all_source_ids_count']:,} ({overall['official_id_absent_from_all_source_ids_rate']:.4%})",
        f"- First-pitch batter mismatch: {overall['first_pitch_mismatch_count']:,}/{overall['first_pitch_comparable_count']:,} ({overall['first_pitch_mismatch_rate']:.4%})",
        f"- Last-pitch batter mismatch: {overall['last_pitch_mismatch_count']:,}/{overall['last_pitch_comparable_count']:,} ({overall['last_pitch_mismatch_rate']:.4%})",
        f"- In-play pitch batter mismatch: {overall['bip_pitch_mismatch_count']:,}/{overall['bip_comparable_count']:,} ({overall['bip_pitch_mismatch_rate']:.4%})",
        "",
        "## By league",
        "",
    ]
    for league_id, summary in league_summaries.items():
        lines.append(
            f"- {league_id} {summary['league_name']}: PAs={summary['official_batter_comparable_count']:,}; "
            f"multi-ID={summary['multiple_source_batter_id_sequence_count']}; "
            f"first mismatch={summary['first_pitch_mismatch_count']}; "
            f"last mismatch={summary['last_pitch_mismatch_count']}; "
            f"BIP mismatch={summary['bip_pitch_mismatch_count']}"
        )
    lines.append("")
    summary_text = "\n".join(lines)
    (report_dir / "source_batter_identity_fidelity.md").write_text(
        summary_text, encoding="utf-8"
    )
    print(summary_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
