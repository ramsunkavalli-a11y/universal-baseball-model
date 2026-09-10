import polars as pl
import pytest

from universal_baseball.prospect_arrival import (
    arrival_design,
    build_arrival_cohort,
    fit_arrival_model,
    six_year_probability,
    _positive_component_roles,
    _primary_hitter_positions,
    _role_tier,
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
            "hits": [100, 75], "hit_by_pitch": [2, 1],
        }
    )
    result = build_arrival_cohort(
        snapshots, stats, membership, skill, snapshot_year=2021, horizon=2,
        player_type="hitter",
    )
    assert result.get_column("player_id").to_list() == [1]
    assert result.item(0, "arrived_within_horizon") == 1
    assert result.item(0, "meaningful_role_within_horizon") == 0
    assert result.item(0, "established_role_within_horizon") == 0
    assert result.item(0, "role_tier") == "MIDDLE_INFIELD"
    assert arrival_design(result, feature_set="stable_demographics").shape[1] > (
        arrival_design(result, feature_set="core").shape[1]
    )
    assert arrival_design(result, feature_set="all_demographics").shape[1] > (
        arrival_design(result, feature_set="stable_demographics").shape[1]
    )


def test_two_year_probability_converts_to_six_year_windows() -> None:
    assert abs(six_year_probability(0.2) - 0.488) < 1e-12


@pytest.mark.parametrize(
    ("code", "expected"),
    [("2", "C"), ("4", "MIDDLE_INFIELD"), ("6", "MIDDLE_INFIELD"),
     ("7", "OUTFIELD"), ("8", "OUTFIELD"), ("9", "OUTFIELD"),
     ("3", "CORNER"), ("5", "CORNER"), ("10", "OTHER")],
)
def test_statsapi_numeric_hitter_position_codes_map_to_model_roles(
    code: str, expected: str
) -> None:
    assert _role_tier(code, player_type="hitter") == expected


def test_primary_hitter_position_is_games_weighted_and_deterministic() -> None:
    stats = pl.DataFrame(
        {
            "season": [2025, 2025, 2025, 2025],
            "stat_group": ["hitting"] * 4,
            "sport_id": [11] * 4,
            "player_id": [1, 1, 2, 2],
            "position_code": ["2", "6", "6", "4"],
            "games": [8, 20, 12, 12],
        }
    )

    result = _primary_hitter_positions(stats, snapshot_year=2025)

    assert result.to_dicts() == [
        {"player_id": 1, "position": "6"},
        {"player_id": 2, "position": "4"},
    ]


def test_origin_design_normalizes_statsapi_country_aliases() -> None:
    base = {
        "age_years": [21.0],
        "level_tier": ["AA"],
        "current_milb_workload": [300.0],
        "prior_affiliated_workload": [600.0],
        "prior_affiliated_seasons": [2.0],
        "on_40man": [False],
        "role_tier": ["STARTER"],
        "production_rate_1": [0.25],
        "production_rate_2": [0.08],
        "production_rate_3": [0.01],
        "production_rate_4": [0.02],
        "bat_side": ["R"],
        "pitch_hand": ["R"],
        "gender": ["M"],
        "birth_city": ["UNKNOWN"],
        "birth_state_province": ["UNKNOWN"],
        "height_inches": [72.0],
        "weight_pounds": [190.0],
        "strike_zone_top": [3.4],
        "strike_zone_bottom": [1.6],
        "primary_position_code": ["1"],
    }
    alias = arrival_design(
        pl.DataFrame({**base, "birth_country": ["VEN"]}), feature_set="origin"
    )
    canonical = arrival_design(
        pl.DataFrame({**base, "birth_country": ["Venezuela"]}),
        feature_set="origin",
    )
    assert (alias == canonical).all()


def test_arrival_fit_requires_positive_regularization() -> None:
    with pytest.raises(ValueError, match="regularization_c"):
        fit_arrival_model(
            pl.DataFrame(), player_type="hitter", regularization_c=0.0
        )


