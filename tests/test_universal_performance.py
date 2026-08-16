from __future__ import annotations

import polars as pl

from universal_baseball.bin_value_policy import LEAGUE_LEVEL_GROUP
from universal_baseball.mlb_bin_value_policy import MLB_LEAGUE_IDS
from universal_baseball.universal_performance import (
    combine_universal_batting_performance,
)


def _frames(league_ids: list[int]) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    summary_rows = []
    profile_rows = []
    value_rows = []
    for league_id in league_ids:
        summary_rows.append(
            {
                "season": 2024,
                "league_id": league_id,
                "player_id": league_id * 10,
                "batting_plate_appearances": 10,
                "bb_hbp_count": 1,
                "strikeout_count": 2,
                "aggregate_contact_count": 7,
                "contact_event_count": 7,
                "core_contact_count": 7,
                "bunt_contact_count": 0,
                "foul_air_excluded_count": 0,
                "unknown_contact_count": 0,
                "official_overlay_contact_count": 0,
                "core_profile_event_count": 10,
                "core_profile_uncovered_pa_count": 0,
                "core_profile_coverage_rate": 1.0,
                "contact_count_residual_vs_aggregate": 0,
                "valued_core_event_count": 10,
                "unvalued_core_event_count": 0,
                "core_expected_run_value_total": 0.0,
                "core_expected_run_value_per_100_pa": 0.0,
                "has_uncertified_or_missing_bin_value": False,
            }
        )
        for core_bin, count, value in [("BB_HBP", 1, 0.3), ("K", 2, -0.1), ("PULL_GB", 7, -0.01)]:
            profile_rows.append(
                {
                    "season": 2024,
                    "league_id": league_id,
                    "player_id": league_id * 10,
                    "core_bin": core_bin,
                    "occurrence_count": count,
                    "batting_plate_appearances": 10,
                    "share_of_plate_appearances": count / 10,
                    "estimated_mean_run_value": value,
                    "expected_run_value": count * value,
                    "estimator_method": "certified_test",
                    "estimator_certified": True,
                }
            )
            value_rows.append(
                {
                    "season": 2024,
                    "league_id": league_id,
                    "core_bin": core_bin,
                    "estimated_mean_run_value": value,
                    "estimator_method": "certified_test",
                    "estimator_certified": True,
                    "prior_strength": 0,
                    "direct_occurrence_count": 100,
                }
            )
    return pl.DataFrame(summary_rows), pl.DataFrame(profile_rows), pl.DataFrame(value_rows)


def test_universal_combiner_preserves_all_actual_leagues_and_level_context() -> None:
    affiliated = _frames(sorted(LEAGUE_LEVEL_GROUP))
    mlb = _frames(sorted(MLB_LEAGUE_IDS))

    summary, profile, values, metrics = combine_universal_batting_performance(
        *affiliated,
        *mlb,
        expected_season=2024,
    )

    assert summary.get_column("league_id").n_unique() == 16
    assert set(summary.get_column("level_group").unique().to_list()) == {
        "MLB",
        "AAA",
        "AA",
        "HIGH_A",
        "SINGLE_A",
        "ROOKIE_COMPLEX",
    }
    assert summary.filter(pl.col("league_id").is_in(sorted(MLB_LEAGUE_IDS))).get_column(
        "source_level_bucket"
    ).unique().to_list() == ["mlb"]
    assert metrics["actual_league_count"] == 16
    assert metrics["combined_contract"]["total_plate_appearances"] == 160
    assert profile.height == 48
    assert values.height == 48
