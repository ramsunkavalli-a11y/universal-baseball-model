import polars as pl

from universal_baseball.affiliated_team_context_source import (
    audit_skill_context_coverage,
    project_team_context_payload,
)


def test_team_context_preserves_league_and_venue_identity() -> None:
    context = project_team_context_payload(
        {
            "teams": [{
                "id": 10,
                "name": "Test Club",
                "sport": {"id": 11},
                "league": {"id": 112, "name": "International League"},
                "division": {"id": 999},
                "venue": {"id": 1000, "name": "Test Park"},
            }]
        },
        season=2025,
    )
    assert context.item(0, "league_id") == 112
    assert context.item(0, "venue_id") == 1000
    coverage = audit_skill_context_coverage(
        pl.DataFrame({"season": [2025], "team_id": [10], "sport_id": [11]}),
        context,
    )
    assert coverage["coverage_rate"] == 1.0
