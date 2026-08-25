import polars as pl
import pytest

from universal_baseball.hitter_v2_matchup_context import (
    add_strict_prior_pitcher_evidence,
    build_terminal_matchup_sidecar,
    reconcile_sidecar_to_player_games,
)


def _pitches() -> pl.DataFrame:
    return pl.DataFrame(
        [
            (1, 0, 1, "2024-04-01", 10, 100, "R", "L"),
            (1, 0, 2, "2024-04-01", 10, 100, "R", "L"),
            (1, 1, 1, "2024-04-01", 11, 100, "L", "L"),
            (2, 0, 1, "2024-04-02", 10, 100, "R", "L"),
        ],
        schema={
            "game_pk": pl.Int64,
            "at_bat_index": pl.Int64,
            "pitch_number": pl.Int64,
            "game_date": pl.String,
            "source_batter_id": pl.Int64,
            "pitcher_id": pl.Int64,
            "batter_side": pl.String,
            "pitcher_hand": pl.String,
        },
        orient="row",
    )


def _terminal() -> pl.DataFrame:
    return pl.DataFrame(
        [
            (1, 0, 2, 10, 103, "source_terminal_batter"),
            (1, 1, 1, 11, 103, "source_terminal_batter"),
            (2, 0, 1, 10, 103, "source_terminal_batter"),
        ],
        schema={
            "game_pk": pl.Int64,
            "at_bat_index": pl.Int64,
            "terminal_pitch_number": pl.Int64,
            "player_id": pl.Int64,
            "league_id": pl.Int64,
            "participant_authority": pl.String,
        },
        orient="row",
    )


def _sidecar() -> pl.DataFrame:
    return build_terminal_matchup_sidecar(
        _pitches(),
        _terminal(),
        season=2024,
        level_group="MLB",
        source_system="TEST",
        capability_tier="universal_pbp",
    )


def test_sidecar_uses_exact_terminal_pitch_and_is_unique() -> None:
    sidecar = _sidecar()
    assert sidecar.height == 3
    assert sidecar.select("game_pk", "at_bat_index").n_unique() == 3
    first = sidecar.filter((pl.col("game_pk") == 1) & (pl.col("at_bat_index") == 0))
    assert first["terminal_pitch_number"].item() == 2
    assert first["raw_terminal_row_count"].item() == 1
    assert first["matchup_ready"].item()


def test_sidecar_fails_closed_on_terminal_matchup_conflict() -> None:
    duplicate = _pitches().filter(
        (pl.col("game_pk") == 1)
        & (pl.col("at_bat_index") == 0)
        & (pl.col("pitch_number") == 2)
    ).with_columns(pl.lit(999, dtype=pl.Int64).alias("pitcher_id"))
    sidecar = build_terminal_matchup_sidecar(
        pl.concat([_pitches(), duplicate]),
        _terminal(),
        season=2024,
        level_group="MLB",
        source_system="TEST",
        capability_tier="universal_pbp",
    )
    conflicted = sidecar.filter(
        (pl.col("game_pk") == 1) & (pl.col("at_bat_index") == 0)
    )
    assert conflicted["pitcher_count"].item() == 2
    assert not conflicted["matchup_ready"].item()
    assert conflicted["matchup_fallback_reason"].item() == (
        "conflicting_terminal_source_rows"
    )


def test_prior_pitcher_evidence_excludes_same_date_and_future() -> None:
    sidecar = add_strict_prior_pitcher_evidence(_sidecar())
    same_day = sidecar.filter(pl.col("game_date") == pl.date(2024, 4, 1))
    next_day = sidecar.filter(pl.col("game_date") == pl.date(2024, 4, 2))
    assert same_day["prior_pitcher_pa"].to_list() == [0, 0]
    assert next_day["prior_pitcher_pa"].item() == 2

    future = _sidecar().with_columns(
        pl.when(pl.col("game_pk") == 2)
        .then(pl.date(2025, 4, 2))
        .otherwise(pl.col("game_date"))
        .alias("game_date")
    )
    before = add_strict_prior_pitcher_evidence(_sidecar()).filter(pl.col("game_pk") == 1)
    after = add_strict_prior_pitcher_evidence(future).filter(pl.col("game_pk") == 1)
    assert before["prior_pitcher_pa"].to_list() == after["prior_pitcher_pa"].to_list()

    outcome_ready = _sidecar().with_columns(
        (pl.col("player_id") == 10).alias("modeling_join_ready")
    )
    outcome_prior = add_strict_prior_pitcher_evidence(
        outcome_ready,
        evidence_ready_column="modeling_join_ready",
        output_column="prior_outcome_ready_pitcher_pa",
        date_count_column="outcome_ready_pitcher_pa_on_date",
    )
    assert outcome_prior.filter(pl.col("game_pk") == 2)[
        "prior_outcome_ready_pitcher_pa"
    ].item() == 1


def test_player_game_reconciliation_requires_exact_accepted_counts() -> None:
    sidecar = add_strict_prior_pitcher_evidence(_sidecar())
    player_games = pl.DataFrame(
        [
            (2024, 103, 1, 10, 1, "accepted_exact", True),
            (2024, 103, 1, 11, 1, "accepted_exact", True),
            (2024, 103, 2, 10, 2, "accepted_exact", True),
        ],
        schema={
            "season": pl.Int64,
            "league_id": pl.Int64,
            "game_id": pl.Int64,
            "player_id": pl.Int64,
            "accepted_terminal_pa": pl.Int64,
            "source_status": pl.String,
            "modeling_eligible": pl.Boolean,
        },
        orient="row",
    )
    attached, reconciliation = reconcile_sidecar_to_player_games(sidecar, player_games)
    assert attached.filter(pl.col("game_pk") == 1)["modeling_join_ready"].to_list() == [
        True,
        True,
    ]
    mismatch = reconciliation.filter(pl.col("game_id") == 2)
    assert not mismatch["sidecar_player_game_ready"].item()
    assert mismatch["sidecar_reconciliation_status"].item() == (
        "terminal_pa_count_mismatch"
    )


def test_duplicate_terminal_authority_fails() -> None:
    with pytest.raises(ValueError, match="terminal authority is not unique"):
        build_terminal_matchup_sidecar(
            _pitches(),
            pl.concat([_terminal(), _terminal().head(1)]),
            season=2024,
            level_group="MLB",
            source_system="TEST",
            capability_tier="universal_pbp",
        )
