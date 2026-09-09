from __future__ import annotations

import pytest

from universal_baseball.affiliated_skill_source import project_affiliated_skill_splits


def _split(stat: dict[str, int]) -> dict[str, object]:
    return {
        "player": {"id": 10, "fullName": "Test Player"},
        "sport": {"id": 12},
        "team": {"id": 999},
        "stat": {"age": 23, **stat},
    }


def test_projects_affiliated_hitting_components_without_filling_fields() -> None:
    frame = project_affiliated_skill_splits(
        [_split({
            "plateAppearances": 100, "atBats": 85, "hits": 25, "doubles": 5,
            "triples": 1, "homeRuns": 4, "baseOnBalls": 10,
            "intentionalWalks": 1, "hitByPitch": 2, "strikeOuts": 20,
            "sacBunts": 1, "sacFlies": 2, "stolenBases": 3,
            "caughtStealing": 1, "groundIntoDoublePlay": 2,
        })],
        season=2025, stat_group="hitting",
    )
    assert frame.item(0, "level_group") == "AA"
    assert frame.item(0, "plate_appearances") == 100
    assert frame.item(0, "intentional_walks") == 1


def test_projects_affiliated_pitching_components_and_rejects_bad_accounting() -> None:
    stat = {
        "gamesPlayed": 20, "gamesStarted": 10, "battersFaced": 300,
        "strikeOuts": 80, "baseOnBalls": 30, "intentionalWalks": 2,
        "hitBatsmen": 4, "homeRuns": 10,
    }
    frame = project_affiliated_skill_splits(
        [_split(stat)], season=2025, stat_group="pitching"
    )
    assert frame.item(0, "batters_faced") == 300
    bad = dict(stat)
    bad["gamesStarted"] = 21
    with pytest.raises(ValueError, match="accounting"):
        project_affiliated_skill_splits(
            [_split(bad)], season=2025, stat_group="pitching"
        )


def test_missing_affiliated_component_is_not_silently_zeroed() -> None:
    with pytest.raises(ValueError, match="missing sacFlies"):
        project_affiliated_skill_splits(
            [_split({
                "plateAppearances": 1, "atBats": 1, "hits": 0, "doubles": 0,
                "triples": 0, "homeRuns": 0, "baseOnBalls": 0,
                "intentionalWalks": 0, "hitByPitch": 0, "strikeOuts": 1,
                "sacBunts": 0, "stolenBases": 0, "caughtStealing": 0,
                "groundIntoDoublePlay": 0,
            })],
            season=2025, stat_group="hitting",
        )
