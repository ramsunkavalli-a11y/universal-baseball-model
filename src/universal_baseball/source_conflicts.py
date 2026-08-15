"""Diagnostics for conflicting observations that claim the same source grain."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import polars as pl


DEFAULT_PITCH_KEY = ("game_pk", "at_bat_number", "pitch_number")


def profile_natural_key_conflicts(
    frame: pl.DataFrame,
    *,
    key: Sequence[str] = DEFAULT_PITCH_KEY,
    example_limit: int = 10,
) -> dict[str, Any]:
    """Profile distinct payloads that share a claimed natural key.

    Exact duplicate rows are removed before conflict analysis. A remaining key
    with more than one row therefore represents two or more distinct source
    payloads for the same claimed observation. This function only describes the
    conflict; it does not choose a winner or mutate the source.
    """

    key_columns = list(key)
    missing = [column for column in key_columns if column not in frame.columns]
    if missing:
        return {
            "available": False,
            "natural_key": key_columns,
            "missing_key_columns": missing,
        }

    exact_unique = frame.unique()
    key_groups = exact_unique.group_by(key_columns).len()
    conflict_groups = key_groups.filter(pl.col("len") > 1)

    base: dict[str, Any] = {
        "available": True,
        "natural_key": key_columns,
        "raw_rows": int(frame.height),
        "exact_unique_rows": int(exact_unique.height),
        "natural_key_unique_rows": int(key_groups.height),
        "conflicting_key_group_count": int(conflict_groups.height),
        "conflicting_key_extra_rows": int(
            conflict_groups.select((pl.col("len") - 1).sum()).item() or 0
        ),
    }

    if conflict_groups.is_empty():
        return {
            **base,
            "variant_count_distribution": {},
            "changed_column_group_counts": {},
            "top_changed_columns": [],
            "examples": [],
        }

    variant_distribution_rows = (
        conflict_groups.group_by("len")
        .agg(pl.len().alias("key_groups"))
        .sort("len")
        .to_dicts()
    )
    variant_distribution = {
        str(int(row["len"])): int(row["key_groups"])
        for row in variant_distribution_rows
    }

    conflicting_rows = exact_unique.join(
        conflict_groups.select(key_columns),
        on=key_columns,
        how="semi",
    )
    payload_columns = [
        column for column in exact_unique.columns if column not in key_columns
    ]

    if not payload_columns:
        return {
            **base,
            "variant_count_distribution": variant_distribution,
            "changed_column_group_counts": {},
            "top_changed_columns": [],
            "examples": [],
        }

    variation = conflicting_rows.group_by(key_columns).agg(
        [pl.col(column).n_unique().alias(column) for column in payload_columns]
    )
    count_row = variation.select(
        [
            (pl.col(column) > 1).sum().alias(column)
            for column in payload_columns
        ]
    ).to_dicts()[0]
    changed_counts = {
        column: int(count)
        for column, count in count_row.items()
        if int(count or 0) > 0
    }
    changed_counts = dict(
        sorted(changed_counts.items(), key=lambda item: (-item[1], item[0]))
    )

    examples: list[dict[str, Any]] = []
    for row in variation.head(max(example_limit, 0)).to_dicts():
        changed = [
            column
            for column in payload_columns
            if int(row.get(column) or 0) > 1
        ]
        examples.append(
            {
                **{column: row[column] for column in key_columns},
                "changed_columns": changed,
            }
        )

    return {
        **base,
        "variant_count_distribution": variant_distribution,
        "changed_column_group_counts": changed_counts,
        "top_changed_columns": [
            {"column": column, "conflicting_key_groups": count}
            for column, count in list(changed_counts.items())[:25]
        ],
        "examples": examples,
    }
