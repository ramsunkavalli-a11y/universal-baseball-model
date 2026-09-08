from __future__ import annotations

import pytest

from scripts.audit_affiliated_full_roster_source import _profile_ids


def test_ids_extracts_unique_player_ids() -> None:
    assert _profile_ids([{"person": {"id": 2}}, {"person": {"id": 1}}]) == (
        {1, 2},
        0,
    )


def test_ids_reports_duplicate_source_rows_without_changing_membership() -> None:
    assert _profile_ids([{"person": {"id": 1}}, {"person": {"id": 1}}]) == (
        {1},
        1,
    )


def test_ids_rejects_missing_identity() -> None:
    with pytest.raises(ValueError, match="person.id"):
        _profile_ids([{"person": {}}])
