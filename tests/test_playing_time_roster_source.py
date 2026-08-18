from __future__ import annotations

from datetime import date

import pytest

from universal_baseball.playing_time_roster_source import (
    project_team_40man_membership_payload,
    project_team_roster_payload,
)


def _payload() -> dict[str, object]:
    return {
        "roster": [
            {
                "person": {"id": 1, "fullName": "One Player", "link": "/api/v1/people/1"},
                "position": {"code": "3", "abbreviation": "1B"},
                "status": {"code": "A", "description": "Active"},
                "parentTeamId": 137,
            },
            {
                "person": {"id": 2, "fullName": "Two Player", "link": "/api/v1/people/2"},
                "position": {"code": "6", "abbreviation": "SS"},
                "status": {"code": "A", "description": "Active"},
                "parentTeamId": 137,
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
    assert frame.item(0, "status_description") == "Active"


def test_row_level_roster_projection_still_rejects_duplicate_player_ids() -> None:
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


def test_40man_membership_allows_conflicting_status_duplicate_but_not_status_inference() -> None:
    payload = _payload()
    payload["roster"].append(  # type: ignore[index,union-attr]
        {
            "person": {"id": 1, "fullName": "One Player", "link": "/api/v1/people/1"},
            "position": {"code": "3", "abbreviation": "1B"},
            "status": {"code": "MIN", "description": "Reassigned to Minors"},
            "parentTeamId": 137,
        }
    )
    membership = project_team_40man_membership_payload(
        payload,
        team_id=137,
        season=2022,
        as_of_date=date(2022, 10, 15),
    )
    player = membership.filter(membership["player_id"] == 1).row(0, named=True)
    assert membership.height == 2
    assert player["on_40man"] is True
    assert player["source_row_count"] == 2
    assert player["source_status_conflict"] is True
    assert player["source_status_codes"] == "A,MIN"


def test_40man_membership_rejects_duplicate_identity_conflict() -> None:
    payload = _payload()
    payload["roster"].append(  # type: ignore[index,union-attr]
        {
            "person": {"id": 1, "fullName": "Different Person", "link": "/api/v1/people/1"},
            "status": {"code": "MIN", "description": "Reassigned to Minors"},
            "parentTeamId": 137,
        }
    )
    with pytest.raises(ValueError, match="duplicate identity conflict"):
        project_team_40man_membership_payload(
            payload,
            team_id=137,
            season=2022,
            as_of_date=date(2022, 10, 15),
        )


def test_40man_membership_rejects_parent_team_conflict() -> None:
    payload = _payload()
    payload["roster"][0]["parentTeamId"] = 999  # type: ignore[index]
    with pytest.raises(ValueError, match="parentTeamId mismatch"):
        project_team_40man_membership_payload(
            payload,
            team_id=137,
            season=2022,
            as_of_date=date(2022, 10, 15),
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
