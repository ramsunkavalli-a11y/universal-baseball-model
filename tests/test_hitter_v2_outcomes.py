from datetime import date

import polars as pl
import pytest

from universal_baseball.hitter_v2_outcomes import (
    OFFICIAL_BATTING_FIELDS,
    TERMINAL_OUTCOMES,
    aggregate_player_season_outcomes,
    aggregate_terminal_contacts,
    assemble_player_game_outcomes,
    assert_outcome_invariants,
    project_official_player_game_outcomes,
    resolve_official_player_game_outcomes,
)


def _official_raw(*, hits: int = 3, pa: int = 17) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_id": [101],
            "game_date": ["2022-06-01"],
            "game_type": ["R"],
            "league_id": [130],
            "team_id": [10],
            "player_id": [7],
            "batting_PA": [pa],
            "batting_AB": [10],
            "batting_H": [hits],
            "batting_2B": [1],
            "batting_3B": [0],
            "batting_HR": [1],
            "batting_BB": [3],
            "batting_IBB": [1],
            "batting_HBP": [1],
            "batting_SO": [2],
            "batting_SF": [1],
            "batting_SH": [1],
            "batting_CI": [1],
            "batting_GiDP": [1],
            "batting_GiTP": [0],
        }
    )


def _contacts() -> pl.DataFrame:
    groups = ["HR", "2B", "1B", "ROE", "FC_REACH", "SF", "MULTI_OUT", "OUT", "OUT"]
    return pl.DataFrame(
        {
            "game_pk": [101] * len(groups),
            "at_bat_index": list(range(len(groups))),
            "league_id": [130] * len(groups),
            "player_id": [7] * len(groups),
            "terminal_outcome_group": groups,
            "terminal_outcome_status": ["supported"] * len(groups),
        }
    )


def _resolved(raw: pl.DataFrame) -> pl.DataFrame:
    projected = project_official_player_game_outcomes(
        raw, source_asset="probe.csv", season=2022
    )
    resolved, diagnostics = resolve_official_player_game_outcomes(projected)
    assert diagnostics["unresolved_player_game_count"] == 0
    return resolved


def test_exhaustive_player_game_and_player_season_accounting() -> None:
    contacts = aggregate_terminal_contacts(_contacts())
    player_games = assemble_player_game_outcomes(
        _resolved(_official_raw()), contacts, season=2022, level_group="rk"
    )

    assert player_games.height == 1
    row = player_games.row(0, named=True)
    assert {outcome: row[outcome] for outcome in TERMINAL_OUTCOMES} == {
        "UBB": 2,
        "IBB": 1,
        "HBP": 1,
        "K": 2,
        "HR": 1,
        "3B": 0,
        "2B": 1,
        "1B": 1,
        "ROE": 1,
        "FC_REACH": 1,
        "SF": 1,
        "MULTI_OUT": 1,
        "OTHER_OUT": 2,
        "SH_OR_SPECIAL": 2,
    }
    assert row["accepted_terminal_pa"] == row["batting_PA"] == 17
    assert row["hitter_talent_pa"] == 14
    assert row["source_status"] == "accepted_exact"
    assert_outcome_invariants(player_games)

    player_seasons = aggregate_player_season_outcomes(player_games)
    assert player_seasons.height == 1
    assert player_seasons.item(0, "batting_PA") == 17
    assert player_seasons.item(0, "HR") == 1


def test_official_snapshot_resolution_is_fail_closed_and_chronology_agnostic() -> None:
    first = _official_raw().with_columns(pl.lit(16).alias("batting_PA"))
    second = _official_raw()
    observations = pl.concat(
        [
            project_official_player_game_outcomes(first, source_asset="later_name.csv"),
            project_official_player_game_outcomes(second, source_asset="earlier_name.csv"),
        ]
    )
    resolved, diagnostics = resolve_official_player_game_outcomes(observations)
    assert resolved.item(0, "batting_PA") == 17
    assert resolved.item(0, "outcome_resolution") == "componentwise_dominance"
    assert diagnostics["resolved_by_componentwise_dominance_count"] == 1

    conflict = second.with_columns(
        pl.lit(16).alias("batting_PA"), pl.lit(4).alias("batting_H")
    )
    observations = pl.concat(
        [
            project_official_player_game_outcomes(second, source_asset="a.csv"),
            project_official_player_game_outcomes(conflict, source_asset="b.csv"),
        ]
    )
    resolved, diagnostics = resolve_official_player_game_outcomes(observations)
    assert resolved.item(0, "outcome_resolution") == "unresolved_nonmonotonic_conflict"
    assert all(resolved.item(0, field) is None for field in OFFICIAL_BATTING_FIELDS)
    assert diagnostics["unresolved_player_game_count"] == 1


def test_reconciliation_mismatch_is_retained_but_not_accepted() -> None:
    player_games = assemble_player_game_outcomes(
        _resolved(_official_raw(hits=4)),
        aggregate_terminal_contacts(_contacts()),
        season=2022,
        level_group="rk",
    )
    assert player_games.item(0, "hit_residual") == 1
    assert player_games.item(0, "source_status") == "failed_closed_reconciliation"
    with pytest.raises(ValueError, match="accepted outcome table cannot be empty"):
        assert_outcome_invariants(player_games)


def test_terminal_contact_contract_rejects_duplicates_and_unsupported_rows() -> None:
    duplicated = pl.concat([_contacts(), _contacts().head(1)])
    with pytest.raises(ValueError, match="not unique"):
        aggregate_terminal_contacts(duplicated)

    unsupported = _contacts().with_columns(
        pl.when(pl.col("at_bat_index") == 0)
        .then(pl.lit("UNKNOWN"))
        .otherwise(pl.col("terminal_outcome_group"))
        .alias("terminal_outcome_group")
    )
    with pytest.raises(ValueError, match="unsupported terminal contact groups"):
        aggregate_terminal_contacts(unsupported)


def test_projector_rejects_partial_schema_and_preserves_dates() -> None:
    with pytest.raises(ValueError, match="missing Hitter v2 outcome fields"):
        project_official_player_game_outcomes(_official_raw().drop("batting_IBB"), source_asset="x")
    resolved = _resolved(_official_raw())
    assert resolved.item(0, "game_date") == date(2022, 6, 1)
