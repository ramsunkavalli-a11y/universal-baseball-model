from __future__ import annotations

from datetime import date

import pytest

from universal_baseball.rights_transactions import (
    RIGHTS_TRANSACTION_SCHEMA,
    project_transaction_payload,
)


CUTOFF = date(2024, 10, 15)


def _row(**updates: object) -> dict[str, object]:
    row: dict[str, object] = {
        "id": 739233,
        "person": {"id": 658431, "fullName": "Adonis Medina"},
        "toTeam": {"id": 120, "name": "Washington Nationals"},
        "date": "2024-02-02",
        "effectiveDate": "2024-02-02",
        "resolutionDate": "2024-02-02",
        "typeCode": "SFA",
        "typeDesc": "Signed as Free Agent",
        "description": "Signed to a minor league contract.",
    }
    row.update(updates)
    return row


def test_project_transaction_payload_preserves_event_without_rights_inference() -> None:
    result = project_transaction_payload(
        {"transactions": [_row()]},
        as_of_date=CUTOFF,
        source_snapshot_id="transactions:658431:through:2024-10-15",
    )
    assert result.schema == RIGHTS_TRANSACTION_SCHEMA
    event = result.row(0, named=True)
    assert event["player_id"] == 658431
    assert event["type_code"] == "SFA"
    assert event["to_team_id"] == 120
    assert "rights_state" not in result.columns


def test_transaction_projection_rejects_future_effective_event() -> None:
    with pytest.raises(ValueError, match="crosses as-of cutoff"):
        project_transaction_payload(
            {"transactions": [_row(effectiveDate="2024-10-16")]},
            as_of_date=CUTOFF,
            source_snapshot_id="snapshot",
        )


def test_transaction_projection_rejects_duplicate_ids() -> None:
    with pytest.raises(ValueError, match="duplicate transaction_id"):
        project_transaction_payload(
            {"transactions": [_row(), _row()]},
            as_of_date=CUTOFF,
            source_snapshot_id="snapshot",
        )


def test_transaction_projection_allows_empty_result_with_stable_schema() -> None:
    result = project_transaction_payload(
        {"transactions": []},
        as_of_date=CUTOFF,
        source_snapshot_id="snapshot",
    )
    assert result.is_empty()
    assert result.schema == RIGHTS_TRANSACTION_SCHEMA


def test_transaction_projection_requires_structured_source() -> None:
    with pytest.raises(ValueError, match="transactions list"):
        project_transaction_payload(
            {},
            as_of_date=CUTOFF,
            source_snapshot_id="snapshot",
        )
