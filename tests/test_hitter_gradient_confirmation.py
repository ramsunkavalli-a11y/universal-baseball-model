from __future__ import annotations

import polars as pl

from universal_baseball.hitter_gradient_confirmation import (
    add_confirmation_strata,
    outcome_metrics,
    score_confirmation_rows,
)
from universal_baseball.hitter_gradient_materialization import CONTACT_OUTCOMES


def _rows() -> pl.DataFrame:
    values: dict[str, list[object]] = {
        "player_id": [1, 2],
        "source_level": ["a", "aa"],
        "target_source_level": ["a+", "a"],
        "contacts": [50, 175],
        "target_contacts": [100, 200],
    }
    for index, outcome in enumerate(CONTACT_OUTCOMES):
        actual = [0.6, 0.5] if index == 0 else [0.4 / 8, 0.5 / 8]
        base = [0.5, 0.4] if index == 0 else [0.5 / 8, 0.6 / 8]
        candidate = [0.58, 0.48] if index == 0 else [0.42 / 8, 0.52 / 8]
        values[f"actual__{outcome}"] = actual
        values[f"contact_only__{outcome}"] = base
        values[f"gradient__{outcome}"] = candidate
    return pl.DataFrame(values)


def test_confirmation_scores_better_candidate() -> None:
    result = score_confirmation_rows(_rows())
    assert result["players"] == 2
    assert result["gradient_vs_contact_only"]["rate_rmse"] < 0
    assert result["gradient_vs_contact_only"]["multinomial_log_loss"] < 0
    assert result["gradient_vs_contact_only"]["multinomial_brier"] < 0


def test_locked_strata_and_outcomes_are_complete() -> None:
    rows = add_confirmation_strata(_rows())
    assert rows["source_workload_group"].to_list() == ["30_to_74", "150_plus"]
    assert rows["level_transition"].to_list() == ["advanced", "demoted"]
    outcomes = outcome_metrics(rows)
    assert [row["outcome"] for row in outcomes] == list(CONTACT_OUTCOMES)
