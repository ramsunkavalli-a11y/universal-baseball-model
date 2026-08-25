import math

import polars as pl
import pytest

from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_stage2f import (
    LEVELS,
    apply_h0_neutral_projection,
    fit_forward_development,
    fit_reference_level_translations,
    fit_training_origin_calibration,
    predict_development_delta,
    probabilities_from_links,
    probability_links,
    wrap_reference_level_probabilities,
)


def _probabilities(**updates: float) -> dict[str, float]:
    values = {
        "UBB": 0.08,
        "HBP": 0.01,
        "K": 0.22,
        "HR": 0.04,
        "3B": 0.005,
        "2B": 0.045,
        "1B": 0.15,
        "ROE": 0.015,
        "FC_REACH": 0.01,
        "SF": 0.025,
        "MULTI_OUT": 0.02,
        "OTHER_OUT": 0.38,
    }
    values.update(updates)
    assert sum(values.values()) == pytest.approx(1.0)
    return values


def _translation_pairs(*, omit_boundary: int | None = None) -> pl.DataFrame:
    components = probability_links(_probabilities())
    rows = []
    for component in components:
        for boundary, (origin, destination) in enumerate(
            zip(LEVELS[:-1], LEVELS[1:], strict=True)
        ):
            if boundary == omit_boundary:
                continue
            rows.append(
                {
                    "component": component,
                    "origin_level": origin,
                    "destination_level": destination,
                    "age": 22.0,
                    "link_delta": 0.04,
                    "mover_pa": 1000.0,
                    "origin_season": 2020,
                    "destination_season": 2021,
                }
            )
    return pl.DataFrame(rows)


def test_nested_link_round_trip_is_complete_and_normalized() -> None:
    original = _probabilities()
    recovered = probabilities_from_links(probability_links(original))

    assert set(recovered) == set(HITTER_TALENT_OUTCOMES)
    assert sum(recovered.values()) == pytest.approx(1.0, abs=1e-12)
    assert recovered == pytest.approx(original, abs=1e-12)
    assert all(value >= 0.0 for value in recovered.values())


def test_removing_all_h0_inputs_returns_outcome_base_exactly() -> None:
    original = _probabilities()
    projection = apply_h0_neutral_projection(original, observed_level="AA")

    assert projection.probabilities == original
    assert projection.translation_path_quality == "exact_untranslated_base"
    assert projection.translation_uncertainty == 0.0
    assert projection.development_applied is False
    assert projection.calibration_applied is False


def test_translation_recovers_synthetic_adjacent_steps_and_mlb_anchor() -> None:
    fit = fit_reference_level_translations(
        _translation_pairs(),
        predictor_cutoff_season=2021,
        prior_mover_pa=250.0,
    )
    contact_edges = fit.edges.filter(
        (pl.col("component") == "contact") & (pl.col("age_band") == "ALL")
    )
    aaa = fit.offsets.filter(
        (pl.col("component") == "contact")
        & (pl.col("age_band") == "ALL")
        & (pl.col("level") == "AAA")
    ).row(0, named=True)
    mlb = fit.offsets.filter(
        (pl.col("component") == "contact")
        & (pl.col("age_band") == "ALL")
        & (pl.col("level") == "MLB")
    ).row(0, named=True)

    assert contact_edges["upward_link_delta"].to_list() == pytest.approx([0.04] * 5)
    assert aaa["link_offset_to_MLB"] == pytest.approx(0.04)
    assert aaa["path_quality"] == "partially_pooled_mover_path"
    assert mlb["link_offset_to_MLB"] == 0.0
    assert mlb["path_quality"] == "reference"


def test_disconnected_edge_uses_nonzero_global_fallback_with_uncertainty() -> None:
    fit = fit_reference_level_translations(
        _translation_pairs(omit_boundary=3),
        predictor_cutoff_season=2021,
        prior_mover_pa=250.0,
    )
    missing_edge = fit.edges.filter(
        (pl.col("component") == "contact")
        & (pl.col("age_band") == "ALL")
        & (pl.col("origin_level") == "AA")
        & (pl.col("destination_level") == "AAA")
    ).row(0, named=True)
    aa_path = fit.offsets.filter(
        (pl.col("component") == "contact")
        & (pl.col("age_band") == "ALL")
        & (pl.col("level") == "AA")
    ).row(0, named=True)

    assert missing_edge["used_global_fallback"] is True
    assert missing_edge["upward_link_delta"] == pytest.approx(0.04)
    assert aa_path["link_offset_to_MLB"] > 0.0
    assert aa_path["translation_uncertainty"] > 0.0
    assert aa_path["path_quality"] == "global_fallback"


