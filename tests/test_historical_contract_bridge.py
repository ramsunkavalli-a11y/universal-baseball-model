import polars as pl

from universal_baseball.fangraphs_opening_day_source import OPENING_DAY_CONTROL_SCHEMA
from universal_baseball.historical_contract_bridge import (
    _cots_service_days,
    build_cots_valuation_terms,
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


def test_valuation_gate_separates_guarantees_arbitration_and_free_agency() -> None:
    players, terms = parse_cots_team_csv(
        CSV, season=2025, team_abbreviation="LAA", source_snapshot_id="cots:test"
    )
    identities = pl.DataFrame(
        {
            "source_record_id": players.get_column("source_record_id"),
            "player_id": [545361, 621493],
            "match_status": ["accepted_team_name_exact_service"] * 2,
            "match_method": ["team_normalized_name_plus_exact_service"] * 2,
            "service_day_difference": [0, 0],
        }
    )
    result = build_cots_valuation_terms(players, terms, identities)
    trout_2026 = result.filter(
        (pl.col("player_id") == 545361) & (pl.col("payroll_year") == 2026)
    ).row(0, named=True)
    assert trout_2026["accepted_salary_dollars"] == 37_120_000
    assert trout_2026["contract_status"] == "guaranteed_contract"
    ward = result.filter(pl.col("player_id") == 621493).sort("payroll_year")
    assert ward.get_column("valuation_treatment").to_list()[:3] == [
        "use_known_guaranteed_salary",
        "calculate_arbitration_from_cba_path",
        "end_incumbent_control",
    ]


def test_valuation_gate_blocks_option_amount_and_unresolved_identity() -> None:
    option_csv = CSV.replace(
        "1 y/$7.825M (25)", "1 y/$7.825M (25)+26 cl opt"
    ).replace("A4,FA", "$12.0,FA")
    players, terms = parse_cots_team_csv(
        option_csv, season=2025, team_abbreviation="LAA", source_snapshot_id="cots:test"
    )
    identities = pl.DataFrame(
        {
            "source_record_id": players.get_column("source_record_id"),
            "player_id": [545361, None],
            "match_status": [
                "accepted_team_name_exact_service",
                "review_service_disagreement",
            ],
            "match_method": [
                "team_normalized_name_plus_exact_service",
                "team_normalized_name_only",
            ],
            "service_day_difference": [0, 1],
        }
    )
    result = build_cots_valuation_terms(players, terms, identities)
    ward_2026 = result.filter(
        (pl.col("source_record_id") == players.row(1, named=True)["source_record_id"])
        & (pl.col("payroll_year") == 2026)
    ).row(0, named=True)
    assert ward_2026["accepted_salary_dollars"] is None
    assert ward_2026["evidence_status"] == "blocked_identity_gate"

    identities = identities.with_columns(
        pl.when(pl.col("player_id").is_null()).then(pl.lit(621493)).otherwise(
            pl.col("player_id")
        ).alias("player_id"),
        pl.lit("accepted_team_name_exact_service").alias("match_status"),
    )
    accepted = build_cots_valuation_terms(players, terms, identities)
    option = accepted.filter(
        (pl.col("player_id") == 621493) & (pl.col("payroll_year") == 2026)
    ).row(0, named=True)
    assert option["accepted_salary_dollars"] is None
    assert option["contract_status"] == "option_unresolved"


def test_valuation_gate_accepts_no_slash_guarantee_and_blocks_generic_options() -> None:
    source = CSV.replace(
        "1 y/$7.825M (25)", "1 y$7.825M (25)+26-27 opts"
    ).replace("A4,FA", "$12.0,$13.0")
    players, terms = parse_cots_team_csv(
        source, season=2025, team_abbreviation="LAA", source_snapshot_id="cots:test"
    )
    identities = pl.DataFrame(
        {
            "source_record_id": players.get_column("source_record_id"),
            "player_id": [545361, 621493],
            "match_status": ["accepted_team_name_exact_service"] * 2,
            "match_method": ["team_normalized_name_plus_exact_service"] * 2,
            "service_day_difference": [0, 0],
        }
    )
    result = build_cots_valuation_terms(players, terms, identities).filter(
        pl.col("player_id") == 621493
    )
    assert result.item(0, "accepted_salary_dollars") == 7_825_000
    assert result.item(1, "contract_status") == "option_unresolved"
    assert result.item(2, "contract_status") == "option_unresolved"
