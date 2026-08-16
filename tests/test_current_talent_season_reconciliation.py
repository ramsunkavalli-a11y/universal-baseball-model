from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_season_reconciliation import (
    reconcile_resolved_outcomes_to_season_aggregates,
)


def _games() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_date": [date(2022, 5, 1), date(2022, 5, 2), date(2022, 5, 1)],
            "game_type": ["R", "R", "R"],
            "league_id": [112, 112, 117],
            "player_id": [10, 10, 20],
            "batting_PA": [4, 5, 4],
            "batting_BB": [1, 0, 1],
            "batting_HBP": [0, 1, 0],
            "batting_SO": [1, 2, 1],
            "outcome_resolution": ["consensus", "consensus", "consensus"],
        }
    )


def _season() -> pl.DataFrame:
    # Player 10 appears on two team rows; reconciliation must aggregate those
    # rows within the actual league rather than compare one team at a time.
    return pl.DataFrame(
        {
            "season": [2022, 2022, 2022],
            "league_id": [112, 112, 117],
            "person_id": [10, 10, 20],
            "team_id": [1, 2, 3],
            "plate_appearances": [4, 5, 4],
            "walks": [1, 0, 1],
            "hit_by_pitch": [0, 1, 0],
            "strikeouts": [1, 2, 1],
        }
    )


def test_reconciliation_aggregates_teams_and_matches_exactly() -> None:
    comparison, metrics = reconcile_resolved_outcomes_to_season_aggregates(
        _games(),
        _season(),
        season=2022,
        expected_league_ids=frozenset({112, 117}),
    )
    assert comparison.height == 2
    assert metrics["exact_reconciliation"] is True
    assert metrics["mismatch_player_league_count"] == 0
    assert metrics["fields"]["plate_appearances"]["game_total"] == 13
    assert metrics["fields"]["plate_appearances"]["season_total"] == 13


def test_reconciliation_preserves_mismatch_diagnostics_without_repair() -> None:
    bad = _season().with_columns(
        pl.when((pl.col("league_id") == 117) & (pl.col("person_id") == 20))
        .then(pl.col("walks") + 1)
        .otherwise(pl.col("walks"))
        .alias("walks")
    )
    comparison, metrics = reconcile_resolved_outcomes_to_season_aggregates(
        _games(), bad, season=2022, expected_league_ids=frozenset({112, 117})
    )
    row = comparison.filter(pl.col("player_id") == 20).row(0, named=True)
    assert row["walks_difference"] == -1
    assert row["has_any_mismatch"] is True
    assert metrics["exact_reconciliation"] is False
    assert metrics["fields"]["walks"]["signed_difference"] == -1
    assert metrics["fields"]["walks"]["absolute_difference"] == 1

    with pytest.raises(ValueError, match="do not exactly reconcile"):
        reconcile_resolved_outcomes_to_season_aggregates(
            _games(),
            bad,
            season=2022,
            expected_league_ids=frozenset({112, 117}),
            require_exact=True,
        )


def test_reconciliation_rejects_missing_expected_league() -> None:
    with pytest.raises(ValueError, match="season aggregates do not cover expected actual leagues"):
        reconcile_resolved_outcomes_to_season_aggregates(
            _games(),
            _season().filter(pl.col("league_id") == 112),
            season=2022,
            expected_league_ids=frozenset({112, 117}),
        )
