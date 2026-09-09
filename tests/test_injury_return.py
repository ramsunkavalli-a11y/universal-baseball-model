from datetime import date

import polars as pl

from universal_baseball.injury_return import (
    build_injury_return_cohort,
    elapsed_days_band,
    fit_injury_return_references,
    normalize_injury_transaction_payload,
)
from universal_baseball.rights_transactions import project_transaction_payload


def _row(transaction_id: int, player_id: int, effective: str, description: str):
    return {
        "id": transaction_id,
        "person": {"id": player_id, "fullName": f"Player {player_id}"},
        "date": effective,
        "effectiveDate": effective,
        "typeCode": "SC",
        "typeDesc": "Status Change",
        "description": description,
    }


def test_return_cohort_replays_cutoff_state_and_later_activation() -> None:
    payload = {
        "transactions": [
            _row(1, 10, "2025-08-20", "Team placed P Player 10 on the 15-day injured list."),
            _row(2, 10, "2025-09-18", "Team activated P Player 10 from the 15-day injured list."),
            _row(3, 20, "2025-07-01", "Team placed P Player 20 on the 10-day injured list."),
            _row(4, 20, "2025-08-01", "Team transferred P Player 20 to the 60-day injured list."),
            _row(5, 30, "2025-08-01", "Team placed P Player 30 on the 10-day injured list."),
            _row(6, 30, "2025-09-01", "Team activated P Player 30 from the 10-day injured list."),
        ]
    }
    transactions = project_transaction_payload(
        payload, as_of_date=date(2025, 10, 1), source_snapshot_id="mlb:test"
    )
    result = build_injury_return_cohort(
        transactions,
        cutoff_date=date(2025, 9, 8),
        season_end_date=date(2025, 9, 28),
    )
    assert result.get_column("player_id").to_list() == [10, 20]
    returned = result.filter(pl.col("player_id") == 10)
    assert returned.item(0, "days_on_il_at_cutoff") == 19
    assert returned.item(0, "days_until_activation") == 10
    assert returned.item(0, "remaining_season_availability_fraction") == 0.55
    stayed_out = result.filter(pl.col("player_id") == 20)
    assert stayed_out.item(0, "injury_list_type") == "60_day"
    assert stayed_out.item(0, "returned_by_season_end") is False


def test_reference_fit_shrinks_sparse_cells_to_population() -> None:
    transactions = project_transaction_payload(
        {
            "transactions": [
                _row(1, 1, "2025-09-01", "Team placed P One on the 10-day injured list."),
                _row(2, 1, "2025-09-18", "Team activated P One from the 10-day injured list."),
                _row(3, 2, "2025-08-01", "Team placed P Two on the 60-day injured list."),
            ]
        },
        as_of_date=date(2025, 10, 1),
        source_snapshot_id="mlb:test",
    )
    cohort = build_injury_return_cohort(
        transactions,
        cutoff_date=date(2025, 9, 8),
        season_end_date=date(2025, 9, 28),
    )
    fit = fit_injury_return_references(cohort, prior_players=2.0)
    assert fit.references.height == 3
    cell = fit.references.filter(pl.col("injury_list_type") == "10_day")
    assert 0.5 < cell.item(0, "return_probability") < 1.0
    assert elapsed_days_band(60) == "60_plus"


def test_normalization_keeps_only_identifiable_injury_events() -> None:
    payload, metrics = normalize_injury_transaction_payload(
        {
            "transactions": [
                _row(1, 1, "2025-08-01", "Team placed P One on the 15-day injured list."),
                {**_row(2, 2, "2025-08-02", "Team activated P Two from the 15-day injured list."), "effectiveDate": "2026-04-01"},
                _row(3, 3, "2025-08-03", "Team optioned Player 3."),
                {**_row(1, 1, "2025-08-04", "Team placed P One on the 15-day injured list."), "effectiveDate": "2025-08-01"},
            ]
        },
        season=2025,
    )
    assert len(payload["transactions"]) == 2
    assert payload["transactions"][1]["effectiveDate"] == "2025-08-02"
    assert metrics["cross_year_effective_date_corrections"] == 1
    assert metrics["duplicate_event_rows_removed"] == 1
