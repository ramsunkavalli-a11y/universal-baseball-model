#!/usr/bin/env python
"""Build a one-game canonical source→Parquet→DuckDB foundation proof of concept.

This is deliberately not a historical backfill. It uses a known 2023 ACL game
that exercises two real edge cases already found during certification:

- a physical pitch inside a sequence that does not become a plate appearance;
- the reusable-source pinch-runner batter mutation.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import duckdb
from mlbstatsapi import MlbDataAdapter
import polars as pl

from universal_baseball.canonical_adapters import (
    normalize_armstjc_pitch_observations,
    normalize_official_play_sequence_observations,
    stable_payload_hash,
)
from universal_baseball.canonical_schema import (
    CANONICAL_SCHEMA_VERSION,
    validate_normalization_definition,
    validate_provenance_links,
    validate_quality_issue,
    validate_source_snapshot,
)
from universal_baseball.certification import download_file, read_quarantined_csv, sha256_file
from universal_baseball.provenance import NormalizationDefinition, SourceSnapshot
from universal_baseball.source_identity import compare_source_mlbam_ids
from universal_baseball.storage import write_canonical_parquet


DEFAULT_ASSET = "2023_8_rk_pbp.csv"
DEFAULT_URL = (
    "https://github.com/armstjc/milb-data-repository/releases/download/pbp/"
    + DEFAULT_ASSET
)
DEFAULT_GAME_ID = 743157


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-url", default=DEFAULT_URL)
    parser.add_argument("--source-asset", default=DEFAULT_ASSET)
    parser.add_argument("--game-id", type=int, default=DEFAULT_GAME_ID)
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/foundation-poc"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/canonical/foundation-poc"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/foundation-poc"),
    )
    return parser.parse_args()


def _utc_from_metadata(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("retrieval timestamp must be timezone-aware")
    return parsed.astimezone(UTC)


def _capture_official_payload(game_id: int, path: Path) -> tuple[dict[str, Any], datetime, str]:
    adapter = MlbDataAdapter(ver="v1")
    try:
        response = adapter.get(f"game/{game_id}/playByPlay")
    finally:
        adapter.close()
    if not response.data:
        raise RuntimeError(f"official playByPlay returned no data for game {game_id}")

    path.parent.mkdir(parents=True, exist_ok=True)
    payload_text = json.dumps(
        response.data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    path.write_text(payload_text, encoding="utf-8")
    return dict(response.data), datetime.now(UTC), sha256_file(path)


def _official_true_pa_identity_frame(sequences: pl.DataFrame) -> pl.DataFrame:
    return (
        sequences.filter(pl.col("is_plate_appearance") == True)  # noqa: E712
        .select(
            [
                pl.col("game_pk").cast(pl.String),
                pl.col("at_bat_index").cast(pl.String).alias("at_bat_number"),
                pl.col("batter_mlbam_id").alias("batter_id"),
                pl.col("pitcher_mlbam_id").alias("pitcher_id"),
                pl.col("result_event_type").alias("event_type"),
            ]
        )
    )


def _quality_issues_from_identity(
    comparison: dict[str, Any],
    *,
    source_snapshot_id: str,
    normalization_id: str,
    detected_at: datetime,
) -> pl.DataFrame:
    rows: list[dict[str, Any]] = []
    for mismatch in comparison.get("identity_mismatch_examples") or []:
        details = json.dumps(mismatch, sort_keys=True, separators=(",", ":"))
        issue_material = {
            "issue_code": "reusable_source_identity_mismatch",
            "source_snapshot_id": source_snapshot_id,
            "normalization_id": normalization_id,
            **mismatch,
        }
        rows.append(
            {
                "quality_issue_id": stable_payload_hash(issue_material),
                "issue_code": "reusable_source_identity_mismatch",
                "severity": "warning",
                "entity_type": "play_sequence",
                "game_pk": int(mismatch["game_pk"]),
                "at_bat_index": int(mismatch["at_bat_number"]),
                "pitch_number": None,
                "mlbam_id": mismatch.get("source_id"),
                "source_snapshot_id": source_snapshot_id,
                "normalization_id": normalization_id,
                "check_name": "source_identity_vs_official_sequence",
                "check_version": "1",
                "detected_at_utc": detected_at,
                "details_json": details,
            }
        )

    if not rows:
        return validate_quality_issue(
            pl.DataFrame(
                schema={
                    "quality_issue_id": pl.String,
                    "issue_code": pl.String,
                    "severity": pl.String,
                    "entity_type": pl.String,
                    "check_name": pl.String,
                    "check_version": pl.String,
                    "detected_at_utc": pl.Datetime(time_unit="us", time_zone="UTC"),
                    "details_json": pl.String,
                }
            )
        )
    return validate_quality_issue(pl.DataFrame(rows))


def _markdown(payload: dict[str, Any]) -> str:
    checks = payload["checks"]
    return "\n".join(
        [
            "# Canonical foundation POC",
            "",
            f"- Game: `{payload['game_pk']}`",
            f"- Source asset: `{payload['source_asset']}`",
            f"- Canonical schema version: `{CANONICAL_SCHEMA_VERSION}`",
            f"- Source pitch observations: {payload['counts']['pitch_observations']}",
            f"- Official play-sequence observations: {payload['counts']['play_sequence_observations']}",
            f"- Official true PAs: {payload['counts']['true_plate_appearances']}",
            f"- Official non-PA sequences: {payload['counts']['non_pa_sequences']}",
            f"- Physical pitches attached to non-PA sequences: {checks['physical_pitches_in_non_pa_sequences']}",
            f"- Reusable-source identity mismatches: {payload['counts']['identity_mismatches']}",
            f"- Quality issues emitted: {payload['counts']['quality_issues']}",
            f"- Parquet artifacts written: {len(payload['artifacts'])}",
            f"- DuckDB joined pitch rows: {checks['duckdb_joined_pitch_rows']}",
            "",
            "## Assertions",
            "",
            f"- Non-PA physical pitch preserved: **{checks['non_pa_pitch_preserved']}**",
            f"- True/non-PA classification both present: **{checks['both_sequence_classes_present']}**",
            f"- Known source identity defect becomes quality evidence: **{checks['identity_issue_preserved']}**",
            f"- DuckDB can query written Parquet directly: **{checks['duckdb_query_ok']}**",
            "",
            "No source row or identity is repaired in this POC. Canonical sequence identity comes from official structured evidence; raw reusable-source participant IDs remain source observations.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)

    source_path = args.work_dir / args.source_asset
    source_metadata = download_file(args.source_url, source_path)
    raw_source = read_quarantined_csv(source_path)
    source_game = raw_source.filter(
        pl.col("game_pk").cast(pl.String) == str(args.game_id)
    )
    if source_game.is_empty():
        raise RuntimeError(f"source asset contains no rows for game {args.game_id}")

    armstjc_snapshot = SourceSnapshot.build(
        source_name="armstjc_milb_pbp",
        source_role="historical_bootstrap",
        upstream_locator=args.source_url,
        upstream_version=args.source_asset,
        content_sha256=source_metadata["sha256"],
        retrieved_at_utc=_utc_from_metadata(source_metadata["retrieved_at_utc"]),
        license_id="MIT",
        raw_object_key=str(source_path),
    )
    armstjc_normalization = NormalizationDefinition.build(
        source_snapshot_id=armstjc_snapshot.source_snapshot_id,
        normalizer_name="canonical_armstjc_pitch_adapter",
        normalizer_version="0.1",
        canonical_schema_version=CANONICAL_SCHEMA_VERSION,
    )

    official_path = args.work_dir / f"mlb-statsapi-{args.game_id}-playbyplay.json"
    official_payload, official_retrieved, official_sha = _capture_official_payload(
        args.game_id, official_path
    )
    official_snapshot = SourceSnapshot.build(
        source_name="mlb_stats_api_playbyplay",
        source_role="official_authority",
        upstream_locator=f"v1/game/{args.game_id}/playByPlay",
        upstream_version="v1",
        content_sha256=official_sha,
        retrieved_at_utc=official_retrieved,
        raw_object_key=str(official_path),
    )
    official_normalization = NormalizationDefinition.build(
        source_snapshot_id=official_snapshot.source_snapshot_id,
        normalizer_name="canonical_official_sequence_adapter",
        normalizer_version="0.1",
        canonical_schema_version=CANONICAL_SCHEMA_VERSION,
    )

    source_snapshots = validate_source_snapshot(
        pl.DataFrame([
            armstjc_snapshot.as_record(),
            official_snapshot.as_record(),
        ])
    )
    normalizations = validate_normalization_definition(
        pl.DataFrame([
            armstjc_normalization.as_record(),
            official_normalization.as_record(),
        ])
    )

    pitch_observations = normalize_armstjc_pitch_observations(
        source_game,
        source_snapshot_id=armstjc_snapshot.source_snapshot_id,
        normalization_id=armstjc_normalization.normalization_id,
    )
    sequence_observations = normalize_official_play_sequence_observations(
        args.game_id,
        official_payload,
        source_snapshot_id=official_snapshot.source_snapshot_id,
        normalization_id=official_normalization.normalization_id,
    )
    validate_provenance_links(
        pitch_observations,
        normalizations,
        source_snapshots,
        table_name="pitch_observation",
    )
    validate_provenance_links(
        sequence_observations,
        normalizations,
        source_snapshots,
        table_name="play_sequence_observation",
    )

    identity_comparison = compare_source_mlbam_ids(
        source_game,
        _official_true_pa_identity_frame(sequence_observations),
    )
    quality_issues = _quality_issues_from_identity(
        identity_comparison,
        source_snapshot_id=armstjc_snapshot.source_snapshot_id,
        normalization_id=armstjc_normalization.normalization_id,
        detected_at=datetime.now(UTC),
    )

    tables = {
        "source_snapshot": source_snapshots,
        "normalization_definition": normalizations,
        "play_sequence_observation": sequence_observations,
        "pitch_observation": pitch_observations,
        "quality_issue": quality_issues,
    }
    artifacts = {}
    for table_name, frame in tables.items():
        artifact = write_canonical_parquet(
            frame,
            args.output_dir / f"{table_name}.parquet",
            table_name=table_name,
        )
        artifacts[table_name] = artifact.as_record()

    sequence_path = args.output_dir / "play_sequence_observation.parquet"
    pitch_path = args.output_dir / "pitch_observation.parquet"
    with duckdb.connect(":memory:") as connection:
        joined_pitch_rows = connection.execute(
            "SELECT count(*) FROM read_parquet(?) p "
            "JOIN read_parquet(?) s USING (game_pk, at_bat_index)",
            [str(pitch_path), str(sequence_path)],
        ).fetchone()[0]
        non_pa_pitch_rows = connection.execute(
            "SELECT count(*) FROM read_parquet(?) p "
            "JOIN read_parquet(?) s USING (game_pk, at_bat_index) "
            "WHERE s.is_plate_appearance = false",
            [str(pitch_path), str(sequence_path)],
        ).fetchone()[0]

    true_pa_count = sequence_observations.filter(pl.col("is_plate_appearance") == True).height  # noqa: E712
    non_pa_count = sequence_observations.filter(pl.col("is_plate_appearance") == False).height  # noqa: E712
    counts = {
        "pitch_observations": pitch_observations.height,
        "play_sequence_observations": sequence_observations.height,
        "true_plate_appearances": true_pa_count,
        "non_pa_sequences": non_pa_count,
        "identity_mismatches": identity_comparison["identity_mismatch_count"],
        "quality_issues": quality_issues.height,
    }
    checks = {
        "physical_pitches_in_non_pa_sequences": int(non_pa_pitch_rows),
        "duckdb_joined_pitch_rows": int(joined_pitch_rows),
        "non_pa_pitch_preserved": non_pa_pitch_rows > 0,
        "both_sequence_classes_present": true_pa_count > 0 and non_pa_count > 0,
        "identity_issue_preserved": (
            identity_comparison["identity_mismatch_count"] > 0
            and quality_issues.height >= identity_comparison["identity_mismatch_count"]
        ),
        "duckdb_query_ok": joined_pitch_rows > 0,
    }

    if not all(
        checks[key]
        for key in (
            "non_pa_pitch_preserved",
            "both_sequence_classes_present",
            "identity_issue_preserved",
            "duckdb_query_ok",
        )
    ):
        raise RuntimeError(f"canonical foundation POC failed assertions: {checks}")

    report = {
        "report_schema_version": 1,
        "game_pk": args.game_id,
        "source_asset": args.source_asset,
        "counts": counts,
        "checks": checks,
        "identity_comparison": identity_comparison,
        "artifacts": artifacts,
    }
    (args.report_dir / "canonical_foundation_poc.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    summary = _markdown(report)
    (args.report_dir / "canonical_foundation_poc.md").write_text(
        summary, encoding="utf-8"
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
