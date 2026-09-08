from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from universal_baseball.team_control import (
    CONTROL_PLAYER_SCHEMA,
    CONTROL_STINT_SCHEMA,
    SEASON_WINDOW_SCHEMA,
    build_team_control_summary,
    calculate_control_years,
)


CUTOFF = date(2025, 9, 28)


def _stints(rows: list[dict[str, object]]) -> pl.DataFrame:
    return pl.DataFrame(rows, schema=CONTROL_STINT_SCHEMA)


def _stint(
    player_id: int,
    state: str,
    start: str,
    end: str,
    *,
    season: int = 2025,
) -> dict[str, object]:
    return {
        "player_id": player_id,
        "season": season,
        "start_date": date.fromisoformat(start),
        "end_date": date.fromisoformat(end),
        "roster_state": state,
        "source_snapshot_id": f"statsapi:{player_id}:{state}",
    }


def _windows() -> pl.DataFrame:
    return pl.DataFrame(
        [{"season": 2025, "start_date": date(2025, 3, 27), "end_date": CUTOFF}],
        schema=SEASON_WINDOW_SCHEMA,
    )


def _players(rows: list[dict[str, object]]) -> pl.DataFrame:
    defaults = {
        "player_name": "Player",
        "birth_date": date(2000, 1, 1),
        "first_pro_contract_date": date(2019, 6, 1),
        "on_40man": False,
        "service_days_before_window": 0,
        "option_years_used_before_window": 0,
        "full_pro_seasons_before_window": 0,
        "history_complete": True,
        "source_snapshot_ids": "statsapi:test",
    }
    return pl.DataFrame([{**defaults, **row} for row in rows], schema=CONTROL_PLAYER_SCHEMA)


def test_service_time_unions_overlaps_subtracts_exclusions_and_caps_at_172() -> None:
    years = calculate_control_years(
        _stints(
            [
                _stint(1, "mlb_active", "2025-03-27", "2025-09-28"),
                _stint(1, "mlb_injured", "2025-05-01", "2025-05-20"),
                _stint(1, "service_excluded", "2025-06-01", "2025-06-10"),
            ]
        ),
        _windows(),
        as_of_date=CUTOFF,
    ).row(0, named=True)
    assert years["service_days"] == 172


def test_option_year_requires_20_days_and_only_counts_once_per_season() -> None:
    years = calculate_control_years(
        _stints(
            [
                _stint(1, "minors_optioned", "2025-04-01", "2025-04-10"),
                _stint(1, "minors_optioned", "2025-05-01", "2025-05-10"),
                _stint(2, "minors_optioned", "2025-04-01", "2025-04-19"),
            ]
        ),
        _windows(),
        as_of_date=CUTOFF,
    )
    assert years.filter(pl.col("player_id") == 1).item(0, "option_year_used") is True
    assert years.filter(pl.col("player_id") == 1).item(0, "optioned_days") == 20
    assert years.filter(pl.col("player_id") == 2).item(0, "option_year_used") is False


def test_full_pro_season_supports_active_plus_injured_rule() -> None:
    years = calculate_control_years(
        _stints(
            [
                _stint(1, "pro_active", "2025-04-01", "2025-04-30"),
                _stint(1, "pro_injured", "2025-05-01", "2025-06-29"),
            ]
        ),
        _windows(),
        as_of_date=CUTOFF,
    ).row(0, named=True)
    assert years["pro_active_days"] == 30
    assert years["pro_active_or_injured_days"] == 90
    assert years["full_pro_season"] is True


def test_summary_calculates_service_options_rule5_and_eligibility() -> None:
    years = calculate_control_years(
        _stints([_stint(1, "mlb_active", "2025-03-27", "2025-06-23")]),
        _windows(),
        as_of_date=CUTOFF,
    )
    summary = build_team_control_summary(
        _players(
            [
                {
                    "player_id": 1,
                    "player_name": "One",
                    "birth_date": date(2000, 1, 1),
                    "first_pro_contract_date": date(2019, 6, 1),
                    "service_days_before_window": 2 * 172,
                    "option_years_used_before_window": 3,
                    "full_pro_seasons_before_window": 4,
                }
            ]
        ),
        years,
        as_of_date=CUTOFF,
        super_two_pool_complete=True,
    ).row(0, named=True)
    assert summary["service_time"] == "2.089"
    assert summary["cba_eligibility_class"] == "super_two_eligible"
    assert summary["option_years_allowed"] == 4
    assert summary["options_remaining"] == 1
    assert summary["rule5_eligibility_year"] == 2022
    assert summary["rule5_status"] == "eligible_next_rule5_draft"


def test_team_only_input_does_not_invent_a_super_two_cutoff() -> None:
    years = calculate_control_years(
        _stints([_stint(1, "mlb_active", "2025-03-27", "2025-06-23")]),
        _windows(),
        as_of_date=CUTOFF,
    )
    result = build_team_control_summary(
        _players([{"player_id": 1, "service_days_before_window": 2 * 172}]),
        years,
        as_of_date=CUTOFF,
    ).row(0, named=True)
    assert result["cba_eligibility_class"] == "super_two_candidate"
    assert result["super_two_cutoff_days"] is None
    assert result["review_reasons"] == "super_two_pool_incomplete"


def test_40man_player_is_rule5_protected() -> None:
    result = build_team_control_summary(
        _players(
            [
                {
                    "player_id": 1,
                    "on_40man": True,
                    "birth_date": None,
                    "first_pro_contract_date": None,
                }
            ]
        ),
        pl.DataFrame(schema={
            "player_id": pl.Int64,
            "season": pl.Int64,
            "service_days": pl.Int64,
            "optioned_days": pl.Int64,
            "option_year_used": pl.Boolean,
            "pro_active_days": pl.Int64,
            "pro_active_or_injured_days": pl.Int64,
            "full_pro_season": pl.Boolean,
        }),
        as_of_date=CUTOFF,
    ).row(0, named=True)
    assert result["rule5_status"] == "protected_40man"
    assert result["calculation_confidence"] == "rule_calculated"


def test_incomplete_history_remains_visible_instead_of_becoming_zero_confidence() -> None:
    result = build_team_control_summary(
        _players([{"player_id": 1, "history_complete": False}]),
        pl.DataFrame(schema={
            "player_id": pl.Int64,
            "season": pl.Int64,
            "service_days": pl.Int64,
            "optioned_days": pl.Int64,
            "option_year_used": pl.Boolean,
            "pro_active_days": pl.Int64,
            "pro_active_or_injured_days": pl.Int64,
            "full_pro_season": pl.Boolean,
        }),
        as_of_date=CUTOFF,
    ).row(0, named=True)
    assert result["calculation_confidence"] == "insufficient_history"
    assert result["review_reasons"] == "incomplete_statsapi_history"


def test_future_stint_fails_chronology_check() -> None:
    with pytest.raises(ValueError, match="invalid identity, interval"):
        calculate_control_years(
            _stints([_stint(1, "mlb_active", "2025-09-28", "2025-09-29")]),
            _windows(),
            as_of_date=CUTOFF,
        )
