import pytest

from scripts.audit_multiyear_horizon_support import horizon_support


def test_mature_labels_do_not_imply_a_valid_long_horizon_backtest():
    result = horizon_support([2015, 2016, 2017, 2018, 2021, 2022, 2023, 2024], list(range(2015, 2026)))
    six = result[5]
    assert six["cumulative_label_origins"] == [2015, 2016, 2017, 2018]
    assert six["outer_origins_with_prior_training"] == []
    assert six["outer_origins_with_nested_support"] == []


def test_embargo_applies_to_the_full_label_window_and_inner_validation():
    two = horizon_support([2000, 2003, 2006], list(range(2001, 2009)))[1]
    assert two["outer_origins_with_prior_training"] == [2003, 2006]
    assert two["outer_origins_with_nested_support"] == [2006]
    assert two["folds"][-1]["inner_validation_origins"] == [2003]
    same_year = horizon_support([2000, 2002], list(range(2001, 2005)))[1]
    assert same_year["outer_origins_with_prior_training"] == []


def test_missing_intervening_year_prevents_cumulative_label():
    three = horizon_support([2019], [2021, 2022])[2]
    assert three["annual_label_origins"] == [2019]
    assert three["cumulative_label_origins"] == []


def test_protected_outcomes_are_rejected():
    with pytest.raises(ValueError, match="boundary"):
        horizon_support([2024], [2025, 2026])
    with pytest.raises(ValueError, match="Protected"):
        horizon_support([2024], [2025], last_outcome=2026)
