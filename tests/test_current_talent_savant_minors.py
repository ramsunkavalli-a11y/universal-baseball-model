from datetime import date
from urllib.parse import parse_qs, urlparse

import pytest

from universal_baseball.current_talent_savant_minors import (
    REGULAR_SEASON_GAME_TYPE_FILTER,
    SAVANT_MINORS_CSV_ROOT,
    build_tracked_minor_savant_url,
    plan_tracked_minor_savant_requests,
)


def test_tracked_minor_savant_url_uses_explicit_tracked_regular_season_filters() -> None:
    url = build_tracked_minor_savant_url(date(2022, 6, 1), date(2022, 6, 2))
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == SAVANT_MINORS_CSV_ROOT
    assert params == {
        "all": ["true"],
        "player_type": ["batter"],
        "hfGT": [REGULAR_SEASON_GAME_TYPE_FILTER],
        "game_date_gt": ["2022-06-01"],
        "game_date_lt": ["2022-06-02"],
        "type": ["details"],
        "minors": ["true"],
        "hfFlag": ["is..tracked|"],
        "chk_is..tracked": ["on"],
    }


def test_tracked_minor_savant_url_allows_single_date_probe() -> None:
    url = build_tracked_minor_savant_url(date(2023, 7, 1), date(2023, 7, 1))
    params = parse_qs(urlparse(url).query)
    assert params["game_date_gt"] == ["2023-07-01"]
    assert params["game_date_lt"] == ["2023-07-01"]
    assert params["hfGT"] == [REGULAR_SEASON_GAME_TYPE_FILTER]


def test_tracked_minor_savant_url_rejects_reverse_range() -> None:
    with pytest.raises(ValueError, match="end_date"):
        build_tracked_minor_savant_url(date(2023, 7, 2), date(2023, 7, 1))


def test_request_plan_is_contiguous_nonoverlapping_and_bounded() -> None:
    planned = plan_tracked_minor_savant_requests(
        date(2022, 7, 1),
        date(2022, 7, 10),
        chunk_days=4,
    )

    assert [(request.start_date, request.end_date) for request in planned] == [
        (date(2022, 7, 1), date(2022, 7, 4)),
        (date(2022, 7, 5), date(2022, 7, 8)),
        (date(2022, 7, 9), date(2022, 7, 10)),
    ]
    assert [request.raw_filename for request in planned] == [
        "savant-minors-tracked-2022-07-01_2022-07-04.csv",
        "savant-minors-tracked-2022-07-05_2022-07-08.csv",
        "savant-minors-tracked-2022-07-09_2022-07-10.csv",
    ]
    for request in planned:
        params = parse_qs(urlparse(request.request_url).query)
        assert params["game_date_gt"] == [request.start_date.isoformat()]
        assert params["game_date_lt"] == [request.end_date.isoformat()]
        assert params["chk_is..tracked"] == ["on"]
        assert params["hfGT"] == [REGULAR_SEASON_GAME_TYPE_FILTER]


def test_request_plan_supports_one_day_and_rejects_invalid_chunk_size() -> None:
    planned = plan_tracked_minor_savant_requests(
        date(2021, 5, 4),
        date(2021, 5, 4),
    )
    assert len(planned) == 1
    assert planned[0].start_date == date(2021, 5, 4)
    assert planned[0].end_date == date(2021, 5, 4)

    with pytest.raises(ValueError, match="chunk_days"):
        plan_tracked_minor_savant_requests(
            date(2021, 5, 4),
            date(2021, 5, 5),
            chunk_days=0,
        )
