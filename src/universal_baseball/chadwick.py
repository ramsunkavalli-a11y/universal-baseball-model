"""Versioned Chadwick Register loading and MLBAM coverage diagnostics.

The project reuses Chadwick's public authority file rather than attempting to
resolve baseball identities from names. MLBAM remains the canonical modern event
identifier; this module only loads a pinned Chadwick snapshot for cross-system
enrichment and coverage certification.
"""

from __future__ import annotations

from collections import Counter
from io import BytesIO
from pathlib import Path
import re
from typing import Iterable, Any
from zipfile import ZipFile

import polars as pl


CHADWICK_REPOSITORY = "chadwickbureau/register"
# Public Register update dated 2026-08-02. Pinning the commit makes the first
# identity audit reproducible even after the public master branch advances.
CHADWICK_SNAPSHOT_SHA = "2e8e73355f9c77b963115377bd98c784cfeec10f"
CHADWICK_ARCHIVE_URL = (
    "https://github.com/chadwickbureau/register/archive/"
    f"{CHADWICK_SNAPSHOT_SHA}.zip"
)

PEOPLE_FILE_PATTERN = re.compile(r"/data/people-[0-9a-f]\.csv$")
EXPECTED_PEOPLE_SHARDS = 16

CROSSWALK_COLUMNS = (
    "key_uuid",
    "key_person",
    "key_mlbam",
    "key_retro",
    "key_bbref",
    "key_bbref_minors",
    "key_fangraphs",
    "name_last",
    "name_first",
    "birth_year",
    "birth_month",
    "birth_day",
    "pro_played_first",
    "pro_played_last",
    "mlb_played_first",
    "mlb_played_last",
)

STRING_COLUMNS = (
    "key_uuid",
    "key_person",
    "key_retro",
    "key_bbref",
    "key_bbref_minors",
    "key_fangraphs",
    "name_last",
    "name_first",
)


def _people_members(archive: ZipFile) -> list[str]:
    members = sorted(
        member
        for member in archive.namelist()
        if PEOPLE_FILE_PATTERN.search(member)
    )
    if len(members) != EXPECTED_PEOPLE_SHARDS:
        raise ValueError(
            "unexpected Chadwick people-shard count: "
            f"expected {EXPECTED_PEOPLE_SHARDS}, observed {len(members)}"
        )
    return members


def read_chadwick_people_archive(path: Path) -> pl.DataFrame:
    """Read all public Chadwick people shards from one pinned repository ZIP.

    Unlike pybaseball's current player lookup, this function intentionally does
    **not** filter the Register to people with major-league identifiers. That
    would structurally remove the very minor-league/DSL players this project must
    retain.
    """

    frames: list[pl.DataFrame] = []
    with ZipFile(path) as archive:
        for member in _people_members(archive):
            frame = pl.read_csv(
                BytesIO(archive.read(member)),
                infer_schema_length=10_000,
                null_values=["", "NA"],
                schema_overrides={column: pl.String for column in STRING_COLUMNS},
            )
            missing = sorted(set(CROSSWALK_COLUMNS) - set(frame.columns))
            if missing:
                raise ValueError(
                    f"Chadwick shard {member!r} missing required columns: {missing}"
                )
            frames.append(frame.select(list(CROSSWALK_COLUMNS)))

    people = pl.concat(frames, how="vertical_relaxed")
    return people.with_columns(
        [
            pl.col("key_mlbam").cast(pl.Int64, strict=False),
            pl.col("birth_year").cast(pl.Int64, strict=False),
            pl.col("birth_month").cast(pl.Int64, strict=False),
            pl.col("birth_day").cast(pl.Int64, strict=False),
            pl.col("pro_played_first").cast(pl.Int64, strict=False),
            pl.col("pro_played_last").cast(pl.Int64, strict=False),
            pl.col("mlb_played_first").cast(pl.Int64, strict=False),
            pl.col("mlb_played_last").cast(pl.Int64, strict=False),
        ]
    )


def mlbam_crosswalk(people: pl.DataFrame) -> pl.DataFrame:
    """Return Chadwick rows that can enrich a structured MLBAM identity."""

    if "key_mlbam" not in people.columns:
        raise ValueError("Chadwick people frame missing key_mlbam")
    return people.filter(pl.col("key_mlbam").is_not_null())


def profile_mlbam_coverage(
    people: pl.DataFrame,
    mlbam_ids: Iterable[int],
) -> dict[str, Any]:
    """Measure pinned-Chadwick coverage for observed structured MLBAM IDs."""

    requested = sorted({int(value) for value in mlbam_ids})
    crosswalk = mlbam_crosswalk(people)

    id_counts: Counter[int] = Counter(
        int(value) for value in crosswalk.get_column("key_mlbam").to_list()
    )
    duplicate_ids = {
        mlbam_id: count
        for mlbam_id, count in sorted(id_counts.items())
        if count > 1
    }

    requested_set = set(requested)
    matched = sorted(requested_set & set(id_counts))
    missing = sorted(requested_set - set(id_counts))

    requested_rows = crosswalk.filter(pl.col("key_mlbam").is_in(requested))
    duplicate_requested = {
        mlbam_id: duplicate_ids[mlbam_id]
        for mlbam_id in matched
        if mlbam_id in duplicate_ids
    }

    return {
        "snapshot_sha": CHADWICK_SNAPSHOT_SHA,
        "people_row_count": people.height,
        "mlbam_crosswalk_row_count": crosswalk.height,
        "unique_mlbam_id_count": len(id_counts),
        "duplicate_mlbam_id_count": len(duplicate_ids),
        "duplicate_mlbam_ids": duplicate_ids,
        "requested_mlbam_id_count": len(requested),
        "matched_mlbam_id_count": len(matched),
        "missing_mlbam_id_count": len(missing),
        "coverage_rate": len(matched) / len(requested) if requested else None,
        "matched_mlbam_ids": matched,
        "missing_mlbam_ids": missing,
        "duplicate_requested_mlbam_ids": duplicate_requested,
        "matched_rows": requested_rows.sort("key_mlbam").to_dicts(),
    }
