import polars as pl
import pytest

from universal_baseball.workload_uncertainty_validation import (
    summarize_positive_workload_coverage,
    zero_truncated_nb2_quantile,
)


def test_zero_truncated_nb2_quantiles_are_positive_and_ordered() -> None:
    lower = zero_truncated_nb2_quantile(0.1, positive_mean=300.0, alpha=0.5)
    upper = zero_truncated_nb2_quantile(0.9, positive_mean=300.0, alpha=0.5)
    assert 1 <= lower < upper


def test_positive_workload_coverage_excludes_zero_outcomes() -> None:
    result = summarize_positive_workload_coverage(
        pl.DataFrame(
            {
                "conditional_mean": [300.0, 300.0, 300.0],
                "nb_alpha": [0.5, 0.5, 0.5],
                "observed_workload": [0.0, 300.0, 1000.0],
            }
        )
    )
    assert result["active_players"] == 2
    assert result["coverage"] == pytest.approx(0.5)
    assert result["upper_miss_rate"] == pytest.approx(0.5)
