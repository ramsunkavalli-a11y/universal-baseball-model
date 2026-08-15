from __future__ import annotations

from pathlib import Path

import duckdb
import polars as pl

from universal_baseball.canonical_schema import validate_pitch_observation
from universal_baseball.storage import schema_fingerprint, write_canonical_parquet


def _pitch_frame() -> pl.DataFrame:
    return validate_pitch_observation(
        pl.DataFrame(
            [
                {
                    "normalization_id": "a" * 64,
                    "source_snapshot_id": "b" * 64,
                    "game_pk": 100,
                    "at_bat_index": 1,
                    "pitch_number": 1,
                    "payload_hash": "c" * 64,
                    "duplicate_row_count": 2,
                    "source_batter_mlbam_id": 10,
                    "source_pitcher_mlbam_id": 20,
                    "pitch_code": "X",
                    "is_in_play": True,
                    "bb_type": "line_drive",
                    "hc_x": 120.5,
                    "hc_y": 90.25,
                },
                {
                    "normalization_id": "a" * 64,
                    "source_snapshot_id": "b" * 64,
                    "game_pk": 100,
                    "at_bat_index": 2,
                    "pitch_number": 1,
                    "payload_hash": "d" * 64,
                    "duplicate_row_count": 1,
                    "source_batter_mlbam_id": 11,
                    "source_pitcher_mlbam_id": 20,
                    "pitch_code": "S",
                    "is_in_play": False,
                },
            ]
        )
    )


def test_canonical_parquet_round_trip_is_polars_and_duckdb_queryable(tmp_path: Path) -> None:
    frame = _pitch_frame()
    path = tmp_path / "pitch_observation.parquet"

    artifact = write_canonical_parquet(
        frame,
        path,
        table_name="pitch_observation",
    )

    assert path.exists()
    assert artifact.row_count == 2
    assert artifact.file_size_bytes > 0
    assert len(artifact.file_sha256) == 64
    assert artifact.schema_sha256 == schema_fingerprint(frame.schema)

    reloaded = pl.read_parquet(path)
    assert reloaded.schema == frame.schema
    assert reloaded.to_dicts() == frame.to_dicts()

    with duckdb.connect(":memory:") as connection:
        row = connection.execute(
            "SELECT count(*) AS n, sum(duplicate_row_count) AS raw_rows "
            "FROM read_parquet(?)",
            [str(path)],
        ).fetchone()
    assert row == (2, 3)


def test_write_is_atomic_and_requires_parquet_suffix(tmp_path: Path) -> None:
    frame = _pitch_frame()
    path = tmp_path / "nested" / "pitch.parquet"
    write_canonical_parquet(frame, path, table_name="pitch_observation")
    assert path.exists()
    assert not list(path.parent.glob("*.tmp"))

    try:
        write_canonical_parquet(frame, tmp_path / "pitch.csv", table_name="pitch")
    except ValueError as exc:
        assert ".parquet" in str(exc)
    else:
        raise AssertionError("non-Parquet canonical path should fail")
