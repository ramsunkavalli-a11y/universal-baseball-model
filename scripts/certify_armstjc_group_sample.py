#!/usr/bin/env python
"""Compare one or more source games from each observed group to official PBP."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.certification import read_quarantined_csv
from universal_baseball.official import fetch_official_game_evidence
from universal_baseball.sampling import select_game_ids_by_group
from universal_baseball.source_comparison import compare_pitch_source_to_official_pas


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", type=Path, required=True)
    parser.add_argument("--group-column", default="league_name")
    parser.add_argument("--games-per-group", type=int, default=1)
    parser.add_argument("--report-dir", type=Path, required=True)
    return parser.parse_args()


def _fetch_game(game_id: int) -> tuple[pl.DataFrame, pl.DataFrame]:
    return fetch_official_game_evidence([game_id])


def main() -> int:
    args = parse_args()
    frame = read_quarantined_csv(args.input_file)
    selected = select_game_ids_by_group(
        frame,
        args.group_column,
        per_group=args.games_per_group,
    )
    if not selected:
        raise RuntimeError(
            f"no game groups selected from source column {args.group_column!r}"
        )

    groups: dict[str, Any] = {}
    failed_games: list[dict[str, Any]] = []

    for group_value, game_ids in selected.items():
        group_source = frame.filter(
            pl.col(args.group_column).cast(pl.String) == group_value
        )
        pa_frames: list[pl.DataFrame] = []
        pitch_frames: list[pl.DataFrame] = []
        successful_ids: list[int] = []

        for game_id in game_ids:
            try:
                pa_frame, pitch_frame = _fetch_game(game_id)
            except Exception as exc:
                failed_games.append(
                    {
                        "group": group_value,
                        "game_pk": game_id,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
                continue
            if pa_frame.is_empty():
                failed_games.append(
                    {
                        "group": group_value,
                        "game_pk": game_id,
                        "error_type": "EmptyOfficialPAFrame",
                        "error": "official PBP projection returned no rows",
                    }
                )
                continue
            pa_frames.append(pa_frame)
            pitch_frames.append(pitch_frame)
            successful_ids.append(game_id)

        if not successful_ids:
            groups[group_value] = {
                "requested_game_ids": game_ids,
                "successful_game_ids": [],
                "comparison": None,
            }
            continue

        official_pas = pl.concat(pa_frames, how="vertical_relaxed")
        official_pitches = pl.concat(pitch_frames, how="vertical_relaxed")
        source_sample = group_source.filter(
            pl.col("game_pk").is_in([str(game_id) for game_id in successful_ids])
        )
        comparison = compare_pitch_source_to_official_pas(
            source_sample,
            official_pas,
            official_pitches,
        )
        groups[group_value] = {
            "requested_game_ids": game_ids,
            "successful_game_ids": successful_ids,
            "comparison": comparison,
        }

    payload = {
        "report_schema_version": 1,
        "source_file": args.input_file.name,
        "group_column": args.group_column,
        "games_per_group": args.games_per_group,
        "selected_groups": selected,
        "groups": groups,
        "failed_games": failed_games,
    }

    args.report_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.report_dir / "armstjc_group_official_sample.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# armstjc grouped official sample",
        "",
        f"- Source file: `{args.input_file.name}`",
        f"- Group column: `{args.group_column}`",
        f"- Groups sampled: {len(selected)}",
        f"- Failed games: {len(failed_games)}",
        "",
    ]
    for group_value, result in groups.items():
        comparison = result.get("comparison")
        lines.append(f"## {group_value}")
        lines.append("")
        lines.append(f"- Games: {result['successful_game_ids']}")
        if comparison is None:
            lines.append("- No successful official comparison.")
        else:
            lines.append(
                f"- Shared PAs: {comparison['shared_pa_count']}/"
                f"{comparison['official_pa_count']} official PAs"
            )
            lines.append(
                f"- Official-only positive-pitch PAs: "
                f"{comparison['official_only_positive_pitch_pa_count']}"
            )
            lines.append(
                f"- Pitch-count mismatch PAs: "
                f"{comparison['pitch_count_mismatch_pa_count']}"
            )
        lines.append("")

    (args.report_dir / "armstjc_group_official_sample.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print("\n".join(lines))

    # A source-group audit should fail only if a requested group could not be
    # checked at all. Observed source-vs-current-feed discrepancies remain report
    # evidence to investigate rather than being auto-repaired or hidden.
    return 1 if any(result.get("comparison") is None for result in groups.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
