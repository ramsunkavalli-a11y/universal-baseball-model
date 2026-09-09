from __future__ import annotations

from datetime import date

from universal_baseball.people_control_source import project_people_control_payload


AS_OF = date(2024, 10, 15)


def _payload() -> dict[str, object]:
    return {
        "people": [
            {
                "id": 10,
                "fullName": "Player Ten",
                "birthDate": "2000-01-02",
                "currentTeam": {"id": 555, "parentOrgId": 135},
                "rosterEntries": [
                    {
                        "team": {"id": 135},
                        "status": {"code": "A", "description": "Active"},
                        "startDate": "2024-03-20",
                        "isActiveFortyMan": True,
                    }
                ],
                "transactions": [
                    {
                        "id": 1,
                        "date": "2019-06-01",
                        "effectiveDate": "2019-06-01",
                        "typeCode": "SGN",
                        "typeDesc": "Signed",
                        "description": "Signed a professional contract.",
                    },
                    {
                        "id": 2,
                        "date": "2025-01-01",
                        "effectiveDate": "2025-01-01",
                        "typeCode": "OPT",
                        "typeDesc": "Optioned",
                        "description": "Optioned.",
                    },
                ],
            }
        ]
    }


def test_people_control_projection_combines_evidence_and_clips_future_events() -> None:
    result = project_people_control_payload(
        _payload(), as_of_date=AS_OF, source_snapshot_id="statsapi:test"
    )
    person = result.people.row(0, named=True)
    assert person["birth_date"] == date(2000, 1, 2)
    assert person["current_team_id"] == 555
    assert person["current_team_parent_org_id"] == 135
    assert person["first_pro_contract_date"] == date(2019, 6, 1)
    assert result.roster_entries.height == 1
    assert result.transactions.get_column("transaction_id").to_list() == [1]


def test_future_resolution_is_treated_as_unresolved_at_cutoff() -> None:
    payload = _payload()
    transaction = payload["people"][0]["transactions"][0]  # type: ignore[index]
    transaction["resolutionDate"] = "2025-01-01"  # type: ignore[index]
    result = project_people_control_payload(
        payload, as_of_date=AS_OF, source_snapshot_id="statsapi:test"
    )
    assert result.transactions.item(0, "resolution_date") is None
