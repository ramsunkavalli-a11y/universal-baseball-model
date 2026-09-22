from datetime import date

import polars as pl
import pytest

from universal_baseball.hitter_ball_environment import (
    add_ball_environment_history,
    aggregate_player_ball_features,
    apply_crossfit_regime_adjustments,
    prepare_air_contact_history,
)


def _event(
    day: int,
    game: int,
    batter: int,
    pitcher: int,
    outcome: str,
) -> dict[str, object]:
    return {
        "season": 2024,
        "league_id": 1,
        "level": "AAA",
        "game_date": date(2024, 4, day),
        "game_pk": game,
        "at_bat_index": 1,
        "player_id": batter,
        "pitcher": pitcher,
        "core_bin": "PULL_OFFB",
        "canonical_outcome": outcome,
    }


def test_prior_quality_excludes_current_day() -> None:
    events = pl.DataFrame(
        [
            _event(1, 10, 1, 8, "HR"),
            _event(1, 11, 1, 8, "OTHER_OUT"),
            _event(2, 12, 1, 8, "OTHER_OUT"),
        ]
    )
    result = prepare_air_contact_history(events, prior_exposure=10, prior_rate=0.1)

    assert result.filter(pl.col("game_date") == date(2024, 4, 1))[
        "prior_hitter_air_contacts"
    ].to_list() == [0, 0]
    assert (
        result.filter(pl.col("game_date") == date(2024, 4, 2)).item(
            0, "prior_hitter_air_contacts"
        )
        == 2
    )
    assert (
        result.filter(pl.col("game_date") == date(2024, 4, 2)).item(
            0, "prior_hitter_air_hr"
        )
        == 1
    )


def test_regime_adjustment_is_estimated_on_other_games() -> None:
    events = pl.DataFrame(
        {
            "game_date": [date(2024, 4, 1)] * 4,
            "game_pk": [10, 12, 11, 13],
            "at_bat_index": [1, 1, 1, 1],
            "ball_regime_key": ["AAA|2024|0"] * 4,
            "ball_crossfit_fold": [0, 0, 1, 1],
            "is_hr": [1, 1, 0, 0],
            "base_hr_probability": [0.1] * 4,
        }
    )
    adjusted, fitted = apply_crossfit_regime_adjustments(events, prior_exposure=2)

    fold_zero = adjusted.filter(pl.col("ball_crossfit_fold") == 0)
    fold_one = adjusted.filter(pl.col("ball_crossfit_fold") == 1)
    assert fold_zero["ball_regime_log_odds"].max() < 0
    assert fold_one["ball_regime_log_odds"].min() > 0
    assert fitted.height == 2


def test_player_features_and_exact_lags() -> None:
    events = pl.DataFrame(
        {
            "season": [2024, 2024],
            "player_id": [1, 1],
            "is_hr": [1, 0],
            "ball_regime_log_odds": [0.2, -0.1],
            "ball_probability_effect": [0.02, -0.01],
        }
    )
    annual = aggregate_player_ball_features(events)
    panel = pl.DataFrame({"origin_year": [2024, 2025], "player_id": [1, 1]})
    result = add_ball_environment_history(panel, annual)

    assert annual.item(0, "ball_neutralized_air_hr_rate") == pytest.approx(0.495)
    assert result["lag0__ball__available"].to_list() == [1, 0]
    assert result["lag1__ball__available"].to_list() == [0, 1]
