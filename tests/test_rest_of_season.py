from datetime import date

import polars as pl

from universal_baseball.rest_of_season import (
    build_hitter_ros_paths,
    build_remaining_base_salary,
    project_team_schedule_calendar,
)


def test_schedule_and_salary_use_days_after_as_of() -> None:
    payload = {
        "dates": [
            {
                "games": [
                    {
                        "gamePk": 1, "gameType": "R", "officialDate": "2026-04-01",
                        "teams": {"home": {"team": {"id": 1}}, "away": {"team": {"id": 2}}},
                        "status": {
                            "abstractGameState": "Final", "detailedState": "Postponed"
                        },
                    }
                ]
            },
            {
                "games": [
                    {
                        "gamePk": 1, "gameType": "R", "officialDate": "2026-04-01",
                        "teams": {"home": {"team": {"id": 1}}, "away": {"team": {"id": 2}}},
                        "status": {
                            "abstractGameState": "Final", "detailedState": "Final"
                        },
                    }
                ]
            },
            {
                "games": [
                    {
                        "gamePk": 2, "gameType": "R", "officialDate": "2026-04-10",
                        "teams": {"home": {"team": {"id": 2}}, "away": {"team": {"id": 1}}},
                        "status": {"abstractGameState": "Preview"},
                    }
                ]
            },
        ]
    }
    calendar, completed, scheduled = project_team_schedule_calendar(
        payload, season=2026, as_of_date=date(2026, 4, 5)
    )
    assert (completed, scheduled) == (1, 2)
    assert calendar.item(0, "championship_season_days") == 10
    assert calendar.item(0, "remaining_days_after_as_of") == 5
    salary = build_remaining_base_salary(
        pl.DataFrame(
            {
                "player_id": [7], "organization_id": [1], "payroll_year": [2026],
                "amount_dollars": [1_000_000], "term_label": ["salary_or_option_amount"],
                "overlay_status": ["accepted_contract_overlay"],
                "source_snapshot_id": ["fg:test"],
            }
        ),
        calendar,
        as_of_date=date(2026, 4, 5),
    )
    assert salary.item(0, "remaining_base_salary_dollars") == 500_000


def test_hitter_ros_blends_current_pace_and_full_season_prior() -> None:
    result = build_hitter_ros_paths(
        pl.DataFrame({"player_id": [1, 2]}),
        pl.DataFrame({"player_id": [1], "batting_plate_appearances": [200]}),
        pl.DataFrame({"player_id": [1, 2], "expected_mlb_pa": [500.0, 100.0]}),
        pl.DataFrame(
            {
                "player_id": [1, 2],
                "conditional_war_per_600_pa": [3.0, 2.0],
            }
        ),
        as_of_date=date(2026, 7, 1),
        completed_league_games=1215,
        scheduled_league_games=2430,
    )
    assert result.height == 2
    assert result.filter(pl.col("player_id") == 2).item(
        0, "projected_remaining_opportunity"
    ) == 50.0
    assert result.get_column("projected_remaining_war").is_finite().all()
