from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.performance_season import (
    build_batting_performance_season,
    estimate_certified_bin_values,
)


def _direct_values() -> pl.DataFrame:
    rows = []
    for league_id, adjustment in [(112, 0.00), (117, 0.02)]:
        for core_bin, mean, n in [
            ("BB_HBP", 0.30, 200),
            ("K", -0.05, 300),
            ("PULL_GB", 0.10, 120),
            ("CENTER_LD", 0.28, 60),
        ]:
            rows.append(
                {
                    "season": 2024,
                    "league_id": league_id,
                    "core_bin": core_bin,
                    "occurrence_count": n,
                    "mean_run_value": mean + adjustment,
                }
            )
    return pl.DataFrame(rows)


def test_certified_bin_values_use_same_level_peer_prior_for_aaa() -> None:
    result = estimate_certified_bin_values(_direct_values())
    row = result.filter(
        (pl.col("league_id") == 112) & (pl.col("core_bin") == "BB_HBP")
    ).to_dicts()[0]

    expected = (0.30 * 200 + 0.32 * 25) / 225
    assert row["prior_strength"] == 25
    assert row["prior_environment_count"] == 1
    assert row["prior_source_occurrence_count"] == 200
    assert row["prior_mean_run_value"] == pytest.approx(0.32)
    assert row["estimated_mean_run_value"] == pytest.approx(expected)
    assert row["estimator_method"] == "certified_same_level_peer_pooling"
    assert row["estimator_certified"] is True


def test_pooled_policy_without_peer_is_marked_uncertified_not_cross_level_filled() -> None:
    only = _direct_values().filter(pl.col("league_id") == 112)
    row = estimate_certified_bin_values(only).filter(
        pl.col("core_bin") == "BB_HBP"
    ).to_dicts()[0]
    assert row["estimated_mean_run_value"] == pytest.approx(0.30)
    assert row["prior_environment_count"] == 0
    assert row["estimator_method"] == "direct_missing_required_peer_support"
    assert row["estimator_certified"] is False


def _batting() -> pl.DataFrame:
    # Player 10 changed teams inside the same league; the transform should sum
    # the two team rows to one player-league-season record.
    return pl.DataFrame(
        {
            "season": [2024, 2024, 2024],
            "league_id": [112, 112, 112],
            "team_id": [1, 2, 1],
            "player_id": [10, 10, 20],
            "batting_plate_appearances": [60, 40, 50],
            "batting_base_on_balls": [6, 4, 5],
            "batting_hit_by_pitch": [1, 1, 0],
            "batting_strike_outs": [12, 8, 10],
            "batting_balls_in_play": [39, 26, 34],
        }
    )


def _classified_contacts() -> pl.DataFrame:
    rows = []
    # Player 10 has 65 broad contacts: 50 core, 5 bunts, 4 foul-air, 6 unknown.
    statuses = (
        [("PULL_GB", "core_contact", "source_default")] * 35
        + [("CENTER_LD", "core_contact", "source_default")] * 15
        + [(None, "special_bunt", "source_default")] * 5
        + [(None, "foul_air_excluded", "source_default")] * 4
        + [(None, "unknown_missing_direction", "official_exception_overlay")] * 6
    )
    for index, (core_bin, status, authority) in enumerate(statuses):
        rows.append(
            {
                "season": 2024,
                "league_id": 112,
                "game_pk": 1000 + index // 10,
                "at_bat_index": index,
                "pitch_number": 1,
                "batter_mlbam_id": 10,
                "participant_authority": authority,
                "result_description_authority": "source_certified_mirror",
                "trajectory_family": "GB" if core_bin == "PULL_GB" else "LD",
                "spray_angle": 0.0,
                "direction": "pull" if core_bin == "PULL_GB" else "center",
                "foul_air_status": "not_foul_air_trajectory",
                "is_foul_air_out": status == "foul_air_excluded",
                "core_bin": core_bin,
                "core_profile_eligible": core_bin is not None,
                "contact_profile_status": status,
            }
        )

    # Player 20 has all 34 contacts core.
    for index in range(34):
        rows.append(
            {
                "season": 2024,
                "league_id": 112,
                "game_pk": 2000 + index // 10,
                "at_bat_index": index,
                "pitch_number": 1,
                "batter_mlbam_id": 20,
                "participant_authority": "source_default",
                "result_description_authority": "source_certified_mirror",
                "trajectory_family": "GB",
                "spray_angle": 0.0,
                "direction": "pull",
                "foul_air_status": "not_foul_air_trajectory",
                "is_foul_air_out": False,
                "core_bin": "PULL_GB",
                "core_profile_eligible": True,
                "contact_profile_status": "core_contact",
            }
        )
    return pl.DataFrame(rows, schema_overrides={"core_bin": pl.String})


def test_batting_performance_season_combines_aggregate_outcomes_and_contact_profile() -> None:
    values = estimate_certified_bin_values(_direct_values())
    summary, profile = build_batting_performance_season(
        _batting(), _classified_contacts(), values
    )
    assert summary.height == 2

    player = summary.filter(pl.col("player_id") == 10).to_dicts()[0]
    assert player["batting_plate_appearances"] == 100
    assert player["bb_hbp_count"] == 12
    assert player["strikeout_count"] == 20
    assert player["aggregate_contact_count"] == 65
    assert player["contact_event_count"] == 65
    assert player["contact_count_residual_vs_aggregate"] == 0
    assert player["core_contact_count"] == 50
    assert player["bunt_contact_count"] == 5
    assert player["foul_air_excluded_count"] == 4
    assert player["unknown_contact_count"] == 6
    assert player["official_overlay_contact_count"] == 6
    assert player["core_profile_event_count"] == 82
    assert player["core_profile_uncovered_pa_count"] == 18
    assert player["core_profile_coverage_rate"] == pytest.approx(0.82)
    assert player["valued_core_event_count"] == 82
    assert player["unvalued_core_event_count"] == 0
    assert player["has_uncertified_or_missing_bin_value"] is False

    bins = {
        row["core_bin"]: row
        for row in profile.filter(pl.col("player_id") == 10).to_dicts()
    }
    assert bins["BB_HBP"]["occurrence_count"] == 12
    assert bins["K"]["occurrence_count"] == 20
    assert bins["PULL_GB"]["occurrence_count"] == 35
    assert bins["CENTER_LD"]["occurrence_count"] == 15
    assert all(row["estimator_certified"] for row in bins.values())


def test_contact_orphan_is_a_hard_quality_error() -> None:
    contacts = _classified_contacts().with_columns(
        pl.when(pl.col("batter_mlbam_id") == 20)
        .then(pl.lit(999))
        .otherwise(pl.col("batter_mlbam_id"))
        .alias("batter_mlbam_id")
    )
    with pytest.raises(ValueError, match="absent from aggregate backbone"):
        build_batting_performance_season(
            _batting(), contacts, estimate_certified_bin_values(_direct_values())
        )
