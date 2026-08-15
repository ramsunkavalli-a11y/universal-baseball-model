"""Deterministic sampling helpers for source-certification audits."""

from __future__ import annotations

import polars as pl

from universal_baseball.source_comparison import select_diverse_game_ids


def select_game_ids_by_group(
    frame: pl.DataFrame,
    group_column: str,
    *,
    per_group: int = 1,
) -> dict[str, list[int]]:
    """Select date-spread game IDs within every observed nonblank group.

    This is meant for certification coverage, not statistical random sampling.
    Group labels come from the source rows themselves (for example
    ``league_name`` inside an upstream Rookie bucket), which lets us verify that
    a broad file label is not hiding materially different competitions.
    """

    if per_group <= 0:
        return {}
    required = {"game_pk", group_column}
    if not required.issubset(frame.columns):
        return {}

    values = sorted(
        {
            str(value).strip()
            for value in frame.get_column(group_column).drop_nulls().to_list()
            if str(value).strip()
        }
    )
    selected: dict[str, list[int]] = {}
    for value in values:
        subset = frame.filter(pl.col(group_column).cast(pl.String) == value)
        ids = select_diverse_game_ids(subset, limit=per_group)
        if ids:
            selected[value] = ids
    return selected
