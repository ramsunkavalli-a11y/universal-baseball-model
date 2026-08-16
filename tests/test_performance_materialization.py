from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.performance_materialization import (
    combine_batting_performance_frames,
)


LEAGUES = [112, 117, 109, 111, 113, 116, 118, 126, 110, 122, 123, 121, 124, 130]


def _summary(league_id: int, player_id: int) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2024],
            "league_id": [league_id],
            "player_id": [player_id],
            "batting_plate_appearances": [100],
            "contact_event_count": [60],
            "contact_count_residual_vs_aggregate": [0],
            "core_profile_event_count": [97],
            "unknown_contact_count": [1],
            "official_overlay_contact_count": [2],
            "has_uncertified_or_missing_bin_value": [False],
            "unvalued_core_event_count": [0],
        }
    )


def _profile(league_id: int, player_id: int) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2024],
            "league_id": [league_id],
            "player_id": [player_id],
            "core_bin": ["K"],
            "occurrence_count": [20],
        }
    )


def _values(league_id: int) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2024],
            "league_id": [league_id],
            "core_bin": ["K"],
            "estimated_mean_run_value": [-0.05],
        }
    )


def test_combiner_preserves_actual_league_grain_and_adds_level_context() -> None:
    summaries = [_summary(league_id, 1000 + i) for i, league_id in enumerate(LEAGUES)]
    profiles = [_profile(league_id, 1000 + i) for i, league_id in enumerate(LEAGUES)]
    values = [_values(league_id) for league_id in LEAGUES]

    summary, profile, bin_values, metrics = combine_batting_performance_frames(
        summaries,
        profiles,
        values,
        expected_season=2024,
    )

    assert summary.height == len(LEAGUES)
    assert summary.get_column("league_id").n_unique() == len(LEAGUES)
    assert summary.get_column("level_group").n_unique() == 5
    assert set(summary.get_column("filename_level")) == {"aaa", "aa", "a+", "a", "rk"}
    assert profile.height == len(LEAGUES)
    assert bin_values.height == len(LEAGUES)
    assert metrics["total_plate_appearances"] == 100 * len(LEAGUES)
    assert metrics["core_profile_coverage_rate"] == pytest.approx(0.97)
    assert metrics["unvalued_core_event_count"] == 0
    assert metrics["uncertified_or_missing_bin_value_player_rows"] == 0


def test_same_player_at_two_levels_remains_two_performance_rows() -> None:
    summary, _, _, _ = combine_batting_performance_frames(
        [_summary(112, 10), _summary(109, 10)],
        [_profile(112, 10), _profile(109, 10)],
        [_values(112), _values(109)],
        expected_season=2024,
        require_all_certified_leagues=False,
    )
    assert summary.height == 2
    assert summary.get_column("player_id").to_list() == [10, 10]
    assert set(summary.get_column("level_group")) == {"AAA", "AA"}


def test_duplicate_player_league_season_is_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate canonical keys"):
        combine_batting_performance_frames(
            [_summary(112, 10), _summary(112, 10)],
            [_profile(112, 10)],
            [_values(112)],
            expected_season=2024,
            require_all_certified_leagues=False,
        )


def test_profile_orphan_player_is_rejected() -> None:
    with pytest.raises(ValueError, match="absent from summary"):
        combine_batting_performance_frames(
            [_summary(112, 10)],
            [_profile(112, 99)],
            [_values(112)],
            expected_season=2024,
            require_all_certified_leagues=False,
        )


def test_profile_bin_without_value_is_rejected() -> None:
    profile = _profile(112, 10).with_columns(pl.lit("PULL_GB").alias("core_bin"))
    with pytest.raises(ValueError, match="absent from league bin-value table"):
        combine_batting_performance_frames(
            [_summary(112, 10)],
            [profile],
            [_values(112)],
            expected_season=2024,
            require_all_certified_leagues=False,
        )


def test_full_affiliated_coverage_is_required_by_default() -> None:
    with pytest.raises(ValueError, match="affiliated league coverage mismatch"):
        combine_batting_performance_frames(
            [_summary(112, 10)],
            [_profile(112, 10)],
            [_values(112)],
            expected_season=2024,
        )
