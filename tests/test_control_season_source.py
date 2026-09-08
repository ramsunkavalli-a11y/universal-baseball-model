from __future__ import annotations

from datetime import date

import pytest

from universal_baseball.control_season_source import project_season_window


def test_project_season_window_uses_official_regular_season_dates() -> None:
    result = project_season_window(
        {
            "seasons": [
                {
                    "seasonId": "2026",
                    "regularSeasonStartDate": "2026-03-25",
                    "regularSeasonEndDate": "2026-09-27",
                }
            ]
        },
        season=2026,
    ).row(0, named=True)
    assert result["start_date"] == date(2026, 3, 25)
    assert result["end_date"] == date(2026, 9, 27)


def test_project_season_window_rejects_wrong_season() -> None:
    with pytest.raises(ValueError, match="does not match"):
        project_season_window(
            {
                "seasons": [
                    {
                        "seasonId": "2025",
                        "regularSeasonStartDate": "2025-03-27",
                        "regularSeasonEndDate": "2025-09-28",
                    }
                ]
            },
            season=2026,
        )
