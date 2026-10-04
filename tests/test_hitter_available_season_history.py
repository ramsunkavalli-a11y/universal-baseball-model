import pytest

from universal_baseball.hitter_available_season_history import seasons, AFFILIATED


@pytest.mark.parametrize('origin,expected',[(2020,[2019,2018,2017]),
    (2021,[2021,2019,2018]),(2022,[2022,2021,2019]),(2023,[2023,2022,2021]),
    (2018,[2018,2017,2016])])
def test_only_known_system_cancellation_is_skipped(origin,expected):
    assert seasons(origin,True)==expected
    assert seasons(origin,False)==[origin,origin-1,origin-2]


def test_calendar_leagues_are_not_remapped():
    assert 'MLB' not in AFFILIATED and 'MEX' not in AFFILIATED
    assert 'DSL' in AFFILIATED and 'Aminus' in AFFILIATED
