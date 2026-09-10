import polars as pl
import pytest

from universal_baseball.war_uncertainty_validation import (
    summarize_binary_probability_calibration,
    summarize_interval_coverage,
    summarize_named_slices,
    summarize_normal_reference_calibration,
    wilson_interval,
)


def _frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "projected_war_mean": [0.0, 0.0, 0.0, 0.0],
            "projected_war_lower": [-1.0, -1.0, -1.0, -1.0],
            "projected_war_upper": [1.0, 1.0, 1.0, 1.0],
            "annual_war_variance": [1.0, 1.0, 1.0, 0.0],
            "observed_neutral_war": [0.0, -2.0, 2.0, 0.0],
            "group": ["a", "a", "b", "b"],
        }
    )


def test_wilson_interval_contains_observed_fraction() -> None:
    lower, upper = wilson_interval(8, 10)
    assert lower < 0.8 < upper


def test_interval_summary_keeps_both_miss_tails_and_zero_variance() -> None:
    result = summarize_interval_coverage(_frame())
    assert result["players"] == 4
    assert result["coverage"] == 0.5
    assert result["lower_tail_miss_rate"] == 0.25
    assert result["upper_tail_miss_rate"] == 0.25
    assert result["positive_variance_players"] == 3
    assert result["mean_interval_score"] == pytest.approx(7.0)
    assert result["standardized_error_mean"] == 0.0
    assert result["standardized_error_rmse"] == pytest.approx((8 / 3) ** 0.5)


def test_named_slices_retain_small_groups_but_mark_them_ineligible() -> None:
    result = summarize_named_slices(_frame(), slice_column="group")
    assert [row["slice_value"] for row in result] == ["a", "b"]
    assert not any(row["decision_eligible"] for row in result)


def test_interval_summary_rejects_inverted_bounds() -> None:
    frame = _frame().with_columns(pl.lit(2.0).alias("projected_war_lower"))
    with pytest.raises(ValueError, match="invalid intervals"):
        summarize_interval_coverage(frame)


def test_probability_calibration_uses_fixed_forecast_bands() -> None:
    frame = pl.DataFrame(
        {
            "probability": [0.05, 0.20, 0.50, 0.90],
            "observed": [0, 0, 1, 1],
        }
    )
    result = summarize_binary_probability_calibration(
        frame,
        probability_column="probability",
        outcome_column="observed",
        minimum_bin_size=1,
    )
    assert result["players"] == 4
    assert result["brier"] == pytest.approx((0.05**2 + 0.20**2 + 0.50**2 + 0.10**2) / 4)
    assert len(result["fixed_probability_bands"]) == 4
    assert all(row["decision_eligible"] for row in result["fixed_probability_bands"])


def test_normal_reference_calibration_reports_fixed_quantiles_and_pit() -> None:
    result = summarize_normal_reference_calibration(_frame())
    assert result["positive_variance_players"] == 3
    assert result["zero_variance_players_excluded"] == 1
    assert len(result["fixed_pit_bin_counts"]) == 10
    assert sum(result["fixed_pit_bin_counts"]) == 3
    assert [row["nominal_quantile"] for row in result["fixed_quantile_calibration"]] == [
        0.10,
        0.25,
        0.50,
        0.75,
        0.90,
    ]


def test_normal_reference_calibration_requires_positive_variance() -> None:
    with pytest.raises(ValueError, match="positive variance"):
        summarize_normal_reference_calibration(
            _frame().with_columns(pl.lit(0.0).alias("annual_war_variance"))
        )
