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


def test_historical_return_factor_changes_only_exact_injury_match() -> None:
    statuses = project_current_affiliated_status_payload(
        {
            "roster": [
                {"person": {"id": 1}, "status": {"code": "D15", "description": "IL"}},
                {"person": {"id": 2}, "status": {"code": "D15", "description": "IL"}},
            ]
        },
        organization_id=135,
        as_of_date=date(2026, 9, 8),
    )
    stints = pl.DataFrame(
        {
            "season": [2026], "cutoff_date": [date(2026, 9, 8)],
            "player_id": [1], "player_name": ["One"],
            "injury_list_type": ["15_day"],
            "il_start_date": [date(2026, 8, 20)],
            "days_on_il_at_cutoff": [19],
            "season_end_date": [date(2026, 9, 27)],
            "activation_date": [None], "returned_by_season_end": [False],
            "days_until_activation": [None],
            "remaining_season_availability_fraction": [0.0],
            "source_snapshot_ids": ["mlb:test"],
        }
    )
    references = pl.DataFrame(
        {
            "injury_list_type": ["ALL", "15_day"],
            "elapsed_days_band": ["ALL", "15_29"],
            "reference_level": ["population", "il_type_elapsed_shrunk"],
            "observation_count": [100, 20], "returned_count": [20, 8],
            "return_probability": [0.2, 0.4],
            "mean_remaining_availability_fraction": [0.1, 0.25],
        }
    )
    result = apply_current_availability_sensitivity(
        pl.DataFrame(
            {
                "player_id": [1, 2], "organization_id": [135, 135],
                "projected_remaining_war_mean": [2.0, 2.0],
            }
        ),
        statuses,
        injury_stints=stints,
        return_references=references,
    )
    matched = result.filter(pl.col("player_id") == 1)
    assert matched.item(0, "projected_remaining_war_mean") == 0.5
    assert matched.item(0, "projected_remaining_war_upper") == 2.0
    unmatched = result.filter(pl.col("player_id") == 2)
    assert unmatched.item(0, "projected_remaining_war_mean") == 2.0
