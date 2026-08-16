from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_evidence import EvidenceWindow
from universal_baseball.current_talent_validation_dataset import (
    build_future_target,
    build_validation_snapshot_dataset,
)


def _summary() -> pl.DataFrame:
    rows = [
        # player 10: AA predictor, then AAA and MLB future environments.
        (2024, "2024-04-10", 1, 111, 10, "AA"),
        (2024, "2024-05-01", 2, 117, 10, "AAA"),
        (2024, "2024-06-01", 3, 1, 10, "MLB"),
        # player 20: MLB predictor, then optioned to AAA.
        (2024, "2024-04-15", 4, 1, 20, "MLB"),
        (2024, "2024-05-15", 5, 117, 20, "AAA"),
        # player 30: two actual leagues on the latest pre-cutoff date -> ambiguous context.
        (2024, "2024-04-20", 6, 111, 30, "AA"),
        (2024, "2024-04-20", 7, 117, 30, "AAA"),
        (2024, "2024-05-10", 8, 111, 30, "AA"),
        # player 40 has future evidence but no predictor evidence.
        (2024, "2024-05-20", 9, 117, 40, "AAA"),
        # Exact 90-day exclusive endpoint from May 1; must not enter target.
        (2024, "2024-07-30", 10, 117, 10, "AAA"),
    ]
    return pl.DataFrame(
        {
            "season": [row[0] for row in rows],
            "game_date": [row[1] for row in rows],
            "game_pk": [row[2] for row in rows],
            "league_id": [row[3] for row in rows],
            "player_id": [row[4] for row in rows],
            "level_group": [row[5] for row in rows],
            "batting_plate_appearances": [4] * len(rows),
            "expected_contact_count": [2] * len(rows),
            "observed_contact_count": [2] * len(rows),
            "contact_count_residual": [0] * len(rows),
            "core_profile_event_count": [4] * len(rows),
            "bunt_contact_count": [0] * len(rows),
            "foul_air_excluded_count": [0] * len(rows),
            "unknown_contact_count": [0] * len(rows),
            "special_noncontact_count": [0] * len(rows),
            "pa_accounting_residual": [0] * len(rows),
            "participant_authority_status": ["source"] * len(rows),
            "source_capability_tier": ["result"] * len(rows),
        }
    )


def _profile() -> pl.DataFrame:
    summary = _summary()
    profile_rows: list[dict[str, object]] = []
    contact_bin_by_game = {
        1: "PULL_GB",
        2: "CENTER_LD",
        3: "OPPO_OFFB",
        4: "PULL_LD",
        5: "CENTER_GB",
        6: "PULL_GB",
        7: "CENTER_GB",
        8: "OPPO_GB",
        9: "PULL_OFFB",
        10: "CENTER_OFFB",
    }
    for row in summary.iter_rows(named=True):
        profile_rows.extend(
            [
                {
                    "season": row["season"],
                    "game_date": row["game_date"],
                    "game_pk": row["game_pk"],
                    "league_id": row["league_id"],
                    "player_id": row["player_id"],
                    "level_group": row["level_group"],
                    "core_bin": "K",
                    "occurrence_count": 2,
                },
                {
                    "season": row["season"],
                    "game_date": row["game_date"],
                    "game_pk": row["game_pk"],
                    "league_id": row["league_id"],
                    "player_id": row["player_id"],
                    "level_group": row["level_group"],
                    "core_bin": contact_bin_by_game[int(row["game_pk"])],
                    "occurrence_count": 2,
                },
            ]
        )
    return pl.DataFrame(profile_rows)


def test_future_target_preserves_actual_environment_and_exclusive_end() -> None:
    summary, profile = build_future_target(
        _summary(),
        _profile(),
        cutoff=date(2024, 5, 1),
    )

    player10 = summary.filter(pl.col("player_id") == 10)
    assert set(player10.get_column("target_level_group").to_list()) == {"AAA", "MLB"}
    assert player10.get_column("future_plate_appearances").sum() == 8
    assert player10.get_column("future_core_events").sum() == 8
    assert player10.get_column("last_target_date").max() == date(2024, 6, 1)
    assert not summary.filter(pl.col("last_target_date") == date(2024, 7, 30)).height
    assert summary.get_column("aggregate_pa_cap_applied").unique().to_list() == [False]

    profile_check = profile.group_by(
        ["player_id", "target_season", "target_league_id", "target_level_group"]
    ).agg(pl.col("future_core_profile_rate").sum().alias("rate_sum"))
    assert profile_check.filter((pl.col("rate_sum") - 1.0).abs() > 1e-12).is_empty()


