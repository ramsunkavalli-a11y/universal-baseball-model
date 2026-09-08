from __future__ import annotations

import polars as pl

from universal_baseball.depth_chart_reference import normalize_fangraphs_depth_chart


def test_depth_chart_normalizes_options_rule5_and_service_reference() -> None:
    sheets = {
        "MLB": pl.DataFrame(
            {
                "PLAYER": ["MLB Player"],
                "Options": ["2"],
                "MLB Service Time": [1.129],
                "HOW ACQUIRED": ["Drafted"],
                "Year": [2021],
                "playerId": ["10"],
            }
        ),
        "Double-A": pl.DataFrame(
            {
                "POSITION PLAYERS": ["Prospect"],
                "Options or R5 Status": ["Dec'27"],
                "MLB Service Time": [None],
                "HOW ACQUIRED": ["Amateur FA"],
                "Year": ["JAN 2023"],
                "playerId": ["sa20"],
            }
        ),
        "Triple-A": pl.DataFrame(
            {
                "PITCHERS": ["Rule Five"],
                "Options or R5 Status": ["R5"],
                "MLB Service Time": [None],
                "HOW ACQUIRED": ["Drafted"],
                "Year": [2020],
                "playerId": ["sa30"],
            }
        ),
    }
    result = normalize_fangraphs_depth_chart(
        sheets, team_name="Padres", season=2026, source_snapshot_id="fg:depth:2026"
    )
    mlb = result.filter(pl.col("fangraphs_id") == "10").row(0, named=True)
    prospect = result.filter(pl.col("fangraphs_id") == "sa20").row(0, named=True)
    rule_five = result.filter(pl.col("fangraphs_id") == "sa30").row(0, named=True)
    assert mlb["reference_options_remaining"] == 2
    assert mlb["reference_service_time"] == "1.129"
    assert prospect["reference_rule5_year"] == 2027
    assert rule_five["reference_rule5_status"] == "rule5_eligible"


def test_depth_chart_rejects_duplicate_stable_ids() -> None:
    sheets = {
        "A": pl.DataFrame({"PLAYER": ["One"], "playerId": ["10"]}),
        "B": pl.DataFrame({"PLAYER": ["Two"], "playerId": ["10"]}),
    }
    try:
        normalize_fangraphs_depth_chart(
            sheets, team_name="Padres", season=2026, source_snapshot_id="fg:test"
        )
    except ValueError as exc:
        assert "duplicate nonblank FanGraphs IDs" in str(exc)
    else:
        raise AssertionError("duplicate FanGraphs ID should fail")
