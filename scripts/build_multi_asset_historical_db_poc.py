#!/usr/bin/env python
"""Build a three-game historical DB slice from two overlapping MiLB assets."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from datetime import UTC, datetime
import json
from pathlib import Path
import shutil
from typing import Any

import duckdb
import polars as pl

from universal_baseball.canonical_adapters import (
    current_event_semantics_snapshot_id,
    normalize_armstjc_pitch_observations,
    normalize_official_play_sequence_observations,
)
from universal_baseball.canonical_schema import (
    CANONICAL_SCHEMA_VERSION,
    validate_normalization_definition,
    validate_source_snapshot,
)
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.event_semantics_registry import (
    current_event_semantics_frame,
    validate_sequence_semantics_links,
)
from universal_baseball.game_observation import normalize_armstjc_game_observations
from universal_baseball.historical_materialization import write_event_table_by_game_month
from universal_baseball.official import (
    project_official_boxscore,
    project_official_play_by_play,
)
from universal_baseball.official_capture import capture_official_json
from universal_baseball.provenance import NormalizationDefinition, SourceSnapshot
from universal_baseball.quality import quality_issues_from_resolution_conflicts
from universal_baseball.reconciliation import (
    aggregate_pa_batting,
    compare_batting_lines,
)
from universal_baseball.resolution import (
    game_resolution_conflicts,
    pitch_resolution_conflicts,
    resolve_game_observations_across_snapshots,
    resolve_pitch_observations_across_snapshots,
)
from universal_baseball.source_comparison import compare_pitch_source_to_official_pas
from universal_baseball.storage import ParquetArtifact, write_canonical_parquet


BASE_URL = "https://github.com/armstjc/milb-data-repository/releases/download/pbp"
SOURCE_KEY = ["game_pk", "at_bat_number", "pitch_number"]
DEFAULT_LEFT = "2025_3_aaa_pbp.csv"
DEFAULT_RIGHT = "2025_4_aaa_pbp.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--left-asset", default=DEFAULT_LEFT)
    parser.add_argument("--right-asset", default=DEFAULT_RIGHT)
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/historical-db-poc"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/poc/historical-db"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/historical-db-poc"),
    )
    return parser.parse_args()


def _as_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"retrieval timestamp is not timezone-aware: {value}")
    return parsed.astimezone(UTC)


def _armstjc_snapshot(
    *,
    asset: str,
    url: str,
    metadata: dict[str, Any],
) -> SourceSnapshot:
    return SourceSnapshot.build(
        source_name="armstjc_milb_pbp",
        source_role="historical_bootstrap",
        upstream_locator=str(metadata.get("resolved_url") or url),
        upstream_version=asset,
        content_sha256=str(metadata["sha256"]),
        retrieved_at_utc=_as_utc(str(metadata["retrieved_at_utc"])),
        knowledge_available_at_utc=None,
        license_id="MIT",
        raw_object_key=f"quarantine/armstjc/{asset}",
    )


def _normalization(
    snapshot_id: str,
    *,
    name: str,
    version: str = "1",
) -> NormalizationDefinition:
    return NormalizationDefinition.build(
        source_snapshot_id=snapshot_id,
        normalizer_name=name,
        normalizer_version=version,
        canonical_schema_version=CANONICAL_SCHEMA_VERSION,
    )


def _game_date_index(frame: pl.DataFrame) -> dict[int, str]:
    index: dict[int, str] = {}
    for row in frame.select(["game_pk", "game_date"]).unique().to_dicts():
        game_pk = int(float(str(row["game_pk"])))
        game_date = str(row["game_date"])
        current = index.get(game_pk)
        if current is None or game_date < current:
            index[game_pk] = game_date
    return index


def _earliest_game(game_ids: set[int], dates: dict[int, str]) -> int:
    if not game_ids:
        raise RuntimeError("required POC game role has no candidate games")
    return min(game_ids, key=lambda game_id: (dates.get(game_id, "9999-99-99"), game_id))


def _select_games(
    left: pl.DataFrame,
    right: pl.DataFrame,
    overlap_conflicts: pl.DataFrame,
) -> dict[str, int]:
    left_dates = _game_date_index(left)
    right_dates = _game_date_index(right)
    left_ids = set(left_dates)
    right_ids = set(right_dates)
    overlap_ids = left_ids & right_ids

    conflict_ids = (
        set(int(value) for value in overlap_conflicts.get_column("game_pk").unique())
        if not overlap_conflicts.is_empty()
        else set()
    )
    overlap_game = (
        _earliest_game(conflict_ids, {**right_dates, **left_dates})
        if conflict_ids
        else _earliest_game(overlap_ids, {**right_dates, **left_dates})
    )
    return {
        "overlap": overlap_game,
        "left_only": _earliest_game(left_ids - right_ids, left_dates),
        "right_only": _earliest_game(right_ids - left_ids, right_dates),
    }


def _filter_games(frame: pl.DataFrame, game_ids: list[int]) -> pl.DataFrame:
    return frame.filter(
        pl.col("game_pk").cast(pl.Int64, strict=False).is_in(game_ids)
    )


def _official_snapshot(
    *,
    game_id: int,
    endpoint_role: str,
    capture: Any,
    raw_object_key: str,
) -> SourceSnapshot:
    return SourceSnapshot.build(
        source_name="mlb_stats_api",
        source_role=endpoint_role,
        upstream_locator=capture.url,
        upstream_version=capture.endpoint,
        content_sha256=capture.content_sha256,
        retrieved_at_utc=capture.retrieved_at_utc,
        # We cannot prove when a current mutable endpoint first contained this
        # representation. Retrieval time is a conservative knowledge bound.
        knowledge_available_at_utc=capture.retrieved_at_utc,
        raw_object_key=raw_object_key,
    )


def _write_global(
    frame: pl.DataFrame,
    output_dir: Path,
    *,
    table_name: str,
) -> ParquetArtifact:
    return write_canonical_parquet(
        frame,
        output_dir / f"{table_name}.parquet",
        table_name=table_name,
    )


def _artifact_records(artifacts: list[ParquetArtifact]) -> list[dict[str, Any]]:
    return [artifact.as_record() for artifact in artifacts]


def _sql_path(path: Path) -> str:
    return path.as_posix().replace("'", "''")


def _duckdb_verify(output_dir: Path, selected_game_count: int) -> dict[str, Any]:
    game_path = _sql_path(output_dir / "game_consensus.parquet")
    source_path = _sql_path(output_dir / "source_snapshot.parquet")
    normalization_path = _sql_path(output_dir / "normalization_definition.parquet")
    quality_path = _sql_path(output_dir / "quality_issue.parquet")
    pitch_obs_glob = _sql_path(output_dir / "pitch_observation" / "**" / "*.parquet")
    pitch_current_glob = _sql_path(output_dir / "pitch_consensus" / "**" / "*.parquet")
    sequence_glob = _sql_path(
        output_dir / "play_sequence_observation" / "**" / "*.parquet"
    )

    con = duckdb.connect(database=":memory:")
    try:
        con.execute(f"CREATE VIEW games AS SELECT * FROM read_parquet('{game_path}')")
        con.execute(
            f"CREATE VIEW pitch_observations AS SELECT * FROM "
            f"read_parquet('{pitch_obs_glob}', hive_partitioning=true)"
        )
        con.execute(
            f"CREATE VIEW pitch_consensus AS SELECT * FROM "
            f"read_parquet('{pitch_current_glob}', hive_partitioning=true)"
        )
        con.execute(
            f"CREATE VIEW sequences AS SELECT * FROM "
            f"read_parquet('{sequence_glob}', hive_partitioning=true)"
        )
        counts = {
            "source_snapshot": int(
                con.execute(
                    f"SELECT count(*) FROM read_parquet('{source_path}')"
                ).fetchone()[0]
            ),
            "normalization_definition": int(
                con.execute(
                    f"SELECT count(*) FROM read_parquet('{normalization_path}')"
                ).fetchone()[0]
            ),
            "game_consensus": int(con.execute("SELECT count(*) FROM games").fetchone()[0]),
            "pitch_observation": int(
                con.execute("SELECT count(*) FROM pitch_observations").fetchone()[0]
            ),
            "pitch_consensus": int(
                con.execute("SELECT count(*) FROM pitch_consensus").fetchone()[0]
            ),
            "play_sequence_observation": int(
                con.execute("SELECT count(*) FROM sequences").fetchone()[0]
            ),
            "quality_issue": int(
                con.execute(
                    f"SELECT count(*) FROM read_parquet('{quality_path}')"
                ).fetchone()[0]
            ),
        }
        pitch_partition_mismatch = int(
            con.execute(
                """
                SELECT count(*)
                FROM pitch_observations p
                JOIN games g USING (game_pk)
                WHERE p.year <> year(g.official_date)
                   OR p.month <> month(g.official_date)
                """
            ).fetchone()[0]
        )
        consensus_partition_mismatch = int(
            con.execute(
                """
                SELECT count(*)
                FROM pitch_consensus p
                JOIN games g USING (game_pk)
                WHERE p.year <> year(g.official_date)
                   OR p.month <> month(g.official_date)
                """
            ).fetchone()[0]
        )
        sequence_partition_mismatch = int(
            con.execute(
                """
                SELECT count(*)
                FROM sequences s
                JOIN games g USING (game_pk)
                WHERE s.year <> year(g.official_date)
                   OR s.month <> month(g.official_date)
                """
            ).fetchone()[0]
        )
        orphan_pitches = int(
            con.execute(
                "SELECT count(*) FROM pitch_consensus p "
                "LEFT JOIN games g USING (game_pk) WHERE g.game_pk IS NULL"
            ).fetchone()[0]
        )
        orphan_sequences = int(
            con.execute(
                "SELECT count(*) FROM sequences s "
                "LEFT JOIN games g USING (game_pk) WHERE g.game_pk IS NULL"
            ).fetchone()[0]
        )
    finally:
        con.close()

    clean = (
        counts["game_consensus"] == selected_game_count
        and pitch_partition_mismatch == 0
        and consensus_partition_mismatch == 0
        and sequence_partition_mismatch == 0
        and orphan_pitches == 0
        and orphan_sequences == 0
    )
    return {
        "counts": counts,
        "pitch_observation_partition_mismatch_count": pitch_partition_mismatch,
        "pitch_consensus_partition_mismatch_count": consensus_partition_mismatch,
        "play_sequence_partition_mismatch_count": sequence_partition_mismatch,
        "orphan_pitch_consensus_count": orphan_pitches,
        "orphan_play_sequence_count": orphan_sequences,
        "clean": clean,
    }


def main() -> int:
    args = parse_args()
    for path in (args.work_dir, args.output_dir, args.report_dir):
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)

    left_url = f"{BASE_URL}/{args.left_asset}"
    right_url = f"{BASE_URL}/{args.right_asset}"
    left_path = args.work_dir / args.left_asset
    right_path = args.work_dir / args.right_asset
    left_meta = download_file(left_url, left_path, timeout_seconds=180)
    right_meta = download_file(right_url, right_path, timeout_seconds=180)
    left = read_quarantined_csv(left_path)
    right = read_quarantined_csv(right_path)

    left_snapshot = _armstjc_snapshot(
        asset=args.left_asset, url=left_url, metadata=left_meta
    )
    right_snapshot = _armstjc_snapshot(
        asset=args.right_asset, url=right_url, metadata=right_meta
    )
    left_pitch_norm = _normalization(
        left_snapshot.source_snapshot_id,
        name="normalize_armstjc_pitch_observations",
    )
    right_pitch_norm = _normalization(
        right_snapshot.source_snapshot_id,
        name="normalize_armstjc_pitch_observations",
    )
    left_game_norm = _normalization(
        left_snapshot.source_snapshot_id,
        name="normalize_armstjc_game_observations",
    )
    right_game_norm = _normalization(
        right_snapshot.source_snapshot_id,
        name="normalize_armstjc_game_observations",
    )

    # Find the overlap game most likely to exercise a real canonical conflict.
    left_keys = left.select(SOURCE_KEY).unique()
    right_keys = right.select(SOURCE_KEY).unique()
    overlap_keys = left_keys.join(right_keys, on=SOURCE_KEY, how="inner")
    if overlap_keys.is_empty():
        raise RuntimeError("POC source pair unexpectedly has no pitch-key overlap")
    left_overlap = left.join(overlap_keys, on=SOURCE_KEY, how="inner")
    right_overlap = right.join(overlap_keys, on=SOURCE_KEY, how="inner")
    overlap_observations = pl.concat(
        [
            normalize_armstjc_pitch_observations(
                left_overlap,
                source_snapshot_id=left_snapshot.source_snapshot_id,
                normalization_id=left_pitch_norm.normalization_id,
            ),
            normalize_armstjc_pitch_observations(
                right_overlap,
                source_snapshot_id=right_snapshot.source_snapshot_id,
                normalization_id=right_pitch_norm.normalization_id,
            ),
        ],
        how="vertical_relaxed",
    )
    source_pitch_definitions = pl.DataFrame(
        [left_pitch_norm.as_record(), right_pitch_norm.as_record()]
    )
    overlap_resolved = resolve_pitch_observations_across_snapshots(
        overlap_observations,
        source_pitch_definitions,
    )
    overlap_conflicts = pitch_resolution_conflicts(overlap_resolved)
    selected_roles = _select_games(left, right, overlap_conflicts)
    selected_game_ids = list(dict.fromkeys(selected_roles.values()))
    if len(selected_game_ids) != 3:
        raise RuntimeError(f"POC game roles did not resolve to three games: {selected_roles}")

    left_selected = _filter_games(left, selected_game_ids)
    right_selected = _filter_games(right, selected_game_ids)
    source_selected = pl.concat([left_selected, right_selected], how="vertical_relaxed")

    left_pitch_observations = normalize_armstjc_pitch_observations(
        left_selected,
        source_snapshot_id=left_snapshot.source_snapshot_id,
        normalization_id=left_pitch_norm.normalization_id,
    )
    right_pitch_observations = normalize_armstjc_pitch_observations(
        right_selected,
        source_snapshot_id=right_snapshot.source_snapshot_id,
        normalization_id=right_pitch_norm.normalization_id,
    )
    pitch_observations = pl.concat(
        [left_pitch_observations, right_pitch_observations], how="vertical_relaxed"
    )
    pitch_consensus = resolve_pitch_observations_across_snapshots(
        pitch_observations,
        source_pitch_definitions,
    )
    pitch_conflicts = pitch_resolution_conflicts(pitch_consensus)

    left_game_observations = normalize_armstjc_game_observations(
        left_selected,
        source_snapshot_id=left_snapshot.source_snapshot_id,
        normalization_id=left_game_norm.normalization_id,
    )
    right_game_observations = normalize_armstjc_game_observations(
        right_selected,
        source_snapshot_id=right_snapshot.source_snapshot_id,
        normalization_id=right_game_norm.normalization_id,
    )
    game_observations = pl.concat(
        [left_game_observations, right_game_observations], how="vertical_relaxed"
    )
    source_game_definitions = pl.DataFrame(
        [left_game_norm.as_record(), right_game_norm.as_record()]
    )
    game_consensus = resolve_game_observations_across_snapshots(
        game_observations,
        source_game_definitions,
    )
    if game_consensus.get_column("official_date").null_count() != 0:
        raise RuntimeError("POC has unresolved game date; cannot partition by event time")
    game_conflicts = game_resolution_conflicts(game_consensus)

    detected_at = datetime.now(UTC)
    pitch_issues = quality_issues_from_resolution_conflicts(
        pitch_consensus,
        entity_type="pitch",
        detected_at_utc=detected_at,
    )
    game_issues = quality_issues_from_resolution_conflicts(
        game_consensus,
        entity_type="game",
        detected_at_utc=detected_at,
    )
    quality_issues = pl.concat([game_issues, pitch_issues], how="vertical_relaxed")

    source_snapshots: list[SourceSnapshot] = [left_snapshot, right_snapshot]
    normalization_definitions: list[NormalizationDefinition] = [
        left_pitch_norm,
        right_pitch_norm,
        left_game_norm,
        right_game_norm,
    ]
    sequence_frames: list[pl.DataFrame] = []
    official_pa_frames: list[pl.DataFrame] = []
    official_pitch_frames: list[pl.DataFrame] = []
    official_boxscore_frames: list[pl.DataFrame] = []
    official_capture_records: list[dict[str, Any]] = []
    semantics_id = current_event_semantics_snapshot_id()

    for game_id in selected_game_ids:
        pbp_capture = capture_official_json(f"game/{game_id}/playByPlay")
        pbp_raw = args.work_dir / "official" / f"game-{game_id}-playByPlay.json"
        pbp_capture.write_raw(pbp_raw)
        pbp_snapshot = _official_snapshot(
            game_id=game_id,
            endpoint_role="official_play_by_play_authority",
            capture=pbp_capture,
            raw_object_key=f"quarantine/mlb/game-{game_id}-playByPlay.json",
        )
        pbp_normalization = _normalization(
            pbp_snapshot.source_snapshot_id,
            name="normalize_official_play_sequence_observations",
        )
        if not isinstance(pbp_capture.data, Mapping):
            raise RuntimeError(f"official PBP game {game_id} is not a JSON object")
        sequence_frames.append(
            normalize_official_play_sequence_observations(
                game_id,
                pbp_capture.data,
                source_snapshot_id=pbp_snapshot.source_snapshot_id,
                normalization_id=pbp_normalization.normalization_id,
                event_semantics_snapshot_id=semantics_id,
            )
        )
        pa_frame, official_pitch_frame = project_official_play_by_play(
            game_id,
            pbp_capture.data,
        )
        official_pa_frames.append(pa_frame)
        official_pitch_frames.append(official_pitch_frame)
        source_snapshots.append(pbp_snapshot)
        normalization_definitions.append(pbp_normalization)
        official_capture_records.append(
            {
                "game_pk": game_id,
                "endpoint": pbp_capture.endpoint,
                "sha256": pbp_capture.content_sha256,
                "bytes": len(pbp_capture.raw_bytes),
            }
        )

        box_capture = capture_official_json(f"game/{game_id}/boxscore")
        box_raw = args.work_dir / "official" / f"game-{game_id}-boxscore.json"
        box_capture.write_raw(box_raw)
        box_snapshot = _official_snapshot(
            game_id=game_id,
            endpoint_role="official_boxscore_reconciliation_authority",
            capture=box_capture,
            raw_object_key=f"quarantine/mlb/game-{game_id}-boxscore.json",
        )
        if not isinstance(box_capture.data, Mapping):
            raise RuntimeError(f"official boxscore game {game_id} is not a JSON object")
        official_boxscore_frames.append(
            project_official_boxscore(game_id, box_capture.data)
        )
        source_snapshots.append(box_snapshot)
        official_capture_records.append(
            {
                "game_pk": game_id,
                "endpoint": box_capture.endpoint,
                "sha256": box_capture.content_sha256,
                "bytes": len(box_capture.raw_bytes),
            }
        )

    play_sequences = pl.concat(sequence_frames, how="vertical_relaxed")
    event_semantics = current_event_semantics_frame()
    validate_sequence_semantics_links(play_sequences, event_semantics)

    official_pas = pl.concat(official_pa_frames, how="vertical_relaxed")
    official_pitch_events = pl.concat(official_pitch_frames, how="vertical_relaxed")
    official_boxscores = pl.concat(official_boxscore_frames, how="vertical_relaxed")
    pitch_structure = compare_pitch_source_to_official_pas(
        source_selected,
        official_pas,
        official_pitch_events,
    )
    derived_batting = aggregate_pa_batting(official_pas)
    batting_reconciliation = compare_batting_lines(derived_batting, official_boxscores)

    if pitch_structure["official_only_positive_pitch_pa_count"] != 0:
        raise RuntimeError("POC has unexplained official positive-pitch PA gaps")
    if pitch_structure["pitch_count_mismatch_pa_count"] != 0:
        raise RuntimeError("POC has source-vs-official pitch-count disagreement")
    if not batting_reconciliation["certification_clean"]:
        raise RuntimeError("POC official PA outcomes do not reconcile to boxscore")

    source_snapshot_frame = validate_source_snapshot(
        pl.DataFrame([snapshot.as_record() for snapshot in source_snapshots])
    )
    normalization_frame = validate_normalization_definition(
        pl.DataFrame(
            [definition.as_record() for definition in normalization_definitions]
        )
    )

    artifacts: list[ParquetArtifact] = []
    artifacts.append(
        _write_global(source_snapshot_frame, args.output_dir, table_name="source_snapshot")
    )
    artifacts.append(
        _write_global(
            normalization_frame,
            args.output_dir,
            table_name="normalization_definition",
        )
    )
    artifacts.append(
        _write_global(game_observations, args.output_dir, table_name="game_observation")
    )
    artifacts.append(
        _write_global(game_consensus, args.output_dir, table_name="game_consensus")
    )
    artifacts.append(
        _write_global(quality_issues, args.output_dir, table_name="quality_issue")
    )
    artifacts.append(
        _write_global(event_semantics, args.output_dir, table_name="event_semantics")
    )
    artifacts.extend(
        write_event_table_by_game_month(
            pitch_observations,
            game_consensus,
            args.output_dir / "pitch_observation",
            table_name="pitch_observation",
        )
    )
    artifacts.extend(
        write_event_table_by_game_month(
            pitch_consensus,
            game_consensus,
            args.output_dir / "pitch_consensus",
            table_name="pitch_consensus",
        )
    )
    artifacts.extend(
        write_event_table_by_game_month(
            play_sequences,
            game_consensus,
            args.output_dir / "play_sequence_observation",
            table_name="play_sequence_observation",
        )
    )

    duckdb_verification = _duckdb_verify(args.output_dir, len(selected_game_ids))
    if not duckdb_verification["clean"]:
        raise RuntimeError("DuckDB round-trip or event-date partition verification failed")

    payload = {
        "poc": "multi_asset_historical_db",
        "left_asset": args.left_asset,
        "right_asset": args.right_asset,
        "selected_game_roles": selected_roles,
        "selected_game_ids": selected_game_ids,
        "source_asset_sha256": {
            args.left_asset: left_meta["sha256"],
            args.right_asset: right_meta["sha256"],
        },
        "overlap_pitch_key_count_in_full_assets": overlap_keys.height,
        "overlap_canonical_conflict_pitch_count_in_full_assets": overlap_conflicts.height,
        "poc_counts": {
            "source_snapshot": source_snapshot_frame.height,
            "normalization_definition": normalization_frame.height,
            "game_observation": game_observations.height,
            "game_consensus": game_consensus.height,
            "game_conflict": game_conflicts.height,
            "pitch_observation": pitch_observations.height,
            "pitch_consensus": pitch_consensus.height,
            "pitch_conflict": pitch_conflicts.height,
            "play_sequence_observation": play_sequences.height,
            "quality_issue": quality_issues.height,
        },
        "pitch_structure": {
            "official_pa_count": pitch_structure["official_pa_count"],
            "shared_pa_count": pitch_structure["shared_pa_count"],
            "official_only_zero_pitch_pa_count": pitch_structure[
                "official_only_zero_pitch_pa_count"
            ],
            "official_only_positive_pitch_pa_count": pitch_structure[
                "official_only_positive_pitch_pa_count"
            ],
            "pitch_count_mismatch_pa_count": pitch_structure[
                "pitch_count_mismatch_pa_count"
            ],
            "source_only_sequence_count": pitch_structure["source_only_pa_count"],
        },
        "batting_reconciliation": {
            "shared_line_count": batting_reconciliation["shared_line_count"],
            "exact_match_line_count": batting_reconciliation["exact_match_line_count"],
            "mismatch_line_count": batting_reconciliation["mismatch_line_count"],
            "certification_clean": batting_reconciliation["certification_clean"],
        },
        "official_capture": official_capture_records,
        "duckdb_verification": duckdb_verification,
        "artifacts": _artifact_records(artifacts),
    }
    (args.report_dir / "historical_db_poc.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# Multi-asset historical database POC",
        "",
        f"- Source assets: `{args.left_asset}` + `{args.right_asset}`",
        f"- Selected roles: {selected_roles}",
        f"- Full-asset overlapping pitch keys: {overlap_keys.height:,}",
        f"- Full-overlap canonical pitch conflicts: {overlap_conflicts.height:,}",
        f"- POC source snapshots: {source_snapshot_frame.height:,}",
        f"- POC normalization definitions: {normalization_frame.height:,}",
        f"- Resolved games: {game_consensus.height:,}",
        f"- Canonical pitch observations: {pitch_observations.height:,}",
        f"- Resolved canonical pitches: {pitch_consensus.height:,}",
        f"- Pitch consensus conflicts in POC: {pitch_conflicts.height:,}",
        f"- Game consensus conflicts in POC: {game_conflicts.height:,}",
        f"- Canonical quality issues: {quality_issues.height:,}",
        f"- Official play-sequence observations: {play_sequences.height:,}",
        f"- Official PA batting lines reconciled exactly: {batting_reconciliation['exact_match_line_count']}/{batting_reconciliation['shared_line_count']}",
        f"- Unexplained positive-pitch official PA gaps: {pitch_structure['official_only_positive_pitch_pa_count']}",
        f"- Pitch-count mismatches: {pitch_structure['pitch_count_mismatch_pa_count']}",
        f"- DuckDB/event-partition verification clean: {duckdb_verification['clean']}",
        "",
        "Raw upstream files remain in quarantine and are not included in the report artifact. Canonical event tables are partitioned by resolved game date, not release filename month. Official play-by-play and boxscore source snapshots are checksummed from the exact HTTP response bytes.",
        "",
    ]
    (args.report_dir / "historical_db_poc.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
