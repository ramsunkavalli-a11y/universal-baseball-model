from __future__ import annotations

import pytest

from universal_baseball.player_value_baserunning_sources import (
    audit_mlb_baserunning_splits,
)


def _split(**stat):
    return {"player": {"id": 1, "fullName": "Example"}, "stat": stat}


def test_mlb_baserunning_source_audit_accepts_complete_counts() -> None:
    result = audit_mlb_baserunning_splits(
        [
            _split(
                stolenBases=8,
                caughtStealing=2,
                groundIntoDoublePlay=4,
                gidpOpp=23,
            ),
            _split(
                stolenBases="0",
                caughtStealing="0",
                groundIntoDoublePlay="0",
                gidpOpp="0",
            ),
        ]
    )

    assert result["row_count"] == 2
    assert result["fields"]["stolenBases"]["complete"] is True
    assert result["fields"]["gidpOpp"]["complete"] is True
    assert result["gidp_opportunity_identity"] == {
        "checked_rows": 2,
        "violation_rows": 0,
    }


def test_mlb_baserunning_source_audit_reports_missing_gidp_opportunity() -> None:
    result = audit_mlb_baserunning_splits(
        [
            _split(stolenBases=8, caughtStealing=2, groundIntoDoublePlay=4),
            _split(stolenBases=1, caughtStealing=0, groundIntoDoublePlay=1),
        ]
    )

    assert result["fields"]["gidpOpp"] == {
        "present_rows": 0,
        "nonnull_rows": 0,
        "missing_rows": 2,
        "complete": False,
    }
    assert result["gidp_opportunity_identity"]["checked_rows"] == 0


def test_mlb_baserunning_source_audit_rejects_gidp_above_opportunities() -> None:
    with pytest.raises(ValueError, match="groundIntoDoublePlay <= gidpOpp"):
        audit_mlb_baserunning_splits(
            [
                _split(
                    stolenBases=2,
                    caughtStealing=1,
                    groundIntoDoublePlay=5,
                    gidpOpp=4,
                )
            ]
        )


def test_mlb_baserunning_source_audit_rejects_negative_or_fractional_counts() -> None:
    with pytest.raises(ValueError, match="invalid stolenBases"):
        audit_mlb_baserunning_splits(
            [
                _split(
                    stolenBases=-1,
                    caughtStealing=0,
                    groundIntoDoublePlay=0,
                    gidpOpp=0,
                )
            ]
        )

    with pytest.raises(ValueError, match="invalid caughtStealing"):
        audit_mlb_baserunning_splits(
            [
                _split(
                    stolenBases=1,
                    caughtStealing=0.5,
                    groundIntoDoublePlay=0,
                    gidpOpp=0,
                )
            ]
        )
