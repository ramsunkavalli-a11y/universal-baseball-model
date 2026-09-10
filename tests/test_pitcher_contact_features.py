import polars as pl

from universal_baseball.pitcher_contact_features import build_pitcher_contact_panel


def test_pitcher_contact_panel_keeps_missingness_in_denominators_explicit() -> None:
    contacts = pl.DataFrame(
        {
            "game_date": ["2021-05-01"] * 5,
            "source_level": ["aa"] * 5,
            "source_pitcher_id": [7] * 5,
            "source_is_in_play": [True] * 5,
            "conflict_field_count": [0, 0, 0, 1, 0],
            "bb_type": ["ground_ball", "fly_ball", "popup", None, "line_drive"],
            "hc_x": [100.0, 100.0, 150.0, None, 125.42],
            "hc_y": [150.0, 150.0, 150.0, None, 150.0],
            "batter_side": ["R", "R", "L", "R", "R"],
        }
    )
    row = build_pitcher_contact_panel(contacts).row(0, named=True)
    assert row["season"] == 2021
    assert row["contact_count"] == 5
    assert row["trajectory_known_count"] == 4
    assert row["ground_count"] == 1
    assert row["airborne_count"] == 3
    assert row["popup_count"] == 1
    assert row["direction_known_count"] == 4
    assert row["conflicted_contact_count"] == 1


def test_pitcher_contact_panel_excludes_noncontacts_and_missing_pitcher() -> None:
    contacts = pl.DataFrame(
        {
            "game_date": ["2021-05-01", "2021-05-01"],
            "source_level": ["aa", "aa"],
            "source_pitcher_id": [7, None],
            "source_is_in_play": [False, True],
            "conflict_field_count": [0, 0],
            "bb_type": [None, "ground_ball"],
            "hc_x": [None, 100.0],
            "hc_y": [None, 150.0],
            "batter_side": ["R", "R"],
        }
    )
    assert build_pitcher_contact_panel(contacts).is_empty()
