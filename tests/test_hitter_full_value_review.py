import pytest
from universal_baseball.hitter_full_value_review import recenter_positive_pa, forecast_pa_column


def row(pid, pa, bat):
    return dict(player_id=pid, origin_year=2023, expected_PA=pa,
                batting_runs=bat, replacement_runs=3., league_runs=0.,
                park_runs=0., runs_per_win=10., combined=(bat+3)/10)


def test_zero_origin_pa_excluded_only_from_reference_not_forecasts():
    original = [row(1, 100, 2), row(2, 50, 9), row(3, 10, 1)]
    corrected, receipt = recenter_positive_pa(original, {(2023, 1): 500, (2023, 2): 0})
    assert len(corrected) == 3
    assert receipt[0]['reference_people'] == 1
    assert corrected[0]['league_runs'] == -2
    assert corrected[1]['league_runs'] == -1
    assert corrected[2]['league_runs'] == pytest.approx(-.2)
    assert original[0]['league_runs'] == 0
    for old, new in zip(original, corrected):
        assert all(old[k] == new[k] for k in old if k not in ('league_runs', 'combined'))


def test_no_reference_exposure_is_error():
    with pytest.raises(ValueError):
        recenter_positive_pa([row(1, 0, 0)], {(2023, 1): 1})


def test_public_opportunity_uses_public_system():
    assert forecast_pa_column('steamer') == 'steamer_PA'
    assert forecast_pa_column('zips') == 'zips_PA'
    assert forecast_pa_column('combined') == 'expected_PA'
