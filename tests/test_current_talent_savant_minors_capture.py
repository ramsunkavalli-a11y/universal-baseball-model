from datetime import date
from pathlib import Path
import sys

import polars as pl
import pytest
import requests

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from capture_current_talent_savant_minors_tracking import (  # noqa: E402
    _certified_date_bounds,
    _fetch_with_retry,
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


def _response(status: int) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response.url = "https://example.test"
    response._content = b"ok"
    return response


class _FakeSession:
    def __init__(self, outcomes: list[requests.Response | Exception]) -> None:
        self.outcomes = list(outcomes)
        self.calls = 0

    def get(self, url: str, timeout: int) -> requests.Response:
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def test_fetch_retries_transient_http_with_bounded_exponential_backoff() -> None:
    session = _FakeSession([_response(503), _response(429), _response(200)])
    sleeps: list[float] = []

    response, attempts = _fetch_with_retry(
        session,  # type: ignore[arg-type]
        "https://example.test",
        max_attempts=4,
        base_backoff_seconds=2.0,
        sleep_fn=sleeps.append,
    )

    assert response.status_code == 200
    assert attempts == 3
    assert session.calls == 3
    assert sleeps == [2.0, 4.0]


def test_fetch_retries_transport_exception_but_not_nontransient_http() -> None:
    session = _FakeSession([requests.ConnectionError("temporary"), _response(200)])
    sleeps: list[float] = []

    response, attempts = _fetch_with_retry(
        session,  # type: ignore[arg-type]
        "https://example.test",
        max_attempts=2,
        base_backoff_seconds=1.0,
        sleep_fn=sleeps.append,
    )
    assert response.status_code == 200
    assert attempts == 2
    assert sleeps == [1.0]

    no_retry = _FakeSession([_response(404), _response(200)])
    with pytest.raises(requests.HTTPError):
        _fetch_with_retry(
            no_retry,  # type: ignore[arg-type]
            "https://example.test",
            max_attempts=2,
            base_backoff_seconds=0.0,
            sleep_fn=lambda _: None,
        )
    assert no_retry.calls == 1
