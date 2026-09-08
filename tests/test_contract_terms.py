from __future__ import annotations

import polars as pl

from universal_baseball.contract_terms import normalize_fangraphs_payroll


def _player_sheet(
    player: str = "Player One",
    player_id: str = "10",
    contract: str = "3 yr, $30M (2026-28), 2027-28 player options",
) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "Player": [player],
            "Service Time": [2.004],
            "Contract": [contract],
            "Info": [None],
            "AAV": ["$10,000,000"],
            "2026": ["$8,000,000"],
            "2027": ["ARB 1"],
            "2028": ["FREE AGENT"],
            "playerId": [player_id],
        }
    )


def _sheets() -> dict[str, pl.DataFrame]:
    base = _player_sheet()
    return {
        "Guaranteed": base,
        "Eligible For Arb": _player_sheet("Player Two", "20", "1 yr, $2M (2026)"),
        "Not Yet Eligible For Arb": _player_sheet("Player Three", "30", "1 yr, $1M (2026)"),
        "No Longer On 40-Man Roster": _player_sheet("Player Four", "40", "1 yr, $1M (2026)"),
        "Other Payments": pl.DataFrame(
            {
                "Description": ["$ due for potential buyout", "$ paid by old team"],
                "2026": ["$500,000", "-$2,000,000"],
            }
        ),
    }


def test_payroll_normalizer_separates_contract_evidence_from_cba_reference() -> None:
    result = normalize_fangraphs_payroll(
        _sheets(), team_name="Padres", season=2026, source_snapshot_id="fg:padres:2026"
    )
    player = result.players.filter(pl.col("fangraphs_id") == "10").row(0, named=True)
    assert player["aav_dollars"] == 10_000_000
    assert player["reference_service_time"] == "2.004"
    assert result.year_terms.filter(pl.col("fangraphs_id") == "10").get_column(
        "term_label"
    ).to_list() == ["salary_or_option_amount", "arbitration_1", "free_agent"]


def test_explicit_option_range_becomes_structured_clause() -> None:
    result = normalize_fangraphs_payroll(
        _sheets(), team_name="Padres", season=2026, source_snapshot_id="fg:padres:2026"
    )
    clause = result.clauses.filter(pl.col("fangraphs_id") == "10").row(0, named=True)
    assert clause["clause_type"] == "player_option"
    assert clause["start_year"] == 2027
    assert clause["end_year"] == 2028


def test_other_payments_keep_contingency_and_negative_trade_credit() -> None:
    result = normalize_fangraphs_payroll(
        _sheets(), team_name="Padres", season=2026, source_snapshot_id="fg:padres:2026"
    )
    assert result.other_payments.get_column("amount_dollars").to_list() == [500_000, -2_000_000]
    assert result.other_payments.get_column("payment_type").to_list() == ["buyout", "trade_credit"]
    assert result.other_payments.get_column("is_contingent").to_list() == [True, False]


def test_empty_no_longer_on_40man_section_may_be_omitted() -> None:
    sheets = _sheets()
    del sheets["No Longer On 40-Man Roster"]

    result = normalize_fangraphs_payroll(
        sheets, team_name="Tigers", season=2026, source_snapshot_id="fg:tigers:2026"
    )

    assert result.players.height == 3
    assert "No Longer On 40-Man Roster" not in set(
        result.players.get_column("payroll_section").to_list()
    )


def test_vesting_fallback_and_declined_opt_out_are_structured() -> None:
    sheets = _sheets()
    sheets["Guaranteed"] = pl.concat(
        [
            _player_sheet(
                "Vesting Player",
                "50",
                "3 yr, $37M (2026-28), 2029 vesting option; $9M club option if option doesn't vest",
            ),
            _player_sheet(
                "Declined Player",
                "60",
                "3 yr, $49.5M (2025-27; 2026 opt out declined)",
            ),
        ]
    )

    result = normalize_fangraphs_payroll(
        sheets, team_name="Test", season=2026, source_snapshot_id="fg:test:2026"
    )

    by_player = {
        row["player_name"]: row["clause_type"]
        for row in result.clauses.iter_rows(named=True)
    }
    assert result.players.filter(
        pl.col("clause_parse_status") == "review_unparsed_clause"
    ).is_empty()
    assert set(
        result.clauses.filter(pl.col("player_name") == "Vesting Player").get_column(
            "clause_type"
        )
    ) == {"vesting_option", "fallback_club_option"}
    assert by_player["Declined Player"] == "declined_opt_out"
