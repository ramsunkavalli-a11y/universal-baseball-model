from __future__ import annotations

import math

import polars as pl

from universal_baseball.conditional_war_rates import (
    apply_tango_pitcher_aging,
    build_hitter_conditional_war_rates,
    build_pitcher_conditional_war_rates,
)


def _hitting_history() -> pl.DataFrame:
    rows = []
    for season, player_id, pa, hits, doubles, triples, hr, bb, ibb, hbp in (
        (2024, 1, 400, 100, 20, 2, 15, 40, 2, 4),
        (2025, 1, 500, 140, 25, 3, 25, 55, 2, 5),
        (2026, 1, 300, 90, 15, 2, 20, 35, 1, 3),
        (2025, 9, 600, 150, 30, 3, 20, 60, 3, 6),
    ):
        rows.append(
            {
                "season": season, "league_id": 103, "player_id": player_id,
                "batting_plate_appearances": pa, "batting_hits": hits,
                "batting_doubles": doubles, "batting_triples": triples,
                "batting_home_runs": hr, "batting_base_on_balls": bb,
                "batting_intentional_walks": ibb, "batting_hit_by_pitch": hbp,
            }
        )
    return pl.DataFrame(rows)


def _pitching_history() -> pl.DataFrame:
    rows = []
    for season, player_id, games, starts, bf, so, bb, ibb, hbp, hr in (
        (2024, 1, 30, 30, 700, 180, 55, 3, 6, 20),
        (2025, 1, 30, 30, 720, 190, 50, 2, 5, 18),
        (2026, 1, 20, 20, 480, 130, 36, 2, 4, 14),
        (2025, 9, 60, 0, 260, 70, 20, 2, 3, 8),
    ):
        rows.append(
            {
                "season": season, "league_id": 103, "player_id": player_id,
                "pitching_games_played": games, "pitching_games_started": starts,
                "pitching_batters_faced": bf, "pitching_strike_outs": so,
                "pitching_base_on_balls": bb, "pitching_intentional_walks": ibb,
                "pitching_hit_batsmen": hbp, "pitching_home_runs": hr,
            }
        )
    return pl.DataFrame(rows)


def test_tango_pitcher_aging_preserves_probability() -> None:
    source = {"so": 0.25, "ubb": 0.08, "hbp": 0.01, "hr": 0.03, "other": 0.63}
    aged = apply_tango_pitcher_aging(source, current_age=25.0, target_age=35.0)
    assert math.isclose(sum(aged.values()), 1.0)
    assert aged["so"] < source["so"]
    assert aged["hr"] > source["hr"]


def test_hitter_rates_cover_history_and_prior_players_for_each_year() -> None:
    players = pl.DataFrame(
        {"player_id": [1, 2], "age_years": [27.0, None], "position_code": ["6", "O"]}
    )
    result = build_hitter_conditional_war_rates(
        players, _hitting_history(), current_season=2026,
        forecast_seasons=(2027, 2028), reference_plate_appearances=1200,
        runs_per_win=10.0,
    )
    assert result.height == 4
    assert set(result.get_column("evidence_tier")) == {"mlb_history", "population_prior"}
    assert result.filter(pl.col("player_id") == 1).get_column("primary_position").unique().to_list() == ["SS"]
    assert result.get_column("conditional_war_per_600_pa").is_finite().all()


def test_hitter_rates_add_supplied_baserunning_runs() -> None:
    players = pl.DataFrame(
        {"player_id": [1], "age_years": [27.0], "position_code": ["6"]}
    )
    neutral = build_hitter_conditional_war_rates(
        players, _hitting_history(), current_season=2026,
        forecast_seasons=(2027,), reference_plate_appearances=1200,
        runs_per_win=10.0,
    )
    supplied = build_hitter_conditional_war_rates(
        players, _hitting_history(), current_season=2026,
        forecast_seasons=(2027,), reference_plate_appearances=1200,
        runs_per_win=10.0,
        baserunning_rates=pl.DataFrame(
            {
                "player_id": [1], "season": [2027],
                "baserunning_runs_per_600": [5.0],
                "baserunning_evidence_tier": ["steal_only"],
                "baserunning_model_id": ["test"],
            }
        ),
    )
    assert math.isclose(
        supplied.item(0, "conditional_war_per_600_pa")
        - neutral.item(0, "conditional_war_per_600_pa"),
        0.5,
    )
    assert supplied.item(0, "missing_component_policy") == "league_average_defense"


def test_pitcher_rates_cover_history_and_prior_players_and_age_components() -> None:
    players = pl.DataFrame({"player_id": [1, 2], "age_years": [25.0, None]})
    result = build_pitcher_conditional_war_rates(
        players, _pitching_history(), current_season=2026,
        forecast_seasons=(2027, 2032), reference_batters_faced=980,
        runs_per_win=10.0,
    )
    assert result.height == 4
    assert set(result.get_column("evidence_tier")) == {"mlb_history", "population_prior"}
    sums = result.select(
        pl.sum_horizontal(
            "predicted_so_rate", "predicted_ubb_rate", "predicted_hbp_rate",
            "predicted_hr_rate", "predicted_other_rate",
        ).alias("sum")
    )
    assert sums.filter((pl.col("sum") - 1.0).abs() > 1e-12).is_empty()
    assert result.get_column("conditional_war_per_800_bf").is_finite().all()
