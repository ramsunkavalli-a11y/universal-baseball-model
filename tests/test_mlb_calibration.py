from __future__ import annotations

import polars as pl

from universal_baseball.mlb_calibration import (
    intraleague_schedule_candidates,
    performance_core_from_official,
    spread_sample,
)


def test_spread_sample_is_deterministic_and_uses_endpoints() -> None:
    rows = [
        {"game_pk": game_pk, "game_date": f"2024-04-{day:02d}"}
        for game_pk, day in [(5, 5), (1, 1), (3, 3), (2, 2), (4, 4)]
    ]
    sample = spread_sample(rows, 3)
    assert [row["game_pk"] for row in sample] == [1, 3, 5]


def test_intraleague_schedule_candidates_excludes_interleague() -> None:
    payload = {
        "dates": [
            {
                "date": "2024-04-01",
                "games": [
                    {
                        "gamePk": 1,
                        "gameType": "R",
                        "status": {"abstractGameState": "Final"},
                        "teams": {
                            "home": {"team": {"id": 10}},
                            "away": {"team": {"id": 11}},
                        },
                    },
                    {
                        "gamePk": 2,
                        "gameType": "R",
                        "status": {"abstractGameState": "Final"},
                        "teams": {
                            "home": {"team": {"id": 10}},
                            "away": {"team": {"id": 20}},
                        },
                    },
                    {
                        "gamePk": 3,
                        "gameType": "R",
                        "status": {"abstractGameState": "Final"},
                        "teams": {
                            "home": {"team": {"id": 20}},
                            "away": {"team": {"id": 21}},
                        },
                    },
                ],
            }
        ]
    }
    candidates = intraleague_schedule_candidates(
        payload,
        {10: 103, 11: 103, 20: 104, 21: 104},
    )
    assert [row["game_pk"] for row in candidates[103]] == [1]
    assert [row["game_pk"] for row in candidates[104]] == [3]


def test_official_core_mapping_uses_outcomes_and_screened_contact_bins() -> None:
    pa = pl.DataFrame(
        {
            "game_pk": [100, 100, 100],
            "at_bat_number": [0, 1, 2],
            "batter_id": [1, 2, 3],
            "batter_side": ["R", "L", "R"],
            "event_type": ["walk", "strikeout", "single"],
            "description": ["walks", "strikes out", "singles on a line drive"],
        }
    )
    pitch = pl.DataFrame(
        {
            "game_pk": [100],
            "at_bat_number": [2],
            "pitch_number": [4],
            "is_in_play": [True],
            "hit_trajectory": ["line_drive"],
            "hit_coord_x": [125.42],
            "hit_coord_y": [100.0],
        }
    )

    result = performance_core_from_official(pa, pitch, season=2024, league_id=103)
    bins = {row["at_bat_index"]: row["core_bin"] for row in result.to_dicts()}
    assert bins[0] == "BB_HBP"
    assert bins[1] == "K"
    assert bins[2] in {"PULL_LD", "CENTER_LD", "OPPO_LD"}
    assert result.get_column("season").unique().to_list() == [2024]
    assert result.get_column("league_id").unique().to_list() == [103]
