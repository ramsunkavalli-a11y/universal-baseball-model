from datetime import date

import polars as pl
import pytest

from universal_baseball.projection_checkpoint_comparison import (
    compare_projection_checkpoints,
)


def _frame(as_of: date, rows: list[tuple[int, int, float, float]]) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "as_of_date": as_of,
                "player_id": player_id,
                "season": season,
                "expected_mlb_pa": workload,
                "conditional_war_per_600_pa": rate,
                "expected_war": workload * rate / 600.0,
            }
            for player_id, season, workload, rate in rows
        ]
    )


def test_checkpoint_comparison_separates_universe_and_reconciles_effects() -> None:
    earlier = _frame(
        date(2025, 3, 27), [(1, 2026, 300.0, 2.0), (2, 2026, 100.0, 1.0)]
    )
    later = _frame(
        date(2025, 10, 15), [(1, 2026, 360.0, 3.0), (3, 2026, 200.0, 2.0)]
    )
    changes, universe = compare_projection_checkpoints(
        earlier,
        later,
        component="hitter",
        workload_column="expected_mlb_pa",
        rate_column="conditional_war_per_600_pa",
        workload_unit=600.0,
    )
    row = changes.row(0, named=True)
    assert row["expected_war_delta"] == pytest.approx(0.8)
    assert row["opportunity_effect_war"] == pytest.approx(0.2)
    assert row["skill_effect_war"] == pytest.approx(0.6)
    assert row["decomposition_residual_war"] == pytest.approx(0.0)
    assert dict(universe.group_by("universe_status").len().iter_rows()) == {
        "departed": 1,
        "new": 1,
        "retained": 1,
    }


def test_checkpoint_comparison_rejects_reversed_dates() -> None:
    frame = _frame(date(2025, 3, 27), [(1, 2026, 300.0, 2.0)])
    with pytest.raises(ValueError, match="increasing as-of date"):
        compare_projection_checkpoints(
            frame,
            frame,
            component="hitter",
            workload_column="expected_mlb_pa",
            rate_column="conditional_war_per_600_pa",
            workload_unit=600.0,
        )
