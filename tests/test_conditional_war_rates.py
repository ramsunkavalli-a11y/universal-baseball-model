from __future__ import annotations

import math

import polars as pl

from universal_baseball.conditional_war_rates import (
    apply_pitcher_next_year_profiles_to_rate_table,
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
    assert result.get_column("posterior_concentration").min() > 0.0
    assert result.get_column("event_run_variance").min() >= 0.0


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


def test_hitter_rates_add_supplied_defense_runs() -> None:
    players = pl.DataFrame(
        {"player_id": [1], "age_years": [27.0], "position_code": ["6"]}
    )
    baserunning = pl.DataFrame(
        {
            "player_id": [1], "season": [2027],
            "baserunning_runs_per_600": [0.0],
            "baserunning_evidence_tier": ["test"],
            "baserunning_model_id": ["test"],
        }
    )
    result = build_hitter_conditional_war_rates(
        players, _hitting_history(), current_season=2026,
        forecast_seasons=(2027,), reference_plate_appearances=1200,
        runs_per_win=10.0, baserunning_rates=baserunning,
        defense_rates=pl.DataFrame(
            {
                "player_id": [1], "season": [2027],
                "defense_runs_per_600": [6.0],
                "defense_evidence_tier": ["frozen_u1_adjacent_year"],
                "defense_model_id": ["test_defense"],
            }
        ),
    )
    assert result.item(0, "defense_runs_per_600") == 6.0
    assert result.item(0, "defense_evidence_tier") == (
        "frozen_u1_adjacent_year"
    )
    assert result.item(0, "missing_component_policy") == "none"


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
    assert result.get_column("posterior_concentration").min() > 0.0
    assert result.get_column("posterior_run_rate_variance").min() >= 0.0


def test_pitcher_next_year_profile_applies_only_to_affiliated_evidence() -> None:
    players = pl.DataFrame({"player_id": [1, 2], "age_years": [25.0, 21.0]})
    affiliated = pl.DataFrame({
        "player_id": [2],
        "weighted_affiliated_exposure": [150.0],
        "affiliated_reliability": [0.15],
        "p_so": [0.22],
        "p_ubb": [0.09],
        "p_hbp": [0.01],
        "p_hr": [0.03],
        "p_other": [0.65],
    })
    next_year = pl.DataFrame({
        "player_id": [1, 2],
        "next_p_so": [0.10, 0.30],
        "next_p_ubb": [0.20, 0.07],
        "next_p_hbp": [0.02, 0.01],
        "next_p_hr": [0.06, 0.02],
        "next_p_other": [0.62, 0.60],
    })
    result = build_pitcher_conditional_war_rates(
        players,
        _pitching_history(),
        current_season=2026,
        forecast_seasons=(2027, 2028),
        reference_batters_faced=980,
        runs_per_win=10.0,
        affiliated_profiles=affiliated,
        affiliated_next_year_profiles=next_year,
    )
    affiliated_result = result.filter(pl.col("player_id") == 2).sort("season")
    assert affiliated_result.item(0, "pitch_process_applied") is True
    assert math.isclose(affiliated_result.item(0, "predicted_so_rate"), 0.30)
    assert affiliated_result.item(1, "predicted_so_rate") != 0.30
    mlb_result = result.filter(pl.col("player_id") == 1)
    assert not mlb_result.get_column("pitch_process_applied").any()


def test_pitcher_process_bridge_preserves_uncovered_and_updates_covered() -> None:
    affiliated = pl.DataFrame({
        "player_id": [2],
        "weighted_affiliated_exposure": [150.0],
        "affiliated_reliability": [0.15],
        "p_so": [0.22],
        "p_ubb": [0.09],
        "p_hbp": [0.01],
        "p_hr": [0.03],
        "p_other": [0.65],
    })
    base = build_pitcher_conditional_war_rates(
        pl.DataFrame({"player_id": [1, 2], "age_years": [25.0, None]}),
        _pitching_history(),
        current_season=2026,
        forecast_seasons=(2027, 2028),
        reference_batters_faced=980,
        runs_per_win=10.0,
        affiliated_profiles=affiliated,
    )
    profiles = pl.DataFrame({
        "player_id": [1, 2],
        "next_p_so": [0.40, 0.32],
        "next_p_ubb": [0.05, 0.06],
        "next_p_hbp": [0.01, 0.01],
        "next_p_hr": [0.02, 0.02],
        "next_p_other": [0.52, 0.59],
    })
    adjusted = apply_pitcher_next_year_profiles_to_rate_table(
        base, profiles, current_season=2026, runs_per_win=10.0
    )
    covered = adjusted.filter(pl.col("player_id") == 2)
    assert covered.get_column("pitch_process_applied").all()
    assert math.isclose(covered.item(0, "predicted_so_rate"), 0.32)
    uncovered_before = base.filter(pl.col("player_id") == 1).select(base.columns)
    uncovered_after = adjusted.filter(pl.col("player_id") == 1).select(base.columns)
    assert uncovered_after.equals(uncovered_before)


def test_offseason_rate_cutoff_uses_completed_prior_season() -> None:
    hitter = build_hitter_conditional_war_rates(
        pl.DataFrame(
            {"player_id": [1], "age_years": [28.0], "position_code": ["6"]}
        ),
        _hitting_history(),
        current_season=2026,
        forecast_seasons=(2026,),
        reference_plate_appearances=1100,
        runs_per_win=10.0,
        evidence_anchor_season=2025,
        reference_season=2025,
    )
    pitcher = build_pitcher_conditional_war_rates(
        pl.DataFrame({"player_id": [1], "age_years": [28.0]}),
        _pitching_history(),
        current_season=2026,
        forecast_seasons=(2026,),
        reference_batters_faced=980,
        runs_per_win=10.0,
        evidence_anchor_season=2025,
        reference_season=2025,
    )
    assert hitter.item(0, "weighted_history_pa") == 2300.0
    assert pitcher.item(0, "weighted_history_bf") == 3560.0
    assert hitter.item(0, "target_age") == 28.0
    assert pitcher.item(0, "target_age") == 28.0
