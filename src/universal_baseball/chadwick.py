"""Versioned Chadwick Register loading and MLBAM coverage diagnostics.

The project reuses Chadwick's public authority file rather than attempting to
resolve baseball identities from names. MLBAM remains the canonical modern event
identifier; this module only loads a pinned Chadwick snapshot for cross-system
enrichment and coverage certification.
"""

from __future__ import annotations

from collections import Counter
from datetime import date
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


def build_mlbam_age_as_of(
    people: pl.DataFrame,
    mlbam_ids: Iterable[int],
    *,
    as_of_date: date,
) -> pl.DataFrame:
    """Derive exact age at one cutoff from Chadwick DOB for requested MLBAM IDs.

    Age is a time-varying model feature and is therefore derived from immutable
    date of birth plus the explicit snapshot cutoff; a mutable current-age field
    is never stored. Complete but invalid dates, future dates, and duplicate
    Chadwick rows for a requested MLBAM ID fail closed. Partial DOBs are retained
    as missing exact age rather than being imputed to January 1 or another
    invented date.
    """

    required = {"key_mlbam", "birth_year", "birth_month", "birth_day"}
    missing = sorted(required - set(people.columns))
    if missing:
        raise ValueError(f"Chadwick people frame missing age fields: {missing}")

    requested = sorted({int(value) for value in mlbam_ids})
    if not requested:
        return pl.DataFrame(
            schema={
                "player_id": pl.Int64,
                "birth_date": pl.Date,
                "age_years": pl.Float64,
                "age_source_status": pl.String,
            }
        )

    selected = people.filter(pl.col("key_mlbam").is_in(requested))
    duplicates = (
        selected.group_by("key_mlbam")
        .len()
        .filter(pl.col("len") > 1)
        .sort("key_mlbam")
    )
    if not duplicates.is_empty():
        ids = [int(value) for value in duplicates.get_column("key_mlbam").to_list()]
        raise ValueError(f"Chadwick has duplicate requested MLBAM IDs: {ids}")

    by_id = {
        int(row["key_mlbam"]): row
        for row in selected.select(
            "key_mlbam", "birth_year", "birth_month", "birth_day"
        ).iter_rows(named=True)
    }
    rows: list[dict[str, object]] = []
    for player_id in requested:
        source = by_id.get(player_id)
        if source is None:
            rows.append(
                {
                    "player_id": player_id,
                    "birth_date": None,
                    "age_years": None,
                    "age_source_status": "missing_chadwick_identity",
                }
            )
            continue

        parts = (
            source["birth_year"],
            source["birth_month"],
            source["birth_day"],
        )
        present = [value is not None for value in parts]
        if not any(present):
            rows.append(
                {
                    "player_id": player_id,
                    "birth_date": None,
                    "age_years": None,
                    "age_source_status": "missing_birth_date",
                }
            )
            continue
        if not all(present):
            rows.append(
                {
                    "player_id": player_id,
                    "birth_date": None,
                    "age_years": None,
                    "age_source_status": "partial_birth_date",
                }
            )
            continue

        try:
            birth_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Chadwick has invalid complete birth date for MLBAM {player_id}: {parts}"
            ) from exc
        if birth_date > as_of_date:
            raise ValueError(
                f"Chadwick birth date is after as-of date for MLBAM {player_id}: "
                f"birth={birth_date.isoformat()}, as_of={as_of_date.isoformat()}"
            )

        age_years = (as_of_date - birth_date).days / 365.2425
        rows.append(
            {
                "player_id": player_id,
                "birth_date": birth_date,
                "age_years": float(age_years),
                "age_source_status": "exact_birth_date",
            }
        )

    return pl.DataFrame(
        rows,
        schema={
            "player_id": pl.Int64,
            "birth_date": pl.Date,
            "age_years": pl.Float64,
            "age_source_status": pl.String,
        },
    ).sort("player_id")


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
