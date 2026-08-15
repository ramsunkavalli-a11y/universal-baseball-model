"""Audit relationships between reusable source partitions.

These helpers answer whether upstream filenames behave like disjoint calendar
partitions, overlapping snapshots, or something else. They do not mutate or
repair source data.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import polars as pl


DEFAULT_NATURAL_KEY = ("game_pk", "at_bat_number", "pitch_number")


def _require_columns(frame: pl.DataFrame, columns: Sequence[str], label: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def _partition_profile(
    frame: pl.DataFrame,
    *,
    natural_key: Sequence[str],
) -> dict[str, Any]:
    _require_columns(frame, natural_key, "partition")

    exact_unique = frame.unique()
    key_counts = exact_unique.group_by(list(natural_key)).len()
    conflicting_groups = key_counts.filter(pl.col("len") > 1)

    profile: dict[str, Any] = {
        "raw_rows": int(frame.height),
        "exact_unique_rows": int(exact_unique.height),
        "exact_duplicate_extra_rows": int(frame.height - exact_unique.height),
        "unique_games": int(exact_unique.get_column("game_pk").n_unique()),
        "natural_key_groups_after_exact_dedup": int(key_counts.height),
        "conflicting_natural_key_groups": int(conflicting_groups.height),
        "rows_with_null_natural_key_component": int(
            exact_unique.select(
                pl.any_horizontal(
                    [pl.col(column).is_null() for column in natural_key]
                ).sum()
            ).item()
        ),
    }

    if "game_date" in exact_unique.columns:
        dates = exact_unique.get_column("game_date").drop_nulls()
        profile["min_game_date"] = dates.min() if len(dates) else None
        profile["max_game_date"] = dates.max() if len(dates) else None
        profile["game_month_values"] = (
            sorted(
                value
                for value in exact_unique.get_column("game_month")
                .drop_nulls()
                .unique()
                .to_list()
            )
            if "game_month" in exact_unique.columns
            else []
        )
        profile["rows_by_game_date"] = (
            exact_unique.group_by("game_date")
            .len()
            .sort("game_date")
            .to_dicts()
        )
    else:
        profile["min_game_date"] = None
        profile["max_game_date"] = None
        profile["game_month_values"] = []
        profile["rows_by_game_date"] = []

    return profile


def _changed_overlap_details(
    left_unique: pl.DataFrame,
    right_unique: pl.DataFrame,
    *,
    natural_key: Sequence[str],
    shared_columns: Sequence[str],
    example_limit: int = 10,
) -> dict[str, Any]:
    """Describe column-level differences for overlapping natural keys.

    The analysis is fully comparable only when each exact-deduplicated partition
    has one row per natural key. If either partition has internal key conflicts,
    callers still get the high-level overlap counts but this detailed comparison
    is withheld rather than choosing an arbitrary row.
    """

    left_key_counts = left_unique.group_by(list(natural_key)).len()
    right_key_counts = right_unique.group_by(list(natural_key)).len()
    if (
        left_key_counts.filter(pl.col("len") > 1).height
        or right_key_counts.filter(pl.col("len") > 1).height
    ):
        return {
            "available": False,
            "reason": "one or both partitions contain conflicting natural keys",
            "changed_column_counts": {},
            "examples": [],
        }

    non_key_columns = [
        column for column in shared_columns if column not in set(natural_key)
    ]
    if not non_key_columns:
        return {
            "available": True,
            "changed_column_counts": {},
            "examples": [],
        }

    joined = left_unique.join(
        right_unique,
        on=list(natural_key),
        how="inner",
        suffix="_right",
        nulls_equal=True,
    )
    if joined.is_empty():
        return {
            "available": True,
            "changed_column_counts": {},
            "examples": [],
        }

    flag_names = {column: f"__changed__{column}" for column in non_key_columns}
    flagged = joined.with_columns(
        [
            (~pl.col(column).eq_missing(pl.col(f"{column}_right"))).alias(
                flag_names[column]
            )
            for column in non_key_columns
        ]
    )
    any_changed = pl.any_horizontal(
        [pl.col(flag_names[column]) for column in non_key_columns]
    )
    changed_rows = flagged.filter(any_changed)

    changed_column_counts: dict[str, int] = {}
    for column in non_key_columns:
        count = int(flagged.select(pl.col(flag_names[column]).sum()).item())
        if count:
            changed_column_counts[column] = count

    # Order by frequency so the most systematic revisions are obvious first.
    changed_column_counts = dict(
        sorted(changed_column_counts.items(), key=lambda item: (-item[1], item[0]))
    )

    examples: list[dict[str, Any]] = []
    for row in changed_rows.sort(list(natural_key)).head(example_limit).to_dicts():
        changed_columns = [
            column for column in non_key_columns if row[flag_names[column]]
        ]
        values = {
            column: {
                "left": row.get(column),
                "right": row.get(f"{column}_right"),
            }
            for column in changed_columns
        }
        examples.append(
            {
                **{column: row.get(column) for column in natural_key},
                "changed_columns": changed_columns,
                "values": values,
            }
        )

    return {
        "available": True,
        "changed_column_counts": changed_column_counts,
        "examples": examples,
    }


def compare_adjacent_partitions(
    left: pl.DataFrame,
    right: pl.DataFrame,
    *,
    natural_key: Sequence[str] = DEFAULT_NATURAL_KEY,
) -> dict[str, Any]:
    """Compare two source files without assuming their filename partition semantics.

    Exact duplicate rows are removed independently *for comparison only*. The
    function then measures natural-key overlap and whether overlapping keys carry
    equivalent normalized row values at retrieval time.
    """

    _require_columns(left, natural_key, "left partition")
    _require_columns(right, natural_key, "right partition")

    if set(left.columns) != set(right.columns):
        left_only_columns = sorted(set(left.columns) - set(right.columns))
        right_only_columns = sorted(set(right.columns) - set(left.columns))
    else:
        left_only_columns = []
        right_only_columns = []

    shared_columns = [column for column in left.columns if column in right.columns]
    left_unique = left.select(shared_columns).unique()
    right_unique = right.select(shared_columns).unique()

    left_keys = left_unique.select(list(natural_key)).unique()
    right_keys = right_unique.select(list(natural_key)).unique()
    overlap_keys = left_keys.join(
        right_keys,
        on=list(natural_key),
        how="inner",
        nulls_equal=True,
    )
    overlap_key_count = int(overlap_keys.height)

    changed_detail = _changed_overlap_details(
        left_unique,
        right_unique,
        natural_key=natural_key,
        shared_columns=shared_columns,
    )

    if changed_detail["available"]:
        changed_overlap_keys = int(
            sum(
                1
                for _ in left_unique.join(
                    right_unique,
                    on=list(natural_key),
                    how="inner",
                    suffix="_right",
                    nulls_equal=True,
                )
                .with_columns(
                    [
                        (~pl.col(column).eq_missing(pl.col(f"{column}_right"))).alias(
                            f"__changed__{column}"
                        )
                        for column in shared_columns
                        if column not in set(natural_key)
                    ]
                )
                .filter(
                    pl.any_horizontal(
                        [
                            pl.col(f"__changed__{column}")
                            for column in shared_columns
                            if column not in set(natural_key)
                        ]
                    )
                )
                .select(list(natural_key))
                .unique()
                .iter_rows()
            )
        )
        identical_overlap_keys = overlap_key_count - changed_overlap_keys
    else:
        # Retain a conservative high-level classification when internal key
        # conflicts make one-to-one row comparison ambiguous.
        left_hashed = left_unique.with_columns(
            pl.struct(shared_columns).hash().alias("_row_hash")
        )
        right_hashed = right_unique.with_columns(
            pl.struct(shared_columns).hash().alias("_row_hash")
        )
        overlap_hashes = left_hashed.select([*natural_key, "_row_hash"]).join(
            right_hashed.select([*natural_key, "_row_hash"]),
            on=list(natural_key),
            how="inner",
            suffix="_right",
            nulls_equal=True,
        )
        identical_overlap_keys = int(
            overlap_hashes.filter(pl.col("_row_hash") == pl.col("_row_hash_right"))
            .select(list(natural_key))
            .unique()
            .height
        )
        changed_overlap_keys = overlap_key_count - identical_overlap_keys

    left_only_keys = left_keys.join(
        right_keys,
        on=list(natural_key),
        how="anti",
        nulls_equal=True,
    )
    right_only_keys = right_keys.join(
        left_keys,
        on=list(natural_key),
        how="anti",
        nulls_equal=True,
    )

    overlap_by_date: list[dict[str, Any]] = []
    if "game_date" in shared_columns and overlap_key_count:
        left_dates = left_unique.select([*natural_key, "game_date"]).unique()
        overlap_dates = overlap_keys.join(
            left_dates,
            on=list(natural_key),
            how="left",
            nulls_equal=True,
        )
        overlap_by_date = (
            overlap_dates.group_by("game_date")
            .len()
            .sort("game_date")
            .to_dicts()
        )

    return {
        "natural_key": list(natural_key),
        "left": _partition_profile(left, natural_key=natural_key),
        "right": _partition_profile(right, natural_key=natural_key),
        "schema": {
            "left_column_count": len(left.columns),
            "right_column_count": len(right.columns),
            "shared_column_count": len(shared_columns),
            "left_only_columns": left_only_columns,
            "right_only_columns": right_only_columns,
        },
        "overlap": {
            "natural_key_count": overlap_key_count,
            "identical_full_row_key_count": identical_overlap_keys,
            "changed_full_row_key_count": changed_overlap_keys,
            "left_only_natural_key_count": int(left_only_keys.height),
            "right_only_natural_key_count": int(right_only_keys.height),
            "natural_keys_by_game_date": overlap_by_date,
            "changed_row_detail": changed_detail,
        },
    }
