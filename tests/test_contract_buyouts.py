import polars as pl

from universal_baseball.contract_buyouts import link_option_buyouts


def test_option_buyouts_link_exactly_within_same_payroll_source() -> None:
    terms = pl.DataFrame(
        {
            "team_name": ["Padres"],
            "player_name": ["Example Player"],
            "player_id": [123],
            "organization_id": [135],
            "overlay_status": ["accepted_contract_overlay"],
        }
    )
    payments = pl.DataFrame(
        {
            "team_name": ["Padres", "Padres"],
            "organization_id": [135, 135],
            "payment_year": [2027, 2026],
            "description": [
                "$ due for potential buyout of Example Player",
                "$ due for buyout of Former Player",
            ],
            "amount_dollars": [2_000_000, 1_000_000],
            "payment_type": ["buyout", "buyout"],
            "is_contingent": [True, False],
            "source_snapshot_id": ["fg:test", "fg:test"],
        }
    )
    result = link_option_buyouts(terms, payments)
    assert result.coverage["potential_buyout_rows"] == 1
    assert result.coverage["linked_buyout_rows"] == 1
    assert result.links.item(0, "player_id") == 123
    assert result.links.item(0, "buyout_dollars") == 2_000_000
    assert result.links.item(0, "buyout_link_status") == (
        "matched_exact_within_payroll"
    )
