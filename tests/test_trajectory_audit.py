from __future__ import annotations

import polars as pl

from universal_baseball.trajectory_audit import (
    build_trajectory_profile,
    collapse_trajectory_evidence,
)


def test_collapse_trajectory_evidence_nulls_conflicting_fields() -> None:
    frame = pl.DataFrame(
        {
            "game_pk": ["1", "1", "1"],
            "at_bat_number": ["0", "0", "0"],
            "pitch_number": ["1", "1", "1"],
            "type": ["X", "X", "X"],
            "bb_type": ["popup", "popup", "fly_ball"],
            "hit_location": ["6", "6", "6"],
            "description": ["Batter pops out.", "Batter pops out.", "Batter pops out."],
        }
    )

    row = collapse_trajectory_evidence(frame).to_dicts()[0]

    assert row["type"] == "X"
    assert row["type__conflict"] is False
    assert row["bb_type"] is None
    assert row["bb_type__conflict"] is True
    assert row["hit_location"] == "6"


def test_profile_separates_popup_fly_and_bunt_behavior() -> None:
    frame = pl.DataFrame(
        {
            "game_pk": ["1"] * 7,
            "at_bat_number": [str(i) for i in range(7)],
            "pitch_number": ["1"] * 7,
            "type": ["X", "X", "X", "X", "X", "X", "S"],
            "bb_type": [
                "popup",
                "popup",
                "fly_ball",
                "ground_ball",
                "bunt_grounder",
                None,
                None,
            ],
            "hit_location": ["4", "8", "8", "6", "5", None, None],
            "description": [
                "Batter pops out to second baseman.",
                "Batter pops out to center fielder in foul territory.",
                "Batter flies out to center fielder.",
                "Batter grounds out to shortstop.",
                "Batter bunts for a single to third baseman.",
                "Ball put in play with unknown trajectory.",
                "Swinging Strike.",
            ],
        },
        schema={
            "game_pk": pl.String,
            "at_bat_number": pl.String,
            "pitch_number": pl.String,
            "type": pl.String,
            "bb_type": pl.String,
            "hit_location": pl.String,
            "description": pl.String,
        },
    )

    report = build_trajectory_profile(frame)

    assert report["in_play_pitch_key_count"] == 6
    assert report["known_trajectory_count"] == 5
    assert report["unknown_trajectory_count"] == 1
    assert report["trajectory_counts"]["popup"] == 2
    assert report["bunt_in_play_count"] == 1
    assert report["bunt_share_of_in_play"] == 1 / 6

    popup = report["trajectory_details"]["popup"]
    assert popup["infield_first_touch_count"] == 1
    assert popup["outfield_first_touch_count"] == 1
    assert popup["description_mentions_foul_count"] == 1
    assert popup["description_hit_like_count"] == 0

    bunt = report["trajectory_details"]["bunt_grounder"]
    assert bunt["description_hit_like_count"] == 1


def test_profile_counts_foul_airborne_descriptions_without_parsing_for_production() -> None:
    frame = pl.DataFrame(
        {
            "game_pk": ["1", "1", "1"],
            "at_bat_number": ["0", "1", "2"],
            "pitch_number": ["1", "1", "1"],
            "type": ["X", "X", "X"],
            "bb_type": ["popup", "fly_ball", "line_drive"],
            "hit_location": ["2", "7", "6"],
            "description": [
                "Batter pops out to catcher in foul territory.",
                "Batter flies out to left fielder.",
                "Batter lines out to shortstop in foul territory.",
            ],
        }
    )

    report = build_trajectory_profile(frame)

    assert report["airborne_count"] == 2
    assert report["airborne_description_mentions_foul_count"] == 1
    assert report["airborne_description_mentions_foul_rate"] == 0.5