def test_validation_dataset_freezes_as_of_environment_and_transition_strata() -> None:
    dataset = build_validation_snapshot_dataset(
        _summary(),
        _profile(),
        cutoff=date(2024, 5, 1),
        window=EvidenceWindow("all_history"),
    )

    player10_predictor = dataset.predictor_summary.filter(pl.col("player_id") == 10).row(
        0, named=True
    )
    assert player10_predictor["raw_plate_appearances"] == 4
    assert player10_predictor["as_of_context_date"] == date(2024, 4, 10)
    assert player10_predictor["as_of_league_id"] == 111
    assert player10_predictor["as_of_level_group"] == "AA"
    assert player10_predictor["prior_mlb_evidence"] is False

    player10_scoring = dataset.scoring_rows.filter(pl.col("player_id") == 10)
    transitions = dict(
        zip(
            player10_scoring.get_column("target_level_group").to_list(),
            player10_scoring.get_column("target_transition").to_list(),
            strict=True,
        )
    )
    assert transitions == {"AAA": "PROMOTION", "MLB": "MLB_DEBUT"}

    player20 = dataset.scoring_rows.filter(pl.col("player_id") == 20).row(0, named=True)
    assert player20["as_of_level_group"] == "MLB"
    assert player20["prior_mlb_evidence"] is True
    assert player20["target_level_group"] == "AAA"
    assert player20["target_transition"] == "MLB_TO_MILB"

    player30 = dataset.scoring_rows.filter(pl.col("player_id") == 30).row(0, named=True)
    assert player30["as_of_environment_ambiguous"] is True
    assert player30["as_of_league_id"] is None
    assert player30["as_of_level_group"] is None
    assert player30["target_transition"] == "AMBIGUOUS_AS_OF_ENVIRONMENT"


def test_target_players_without_pre_cutoff_predictor_are_reported_not_backfilled() -> None:
    dataset = build_validation_snapshot_dataset(
        _summary(),
        _profile(),
        cutoff=date(2024, 5, 1),
        window=EvidenceWindow("all_history"),
    )

    assert 40 in dataset.target_summary.get_column("player_id").to_list()
    assert 40 not in dataset.scoring_rows.get_column("player_id").to_list()
    assert dataset.metrics["target_player_without_predictor_count"] == 1
    assert dataset.metrics["aggregate_pa_cap_applied"] is False
    assert dataset.metrics["aggregate_pa_cap_status"] == "requires_pa_grain_future_events"


def test_target_profile_reconciliation_stays_separate_from_pa_denominator() -> None:
    summary = _summary().with_columns(
        pl.when(pl.col("game_pk") == 8)
        .then(pl.lit(3))
        .otherwise(pl.col("observed_contact_count"))
        .alias("observed_contact_count"),
        pl.when(pl.col("game_pk") == 8)
        .then(pl.lit(1))
        .otherwise(pl.col("contact_count_residual"))
        .alias("contact_count_residual"),
        pl.when(pl.col("game_pk") == 8)
        .then(pl.lit(1))
        .otherwise(pl.col("unknown_contact_count"))
        .alias("unknown_contact_count"),
    )

    target_summary, target_profile = build_future_target(
        summary,
        _profile(),
        cutoff=date(2024, 5, 1),
    )
    player30 = target_summary.filter(pl.col("player_id") == 30).row(0, named=True)
    assert player30["future_contact_count_residual"] == 1
    assert player30["future_plate_appearances"] == 4
    assert player30["future_core_events"] == 4
    assert target_profile.filter(pl.col("player_id") == 30).get_column(
        "future_occurrence_count"
    ).sum() == 4


def test_invalid_profile_still_fails_before_validation_dataset_build() -> None:
    bad_profile = _profile().with_columns(
        pl.when((pl.col("game_pk") == 2) & (pl.col("core_bin") == "K"))
        .then(pl.lit(1))
        .otherwise(pl.col("occurrence_count"))
        .alias("occurrence_count")
    )
    with pytest.raises(ValueError, match="do not reconcile"):
        build_validation_snapshot_dataset(
            _summary(),
            bad_profile,
            cutoff=date(2024, 5, 1),
            window=EvidenceWindow("all_history"),
        )
