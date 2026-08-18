from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_evidence import EvidenceWindow
from universal_baseball.projection_dataset import (
    build_projection_future_target,
    build_projection_snapshot_dataset,
)
from universal_baseball.projection_validation import (
    PROJECTION_V1_CONFIRMATION_FOLD,
    PROJECTION_V1_DEVELOPMENT_FOLDS,
)


def _game_row(
    *,
    season: int,
    game_date: date,
    game_pk: int,
    league_id: int,
    player_id: int,
    level_group: str,
) -> dict[str, object]:
    return {
        "season": season,
        "game_date": game_date,
        "game_pk": game_pk,
        "league_id": league_id,
        "player_id": player_id,
        "level_group": level_group,
        "batting_plate_appearances": 4,
        "expected_contact_count": 2,
        "observed_contact_count": 2,
        "contact_count_residual": 0,
        "core_profile_event_count": 4,
        "bunt_contact_count": 0,
        "foul_air_excluded_count": 0,
        "unknown_contact_count": 0,
        "special_noncontact_count": 0,
        "pa_accounting_residual": 0,
        "participant_authority_status": "source_default",
        "source_capability_tier": "synthetic_test",
    }


def _profile_rows(summary: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for game in summary.iter_rows(named=True):
        for core_bin, count in (("BB_HBP", 1), ("K", 1), ("PULL_GB", 2)):
            rows.append(
                {
                    "season": game["season"],
                    "game_date": game["game_date"],
                    "game_pk": game["game_pk"],
                    "league_id": game["league_id"],
                    "player_id": game["player_id"],
                    "level_group": game["level_group"],
                    "core_bin": core_bin,
                    "occurrence_count": count,
                }
            )
    return pl.DataFrame(rows)


def _development_evidence() -> tuple[pl.DataFrame, pl.DataFrame]:
    summary = pl.DataFrame(
        [
            # Player 1 has pre-snapshot AAA evidence and a 2024 MLB debut target.
            _game_row(
                season=2023,
                game_date=date(2023, 9, 20),
                game_pk=1,
                league_id=117,
                player_id=1,
                level_group="AAA",
            ),
            # Same player after the snapshot: neither predictor evidence nor 2024 target.
            _game_row(
                season=2023,
                game_date=date(2023, 11, 1),
                game_pk=2,
                league_id=117,
                player_id=1,
                level_group="AAA",
            ),
            _game_row(
                season=2024,
                game_date=date(2024, 4, 1),
                game_pk=3,
                league_id=103,
                player_id=1,
                level_group="MLB",
            ),
            _game_row(
                season=2024,
                game_date=date(2024, 5, 1),
                game_pk=4,
                league_id=103,
                player_id=1,
                level_group="MLB",
            ),
            # Player 2 has predictor evidence but no future opportunity.
            _game_row(
                season=2023,
                game_date=date(2023, 8, 15),
                game_pk=5,
                league_id=111,
                player_id=2,
                level_group="AA",
            ),
            # Player 3 has future opportunity but no pre-snapshot evidence.
            _game_row(
                season=2024,
                game_date=date(2024, 6, 10),
                game_pk=6,
                league_id=116,
                player_id=3,
                level_group="HIGH_A",
            ),
            # 2025 is outside the development target and must never enter it.
            _game_row(
                season=2025,
                game_date=date(2025, 4, 1),
                game_pk=7,
                league_id=103,
                player_id=1,
                level_group="MLB",
            ),
        ]
    )
    return summary, _profile_rows(summary)


def test_projection_future_target_is_exact_next_calendar_year_and_reconciles_profile():
    summary, profile = _development_evidence()
    fold = PROJECTION_V1_DEVELOPMENT_FOLDS[-1]

    target_summary, target_profile, metrics = build_projection_future_target(
        summary,
        profile,
        fold=fold,
    )

    assert set(target_summary.get_column("target_season").to_list()) == {2024}
    assert set(target_summary.get_column("player_id").to_list()) == {1, 3}
    assert target_summary.get_column("future_plate_appearances").sum() == 12
    assert target_summary.get_column("future_core_events").sum() == 12
    assert target_profile.get_column("future_occurrence_count").sum() == 12
    assert metrics["future_player_count"] == 2
    assert metrics["future_plate_appearances"] == 12
    assert metrics["confirmation"] is False


def test_projection_snapshot_reuses_strict_pre_snapshot_predictor_and_preserves_transitions():
    summary, profile = _development_evidence()
    fold = PROJECTION_V1_DEVELOPMENT_FOLDS[-1]
    window = EvidenceWindow(
        label="projection_test_1095d_180d",
        lookback_days=1095,
        half_life_days=180.0,
    )

    dataset = build_projection_snapshot_dataset(
        summary,
        profile,
        fold=fold,
        window=window,
    )

    assert set(dataset.predictor_summary.get_column("player_id").to_list()) == {1, 2}
    player1 = dataset.predictor_summary.filter(pl.col("player_id") == 1).row(0, named=True)
    assert player1["game_count"] == 1
    assert player1["last_evidence_date"] == date(2023, 9, 20)
    assert player1["as_of_level_group"] == "AAA"
    assert player1["prior_mlb_evidence"] is False

    assert set(dataset.target_summary.get_column("player_id").to_list()) == {1, 3}
    assert set(dataset.scoring_rows.get_column("player_id").to_list()) == {1}
    assert dataset.scoring_rows.get_column("target_transition").unique().to_list() == ["MLB_DEBUT"]

    assert dataset.metrics["predictor_player_without_target_count"] == 1
    assert dataset.metrics["target_player_without_predictor_count"] == 1
    assert dataset.metrics["scored_player_count"] == 1
    assert dataset.metrics["zero_future_opportunity_treated_as_bad_skill"] is False
    assert dataset.metrics["playing_time_modeled"] is False


def test_projection_target_keeps_multiple_actual_future_environments_separate():
    summary, profile = _development_evidence()
    extra = pl.DataFrame(
        [
            _game_row(
                season=2024,
                game_date=date(2024, 7, 1),
                game_pk=8,
                league_id=117,
                player_id=1,
                level_group="AAA",
            )
        ]
    )
    summary = pl.concat([summary, extra], how="diagonal_relaxed")
    profile = pl.concat([profile, _profile_rows(extra)], how="diagonal_relaxed")

    target_summary, _, _ = build_projection_future_target(
        summary,
        profile,
        fold=PROJECTION_V1_DEVELOPMENT_FOLDS[-1],
    )
    player1 = target_summary.filter(pl.col("player_id") == 1)
    assert set(player1.get_column("target_level_group").to_list()) == {"AAA", "MLB"}
    assert player1.height == 2


def test_projection_confirmation_target_is_quarantined_by_default():
    summary = pl.DataFrame(
        [
            _game_row(
                season=2024,
                game_date=date(2024, 9, 1),
                game_pk=10,
                league_id=117,
                player_id=1,
                level_group="AAA",
            ),
            _game_row(
                season=2025,
                game_date=date(2025, 5, 1),
                game_pk=11,
                league_id=103,
                player_id=1,
                level_group="MLB",
            ),
        ]
    )
    profile = _profile_rows(summary)

    with pytest.raises(ValueError, match="quarantined"):
        build_projection_future_target(
            summary,
            profile,
            fold=PROJECTION_V1_CONFIRMATION_FOLD,
        )
    with pytest.raises(ValueError, match="quarantined"):
        build_projection_snapshot_dataset(
            summary,
            profile,
            fold=PROJECTION_V1_CONFIRMATION_FOLD,
            window=EvidenceWindow(label="test", lookback_days=1095, half_life_days=180.0),
        )


def test_projection_confirmation_can_only_be_opened_with_explicit_authorization():
    summary = pl.DataFrame(
        [
            _game_row(
                season=2024,
                game_date=date(2024, 9, 1),
                game_pk=10,
                league_id=117,
                player_id=1,
                level_group="AAA",
            ),
            _game_row(
                season=2025,
                game_date=date(2025, 5, 1),
                game_pk=11,
                league_id=103,
                player_id=1,
                level_group="MLB",
            ),
        ]
    )
    profile = _profile_rows(summary)

    target_summary, _, metrics = build_projection_future_target(
        summary,
        profile,
        fold=PROJECTION_V1_CONFIRMATION_FOLD,
        allow_confirmation=True,
    )
    assert target_summary.get_column("target_season").unique().to_list() == [2025]
    assert metrics["confirmation_access_explicitly_authorized"] is True
