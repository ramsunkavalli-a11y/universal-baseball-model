#!/usr/bin/env python
"""Compare MLBAM identities in a reusable MiLB source file with official PBP."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.certification import (
    download_file,
    read_quarantined_csv,
    sha256_file,
)
from universal_baseball.official import fetch_official_game_evidence
from universal_baseball.source_comparison import select_diverse_game_ids
from universal_baseball.source_identity import compare_source_mlbam_ids


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--asset-name", required=True)
    parser.add_argument("--game-id", type=int, action="append", default=None)
    parser.add_argument(
        "--sample-games",
        type=int,
        default=0,
        help="Select date-spread games when no explicit --game-id is supplied.",
    )
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    return parser.parse_args()


def _fetch_official(
    game_ids: list[int],
) -> tuple[pl.DataFrame, list[int], list[dict[str, Any]]]:
    frames: list[pl.DataFrame] = []
    successes: list[int] = []
    failures: list[dict[str, Any]] = []

    for game_id in game_ids:
        try:
            pa_frame, _ = fetch_official_game_evidence([game_id])
        except Exception as exc:
            failures.append(
                {
                    "game_pk": game_id,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
            continue
        if pa_frame.is_empty():
            failures.append(
                {
                    "game_pk": game_id,
                    "error_type": "EmptyOfficialPAFrame",
                    "error": "official true-PA projection returned no rows",
                }
            )
            continue
        frames.append(pa_frame)
        successes.append(game_id)

    if not frames:
        return pl.DataFrame(), successes, failures
    return pl.concat(frames, how="vertical_relaxed"), successes, failures


def _markdown(payload: dict[str, Any]) -> str:
    result = payload["comparison"]
    rate = result["identity_match_rate"]
    rate_text = f"{rate:.2%}" if rate is not None else "n/a"
    lines = [
        "# Reusable-source MLBAM identity audit",
        "",
        f"- Source asset: `{payload['source_asset']}`",
        f"- Source SHA-256: `{payload['source_sha256']}`",
        f"- Requested games: `{payload['requested_game_ids']}`",
        f"- Official games successfully checked: `{payload['successful_game_ids']}`",
        f"- Official fetch failures: {len(payload['official_fetch_failures'])}",
        f"- Source pitch-bearing sequences: {result['source_pitch_sequence_count']}",
        f"- Official true PAs: {result['official_true_pa_count']}",
        f"- Shared source-sequence / true-PA keys: {result['shared_sequence_true_pa_count']}",
        f"- Source-only pitch-bearing sequences: {result['source_only_pitch_sequence_count']}",
        f"- Official-only true PAs: {result['official_only_true_pa_count']}",
        f"- Batter/pitcher identities compared: {result['identity_comparison_count']}",
        f"- Identity matches: {result['identity_match_count']}",
        f"- Identity mismatches: {result['identity_mismatch_count']}",
        f"- Source identity conflicts: {result['source_identity_conflict_count']}",
        f"- Missing source identities on shared true PAs: {result['source_identity_missing_count']}",
        f"- Identity match rate: **{rate_text}**",
        f"- Clean on shared true PAs: **{result['certification_clean_on_shared_true_pas']}**",
        "",
        "## By role",
        "",
        "| Role | Compared | Matched | Mismatched | Missing | Conflicting source IDs |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for role in ("batter", "pitcher"):
        counts = result["role_counts"][role]
        lines.append(
            f"| {role} | {counts['compared']} | {counts['matched']} | "
            f"{counts['mismatched']} | {counts['missing']} | {counts['conflict']} |"
        )

    for heading, key in (
        ("Identity mismatch examples", "identity_mismatch_examples"),
        ("Source identity conflict examples", "source_identity_conflict_examples"),
        ("Missing source identity examples", "source_identity_missing_examples"),
        ("Source-only pitch-bearing sequence examples", "source_only_pitch_sequence_examples"),
        ("Official-only true PA examples", "official_only_true_pa_examples"),
    ):
        examples = result.get(key) or []
        if examples:
            lines.extend(["", f"## {heading}", "", "```json"])
            lines.append(json.dumps(examples[:10], indent=2, sort_keys=True))
            lines.append("```")

    lines.extend(
        [
            "",
            "This audit never repairs IDs and never matches by player name. Source-only "
            "pitch-bearing sequences are diagnostic source evidence, not assumed plate "
            "appearances. A mismatch or conflict must be investigated before promotion.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    source_path = args.work_dir / args.asset_name
    metadata = download_file(args.url, source_path)
    source = read_quarantined_csv(source_path)

    if args.game_id:
        requested_game_ids = list(dict.fromkeys(args.game_id))
    else:
        if args.sample_games <= 0:
            raise ValueError("provide --game-id or a positive --sample-games")
        requested_game_ids = select_diverse_game_ids(source, limit=args.sample_games)

    official_pas, successful_game_ids, failures = _fetch_official(requested_game_ids)
    if not successful_game_ids:
        raise RuntimeError("official adapter failed for every requested game")

    successful_strings = [str(game_id) for game_id in successful_game_ids]
    source_sample = source.filter(pl.col("game_pk").is_in(successful_strings))
    comparison = compare_source_mlbam_ids(source_sample, official_pas)

    payload = {
        "report_schema_version": 1,
        "source_asset": args.asset_name,
        "source_url": args.url,
        "source_sha256": metadata.get("sha256") or sha256_file(source_path),
        "retrieved_at_utc": metadata.get("retrieved_at_utc"),
        "requested_game_ids": requested_game_ids,
        "successful_game_ids": successful_game_ids,
        "official_fetch_failures": failures,
        "comparison": comparison,
    }

    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / "armstjc_identity_audit.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    summary = _markdown(payload)
    (args.report_dir / "armstjc_identity_audit.md").write_text(
        summary,
        encoding="utf-8",
    )
    print(summary)

    # Only shared true-PAs determine identity cleanliness. Source-only sequence
    # keys are retained as evidence because the pitch source cannot establish PA
    # semantics by itself.
    return 0 if comparison["certification_clean_on_shared_true_pas"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
