import polars as pl

from universal_baseball.pitcher_contact_features import (
    build_hitter_full_bip_outcomes,
    build_hitter_full_bip_profile,
    build_pitcher_contact_panel,
    build_pitcher_full_bip_outcomes,
    build_pitcher_full_bip_profile,
)


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


def test_pitcher_full_bip_profile_reuses_hitter_classifier() -> None:
    contacts = pl.DataFrame(
        {
            "game_date": ["2021-05-01", "2021-05-01", "2021-05-01"],
            "league_id": [-2, -2, -2],
            "source_level": ["aa", "aa", "aa"],
            "game_pk": [1, 1, 1],
            "at_bat_index": [1, 2, 3],
            "pitch_number": [3, 2, 4],
            "source_batter_id": [10, 11, 12],
            "source_pitcher_id": [7, 7, 7],
            "source_is_in_play": [True, True, True],
            "conflict_field_count": [0, 0, 0],
            "bb_type": ["fly_ball", "ground_ball", "bunt_grounder"],
            "hc_x": [80.0, 170.0, 100.0],
            "hc_y": [100.0, 100.0, 100.0],
            "batter_side": ["R", "R", "R"],
            "result_description": [
                "Batter flies out to center fielder.",
                "Batter grounds out to second baseman.",
                "Batter is out on a bunt.",
            ],
            "structured_event": ["field_out", "field_out", "sac_bunt"],
        }
    )
    profile = build_pitcher_full_bip_profile(contacts)
    counts = {
        row["core_bin"]: row["occurrence_count"] for row in profile.to_dicts()
    }
    assert counts == {"PULL_OFFB": 1, "OPPO_GB": 1}
    outcomes = build_pitcher_full_bip_outcomes(contacts)
    assert outcomes.select("core_bin", "canonical_outcome", "occurrence_count").to_dicts() == [
        {"core_bin": "OPPO_GB", "canonical_outcome": "OTHER_OUT", "occurrence_count": 1},
        {"core_bin": "PULL_OFFB", "canonical_outcome": "OTHER_OUT", "occurrence_count": 1},
    ]


def test_pitcher_bip_outcomes_exclude_noncontact_terminal_label() -> None:
    contacts = pl.DataFrame(
        {
            "game_date": ["2021-05-01"], "league_id": [-2], "source_level": ["aa"],
            "game_pk": [1], "at_bat_index": [1], "pitch_number": [3],
            "source_batter_id": [10], "source_pitcher_id": [7],
            "source_is_in_play": [True], "conflict_field_count": [0],
            "bb_type": ["fly_ball"], "hc_x": [80.0], "hc_y": [100.0],
            "batter_side": ["R"], "structured_event": ["hit_by_pitch"],
            "result_description": ["Batter hit by pitch."],
        }
    )
    assert build_pitcher_full_bip_outcomes(contacts).is_empty()


def test_hitter_and_pitcher_profiles_share_event_classification() -> None:
    contacts = pl.DataFrame(
        {
            "game_date": ["2021-05-01", "2021-05-01"],
            "league_id": [-2, -2], "source_level": ["aa", "aa"],
            "game_pk": [1, 1], "at_bat_index": [1, 2], "pitch_number": [3, 2],
            "source_batter_id": [10, 11], "source_pitcher_id": [7, 7],
            "source_is_in_play": [True, True], "conflict_field_count": [0, 0],
            "bb_type": ["fly_ball", "ground_ball"], "hc_x": [80.0, 170.0],
            "hc_y": [100.0, 100.0], "batter_side": ["R", "R"],
            "structured_event": ["home_run", "field_out"],
            "result_description": ["Batter homers.", "Batter grounds out."],
        }
    )
    hitter = build_hitter_full_bip_profile(contacts)
    pitcher = build_pitcher_full_bip_profile(contacts)
    assert hitter.select("core_bin", "occurrence_count").group_by("core_bin").sum().sort(
        "core_bin"
    ).equals(
        pitcher.select("core_bin", "occurrence_count").group_by("core_bin").sum().sort(
            "core_bin"
        )
    )
    outcomes = build_hitter_full_bip_outcomes(contacts)
    assert set(outcomes["canonical_outcome"].to_list()) == {"HR", "OTHER_OUT"}
