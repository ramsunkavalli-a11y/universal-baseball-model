from datetime import date

import polars as pl
import pytest

from scripts.materialize_current_talent_batted_ball_development import (
    DEVELOPMENT_CUTOFFS,
    MEANINGFUL_NON_MLB_FUTURE_CORE_EVENTS,
    TRAINING_CUTOFF,
    _load_tracking,
    _mean_pair_delta,
    _non_mlb_guardrails,
)
from universal_baseball.current_talent_batted_ball_reconciliation import (
    RECONCILED_TRACKED_BBE_SCHEMA,
)


def _tracking(season: int) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_date": [date(season, 6, 1)],
            "game_pk": [1],
            "player_id": [10],
            "at_bat_number": [1],
            "pitch_number": [3],
            "launch_speed": [98.0],
            "launch_angle": [18.0],
            "sweet_spot": [True],
            "season": [season],
            "league_id": [117],
            "level_group": ["AAA"],
            "source_family": ["MILB_SAVANT_TRACKED"],
            "source_capability_tier": [f"MILB_SAVANT_TRACKED:{season}:117:AAA"],
        }
    ).cast(RECONCILED_TRACKED_BBE_SCHEMA, strict=True)


def test_development_dates_are_frozen_and_contain_no_confirmation_fold() -> None:
    assert TRAINING_CUTOFF == date(2021, 7, 15)
    assert DEVELOPMENT_CUTOFFS == (
        date(2022, 7, 15),
        date(2022, 8, 1),
        date(2022, 9, 1),
    )
    assert all(value.year == 2022 for value in DEVELOPMENT_CUTOFFS)
    assert MEANINGFUL_NON_MLB_FUTURE_CORE_EVENTS == 1000


def test_tracking_loader_fails_closed_on_wrong_season(tmp_path) -> None:
    path = tmp_path / "tracking.parquet"
    _tracking(2022).write_parquet(path)

    with pytest.raises(ValueError, match="season mismatch"):
        _load_tracking(path, 2021)

    observed = _load_tracking(path, 2022)
    assert observed.schema == RECONCILED_TRACKED_BBE_SCHEMA
    assert observed.height == 1


def _paired_capability_rows(*, support_per_fold: int, worse_folds: set[date]) -> pl.DataFrame:
    rows = []
    tier = "MILB_SAVANT_TRACKED:2022:117:AAA"
    for cutoff in DEVELOPMENT_CUTOFFS:
        for model in ("baseline2", "batted_ball_richer"):
            b2_log = 2.0
            b2_brier = 0.80
            worse = cutoff in worse_folds and model == "batted_ball_richer"
            rows.append(
                {
                    "as_of_date": cutoff,
                    "source_capability_tier": tier,
                    "model": model,
                    "future_core_events": support_per_fold,
                    "player_count": 20,
                    "event_weighted_log_loss": b2_log + (0.01 if worse else (-0.01 if model == "batted_ball_richer" else 0.0)),
                    "event_weighted_multinomial_brier": b2_brier + (0.01 if worse else (-0.01 if model == "batted_ball_richer" else 0.0)),
                    "non_mlb_source_tier": True,
                }
            )
    return pl.DataFrame(rows)


def test_non_mlb_tier_guardrail_requires_meaningful_support_before_hard_failure() -> None:
    low_support = _paired_capability_rows(
        support_per_fold=100,
        worse_folds={DEVELOPMENT_CUTOFFS[0], DEVELOPMENT_CUTOFFS[1]},
    )
    summary, failures = _non_mlb_guardrails(low_support)
    assert failures == []
    assert summary["tier_diagnostics"][0]["meaningfully_supported"] is False

    meaningful = _paired_capability_rows(
        support_per_fold=400,
        worse_folds={DEVELOPMENT_CUTOFFS[0], DEVELOPMENT_CUTOFFS[1]},
    )
    summary, failures = _non_mlb_guardrails(meaningful)
    assert summary["tier_diagnostics"][0]["future_core_events"] == 1200
    assert summary["tier_diagnostics"][0]["meaningfully_supported"] is True
    assert len(failures) == 1
    assert failures[0]["worse_on_both_fold_count"] == 2


def test_equal_fold_mean_delta_does_not_event_weight_folds_again() -> None:
    rows = []
    for index, cutoff in enumerate(DEVELOPMENT_CUTOFFS):
        b2 = 2.0
        richer_delta = (-0.03, 0.01, -0.03)[index]
        for model, value in (
            ("baseline2", b2),
            ("batted_ball_richer", b2 + richer_delta),
        ):
            rows.append(
                {
                    "as_of_date": cutoff,
                    "model": model,
                    "future_core_events": (100, 100000, 100)[index],
                    "event_weighted_log_loss": value,
                    "event_weighted_multinomial_brier": 0.8,
                }
            )
    frame = pl.DataFrame(rows)

    assert _mean_pair_delta(frame, "event_weighted_log_loss") == pytest.approx(
        (-0.03 + 0.01 - 0.03) / 3
    )
