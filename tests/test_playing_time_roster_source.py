from __future__ import annotations

from datetime import date

import pytest

import universal_baseball.playing_time_roster_source as roster_source
from universal_baseball.playing_time_roster_source import (
    fetch_team_40man_membership_as_of,
    fetch_team_full_roster_candidates_as_of,
    project_team_40man_membership_payload,
    project_team_full_roster_candidates_payload,
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
    assert player["source_parent_team_ids"] == "137"
    assert player["source_parent_team_id_mismatch"] is False


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


def test_40man_membership_treats_parent_team_mismatch_as_diagnostic_only() -> None:
    payload = _payload()
    payload["roster"][0]["parentTeamId"] = 999  # type: ignore[index]
    membership = project_team_40man_membership_payload(
        payload,
        team_id=137,
        season=2022,
        as_of_date=date(2022, 10, 15),
    )
    player = membership.filter(membership["player_id"] == 1).row(0, named=True)
    assert player["on_40man"] is True
    assert player["team_id"] == 137
    assert player["source_parent_team_ids"] == "999"
    assert player["source_parent_team_id_mismatch"] is True


def test_project_team_roster_payload_rejects_unknown_roster_type() -> None:
    with pytest.raises(ValueError, match="unsupported roster type"):
        project_team_roster_payload(
            _payload(),
            team_id=137,
            season=2022,
            as_of_date=date(2022, 10, 15),
            roster_type="futureRoster",
        )


def test_full_roster_projector_collapses_duplicate_candidate_rows() -> None:
    payload = _payload()
    payload["roster"].append(payload["roster"][0])  # type: ignore[index,union-attr]
    candidates = project_team_full_roster_candidates_payload(
        payload,
        team_id=137,
        season=2024,
        as_of_date=date(2024, 10, 15),
    )
    assert candidates.height == 2
    assert candidates.filter(candidates["player_id"] == 1).item(0, "source_row_count") == 2


def test_full_roster_projector_rejects_duplicate_identity_conflict() -> None:
    payload = _payload()
    payload["roster"].append(  # type: ignore[index,union-attr]
        {
            "person": {"id": 1, "fullName": "Different", "link": "/api/v1/people/1"},
            "status": {"code": "A"},
        }
    )
    with pytest.raises(ValueError, match="duplicate identity conflict"):
        project_team_full_roster_candidates_payload(
            payload,
            team_id=137,
            season=2024,
            as_of_date=date(2024, 10, 15),
        )


def test_roster_fetch_helpers_use_the_matching_projector(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_fetch(*args: object, **kwargs: object) -> tuple[dict[str, object], dict[str, object]]:
        return _payload(), {"requested_url": "test"}

    monkeypatch.setattr(roster_source, "_fetch_roster_payload", fake_fetch)
    forty_man, _ = fetch_team_40man_membership_as_of(
        137, season=2024, as_of_date=date(2024, 10, 15)
    )
    full_roster, _ = fetch_team_full_roster_candidates_as_of(
        137, season=2024, as_of_date=date(2024, 10, 15)
    )
    assert "on_40man" in forty_man.columns
    assert "candidate_organization_id" in full_roster.columns
