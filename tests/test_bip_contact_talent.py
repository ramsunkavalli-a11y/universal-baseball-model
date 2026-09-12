import polars as pl
import pytest

from universal_baseball.bip_contact_talent import (
    BipResidualBlend,
    apply_bip_residual_blend,
    estimate_neutral_bip_values,
    fit_bip_residual_blend,
    score_projected_bip_profile,
)
from universal_baseball.performance_season import CONTACT_CORE_BINS


def _profile(probabilities: dict[str, float]) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "player_id": 1,
                "core_bin": core_bin,
                "projected_bip_probability": probabilities.get(core_bin, 0.0),
            }
            for core_bin in CONTACT_CORE_BINS
        ]
    )


def _values() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {"core_bin": core_bin, "neutral_run_value": float(index)}
            for index, core_bin in enumerate(CONTACT_CORE_BINS)
        ]
    )


def test_full_profile_contact_value_uses_every_bin() -> None:
    probabilities = {core_bin: 0.1 for core_bin in CONTACT_CORE_BINS}
    scored = score_projected_bip_profile(_profile(probabilities), _values())
    assert scored["bip_contact_value"][0] == pytest.approx(4.5)
    assert scored["bip_profile_bins"][0] == 10


def test_neutral_values_are_learned_from_terminal_outcomes() -> None:
    rows = []
    for core_bin in CONTACT_CORE_BINS:
        rows.extend(
            [
                {"core_bin": core_bin, "canonical_outcome": "1B", "occurrence_count": 3},
                {"core_bin": core_bin, "canonical_outcome": "OTHER_OUT", "occurrence_count": 1},
            ]
        )
    values = estimate_neutral_bip_values(pl.DataFrame(rows))
    assert values.height == 10
    assert values["value_events"].to_list() == [4] * 10
    assert values["neutral_run_value"].to_list() == pytest.approx([0.6582] * 10)


def test_profile_must_be_complete_and_normalized() -> None:
    probabilities = {core_bin: 0.1 for core_bin in CONTACT_CORE_BINS}
    incomplete = _profile(probabilities).filter(pl.col("core_bin") != "IFFB")
    with pytest.raises(ValueError, match="ten bins summing to one"):
        score_projected_bip_profile(incomplete, _values())


def test_residual_blend_learns_supported_increment() -> None:
    training = pl.DataFrame(
        {
            "player_id": [1, 2],
            "baseline_contact_value": [0.0, 0.0],
            "bip_contact_value": [1.0, -1.0],
            "target_contact_value": [0.5, -0.5],
            "target_contacts": [100.0, 100.0],
        }
    )
    blend = fit_bip_residual_blend(training)
    assert blend.weight == pytest.approx(0.5)
    assert blend.training_contacts == 200.0


def test_unsupported_or_reversed_signal_falls_back_to_baseline() -> None:
    training = pl.DataFrame(
        {
            "player_id": [1, 2],
            "baseline_contact_value": [0.0, 0.0],
            "bip_contact_value": [1.0, -1.0],
            "target_contact_value": [-0.5, 0.5],
            "target_contacts": [100.0, 100.0],
        }
    )
    blend = fit_bip_residual_blend(training)
    assert blend.unconstrained_weight < 0.0
    assert blend.weight == 0.0
    estimates = pl.DataFrame(
        {
            "player_id": [1],
            "baseline_contact_value": [0.2],
            "bip_contact_value": [0.8],
        }
    )
    applied = apply_bip_residual_blend(estimates, blend)
    assert applied["blended_contact_value"][0] == 0.2


def test_blend_cannot_extrapolate_past_bip_estimate() -> None:
    estimates = pl.DataFrame(
        {
            "player_id": [1],
            "baseline_contact_value": [0.2],
            "bip_contact_value": [0.8],
        }
    )
    applied = apply_bip_residual_blend(
        estimates, BipResidualBlend(1.0, 1, 100.0, 3.0)
    )
    assert applied["blended_contact_value"][0] == pytest.approx(0.8)
