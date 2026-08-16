import polars as pl
import pytest

from universal_baseball.current_talent_milb_evidence import (
    build_milb_current_talent_player_game_evidence,
    project_milb_player_game_outcomes,
    resolve_milb_player_game_outcomes,
)


def _raw_player_games() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_id": [100, 100, 101],
            "game_date": ["2024-04-10", "2024-04-12", "2024-04-20"],
            "game_type": ["R", "R", "R"],
            "league_id": [117, 117, 117],
            "player_id": [10, 10, 10],
            # game 100 partial snapshot followed by a complete/resumed snapshot
            "batting_PA": [2, 4, 4],
            "batting_AB": [2, 3, 4],
            "batting_BB": [0, 1, 0],
            "batting_HBP": [0, 0, 0],
            "batting_SO": [1, 1, 1],
            "batting_SF": [0, 0, 0],
            "batting_SH": [0, 0, 0],
            "batting_CI": [0, 0, 0],
        }
    )


def _contacts() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2024, 2024, 2024, 2024],
            "league_id": [117, 117, 117, 117],
            "game_pk": [100, 100, 101, 101],
            "batter_mlbam_id": [10, 10, 10, 10],
            "participant_authority": [
                "source_default",
                "official_sequence_overlay",
                "source_default",
                "source_default",
            ],
            "core_bin": ["PULL_GB", "CENTER_LD", "IFFB", None],
            "contact_profile_status": [
                "core_contact",
                "core_contact",
                "core_contact",
                "special_bunt",
            ],
        }
    )


def test_player_game_outcome_resolution_uses_latest_date_for_dominant_snapshot() -> None:
    projected = project_milb_player_game_outcomes(
        _raw_player_games(), source_asset="fixture", season=2024
    )
    resolved, metrics = resolve_milb_player_game_outcomes(projected)

    game100 = resolved.filter(pl.col("game_id") == 100).row(0, named=True)
    assert game100["batting_PA"] == 4
    assert str(game100["game_date"]) == "2024-04-12"
    assert game100["game_date_conflict"] is True
    assert game100["outcome_resolution"] == "componentwise_dominance"
    assert metrics["resolved_by_componentwise_dominance_count"] == 1
    assert metrics["game_date_conflict_player_game_count"] == 1
    assert metrics["unresolved_player_game_count"] == 0


def test_build_milb_player_game_evidence_reconciles_core_profile() -> None:
    projected = project_milb_player_game_outcomes(
        _raw_player_games(), source_asset="fixture", season=2024
    )
    resolved, _ = resolve_milb_player_game_outcomes(projected)
    summary, profile, metrics = build_milb_current_talent_player_game_evidence(
        resolved, _contacts()
    )

    game100 = summary.filter(pl.col("game_pk") == 100).row(0, named=True)
    # 1 BB + 1 K + 2 classified core contacts = 4 core events / 4 PA.
    assert game100["batting_plate_appearances"] == 4
    assert game100["core_profile_event_count"] == 4
    assert game100["non_core_event_count"] == 0
    assert game100["unknown_event_count"] == 0
    assert game100["participant_authority_status"] == "mixed_source_and_official"

    game101 = summary.filter(pl.col("game_pk") == 101).row(0, named=True)
    # 1 K + 1 IFFB + 1 bunt leaves one PA explicitly unknown/non-core residual.
    assert game101["core_profile_event_count"] == 2
    assert game101["non_core_event_count"] == 1
    assert game101["unknown_event_count"] == 1

    p100 = profile.filter(pl.col("game_pk") == 100)
    assert p100.get_column("occurrence_count").sum() == 4
    assert set(p100.get_column("core_bin").to_list()) == {
        "BB_HBP",
        "K",
        "PULL_GB",
        "CENTER_LD",
    }
    assert metrics["player_game_count"] == 2
    assert metrics["contact_event_count"] == 4
    assert metrics["official_overlay_contact_count"] == 1


def test_nonmonotonic_outcome_conflict_remains_unresolved() -> None:
    raw = _raw_player_games().filter(pl.col("game_id") == 100).with_columns(
        pl.when(pl.arange(0, pl.len()) == 1)
        .then(pl.lit(0))
        .otherwise(pl.col("batting_SO"))
        .alias("batting_SO")
    )
    projected = project_milb_player_game_outcomes(raw, source_asset="fixture")
    resolved, metrics = resolve_milb_player_game_outcomes(projected)
    assert resolved.row(0, named=True)["outcome_resolution"] == "unresolved_nonmonotonic_conflict"
    assert metrics["unresolved_player_game_count"] == 1


def test_overaccounted_player_game_fails_loudly() -> None:
    raw = _raw_player_games().filter(pl.col("game_id") == 101)
    projected = project_milb_player_game_outcomes(raw, source_asset="fixture")
    resolved, _ = resolve_milb_player_game_outcomes(projected)
    contacts = pl.concat([_contacts().filter(pl.col("game_pk") == 101)] * 3)
    with pytest.raises(ValueError, match="over-accounts"):
        build_milb_current_talent_player_game_evidence(resolved, contacts)
