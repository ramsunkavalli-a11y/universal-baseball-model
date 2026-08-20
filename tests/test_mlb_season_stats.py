from __future__ import annotations

import json

import pytest
import requests

import universal_baseball.mlb_season_stats as mlb_season_stats
from universal_baseball.mlb_season_stats import (
    MLB_BATTING_BACKBONE_SCHEMA,
    MLB_PITCHING_BACKBONE_SCHEMA,
    capture_manifest,
    project_mlb_hitting_splits,
    project_mlb_pitching_splits,
)
from universal_baseball.pitching_performance import build_pitching_performance


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
        "stolenBases": 8,
        "caughtStealing": 2,
        "groundIntoDoublePlay": 4,
    }
    stat.update(overrides)
    return {
        "player": {"id": player_id, "fullName": f"Player {player_id}"},
        "stat": stat,
    }


def _pitching_split(player_id: int, **overrides):
    stat = {
        "gamesPlayed": 20,
        "gamesStarted": 12,
        "battersFaced": 300,
        "strikeOuts": 80,
        "baseOnBalls": 25,
        "intentionalWalks": 2,
        "hitBatsmen": 4,
        "homeRuns": 10,
    }
    stat.update(overrides)
    return {
        "player": {"id": player_id, "fullName": f"Pitcher {player_id}"},
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
    assert row["batting_stolen_bases"] == 8
    assert row["batting_caught_stealing"] == 2
    assert row["batting_ground_into_double_play"] == 4
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


def test_missing_certified_baserunning_field_fails_loudly() -> None:
    split = _split(101)
    del split["stat"]["caughtStealing"]
    with pytest.raises(ValueError, match="caughtStealing"):
        project_mlb_hitting_splits([split], season=2024, league_id=103)


def test_duplicate_player_league_season_is_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        project_mlb_hitting_splits(
            [_split(101), _split(101)], season=2024, league_id=103
        )


def test_unknown_actual_league_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported MLB actual league"):
        project_mlb_hitting_splits([_split(101)], season=2024, league_id=999)


def test_mlb_pitching_projection_matches_universal_performance_contract() -> None:
    frame = project_mlb_pitching_splits(
        [_pitching_split(201)], season=2024, league_id=103
    )
    assert frame.schema == MLB_PITCHING_BACKBONE_SCHEMA
    row = frame.to_dicts()[0]
    assert row["pitching_batters_faced"] == 300
    assert row["pitching_games_started"] == 12
    assert row["pitching_intentional_walks"] == 2

    performance = build_pitching_performance(frame)
    summary = performance.summary.to_dicts()[0]
    assert summary["pitching_unintentional_walks"] == 23
    assert summary["pitching_other_batters_faced"] == 183
    assert summary["pitching_profile_event_count"] == 300


def test_mlb_pitching_projection_fails_on_missing_or_inconsistent_counts() -> None:
    missing = _pitching_split(201)
    del missing["stat"]["hitBatsmen"]
    with pytest.raises(ValueError, match="missing fields.*hitBatsmen"):
        project_mlb_pitching_splits([missing], season=2024, league_id=103)

    with pytest.raises(ValueError, match="IBB exceeds BB"):
        project_mlb_pitching_splits(
            [_pitching_split(201, baseOnBalls=1, intentionalWalks=2)],
            season=2024,
            league_id=103,
        )


def test_mlb_pitching_projection_rejects_duplicate_canonical_grain() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        project_mlb_pitching_splits(
            [_pitching_split(201), _pitching_split(201)],
            season=2024,
            league_id=104,
        )


def test_capture_manifest_is_stable_json() -> None:
    # No captures is still a deterministic serializable provenance object.
    assert json.loads(capture_manifest([])) == []


class _FakeResponse:
    def __init__(self, status_code: int = 200):
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status={self.status_code}")


class _TimeoutThenSuccessSession:
    def __init__(self):
        self.calls = 0

    def get(self, *_args, **_kwargs):
        self.calls += 1
        if self.calls == 1:
            raise requests.ReadTimeout("transient")
        return _FakeResponse(200)


class _BadGatewayThenSuccessSession:
    def __init__(self):
        self.calls = 0

    def get(self, *_args, **_kwargs):
        self.calls += 1
        return _FakeResponse(502 if self.calls == 1 else 200)


def test_statsapi_transport_timeout_is_retried(monkeypatch) -> None:
    monkeypatch.setattr(mlb_season_stats.time, "sleep", lambda _seconds: None)
    session = _TimeoutThenSuccessSession()
    response = mlb_season_stats._statsapi_get_with_retry(
        session,
        "https://statsapi.mlb.com/api/v1/teams",
        params={"sportId": 1, "season": 2023},
        timeout_seconds=1,
        attempts=2,
    )
    assert response.status_code == 200
    assert session.calls == 2


def test_statsapi_retryable_502_is_retried(monkeypatch) -> None:
    monkeypatch.setattr(mlb_season_stats.time, "sleep", lambda _seconds: None)
    session = _BadGatewayThenSuccessSession()
    response = mlb_season_stats._statsapi_get_with_retry(
        session,
        "https://statsapi.mlb.com/api/v1/stats",
        params={"season": 2023},
        timeout_seconds=1,
        attempts=2,
    )
    assert response.status_code == 200
    assert session.calls == 2
