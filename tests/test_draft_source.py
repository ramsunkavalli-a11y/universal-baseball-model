import polars as pl

from universal_baseball.draft_source import draft_pedigree_as_of, project_draft_payload


def test_project_draft_payload_uses_structured_fields_only() -> None:
    payload = {
        "drafts": {
            "rounds": [{
                "picks": [{
                    "year": "2023", "pickNumber": 1, "roundPickNumber": 1,
                    "pickRound": "1", "pickValue": "9721000",
                    "signingBonus": "9200000", "isDrafted": True,
                    "blurb": "must not become a model field",
                    "person": {"id": 694973, "fullName": "Paul Skenes"},
                    "school": {"schoolClass": "4YR JR"},
                }]
            }]
        }
    }
    result = project_draft_payload(
        payload, draft_year=2023, source_snapshot_id="statsapi:draft:2023"
    )
    assert result.height == 1
    assert result.row(0, named=True)["signing_bonus_dollars"] == 9_200_000
    assert "blurb" not in result.columns


def test_project_draft_payload_keeps_missing_bonus_explicit() -> None:
    payload = {
        "drafts": {"rounds": [{"picks": [{
            "year": "2010", "pickNumber": 25, "pickRound": "1",
            "person": {"id": 10, "fullName": "Player"},
        }]}]}
    }
    result = project_draft_payload(
        payload, draft_year=2010, source_snapshot_id="statsapi:draft:2010"
    )
    assert result.row(0, named=True)["signing_bonus_dollars"] is None


def test_draft_pedigree_is_cutoff_safe_and_era_neutral() -> None:
    history = pl.DataFrame(
        {
            "draft_year": [2018, 2018, 2020], "player_id": [1, 2, 1],
            "pick_number": [1, 100, 2], "signing_bonus_dollars": [10, 1, 20],
            "school_class": ["HS", "4YR JR", "4YR JR"],
            "drafted": [True, True, True],
        }
    )
    old = draft_pedigree_as_of(history, 2018)
    assert old.height == 2
    assert old.filter(pl.col("player_id") == 1).item(0, "high_school_draftee")
    assert old.filter(pl.col("player_id") == 1).item(0, "draft_pick_quality") == 1.0
    new = draft_pedigree_as_of(history, 2020)
    assert not new.filter(pl.col("player_id") == 1).item(0, "high_school_draftee")
