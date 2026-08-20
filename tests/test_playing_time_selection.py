from __future__ import annotations

import polars as pl

from universal_baseball.playing_time_model import PT_FORM_A, PT_FORM_B, PT_FORM_B0, PT_FORM_C
from universal_baseball.playing_time_selection import select_playing_time_form


def _rows() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "form": PT_FORM_B0,
                "mean_full_negative_log_likelihood": 1.2000,
                "participation_log_loss": 0.3000,
                "unconditional_mlb_pa_mae": 90.0,
            },
            {
                "form": PT_FORM_A,
                "mean_full_negative_log_likelihood": 1.1500,
                "participation_log_loss": 0.2800,
                "unconditional_mlb_pa_mae": 84.0,
            },
            {
                "form": PT_FORM_B,
                "mean_full_negative_log_likelihood": 1.1495,
                "participation_log_loss": 0.2798,
                "unconditional_mlb_pa_mae": 83.0,
            },
            {
                "form": PT_FORM_C,
                "mean_full_negative_log_likelihood": 1.1494,
                "participation_log_loss": 0.2797,
                "unconditional_mlb_pa_mae": 83.5,
            },
        ]
    )


def test_selection_uses_frozen_full_nll_then_participation_then_mae() -> None:
    result = select_playing_time_form(_rows())
    assert result.selected_form == PT_FORM_B
    assert result.baseline0_selected is False
    assert result.advances_to_out_of_time_validation is True


def test_selection_prefers_simpler_form_after_frozen_metric_ties() -> None:
    frame = _rows().with_columns(
        pl.when(pl.col("form").is_in([PT_FORM_A, PT_FORM_B]))
        .then(1.15)
        .otherwise(pl.col("mean_full_negative_log_likelihood"))
        .alias("mean_full_negative_log_likelihood"),
        pl.when(pl.col("form").is_in([PT_FORM_A, PT_FORM_B]))
        .then(0.28)
        .otherwise(pl.col("participation_log_loss"))
        .alias("participation_log_loss"),
        pl.when(pl.col("form").is_in([PT_FORM_A, PT_FORM_B]))
        .then(84.0)
        .otherwise(pl.col("unconditional_mlb_pa_mae"))
        .alias("unconditional_mlb_pa_mae"),
    ).with_columns(
        pl.when(pl.col("form") == PT_FORM_C)
        .then(1.30)
        .otherwise(pl.col("mean_full_negative_log_likelihood"))
        .alias("mean_full_negative_log_likelihood")
    )
    result = select_playing_time_form(frame)
    assert result.selected_form == PT_FORM_A


def test_selection_freezes_level_baseline_when_it_is_best() -> None:
    frame = _rows().with_columns(
        pl.when(pl.col("form") == PT_FORM_B0)
        .then(1.0)
        .otherwise(pl.col("mean_full_negative_log_likelihood"))
        .alias("mean_full_negative_log_likelihood"),
        pl.when(pl.col("form") == PT_FORM_B0)
        .then(0.25)
        .otherwise(pl.col("participation_log_loss"))
        .alias("participation_log_loss"),
        pl.when(pl.col("form") == PT_FORM_B0)
        .then(80.0)
        .otherwise(pl.col("unconditional_mlb_pa_mae"))
        .alias("unconditional_mlb_pa_mae"),
    )
    result = select_playing_time_form(frame)
    assert result.selected_form == PT_FORM_B0
    assert result.baseline0_selected is True
    assert result.advances_to_out_of_time_validation is False
