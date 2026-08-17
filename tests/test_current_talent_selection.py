from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_selection import summarize_selection_grid


def _row(
    candidate_id: str,
    cutoff: date,
    *,
    log_loss: float,
    brier: float,
    half_life: float,
    prior_strength: float,
    translation: str,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "season": cutoff.year,
        "as_of_date": cutoff,
        "half_life_days": half_life,
        "prior_strength_core_events": prior_strength,
        "translation_variant": translation,
        "scored_player_count": 100,
        "scored_target_environment_count": 120,
        "future_core_events": 10_000,
        "baseline0_log_loss": 2.30,
        "baseline1_log_loss": log_loss,
        "baseline1_minus_baseline0_log_loss": log_loss - 2.30,
        "baseline0_brier": 0.88,
        "baseline1_brier": brier,
        "baseline1_minus_baseline0_brier": brier - 0.88,
        "baseline0_mean_abs_calibration_intercept_error": 0.8,
        "baseline1_mean_abs_calibration_intercept_error": 0.5,
        "baseline0_mean_abs_calibration_slope_error": 0.3,
        "baseline1_mean_abs_calibration_slope_error": 0.2,
        "baseline0_mean_ece": 0.003,
        "baseline1_mean_ece": 0.004,
    }


def test_selection_equal_weights_folds_and_uses_log_loss_primary() -> None:
    folds = [date(2021, 7, 15), date(2022, 7, 15)]
    rows = [
        _row(
            "a",
            folds[0],
            log_loss=2.10,
            brier=0.86,
            half_life=90,
            prior_strength=100,
            translation="fitted_translation",
        ),
        _row(
            "a",
            folds[1],
            log_loss=2.30,
            brier=0.86,
            half_life=90,
            prior_strength=100,
            translation="fitted_translation",
        ),
        _row(
            "b",
            folds[0],
            log_loss=2.19,
            brier=0.85,
            half_life=180,
            prior_strength=200,
            translation="zero_offset_translation",
        ),
        _row(
            "b",
            folds[1],
            log_loss=2.19,
            brier=0.85,
            half_life=180,
            prior_strength=200,
            translation="zero_offset_translation",
        ),
    ]
    summary = summarize_selection_grid(
        pl.DataFrame(rows),
        expected_fold_count=2,
        expected_candidate_count=2,
    )

    # A's mean is 2.20 despite a very strong first fold; B's equal-fold mean is
    # 2.19 and therefore wins the predeclared primary objective.
    assert summary.selected_candidate["candidate_id"] == "b"
    ranked = summary.ranked_candidates
    assert ranked.filter(pl.col("candidate_id") == "a").item(
        0, "mean_baseline1_log_loss"
    ) == pytest.approx(2.20)
    assert ranked.filter(pl.col("candidate_id") == "b").item(
        0, "mean_baseline1_log_loss"
    ) == pytest.approx(2.19)


def test_selection_marks_proper_score_pareto_frontier() -> None:
    folds = [date(2021, 7, 15), date(2022, 7, 15)]
    rows: list[dict[str, object]] = []
    for cutoff in folds:
        rows.extend(
            [
                _row(
                    "ll_best",
                    cutoff,
                    log_loss=2.18,
                    brier=0.86,
                    half_life=45,
                    prior_strength=50,
                    translation="fitted_translation",
                ),
                _row(
                    "brier_best",
                    cutoff,
                    log_loss=2.19,
                    brier=0.84,
                    half_life=90,
                    prior_strength=100,
                    translation="zero_offset_translation",
                ),
                _row(
                    "dominated",
                    cutoff,
                    log_loss=2.20,
                    brier=0.87,
                    half_life=180,
                    prior_strength=200,
                    translation="zero_offset_translation",
                ),
            ]
        )
    summary = summarize_selection_grid(
        pl.DataFrame(rows),
        expected_fold_count=2,
        expected_candidate_count=3,
    )
    frontier = set(
        summary.ranked_candidates.filter(pl.col("proper_score_pareto_frontier")).get_column(
            "candidate_id"
        )
    )
    assert frontier == {"ll_best", "brier_best"}
    assert summary.selected_candidate["candidate_id"] == "ll_best"


def test_selection_fails_when_candidate_coverage_differs_inside_fold() -> None:
    cutoff = date(2021, 7, 15)
    rows = [
        _row(
            "a",
            cutoff,
            log_loss=2.1,
            brier=0.85,
            half_life=90,
            prior_strength=100,
            translation="fitted_translation",
        ),
        _row(
            "b",
            cutoff,
            log_loss=2.1,
            brier=0.85,
            half_life=90,
            prior_strength=200,
            translation="fitted_translation",
        ),
    ]
    rows[1]["future_core_events"] = 9_999
    with pytest.raises(ValueError, match="coverage differs"):
        summarize_selection_grid(
            pl.DataFrame(rows),
            expected_fold_count=1,
            expected_candidate_count=2,
        )
