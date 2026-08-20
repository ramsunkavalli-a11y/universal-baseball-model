from __future__ import annotations

import pytest

from universal_baseball.player_value_centering_sensitivity_feasibility import (
    REQUIRED_SURFACE_KEYS,
    evaluate_centering_sensitivity_feasibility,
)


def test_complete_surface_is_feasible() -> None:
    result = evaluate_centering_sensitivity_feasibility(
        {key: True for key in REQUIRED_SURFACE_KEYS}
    )
    assert result.complete
    assert result.missing_keys == ()


def test_any_missing_surface_fails_closed() -> None:
    availability = {key: True for key in REQUIRED_SURFACE_KEYS}
    availability["official_positive_pa_membership"] = False
    availability["mlb_batting_run_reference"] = False
    result = evaluate_centering_sensitivity_feasibility(availability)
    assert not result.complete
    assert result.missing_keys == (
        "official_positive_pa_membership",
        "mlb_batting_run_reference",
    )


def test_incomplete_or_unknown_maps_are_rejected() -> None:
    with pytest.raises(ValueError, match="missing required"):
        evaluate_centering_sensitivity_feasibility({})
    availability = {key: True for key in REQUIRED_SURFACE_KEYS}
    availability["invented"] = True
    with pytest.raises(ValueError, match="unknown"):
        evaluate_centering_sensitivity_feasibility(availability)

