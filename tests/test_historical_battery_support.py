from __future__ import annotations

import polars as pl

from universal_baseball.historical_battery_support import (
    classify_battery_plate_appearances,
    fit_crossed_battery_effects,
)


def _terminal_rows() -> pl.DataFrame:
    descriptions = [
        "Batter One walks.",
        "Batter Two is hit by pitch.",
        "Batter Three strikes out swinging.",
        "Batter Four intentionally walks.",
        "Runner steals 2nd base.",
        "Batter Five homers on a fly ball to left field.",
    ]
    return pl.DataFrame(
        {
            "season": [2024] * 6,
            "level": ["a"] * 6,
            "game_pk": [1] * 6,
            "at_bat_index": list(range(6)),
            "batter": [100, 101, 102, 103, 104, 105],
            "pitcher": [200] * 6,
            "fielder_2": [300] * 6,
            "stand": ["R"] * 6,
            "p_throws": ["R"] * 6,
            "park_key": ["2024:AAA"] * 6,
            "bb_type": [None, None, None, None, None, "fly_ball"],
            "pa_description": descriptions,
            "terminal_outcome_group": [None, None, None, None, None, "HR"],
            "terminal_outcome_status": [
                "unsupported_narrative_result",
                "unsupported_narrative_result",
                "unsupported_narrative_result",
                "unsupported_narrative_result",
                "unsupported_narrative_result",
                "supported_narrative_fallback",
            ],
        }
    )


def test_classify_battery_plate_appearances() -> None:
    result = classify_battery_plate_appearances(_terminal_rows())
    assert result.height == 4
    assert result.get_column("control_failure").to_list() == [1, 1, 0, 0]
    assert result.get_column("strikeout").to_list() == [0, 0, 1, 0]
    assert result.get_column("home_run").to_list() == [0, 0, 0, 1]


def test_crossed_fit_finds_persistent_catcher_direction() -> None:
    rows = []
    for season in (2023, 2024):
        for catcher in (300, 301):
            for pitcher in (200, 201, 202):
                for batter in range(100, 110):
                    for repeat in range(8):
                        failure = catcher == 301 and repeat < 2
                        rows.append(
                            {
                                "season": season,
                                "level": "a",
                                "game_pk": season * 100_000 + len(rows),
                                "at_bat_index": repeat,
                                "catcher_id": catcher,
                                "pitcher_id": pitcher,
                                "batter_id": batter,
                                "pitcher_hand": "R",
                                "batter_side": "R",
                                "park_context": f"{season}:AAA",
                                "control_failure": int(failure),
                            }
                        )
    fit = fit_crossed_battery_effects(
        pl.DataFrame(rows),
        outcome_column="control_failure",
        pitcher_prior=10,
        batter_prior=10,
        catcher_prior=10,
        pair_prior=10,
        context_prior=10,
        park_prior=10,
        iterations=4,
    )
    for season in (2023, 2024):
        effects = dict(
            fit.catchers.filter(pl.col("season") == season)
            .select("player_id", "effect")
            .iter_rows()
        )
        assert effects[301] > effects[300]
    assert fit.pairs.height == 12
