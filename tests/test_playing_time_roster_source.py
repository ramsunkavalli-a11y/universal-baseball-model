from __future__ import annotations

from datetime import date

import pytest

from universal_baseball.playing_time_roster_source import project_team_roster_payload


def _payload() -> dict[str, object]:
    return {
        "roster": [
            {
                "person": {"id": 1, "fullName": "One Player"},
                "position": {"code": "3", "abbreviation": "1B"},
                "status": {"code": "A", "description": "Active"},
            },
            {
                "person": {"id": 2, "fullName": "Two Player"},
                "position": {"code": "6", "abbreviation": "SS"},
                "status": {"code": "A", "description": "Active"},
            },
        ]
    }


def test_project_team_roster_payload_preserves_snapshot_identity_and_status() -> None:
    frame = project_team_roster_payload(
        _payload(),
        team_id=137,
        season=2022,
        as_of_date=date(2022, 10, 15),
        roster_type="40Man",
    )
    assert frame.height == 2
    assert frame.get_column("player_id").to_list() == [1, 2]
    assert frame.get_column("team_id").unique().to_list() == [137]
    assert frame.get_column("season").unique().to_list() == [2022]
    assert frame.get_column("roster_type").unique().to_list() == ["40Man"]
    assert frame.item(0, "status_description") == "Active"


def test_project_team_roster_payload_rejects_duplicate_player_ids() -> None:
    payload = _payload()
    payload["roster"].append(payload["roster"][0])  # type: ignore[index,union-attr]
    with pytest.raises(ValueError, match="duplicate player IDs"):
        project_team_roster_payload(
            payload,
            team_id=137,
            season=2022,
            as_of_date=date(2022, 10, 15),
            roster_type="40Man",
        )


def test_project_team_roster_payload_rejects_unknown_roster_type() -> None:
    with pytest.raises(ValueError, match="unsupported roster type"):
        project_team_roster_payload(
            _payload(),
            team_id=137,
            season=2022,
            as_of_date=date(2022, 10, 15),
            roster_type="futureRoster",
        )
