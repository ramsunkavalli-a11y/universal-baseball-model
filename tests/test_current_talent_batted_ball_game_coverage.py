import polars as pl
import pytest

from universal_baseball.current_talent_batted_ball_game_coverage import (
    build_certified_game_tracking_coverage,
)


def test_game_coverage_uses_certified_games_as_denominator() -> None:
    certified = pl.DataFrame(
        {
            "game_pk": [1, 1, 2, 2, 3, 3, 4, 4],
            "player_id": [10, 11, 10, 12, 13, 14, 15, 16],
            "season": [2022] * 8,
            "league_id": [117] * 8,
            "level_group": ["AAA"] * 8,
        }
    )
    raw = pl.DataFrame(
        {
            "game_pk": ["1", "1", "1"],
            "launch_speed": ["99.0", None, "88.0"],
        }
    )

    by_environment, metrics = build_certified_game_tracking_coverage(raw, certified)

    assert metrics == {
        "certified_game_count": 4,
        "returned_source_game_count": 1,
        "tracked_game_count": 1,
        "unmatched_source_game_count": 0,
        "tracked_game_share": pytest.approx(0.25),
    }
    row = by_environment.row(0, named=True)
    assert row["certified_game_count"] == 4
    assert row["tracked_game_count"] == 1
    assert row["tracked_game_share"] == pytest.approx(0.25)


def test_game_coverage_keeps_zero_returned_environment_and_reports_unmatched_source_game() -> None:
    certified = pl.DataFrame(
        {
            "game_pk": [1, 2, 3],
            "player_id": [10, 20, 30],
            "season": [2022, 2022, 2022],
            "league_id": [112, 112, 117],
            "level_group": ["AAA", "AAA", "AAA"],
        }
    )
    raw = pl.DataFrame({"game_pk": ["1", "999"]})

    by_environment, metrics = build_certified_game_tracking_coverage(raw, certified)

    rows = {
        row["league_id"]: row for row in by_environment.to_dicts()
    }
    assert rows[112]["certified_game_count"] == 2
    assert rows[112]["tracked_game_count"] == 1
    assert rows[112]["tracked_game_share"] == pytest.approx(0.5)
    assert rows[117]["certified_game_count"] == 1
    assert rows[117]["tracked_game_count"] == 0
    assert rows[117]["tracked_game_share"] == pytest.approx(0.0)
    assert metrics["unmatched_source_game_count"] == 1


def test_game_coverage_fails_on_ambiguous_game_environment() -> None:
    certified = pl.DataFrame(
        {
            "game_pk": [1, 1],
            "player_id": [10, 11],
            "season": [2022, 2022],
            "league_id": [112, 117],
            "level_group": ["AAA", "AAA"],
        }
    )
    raw = pl.DataFrame({"game_pk": ["1"]})

    with pytest.raises(ValueError, match="ambiguous game environment"):
        build_certified_game_tracking_coverage(raw, certified)
