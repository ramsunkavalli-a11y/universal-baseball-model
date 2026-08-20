from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.pitching_performance import (
    PITCHING_OUTCOME_BINS,
    build_pitching_performance,
    validate_pitching_performance,
)


def _row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "season": 2024,
        "league_id": 112,
        "player_id": 700001,
        "pitching_games_played": 20,
        "pitching_games_started": 10,
        "pitching_batters_faced": 200,
        "pitching_strike_outs": 50,
        "pitching_base_on_balls": 20,
        "pitching_intentional_walks": 2,
        "pitching_hit_batsmen": 3,
        "pitching_home_runs": 10,
    }
    row.update(overrides)
    return row


def test_build_pitching_performance_reconciles_exhaustive_bf_profile() -> None:
    result = build_pitching_performance(pl.DataFrame([_row()]))

    assert result.summary.item(0, "pitching_unintentional_walks") == 18
    assert result.summary.item(0, "pitching_other_batters_faced") == 119
    assert result.summary.item(0, "observed_starter_share") == pytest.approx(0.5)
    assert result.profile.get_column("pitching_outcome_bin").to_list() == sorted(
        PITCHING_OUTCOME_BINS
    )
    assert result.profile.get_column("occurrence_count").sum() == 200
    assert result.profile.get_column("observed_probability").sum() == pytest.approx(1.0)
    assert result.metrics["all_profile_counts_reconcile_to_bf"] is True


def test_intentional_walk_is_observable_but_neutral_in_pitcher_walk_skill() -> None:
    result = build_pitching_performance(
        pl.DataFrame(
            [
                _row(
                    pitching_batters_faced=10,
                    pitching_strike_outs=2,
                    pitching_base_on_balls=3,
                    pitching_intentional_walks=2,
                    pitching_hit_batsmen=0,
                    pitching_home_runs=1,
                )
            ]
        )
    )

    counts = dict(
        result.profile.select("pitching_outcome_bin", "occurrence_count").iter_rows()
    )
    assert counts == {"HBP": 0, "HR": 1, "K": 2, "OTHER_BF": 6, "UBB": 1}


def test_multiteam_rows_are_summed_but_actual_leagues_remain_separate() -> None:
    result = build_pitching_performance(
        pl.DataFrame(
            [
                _row(pitching_batters_faced=100, pitching_games_played=10, pitching_games_started=5),
                _row(pitching_batters_faced=200, pitching_games_played=20, pitching_games_started=10),
                _row(
                    league_id=117,
                    pitching_batters_faced=80,
                    pitching_games_played=8,
                    pitching_games_started=8,
                    pitching_strike_outs=20,
                    pitching_base_on_balls=8,
                    pitching_intentional_walks=1,
                    pitching_hit_batsmen=1,
                    pitching_home_runs=4,
                ),
            ]
        )
    )

    assert result.summary.height == 2
    assert result.summary.filter(pl.col("league_id") == 112).item(
        0, "pitching_batters_faced"
    ) == 300
    assert result.summary.filter(pl.col("league_id") == 117).item(
        0, "pitching_batters_faced"
    ) == 80


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("pitching_intentional_walks", 21, "intentional walks"),
        ("pitching_strike_outs", 180, "components exceed"),
        ("pitching_games_started", 21, "started cannot exceed"),
        ("pitching_batters_faced", -1, "nonnegative"),
        ("pitching_home_runs", 1.5, "finite integers"),
    ],
)
def test_pitching_performance_fails_closed_on_invalid_counts(
    field: str,
    value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        build_pitching_performance(pl.DataFrame([_row(**{field: value})]))


def test_zero_bf_rows_are_diagnostic_not_fake_profiles() -> None:
    result = build_pitching_performance(
        pl.DataFrame(
            [
                _row(),
                _row(
                    player_id=700002,
                    pitching_games_played=0,
                    pitching_games_started=0,
                    pitching_batters_faced=0,
                    pitching_strike_outs=0,
                    pitching_base_on_balls=0,
                    pitching_intentional_walks=0,
                    pitching_hit_batsmen=0,
                    pitching_home_runs=0,
                ),
            ]
        )
    )

    assert result.summary.height == 1
    assert result.metrics["zero_bf_source_row_count"] == 1


def test_validate_pitching_performance_rejects_missing_profile_bin() -> None:
    result = build_pitching_performance(pl.DataFrame([_row()]))
    broken = result.profile.filter(pl.col("pitching_outcome_bin") != "HR")

    with pytest.raises(ValueError, match="does not reconcile"):
        validate_pitching_performance(result.summary, broken)
