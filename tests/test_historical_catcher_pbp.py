from __future__ import annotations

import polars as pl

from universal_baseball.historical_catcher_pbp import (
    extract_catcher_blocking_opportunities,
    extract_catcher_throwing_attempts,
    fit_crossed_catcher_pitcher_effects,
    score_binary_context_residuals,
)


def test_extract_throwing_attempts_excludes_pickoffs() -> None:
    terminal = pl.DataFrame(
        {
            "season": [2024, 2024, 2024],
            "level": ["aaa"] * 3,
            "game_pk": [1, 1, 1],
            "at_bat_index": [1, 2, 3],
            "pa_description": [
                "Runner A caught stealing 2nd base, catcher C to shortstop S.",
                "Batter strikes out swinging. Runner B steals (4) 2nd base.",
                "Runner C picked off and caught stealing 2nd base.",
            ],
            "fielder_2": [10, 10, 10],
            "pitcher": [20, 20, 20],
            "p_throws": ["R", "R", "R"],
            "outs_when_up": [0, 1, 2],
            "park_key": ["2024:AAA"] * 3,
        }
    )
    attempts = extract_catcher_throwing_attempts(terminal)
    assert attempts.height == 2
    assert attempts.get_column("caught_stealing").to_list() == [1, 0]


def test_blocking_and_crossed_effects() -> None:
    rows = []
    for season in (2022, 2023):
        for index in range(100):
            catcher = 10 if index % 2 == 0 else 11
            pitcher = 20 if index % 4 < 2 else 21
            failure = catcher == 11 and pitcher == 21 and index % 5 == 0
            rows.append(
                {
                    "season": season,
                    "level": "aaa",
                    "game_pk": season * 1000 + index,
                    "at_bat_index": index,
                    "pitch_number": 1,
                    "fielder_2": catcher,
                    "pitcher": pitcher,
                    "p_throws": "R",
                    "stand": "R",
                    "balls": 1,
                    "strikes": 1,
                    "plate_x": 0.0,
                    "plate_z": 1.0,
                    "sz_top": 3.5,
                    "sz_bot": 1.5,
                    "home_team": "AAA",
                    "start_runner_count": 1,
                    "clean_block_opportunity": True,
                    "block_result": "wild_pitch" if failure else "blocked",
                }
            )
    blocks = extract_catcher_blocking_opportunities(pl.DataFrame(rows))
    scored = score_binary_context_residuals(
        blocks,
        outcome_column="block_failure",
        context_columns=[
            "start_runner_count",
            "balls",
            "strikes",
            "pitcher_hand",
            "batter_side",
        ],
    )
    catchers, pitchers = fit_crossed_catcher_pitcher_effects(
        scored, catcher_prior=20, pitcher_prior=20
    )
    assert catchers.height == 4
    assert pitchers.height == 4
    assert catchers.filter(pl.col("player_id") == 11).get_column("effect").mean() > catchers.filter(
        pl.col("player_id") == 10
    ).get_column("effect").mean()
