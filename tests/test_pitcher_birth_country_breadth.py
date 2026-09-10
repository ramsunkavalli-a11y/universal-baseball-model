import polars as pl

from universal_baseball.pitcher_demographic_breadth import add_pitcher_country_features


def test_country_features_normalize_aliases_and_leave_other_as_reference() -> None:
    features = pl.DataFrame(
        {
            "player_id": [1, 2, 3, 4],
            "age_relative": [1.0, -1.0, 0.5, 0.0],
        }
    )
    demographics = pl.DataFrame(
        {
            "player_id": [1, 2, 3, 4],
            "birth_country": ["USA", "DOM", "VEN", "Canada"],
        }
    )
    result = add_pitcher_country_features(features, demographics).sort("player_id")

    assert result.get_column("country").to_list() == [
        "USA", "Dominican Republic", "Venezuela", "Canada"
    ]
    assert result.get_column("country_usa").to_list() == [1.0, 0.0, 0.0, 0.0]
    assert result.get_column("country_dominican").to_list() == [0.0, 1.0, 0.0, 0.0]
    assert result.get_column("country_venezuela").to_list() == [0.0, 0.0, 1.0, 0.0]
    assert result.get_column("age_x_dominican").to_list() == [0.0, -1.0, 0.0, 0.0]
