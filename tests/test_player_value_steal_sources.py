from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.player_value_steal_sources import (
    _project_milb_frame,
    _project_milb_frame_with_report,
    project_mlb_steal_splits,
)


def test_project_mlb_steal_split_maps_required_counts() -> None:
    rows = project_mlb_steal_splits(
        [
            {
                "player": {"id": 123, "fullName": "Runner Example"},
                "stat": {
                    "plateAppearances": 200,
                    "hits": 50,
                    "doubles": 10,
                    "triples": 2,
                    "homeRuns": 8,
                    "baseOnBalls": 20,
                    "intentionalWalks": 2,
                    "hitByPitch": 3,
                    "stolenBases": 12,
                    "caughtStealing": 3,
                },
            }
        ],
        season=2024,
    )

    row = rows[0]
    assert row.player_id == 123
    assert row.tier == "MLB"
    assert row.singles == 30
    assert row.opportunity_proxy == 51
    assert row.attempts == 15


def test_project_mlb_steal_split_fails_on_missing_required_count() -> None:
    with pytest.raises(ValueError, match="missing fields"):
        project_mlb_steal_splits(
            [
                {
                    "player": {"id": 123},
                    "stat": {
                        "plateAppearances": 10,
                        "hits": 2,
                        "doubles": 0,
                        "triples": 0,
                        "homeRuns": 0,
                        "baseOnBalls": 1,
                        "intentionalWalks": 0,
                        "hitByPitch": 0,
                        "stolenBases": 1,
                    },
                }
            ],
            season=2024,
        )


def _milb_frame(*, caught_stealing=4) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2023],
            "team_id": [1],
            "team_league_id": [112],
            "player_id": [456],
            "player_full_name": ["Minor Runner"],
            "batting_PA": [180],
            "batting_H": [45],
            "batting_2B": [9],
            "batting_3B": [2],
            "batting_HR": [6],
            "batting_BB": [18],
            "batting_IBB": [1],
            "batting_HBP": [2],
            "batting_SB": [15],
            "batting_CS": [caught_stealing],
        }
    )


def test_project_milb_frame_uses_standardized_release_fields() -> None:
    rows = _project_milb_frame(_milb_frame(), season=2023, tier="AAA")

    row = rows[0]
    assert row.environment_id == "MILB:112"
    assert row.tier == "AAA"
    assert row.player_id == 456
    assert row.singles == 28
    assert row.opportunity_proxy == 47
    assert row.attempts == 19


def test_project_milb_frame_reports_and_excludes_incomplete_required_row() -> None:
    rows, report = _project_milb_frame_with_report(
        _milb_frame(caught_stealing=None), season=2023, tier="AAA"
    )

    assert rows == []
    assert report == {
        "source_row_count": 1,
        "projected_row_count": 0,
        "dropped_incomplete_required_stat_rows": 1,
        "dropped_invalid_identity_or_season_rows": 0,
    }


def test_project_milb_frame_fails_closed_when_sb_cs_columns_missing() -> None:
    frame = _milb_frame().drop(["batting_SB", "batting_CS"])

    with pytest.raises(ValueError, match="missing required standardized columns"):
        _project_milb_frame(frame, season=2023, tier="AAA")
