import polars as pl
import pytest

from universal_baseball.war_uncertainty_validation import (
    summarize_interval_coverage,
    summarize_named_slices,
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
