from datetime import date
from urllib.parse import parse_qs, urlparse

import pytest

from universal_baseball.current_talent_savant_minors import (
    SAVANT_MINORS_CSV_ROOT,
    build_tracked_minor_savant_url,
)


def test_tracked_minor_savant_url_uses_explicit_tracked_filters() -> None:
    url = build_tracked_minor_savant_url(date(2022, 6, 1), date(2022, 6, 2))
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == SAVANT_MINORS_CSV_ROOT
    assert params == {
        "all": ["true"],
        "player_type": ["batter"],
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


def test_tracked_minor_savant_url_rejects_reverse_range() -> None:
    with pytest.raises(ValueError, match="end_date"):
        build_tracked_minor_savant_url(date(2023, 7, 2), date(2023, 7, 1))
