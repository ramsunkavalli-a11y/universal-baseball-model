from datetime import date

import polars as pl

from universal_baseball.historical_replay_inputs import (
    build_historical_replay_economics_inputs,
)


def _paths() -> tuple[pl.DataFrame, pl.DataFrame]:
    hitter = pl.DataFrame(
        {
            "player_id": [1, 1, 2, 2, 3, 3],
            "season": [2025, 2026] * 3,
            "expected_war": [1.0, 1.1, 0.5, 0.6, 0.2, 0.3],
        }
    )
    pitcher = pl.DataFrame(
        {
            "player_id": [1, 1],
            "season": [2025, 2026],
            "expected_war": [0.4, 0.5],
        }
    )
    return hitter, pitcher


def _opening() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "player_id": [1, 2],
            "team_abbreviation": ["SDP", "SFG"],
            "service_days": [100, 2 * 172 + 20],
            "source_snapshot_id": ["opening", "opening"],
        }
    )


def _terms() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "player_id": [1, 1],
            "payroll_year": [2025, 2026],
            "accepted_salary_dollars": [5_000_000, None],
            "contract_status": ["guaranteed_contract", "free_agent"],
            "evidence_status": [
                "amount_within_explicit_guaranteed_range",
                "explicit_free_agent",
            ],
            "review_reason": ["", ""],
            "source_snapshot_id": ["terms", "terms"],
        }
    )


def test_historical_join_combines_two_way_war_and_contract_control() -> None:
    hitter, pitcher = _paths()
    result = build_historical_replay_economics_inputs(
        hitter,
        pitcher,
        _opening(),
        _terms(),
        as_of_date=date(2025, 3, 27),
        projection_source_id="projection",
    )

    player_one = result.annual_inputs.filter(pl.col("player_id") == 1).sort("season")
    assert player_one.get_column("projected_war_mean").to_list() == [1.4, 1.6]
    assert player_one.get_column("control_status").to_list() == [
        "guaranteed_contract",
        "free_agent",
    ]
    assert player_one.item(0, "known_salary_dollars") == 5_000_000


def test_historical_join_fails_closed_on_super_two_and_missing_owner() -> None:
    hitter, pitcher = _paths()
    result = build_historical_replay_economics_inputs(
        hitter,
        pitcher,
        _opening(),
        _terms(),
        as_of_date=date(2025, 3, 27),
        projection_source_id="projection",
    )

    player_two = result.annual_inputs.filter(pl.col("player_id") == 2).sort("season")
    assert player_two.item(0, "control_status") == "super_two_candidate"
    assert player_two.item(0, "contract_structure_review_reason") == (
        "historical_super_two_status_unresolved"
    )
    assert player_two.item(1, "control_status") == "arbitration_eligible"
    assert result.coverage["projection_rows_without_opening_owner"] == 2


def test_historical_join_rejects_unknown_team() -> None:
    hitter, pitcher = _paths()
    opening = _opening().with_columns(
        pl.when(pl.col("player_id") == 1)
        .then(pl.lit("XXX"))
        .otherwise(pl.col("team_abbreviation"))
        .alias("team_abbreviation")
    )
    try:
        build_historical_replay_economics_inputs(
            hitter,
            pitcher,
            opening,
            _terms(),
            as_of_date=date(2025, 3, 27),
            projection_source_id="projection",
        )
    except ValueError as exc:
        assert "unknown teams" in str(exc)
    else:
        raise AssertionError("unknown historical teams must fail closed")
