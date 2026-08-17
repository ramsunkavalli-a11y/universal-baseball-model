from __future__ import annotations

import csv
from datetime import date
from io import StringIO
from pathlib import Path
from zipfile import ZipFile

import polars as pl
import pytest

from universal_baseball.chadwick import (
    CROSSWALK_COLUMNS,
    build_mlbam_age_as_of,
    profile_mlbam_coverage,
    read_chadwick_people_archive,
)


def _row(**values: object) -> dict[str, object]:
    return {column: values.get(column, "") for column in CROSSWALK_COLUMNS}


def _csv_bytes(rows: list[dict[str, object]]) -> bytes:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=list(CROSSWALK_COLUMNS))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def _write_archive(path: Path) -> None:
    hex_shards = "0123456789abcdef"
    with ZipFile(path, "w") as archive:
        for index, shard in enumerate(hex_shards):
            rows: list[dict[str, object]] = []
            if index == 0:
                rows.extend(
                    [
                        _row(
                            key_uuid="uuid-minor-only",
                            key_person="minor001",
                            key_mlbam=900001,
                            name_last="Prospect",
                            name_first="New",
                            pro_played_first=2026,
                            pro_played_last=2026,
                        ),
                        _row(
                            key_uuid="uuid-major",
                            key_person="major001",
                            key_mlbam=500001,
                            key_retro="major001",
                            key_bbref="major01",
                            key_fangraphs="12345",
                            name_last="Major",
                            name_first="Player",
                            pro_played_first=2018,
                            pro_played_last=2026,
                            mlb_played_first=2020,
                            mlb_played_last=2026,
                        ),
                    ]
                )
            elif index == 1:
                rows.append(
                    _row(
                        key_uuid="uuid-duplicate",
                        key_person="dupe0001",
                        key_mlbam=500001,
                        name_last="Duplicate",
                        name_first="Identity",
                    )
                )
            else:
                rows.append(
                    _row(
                        key_uuid=f"uuid-{shard}",
                        key_person=f"person{shard}",
                        name_last="NoMlbam",
                        name_first=shard,
                    )
                )

            archive.writestr(
                f"register-test/data/people-{shard}.csv",
                _csv_bytes(rows),
            )


def test_chadwick_loader_keeps_minor_only_mlbam_rows(tmp_path: Path) -> None:
    archive_path = tmp_path / "register.zip"
    _write_archive(archive_path)

    people = read_chadwick_people_archive(archive_path)

    minor = people.filter(people["key_mlbam"] == 900001).to_dicts()[0]
    assert minor["key_uuid"] == "uuid-minor-only"
    assert minor["pro_played_first"] == 2026
    assert minor["mlb_played_first"] is None


def test_chadwick_coverage_reports_missing_and_duplicate_mlbam_ids(tmp_path: Path) -> None:
    archive_path = tmp_path / "register.zip"
    _write_archive(archive_path)
    people = read_chadwick_people_archive(archive_path)

    result = profile_mlbam_coverage(people, [500001, 900001, 999999])

    assert result["requested_mlbam_id_count"] == 3
    assert result["matched_mlbam_id_count"] == 2
    assert result["missing_mlbam_ids"] == [999999]
    assert result["duplicate_requested_mlbam_ids"] == {500001: 2}
    assert result["coverage_rate"] == 2 / 3


def test_age_as_of_uses_exact_dob_and_does_not_impute_partial_dates() -> None:
    people = pl.DataFrame(
        {
            "key_mlbam": [101, 102, 103],
            "birth_year": [2000, 2001, None],
            "birth_month": [2, None, None],
            "birth_day": [29, None, None],
        },
        schema_overrides={
            "key_mlbam": pl.Int64,
            "birth_year": pl.Int64,
            "birth_month": pl.Int64,
            "birth_day": pl.Int64,
        },
    )

    result = build_mlbam_age_as_of(
        people,
        [101, 102, 103, 999],
        as_of_date=date(2021, 3, 1),
    ).to_dicts()

    exact = result[0]
    assert exact["player_id"] == 101
    assert exact["birth_date"] == date(2000, 2, 29)
    assert exact["age_source_status"] == "exact_birth_date"
    assert exact["age_years"] == pytest.approx(
        (date(2021, 3, 1) - date(2000, 2, 29)).days / 365.2425
    )

    assert result[1]["age_source_status"] == "partial_birth_date"
    assert result[1]["birth_date"] is None
    assert result[1]["age_years"] is None
    assert result[2]["age_source_status"] == "missing_birth_date"
    assert result[3]["age_source_status"] == "missing_chadwick_identity"


def test_age_as_of_fails_closed_on_duplicate_requested_mlbam() -> None:
    people = pl.DataFrame(
        {
            "key_mlbam": [101, 101],
            "birth_year": [2000, 2000],
            "birth_month": [1, 1],
            "birth_day": [2, 2],
        }
    )
    with pytest.raises(ValueError, match="duplicate requested MLBAM IDs"):
        build_mlbam_age_as_of(people, [101], as_of_date=date(2021, 8, 1))


def test_age_as_of_fails_closed_on_invalid_complete_or_future_birth_date() -> None:
    invalid = pl.DataFrame(
        {
            "key_mlbam": [101],
            "birth_year": [2000],
            "birth_month": [2],
            "birth_day": [30],
        }
    )
    with pytest.raises(ValueError, match="invalid complete birth date"):
        build_mlbam_age_as_of(invalid, [101], as_of_date=date(2021, 8, 1))

    future = pl.DataFrame(
        {
            "key_mlbam": [102],
            "birth_year": [2022],
            "birth_month": [1],
            "birth_day": [1],
        }
    )
    with pytest.raises(ValueError, match="birth date is after as-of date"):
        build_mlbam_age_as_of(future, [102], as_of_date=date(2021, 8, 1))
