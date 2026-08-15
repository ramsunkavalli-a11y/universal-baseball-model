#!/usr/bin/env python
"""Audit pinned Chadwick coverage for structured MLBAM IDs from official PBP."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from universal_baseball.certification import download_file
from universal_baseball.chadwick import (
    CHADWICK_ARCHIVE_URL,
    CHADWICK_SNAPSHOT_SHA,
    profile_mlbam_coverage,
    read_chadwick_people_archive,
)
from universal_baseball.official import fetch_official_game_evidence


DEFAULT_SAMPLES = (
    "aaa=780856",
    "dsl=773530",
    "fcl=771821",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sample",
        action="append",
        default=None,
        help="label=game_pk; may be repeated",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/chadwick"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/identity"),
    )
    return parser.parse_args()


def _parse_samples(values: list[str]) -> list[tuple[str, int]]:
    samples: list[tuple[str, int]] = []
    labels: set[str] = set()
    for value in values:
        if "=" not in value:
            raise ValueError(f"sample must be label=game_pk, got {value!r}")
        label, game_id_text = value.split("=", 1)
        label = label.strip()
        if not label:
            raise ValueError("sample label cannot be blank")
        if label in labels:
            raise ValueError(f"duplicate sample label: {label!r}")
        labels.add(label)
        samples.append((label, int(game_id_text)))
    return samples


def _player_ids_from_game(game_id: int) -> tuple[list[int], dict[str, Any]]:
    pa_frame, _ = fetch_official_game_evidence([game_id])
    if pa_frame.is_empty():
        raise RuntimeError(f"official PA projection returned no rows for game {game_id}")

    batter_ids = {
        int(value)
        for value in pa_frame.get_column("batter_id").drop_nulls().to_list()
    }
    pitcher_ids = {
        int(value)
        for value in pa_frame.get_column("pitcher_id").drop_nulls().to_list()
    }
    all_ids = sorted(batter_ids | pitcher_ids)
    return all_ids, {
        "game_pk": game_id,
        "official_pa_count": pa_frame.height,
        "unique_batter_id_count": len(batter_ids),
        "unique_pitcher_id_count": len(pitcher_ids),
        "unique_player_id_count": len(all_ids),
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Chadwick MLBAM crosswalk coverage audit",
        "",
        f"- Chadwick snapshot: `{payload['snapshot_sha']}`",
        f"- Archive SHA-256: `{payload['archive']['sha256']}`",
        f"- Public people rows: {payload['combined']['people_row_count']:,}",
        f"- Rows with MLBAM IDs: {payload['combined']['mlbam_crosswalk_row_count']:,}",
        f"- Unique MLBAM IDs: {payload['combined']['unique_mlbam_id_count']:,}",
        f"- Duplicate MLBAM IDs in snapshot: {payload['combined']['duplicate_mlbam_id_count']:,}",
        "",
        "## Sample coverage",
        "",
        "| Sample | Game | Structured IDs | Chadwick matched | Coverage | Duplicate requested IDs |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for label, sample in payload["samples"].items():
        coverage = sample["coverage"]
        rate = coverage["coverage_rate"]
        rate_text = f"{rate:.1%}" if rate is not None else "n/a"
        lines.append(
            f"| {label} | {sample['game']['game_pk']} | "
            f"{coverage['requested_mlbam_id_count']} | "
            f"{coverage['matched_mlbam_id_count']} | {rate_text} | "
            f"{len(coverage['duplicate_requested_mlbam_ids'])} |"
        )

    combined = payload["combined"]
    combined_rate = combined["coverage_rate"]
    lines.extend(
        [
            "",
            "## Combined observed IDs",
            "",
            f"- Requested structured MLBAM IDs: {combined['requested_mlbam_id_count']}",
            f"- Matched in pinned Chadwick: {combined['matched_mlbam_id_count']}",
            f"- Missing / crosswalk-pending: {combined['missing_mlbam_id_count']}",
            f"- Coverage: {combined_rate:.1%}" if combined_rate is not None else "- Coverage: n/a",
            f"- Duplicate requested MLBAM IDs: `{combined['duplicate_requested_mlbam_ids']}`",
        ]
    )

    if combined["missing_mlbam_ids"]:
        lines.extend(
            [
                "",
                "### Crosswalk-pending MLBAM IDs",
                "",
                "`" + ", ".join(str(value) for value in combined["missing_mlbam_ids"]) + "`",
            ]
        )

    lines.extend(
        [
            "",
            "Missing Chadwick links are coverage evidence, not identity failures. "
            "The structured MLBAM IDs remain canonical event identities and are not "
            "fuzzy-matched by name.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    samples = _parse_samples(args.sample or list(DEFAULT_SAMPLES))

    archive_path = args.work_dir / f"register-{CHADWICK_SNAPSHOT_SHA}.zip"
    archive_metadata = download_file(CHADWICK_ARCHIVE_URL, archive_path)
    people = read_chadwick_people_archive(archive_path)

    sample_payload: dict[str, Any] = {}
    combined_ids: set[int] = set()
    for label, game_id in samples:
        player_ids, game_profile = _player_ids_from_game(game_id)
        combined_ids.update(player_ids)
        sample_payload[label] = {
            "game": game_profile,
            "coverage": profile_mlbam_coverage(people, player_ids),
        }

    combined = profile_mlbam_coverage(people, combined_ids)
    payload = {
        "report_schema_version": 1,
        "snapshot_sha": CHADWICK_SNAPSHOT_SHA,
        "snapshot_url": CHADWICK_ARCHIVE_URL,
        "archive": archive_metadata,
        "samples": sample_payload,
        "combined": combined,
    }

    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / "chadwick_identity_coverage.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    summary = _markdown(payload)
    (args.report_dir / "chadwick_identity_coverage.md").write_text(
        summary,
        encoding="utf-8",
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
