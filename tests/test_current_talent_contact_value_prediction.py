from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_contact_value import (
    ContactValueBaselineFit,
    ContactValueResidualFit,
)
from universal_baseball.current_talent_contact_value_prediction import (
    materialize_contact_value_prediction_geometry,
)


def _baseline() -> ContactValueBaselineFit:
    return ContactValueBaselineFit(
        cutoff_date=date(2022, 7, 15),
        intercept=-0.2,
        contact_bin_effects={"IFFB": 0.0, "CENTER_LD": 0.5},
        level_group_effects={"MLB": 0.0, "AAA": 0.03},
        fitted_event_count=1000,
        parameter_count=3,
        fitted_level_groups=("MLB", "AAA"),
        max_training_event_date=date(2022, 7, 14),
    )


def _residual() -> ContactValueResidualFit:
    return ContactValueResidualFit(
        beta_mean_exit_velocity=0.08,
        beta_sweet_spot_share=-0.02,
        fitted_player_count=100,
        fitted_future_contact_count=5000,
        determinant=123.0,
    )


def _paired() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "event_date": date(2022, 7, 20),
                "game_pk": 1,
                "at_bat_index": 1,
                "pitch_number": 1,
                "player_id": 10,
                "contact_bin": "CENTER_LD",
                "level_group": "MLB",
                "terminal_value": 0.4,
                "contact_value_residual_applies": True,
                "z_mean_exit_velocity": 1.0,
                "z_sweet_spot_share": 0.5,
            },
            {
                "event_date": date(2022, 7, 21),
                "game_pk": 2,
                "at_bat_index": 2,
                "pitch_number": 1,
                "player_id": 20,
                "contact_bin": "IFFB",
                "level_group": "AAA",
                "terminal_value": -0.2,
                "contact_value_residual_applies": True,
                "z_mean_exit_velocity": -0.5,
                "z_sweet_spot_share": 1.0,
            },
        ]
    )


def test_prediction_geometry_applies_fixed_fits_on_identical_rows() -> None:
    paired = _paired()
    scored, metrics = materialize_contact_value_prediction_geometry(
        paired,
        baseline_fit=_baseline(),
        residual_fit=_residual(),
    )

    assert scored.height == paired.height
    assert scored.select("game_pk", "at_bat_index", "pitch_number").equals(
        paired.select("game_pk", "at_bat_index", "pitch_number")
    )
    first = scored.row(0, named=True)
    assert first["comparator_contact_value_prediction"] == pytest.approx(0.3)
    assert first["player_contact_value_residual_prediction"] == pytest.approx(0.07)
    assert first["richer_contact_value_prediction"] == pytest.approx(0.37)

    second = scored.row(1, named=True)
    assert second["comparator_contact_value_prediction"] == pytest.approx(-0.17)
    assert second["player_contact_value_residual_prediction"] == pytest.approx(-0.06)
    assert second["richer_contact_value_prediction"] == pytest.approx(-0.23)

    assert metrics["paired_event_count"] == 2
    assert metrics["comparator_richer_event_keys_identical"] is True
    assert metrics["losses_computed"] is False
    assert metrics["model_scoring"] is False
    assert metrics["accessed_2023"] is False
    assert not any("error" in column for column in scored.columns)


def test_prediction_geometry_rejects_fallback_rows() -> None:
    paired = _paired().with_columns(
        pl.when(pl.col("game_pk") == 2)
        .then(pl.lit(False))
        .otherwise(pl.col("contact_value_residual_applies"))
        .alias("contact_value_residual_applies")
    )
    with pytest.raises(ValueError, match="contains fallback rows"):
        materialize_contact_value_prediction_geometry(
            paired,
            baseline_fit=_baseline(),
            residual_fit=_residual(),
        )


def test_prediction_geometry_rejects_duplicate_keys() -> None:
    paired = _paired()
    duplicated = pl.concat([paired, paired.head(1)], how="vertical_relaxed")
    with pytest.raises(ValueError, match="duplicate event keys"):
        materialize_contact_value_prediction_geometry(
            duplicated,
            baseline_fit=_baseline(),
            residual_fit=_residual(),
        )
