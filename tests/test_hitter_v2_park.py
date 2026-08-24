import polars as pl

from universal_baseball.hitter_v2_park import (
    project_schedule_venues,
    resolve_schedule_venue_duplicates,
)


def _payload() -> dict[str, object]:
    return {
        "dates": [
            {
                "date": "2023-05-01",
                "games": [
                    {
                        "gamePk": 1,
                        "gameType": "R",
                        "status": {"codedGameState": "F"},
                        "officialDate": "2023-05-01",
                        "venue": {"id": 100, "name": "Example Park"},
                        "teams": {
                            "away": {"team": {"id": 10}},
                            "home": {"team": {"id": 20}},
                        },
                    },
                    {
                        "gamePk": 2,
                        "gameType": "S",
                        "status": {"codedGameState": "F"},
                        "venue": {"id": 200, "name": "Spring Park"},
                        "teams": {
                            "away": {"team": {"id": 30}},
                            "home": {"team": {"id": 40}},
                        },
                    },
                ],
            }
        ]
    }


def test_schedule_projection_keeps_regular_season_venue() -> None:
    result = project_schedule_venues(_payload(), season=2023, sport_id=11)
    assert result.height == 1
    assert result.row(0, named=True)["venue_id"] == 100
    assert result.row(0, named=True)["venue_source_status"] == (
        "accepted_official_schedule_venue"
    )


def test_duplicate_schedule_conflict_is_retained_fail_closed() -> None:
    base = project_schedule_venues(_payload(), season=2023, sport_id=11)
    conflict = pl.concat(
        [
            base,
            base.with_columns(pl.lit(999, dtype=pl.Int64).alias("venue_id")),
        ],
        how="vertical",
    )
    result = resolve_schedule_venue_duplicates(conflict).row(0, named=True)
    assert result["venue_context_eligible"] is False
    assert result["venue_source_status"] == (
        "failed_closed_schedule_venue_conflict_or_missing"
    )


def test_duplicate_schedule_date_does_not_invalidate_unique_venue() -> None:
    base = project_schedule_venues(_payload(), season=2023, sport_id=11)
    changed_date = base.with_columns(pl.lit("2023-05-02").alias("official_date"))
    result = resolve_schedule_venue_duplicates(
        pl.concat([base, changed_date], how="vertical")
    ).row(0, named=True)
    assert result["venue_context_eligible"] is True
    assert result["raw_schedule_row_count"] == 2
