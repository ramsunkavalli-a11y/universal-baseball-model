import polars as pl
import pytest

from universal_baseball.historical_war_scoring import (
    score_hitter_neutral_war,
    score_pitcher_neutral_war,
    whole_player_war_metrics,
)


def _hitting(player_id: int = 1) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "player_id": [player_id],
            "batting_plate_appearances": [10],
            "batting_hits": [3],
            "batting_doubles": [1],
            "batting_triples": [0],
            "batting_home_runs": [1],
            "batting_base_on_balls": [1],
            "batting_intentional_walks": [0],
            "batting_hit_by_pitch": [0],
        }
    )


def _pitching(player_id: int = 1) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "player_id": [player_id],
            "pitching_batters_faced": [10],
            "pitching_strike_outs": [2],
            "pitching_base_on_balls": [1],
            "pitching_intentional_walks": [0],
            "pitching_hit_batsmen": [0],
            "pitching_home_runs": [1],
        }
    )


def test_hitter_score_retains_player_without_outcome_as_zero() -> None:
    projections = pl.DataFrame(
        {
            "player_id": [1, 2],
            "expected_war": [0.2, 0.1],
            "positional_runs_per_600": [0.0, 0.0],
            "replacement_runs_per_600": [18.0, 18.0],
            "predicted_ubb_rate": [0.1, 0.1],
            "predicted_hbp_rate": [0.0, 0.0],
            "predicted_single_rate": [0.1, 0.1],
            "predicted_double_rate": [0.1, 0.1],
            "predicted_triple_rate": [0.0, 0.0],
            "predicted_hr_rate": [0.1, 0.1],
            "predicted_other_rate": [0.6, 0.6],
        }
    )
    scored, metrics = score_hitter_neutral_war(
        projections, _hitting(), _hitting(), runs_per_win=10.0
    )

    assert scored.filter(pl.col("player_id") == 2).item(
        0, "observed_neutral_war"
    ) == 0.0
    assert metrics["positive_workload_players"] == 1
    assert metrics["model_minus_population_component_log_loss"] == pytest.approx(0)


def test_pitcher_score_and_whole_player_sum_components() -> None:
    projections = pl.DataFrame(
        {
            "player_id": [1],
            "expected_war": [0.3],
            "replacement_runs_per_800": [18.0],
            "predicted_so_rate": [0.2],
            "predicted_ubb_rate": [0.1],
            "predicted_hbp_rate": [0.0],
            "predicted_hr_rate": [0.1],
            "predicted_other_rate": [0.6],
        }
    )
    pitcher, metrics = score_pitcher_neutral_war(
        projections, _pitching(), _pitching(), runs_per_win=10.0
    )
    hitter, _ = score_hitter_neutral_war(
        pl.DataFrame(
            {
                "player_id": [1],
                "expected_war": [0.2],
                "positional_runs_per_600": [0.0],
                "replacement_runs_per_600": [18.0],
                "predicted_ubb_rate": [0.1],
                "predicted_hbp_rate": [0.0],
                "predicted_single_rate": [0.1],
                "predicted_double_rate": [0.1],
                "predicted_triple_rate": [0.0],
                "predicted_hr_rate": [0.1],
                "predicted_other_rate": [0.6],
            }
        ),
        _hitting(),
        _hitting(),
        runs_per_win=10.0,
    )
    whole, whole_metrics = whole_player_war_metrics(hitter, pitcher)

    assert metrics["model_minus_population_component_log_loss"] == pytest.approx(0)
    assert whole.item(0, "expected_war") == pytest.approx(0.5)
    assert whole_metrics["players"] == 1
