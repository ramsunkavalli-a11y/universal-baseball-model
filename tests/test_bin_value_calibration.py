from __future__ import annotations

import math

import polars as pl
import pytest

from universal_baseball.bin_value_calibration import (
    bin_calibration_coverage,
    summarize_direct_bin_values,
)


def test_direct_bin_calibration_returns_mean_sd_and_standard_error() -> None:
    events = pl.DataFrame(
        {
            "season": [2024, 2024, 2024, 2024],
            "league_id": [112, 112, 112, 112],
            "core_bin": ["K", "K", "K", "BB_HBP"],
            "re24": [-0.1, -0.2, 0.0, 0.4],
        }
    )
    result = summarize_direct_bin_values(events)
    strikeout = result.filter(pl.col("core_bin") == "K").to_dicts()[0]
    assert strikeout["occurrence_count"] == 3
    assert strikeout["mean_run_value"] == pytest.approx(-0.1)
    assert strikeout["run_value_std_dev"] == pytest.approx(0.1)
    assert strikeout["standard_error"] == pytest.approx(0.1 / math.sqrt(3))

    walk = result.filter(pl.col("core_bin") == "BB_HBP").to_dicts()[0]
    assert walk["occurrence_count"] == 1
    assert walk["mean_run_value"] == pytest.approx(0.4)
    assert walk["run_value_std_dev"] is None
    assert walk["standard_error"] is None


def test_legacy_opposite_label_normalizes_to_production_oppo_vocabulary() -> None:
    events = pl.DataFrame(
        {
            "season": [2024, 2024],
            "league_id": [112, 112],
            "core_bin": ["OPPOSITE_GB", "OPPOSITE_GB"],
            "re24": [0.1, 0.3],
        }
    )
    value = summarize_direct_bin_values(events).to_dicts()[0]
    assert value["core_bin"] == "OPPO_GB"
    assert value["occurrence_count"] == 2
    assert value["mean_run_value"] == pytest.approx(0.2)

    coverage = bin_calibration_coverage(events).to_dicts()[0]
    assert coverage["core_bin"] == "OPPO_GB"
    assert coverage["event_count"] == 2


def test_missing_re24_is_excluded_from_mean_but_visible_in_coverage() -> None:
    events = pl.DataFrame(
        {
            "season": [2024, 2024, 2024],
            "league_id": [112, 112, 112],
            "core_bin": ["PULL_GB", "PULL_GB", "PULL_GB"],
            "re24": [0.1, None, 0.3],
        },
        schema_overrides={"re24": pl.Float64},
    )
    value = summarize_direct_bin_values(events).to_dicts()[0]
    assert value["occurrence_count"] == 2
    assert value["mean_run_value"] == pytest.approx(0.2)

    coverage = bin_calibration_coverage(events).to_dicts()[0]
    assert coverage["event_count"] == 3
    assert coverage["valued_event_count"] == 2
    assert coverage["missing_re24_count"] == 1
    assert coverage["re24_coverage_rate"] == pytest.approx(2 / 3)


def test_non_core_bin_is_rejected() -> None:
    events = pl.DataFrame(
        {
            "season": [2024],
            "league_id": [112],
            "core_bin": ["BUNT"],
            "re24": [0.1],
        }
    )
    with pytest.raises(ValueError, match="non-core"):
        summarize_direct_bin_values(events)
