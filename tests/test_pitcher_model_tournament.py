import polars as pl

from universal_baseball.hitter_target_architecture import feature_columns
from universal_baseball.pitcher_model_tournament import to_generic_two_part_panel


def test_pitcher_adapter_excludes_every_future_target() -> None:
    panel = pl.DataFrame(
        {
            "origin_year": [2024],
            "target_season": [2025],
            "player_id": [1],
            "lag0__highest_level": ["AAA"],
            "lag0__strikeout_rate": [0.30],
            "target_mlb_bf": [100],
            "target_mlb_active": [1],
            "target_conditional_component_war_per_800": [2.0],
            "target_component_war": [0.25],
        }
    )

    generic = to_generic_two_part_panel(panel)

    assert feature_columns(generic) == [
        "lag0__highest_level",
        "lag0__strikeout_rate",
    ]
