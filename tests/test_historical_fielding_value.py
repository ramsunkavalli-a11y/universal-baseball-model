from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.historical_fielding_value import (
    add_contextual_fielding_runs,
    add_terminal_re24_change,
)


def test_terminal_re24_change_uses_next_base_out_state() -> None:
    terminal = pl.DataFrame(
        {
            "season": [2024, 2024],
            "level": ["aaa", "aaa"],
            "game_pk": [1, 1],
            "inning": [1, 1],
            "inning_top_bot": ["Top", "Top"],
            "at_bat_index": [0, 1],
            "outs_when_up": [0, 0],
            "start_runner_1b": [None, 10],
            "start_runner_2b": [None, None],
            "start_runner_3b": [None, None],
            "bat_score": [0, 0],
            "post_bat_score": [0, 0],
        }
    )
    re24 = pl.DataFrame(
        {
            "season": [2024, 2024],
            "level": ["aaa", "aaa"],
            "outs_when_up": [0, 0],
            "base_state": [0, 1],
            "run_expectancy": [0.5, 0.9],
        }
    )
    valued = add_terminal_re24_change(terminal, re24)
    assert valued["batting_re24_change"][0] == pytest.approx(0.4)


def test_contextual_fielding_runs_credits_an_out() -> None:
    scored = pl.DataFrame(
        {
            "season": [2024, 2024],
            "level": ["aaa", "aaa"],
            "game_pk": [1, 1],
            "at_bat_index": [0, 1],
            "responsible_position": [6, 6],
            "responsible_fielder_id": [10, 11],
            "actual_out": [1.0, 0.0],
            "fielding_out_residual": [0.4, -0.6],
            "outs_when_up": [0, 0],
            "start_runner_1b": [None, None],
            "start_runner_2b": [None, None],
            "start_runner_3b": [None, None],
        }
    )
    terminal = pl.DataFrame(
        {
            "season": [2024, 2024],
            "level": ["aaa", "aaa"],
            "game_pk": [1, 1],
            "at_bat_index": [0, 1],
            "batting_re24_change": [-0.3, 0.7],
        }
    )
    valued = add_contextual_fielding_runs(scored, terminal)
    assert valued["out_run_swing"].to_list() == pytest.approx([1.0, 1.0])
    assert valued["fielding_runs_above_expected"].to_list() == pytest.approx(
        [0.4, -0.6]
    )
