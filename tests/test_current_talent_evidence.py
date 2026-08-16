from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_evidence import (
    EvidenceWindow,
    build_predictor_snapshot,
    validate_player_game_evidence,
)


def _summary() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2024, 2024, 2024, 2024],
            "game_date": ["2024-04-01", "2024-04-20", "2024-05-01", "2024-04-15"],
            "game_pk": [1, 2, 3, 4],
            "league_id": [117, 117, 117, 1],
            "player_id": [10, 10, 10, 20],
            "level_group": ["AAA", "AAA", "AAA", "MLB"],
            "batting_plate_appearances": [4, 4, 4, 5],
            "core_profile_event_count": [4, 3, 4, 4],
            "non_core_event_count": [0, 1, 0, 0],
            "unknown_event_count": [0, 0, 0, 1],
            "participant_authority_status": ["source", "official_overlay", "source", "official"],
            "source_capability_tier": ["result", "result", "result", "mlb_full"],
        }
    )


def _profile() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2024, 2024, 2024, 2024, 2024, 2024, 2024],
            "game_date": [
                "2024-04-01",
                "2024-04-01",
                "2024-04-20",
                "2024-04-20",
                "2024-05-01",
                "2024-04-15",
                "2024-04-15",
            ],
            "game_pk": [1, 1, 2, 2, 3, 4, 4],
            "league_id": [117, 117, 117, 117, 117, 1, 1],
            "player_id": [10, 10, 10, 10, 10, 20, 20],
            "level_group": ["AAA", "AAA", "AAA", "AAA", "AAA", "MLB", "MLB"],
            "core_bin": ["K", "BB_HBP", "K", "PULL_GB", "K", "K", "CENTER_LD"],
            "occurrence_count": [3, 1, 2, 1, 4, 2, 2],
        }
    )


def test_player_game_evidence_contract_reconciles_profile() -> None:
    report = validate_player_game_evidence(_summary(), _profile())
    assert report["player_game_count"] == 4
    assert report["player_count"] == 2
    assert report["actual_league_count"] == 2
    assert report["total_plate_appearances"] == 17
    assert report["total_core_events"] == 15


def test_snapshot_excludes_cutoff_day_and_preserves_actual_league_history() -> None:
    summary, profile = build_predictor_snapshot(
        _summary(),
        _profile(),
        cutoff=date(2024, 5, 1),
        window=EvidenceWindow("all_history"),
    )

    player10 = summary.filter(pl.col("player_id") == 10).row(0, named=True)
    assert player10["raw_plate_appearances"] == 8
    assert player10["raw_core_events"] == 7
    assert player10["raw_non_core_events"] == 1
    assert player10["game_count"] == 2
    assert player10["league_count"] == 1
    assert player10["min_level_group"] == "AAA"
    assert player10["max_level_group"] == "AAA"
    assert player10["last_evidence_date"] == date(2024, 4, 20)

    player10_profile = profile.filter(pl.col("player_id") == 10)
    assert player10_profile.get_column("raw_occurrence_count").sum() == 7
    assert set(player10_profile.get_column("core_bin").to_list()) == {"K", "BB_HBP", "PULL_GB"}
    assert pytest.approx(player10_profile.get_column("raw_core_profile_rate").sum()) == 1.0


def test_snapshot_hard_lookback_window_is_deterministic() -> None:
    summary, profile = build_predictor_snapshot(
        _summary(),
        _profile(),
        cutoff=date(2024, 5, 1),
        window=EvidenceWindow("recent_20d", lookback_days=20),
    )

    player10 = summary.filter(pl.col("player_id") == 10).row(0, named=True)
    assert player10["raw_plate_appearances"] == 4
    assert player10["raw_core_events"] == 3
    assert player10["first_evidence_date"] == date(2024, 4, 20)
    assert profile.filter(pl.col("player_id") == 10).get_column("raw_occurrence_count").sum() == 3


def test_snapshot_half_life_exposes_effective_evidence_without_changing_raw_counts() -> None:
    summary, profile = build_predictor_snapshot(
        _summary(),
        _profile(),
        cutoff=date(2024, 5, 1),
        window=EvidenceWindow("decayed", half_life_days=10),
    )

    player10 = summary.filter(pl.col("player_id") == 10).row(0, named=True)
    assert player10["raw_plate_appearances"] == 8
    assert 0 < player10["effective_plate_appearances"] < 8
    assert 0 < player10["effective_core_events"] < 7
    assert pytest.approx(
        profile.filter(pl.col("player_id") == 10).get_column("effective_occurrence_count").sum(),
        abs=1e-9,
    ) == player10["effective_core_events"]
    assert pytest.approx(
        profile.filter(pl.col("player_id") == 10).get_column("effective_core_profile_rate").sum(),
        abs=1e-9,
    ) == 1.0


def test_profile_mismatch_fails_loudly() -> None:
    bad_profile = _profile().with_columns(
        pl.when((pl.col("game_pk") == 1) & (pl.col("core_bin") == "K"))
        .then(pl.lit(2))
        .otherwise(pl.col("occurrence_count"))
        .alias("occurrence_count")
    )
    with pytest.raises(ValueError, match="do not reconcile"):
        validate_player_game_evidence(_summary(), bad_profile)


def test_invalid_window_parameters_fail() -> None:
    with pytest.raises(ValueError):
        EvidenceWindow("bad", lookback_days=0)
    with pytest.raises(ValueError):
        EvidenceWindow("bad", half_life_days=0)
