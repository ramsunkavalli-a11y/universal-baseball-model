from datetime import UTC, datetime

import polars as pl

from universal_baseball.player_game_stats import (
    ArmstjcPlayerGameAsset,
    identify_unambiguous_contact_reassignments,
    parse_player_game_asset_name,
    project_player_game_batting,
    resolve_player_game_batting,
    validate_player_game_asset_inventory,
)


def test_parse_player_game_asset_name() -> None:
    assert parse_player_game_asset_name("2024_7_aaa_player_game_stats.csv") == (
        2024,
        7,
        "aaa",
    )
    assert parse_player_game_asset_name("2024_6_A+_player_game_stats.csv") == (
        2024,
        6,
        "a+",
    )
    assert parse_player_game_asset_name("2024_7_aaa_pbp.csv") is None


def test_inventory_rejects_duplicate_names() -> None:
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    asset = ArmstjcPlayerGameAsset(
        asset_id=1,
        name="2024_7_aaa_player_game_stats.csv",
        size_bytes=100,
        created_at_utc=timestamp,
        updated_at_utc=timestamp,
        browser_download_url="https://example.test/asset.csv",
        year=2024,
        filename_period=7,
        filename_level="aaa",
    )
    try:
        validate_player_game_asset_inventory([asset, asset])
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate inventory should fail")


def _raw_player_game_rows() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_id": [10, 10, 10],
            "game_date": ["2024-07-01"] * 3,
            "game_type": ["R"] * 3,
            "league_id": [117] * 3,
            "team_id": [1] * 3,
            "player_id": [100, 100, 101],
            "batting_PA": [4, 4, None],
            "batting_AB": [4, 4, None],
            "batting_SO": [1, 1, None],
            "batting_SF": [0, 0, None],
            "batting_SH": [0, 0, None],
        }
    )


def test_project_and_resolve_exact_duplicate_player_game_rows() -> None:
    projected = project_player_game_batting(
        _raw_player_game_rows(), source_asset="2024_7_aaa_player_game_stats.csv", season=2024
    )
    assert projected.filter(pl.col("player_id") == 100).get_column(
        "expected_contact_count"
    ).to_list() == [3, 3]
    assert projected.filter(pl.col("player_id") == 101).get_column(
        "expected_contact_count"
    ).to_list() == [0]

    resolved, diagnostics = resolve_player_game_batting(projected)
    assert diagnostics["raw_observation_count"] == 3
    assert diagnostics["exact_unique_observation_count"] == 2
    assert diagnostics["exact_duplicate_row_count"] == 1
    assert diagnostics["conflicting_player_game_count"] == 0
    assert diagnostics["resolved_by_componentwise_dominance_count"] == 0
    assert diagnostics["unresolved_conflicting_player_game_count"] == 0
    assert resolved.height == 2


def test_partial_contact_inputs_stay_unresolved() -> None:
    raw = _raw_player_game_rows().with_columns(
        pl.when(pl.col("player_id") == 100)
        .then(None)
        .otherwise(pl.col("batting_SF"))
        .alias("batting_SF")
    )
    projected = project_player_game_batting(raw, source_asset="test.csv", season=2024)
    assert projected.filter(pl.col("player_id") == 100).get_column(
        "expected_contact_count"
    ).null_count() == 2


def _single_player_game(
    *,
    pa: int | None,
    ab: int | None,
    so: int | None,
    sf: int | None,
    sh: int | None,
) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_id": [20],
            "game_date": ["2024-07-24"],
            "game_type": ["R"],
            "league_id": [117],
            "team_id": [1],
            "player_id": [200],
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


def test_blank_snapshot_resolves_to_unique_complete_cumulative_snapshot() -> None:
    blank = project_player_game_batting(
        _single_player_game(pa=None, ab=None, so=None, sf=None, sh=None),
        source_asset="2024_6_aaa_player_game_stats.csv",
        season=2024,
    )
    complete = project_player_game_batting(
        _single_player_game(pa=4, ab=4, so=1, sf=0, sh=0),
        source_asset="2024_7_aaa_player_game_stats.csv",
        season=2024,
    )
    resolved, diagnostics = resolve_player_game_batting(
        pl.concat([blank, complete], how="vertical_relaxed")
    )
    row = resolved.row(0, named=True)
    assert row["expected_contact_count"] == 3
    assert row["player_game_resolution"] == "componentwise_dominance"
    assert row["resolved_by_componentwise_dominance"] is True
    assert diagnostics["conflicting_player_game_count"] == 1
    assert diagnostics["resolved_by_componentwise_dominance_count"] == 1
    assert diagnostics["unresolved_conflicting_player_game_count"] == 0


def test_nonmonotonic_snapshot_conflict_remains_unresolved() -> None:
    first = project_player_game_batting(
        _single_player_game(pa=4, ab=4, so=1, sf=0, sh=0),
        source_asset="first.csv",
        season=2024,
    )
    # More PA but fewer AB: neither vector can be a cumulative continuation of
    # the other, so filename/order must not break the tie.
    second = project_player_game_batting(
        _single_player_game(pa=5, ab=3, so=1, sf=1, sh=0),
        source_asset="second.csv",
        season=2024,
    )
    resolved, diagnostics = resolve_player_game_batting(
        pl.concat([first, second], how="vertical_relaxed")
    )
    row = resolved.row(0, named=True)
    assert row["expected_contact_count"] is None
    assert row["player_game_resolution"] == "unresolved_nonmonotonic_conflict"
    assert diagnostics["conflicting_player_game_count"] == 1
    assert diagnostics["resolved_by_componentwise_dominance_count"] == 0
    assert diagnostics["unresolved_conflicting_player_game_count"] == 1


def test_identify_only_strict_unambiguous_reassignment() -> None:
    comparison = pl.DataFrame(
        {
            "game_id": [1, 1, 2, 2, 3, 3],
            "player_id": [11, 12, 21, 22, 31, 32],
            "source_contact_count": [1, 3, 2, 3, 1, 3],
            "expected_contact_count": [0, 4, 1, 4, 0, 5],
            "difference": [1, -1, 1, -1, 1, -2],
        }
    )
    repairs = identify_unambiguous_contact_reassignments(comparison)
    assert repairs.to_dicts() == [
        {"game_id": 1, "source_batter_id": 11, "reassigned_batter_id": 12}
    ]
