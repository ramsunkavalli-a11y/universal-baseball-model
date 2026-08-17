from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_contact_value import fit_contact_value_baseline
from universal_baseball.current_talent_contact_value_baseline import (
    fit_contact_value_baseline_from_cells,
    fit_contact_value_baseline_sufficient_statistics,
    summarize_contact_value_baseline_cells,
)
from universal_baseball.performance_season import CONTACT_CORE_BINS


def _weighted_fixture() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for level_index, level in enumerate(("MLB", "AAA", "AA")):
        level_effect = -0.12 * level_index
        for bin_index, contact_bin in enumerate(CONTACT_CORE_BINS):
            bin_effect = 0.025 * bin_index
            count = 1 + ((bin_index + 2 * level_index) % 5)
            for repeat in range(count):
                rows.append(
                    {
                        "event_date": date(2021, 7, 10),
                        "contact_bin": contact_bin,
                        "level_group": level,
                        "terminal_value": 0.2
                        + bin_effect
                        + level_effect
                        + 0.001 * (repeat - (count - 1) / 2),
                    }
                )
    rows.append(
        {
            "event_date": date(2021, 7, 15),
            "contact_bin": "IFFB",
            "level_group": "MLB",
            "terminal_value": 999.0,
        }
    )
    return pl.DataFrame(rows)


def test_sufficient_statistics_fit_matches_original_eventwise_fit() -> None:
    cutoff = date(2021, 7, 15)
    frame = _weighted_fixture()
    original = fit_contact_value_baseline(frame, cutoff_date=cutoff)
    fast, cells = fit_contact_value_baseline_sufficient_statistics(frame, cutoff_date=cutoff)

    assert cells.height == len(CONTACT_CORE_BINS) * 3
    assert fast.fitted_event_count == original.fitted_event_count
    assert fast.parameter_count == original.parameter_count
    assert fast.max_training_event_date == original.max_training_event_date
    assert fast.fitted_level_groups == original.fitted_level_groups
    assert fast.intercept == pytest.approx(original.intercept, abs=1e-12)
    for contact_bin in CONTACT_CORE_BINS:
        assert fast.contact_bin_effects[contact_bin] == pytest.approx(
            original.contact_bin_effects[contact_bin], abs=1e-12
        )
    for level in ("MLB", "AAA", "AA"):
        assert fast.level_group_effects[level] == pytest.approx(
            original.level_group_effects[level], abs=1e-12
        )


def test_cell_summary_is_strictly_pre_cutoff_and_preserves_event_weight() -> None:
    cutoff = date(2021, 7, 15)
    frame = _weighted_fixture()
    cells, max_event_date, event_count = summarize_contact_value_baseline_cells(
        frame, cutoff_date=cutoff
    )
    assert max_event_date == date(2021, 7, 10)
    assert event_count == frame.filter(pl.col("event_date") < cutoff).height
    assert cells.get_column("event_count").sum() == event_count
    assert cells.get_column("terminal_value_sum").sum() == pytest.approx(
        frame.filter(pl.col("event_date") < cutoff).get_column("terminal_value").sum(),
        abs=1e-12,
    )


def test_fit_from_cells_rejects_event_count_mismatch() -> None:
    cutoff = date(2021, 7, 15)
    cells, max_event_date, event_count = summarize_contact_value_baseline_cells(
        _weighted_fixture(), cutoff_date=cutoff
    )
    with pytest.raises(ValueError, match="fitted_event_count disagrees"):
        fit_contact_value_baseline_from_cells(
            cells,
            cutoff_date=cutoff,
            max_training_event_date=max_event_date,
            fitted_event_count=event_count + 1,
        )


def test_fit_from_cells_preserves_rank_deficiency_failure() -> None:
    rows: list[dict[str, object]] = []
    for contact_bin in CONTACT_CORE_BINS:
        level = "AAA" if contact_bin == "OPPO_GB" else "MLB"
        rows.append(
            {
                "event_date": date(2021, 7, 1),
                "contact_bin": contact_bin,
                "level_group": level,
                "terminal_value": 0.1,
            }
        )
    with pytest.raises(ValueError, match="rank deficient"):
        fit_contact_value_baseline_sufficient_statistics(
            pl.DataFrame(rows), cutoff_date=date(2021, 7, 15)
        )
