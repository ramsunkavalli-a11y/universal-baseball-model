from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from universal_baseball.control_baseline import (
    advance_control_baselines,
    build_control_baselines,
    service_time_to_days,
)
from universal_baseball.team_control import CONTROL_STINT_SCHEMA, SEASON_WINDOW_SCHEMA


def test_service_time_parser_uses_172_day_years() -> None:
    assert service_time_to_days("2.069") == 413
    assert service_time_to_days("") is None
    with pytest.raises(ValueError, match="remainder"):
        service_time_to_days("2.172")


def test_baseline_requires_stable_identity_before_acceptance() -> None:
    references = pl.DataFrame(
        {
            "fangraphs_id": ["10", "20"],
            "player_name": ["Stable", "Name Only"],
            "reference_service_time": ["2.069", "0.010"],
            "reference_options_remaining": [1, 3],
            "reference_rule5_status": ["", ""],
            "reference_rule5_year": [None, None],
            "source_snapshot_id": ["fg:test", "fg:test"],
        }
    )
    matches = pl.DataFrame(
        {
            "fangraphs_id": ["10", "20"],
            "player_id": [101, 202],
            "match_status": ["matched_stable_id", "matched_validation_only"],
        }
    )
    result = build_control_baselines(
        references, matches, baseline_as_of_date=date(2026, 9, 8)
    )
    by_id = {row["fangraphs_id"]: row for row in result.iter_rows(named=True)}
    assert by_id["10"]["service_days"] == 413
    assert by_id["10"]["baseline_status"] == "accepted_stable_identity"
    assert by_id["20"]["baseline_status"] == "review_name_only_identity"


def test_forward_roll_adds_service_but_only_later_season_option_years() -> None:
    references = pl.DataFrame(
        {
            "fangraphs_id": ["10"],
            "player_name": ["Stable"],
            "reference_service_time": ["2.069"],
            "reference_options_remaining": [2],
            "reference_rule5_status": [""],
            "reference_rule5_year": [None],
            "source_snapshot_id": ["fg:test"],
        }
    )
    matches = pl.DataFrame(
        {
            "fangraphs_id": ["10"],
            "player_id": [101],
            "match_status": ["matched_stable_id"],
        }
    )
    baselines = build_control_baselines(
        references, matches, baseline_as_of_date=date(2026, 6, 30)
    )
    stints = pl.DataFrame(
        [
            {
                "player_id": 101,
                "season": 2026,
                "start_date": date(2026, 6, 1),
                "end_date": date(2026, 7, 30),
                "roster_state": "mlb_active",
                "source_snapshot_id": "statsapi:2026",
            },
            {
                "player_id": 101,
                "season": 2026,
                "start_date": date(2026, 7, 1),
                "end_date": date(2026, 7, 30),
                "roster_state": "minors_optioned",
                "source_snapshot_id": "statsapi:2026",
            },
            {
                "player_id": 101,
                "season": 2027,
                "start_date": date(2027, 4, 1),
                "end_date": date(2027, 4, 20),
                "roster_state": "minors_optioned",
                "source_snapshot_id": "statsapi:2027",
            },
        ],
        schema=CONTROL_STINT_SCHEMA,
    )
    windows = pl.DataFrame(
        [
            {"season": 2026, "start_date": date(2026, 3, 25), "end_date": date(2026, 9, 27)},
            {"season": 2027, "start_date": date(2027, 3, 25), "end_date": date(2027, 9, 27)},
        ],
        schema=SEASON_WINDOW_SCHEMA,
    )
    result = advance_control_baselines(
        baselines, stints, windows, as_of_date=date(2027, 4, 20)
    ).row(0, named=True)
    assert result["added_service_days"] == 30
    assert result["service_time"] == "2.099"
    assert result["new_option_years"] == 1
    assert result["options_remaining"] == 1
