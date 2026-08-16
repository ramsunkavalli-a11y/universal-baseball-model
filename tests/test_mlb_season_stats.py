from __future__ import annotations

import json

import pytest

from universal_baseball.mlb_season_stats import (
    MLB_BATTING_BACKBONE_SCHEMA,
    capture_manifest,
    project_mlb_hitting_splits,
)


def _split(player_id: int, **overrides):
    stat = {
        "plateAppearances": 100,
        "atBats": 85,
        "baseOnBalls": 10,
        "intentionalWalks": 1,
        "hitByPitch": 2,
        "strikeOuts": 20,
        "sacBunts": 1,
        "sacFlies": 2,
    }
    stat.update(overrides)
    return {
        "player": {"id": player_id, "fullName": f"Player {player_id}"},
        "stat": stat,
    }


def test_mlb_bulk_projection_matches_performance_backbone_contract() -> None:
    frame = project_mlb_hitting_splits([_split(101)], season=2024, league_id=103)
    assert frame.schema == MLB_BATTING_BACKBONE_SCHEMA
    row = frame.to_dicts()[0]
    assert row["season"] == 2024
    assert row["league_id"] == 103
    assert row["player_id"] == 101
    assert row["batting_plate_appearances"] == 100
    assert row["batting_base_on_balls"] == 10
    assert row["batting_hit_by_pitch"] == 2
    assert row["batting_strike_outs"] == 20
    assert row["batting_balls_in_play"] == 68  # AB - SO + SH + SF
    assert row["simple_pa_accounting_residual"] == 0


def test_pa_accounting_residual_is_preserved_not_forced_to_zero() -> None:
    frame = project_mlb_hitting_splits(
        [_split(101, plateAppearances=101)], season=2024, league_id=104
    )
    assert frame.to_dicts()[0]["simple_pa_accounting_residual"] == -1


def test_missing_required_field_fails_loudly() -> None:
    split = _split(101)
    del split["stat"]["hitByPitch"]
    with pytest.raises(ValueError, match="missing fields"):
        project_mlb_hitting_splits([split], season=2024, league_id=103)


def test_duplicate_player_league_season_is_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        project_mlb_hitting_splits(
            [_split(101), _split(101)], season=2024, league_id=103
        )


def test_unknown_actual_league_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported MLB actual league"):
        project_mlb_hitting_splits([_split(101)], season=2024, league_id=999)


def test_capture_manifest_is_stable_json() -> None:
    # No captures is still a deterministic serializable provenance object.
    assert json.loads(capture_manifest([])) == []
