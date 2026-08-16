from __future__ import annotations

import polars as pl

from universal_baseball.player_game_controls import resolve_player_game_contact_controls
from universal_baseball.player_game_stats import project_player_game_batting


def _raw(
    *,
    game_date: str = "2024-07-01",
    game_type: str = "R",
    league_id: int = 117,
    team_id: int = 1,
    pa: int | None = 4,
    ab: int | None = 4,
    so: int | None = 1,
    sf: int | None = 0,
    sh: int | None = 0,
) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_id": [10],
            "game_date": [game_date],
            "game_type": [game_type],
            "league_id": [league_id],
            "team_id": [team_id],
            "player_id": [100],
            "batting_PA": [pa],
            "batting_AB": [ab],
            "batting_SO": [so],
            "batting_SF": [sf],
            "batting_SH": [sh],
        },
        schema_overrides={
            "batting_PA": pl.Int64,
            "batting_AB": pl.Int64,
            "batting_SO": pl.Int64,
            "batting_SF": pl.Int64,
            "batting_SH": pl.Int64,
        },
    )


def _project(raw: pl.DataFrame, asset: str) -> pl.DataFrame:
    return project_player_game_batting(raw, source_asset=asset, season=2024, game_type=None)


def test_game_date_conflict_does_not_erase_unique_contact_count() -> None:
    first = _project(_raw(game_date="2024-07-28"), "july.csv")
    second = _project(
        _raw(game_date="2024-08-14", pa=5, ab=5, so=1), "august.csv"
    )
    resolved, diagnostics = resolve_player_game_contact_controls(
        pl.concat([first, second], how="vertical_relaxed")
    )
    row = resolved.to_dicts()[0]
    assert row["expected_contact_count"] == 4
    assert row["game_date"] is None
    assert row["game_date_conflict"] is True
    assert row["nonblocking_metadata_conflict"] is True
    assert row["blocking_metadata_conflict"] is False
    assert diagnostics["game_date_conflict_player_game_count"] == 1
    assert diagnostics["unresolved_contact_control_count"] == 0


def test_team_id_conflict_is_explicit_but_nonblocking_for_contact_control() -> None:
    first = _project(_raw(team_id=1), "first.csv")
    second = _project(_raw(team_id=2), "second.csv")
    resolved, diagnostics = resolve_player_game_contact_controls(
        pl.concat([first, second], how="vertical_relaxed")
    )
    row = resolved.to_dicts()[0]
    assert row["expected_contact_count"] == 3
    assert row["team_id"] is None
    assert row["team_id_conflict"] is True
    assert row["player_game_resolution"] == "consensus"
    assert diagnostics["unresolved_contact_control_count"] == 0


def test_nonblocking_metadata_conflict_and_cumulative_batting_change_resolve_together() -> None:
    blank = _project(
        _raw(game_date="2024-07-28", pa=None, ab=None, so=None, sf=None, sh=None),
        "first.csv",
    )
    complete = _project(
        _raw(game_date="2024-08-14", pa=4, ab=4, so=1, sf=0, sh=0),
        "second.csv",
    )
    resolved, diagnostics = resolve_player_game_contact_controls(
        pl.concat([blank, complete], how="vertical_relaxed")
    )
    row = resolved.to_dicts()[0]
    assert row["expected_contact_count"] == 3
    assert row["player_game_resolution"] == "componentwise_dominance"
    assert row["game_date_conflict"] is True
    assert diagnostics["resolved_by_componentwise_dominance_count"] == 1
    assert diagnostics["unresolved_contact_control_count"] == 0


def test_league_conflict_remains_a_hard_blocker() -> None:
    first = _project(_raw(league_id=117), "first.csv")
    second = _project(_raw(league_id=112), "second.csv")
    resolved, diagnostics = resolve_player_game_contact_controls(
        pl.concat([first, second], how="vertical_relaxed")
    )
    row = resolved.to_dicts()[0]
    assert row["expected_contact_count"] is None
    assert row["league_id_conflict"] is True
    assert row["blocking_metadata_conflict"] is True
    assert diagnostics["blocking_metadata_conflict_player_game_count"] == 1
    assert diagnostics["unresolved_contact_control_count"] == 1
