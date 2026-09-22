from datetime import datetime, timezone

from universal_baseball.affiliated_game_context_source import project_schedule_payload


def test_project_schedule_payload_keeps_complete_scored_games_only() -> None:
    payload = {
        "dates": [{"games": [
            {
                "gamePk": 10, "officialDate": "2024-04-02", "gameType": "R",
                "gameDate": "2024-04-03T01:05:00Z", "dayNight": "night",
                "status": {"statusCode": "F"}, "scheduledInnings": 9,
                "venue": {
                    "id": 50, "name": "Test Park",
                    "location": {
                        "city": "Somewhere", "stateAbbrev": "CA",
                        "country": "USA",
                        "defaultCoordinates": {"latitude": 34.1, "longitude": -118.2},
                    },
                    "fieldInfo": {
                        "capacity": 10000, "turfType": "Grass", "roofType": "Open",
                        "leftLine": 330, "center": 400, "rightLine": 325,
                    },
                },
                "weather": {"condition": "Clear", "temp": "74", "wind": "12 mph, Out To RF"},
                "gameInfo": {
                    "attendance": 8800, "firstPitch": "2024-04-03T01:09:00.000Z",
                    "gameDurationMinutes": 171, "delayDurationMinutes": 0,
                },
                "officials": [{
                    "official": {"id": 777}, "officialType": "Home Plate",
                }],
                "teams": {
                    "home": {"team": {"id": 1}, "score": 7},
                    "away": {"team": {"id": 2}, "score": 3},
                },
            },
            {
                "gamePk": 11, "officialDate": "2024-04-03", "gameType": "R",
                "status": {"statusCode": "S"}, "venue": {"id": 50},
                "teams": {
                    "home": {"team": {"id": 1}},
                    "away": {"team": {"id": 2}},
                },
            },
        ]}]
    }

    result = project_schedule_payload(payload, season=2024, sport_id=11)

    assert result.height == 1
    assert result.row(0, named=True)["home_score"] == 7
    assert result.row(0, named=True)["venue_id"] == 50
    row = result.row(0, named=True)
    assert row["scheduled_datetime_utc"] == datetime(
        2024, 4, 3, 1, 5, tzinfo=timezone.utc
    )
    assert row["first_pitch_datetime_utc"] == datetime(
        2024, 4, 3, 1, 9, tzinfo=timezone.utc
    )
    assert row["wind_mph"] == 12.0
    assert row["wind_direction"] == "Out To RF"
    assert row["temperature_f"] == 74.0
    assert row["home_plate_umpire_id"] == 777
    assert row["turf_type"] == "Grass"
    assert row["center_field_ft"] == 400


def test_project_schedule_payload_deduplicates_rescheduled_game_listing() -> None:
    game = {
        "gamePk": 10, "officialDate": "2024-04-02", "gameType": "R",
        "status": {"statusCode": "F"}, "scheduledInnings": 9,
        "venue": {"id": 50},
        "teams": {
            "home": {"team": {"id": 1}, "score": 7},
            "away": {"team": {"id": 2}, "score": 3},
        },
    }
    result = project_schedule_payload(
        {"dates": [{"games": [game]}, {"games": [game]}]},
        season=2024,
        sport_id=11,
    )
    assert result.height == 1


def test_project_schedule_payload_excludes_conflicting_resume_venues() -> None:
    def game(venue: int) -> dict:
        return {
            "gamePk": 10, "officialDate": "2024-04-02", "gameType": "R",
            "status": {"statusCode": "F"}, "scheduledInnings": 9,
            "venue": {"id": venue},
            "teams": {
                "home": {"team": {"id": 1}, "score": 7},
                "away": {"team": {"id": 2}, "score": 3},
            },
        }
    result = project_schedule_payload(
        {"dates": [{"games": [game(50)]}, {"games": [game(60)]}]},
        season=2024,
        sport_id=11,
    )
    assert result.is_empty()
