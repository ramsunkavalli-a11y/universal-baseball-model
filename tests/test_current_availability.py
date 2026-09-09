from datetime import date

import polars as pl

from universal_baseball.current_availability import (
    apply_current_availability_sensitivity,
    project_current_affiliated_status_payload,
)


def test_status_projection_separates_season_out_from_unknown_return() -> None:
    payload = {
        "roster": [
            {
                "person": {"id": 1},
                "status": {"code": "ILF", "description": "Full Season"},
            },
            {
                "person": {"id": 2},
                "status": {"code": "D10", "description": "Injured 10-Day"},
            },
            {
                "person": {"id": 3},
                "status": {"code": "A", "description": "Active"},
            },
        ]
    }
    result = project_current_affiliated_status_payload(
        payload, organization_id=135, as_of_date=date(2026, 9, 8)
    )
    assert result.filter(pl.col("player_id") == 1).item(
        0, "availability_category"
    ) == "official_season_out"
    assert result.filter(pl.col("player_id") == 2).item(
        0, "availability_category"
    ) == "injured_return_date_unresolved"


def test_availability_zeroes_only_proven_out_and_bounds_unresolved_injury() -> None:
    status_rows = []
    for player_id, code in ((1, "ILF"), (2, "D10"), (3, "A")):
        status_rows.append(
            {
                "person": {"id": player_id},
                "status": {"code": code, "description": code},
            }
        )
    statuses = project_current_affiliated_status_payload(
        {"roster": status_rows},
        organization_id=135,
        as_of_date=date(2026, 9, 8),
    )
    result = apply_current_availability_sensitivity(
        pl.DataFrame(
            {
                "player_id": [1, 2, 3],
                "organization_id": [135, 135, 135],
                "projected_remaining_war_mean": [1.0, 2.0, -1.0],
            }
        ),
        statuses,
    )
    assert result.filter(pl.col("player_id") == 1).item(
        0, "projected_remaining_war_mean"
    ) == 0.0
    injured = result.filter(pl.col("player_id") == 2)
    assert injured.item(0, "projected_remaining_war_mean") == 2.0
    assert injured.item(0, "projected_remaining_war_lower") == 0.0
    assert injured.item(0, "projected_remaining_war_upper") == 2.0
    active = result.filter(pl.col("player_id") == 3)
    assert active.item(0, "projected_remaining_war_lower") == -1.0
    assert active.item(0, "projected_remaining_war_upper") == -1.0
