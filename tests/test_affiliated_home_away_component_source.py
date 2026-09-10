from universal_baseball.affiliated_home_away_component_source import (
    project_home_away_payload,
)


def _split(code: str, group: str) -> dict:
    stat = {
        "baseOnBalls": 4, "intentionalWalks": 1, "homeRuns": 2,
        "strikeOuts": 7,
    }
    if group == "hitting":
        stat.update({
            "plateAppearances": 30, "hits": 8, "doubles": 2,
            "triples": 1, "hitByPitch": 1,
        })
    else:
        stat.update({"battersFaced": 35, "hitBatsmen": 1})
    return {
        "split": {"code": code}, "team": {"id": 10},
        "player": {"id": 20}, "stat": stat,
    }


def test_project_home_away_payload_keeps_both_groups_and_splits() -> None:
    payload = {"stats": [
        {
            "group": {"displayName": "hitting"}, "totalSplits": 2,
            "splits": [_split("h", "hitting"), _split("a", "hitting")],
        },
        {
            "group": {"displayName": "pitching"}, "totalSplits": 2,
            "splits": [_split("h", "pitching"), _split("a", "pitching")],
        },
    ]}

    hitters, pitchers = project_home_away_payload(
        payload, season=2024, sport_id=11
    )

    assert hitters.height == pitchers.height == 2
    assert hitters.get_column("split_code").to_list() == ["a", "h"]
    assert hitters.get_column("plate_appearances").sum() == 60
    assert pitchers.get_column("batters_faced").sum() == 70


def test_project_home_away_payload_rejects_truncation() -> None:
    payload = {"stats": [
        {
            "group": {"displayName": "hitting"}, "totalSplits": 3,
            "splits": [_split("h", "hitting"), _split("a", "hitting")],
        },
        {
            "group": {"displayName": "pitching"}, "totalSplits": 2,
            "splits": [_split("h", "pitching"), _split("a", "pitching")],
        },
    ]}
    try:
        project_home_away_payload(payload, season=2024, sport_id=11)
    except ValueError as error:
        assert "truncated" in str(error)
    else:
        raise AssertionError("truncated response should fail")
