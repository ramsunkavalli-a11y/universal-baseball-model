"""Contact-control view of reusable player-game batting snapshots.

The general player-game resolver correctly treats every metadata disagreement as
unresolved because those fields may matter to other consumers. Contact identity
control needs a narrower contract: after rows have already been restricted to a
season and regular-season game type, only actual league identity is required to
compare ``game_id + player_id`` contact counts with reusable PBP.

Historical 2024 audits exposed suspended/resumed or corrected game snapshots in
which ``game_date`` changed while game ID, league, and batting totals remained a
valid cumulative sequence. A small number of player rows also carried differing
``team_id`` values while league and batting evidence remained resolvable. Those
metadata differences must remain explicit, but they should not erase an
otherwise unique contact count.

This module therefore masks only *non-blocking* metadata conflicts
(``game_date`` and ``team_id``) before delegating batting-vector resolution to
the conservative base resolver. ``game_type`` and ``league_id`` conflicts remain
hard blockers. No filename/upload chronology is introduced.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from universal_baseball.player_game_stats import (
    PLAYER_GAME_KEY,
    resolve_player_game_batting,
)


NONBLOCKING_CONTACT_CONTROL_METADATA = ("game_date", "team_id")
BLOCKING_CONTACT_CONTROL_METADATA = ("game_type", "league_id")


def _metadata_conflict_flags(observations: pl.DataFrame) -> pl.DataFrame:
    required = {
        *PLAYER_GAME_KEY,
        *NONBLOCKING_CONTACT_CONTROL_METADATA,
        *BLOCKING_CONTACT_CONTROL_METADATA,
    }
    missing = sorted(required - set(observations.columns))
    if missing:
        raise ValueError(f"player-game observations missing contact-control metadata: {missing}")

    aggregations: list[pl.Expr] = []
    for field in (*NONBLOCKING_CONTACT_CONTROL_METADATA, *BLOCKING_CONTACT_CONTROL_METADATA):
        aggregations.append(
            pl.col(field).drop_nulls().n_unique().alias(f"{field}_value_count")
        )
    return (
        observations.group_by(PLAYER_GAME_KEY)
        .agg(*aggregations)
        .with_columns(
            *[
                (pl.col(f"{field}_value_count") > 1).alias(f"{field}_conflict")
                for field in (
                    *NONBLOCKING_CONTACT_CONTROL_METADATA,
                    *BLOCKING_CONTACT_CONTROL_METADATA,
                )
            ]
        )
        .with_columns(
            pl.any_horizontal(
                [pl.col(f"{field}_conflict") for field in NONBLOCKING_CONTACT_CONTROL_METADATA]
            ).alias("nonblocking_metadata_conflict"),
            pl.any_horizontal(
                [pl.col(f"{field}_conflict") for field in BLOCKING_CONTACT_CONTROL_METADATA]
            ).alias("blocking_metadata_conflict"),
        )
        .sort(PLAYER_GAME_KEY)
    )


def resolve_player_game_contact_controls(
    observations: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Resolve reusable player-game batting for contact-identity control.

    ``game_date`` and ``team_id`` conflicts are retained as flags and resolved
    metadata values become null, but they do not block a unique cumulative
    batting vector. ``game_type`` and ``league_id`` disagreements are left
    untouched so the base resolver continues to reject them.
    """

    if observations.is_empty():
        raise ValueError("player-game contact-control observations cannot be empty")

    flags = _metadata_conflict_flags(observations)
    nonblocking_keys = flags.filter(pl.col("nonblocking_metadata_conflict")).select(
        PLAYER_GAME_KEY
    )

    normalized = observations
    if not nonblocking_keys.is_empty():
        normalized = normalized.join(
            nonblocking_keys.with_columns(pl.lit(True).alias("_mask_nonblocking_metadata")),
            on=PLAYER_GAME_KEY,
            how="left",
        ).with_columns(
            *[
                pl.when(pl.col("_mask_nonblocking_metadata").fill_null(False))
                .then(pl.lit(None, dtype=observations.schema[field]))
                .otherwise(pl.col(field))
                .alias(field)
                for field in NONBLOCKING_CONTACT_CONTROL_METADATA
            ]
        ).drop("_mask_nonblocking_metadata")

    resolved, base_diagnostics = resolve_player_game_batting(normalized)
    resolved = resolved.join(
        flags.select(
            *PLAYER_GAME_KEY,
            *[
                pl.col(f"{field}_conflict")
                for field in (
                    *NONBLOCKING_CONTACT_CONTROL_METADATA,
                    *BLOCKING_CONTACT_CONTROL_METADATA,
                )
            ],
            "nonblocking_metadata_conflict",
            "blocking_metadata_conflict",
        ),
        on=PLAYER_GAME_KEY,
        how="left",
    ).with_columns(
        *[
            pl.col(column).fill_null(False)
            for column in (
                "game_date_conflict",
                "team_id_conflict",
                "game_type_conflict",
                "league_id_conflict",
                "nonblocking_metadata_conflict",
                "blocking_metadata_conflict",
            )
        ]
    )

    # A masked non-blocking metadata conflict should no longer create an
    # unresolved contact count. Anything still unresolved remains a genuine
    # batting-vector or blocking-metadata problem and must fail downstream.
    diagnostics: dict[str, Any] = {
        **base_diagnostics,
        "game_date_conflict_player_game_count": flags.filter(
            pl.col("game_date_conflict")
        ).height,
        "team_id_conflict_player_game_count": flags.filter(
            pl.col("team_id_conflict")
        ).height,
        "game_type_conflict_player_game_count": flags.filter(
            pl.col("game_type_conflict")
        ).height,
        "league_id_conflict_player_game_count": flags.filter(
            pl.col("league_id_conflict")
        ).height,
        "nonblocking_metadata_conflict_player_game_count": flags.filter(
            pl.col("nonblocking_metadata_conflict")
        ).height,
        "blocking_metadata_conflict_player_game_count": flags.filter(
            pl.col("blocking_metadata_conflict")
        ).height,
        "resolved_contact_control_count": resolved.filter(
            pl.col("expected_contact_count").is_not_null()
        ).height,
        "unresolved_contact_control_count": resolved.filter(
            pl.col("expected_contact_count").is_null()
        ).height,
    }
    return resolved, diagnostics
