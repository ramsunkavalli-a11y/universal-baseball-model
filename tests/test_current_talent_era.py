import pytest

from universal_baseball.current_talent_era import (
    POST_REORGANIZATION_CURRENT_TALENT_YEARS,
    POST_REORGANIZATION_LEVEL_SPECS,
    current_talent_level_spec,
)


def test_post_reorganization_current_talent_map_is_stable_2021_through_2024() -> None:
    assert POST_REORGANIZATION_CURRENT_TALENT_YEARS == frozenset({2021, 2022, 2023, 2024})
    expected = {
        "aaa": {112, 117},
        "aa": {109, 111, 113},
        "a+": {116, 118, 126},
        "a": {110, 122, 123},
        "rk": {121, 124, 130},
    }
    for season in sorted(POST_REORGANIZATION_CURRENT_TALENT_YEARS):
        for level, league_ids in expected.items():
            assert current_talent_level_spec(season, level).league_ids == frozenset(league_ids)


def test_post_reorganization_map_has_unique_league_ownership() -> None:
    observed = [
        int(league_id)
        for spec in POST_REORGANIZATION_LEVEL_SPECS.values()
        for league_id in spec.league_ids
    ]
    assert len(observed) == len(set(observed)) == 14


def test_pre_reorganization_year_fails_instead_of_backcasting_current_map() -> None:
    with pytest.raises(KeyError, match="outside the certified initial Current Talent era"):
        current_talent_level_spec(2019, "aaa")


def test_unsupported_level_fails_loudly() -> None:
    with pytest.raises(KeyError, match="unsupported affiliated filename level"):
        current_talent_level_spec(2023, "a-")
