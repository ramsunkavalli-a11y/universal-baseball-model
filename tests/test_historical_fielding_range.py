from __future__ import annotations

import polars as pl

from universal_baseball.historical_fielding_range import (
    aggregate_player_fielding_seasons,
    evaluate_fielding_projection,
    project_player_fielding_rates,
    score_contextual_fielding_residuals,
    score_joint_park_defense_fielding_residuals,
    score_visitor_anchored_park_fielding_residuals,
)


def _opportunities() -> pl.DataFrame:
    rows = []
    for season in (2021, 2022, 2023):
        for index in range(80):
            fielder = 10 if index % 2 == 0 else 20
            actual = 1 if (fielder == 10 or index % 5 == 0) else 0
            rows.append(
                {
                    "season": season,
                    "level": "aaa",
                    "game_pk": season * 1000 + index // 10,
                    "at_bat_index": index,
                    "responsible_position": 6,
                    "responsible_fielder_id": fielder,
                    "conversion_out": actual,
                    "bb_type": "ground_ball",
                    "stand": "R" if index % 3 else "L",
                    "p_throws": "R",
                    "park_key": f"{season}:AAA",
                    "batter": 1000 + index,
                    "hc_x": 100.0 + index % 4,
                    "hc_y": 75.0 + index % 3,
                }
            )
    return pl.DataFrame(rows)


def test_contextual_range_scoring_and_aggregation() -> None:
    scored = score_contextual_fielding_residuals(_opportunities())
    assert scored.height == 240
    assert scored.get_column("expected_out_probability").min() > 0
    assert scored.get_column("expected_out_probability").max() < 1

    seasons = aggregate_player_fielding_seasons(scored)
    better = seasons.filter(pl.col("responsible_fielder_id") == 10)
    worse = seasons.filter(pl.col("responsible_fielder_id") == 20)
    assert better.get_column("fielding_outs_above_expected_rate").mean() > 0
    assert worse.get_column("fielding_outs_above_expected_rate").mean() < 0


def test_projection_uses_only_prior_seasons_and_shrinks() -> None:
    seasons = aggregate_player_fielding_seasons(
        score_contextual_fielding_residuals(_opportunities())
    )
    projected = project_player_fielding_rates(
        seasons, target_season=2023, regression_opportunities=100
    )
    assert projected.height == 2
    assert projected.get_column("history_seasons").to_list() == [2, 2]
    assert projected.filter(pl.col("responsible_fielder_id") == 10).item(
        0, "projected_range_rate"
    ) > 0

    paired, metrics = evaluate_fielding_projection(
        seasons,
        target_season=2023,
        regression_opportunities=100,
        minimum_target_opportunities=25,
    )
    assert paired.height == 2
    assert metrics["player_position_count"] == 2
    assert metrics["candidate_rmse"] < metrics["neutral_rmse"]


def test_no_park_baseline_and_joint_effects_separate_park_from_team() -> None:
    rows = []
    players = {"A": 10, "B": 20, "C": 30, "D": 40}
    for game_index in range(80):
        park = "A" if game_index % 2 == 0 else "B"
        visitor = "C" if game_index % 3 else "D"
        for defense_team in (park, visitor):
            # Park A is genuinely difficult for every defense; team C is good
            # regardless of which park it visits.
            actual = int(park != "A" or defense_team == "C")
            rows.append(
                {
                    "season": 2023,
                    "level": "aaa",
                    "game_pk": 1000 + game_index,
                    "at_bat_index": len(rows),
                    "responsible_position": 6,
                    "responsible_fielder_id": players[defense_team],
                    "conversion_out": actual,
                    "bb_type": "ground_ball",
                    "stand": "R",
                    "p_throws": "R",
                    "park_key": f"2023:{park}",
                    "batter": 10000 + len(rows),
                    "hc_x": 110.0,
                    "hc_y": 80.0,
                    "defense_team": defense_team,
                    "home_team": park,
                }
            )
    opportunities = pl.DataFrame(rows)
    no_park = score_contextual_fielding_residuals(
        opportunities, use_park_adjustment=False
    )
    assert no_park.get_column("park_expected_out").equals(
        no_park.get_column("context_expected_out")
    )

    joint = score_joint_park_defense_fielding_residuals(
        opportunities,
        park_prior=10,
        team_prior=10,
        player_prior=10,
        iterations=6,
    )
    park_effects = joint.group_by("park_context").agg(
        pl.col("joint_park_effect").mean().alias("effect")
    )
    assert park_effects.filter(pl.col("park_context") == "2023:A").item(
        0, "effect"
    ) < park_effects.filter(pl.col("park_context") == "2023:B").item(0, "effect")
    assert joint.filter(pl.col("defense_is_home")).height == 80

    visitor_anchored = score_visitor_anchored_park_fielding_residuals(
        opportunities, park_prior=10
    )
    visitor_effects = visitor_anchored.group_by("park_context").agg(
        pl.col("visitor_park_effect").mean().alias("effect")
    )
    assert visitor_effects.filter(pl.col("park_context") == "2023:A").item(
        0, "effect"
    ) < visitor_effects.filter(pl.col("park_context") == "2023:B").item(0, "effect")
