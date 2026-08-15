#!/usr/bin/env python
"""Adjudicate remaining cross-snapshot handedness conflicts with official evidence.

This is a narrow diagnostic for the real 2023 Rookie July/August overlap. It
compares each source snapshot after canonical normalization, then asks the
current official Stats API PA projection which batter side / pitcher hand it
reports for the affected matchup sequence. No source observation is mutated and
no precedence rule is inferred from filenames or timestamps.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.canonical_adapters import normalize_armstjc_pitch_observations
from universal_baseball.canonical_schema import CANONICAL_SCHEMA_VERSION
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.cross_snapshot import compare_resolved_pitch_snapshots
from universal_baseball.official import fetch_official_game_evidence
from universal_baseball.provenance import NormalizationDefinition, make_source_snapshot_id
from universal_baseball.resolution import resolve_pitch_observations_within_snapshot


BASE_URL = "https://github.com/armstjc/milb-data-repository/releases/download/pbp"
SOURCE_KEY = ["game_pk", "at_bat_number", "pitch_number"]
CANONICAL_KEY = ["game_pk", "at_bat_index", "pitch_number"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--left-asset", default="2023_7_rk_pbp.csv")
    parser.add_argument("--right-asset", default="2023_8_rk_pbp.csv")
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/cross-snapshot-hand-diagnostic"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/cross-snapshot-hand-diagnostic"),
    )
    return parser.parse_args()


def _normalized_snapshot(
    frame: pl.DataFrame,
    *,
    asset: str,
    sha256: str,
) -> pl.DataFrame:
    snapshot_id = make_source_snapshot_id(
        source_name="armstjc_milb_pbp",
        content_sha256=sha256,
        upstream_version=asset,
    )
    normalization = NormalizationDefinition.build(
        source_snapshot_id=snapshot_id,
        normalizer_name="normalize_armstjc_pitch_observations",
        normalizer_version="1",
        canonical_schema_version=CANONICAL_SCHEMA_VERSION,
    )
    observations = normalize_armstjc_pitch_observations(
        frame,
        source_snapshot_id=snapshot_id,
        normalization_id=normalization.normalization_id,
    )
    return resolve_pitch_observations_within_snapshot(observations)


def _official_map(game_ids: list[int]) -> tuple[dict[tuple[int, int], dict[str, Any]], list[int]]:
    official_pas, _ = fetch_official_game_evidence(game_ids)
    rows: dict[tuple[int, int], dict[str, Any]] = {}
    for row in official_pas.to_dicts():
        game_pk = int(row["game_pk"])
        at_bat_index = int(row["at_bat_number"])
        rows[(game_pk, at_bat_index)] = {
            "batter_id": row.get("batter_id"),
            "pitcher_id": row.get("pitcher_id"),
            "batter_side": row.get("batter_side"),
            "pitcher_hand": row.get("pitcher_hand"),
            "event_type": row.get("event_type"),
            "description": row.get("description"),
        }
    return rows, sorted({game_pk for game_pk, _ in rows})


def main() -> int:
    args = parse_args()
    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)

    left_path = args.work_dir / args.left_asset
    right_path = args.work_dir / args.right_asset
    left_meta = download_file(f"{BASE_URL}/{args.left_asset}", left_path, timeout_seconds=180)
    right_meta = download_file(f"{BASE_URL}/{args.right_asset}", right_path, timeout_seconds=180)
    left_raw = read_quarantined_csv(left_path)
    right_raw = read_quarantined_csv(right_path)

    overlap = left_raw.select(SOURCE_KEY).unique().join(
        right_raw.select(SOURCE_KEY).unique(),
        on=SOURCE_KEY,
        how="inner",
    )
    left_overlap = left_raw.join(overlap, on=SOURCE_KEY, how="inner")
    right_overlap = right_raw.join(overlap, on=SOURCE_KEY, how="inner")

    left = _normalized_snapshot(
        left_overlap,
        asset=args.left_asset,
        sha256=str(left_meta["sha256"]),
    )
    right = _normalized_snapshot(
        right_overlap,
        asset=args.right_asset,
        sha256=str(right_meta["sha256"]),
    )
    comparison = compare_resolved_pitch_snapshots(left, right)

    conflict_examples = comparison["non_null_conflict_examples"]
    conflict_keys = {
        (int(row["game_pk"]), int(row["at_bat_index"]), int(row["pitch_number"]))
        for row in conflict_examples
    }
    # The comparator intentionally caps examples. Recover all conflicting keys
    # directly so the diagnostic cannot silently miss conflicts if the count grows.
    left_map = {
        tuple(int(row[column]) for column in CANONICAL_KEY): row
        for row in left.to_dicts()
    }
    right_map = {
        tuple(int(row[column]) for column in CANONICAL_KEY): row
        for row in right.to_dicts()
    }
    conflict_keys = set()
    for key in set(left_map) & set(right_map):
        left_row = left_map[key]
        right_row = right_map[key]
        if any(
            left_row.get(field) is not None
            and right_row.get(field) is not None
            and left_row.get(field) != right_row.get(field)
            for field in ("batter_side", "pitcher_hand")
        ):
            conflict_keys.add(key)

    game_ids = sorted({key[0] for key in conflict_keys})
    official, official_game_ids = _official_map(game_ids)

    rows: list[dict[str, Any]] = []
    official_match_count = 0
    official_left_match_count = 0
    official_right_match_count = 0
    official_neither_count = 0
    missing_official_pa_count = 0

    for game_pk, at_bat_index, pitch_number in sorted(conflict_keys):
        left_row = left_map[(game_pk, at_bat_index, pitch_number)]
        right_row = right_map[(game_pk, at_bat_index, pitch_number)]
        official_row = official.get((game_pk, at_bat_index))
        conflict_fields = [
            field
            for field in ("batter_side", "pitcher_hand")
            if left_row.get(field) is not None
            and right_row.get(field) is not None
            and left_row.get(field) != right_row.get(field)
        ]

        adjudication: dict[str, str] = {}
        if official_row is None:
            missing_official_pa_count += 1
            for field in conflict_fields:
                adjudication[field] = "official_pa_missing"
        else:
            official_match_count += 1
            for field in conflict_fields:
                official_value = official_row.get(field)
                left_value = left_row.get(field)
                right_value = right_row.get(field)
                if official_value == left_value and official_value != right_value:
                    adjudication[field] = "left_matches_official"
                    official_left_match_count += 1
                elif official_value == right_value and official_value != left_value:
                    adjudication[field] = "right_matches_official"
                    official_right_match_count += 1
                elif official_value == left_value == right_value:
                    adjudication[field] = "both_match_official"
                else:
                    adjudication[field] = "neither_matches_official"
                    official_neither_count += 1

        rows.append(
            {
                "game_pk": game_pk,
                "at_bat_index": at_bat_index,
                "pitch_number": pitch_number,
                "conflict_fields": conflict_fields,
                "left": {
                    field: left_row.get(field) for field in conflict_fields
                },
                "right": {
                    field: right_row.get(field) for field in conflict_fields
                },
                "official": official_row,
                "adjudication": adjudication,
            }
        )

    payload = {
        "left_asset": args.left_asset,
        "right_asset": args.right_asset,
        "canonical_shared_pitch_count": comparison["shared_pitch_key_count"],
        "canonical_non_null_conflicting_pitch_count": len(conflict_keys),
        "canonical_non_null_conflict_rate": (
            len(conflict_keys) / comparison["shared_pitch_key_count"]
            if comparison["shared_pitch_key_count"]
            else None
        ),
        "conflict_fields": comparison["fields_with_non_null_conflict"],
        "official_requested_game_ids": game_ids,
        "official_games_with_true_pa_rows": official_game_ids,
        "conflicting_pitches_with_official_pa": official_match_count,
        "conflicting_pitches_without_official_pa": missing_official_pa_count,
        "field_conflicts_where_left_matches_official": official_left_match_count,
        "field_conflicts_where_right_matches_official": official_right_match_count,
        "field_conflicts_where_neither_matches_official": official_neither_count,
        "details": rows,
    }

    json_path = args.report_dir / "cross_snapshot_hand_diagnostic.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Cross-snapshot handedness diagnostic",
        "",
        f"- Shared canonical pitch keys: {comparison['shared_pitch_key_count']:,}",
        f"- Pitches with non-null hand conflicts: {len(conflict_keys):,}",
        f"- Conflict rate: {payload['canonical_non_null_conflict_rate']:.2%}",
        f"- Conflict fields: {payload['conflict_fields']}",
        f"- Official games requested: {game_ids}",
        f"- Conflicting pitches with an official true-PA matchup: {official_match_count}",
        f"- Conflicting pitches without an official true-PA matchup: {missing_official_pa_count}",
        f"- Field conflicts where left snapshot matches official: {official_left_match_count}",
        f"- Field conflicts where right snapshot matches official: {official_right_match_count}",
        f"- Field conflicts where neither snapshot matches official: {official_neither_count}",
        "",
        "No source field is repaired by this diagnostic. It tests whether official structured matchup evidence can adjudicate the small residual source-only conflict set.",
        "",
    ]
    (args.report_dir / "cross_snapshot_hand_diagnostic.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
