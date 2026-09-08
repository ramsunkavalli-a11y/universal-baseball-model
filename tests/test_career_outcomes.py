from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from universal_baseball.career_outcomes import (
    BATTING_OUTCOME_SCHEMA,
    PITCHING_OUTCOME_SCHEMA,
    build_career_outcome_panel,
    project_mlb_batting_backbone,
    project_mlb_pitching_backbone,
)
from universal_baseball.mlb_season_stats import (
    project_mlb_hitting_splits,
    project_mlb_pitching_splits,
)


def _players(*ids: int) -> pl.DataFrame:
    return pl.DataFrame({"player_id": ids}, schema={"player_id": pl.Int64})


def _batting(rows: list[dict[str, int]] | None = None) -> pl.DataFrame:
    return pl.DataFrame(rows or [], schema=BATTING_OUTCOME_SCHEMA)


def _pitching(rows: list[dict[str, int]] | None = None) -> pl.DataFrame:
    return pl.DataFrame(rows or [], schema=PITCHING_OUTCOME_SCHEMA)


def _bat_row(player_id: int, season: int, pa: int = 100) -> dict[str, int]:
    return {
        "season": season,
        "player_id": player_id,
        "batting_pa": pa,
        "batting_ab": int(pa * 0.85),
        "batting_hits": int(pa * 0.2),
        "batting_doubles": 3,
        "batting_triples": 1,
        "batting_hr": 4,
        "batting_bb": 10,
        "batting_hbp": 1,
        "batting_so": 25,
    }


def _pitch_row(player_id: int, season: int, bf: int = 100) -> dict[str, int]:
    return {
        "season": season,
        "player_id": player_id,
        "pitching_games": 10,
        "pitching_starts": 5,
        "pitching_bf": bf,
        "pitching_so": 25,
        "pitching_ubb": 8,
        "pitching_hbp": 2,
        "pitching_hr": 4,
    }


def test_complete_season_absence_is_zero_but_future_absence_is_censored() -> None:
    result = build_career_outcome_panel(
        _players(1, 2),
        _batting([_bat_row(1, 2019)]),
        _pitching(),
        cohort_as_of_date=date(2018, 12, 31),
        first_followup_season=2019,
        horizon_seasons=3,
        complete_seasons={2019, 2020},
    )
    absent = result.filter((pl.col("player_id") == 2) & (pl.col("season") == 2019)).row(
        0, named=True
    )
    censored = result.filter((pl.col("player_id") == 2) & (pl.col("season") == 2021)).row(
        0, named=True
    )
    assert absent["followup_status"] == "observed_zero"
    assert absent["any_mlb_participation"] is False
    assert absent["batting_pa"] == 0
    assert absent["pitching_bf"] == 0
    assert censored["followup_status"] == "right_censored"
    assert censored["any_mlb_participation"] is None
    assert censored["batting_pa"] is None


def test_hitter_pitcher_and_two_way_participation_share_one_panel() -> None:
    result = build_career_outcome_panel(
        _players(1, 2, 3),
        _batting([_bat_row(1, 2019), _bat_row(3, 2019)]),
        _pitching([_pitch_row(2, 2019), _pitch_row(3, 2019)]),
        cohort_as_of_date=date(2018, 12, 31),
        first_followup_season=2019,
        horizon_seasons=1,
        complete_seasons={2019},
    )
    assert result.get_column("any_mlb_participation").to_list() == [True, True, True]
    two_way = result.filter(pl.col("player_id") == 3).row(0, named=True)
    assert two_way["batting_pa"] == 100
    assert two_way["pitching_bf"] == 100


def test_multiple_source_rows_sum_before_panel_construction() -> None:
    first = _bat_row(1, 2019, pa=100)
    second = _bat_row(1, 2019, pa=50)
    result = build_career_outcome_panel(
        _players(1),
        _batting([first, second]),
        _pitching(),
        cohort_as_of_date=date(2018, 12, 31),
        first_followup_season=2019,
        horizon_seasons=1,
        complete_seasons={2019},
    )
    assert result.item(0, "batting_pa") == 150


