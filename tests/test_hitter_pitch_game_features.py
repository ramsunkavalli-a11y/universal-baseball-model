from datetime import datetime, timezone

import polars as pl

from universal_baseball.hitter_pitch_game_features import (
    attach_pitch_game_lags,
    build_player_season_pitch_game_features,
    classify_pitch_sequence,
)


def _pitches() -> pl.DataFrame:
    rows = []
    codes = ["B", "C", "F", "S"]
    counts = [(1, 0), (1, 1), (1, 2), (1, 3)]
    for player, game, pitcher in ((10, 100, 30), (11, 101, 31)):
        for number, (code, (balls, strikes)) in enumerate(
            zip(codes, counts, strict=True), start=1
        ):
            rows.append(
                {
                    "season": 2023,
                    "level": "aa",
                    "game_pk": game,
                    "at_bat_index": 1,
                    "pitch_number": number,
                    "batter": player,
                    "pitcher": pitcher,
                    "stand": "R",
                    "p_throws": "R" if player == 10 else "L",
                    "balls": balls,
                    "strikes": strikes,
                    "pitch_result_code": code,
                }
            )
    return pl.DataFrame(rows)


def _games() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_pk": [100, 101],
            "day_night": ["night", "day"],
            "temperature_f": [80.0, 60.0],
            "wind_mph": [10.0, 5.0],
            "wind_direction": ["Out To RF", "In From CF"],
            "weather_condition": ["Clear", "Cloudy"],
            "turf_type": ["Grass", "Artificial"],
            "roof_type": ["Open", "Closed"],
            "left_field_line_ft": [330, 320],
            "center_field_ft": [400, 390],
            "right_field_line_ft": [325, 315],
            "attendance": [5000, 6000],
            "game_duration_minutes": [160, 180],
            "delay_duration_minutes": [0, 15],
            "home_plate_umpire_id": [70, 71],
            "venue_id": [80, 81],
            "scheduled_datetime_utc": [
                datetime(2023, 6, 1, 1, tzinfo=timezone.utc),
                datetime(2023, 6, 2, 18, tzinfo=timezone.utc),
            ],
            "first_pitch_datetime_utc": [
                datetime(2023, 6, 1, 1, 5, tzinfo=timezone.utc),
                datetime(2023, 6, 2, 18, 4, tzinfo=timezone.utc),
            ],
        }
    )


def test_classify_pitch_sequence_reconstructs_pre_pitch_count() -> None:
    result = classify_pitch_sequence(_pitches()).filter(pl.col("batter") == 10)

    assert result["pre_balls"].to_list() == [0, 1, 1, 1]
    assert result["pre_strikes"].to_list() == [0, 0, 1, 2]
    assert result["is_two_strike_pitch"].to_list() == [False, False, False, True]
    assert result["is_swing"].to_list() == [False, False, True, True]
    assert result["is_contact"].to_list() == [False, False, True, False]


def test_build_features_keeps_pitch_skill_and_game_environment() -> None:
    result = build_player_season_pitch_game_features(
        _pitches(), _games(), rate_prior_weight=1.0, split_prior_weight=1.0
    )
    player_10 = result.filter(pl.col("player_id") == 10).row(0, named=True)
    player_11 = result.filter(pl.col("player_id") == 11).row(0, named=True)

    assert result.height == 2
    assert player_10["pitch_count"] == 4
    assert player_10["pa_count"] == 1
    assert player_10["pitches_per_pa"] == 4.0
    assert player_10["two_strike_pa_rate"] == 1.0
    assert player_10["mean_temperature_f"] == 80.0
    assert player_10["night_pa_share"] == 1.0
    assert player_10["wind_out_pa_share"] == 1.0
    assert player_11["artificial_surface_pa_share"] == 1.0
    assert player_11["closed_roof_pa_share"] == 1.0
    assert player_10["split_pitches_vs_r"] == 4
    assert player_11["split_pitches_vs_l"] == 4


def test_attach_pitch_game_lags_preserves_missing_history_flag() -> None:
    annual = build_player_season_pitch_game_features(
        _pitches(), _games(), rate_prior_weight=1.0, split_prior_weight=1.0
    )
    panel = pl.DataFrame(
        {
            "origin_year": [2023, 2024],
            "player_id": [10, 10],
            "target_component_war": [0.0, 0.0],
        }
    )

    result = attach_pitch_game_lags(panel, annual, lags=(0, 1))

    assert result["pitch_lag0__available"].to_list() == [1, 0]
    assert result["pitch_lag1__available"].to_list() == [0, 1]
