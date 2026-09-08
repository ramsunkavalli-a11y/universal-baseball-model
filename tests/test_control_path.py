from datetime import date

import polars as pl

from universal_baseball.control_path import project_future_control_path


def test_future_path_applies_super_two_then_contract_option() -> None:
    players = pl.DataFrame(
        {
            "player_id": [1],
            "organization_id": [135],
            "service_days": [2 * 172 + 10],
            "current_service_days": [100],
            "super_two_selected": [True],
        }
    )
    contracts = pl.DataFrame(
        {
            "player_id": [1],
            "organization_id": [135],
            "payroll_year": [2028],
            "amount_dollars": [10_000_000],
            "term_label": ["salary_or_option_amount"],
            "clause_types": ["club_option"],
        }
    )

    result = project_future_control_path(
        players,
        contracts,
        as_of_date=date(2026, 9, 8),
        through_year=2028,
    )

    assert result.filter(pl.col("control_year") == 2027).item(0, "control_status") == (
        "super_two_eligible"
    )
    assert result.filter(pl.col("control_year") == 2028).item(0, "control_status") == (
        "club_option"
    )


def test_future_path_does_not_emit_unknown_service_or_owner() -> None:
    players = pl.DataFrame(
        {
            "player_id": [1],
            "organization_id": [None],
            "service_days": [None],
            "current_service_days": [0],
            "super_two_selected": [False],
        }
    )
    contracts = pl.DataFrame(
        schema={
            "player_id": pl.Int64,
            "organization_id": pl.Int64,
            "payroll_year": pl.Int64,
            "amount_dollars": pl.Int64,
            "term_label": pl.String,
            "clause_types": pl.String,
        }
    )

    result = project_future_control_path(
        players,
        contracts,
        as_of_date=date(2026, 9, 8),
        through_year=2028,
    )

    assert result.is_empty()
