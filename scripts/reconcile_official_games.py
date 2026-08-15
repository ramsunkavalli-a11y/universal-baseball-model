#!/usr/bin/env python
"""Reconcile narrow official PBP outcomes against official game boxscores."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.official import (
    fetch_official_game_evidence,
    fetch_official_team_batting,
)
from universal_baseball.reconciliation import (
    aggregate_pa_batting,
    compare_batting_lines,
    profile_pa_event_types,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--game-id",
        type=int,
        action="append",
        required=True,
        help="Stats API game_pk; repeat for multiple games.",
    )
    parser.add_argument("--label", default="official-games")
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/reconciliation"),
    )
    parser.add_argument(
        "--require-exact",
        action="store_true",
        help="Return a non-zero exit code if any batting line fails reconciliation.",
    )
    return parser.parse_args()


def _fetch_games(game_ids: list[int]) -> tuple[pl.DataFrame, pl.DataFrame, list[dict[str, Any]]]:
    pa_frames: list[pl.DataFrame] = []
    box_frames: list[pl.DataFrame] = []
    failures: list[dict[str, Any]] = []

    for game_id in game_ids:
        try:
            pa_frame, _ = fetch_official_game_evidence([game_id])
            box_frame = fetch_official_team_batting([game_id])
            if pa_frame.is_empty():
                raise RuntimeError("official playByPlay projection returned no PAs")
            if box_frame.is_empty():
                raise RuntimeError("official boxscore projection returned no team batting lines")
            pa_frames.append(pa_frame)
            box_frames.append(box_frame)
        except Exception as exc:
            failures.append(
                {
                    "game_pk": game_id,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )

    pas = pl.concat(pa_frames, how="vertical_relaxed") if pa_frames else pl.DataFrame()
    boxes = pl.concat(box_frames, how="vertical_relaxed") if box_frames else pl.DataFrame()
    return pas, boxes, failures


def _markdown(payload: dict[str, Any]) -> str:
    comparison = payload["comparison"]
    event_profile = payload["event_type_profile"]
    lines = [
        "# Official PBP → boxscore batting reconciliation",
        "",
        f"- Label: `{payload['label']}`",
        f"- Requested games: {len(payload['requested_game_ids'])}",
        f"- Successfully fetched games: {payload['successful_game_count']}",
        f"- Fetch failures: {len(payload['fetch_failures'])}",
        f"- Derived batting lines: {comparison['derived_line_count']}",
        f"- Official batting lines: {comparison['official_line_count']}",
        f"- Exact matching lines: {comparison['exact_match_line_count']}",
        f"- Mismatching lines: {comparison['mismatch_line_count']}",
        f"- All reconciled: **{comparison['all_reconciled']}**",
        "",
        "## Structured PA event vocabulary",
        "",
        f"Null/blank event types: {event_profile.get('null_or_blank_count')}",
    ]

    for event_type, count in (event_profile.get("counts") or {}).items():
        lines.append(f"- `{event_type}`: {count}")

    if comparison["stat_mismatch_counts"]:
        lines.extend(["", "## Stat mismatch counts", ""])
        for stat, count in comparison["stat_mismatch_counts"].items():
            lines.append(f"- `{stat}`: {count} batting lines")

    if comparison["mismatch_rows"]:
        lines.extend(["", "## Mismatch examples", ""])
        for row in comparison["mismatch_rows"][:20]:
            lines.append(
                f"- game {row['game_pk']} {row['batting_side']}: "
                f"{row['mismatched_stats']}"
            )
            lines.append(
                f"  - derived-official: {row['differences_derived_minus_official']}"
            )

    if payload["fetch_failures"]:
        lines.extend(["", "## Fetch failures", ""])
        for failure in payload["fetch_failures"]:
            lines.append(
                f"- game {failure['game_pk']}: {failure['error_type']}: "
                f"{failure['error'].splitlines()[0]}"
            )

    lines.extend(
        [
            "",
            "This report compares two official representations for the same games. "
            "It certifies our narrow event projection/accounting logic; it does not "
            "make the boxscore independent evidence about MLB's underlying feed.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    game_ids = list(dict.fromkeys(args.game_id))
    pas, boxes, failures = _fetch_games(game_ids)

    if pas.is_empty() or boxes.is_empty():
        raise RuntimeError("no games produced both PBP and boxscore evidence")

    derived = aggregate_pa_batting(pas)
    comparison = compare_batting_lines(derived, boxes)
    event_profile = profile_pa_event_types(pas)
    successful_games = sorted(
        {int(value) for value in derived.get_column("game_pk").unique().to_list()}
    )

    payload = {
        "report_schema_version": 1,
        "label": args.label,
        "requested_game_ids": game_ids,
        "successful_game_ids": successful_games,
        "successful_game_count": len(successful_games),
        "fetch_failures": failures,
        "event_type_profile": event_profile,
        "comparison": comparison,
    }

    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / "official_pbp_boxscore_reconciliation.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    summary = _markdown(payload)
    (args.report_dir / "official_pbp_boxscore_reconciliation.md").write_text(
        summary,
        encoding="utf-8",
    )
    print(summary)

    if args.require_exact and (failures or not comparison["all_reconciled"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
