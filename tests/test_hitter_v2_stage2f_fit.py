from pathlib import Path

import polars as pl
import pytest

from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_stage2f import (
    LEVELS,
    apply_h0_neutral_projection,
    fit_forward_development,
    fit_reference_level_translations,
    fit_training_origin_calibration,
    probability_links,
)
from universal_baseball.hitter_v2_stage2f_fit import (
    H0FitSurfaces,
    apply_compiled_h0_projection,
    compile_h0_surfaces,
    materialize_h0_fit_sources,
)


ROOT = Path(__file__).resolve().parents[1]


def _probabilities() -> dict[str, float]:
    return {
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


def _realistic_surfaces() -> H0FitSurfaces:
    components = probability_links(_probabilities())
    translation_rows = []
    for component in components:
        for origin, destination in zip(LEVELS[:-1], LEVELS[1:], strict=True):
            translation_rows.append(
                {
                    "component": component,
                    "origin_level": origin,
                    "destination_level": destination,
                    "age": 22.0,
                    "link_delta": 0.02,
                    "mover_pa": 500.0,
                    "origin_season": 2020,
                    "destination_season": 2021,
                }
            )
    translation = fit_reference_level_translations(
        pl.DataFrame(translation_rows),
        predictor_cutoff_season=2021,
        prior_mover_pa=250.0,
    )
    development_rows = []
    for component in components:
        for age in range(18, 35):
            development_rows.append(
                {
                    "component": component,
                    "level": "AA",
                    "age": float(age),
                    "reference_link_delta": 0.03 - 0.002 * age,
                    "mover_pa": 200.0,
                    "origin_season": 2020,
                    "destination_season": 2021,
                }
            )
    development = fit_forward_development(
        pl.DataFrame(development_rows),
        predictor_cutoff_season=2021,
        prior_sd=0.1,
        level_age_references={level: 24.0 for level in LEVELS},
    )
    calibration_rows = []
    for component in components:
        for value in (-1.0, -0.25, 0.25, 1.0):
            calibration_rows.append(
                {
                    "component": component,
                    "predicted_link": value,
                    "observed_link": 0.02 + 0.95 * value,
                    "evidence": 100.0,
                    "target_season": 2021,
                }
            )
    calibration = fit_training_origin_calibration(
        pl.DataFrame(calibration_rows),
        predictor_cutoff_season=2021,
        prior_sd=0.1,
    )
    return H0FitSurfaces(
        translation=translation,
        development=development,
        calibration=calibration,
        development_pairs=pl.DataFrame(development_rows),
        calibration_origins=pl.DataFrame(calibration_rows),
    )


def test_compiled_application_is_numerically_identical_to_audited_primitive() -> None:
    probabilities = _probabilities()
    surfaces = _realistic_surfaces()
    expected = apply_h0_neutral_projection(
        probabilities,
        observed_level="AA",
        translation=surfaces.translation,
        development=surfaces.development,
        calibration=surfaces.calibration,
        age_at_target=22.0,
    )
    observed = apply_compiled_h0_projection(
        probabilities,
        compile_h0_surfaces(surfaces),
        observed_level="AA",
        age_at_target=22.0,
        include_calibration=True,
    )

    assert observed.probabilities == pytest.approx(expected.probabilities, abs=1e-14)
    assert observed.translation_path_quality == expected.translation_path_quality
    assert observed.translation_uncertainty == expected.translation_uncertainty
    assert observed.development_applied == expected.development_applied
    assert observed.calibration_applied == expected.calibration_applied


def test_fit_source_materializer_rejects_future_rows_before_any_fit() -> None:
    future = pl.DataFrame({"season": [2022]})
    current = pl.DataFrame({"season": [2021]})

    with pytest.raises(ValueError, match="training source crosses"):
        materialize_h0_fit_sources(
            future,
            current,
            current,
            current,
            current,
            predictor_cutoff_season=2021,
            component_prior_pa=800.0,
        )


def test_fit_runner_has_no_validation_table_loader_or_metric_call() -> None:
    source = (ROOT / "scripts/fit_hitter_v2_stage2f_H0.py").read_text(encoding="utf-8")

    assert "target_player_league_seasons.parquet" not in source
    assert "evaluation_players.parquet" not in source
    assert "score_hitter" not in source
    assert "log_loss" not in source
    assert "brier" not in source.lower()
    assert "woba" not in source.lower()


def test_probability_fixture_is_exhaustive() -> None:
    assert set(_probabilities()) == set(HITTER_TALENT_OUTCOMES)
    assert sum(_probabilities().values()) == pytest.approx(1.0)
