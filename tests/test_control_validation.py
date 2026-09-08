from __future__ import annotations

import polars as pl

from datetime import date

from universal_baseball.control_validation import (
    confirm_name_matches_with_current_roster_entries,
    match_control_reference_players,
)
from universal_baseball.roster_entry_source import ROSTER_ENTRY_SCHEMA


def test_validation_match_prefers_stable_id_then_allows_labeled_name_match() -> None:
    references = pl.DataFrame(
        {"fangraphs_id": ["10", "20", "30"], "player_name": ["Stable", "Ramón Name", "Missing"]}
    )
    candidates = pl.DataFrame(
        {"player_id": [101, 202], "player_name": ["Stable Changed", "Ramon Name"]}
    )
    crosswalk = pl.DataFrame(
        {
            "fangraphs_id": ["10", "20", "30"],
            "player_id": [101, None, None],
            "crosswalk_status": ["matched_unique", "missing_mlbam", "missing_mlbam"],
        }
    )
    result = match_control_reference_players(references, candidates, crosswalk)
    by_id = {row["fangraphs_id"]: row for row in result.iter_rows(named=True)}
    assert by_id["10"]["match_status"] == "matched_stable_id"
    assert by_id["20"]["match_status"] == "matched_validation_only"
    assert by_id["20"]["player_id"] == 202
    assert by_id["30"]["match_status"] == "unmatched"


def test_validation_match_does_not_choose_duplicate_normalized_name() -> None:
    references = pl.DataFrame({"fangraphs_id": ["10"], "player_name": ["Same Name"]})
    candidates = pl.DataFrame(
        {"player_id": [101, 102], "player_name": ["Same Name", "Same-Name"]}
    )
    crosswalk = pl.DataFrame(
        {"fangraphs_id": ["10"], "player_id": [None], "crosswalk_status": ["missing_mlbam"]}
    )
    result = match_control_reference_players(references, candidates, crosswalk)
    assert result.item(0, "match_status") == "ambiguous_name"


def test_name_match_requires_current_roster_entry_for_expected_org() -> None:
    matches = pl.DataFrame(
        [
            {
                "fangraphs_id": "10",
                "reference_player_name": "New Player",
                "player_id": 101,
                "statsapi_player_name": "New Player",
                "match_method": "unique_normalized_name_validation_only",
                "match_status": "matched_validation_only",
            }
        ]
    )
    entries = pl.DataFrame(
        [
            {
                "as_of_date": date(2026, 9, 8),
                "player_id": 101,
                "player_name": "New Player",
                "team_id": 999,
                "parent_org_id": 135,
                "status_code": "A",
                "status_description": "Active",
                "start_date": date(2026, 4, 1),
                "end_date": None,
                "is_active_40man": False,
                "source_snapshot_id": "statsapi:people",
            }
        ],
        schema=ROSTER_ENTRY_SCHEMA,
    )

    result = confirm_name_matches_with_current_roster_entries(
        matches, entries, expected_team_id=135, as_of_date=date(2026, 9, 8)
    )

    assert result.item(0, "match_status") == "matched_official_roster_confirmed_name"
