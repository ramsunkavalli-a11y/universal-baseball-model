#!/usr/bin/env python
"""Exercise ordering-free source resolution and narrow official adjudication."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import polars as pl

from universal_baseball.authority_adjudication import (
    adjudicate_pitch_conflicts_with_official_pas,
)
from universal_baseball.canonical_adapters import normalize_armstjc_pitch_observations
from universal_baseball.canonical_schema import CANONICAL_SCHEMA_VERSION
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.official import fetch_official_game_evidence
from universal_baseball.provenance import NormalizationDefinition, make_source_snapshot_id
from universal_baseball.resolution import (
    pitch_resolution_conflicts,
    resolve_pitch_observations_across_snapshots,
)


BASE_URL = "https://github.com/armstjc/milb-data-repository/releases/download/pbp"
SOURCE_KEY = ["game_pk", "at_bat_number", "pitch_number"]
OFFICIAL_ADJUDICATION_FIELDS = ("batter_side", "pitcher_hand")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--left-asset", default="2023_7_rk_pbp.csv")
    parser.add_argument("--right-asset", default="2023_8_rk_pbp.csv")
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/cross-snapshot-resolution"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/cross-snapshot-resolution"),
    )
    return parser.parse_args()


def _snapshot_id(asset: str, sha256: str) -> str:
    return make_source_snapshot_id(
        source_name="armstjc_milb_pbp",
        content_sha256=sha256,
        upstream_version=asset,
    )


def _normalization(snapshot_id: str) -> NormalizationDefinition:
    return NormalizationDefinition.build(
        source_snapshot_id=snapshot_id,
        normalizer_name="normalize_armstjc_pitch_observations",
        normalizer_version="1",
        canonical_schema_version=CANONICAL_SCHEMA_VERSION,
    )


def _field_conflict_counts(conflicts: pl.DataFrame) -> dict[str, int]:
    if conflicts.is_empty():
        return {}
    counts: Counter[str] = Counter()
    for fields in conflicts.get_column("conflict_fields").to_list():
        for field in fields or []:
            counts[str(field)] += 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _adjudication_records_with_asset_names(
    adjudication: pl.DataFrame,
    snapshot_to_asset: dict[str, str],
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for row in adjudication.to_dicts():
        candidates = row.pop("source_candidates_by_snapshot") or {}
        matching_ids = row.get("matching_source_snapshot_ids") or []
        ambiguous_ids = row.get("ambiguous_source_snapshot_ids") or []
        records.append(
            {
                **row,
                "source_candidates_by_asset": {
                    snapshot_to_asset.get(snapshot_id, snapshot_id): values
                    for snapshot_id, values in candidates.items()
                },
                "matching_source_assets": [
                    snapshot_to_asset.get(snapshot_id, snapshot_id)
                    for snapshot_id in matching_ids
                ],
                "ambiguous_source_assets": [
                    snapshot_to_asset.get(snapshot_id, snapshot_id)
                    for snapshot_id in ambiguous_ids
                ],
            }
        )
    return records


def main() -> int:
    args = parse_args()
    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)

    left_path = args.work_dir / args.left_asset
    right_path = args.work_dir / args.right_asset
    left_meta = download_file(
        f"{BASE_URL}/{args.left_asset}", left_path, timeout_seconds=180
    )
    right_meta = download_file(
        f"{BASE_URL}/{args.right_asset}", right_path, timeout_seconds=180
    )

    left = read_quarantined_csv(left_path)
    right = read_quarantined_csv(right_path)

    left_keys = left.select(SOURCE_KEY).unique()
    right_keys = right.select(SOURCE_KEY).unique()
    overlap_keys = left_keys.join(right_keys, on=SOURCE_KEY, how="inner")
    if overlap_keys.is_empty():
        raise RuntimeError("selected source pair has no overlapping natural pitch keys")

    left_overlap = left.join(overlap_keys, on=SOURCE_KEY, how="inner")
    right_overlap = right.join(overlap_keys, on=SOURCE_KEY, how="inner")

    left_snapshot = _snapshot_id(args.left_asset, str(left_meta["sha256"]))
    right_snapshot = _snapshot_id(args.right_asset, str(right_meta["sha256"]))
    snapshot_to_asset = {
        left_snapshot: args.left_asset,
        right_snapshot: args.right_asset,
    }
    left_normalization = _normalization(left_snapshot)
    right_normalization = _normalization(right_snapshot)

    left_observations = normalize_armstjc_pitch_observations(
        left_overlap,
        source_snapshot_id=left_snapshot,
        normalization_id=left_normalization.normalization_id,
    )
    right_observations = normalize_armstjc_pitch_observations(
        right_overlap,
        source_snapshot_id=right_snapshot,
        normalization_id=right_normalization.normalization_id,
    )
    observations = pl.concat(
        [left_observations, right_observations],
        how="vertical_relaxed",
    )
    definitions = pl.DataFrame(
        [left_normalization.as_record(), right_normalization.as_record()]
    )

    resolved = resolve_pitch_observations_across_snapshots(observations, definitions)
    conflicts = pitch_resolution_conflicts(resolved)
    conflict_counts = _field_conflict_counts(conflicts)

    snapshot_count_distribution = {
        str(row["source_snapshot_count"]): int(row["len"])
        for row in (
            resolved.group_by("source_snapshot_count")
            .len()
            .sort("source_snapshot_count")
            .to_dicts()
        )
    }

    # Only fields already present as structured matchup evidence in the official
    # true-PA projection are adjudicated here. The source-only consensus remains
    # unchanged regardless of the answer.
    adjudication_records: list[dict[str, object]] = []
    adjudication_status_counts: dict[str, int] = {}
    adjudication_sequence_field_count = 0
    relevant_conflicts = conflicts.filter(
        pl.col("conflict_fields").list.eval(
            pl.element().is_in(list(OFFICIAL_ADJUDICATION_FIELDS))
        ).list.any()
    ) if not conflicts.is_empty() else conflicts

    if not relevant_conflicts.is_empty():
        conflict_game_ids = sorted(
            int(value)
            for value in relevant_conflicts.get_column("game_pk").unique().to_list()
        )
        official_pas, _ = fetch_official_game_evidence(conflict_game_ids)
        adjudication = adjudicate_pitch_conflicts_with_official_pas(
            observations,
            relevant_conflicts,
            official_pas,
            fields=OFFICIAL_ADJUDICATION_FIELDS,
        )
        adjudication_sequence_field_count = adjudication.height
        adjudication_status_counts = {
            str(row["status"]): int(row["len"])
            for row in (
                adjudication.group_by("status")
                .len()
                .sort("status")
                .to_dicts()
            )
        }
        adjudication_records = _adjudication_records_with_asset_names(
            adjudication,
            snapshot_to_asset,
        )

    payload = {
        "left_asset": args.left_asset,
        "right_asset": args.right_asset,
        "left_sha256": left_meta["sha256"],
        "right_sha256": right_meta["sha256"],
        "source_overlap_natural_key_count": overlap_keys.height,
        "canonical_resolved_pitch_count": resolved.height,
        "canonical_observation_variant_count": observations.height,
        "raw_source_row_count_in_overlap": int(left_overlap.height + right_overlap.height),
        "resolved_source_snapshot_count_distribution": snapshot_count_distribution,
        "conflicting_pitch_count": conflicts.height,
        "conflicting_pitch_rate": conflicts.height / resolved.height if resolved.height else None,
        "conflict_field_counts": conflict_counts,
        "conflict_examples": conflicts.select(
            [
                "game_pk",
                "at_bat_index",
                "pitch_number",
                "source_snapshot_count",
                "conflict_fields",
            ]
        ).head(25).to_dicts(),
        "official_adjudication": {
            "fields": list(OFFICIAL_ADJUDICATION_FIELDS),
            "sequence_field_count": adjudication_sequence_field_count,
            "status_counts": adjudication_status_counts,
            "records": adjudication_records,
            "note": (
                "Official evidence is diagnostic only; it does not mutate the "
                "source-only consensus view."
            ),
        },
        "resolution_policy": (
            resolved.get_column("resolution_policy")[0] if resolved.height else None
        ),
        "normalizer_name": (
            resolved.get_column("normalizer_name")[0] if resolved.height else None
        ),
        "normalizer_version": (
            resolved.get_column("normalizer_version")[0] if resolved.height else None
        ),
        "canonical_schema_version": CANONICAL_SCHEMA_VERSION,
    }

    (args.report_dir / "cross_snapshot_resolution.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# Cross-snapshot canonical resolution audit",
        "",
        f"- Left asset: `{args.left_asset}`",
        f"- Right asset: `{args.right_asset}`",
        f"- Overlapping source natural pitch keys: {overlap_keys.height:,}",
        f"- Canonical resolved pitches: {resolved.height:,}",
        f"- Canonical observation variants: {observations.height:,}",
        f"- Raw source rows represented: {left_overlap.height + right_overlap.height:,}",
        f"- Pitches with one or more canonical field conflicts: {conflicts.height:,}",
        (
            "- Canonical conflict rate among overlapping pitches: "
            f"{(conflicts.height / resolved.height):.2%}"
            if resolved.height
            else "- Canonical conflict rate: n/a"
        ),
        f"- Resolution policy: `{payload['resolution_policy']}`",
        "",
        "## Canonical fields with conflicts",
        "",
    ]
    if conflict_counts:
        for field, count in conflict_counts.items():
            lines.append(f"- `{field}`: {count:,} pitches")
    else:
        lines.append("- None")

    lines.extend(["", "## Official adjudication of residual hand conflicts", ""])
    if adjudication_records:
        lines.append(
            f"- Unique sequence-field conflicts checked: {adjudication_sequence_field_count:,}"
        )
        for status, count in adjudication_status_counts.items():
            lines.append(f"- `{status}`: {count:,}")
        lines.append("")
        for row in adjudication_records:
            lines.append(
                f"- game {row['game_pk']} sequence {row['at_bat_index']} "
                f"`{row['field']}`: source={row['source_candidates_by_asset']}; "
                f"official={row['official_value']!r}; status={row['status']}"
            )
    else:
        lines.append("- No supported residual conflicts to adjudicate.")

    lines.extend(
        [
            "",
            "No source row is selected as globally newer. Stable non-null fields survive across snapshots; disagreeing canonical fields remain null in the derived source-only view and are explicitly reported. Official evidence is evaluated separately and does not silently mutate source consensus.",
            "",
        ]
    )
    (args.report_dir / "cross_snapshot_resolution.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
