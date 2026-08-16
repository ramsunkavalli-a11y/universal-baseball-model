from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_reconciliation import (
    reconcile_player_game_to_performance,
)


def _game_evidence() -> tuple[pl.DataFrame, pl.DataFrame]:
    summary = pl.DataFrame(
        [
            {
                "season": 2024,
                "game_date": date(2024, 4, 1),
                "game_pk": 1,
                "league_id": 117,
                "player_id": 10,
                "level_group": "AAA",
                "batting_plate_appearances": 4,
                "core_profile_event_count": 3,
                "non_core_event_count": 0,
                "unknown_event_count": 1,
                "participant_authority_status": "source_default",
                "source_capability_tier": "test",
            },
            {
                "season": 2024,
                "game_date": date(2024, 4, 2),
                "game_pk": 2,
                "league_id": 117,
                "player_id": 10,
                "level_group": "AAA",
                "batting_plate_appearances": 5,
                "core_profile_event_count": 4,
                "non_core_event_count": 1,
                "unknown_event_count": 0,
                "participant_authority_status": "source_default",
                "source_capability_tier": "test",
            },
        ]
    )
    profile = pl.DataFrame(
        [
            {
                "season": 2024,
                "game_date": date(2024, 4, 1),
                "game_pk": 1,
                "league_id": 117,
                "player_id": 10,
                "level_group": "AAA",
                "core_bin": "BB_HBP",
                "occurrence_count": 1,
            },
            {
                "season": 2024,
                "game_date": date(2024, 4, 1),
                "game_pk": 1,
                "league_id": 117,
                "player_id": 10,
                "level_group": "AAA",
                "core_bin": "K",
                "occurrence_count": 1,
            },
            {
                "season": 2024,
                "game_date": date(2024, 4, 1),
                "game_pk": 1,
                "league_id": 117,
                "player_id": 10,
                "level_group": "AAA",
                "core_bin": "PULL_GB",
                "occurrence_count": 1,
            },
            {
                "season": 2024,
                "game_date": date(2024, 4, 2),
                "game_pk": 2,
                "league_id": 117,
                "player_id": 10,
                "level_group": "AAA",
                "core_bin": "K",
                "occurrence_count": 2,
            },
            {
                "season": 2024,
                "game_date": date(2024, 4, 2),
                "game_pk": 2,
                "league_id": 117,
                "player_id": 10,
                "level_group": "AAA",
                "core_bin": "CENTER_LD",
                "occurrence_count": 2,
            },
        ]
    )
    return summary, profile


def _performance() -> tuple[pl.DataFrame, pl.DataFrame]:
    summary = pl.DataFrame(
        [
            {
                "season": 2024,
                "league_id": 117,
                "player_id": 10,
                "batting_plate_appearances": 9,
                "core_profile_event_count": 7,
            }
        ]
    )
    profile = pl.DataFrame(
        [
            {"season": 2024, "league_id": 117, "player_id": 10, "core_bin": "BB_HBP", "occurrence_count": 1},
            {"season": 2024, "league_id": 117, "player_id": 10, "core_bin": "K", "occurrence_count": 3},
            {"season": 2024, "league_id": 117, "player_id": 10, "core_bin": "PULL_GB", "occurrence_count": 1},
            {"season": 2024, "league_id": 117, "player_id": 10, "core_bin": "CENTER_LD", "occurrence_count": 2},
        ]
    )
    return summary, profile


def test_exact_game_rollup_reconciles_to_performance() -> None:
    game_summary, game_profile = _game_evidence()
    perf_summary, perf_profile = _performance()
    _, _, metrics = reconcile_player_game_to_performance(
        game_summary, game_profile, perf_summary, perf_profile
    )
    assert metrics["exact_reconciliation"] is True
    assert metrics["game_plate_appearances"] == 9
    assert metrics["game_core_events"] == 7


def test_bin_mismatch_is_hard_failure() -> None:
    game_summary, game_profile = _game_evidence()
    perf_summary, perf_profile = _performance()
    perf_profile = perf_profile.with_columns(
        pl.when(pl.col("core_bin") == "K")
        .then(pl.col("occurrence_count") + 1)
        .otherwise(pl.col("occurrence_count"))
        .alias("occurrence_count")
    )
    with pytest.raises(ValueError, match="does not exactly reconcile"):
        reconcile_player_game_to_performance(
            game_summary, game_profile, perf_summary, perf_profile
        )