def test_reference_wrapper_preserves_simplex_and_is_noop_at_mlb() -> None:
    original = _probabilities()
    fit = fit_reference_level_translations(
        _translation_pairs(),
        predictor_cutoff_season=2021,
        prior_mover_pa=250.0,
    )
    mlb = wrap_reference_level_probabilities(
        original, observed_level="MLB", translation=fit
    )
    low_level = wrap_reference_level_probabilities(
        original, observed_level="SINGLE_A", translation=fit
    )

    assert mlb.probabilities == pytest.approx(original, abs=1e-12)
    assert mlb.translation_path_quality == "reference"
    assert sum(low_level.probabilities.values()) == pytest.approx(1.0)
    assert low_level.probabilities != pytest.approx(original, abs=1e-6)


def test_unobserved_translation_age_band_uses_pooled_path_not_zero_skill() -> None:
    original = _probabilities()
    fit = fit_reference_level_translations(
        _translation_pairs(),
        predictor_cutoff_season=2021,
        prior_mover_pa=250.0,
    )
    projection = apply_h0_neutral_projection(
        original,
        observed_level="AA",
        translation=fit,
        age_at_target=19.0,
    )

    assert projection.translation_path_quality == "age_band_fallback"
    assert projection.translation_uncertainty > 0.0
    assert projection.probabilities != pytest.approx(original, abs=1e-6)


def test_translation_rejects_target_year_or_nonadjacent_pairs() -> None:
    future = _translation_pairs().with_columns(pl.lit(2022).alias("destination_season"))
    with pytest.raises(ValueError, match="adjacent seasons"):
        fit_reference_level_translations(
            future, predictor_cutoff_season=2021, prior_mover_pa=250.0
        )

    future = _translation_pairs().with_columns(
        pl.lit(2021).alias("origin_season"),
        pl.lit(2022).alias("destination_season"),
    )
    with pytest.raises(ValueError, match="predictor cutoff"):
        fit_reference_level_translations(
            future, predictor_cutoff_season=2021, prior_mover_pa=250.0
        )


def test_forward_development_learns_only_synthetic_prior_pairs() -> None:
    references = {level: 24.0 for level in LEVELS}
    pairs = pl.DataFrame(
        [
            {
                "component": "contact",
                "level": "AA",
                "age": float(age),
                "reference_link_delta": 0.08 - 0.012 * (age - 20),
                "mover_pa": 300.0,
                "origin_season": 2020,
                "destination_season": 2021,
            }
            for age in range(18, 35)
        ]
    )
    fit = fit_forward_development(
        pairs,
        predictor_cutoff_season=2021,
        prior_sd=0.1,
        level_age_references=references,
    )
    young = predict_development_delta(fit, "contact", age=19.0, level="AA")
    old = predict_development_delta(fit, "contact", age=33.0, level="AA")

    assert math.isfinite(young)
    assert math.isfinite(old)
    assert young > old


def test_calibration_is_shrunk_toward_identity_and_rejects_future_origin() -> None:
    origins = pl.DataFrame(
        {
            "component": ["contact"] * 4,
            "predicted_link": [-1.0, -0.25, 0.25, 1.0],
            "observed_link": [-0.7, -0.1, 0.3, 0.9],
            "evidence": [100.0] * 4,
            "target_season": [2020] * 4,
        }
    )
    fit = fit_training_origin_calibration(
        origins, predictor_cutoff_season=2021, prior_sd=0.1
    )
    row = fit.coefficients.row(0, named=True)

    assert abs(row["intercept"]) < 0.2
    assert 0.5 < row["slope"] < 1.2
    with pytest.raises(ValueError, match="predictor cutoff"):
        fit_training_origin_calibration(
            origins.with_columns(pl.lit(2022).alias("target_season")),
            predictor_cutoff_season=2021,
            prior_sd=0.1,
        )


def test_terminal_history_power_difference_survives_common_translation() -> None:
    power = _probabilities(HR=0.07, OTHER_OUT=0.35)
    low_power = _probabilities(HR=0.02, OTHER_OUT=0.40)
    fit = fit_reference_level_translations(
        _translation_pairs(),
        predictor_cutoff_season=2021,
        prior_mover_pa=250.0,
    )
    translated_power = wrap_reference_level_probabilities(
        power, observed_level="AA", translation=fit
    ).probabilities
    translated_low = wrap_reference_level_probabilities(
        low_power, observed_level="AA", translation=fit
    ).probabilities

    assert translated_power["HR"] > translated_low["HR"]


def test_coherent_mass_moves_increase_value_in_frozen_order() -> None:
    weights = {"OTHER_OUT": 0.0, "1B": 0.9, "2B": 1.3, "3B": 1.6, "HR": 2.0}
    base = _probabilities()

    values = []
    for destination in ("1B", "2B", "3B", "HR"):
        moved = dict(base)
        moved["OTHER_OUT"] -= 0.01
        moved[destination] += 0.01
        values.append(
            sum(moved.get(key, 0.0) * weight for key, weight in weights.items())
        )

    assert values == sorted(values)
    assert len(set(values)) == 4
