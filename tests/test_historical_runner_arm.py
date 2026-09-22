from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.historical_runner_arm import (
    add_advancement_re24,
    add_advancement_value,
    build_run_expectancy_table,
    evaluate_effect_projection,
    fit_crossed_runner_arm_effects,
    score_contextual_advancement_residuals,
)


def test_re24_advancement_values_only_focal_runner_destination() -> None:
    terminal = pl.DataFrame(
        {
            "season": [2024, 2024, 2024, 2024],
            "level": ["aaa"] * 4,
            "game_pk": [1] * 4,
            "inning": [1] * 4,
            "inning_top_bot": ["Top"] * 4,
            "at_bat_index": [1, 2, 3, 4],
            "outs_when_up": [0, 0, 1, 2],
            "start_runner_1b": [None, 10, None, None],
            "start_runner_2b": [None, None, 10, None],
            "start_runner_3b": [None, None, None, None],
            "bat_score": [0, 0, 0, 1],
            "post_bat_score": [0, 0, 1, 1],
        }
    )
    estimated = build_run_expectancy_table(terminal)
    assert estimated.height > 0
    re24 = pl.DataFrame(
        {
            "season": [2024, 2024],
            "level": ["aaa", "aaa"],
            "outs_when_up": [0, 0],
            "base_state": [5, 3],
            "run_expectancy": [1.4, 1.1],
            "state_opportunities": [100, 100],
        }
    )
    opportunity = pl.DataFrame(
        {
            "season": [2024],
            "level": ["aaa"],
            "runner_id": [10],
            "origin_base": [1],
            "opportunity_type": ["first_on_single"],
            "destination_base": [3],
            "outs_when_up": [0],
            "terminal_outcome_group": ["1B"],
            "on_1b": [20],
            "on_2b": [None],
            "on_3b": [10],
        }
    )
    valued = add_advancement_re24(opportunity, re24)
    assert valued["advancement_re24"][0] == pytest.approx(0.3)


def _opportunities() -> pl.DataFrame:
    rows = []
    for season in (2021, 2022, 2023):
        for index in range(120):
            runner = 10 if index % 2 == 0 else 20
            outfielder = 30 if index % 4 < 2 else 40
            destination = 3 if runner == 10 else 2
            if outfielder == 30 and destination == 3:
                destination = 2
            rows.append(
                {
                    "season": season,
                    "level": "aaa",
                    "game_pk": season * 1000 + index // 10,
                    "at_bat_index": index,
                    "runner_id": runner,
                    "responsible_fielder_id": outfielder,
                    "responsible_position": 7,
                    "opportunity_type": "first_on_single",
                    "origin_base": 1,
                    "destination_base": destination,
                    "outfield_arm_context": True,
                    "outs_when_up": index % 2,
                    "bb_type": "line_drive",
                    "hit_location": 7,
                    "stand": "R",
                    "p_throws": "R",
                    "park_key": f"{season}:AAA",
                }
            )
    return pl.DataFrame(rows)


def test_advancement_value_and_context_scoring() -> None:
    values = add_advancement_value(
        pl.DataFrame(
            {
                "opportunity_type": ["first_on_single"] * 4,
                "origin_base": [1] * 4,
                "destination_base": [0, 2, 3, 4],
            }
        )
    )
    assert values.get_column("advancement_value").to_list() == [-1.0, 0.0, 1.0, 2.0]

    scored = score_contextual_advancement_residuals(_opportunities())
    assert scored.height == 360
    assert scored.get_column("advancement_residual").is_not_null().all()


def test_crossed_effects_separate_fast_runner_and_strong_arm() -> None:
    scored = score_contextual_advancement_residuals(_opportunities())
    runners, arms = fit_crossed_runner_arm_effects(scored)
    assert runners.filter(pl.col("player_id") == 10).get_column("effect").mean() > runners.filter(
        pl.col("player_id") == 20
    ).get_column("effect").mean()
    assert arms.filter(pl.col("player_id") == 30).get_column("effect").mean() > arms.filter(
        pl.col("player_id") == 40
    ).get_column("effect").mean()

    paired, metrics = evaluate_effect_projection(
        runners,
        target_season=2023,
        regression_opportunities=20,
        minimum_target_opportunities=10,
    )
    assert paired.height == 2
    assert metrics["candidate_rmse"] < metrics["neutral_rmse"]
