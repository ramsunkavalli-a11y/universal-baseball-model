from universal_baseball.affiliated_game_context_source import project_schedule_payload


def test_project_schedule_payload_keeps_complete_scored_games_only() -> None:
    payload = {
        "dates": [{"games": [
            {
                "gamePk": 10, "officialDate": "2024-04-02", "gameType": "R",
                "status": {"statusCode": "F"}, "scheduledInnings": 9,
                "venue": {"id": 50},
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
