from __future__ import annotations

import polars as pl

from universal_baseball.control_validation import match_control_reference_players


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
