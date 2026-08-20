from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.projection_ridge import (
    AGE_FEATURE_NAMES,
    LEVEL_FEATURE_NAMES,
    PROJECTION_FORM_AGE,
    PROJECTION_FORM_AGE_LEVEL,
    build_projection_design,
    fit_projection_weighted_ridge,
    predict_projection_ridge,
    projection_age_basis,
    projection_cv_fold,
)


def _context() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "player_id": [101, 102, 103, 104, 105, 106],
            "age_years": [20.0, 23.0, 26.0, 29.0, 32.0, 35.0],
            "as_of_level_group": ["MLB", "AAA", "AA", "High-A", "Single-A", "Rookie Complex"],
        }
    )


def test_projection_age_basis_matches_frozen_piecewise_linear_contract() -> None:
    values = projection_age_basis(29.0)
    assert tuple(values) == AGE_FEATURE_NAMES
    assert values["age_center_27_over_5"] == pytest.approx(0.4)
    assert values["age_hinge_20_over_5"] == pytest.approx(1.8)
    assert values["age_hinge_23_over_5"] == pytest.approx(1.2)
    assert values["age_hinge_26_over_5"] == pytest.approx(0.6)
    assert values["age_hinge_29_over_5"] == pytest.approx(0.0)
    assert values["age_hinge_32_over_5"] == pytest.approx(0.0)
    assert values["age_hinge_35_over_5"] == pytest.approx(0.0)


def test_form_b_uses_mlb_reference_and_only_frozen_level_main_effects() -> None:
    design = build_projection_design(_context(), form=PROJECTION_FORM_AGE_LEVEL)
    mlb = design.filter(pl.col("player_id") == 101).row(0, named=True)
    aaa = design.filter(pl.col("player_id") == 102).row(0, named=True)
    assert all(float(mlb[name]) == 0.0 for name in LEVEL_FEATURE_NAMES)
    assert sum(float(aaa[name]) for name in LEVEL_FEATURE_NAMES) == pytest.approx(1.0)
    assert float(aaa["level_aaa"]) == 1.0


def test_form_a_design_is_independent_of_level_labels() -> None:
    first = build_projection_design(_context(), form=PROJECTION_FORM_AGE)
    changed = _context().with_columns(pl.lit("MLB").alias("as_of_level_group"))
    second = build_projection_design(changed, form=PROJECTION_FORM_AGE)
    assert first.equals(second)


def test_projection_cv_assignment_is_deterministic_and_in_frozen_range() -> None:
    observed = [projection_cv_fold(player_id) for player_id in range(1, 100)]
    repeated = [projection_cv_fold(player_id) for player_id in range(1, 100)]
    assert observed == repeated
    assert set(observed) <= {0, 1, 2, 3, 4}
    assert len(set(observed)) == 5


def test_weighted_ridge_standardizes_training_only_and_predicts_multioutput() -> None:
    context = _context()
    design = build_projection_design(context, form=PROJECTION_FORM_AGE)
    age_signal = design.get_column("age_center_27_over_5")
    responses = pl.DataFrame(
        {
            "player_id": context.get_column("player_id"),
            "future_core_events": [50.0, 100.0, 150.0, 200.0, 250.0, 300.0],
            "delta_ilr_00": (1.5 + age_signal * 0.75).to_list(),
            "delta_ilr_01": (-0.5 + age_signal * -0.25).to_list(),
        }
    )
    fit = fit_projection_weighted_ridge(
        design,
        responses,
        form=PROJECTION_FORM_AGE,
        ridge_lambda=0.001,
        weight_column="future_core_events",
        response_columns=("delta_ilr_00", "delta_ilr_01"),
    )
    predicted = predict_projection_ridge(fit, design).join(responses, on="player_id")
    assert fit.coefficient_matrix.shape == (1 + len(AGE_FEATURE_NAMES), 2)
    assert fit.weighted_means[0] == pytest.approx(0.0)
    assert fit.weighted_scales[0] == pytest.approx(1.0)
    assert predicted.select(
        (pl.col("predicted_delta_ilr_00") - pl.col("delta_ilr_00")).abs().mean()
    ).item() < 0.02
    assert predicted.select(
        (pl.col("predicted_delta_ilr_01") - pl.col("delta_ilr_01")).abs().mean()
    ).item() < 0.02


def test_zero_variance_level_feature_is_retained_as_zero_with_unit_scale() -> None:
    context = pl.DataFrame(
        {
            "player_id": [1, 2, 3, 4, 5],
            "age_years": [22.0, 23.0, 24.0, 25.0, 26.0],
            "as_of_level_group": ["MLB"] * 5,
        }
    )
    design = build_projection_design(context, form=PROJECTION_FORM_AGE_LEVEL)
    responses = pl.DataFrame(
        {
            "player_id": [1, 2, 3, 4, 5],
            "future_core_events": [100.0] * 5,
            "delta_ilr_00": [0.0, 0.1, 0.2, 0.3, 0.4],
        }
    )
    fit = fit_projection_weighted_ridge(
        design,
        responses,
        form=PROJECTION_FORM_AGE_LEVEL,
        ridge_lambda=0.1,
        weight_column="future_core_events",
        response_columns=("delta_ilr_00",),
    )
    standardization = fit.standardization_frame()
    coefficients = fit.coefficient_frame()
    for feature in LEVEL_FEATURE_NAMES:
        row = standardization.filter(pl.col("feature") == feature).row(0, named=True)
        coefficient = coefficients.filter(
            (pl.col("feature") == feature) & (pl.col("response") == "delta_ilr_00")
        ).item(0, "coefficient")
        assert row["zero_variance_in_training"] is True
        assert float(row["weighted_rms_scale"]) == pytest.approx(1.0)
        assert float(coefficient) == pytest.approx(0.0, abs=1e-12)


def test_ridge_rejects_lambda_outside_frozen_grid() -> None:
    context = _context()
    design = build_projection_design(context, form=PROJECTION_FORM_AGE)
    responses = pl.DataFrame(
        {
            "player_id": context.get_column("player_id"),
            "future_core_events": [100.0] * context.height,
            "delta_ilr_00": [0.0] * context.height,
        }
    )
    with pytest.raises(ValueError, match="outside frozen grid"):
        fit_projection_weighted_ridge(
            design,
            responses,
            form=PROJECTION_FORM_AGE,
            ridge_lambda=0.5,
            weight_column="future_core_events",
            response_columns=("delta_ilr_00",),
        )
