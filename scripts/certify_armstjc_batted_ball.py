#!/usr/bin/env python
"""Compare reusable MiLB batted-ball fields with current official hitData."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.batted_ball import compare_source_batted_balls
from universal_baseball.certification import read_quarantined_csv
from universal_baseball.official import fetch_official_game_evidence
from universal_baseball.source_comparison import select_diverse_game_ids


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", type=Path, required=True)
    parser.add_argument("--sample-games", type=int, default=3)
    parser.add_argument("--report-dir", type=Path, required=True)
    return parser.parse_args()


def _fetch_official(
    game_ids: list[int],
) -> tuple[pl.DataFrame, list[dict[str, Any]], list[int]]:
    pitch_frames: list[pl.DataFrame] = []
    failures: list[dict[str, Any]] = []
    successful_ids: list[int] = []

    for game_id in game_ids:
        try:
            _, pitch_frame = fetch_official_game_evidence([game_id])
        except Exception as exc:
            failures.append(
                {
                    "game_pk": game_id,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
            continue
        pitch_frames.append(pitch_frame)
        successful_ids.append(game_id)

    pitches = (
        pl.concat(pitch_frames, how="vertical_relaxed")
        if pitch_frames
        else pl.DataFrame()
    )
    return pitches, failures, successful_ids


def _markdown(payload: dict[str, Any]) -> str:
    comparison = payload["comparison"]
    lines = [
        "# armstjc batted-ball evidence audit",
        "",
        f"- Source file: `{payload['source_file']}`",
        f"- Requested games: {payload['requested_game_ids']}",
        f"- Successful official games: {payload['successful_game_ids']}",
        f"- Official fetch failures: {len(payload['official_fetch_failures'])}",
        f"- Current official in-play pitches: {comparison['official_in_play_pitch_count']}",
        f"- Shared source pitch keys: {comparison['shared_in_play_pitch_key_count']}",
        f"- Current official in-play pitch keys absent from source: "
        f"{comparison['source_missing_in_play_pitch_key_count']}",
        f"- Source field conflicts on a pitch key: "
        f"{comparison['total_source_field_conflict_count']}",
        f"- Field mismatches when both values exist: "
        f"{comparison['total_field_mismatch_count']}",
        f"- Strict current-feed clean: **{comparison['certification_clean']}**",
        "",
        "## Direct field checks",
        "",
        "The source columns below are direct copies of MLB `hitData`/matchup fields. "
        "This audit does not derive spray direction or classify pull/center/opposite.",
        "",
        "| Source field | Official field | Source coverage | Official coverage | Both present | Agreement | Source missing while official present | Source key conflicts |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]

    for source_field, summary in comparison["field_summaries"].items():
        source_coverage = summary["source_coverage_of_official_bip"]
        official_coverage = summary["official_coverage_of_official_bip"]
        agreement = summary["agreement_rate_when_both_nonblank"]
        source_coverage_text = (
            f"{source_coverage:.1%}" if source_coverage is not None else "n/a"
        )
        official_coverage_text = (
            f"{official_coverage:.1%}" if official_coverage is not None else "n/a"
        )
        agreement_text = f"{agreement:.1%}" if agreement is not None else "n/a"
        lines.append(
            f"| `{source_field}` | `{summary['official_field']}` | "
            f"{source_coverage_text} | {official_coverage_text} | "
            f"{summary['both_nonblank']} | {agreement_text} | "
            f"{summary['source_missing_when_official_present']} | "
            f"{summary['source_conflicting_key_count']} |"
        )

    source_trajectory = comparison.get("trajectory_source_counts_on_shared_official_bip") or {}
    official_trajectory = comparison.get("trajectory_official_counts_on_shared_official_bip") or {}
    if source_trajectory or official_trajectory:
        lines.extend(
            [
                "",
                "## Trajectory vocabulary",
                "",
                f"- Source: `{source_trajectory}`",
                f"- Current official: `{official_trajectory}`",
            ]
        )

    if comparison["mismatch_examples"]:
        lines.extend(["", "## Field mismatch examples", ""])
        for row in comparison["mismatch_examples"][:20]:
            lines.append(
                f"- game {row['game_pk']} PA {row['at_bat_number']} pitch "
                f"{row['pitch_number']} `{row['field']}`: "
                f"source={row['source_value']!r}, official={row['official_value']!r}"
            )

    if comparison["source_field_conflict_examples"]:
        lines.extend(["", "## Source payload conflicts affecting audited fields", ""])
        for row in comparison["source_field_conflict_examples"][:20]:
            lines.append(
                f"- game {row['game_pk']} PA {row['at_bat_number']} pitch "
                f"{row['pitch_number']}: {row['conflicts']}"
            )

    lines.extend(
        [
            "",
            "A non-clean result is not automatically a source failure: the current "
            "official feed can contain post-game corrections that differ from the "
            "historical source snapshot. Mismatches are evidence to classify, not "
            "values to overwrite silently.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    source = read_quarantined_csv(args.input_file)
    game_ids = select_diverse_game_ids(source, limit=args.sample_games)
    official_pitches, failures, successful_ids = _fetch_official(game_ids)

    if not successful_ids:
        raise RuntimeError("official adapter failed for every requested game")

    source_sample = source.filter(
        pl.col("game_pk").is_in([str(game_id) for game_id in successful_ids])
    )
    comparison = compare_source_batted_balls(source_sample, official_pitches)
    payload = {
        "report_schema_version": 1,
        "source_file": args.input_file.name,
        "requested_game_ids": game_ids,
        "successful_game_ids": successful_ids,
        "official_fetch_failures": failures,
        "comparison": comparison,
    }

    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / "armstjc_batted_ball_sample.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    summary = _markdown(payload)
    (args.report_dir / "armstjc_batted_ball_sample.md").write_text(
        summary,
        encoding="utf-8",
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
