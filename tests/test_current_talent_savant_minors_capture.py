from datetime import date
from pathlib import Path
import sys

import polars as pl
import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from capture_current_talent_savant_minors_tracking import (  # noqa: E402
    _certified_date_bounds,
    _validate_response_csv,
)


def test_certified_date_bounds_span_all_milb_summary_files(tmp_path) -> None:
    pl.DataFrame(
        {"game_date": ["2022-04-05", "2022-07-01"]}
    ).write_parquet(tmp_path / "current_talent_game_summary_2022_aaa.parquet")
    pl.DataFrame(
        {"game_date": ["2022-05-01", "2022-09-28"]}
    ).write_parquet(tmp_path / "current_talent_game_summary_2022_fsl.parquet")

    start, end = _certified_date_bounds(tmp_path, 2022)

    assert start == date(2022, 4, 5)
    assert end == date(2022, 9, 28)


def test_response_validator_requires_canonical_source_fields() -> None:
    content = (
        "game_date,game_pk,batter,at_bat_number,pitch_number,events,type,des,description,"
        "bb_type,launch_speed,launch_angle\n"
        "2022-06-01,1,10,1,3,single,X,Batter singles.,hit_into_play,line_drive,99.0,18.0\n"
    ).encode()

    rows, columns = _validate_response_csv(content, request_url="https://example.test")

    assert rows == 1
    assert columns == 12


def test_response_validator_fails_closed_on_html_or_schema_drift() -> None:
    with pytest.raises(ValueError, match="not readable CSV|missing fields"):
        _validate_response_csv(b"<html>error</html>", request_url="https://example.test")

    incomplete = b"game_date,game_pk\n2022-06-01,1\n"
    with pytest.raises(ValueError, match="missing fields"):
        _validate_response_csv(incomplete, request_url="https://example.test")