def test_rows_for_players_outside_cohort_do_not_change_denominator() -> None:
    result = build_career_outcome_panel(
        _players(1),
        _batting([_bat_row(1, 2019), _bat_row(999, 2019)]),
        _pitching(),
        cohort_as_of_date=date(2018, 12, 31),
        first_followup_season=2019,
        horizon_seasons=1,
        complete_seasons={2019},
    )
    assert result.height == 1
    assert result.item(0, "player_id") == 1


def test_complete_seasons_must_be_contiguous_prefix() -> None:
    with pytest.raises(ValueError, match="contiguous prefix"):
        build_career_outcome_panel(
            _players(1),
            _batting(),
            _pitching(),
            cohort_as_of_date=date(2018, 12, 31),
            first_followup_season=2019,
            horizon_seasons=3,
            complete_seasons={2019, 2021},
        )


def test_incomplete_season_outcomes_cannot_leak_into_panel() -> None:
    with pytest.raises(ValueError, match="right-censored seasons"):
        build_career_outcome_panel(
            _players(1),
            _batting([_bat_row(1, 2020)]),
            _pitching(),
            cohort_as_of_date=date(2018, 12, 31),
            first_followup_season=2019,
            horizon_seasons=2,
            complete_seasons={2019},
        )


def test_invalid_batting_relationships_fail_closed() -> None:
    invalid = {**_bat_row(1, 2019), "batting_hits": 90, "batting_ab": 80}
    with pytest.raises(ValueError, match="count relationships"):
        build_career_outcome_panel(
            _players(1),
            _batting([invalid]),
            _pitching(),
            cohort_as_of_date=date(2018, 12, 31),
            first_followup_season=2019,
            horizon_seasons=1,
            complete_seasons={2019},
        )


def test_invalid_pitching_relationships_fail_closed() -> None:
    invalid = {**_pitch_row(1, 2019), "pitching_starts": 11}
    with pytest.raises(ValueError, match="count relationships"):
        build_career_outcome_panel(
            _players(1),
            _batting(),
            _pitching([invalid]),
            cohort_as_of_date=date(2018, 12, 31),
            first_followup_season=2019,
            horizon_seasons=1,
            complete_seasons={2019},
        )


def test_mlb_backbone_adapters_supply_career_panel_counts() -> None:
    hitting = project_mlb_hitting_splits(
        [
            {
                "player": {"id": 1, "fullName": "Two Way"},
                "stat": {
                    "plateAppearances": 100,
                    "atBats": 85,
                    "hits": 24,
                    "doubles": 5,
                    "triples": 1,
                    "homeRuns": 4,
                    "baseOnBalls": 10,
                    "intentionalWalks": 1,
                    "hitByPitch": 2,
                    "strikeOuts": 20,
                    "sacBunts": 1,
                    "sacFlies": 2,
                    "stolenBases": 2,
                    "caughtStealing": 1,
                    "groundIntoDoublePlay": 3,
                },
            }
        ],
        season=2019,
        league_id=103,
    )
    pitching = project_mlb_pitching_splits(
        [
            {
                "player": {"id": 1, "fullName": "Two Way"},
                "stat": {
                    "gamesPlayed": 10,
                    "gamesStarted": 5,
                    "battersFaced": 100,
                    "strikeOuts": 25,
                    "baseOnBalls": 10,
                    "intentionalWalks": 2,
                    "hitBatsmen": 2,
                    "homeRuns": 4,
                },
            }
        ],
        season=2019,
        league_id=103,
    )
    result = build_career_outcome_panel(
        _players(1),
        project_mlb_batting_backbone(hitting),
        project_mlb_pitching_backbone(pitching),
        cohort_as_of_date=date(2018, 12, 31),
        first_followup_season=2019,
        horizon_seasons=1,
        complete_seasons={2019},
    ).row(0, named=True)
    assert result["batting_hits"] == 24
    assert result["batting_hr"] == 4
    assert result["pitching_ubb"] == 8
    assert result["any_mlb_participation"] is True
