from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from zipfile import ZipFile

from universal_baseball.chadwick import (
    CROSSWALK_COLUMNS,
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
