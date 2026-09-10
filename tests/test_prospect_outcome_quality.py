from datetime import date

import polars as pl
import pytest

from universal_baseball.prospect_outcome_quality import (
    build_post_debut_workload_paths,
    summarize_three_tier_workload_priors,
    summarize_workload_priors,
    workload_prior,
)


def test_post_debut_paths_keep_zeros_and_scale_shortened_2020() -> None:
    people = pl.DataFrame(
        {
            "player_id": [1, 2],
            "mlb_debut_date": [date(2019, 4, 1), date(2020, 7, 24)],
        }
    )
    stats = pl.DataFrame(
        {
            "season": [2019, 2020, 2024],
            "player_id": [1, 1, 1],
            "batting_pa": [50, 100, 200],
        }
    )
    result = build_post_debut_workload_paths(
        people, stats, player_type="hitter", horizon=6
    )
    assert result.get_column("player_id").to_list() == [1]
    assert result.item(0, "adjusted_total_workload") == pytest.approx(520.0)
    assert result.item(0, "active_seasons") == 3
    assert result.item(0, "meaningful_seasons") == 2
    assert result.item(0, "outcome_tier") == "meaningful"
    assert result.item(0, "outcome_tier_v2") == "meaningful_only"


def test_pitcher_paths_assign_role_and_keep_regular_seasons_diagnostic() -> None:
    people = pl.DataFrame(
        {"player_id": [1], "mlb_debut_date": [date(2015, 4, 1)]}
    )
    stats = pl.DataFrame(
        {
            "season": [2015, 2016, 2020],
            "player_id": [1, 1, 1],
            "pitching_bf": [600, 500, 100],
            "pitching_games": [30, 25, 10],
            "pitching_starts": [30, 20, 0],
        }
    )
    result = build_post_debut_workload_paths(
        people, stats, player_type="pitcher", horizon=6
    )
    assert result.item(0, "career_role") == "starter"
    assert result.item(0, "outcome_tier") == "meaningful"
    assert result.item(0, "regular_seasons") == 2
    assert result.item(0, "outcome_tier_v2") == "established"
    summary = summarize_workload_priors(result)
    assert summary.height == 2
    value, source = workload_prior(
        summary,
        player_type="pitcher",
        outcome_tier="meaningful",
        career_role="starter",
        minimum_role_players=2,
    )
    assert value == pytest.approx(1370.0)
    assert source == "pooled"
    three_tier = summarize_three_tier_workload_priors(result)
    assert set(three_tier.get_column("outcome_tier")) == {"established"}


def test_outcome_quality_requires_complete_cohort() -> None:
    people = pl.DataFrame(
        {"player_id": [1], "mlb_debut_date": [date(2024, 4, 1)]}
    )
    stats = pl.DataFrame(
        {"season": [2024], "player_id": [1], "batting_pa": [10]}
    )
    with pytest.raises(ValueError, match="no complete"):
        build_post_debut_workload_paths(
            people, stats, player_type="hitter", horizon=6
        )
