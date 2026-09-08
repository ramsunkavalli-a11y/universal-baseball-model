from __future__ import annotations

import polars as pl

from universal_baseball.contract_overlay import build_contract_overlay
from universal_baseball.contract_terms import normalize_fangraphs_payroll


def _payroll():
    def sheet(name: str, player_id: str, contract: str) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "Player": [name],
                "Service Time": ["2.000"],
                "Contract": [contract],
                "AAV": ["$10,000,000"],
                "2026": ["$8,000,000"],
                "2027": ["$9,000,000"],
                "playerId": [player_id],
            }
        )

    return normalize_fangraphs_payroll(
        {
            "Guaranteed": sheet("Stable", "10", "2 yr, $17M, 2027 club option"),
            "Eligible For Arb": sheet("Review", "20", "1 yr, $8M"),
            "Not Yet Eligible For Arb": sheet("Third", "30", "1 yr, $8M"),
            "No Longer On 40-Man Roster": sheet("Fourth", "40", "1 yr, $8M"),
        },
        team_name="Padres",
        season=2026,
        source_snapshot_id="fg:test",
    )


def test_contract_overlay_accepts_stable_identity_and_keeps_clauses() -> None:
    matches = pl.DataFrame(
        {
            "fangraphs_id": ["10", "20", "30", "40"],
            "player_id": [101, 202, None, 404],
            "match_status": [
                "matched_stable_id",
                "matched_validation_only",
                "unmatched",
                "stable_id_outside_statsapi_candidates",
            ],
        }
    )
    result = build_contract_overlay(_payroll(), matches)
    stable = result.players.filter(pl.col("fangraphs_id") == "10").row(0, named=True)
    review = result.players.filter(pl.col("fangraphs_id") == "20").row(0, named=True)
    outside = result.players.filter(pl.col("fangraphs_id") == "40").row(0, named=True)
    stable_2027 = result.year_terms.filter(
        (pl.col("fangraphs_id") == "10") & (pl.col("payroll_year") == 2027)
    ).row(0, named=True)
    assert stable["overlay_status"] == "accepted_contract_overlay"
    assert stable["team_name"] == "Padres"
    assert review["overlay_status"] == "review_identity_before_overlay"
    assert outside["overlay_status"] == "accepted_contract_overlay"
    assert stable_2027["clause_types"] == "club_option"
    assert stable_2027["team_name"] == "Padres"
    assert result.unresolved_players.height == 2
