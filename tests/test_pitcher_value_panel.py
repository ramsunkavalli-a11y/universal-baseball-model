import polars as pl
import pytest

from universal_baseball.pitcher_value_panel import (
    build_neutral_mlb_pitcher_value_targets,
    build_pitcher_stat_features,
    build_pitcher_value_panel,
)


def test_pitcher_stat_features_aggregate_levels_and_environment() -> None:
    source = pl.DataFrame(
        {
            "season": [2023, 2023, 2023],
            "player_id": [1, 1, 2],
            "level_group": ["AA", "AAA", "AAA"],
            "reported_age": [22.0, 22.0, 25.0],
            "games": [5, 4, 10],
            "starts": [5, 0, 10],
            "batters_faced": [100, 50, 200],
            "strike_outs": [30, 10, 20],
            "base_on_balls": [11, 5, 20],
            "intentional_walks": [1, 0, 0],
            "hit_batters": [2, 1, 4],
            "home_runs": [3, 2, 10],
        }
    )

    result = build_pitcher_stat_features(source)
    row = result.filter(pl.col("player_id") == 1).row(named=True)

    assert row["batters_faced"] == 150
    assert row["ubb"] == 15
    assert row["highest_level"] == "AAA"
    assert row["bf_level__AA"] == 100
    assert row["bf_level__AAA"] == 50
    assert row["strikeout_rate"] == pytest.approx(40 / 150)
    assert row["start_share"] == pytest.approx(5 / 9)
    assert row["relative_strikeout_rate"] > 0


def test_pitcher_value_targets_center_league_runs() -> None:
    pitching = pl.DataFrame(
        {
            "season": [2024, 2024],
            "player_id": [1, 2],
            "pitching_bf": [100, 100],
            "pitching_so": [30, 10],
            "pitching_ubb": [5, 15],
            "pitching_hbp": [1, 3],
            "pitching_hr": [2, 8],
        }
    )

    result = build_neutral_mlb_pitcher_value_targets(pitching)
    strong = result.filter(pl.col("player_id") == 1).row(named=True)
    weak = result.filter(pl.col("player_id") == 2).row(named=True)

    assert strong["component_war"] > weak["component_war"]
    assert result["pitching_runs_above_average_per_800"].mean() == pytest.approx(0.0)


def test_pitcher_panel_is_zero_inclusive_and_gap_aware() -> None:
    stats = pl.DataFrame(
        {
            "season": [2018, 2019, 2021, 2021],
            "player_id": [1, 1, 1, 2],
            "highest_level": ["A", "AA", "AAA", "AA"],
            "batters_faced": [100, 120, 140, 80],
        }
    )
    targets = pl.DataFrame(
        {
            "season": [2022],
            "player_id": [1],
            "mlb_bf": [50],
            "mlb_active": [1],
            "conditional_component_war_per_800": [2.0],
            "component_war": [0.125],
        }
    )

    panel = build_pitcher_value_panel(stats, targets, origins=(2021,))
    player_one = panel.filter(pl.col("player_id") == 1).row(named=True)
    player_two = panel.filter(pl.col("player_id") == 2).row(named=True)

    assert player_one["lag1__missing"] == 1
    assert player_one["lag2__missing"] == 0
    assert player_one["lag2__highest_level"] == "AA"
    assert player_one["target_component_war"] == pytest.approx(0.125)
    assert player_two["target_mlb_active"] == 0
    assert player_two["target_component_war"] == 0.0


def test_pitcher_panel_refuses_protected_target() -> None:
    stats = pl.DataFrame(
        {"season": [2025], "player_id": [1], "highest_level": ["AAA"]}
    )
    targets = pl.DataFrame(
        {
            "season": [2026],
            "player_id": [1],
            "mlb_bf": [1],
            "mlb_active": [1],
            "conditional_component_war_per_800": [1.0],
            "component_war": [0.00125],
        }
    )

    with pytest.raises(ValueError, match="2026"):
        build_pitcher_value_panel(stats, targets, origins=(2025,))
