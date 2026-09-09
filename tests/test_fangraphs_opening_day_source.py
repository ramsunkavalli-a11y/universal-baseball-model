import json

import pytest

from universal_baseball.fangraphs_opening_day_source import (
    NEXT_DATA_PREFIX,
    extract_next_data_document,
    project_opening_day_control_baseline,
)


def _document(rows):
    return {
        "props": {
            "pageProps": {
                "dehydratedState": {
                    "queries": [
                        {
                            "queryKey": [
                                "roster-resource/opening-day-tracker/data",
                                {"season": 2025, "loaddate": "test"},
                            ],
                            "state": {"data": rows},
                        }
                    ]
                }
            }
        }
    }


def _row(**overrides):
    row = {
        "season": 2025,
        "xMLBAMID": 660644,
        "playerId": "20536",
        "playerName": "Vidal Brujan",
        "team": "CHC",
        "playerTeamId": 17,
        "servicetime": "2.014",
        "options": "0",
        "is40Man": "Y",
        "status": "10IL",
        "projectedOpeningDayRole": "10-Day IL",
    }
    row.update(overrides)
    return row


def test_extract_and_project_opening_day_control_baseline() -> None:
    html = NEXT_DATA_PREFIX + json.dumps(_document([_row()])) + "</script>"
    result = project_opening_day_control_baseline(
        extract_next_data_document(html), season=2025, source_snapshot_id="fg:test"
    ).row(0, named=True)
    assert result["player_id"] == 660644
    assert result["service_days"] == 358
    assert result["options_remaining"] == 0
    assert result["on_40man"] is True


def test_duplicate_role_rows_collapse_when_control_values_agree() -> None:
    frame = project_opening_day_control_baseline(
        _document([_row(), _row(projectedOpeningDayRole="Triple-A")]),
        season=2025,
        source_snapshot_id="fg:test",
    )
    assert frame.height == 1
    assert frame.item(0, "projected_opening_day_role") == "10-Day IL,Triple-A"


def test_conflicting_duplicate_control_rows_fail() -> None:
    with pytest.raises(ValueError, match="conflicting duplicate"):
        project_opening_day_control_baseline(
            _document([_row(), _row(servicetime="3.000")]),
            season=2025,
            source_snapshot_id="fg:test",
        )


def test_rule5_reference_is_not_treated_as_an_option_count() -> None:
    row = project_opening_day_control_baseline(
        _document([_row(options="Dec'26")]),
        season=2025,
        source_snapshot_id="fg:test",
    ).row(0, named=True)
    assert row["options_remaining"] is None
    assert row["rule5_status"] == "rule5_not_yet_eligible"
    assert row["rule5_eligibility_year"] == 2026
