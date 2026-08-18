from __future__ import annotations

import polars as pl

from universal_baseball.position_role_profile import build_batting_role_profiles


def _usage(rows: list[dict[str, object]]) -> pl.DataFrame:
    return pl.DataFrame(rows).with_columns(
        pl.col("season").cast(pl.Int64),
        pl.col("player_id").cast(pl.Int64),
        pl.col("games_played").cast(pl.Int64),
        pl.col("games_started").cast(pl.Int64),
        pl.col("fielding_outs").cast(pl.Int64),
    )


def test_role_profile_prefers_games_started_and_keeps_dh() -> None:
    frame = _usage(
        [
            {
                "season": 2024,
                "player_id": 1,
                "position_abbreviation": "CF",
                "games_played": 100,
                "games_started": 60,
                "fielding_outs": 1500,
            },
            {
                "season": 2024,
                "player_id": 1,
                "position_abbreviation": "DH",
                "games_played": 50,
                "games_started": 40,
                "fielding_outs": 0,
            },
        ]
    )
    built = build_batting_role_profiles(frame)
    profile = built.profile.sort("position_abbreviation")
    assert set(profile.get_column("role_evidence_mode").to_list()) == {"games_started"}
    probabilities = {
        row["position_abbreviation"]: row["role_probability"]
        for row in profile.iter_rows(named=True)
    }
    assert probabilities["CF"] == 0.6
    assert probabilities["DH"] == 0.4
    summary = built.player_season.row(0, named=True)
    assert summary["primary_position"] == "CF"
    assert summary["primary_role_share"] == 0.6


def test_role_profile_uses_games_fallback_when_player_has_no_starts() -> None:
    frame = _usage(
        [
            {
                "season": 2024,
                "player_id": 2,
                "position_abbreviation": "2B",
                "games_played": 6,
                "games_started": 0,
                "fielding_outs": 30,
            },
            {
                "season": 2024,
                "player_id": 2,
                "position_abbreviation": "SS",
                "games_played": 4,
                "games_started": 0,
                "fielding_outs": 18,
            },
        ]
    )
    built = build_batting_role_profiles(frame)
    summary = built.player_season.row(0, named=True)
    assert summary["role_evidence_mode"] == "games_played_fallback"
    assert summary["primary_position"] == "2B"
    assert summary["primary_role_share"] == 0.6


def test_role_profile_excludes_pitcher_usage_from_batting_channel() -> None:
    frame = _usage(
        [
            {
                "season": 2024,
                "player_id": 3,
                "position_abbreviation": "P",
                "games_played": 20,
                "games_started": 20,
                "fielding_outs": 500,
            },
            {
                "season": 2024,
                "player_id": 4,
                "position_abbreviation": "P",
                "games_played": 10,
                "games_started": 10,
                "fielding_outs": 250,
            },
            {
                "season": 2024,
                "player_id": 4,
                "position_abbreviation": "DH",
                "games_played": 15,
                "games_started": 12,
                "fielding_outs": 0,
            },
        ]
    )
    built = build_batting_role_profiles(frame)
    assert built.player_season.get_column("player_id").to_list() == [4]
    assert built.player_season.item(0, "primary_position") == "DH"


def test_primary_tie_break_uses_defensive_outs_before_position_code() -> None:
    frame = _usage(
        [
            {
                "season": 2024,
                "player_id": 5,
                "position_abbreviation": "2B",
                "games_played": 10,
                "games_started": 5,
                "fielding_outs": 90,
            },
            {
                "season": 2024,
                "player_id": 5,
                "position_abbreviation": "SS",
                "games_played": 10,
                "games_started": 5,
                "fielding_outs": 120,
            },
        ]
    )
    built = build_batting_role_profiles(frame)
    assert built.player_season.item(0, "primary_position") == "SS"
