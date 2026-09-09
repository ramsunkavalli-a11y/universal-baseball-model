import polars as pl

from universal_baseball.prospect_arrival import (
    arrival_design,
    build_arrival_cohort,
    six_year_probability,
)


def test_arrival_cohort_excludes_prior_mlb_and_keeps_future_debut() -> None:
    snapshots = pl.DataFrame(
        {
            "snapshot_year": [2021, 2021, 2021], "player_id": [1, 2, 3],
            "age_years": [21.0, 22.0, 31.0],
            "as_of_level_group": ["AA", "AAA", "A"],
        }
    )
    stats = pl.DataFrame(
        {
            "season": [2021, 2020, 2021, 2022],
            "stat_group": ["hitting"] * 4, "player_id": [1, 2, 2, 1],
            "sport_id": [12, 1, 11, 1], "plate_appearances": [400, 10, 300, 5],
            "batters_faced": [0] * 4,
            "position_code": ["SS", "SS", "C", "SS"],
        }
    )
    membership = pl.DataFrame(
        {"season": [2021, 2021], "player_id": [1, 2], "on_40man": [False, True]}
    )
    skill = pl.DataFrame(
        {
            "season": [2021, 2021], "player_id": [1, 2], "sport_id": [12, 11],
            "plate_appearances": [400, 300], "base_on_balls": [40, 30],
            "intentional_walks": [0, 0], "strike_outs": [80, 60],
            "home_runs": [10, 8], "doubles": [20, 15], "triples": [2, 1],
        }
    )
    result = build_arrival_cohort(
        snapshots, stats, membership, skill, snapshot_year=2021, horizon=2,
        player_type="hitter",
    )
    assert result.get_column("player_id").to_list() == [1]
    assert result.item(0, "arrived_within_horizon") == 1
    assert result.item(0, "meaningful_role_within_horizon") == 0
    assert result.item(0, "role_tier") == "MIDDLE_INFIELD"
    assert arrival_design(result, feature_set="stable_demographics").shape[1] > (
        arrival_design(result, feature_set="core").shape[1]
    )
    assert arrival_design(result, feature_set="all_demographics").shape[1] > (
        arrival_design(result, feature_set="stable_demographics").shape[1]
    )


def test_two_year_probability_converts_to_six_year_windows() -> None:
    assert abs(six_year_probability(0.2) - 0.488) < 1e-12
