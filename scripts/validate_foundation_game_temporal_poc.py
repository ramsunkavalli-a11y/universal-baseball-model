#!/usr/bin/env python
"""Add game-grain and temporal-cutoff validation to the foundation POC."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, time
import json
from pathlib import Path

import duckdb
import polars as pl

from universal_baseball.canonical_schema import validate_provenance_links
from universal_baseball.certification import read_quarantined_csv
from universal_baseball.game_observation import (
    normalize_armstjc_game_observations,
    validate_unique_resolved_game_metadata,
)
from universal_baseball.storage import write_canonical_parquet
from universal_baseball.temporal_views import (
    retrospective_event_cutoff,
    vintage_information_set,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-id", type=int, default=743157)
    parser.add_argument(
        "--source-file",
        type=Path,
        default=Path("data/quarantine/foundation-poc/2023_8_rk_pbp.csv"),
    )
    parser.add_argument(
        "--canonical-dir",
        type=Path,
        default=Path("data/canonical/foundation-poc"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/foundation-poc"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_snapshots = pl.read_parquet(args.canonical_dir / "source_snapshot.parquet")
    normalizations = pl.read_parquet(
        args.canonical_dir / "normalization_definition.parquet"
    )
    pitches = pl.read_parquet(args.canonical_dir / "pitch_observation.parquet")
    sequences = pl.read_parquet(
        args.canonical_dir / "play_sequence_observation.parquet"
    )

    armstjc_source = source_snapshots.filter(
        pl.col("source_name") == "armstjc_milb_pbp"
    )
    if armstjc_source.height != 1:
        raise RuntimeError("foundation POC must contain exactly one armstjc source snapshot")
    source_snapshot_id = armstjc_source.get_column("source_snapshot_id")[0]
    armstjc_normalization = normalizations.filter(
        pl.col("source_snapshot_id") == source_snapshot_id
    )
    if armstjc_normalization.height != 1:
        raise RuntimeError(
            "foundation POC must contain exactly one normalization for armstjc snapshot"
        )
    normalization_id = armstjc_normalization.get_column("normalization_id")[0]

    raw = read_quarantined_csv(args.source_file).filter(
        pl.col("game_pk").cast(pl.String) == str(args.game_id)
    )
    games = normalize_armstjc_game_observations(
        raw,
        source_snapshot_id=source_snapshot_id,
        normalization_id=normalization_id,
    )
    validate_unique_resolved_game_metadata(games)
    validate_provenance_links(
        games,
        normalizations,
        source_snapshots,
        table_name="game_observation",
    )

    artifact = write_canonical_parquet(
        games,
        args.canonical_dir / "game_observation.parquet",
        table_name="game_observation",
    )
    resolved_games = games.select(["game_pk", "official_date"])
    event_date = games.get_column("official_date")[0]
    event_cutoff = datetime.combine(event_date, time.max, tzinfo=UTC)

    pitch_event_eligible = retrospective_event_cutoff(
        pitches,
        resolved_games,
        cutoff=event_date,
    )
    sequence_event_eligible = retrospective_event_cutoff(
        sequences,
        resolved_games,
        cutoff=event_date,
    )
    strict_vintage_pitch = vintage_information_set(
        pitches,
        resolved_games,
        source_snapshots,
        cutoff=event_cutoff,
    )

    # The source snapshot was captured in 2026, and its exact 2023 publication
    # vintage is not established in this POC. A strict 2023 vintage view must
    # therefore be empty rather than pretending current corrected history was
    # literally available that day.
    if strict_vintage_pitch.height != 0:
        raise RuntimeError(
            "strict vintage POC unexpectedly admitted observations without "
            "historical knowledge_available_at_utc"
        )
    if pitch_event_eligible.height != pitches.height:
        raise RuntimeError("event cutoff on game date should retain all POC pitches")
    if sequence_event_eligible.height != sequences.height:
        raise RuntimeError("event cutoff on game date should retain all POC sequences")

    with duckdb.connect(":memory:") as connection:
        joined = connection.execute(
            "SELECT count(*) FROM read_parquet(?) p "
            "JOIN read_parquet(?) g USING (game_pk)",
            [
                str(args.canonical_dir / "pitch_observation.parquet"),
                str(args.canonical_dir / "game_observation.parquet"),
            ],
        ).fetchone()[0]
    if int(joined) != pitches.height:
        raise RuntimeError("DuckDB pitch→game join lost or multiplied POC rows")

    payload = {
        "report_schema_version": 1,
        "game_pk": args.game_id,
        "official_date": str(event_date),
        "normalized_level": games.get_column("normalized_level")[0],
        "league_name": games.get_column("league_name")[0],
        "pitch_observation_count": pitches.height,
        "play_sequence_observation_count": sequences.height,
        "retrospective_event_cutoff_pitch_count": pitch_event_eligible.height,
        "retrospective_event_cutoff_sequence_count": sequence_event_eligible.height,
        "strict_vintage_pitch_count_at_event_date": strict_vintage_pitch.height,
        "duckdb_pitch_game_join_count": int(joined),
        "game_artifact": artifact.as_record(),
    }
    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / "game_temporal_poc.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    markdown = "\n".join(
        [
            "# Foundation game / temporal validation",
            "",
            f"- Game: `{args.game_id}`",
            f"- Official date: `{event_date}`",
            f"- Normalized level: `{payload['normalized_level']}`",
            f"- League: `{payload['league_name']}`",
            f"- Pitch observations retained at event cutoff: {pitch_event_eligible.height}/{pitches.height}",
            f"- Sequence observations retained at event cutoff: {sequence_event_eligible.height}/{sequences.height}",
            f"- Pitch observations eligible for strict 2023 vintage view: {strict_vintage_pitch.height}",
            f"- DuckDB pitch→game rows: {joined}",
            "",
            "The empty strict-vintage result is intentional: the exact 2023 public source vintage is not established, so the POC refuses to manufacture historical knowledge timing.",
            "",
        ]
    )
    (args.report_dir / "game_temporal_poc.md").write_text(
        markdown, encoding="utf-8"
    )
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