def test_rate_regression_requires_training_priors_and_dampens_tiny_samples() -> None:
    row = pl.DataFrame(
        {
            "age_years": [21.0], "level_tier": ["AA"],
            "current_milb_workload": [1.0], "prior_affiliated_workload": [1.0],
            "prior_affiliated_seasons": [1.0], "on_40man": [False],
            "role_tier": ["CORNER"], "production_rate_1": [1.0],
            "production_rate_2": [1.0], "production_rate_3": [1.0],
            "production_rate_4": [1.0], "bat_side": ["R"],
            "pitch_hand": ["R"], "gender": ["M"], "birth_country": ["USA"],
            "birth_city": ["City"], "birth_state_province": ["State"],
            "height_inches": [72.0], "weight_pounds": [190.0],
            "strike_zone_top": [3.4], "strike_zone_bottom": [1.6],
            "primary_position_code": ["3"],
        }
    )
    with pytest.raises(ValueError, match="priors"):
        arrival_design(row, production_regression=100.0)
    raw = arrival_design(row)
    regressed = arrival_design(
        row,
        production_priors=(0.1, 0.1, 0.1, 0.1),
        production_regression=100.0,
    )
    assert (regressed[0, -4:] < raw[0, -4:]).all()


def test_baseball_interactions_expand_core_without_current_profile_fields() -> None:
    snapshots = pl.DataFrame(
        {"snapshot_year": [2021], "player_id": [1], "age_years": [21.0],
         "as_of_level_group": ["AA"]}
    )
    stats = pl.DataFrame(
        {"season": [2021], "stat_group": ["hitting"], "player_id": [1],
         "sport_id": [12], "plate_appearances": [100], "batters_faced": [0],
         "position_code": ["SS"]}
    )
    membership = pl.DataFrame(
        {"season": [2021], "player_id": [1], "on_40man": [False]}
    )
    skill = pl.DataFrame(
        {"season": [2021], "player_id": [1], "sport_id": [12],
         "plate_appearances": [100], "base_on_balls": [10],
         "intentional_walks": [0], "strike_outs": [20], "home_runs": [2],
         "doubles": [4], "triples": [1]}
    ).with_columns(
        pl.Series("hits", [25]), pl.Series("hit_by_pitch", [1])
    )
    cohort = build_arrival_cohort(
        snapshots, stats, membership, skill, snapshot_year=2021, horizon=2,
        player_type="hitter",
    )
    assert arrival_design(cohort, feature_set="baseball_interactions").shape[1] > (
        arrival_design(cohort, feature_set="core").shape[1]
    )


def test_established_role_requires_high_or_repeated_future_workload() -> None:
    snapshots = pl.DataFrame(
        {"snapshot_year": [2021, 2021, 2021], "player_id": [1, 2, 3],
         "age_years": [21.0, 21.0, 21.0], "as_of_level_group": ["AA"] * 3}
    )
    rows = []
    for player_id, future in {
        1: [(2022, 410)], 2: [(2022, 310), (2023, 305)], 3: [(2022, 399)],
    }.items():
        rows.append((2021, "hitting", player_id, 12, 100, 0, "SS"))
        rows.extend((year, "hitting", player_id, 1, pa, 0, "SS") for year, pa in future)
    stats = pl.DataFrame(
        rows,
        schema=["season", "stat_group", "player_id", "sport_id",
                "plate_appearances", "batters_faced", "position_code"],
        orient="row",
    )
    membership = pl.DataFrame(
        {"season": [2021] * 3, "player_id": [1, 2, 3], "on_40man": [False] * 3}
    )
    skill = pl.DataFrame(
        {"season": [2021] * 3, "player_id": [1, 2, 3], "sport_id": [12] * 3,
         "plate_appearances": [100] * 3, "base_on_balls": [10] * 3,
         "intentional_walks": [0] * 3, "strike_outs": [20] * 3,
         "home_runs": [2] * 3, "doubles": [4] * 3, "triples": [1] * 3}
    ).with_columns(
        pl.Series("hits", [25] * 3), pl.Series("hit_by_pitch", [1] * 3)
    )
    result = build_arrival_cohort(
        snapshots, stats, membership, skill, snapshot_year=2021, horizon=2,
        player_type="hitter",
    )
    established = dict(
        result.select("player_id", "established_role_within_horizon").iter_rows()
    )
    assert established == {1: 1, 2: 1, 3: 0}


def test_positive_hitter_component_role_is_league_relative_and_workload_gated() -> None:
    skill = pl.DataFrame(
        {
            "season": [2022, 2022, 2022], "player_id": [1, 2, 3],
            "sport_id": [1, 1, 1], "plate_appearances": [250, 250, 100],
            "base_on_balls": [50, 5, 40], "intentional_walks": [0, 0, 0],
            "hit_by_pitch": [0, 0, 0], "hits": [80, 30, 40],
            "doubles": [20, 5, 10], "triples": [2, 0, 1],
            "home_runs": [20, 2, 10],
        }
    )
    result = _positive_component_roles(
        skill, snapshot_year=2021, horizon=2, player_type="hitter"
    )
    assert result.get_column("player_id").to_list() == [1]
