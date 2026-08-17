from __future__ import annotations

from datetime import date, timedelta

import polars as pl
import pytest

from universal_baseball.current_talent_batted_ball_reconciliation import (
    RECONCILED_TRACKED_BBE_SCHEMA,
)
from universal_baseball.current_talent_contact_value_features import (
    CONTACT_VALUE_FEATURE_TRAINING_CUTOFF,
    attach_contact_value_features_to_future_contacts,
    prepare_contact_value_feature_snapshots,
)


def _tracked_rows(
    *,
    season: int,
    player_id: int,
    count: int,
    start_date: date,
    base_ev: float,
    sweet_every: int,
    source_family: str,
    league_id: int,
    level_group: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(count):
        game_date = start_date + timedelta(days=index % 12)
        launch_angle = 15.0 if index % sweet_every == 0 else 40.0
        rows.append(
            {
                "game_date": game_date,
                "game_pk": season * 100000 + player_id * 100 + index,
                "player_id": player_id,
                "at_bat_number": index + 1,
                "pitch_number": 1,
                "launch_speed": base_ev + (index % 3) * 0.5,
                "launch_angle": launch_angle,
                "sweet_spot": 8.0 <= launch_angle <= 32.0,
                "season": season,
                "league_id": league_id,
                "level_group": level_group,
                "source_family": source_family,
                "source_capability_tier": (
                    f"{source_family}:{season}:{league_id}:{level_group}"
                ),
            }
        )
    return rows


def _tracking_frames() -> tuple[pl.DataFrame, pl.DataFrame]:
    rows_2021 = [
        *_tracked_rows(
            season=2021,
            player_id=1,
            count=24,
            start_date=date(2021, 6, 1),
            base_ev=90.0,
            sweet_every=2,
            source_family="MLB_SAVANT",
            league_id=103,
            level_group="MLB",
        ),
        *_tracked_rows(
            season=2021,
            player_id=2,
            count=22,
            start_date=date(2021, 6, 2),
            base_ev=84.0,
            sweet_every=3,
            source_family="MILB_SAVANT_TRACKED",
            league_id=123,
            level_group="SINGLE_A",
        ),
        *_tracked_rows(
            season=2021,
            player_id=3,
            count=10,
            start_date=date(2021, 6, 3),
            base_ev=88.0,
            sweet_every=2,
            source_family="MLB_SAVANT",
            league_id=104,
            level_group="MLB",
        ),
    ]
    rows_2022 = [
        *_tracked_rows(
            season=2022,
            player_id=1,
            count=8,
            start_date=date(2022, 6, 1),
            base_ev=99.0,
            sweet_every=1,
            source_family="MLB_SAVANT",
            league_id=103,
            level_group="MLB",
        ),
        *_tracked_rows(
            season=2022,
            player_id=3,
            count=15,
            start_date=date(2022, 6, 2),
            base_ev=91.0,
            sweet_every=2,
            source_family="MILB_SAVANT_TRACKED",
            league_id=112,
            level_group="AAA",
        ),
    ]
    return (
        pl.DataFrame(rows_2021).cast(RECONCILED_TRACKED_BBE_SCHEMA, strict=True),
        pl.DataFrame(rows_2022).cast(RECONCILED_TRACKED_BBE_SCHEMA, strict=True),
    )


def _future_contacts(cutoff: date) -> pl.DataFrame:
    rows = []
    for index, player_id in enumerate((1, 2, 3, 999), start=1):
        rows.append(
            {
                "event_date": cutoff + timedelta(days=index),
                "game_pk": 9000 + index,
                "at_bat_index": index,
                "pitch_number": 1,
                "league_id": 103,
                "level_group": "MLB",
                "player_id": player_id,
                "participant_authority": "fixture",
                "contact_bin": "CENTER_LD",
                "terminal_outcome_group": "1B",
                "terminal_outcome_status": "fixture_supported",
                "terminal_value": 0.4,
            }
        )
    return pl.DataFrame(rows)


def test_feature_preparation_fits_standardization_once_on_2021_training_snapshot() -> None:
    tracking_2021, tracking_2022 = _tracking_frames()
    prepared = prepare_contact_value_feature_snapshots(tracking_2021, tracking_2022)

    assert prepared.standardization.fitted_player_count == 2
    assert prepared.metrics["training_cutoff"] == "2021-07-15"
    assert prepared.metrics["standardization_fit_source"] == (
        "eligible_2021_07_15_player_features_only"
    )
    assert prepared.metrics["standardization_reused_unchanged_for_2022"] is True
    assert prepared.metrics["model_scoring"] is False
    assert prepared.metrics["accessed_2023"] is False

    training = prepared.snapshots[CONTACT_VALUE_FEATURE_TRAINING_CUTOFF]
    later = prepared.snapshots[date(2022, 7, 15)]
    assert training.metrics["richer_eligible_player_count"] == 2
    # Player 3 becomes eligible only after observed 2022 BBE are added.
    assert later.standardized_features.filter(
        (pl.col("player_id") == 3) & pl.col("tracked_bbe_eligible")
    ).height == 1
    # Player 1's 2022 EV jump changes its z-score, but not the fitted moments.
    train_z = training.standardized_features.filter(pl.col("player_id") == 1).row(0, named=True)
    later_z = later.standardized_features.filter(pl.col("player_id") == 1).row(0, named=True)
    assert later_z["z_mean_exit_velocity"] != train_z["z_mean_exit_velocity"]


def test_feature_attachment_preserves_all_target_rows_and_zero_fallback() -> None:
    tracking_2021, tracking_2022 = _tracking_frames()
    prepared = prepare_contact_value_feature_snapshots(tracking_2021, tracking_2022)
    cutoff = date(2022, 7, 15)
    attached, metrics = attach_contact_value_features_to_future_contacts(
        _future_contacts(cutoff),
        prepared.snapshots[cutoff],
    )

    assert attached.height == 4
    assert attached.select("game_pk", "at_bat_index", "pitch_number").n_unique() == 4
    assert metrics["future_target_contact_count"] == 4
    assert metrics["attached_target_contact_count"] == 4
    assert metrics["paired_richer_target_contact_count"] == 3
    assert metrics["zero_fallback_target_contact_count"] == 1
    assert metrics["target_key_coverage_unchanged"] is True
    assert metrics["comparator_richer_paired_keys_identical_by_construction"] is True
    assert metrics["zero_fallback_exact"] is True

    untracked = attached.filter(pl.col("player_id") == 999).row(0, named=True)
    assert untracked["tracked_bbe_eligible"] is False
    assert untracked["observed_model_bbe"] == 0
    assert untracked["contact_value_residual_applies"] is False
    assert untracked["unavailable_richer_residual_fallback"] == 0.0
    assert untracked["z_mean_exit_velocity"] is None

    paired = attached.filter(pl.col("contact_value_residual_applies"))
    assert set(paired.get_column("player_id").to_list()) == {1, 2, 3}
    assert paired.get_column("unavailable_richer_residual_fallback").null_count() == 3


def test_feature_attachment_preserves_exact_milb_capability_tier() -> None:
    tracking_2021, tracking_2022 = _tracking_frames()
    prepared = prepare_contact_value_feature_snapshots(tracking_2021, tracking_2022)
    cutoff = date(2022, 7, 15)
    attached, metrics = attach_contact_value_features_to_future_contacts(
        _future_contacts(cutoff), prepared.snapshots[cutoff]
    )
    player2 = attached.filter(pl.col("player_id") == 2).row(0, named=True)
    assert player2["observed_milb_bbe"] == 22
    assert player2["observed_source_capability_tiers"] == (
        "MILB_SAVANT_TRACKED:2021:123:SINGLE_A"
    )
    assert metrics["exact_capability_tier_paired_contact_counts"][
        "MILB_SAVANT_TRACKED:2021:123:SINGLE_A"
    ] == 1
    assert metrics["any_observed_milb_paired_contact_count"] >= 1


def test_feature_preparation_rejects_2023_tracking() -> None:
    tracking_2021, tracking_2022 = _tracking_frames()
    bad = tracking_2022.with_columns(
        pl.lit(2023).cast(pl.Int64).alias("season"),
        pl.lit(date(2023, 6, 1)).cast(pl.Date).alias("game_date"),
    )
    with pytest.raises(ValueError, match="season mismatch.*2023"):
        prepare_contact_value_feature_snapshots(tracking_2021, bad)
