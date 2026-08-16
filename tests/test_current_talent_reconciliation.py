from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_reconciliation import (
    reconcile_player_game_to_performance,
)


def _game_evidence() -> tuple[pl.DataFrame, pl.DataFrame]:
    summary = pl.DataFrame(
        [
            {
                "season": 2024,
                "game_date": date(2024, 4, 1),
                "game_pk": 1,
                "league_id": 117,
                "player_id": 10,
                "level_group": "AAA",
                "batting_plate_appearances": 4,
                "expected_contact_count": 2,
                "observed_contact_count": 2,
                "contact_count_residual": 0,
                "core_profile_event_count": 3,
                "bunt_contact_count": 0,
                "foul_air_excluded_count": 0,
                "unknown_contact_count": 1,
                "special_noncontact_count": 0,
                "pa_accounting_residual": 0,
                "participant_authority_status": "source_default",
                "source_capability_tier": "test_v2",
            },
            {
                "season": 2024,
                "game_date": date(2024, 4, 2),
                "game_pk": 2,
                "league_id": 117,
                "player_id": 10,
                "level_group": "AAA",
                "batting_plate_appearances": 5,
                "expected_contact_count": 3,
                "observed_contact_count": 3,
                "contact_count_residual": 0,
                "core_profile_event_count": 4,
                "bunt_contact_count": 1,
                "foul_air_excluded_count": 0,
                "unknown_contact_count": 0,
                "special_noncontact_count": 0,
                "pa_accounting_residual": 0,
                "participant_authority_status": "source_default",
                "source_capability_tier": "test_v2",
            },
        ]
    )
    profile = pl.DataFrame(
        [
            {
                "season": 2024,
                "game_date": date(2024, 4, 1),
                "game_pk": 1,
                "league_id": 117,
                "player_id": 10,
                "level_group": "AAA",
                "core_bin": "BB_HBP",
                "occurrence_count": 1,
            },
            {
                "season": 2024,
                "game_date": date(2024, 4, 1),
                "game_pk": 1,
                "league_id": 117,
                "player_id": 10,
                "level_group": "AAA",
                "core_bin": "K",
                "occurrence_count": 1,
            },
            {
                "season": 2024,
                "game_date": date(2024, 4, 1),
                "game_pk": 1,
                "league_id": 117,
                "player_id": 10,
                "level_group": "AAA",
                "core_bin": "PULL_GB",
                "occurrence_count": 1,
            },
            {
                "season": 2024,
                "game_date": date(2024, 4, 2),
                "game_pk": 2,
                "league_id": 117,
                "player_id": 10,
                "level_group": "AAA",
                "core_bin": "K",
                "occurrence_count": 2,
            },
            {
                "season": 2024,
                "game_date": date(2024, 4, 2),
                "game_pk": 2,
                "league_id": 117,
                "player_id": 10,
                "level_group": "AAA",
                "core_bin": "CENTER_LD",
                "occurrence_count": 2,
            },
        ]
    )
    return summary, profile


def _performance(*, include_contact_fields: bool = False) -> tuple[pl.DataFrame, pl.DataFrame]:
    row = {
        "season": 2024,
        "league_id": 117,
        "player_id": 10,
        "batting_plate_appearances": 9,
        "core_profile_event_count": 7,
    }
    if include_contact_fields:
        row.update(
            {
                "aggregate_contact_count": 5,
                "contact_event_count": 5,
                "contact_count_residual_vs_aggregate": 0,
                "bunt_contact_count": 1,
                "foul_air_excluded_count": 0,
                "unknown_contact_count": 1,
            }
        )
    summary = pl.DataFrame([row])
    profile = pl.DataFrame(
        [
            {"season": 2024, "league_id": 117, "player_id": 10, "core_bin": "BB_HBP", "occurrence_count": 1},
            {"season": 2024, "league_id": 117, "player_id": 10, "core_bin": "K", "occurrence_count": 3},
            {"season": 2024, "league_id": 117, "player_id": 10, "core_bin": "PULL_GB", "occurrence_count": 1},
            {"season": 2024, "league_id": 117, "player_id": 10, "core_bin": "CENTER_LD", "occurrence_count": 2},
        ]
    )
    return summary, profile


def test_exact_game_rollup_reconciles_to_performance() -> None:
    game_summary, game_profile = _game_evidence()
    perf_summary, perf_profile = _performance(include_contact_fields=True)
    summary_comparison, _, metrics = reconcile_player_game_to_performance(
        game_summary, game_profile, perf_summary, perf_profile
    )
    assert metrics["exact_reconciliation"] is True
    assert metrics["game_plate_appearances"] == 9
    assert metrics["game_core_events"] == 7
    assert metrics["summary_fields_compared"] == [
        "batting_plate_appearances",
        "core_profile_event_count",
        "aggregate_contact_count",
        "contact_event_count",
        "contact_count_residual_vs_aggregate",
        "bunt_contact_count",
        "foul_air_excluded_count",
        "unknown_contact_count",
    ]
    assert summary_comparison.row(0, named=True)["has_any_mismatch"] is False


def test_bin_mismatch_is_hard_failure() -> None:
    game_summary, game_profile = _game_evidence()
    perf_summary, perf_profile = _performance()
    perf_profile = perf_profile.with_columns(
        pl.when(pl.col("core_bin") == "K")
        .then(pl.col("occurrence_count") + 1)
        .otherwise(pl.col("occurrence_count"))
        .alias("occurrence_count")
    )
    with pytest.raises(ValueError, match="does not exactly reconcile"):
        reconcile_player_game_to_performance(
            game_summary, game_profile, perf_summary, perf_profile
        )


def test_contact_classification_mismatch_is_hard_failure_when_performance_exposes_it() -> None:
    game_summary, game_profile = _game_evidence()
    perf_summary, perf_profile = _performance(include_contact_fields=True)
    perf_summary = perf_summary.with_columns(
        (pl.col("contact_event_count") + 1).alias("contact_event_count")
    )
    with pytest.raises(ValueError, match="does not exactly reconcile"):
        reconcile_player_game_to_performance(
            game_summary, game_profile, perf_summary, perf_profile
        )


def test_diagnostic_mode_returns_contact_mismatch_rows_before_failure() -> None:
    game_summary, game_profile = _game_evidence()
    perf_summary, perf_profile = _performance(include_contact_fields=True)
    perf_summary = perf_summary.with_columns(
        (pl.col("unknown_contact_count") + 1).alias("unknown_contact_count")
    )
    summary_comparison, _, metrics = reconcile_player_game_to_performance(
        game_summary,
        game_profile,
        perf_summary,
        perf_profile,
        require_exact=False,
    )
    assert metrics["exact_reconciliation"] is False
    assert metrics["summary_mismatch_row_count"] == 1
    assert metrics["summary_field_mismatch_counts"]["unknown_contact_count"] == 1
    assert summary_comparison.row(0, named=True)["unknown_contact_count_difference"] == -1
