from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.pitcher_baseline import (
    PITCHER_HISTORY_SCHEMA,
    PITCHER_RATE_COLUMNS,
    build_pitcher_component_baseline,
    score_pitcher_component_rates,
)


def _row(
    player_id: int,
    season: int,
    *,
    games: int = 20,
    starts: int = 0,
    bf: int = 300,
    so: int = 75,
    ubb: int = 24,
    hbp: int = 3,
    hr: int = 12,
) -> dict[str, int]:
    return {
        "season": season,
        "player_id": player_id,
        "pitching_games": games,
        "pitching_starts": starts,
        "pitching_bf": bf,
        "pitching_so": so,
        "pitching_ubb": ubb,
        "pitching_hbp": hbp,
        "pitching_hr": hr,
    }


def _history(rows: list[dict[str, int]]) -> pl.DataFrame:
    return pl.DataFrame(rows, schema=PITCHER_HISTORY_SCHEMA)


def _players(*ids: int) -> pl.DataFrame:
    return pl.DataFrame({"player_id": ids}, schema={"player_id": pl.Int64})


def test_baseline_returns_every_player_and_probability_simplex() -> None:
    result = build_pitcher_component_baseline(
        _players(1, 2, 99),
        _history([_row(1, 2022), _row(2, 2022, starts=15)]),
        forecast_season=2023,
    )
    assert result.get_column("player_id").to_list() == [1, 2, 99]
    sums = result.select(pl.sum_horizontal(*PITCHER_RATE_COLUMNS).alias("sum"))
    assert sums.filter((pl.col("sum") - 1.0).abs() > 1e-12).is_empty()
    no_history = result.filter(pl.col("player_id") == 99).row(0, named=True)
    assert no_history["reliability"] == 0.0
    assert no_history["weighted_history_bf"] == 0.0
    assert no_history["most_recent_history_season"] is None


def test_three_two_one_recency_weights_are_applied() -> None:
    result = build_pitcher_component_baseline(
        _players(1),
        _history(
            [
                _row(1, 2020, bf=100, so=25, ubb=8, hbp=1, hr=4),
                _row(1, 2021, bf=100, so=25, ubb=8, hbp=1, hr=4),
                _row(1, 2022, bf=100, so=25, ubb=8, hbp=1, hr=4),
                _row(2, 2022, bf=100, so=25, ubb=8, hbp=1, hr=4),
            ]
        ),
        forecast_season=2023,
    ).row(0, named=True)
    assert result["weighted_history_bf"] == 600.0
    assert result["reliability"] == 0.75


def test_role_is_projected_separately_from_component_rates() -> None:
    result = build_pitcher_component_baseline(
        _players(1, 2),
        _history(
            [
                _row(1, 2022, games=30, starts=0),
                _row(2, 2022, games=20, starts=20),
            ]
        ),
        forecast_season=2023,
    )
    roles = dict(result.select("player_id", "predicted_role").iter_rows())
    assert roles == {1: "reliever", 2: "starter"}


def test_history_at_or_after_forecast_is_rejected() -> None:
    with pytest.raises(ValueError, match="crosses forecast cutoff"):
        build_pitcher_component_baseline(
            _players(1),
            _history([_row(1, 2023)]),
            forecast_season=2023,
        )


def test_invalid_component_counts_are_rejected() -> None:
    with pytest.raises(ValueError, match="component relationships"):
        build_pitcher_component_baseline(
            _players(1),
            _history([_row(1, 2022, bf=100, so=90, ubb=20)]),
            forecast_season=2023,
        )


def test_regression_strengths_must_be_positive() -> None:
    with pytest.raises(ValueError, match="regression strengths"):
        build_pitcher_component_baseline(
            _players(1),
            _history([_row(1, 2022)]),
            forecast_season=2023,
            regression_bf=0,
        )


def test_component_scorer_reports_finite_log_loss_and_calibration() -> None:
    target = _history([_row(1, 2022), _row(2, 2022, starts=15)])
    predictions = build_pitcher_component_baseline(
        _players(1, 2),
        _history([_row(1, 2021), _row(2, 2021, starts=15)]),
        forecast_season=2022,
    )
    metrics = score_pitcher_component_rates(predictions, target)
    assert metrics["players"] == 2
    assert metrics["batters_faced"] == 600
    assert metrics["bf_weighted_component_log_loss"] > 0
    assert set(metrics["calibration"]) == {"so", "ubb", "hbp", "hr", "other"}


def test_component_scorer_rejects_target_selected_coverage_mismatch() -> None:
    target = _history([_row(1, 2022), _row(2, 2022)])
    predictions = build_pitcher_component_baseline(
        _players(1),
        _history([_row(1, 2021), _row(2, 2021)]),
        forecast_season=2022,
    )
    with pytest.raises(ValueError, match="coverage differs"):
        score_pitcher_component_rates(predictions, target)
