from universal_baseball.pitch_process_coverage import (
    pitch_process_capability,
    pitch_process_is_eligible,
)


def test_2023_rookie_leagues_are_not_pitch_process_eligible() -> None:
    for league_id in (121, 124, 130):
        capability = pitch_process_capability(2023, league_id)
        assert capability.status == "ineligible_synthetic_sequence"
        assert not pitch_process_is_eligible(2023, league_id)


def test_2024_acl_and_fcl_are_eligible_but_dsl_is_not() -> None:
    assert pitch_process_is_eligible(2024, 121)
    assert pitch_process_is_eligible(2024, 124)
    assert not pitch_process_is_eligible(2024, 130)
    assert pitch_process_capability(2024, 130).status == "ineligible_synthetic_sequence"


def test_uncertified_is_not_treated_as_eligible() -> None:
    capability = pitch_process_capability(2025, 130)
    assert capability.status == "uncertified"
    assert not pitch_process_is_eligible(2025, 130)


def test_certified_full_season_leagues_are_eligible() -> None:
    for season in (2018, 2019, 2021, 2022, 2023, 2024):
        for league_id in (109, 110, 111, 112, 113, 116, 117, 118, 122, 123, 126):
            assert pitch_process_is_eligible(season, league_id)


def test_2021_and_2022_rookie_leagues_are_not_eligible() -> None:
    for season in (2021, 2022):
        for league_id in (121, 124, 130):
            assert not pitch_process_is_eligible(season, league_id)
