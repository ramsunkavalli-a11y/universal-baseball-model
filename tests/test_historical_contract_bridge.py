import polars as pl

from universal_baseball.fangraphs_opening_day_source import OPENING_DAY_CONTROL_SCHEMA
from universal_baseball.historical_contract_bridge import (
    _cots_service_days,
    match_cots_players_to_opening_day,
    parse_cots_team_csv,
)


CSV = """,Player,Pos.,Year,Rd,Pick,Age,MLS,Opts left 1/25,Agent,,Length / Total Value,,Projected,,,,
,,,,,,7/1/25,1/25,,,,,,2025,2026,2027,2028,2029
,,,,,,,,,,,,,,,,,
,\"Trout, Mike\",rf,2009,1,25,33,13.070,2 / 3,Landis,,12 y/$426.5M (19-30),,\"$37,116,667\",$37.12,$37.12,$37.12,$37.12
,\"Ward, Taylor\",lf,2015,1,26,31,4.164,1 / 3,Wasserman,,1 y/$7.825M (25),,\"$7,825,000\",A4,FA,,
,Estimated Player Benefits,,,,,,,,,,,,,$17,000,000,$17.50
"""


def test_cots_numeric_service_restores_trailing_zeroes() -> None:
    assert _cots_service_days("8.16") == 8 * 172 + 160
    assert _cots_service_days("0.17") == 170


def test_parse_cots_team_csv_preserves_amounts_and_states() -> None:
    players, terms = parse_cots_team_csv(
        CSV, season=2025, team_abbreviation="LAA", source_snapshot_id="cots:test"
    )
    assert players.height == 2
    trout = players.filter(pl.col("player_name") == "Mike Trout").row(0, named=True)
    assert trout["service_days"] == 13 * 172 + 70
    assert trout["options_remaining"] == 2
    trout_terms = terms.filter(pl.col("source_record_id") == trout["source_record_id"])
    assert trout_terms.get_column("amount_dollars").to_list()[:2] == [37_116_667, 37_120_000]
    ward = players.filter(pl.col("player_name") == "Taylor Ward").row(0, named=True)
    states = terms.filter(pl.col("source_record_id") == ward["source_record_id"]).get_column(
        "control_state"
    ).to_list()
    assert states[1:3] == ["a4", "free_agent"]


def test_identity_gate_requires_exact_service() -> None:
    players, _ = parse_cots_team_csv(
        CSV, season=2025, team_abbreviation="LAA", source_snapshot_id="cots:test"
    )
    opening = pl.DataFrame(
        [
            {
                "season": 2025,
                "player_id": 545361,
                "fangraphs_id": "10155",
                "player_name": "Mike Trout",
                "team_abbreviation": "LAA",
                "fangraphs_team_id": 1,
                "service_time": "13.070",
                "service_days": 2306,
                "options_remaining": 2,
                "rule5_status": "",
                "rule5_eligibility_year": None,
                "on_40man": True,
                "roster_status": "ACTIVE",
                "projected_opening_day_role": "Lineup Regular",
                "source_snapshot_id": "fg:test",
            },
            {
                "season": 2025,
                "player_id": 621493,
                "fangraphs_id": "13172",
                "player_name": "Taylor Ward",
                "team_abbreviation": "LAA",
                "fangraphs_team_id": 1,
                "service_time": "4.163",
                "service_days": 851,
                "options_remaining": 1,
                "rule5_status": "",
                "rule5_eligibility_year": None,
                "on_40man": True,
                "roster_status": "ACTIVE",
                "projected_opening_day_role": "Lineup Regular",
                "source_snapshot_id": "fg:test",
            },
        ],
        schema=OPENING_DAY_CONTROL_SCHEMA,
    )
    result = match_cots_players_to_opening_day(players, opening)
    assert result.filter(pl.col("player_id") == 545361).height == 1
    assert result.filter(pl.col("match_status") == "review_service_disagreement").height == 1
