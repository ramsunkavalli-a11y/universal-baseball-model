from __future__ import annotations

from datetime import date

import polars as pl

from universal_baseball.current_talent_validation import (
    PRIMARY_FUTURE_HORIZON,
    add_cutoff_membership,
    cap_future_pa_for_aggregate_metrics,
    future_window,
    in_season_snapshot_dates,
)


def test_month_start_snapshots_and_primary_window() -> None:
    assert in_season_snapshot_dates(2024) == (
        date(2024, 5, 1),
        date(2024, 6, 1),
        date(2024, 7, 1),
        date(2024, 8, 1),
        date(2024, 9, 1),
    )
    assert future_window(date(2024, 5, 1), PRIMARY_FUTURE_HORIZON) == (
        date(2024, 5, 1),
        date(2024, 7, 30),
    )


def test_cutoff_membership_has_no_same_day_leakage() -> None:
    frame = pl.DataFrame(
        {
            "game_date": ["2024-04-30", "2024-05-01", "2024-07-29", "2024-07-30"],
            "row": [1, 2, 3, 4],
        }
    )
    result = add_cutoff_membership(frame, cutoff=date(2024, 5, 1))
    rows = {row["row"]: row for row in result.to_dicts()}
    assert rows[1]["is_predictor_evidence"] is True
    assert rows[1]["is_future_target_evidence"] is False
    assert rows[2]["is_predictor_evidence"] is False
    assert rows[2]["is_future_target_evidence"] is True
    assert rows[3]["is_future_target_evidence"] is True
    assert rows[4]["is_future_target_evidence"] is False
    assert rows[4]["is_outside_validation_window"] is True


def test_future_pa_cap_is_chronological_and_per_player() -> None:
    rows = []
    for player_id in (1, 2):
        for index in range(4):
            rows.append(
                {
                    "player_id": player_id,
                    "game_date": f"2024-05-{4-index:02d}",
                    "game_pk": 100 + (4 - index),
                    "at_bat_index": index,
                    "token": f"{player_id}-{index}",
                }
            )
    capped = cap_future_pa_for_aggregate_metrics(pl.DataFrame(rows), cap=2)
    assert capped.group_by("player_id").len().sort("player_id").get_column("len").to_list() == [2, 2]
    # Earliest game dates survive regardless of input order.
    assert set(capped.get_column("game_date").to_list()) == {"2024-05-01", "2024-05-02"}
