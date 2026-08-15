"""Deterministic coverage diagnostics for batted-ball direction evidence.

Reusable source releases can contain repeated observations of one natural pitch
key. This module never resolves an audited field by arbitrary row order: a field
is usable only when all non-null observations for the key agree. Conflicting
fields are counted and projected as null for coverage/comparison purposes.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from universal_baseball.batted_ball_direction import batted_ball_direction_expr


PITCH_KEY = ("game_pk", "at_bat_number", "pitch_number")
AUDITED_SOURCE_FIELDS = (
    "type",
    "bb_type",
    "hit_location",
    "hc_x",
    "hc_y",
    "stand",
)


def _nonblank_expr(column: str) -> pl.Expr:
    return pl.col(column).is_not_null() & (
        pl.col(column).cast(pl.String).str.strip_chars() != ""
    )


def field_location_direction_expr(
    hit_location: pl.Expr,
    stand: pl.Expr,
) -> pl.Expr:
    """Return a coarse diagnostic direction from fielder-location code.

    This is not a promoted baseball feature. Standard positions 5/6/7 are
    treated as the left-field third, 1/2/8 as center, and 3/4/9 as the
    right-field third. It exists only to test whether the broad stringer/fielder
    signal can plausibly act as a lower-confidence fallback when coordinates are
    structurally unavailable.
    """

    location = hit_location.cast(pl.Float64, strict=False).cast(pl.Int64, strict=False)
    left = location.is_in([5, 6, 7])
    center = location.is_in([1, 2, 8])
    right = location.is_in([3, 4, 9])
    valid = stand.is_in(["L", "R"]) & (left | center | right)
    pull = ((stand == "R") & left) | ((stand == "L") & right)

    return (
        pl.when(~valid)
        .then(pl.lit(None, dtype=pl.String))
        .when(center)
        .then(pl.lit("center"))
        .when(pull)
        .then(pl.lit("pull"))
        .otherwise(pl.lit("opposite"))
    )


def _stable_single_value_expr(field: str) -> pl.Expr:
    """Return a field value only when its non-null source observations agree."""

    values = pl.col(field).drop_nulls()
    return (
        pl.when(values.n_unique() <= 1)
        .then(values.first())
        .otherwise(pl.lit(None))
        .alias(field)
    )


def _field_conflict_expr(field: str) -> pl.Expr:
    return (pl.col(field).drop_nulls().n_unique() > 1).alias(f"{field}__conflict")


def collapse_direction_evidence(frame: pl.DataFrame) -> pl.DataFrame:
    """Collapse raw source observations to one deterministic row per pitch key.

    The natural key is preserved exactly. For each audited field, duplicate and
    repeated-snapshot observations are reduced only if all non-null values agree.
    A disagreement creates ``<field>__conflict=True`` and a null resolved value.
    This keeps the coverage audit independent of source row ordering.
    """

    missing_key = sorted(set(PITCH_KEY) - set(frame.columns))
    if missing_key:
        raise ValueError(f"source missing natural pitch key: {missing_key}")
    if "type" not in frame.columns:
        raise ValueError("source missing pitch result code column 'type'")

    fields = [field for field in AUDITED_SOURCE_FIELDS if field in frame.columns]
    aggregations: list[pl.Expr] = []
    for field in fields:
        aggregations.extend(
            [_stable_single_value_expr(field), _field_conflict_expr(field)]
        )

    return frame.group_by(list(PITCH_KEY)).agg(aggregations).sort(list(PITCH_KEY))


def _trajectory_breakdown(frame: pl.DataFrame) -> dict[str, int]:
    if "bb_type" not in frame.columns:
        return {}
    rows = (
        frame.filter(_nonblank_expr("bb_type"))
        .group_by("bb_type")
        .len()
        .sort(["len", "bb_type"], descending=[True, False])
        .to_dicts()
    )
    return {str(row["bb_type"]): int(row["len"]) for row in rows}


def _direction_counts(frame: pl.DataFrame, column: str) -> dict[str, int]:
    rows = (
        frame.filter(pl.col(column).is_not_null())
        .group_by(column)
        .len()
        .sort(column)
        .to_dicts()
    )
    return {str(row[column]): int(row["len"]) for row in rows}


def build_direction_coverage_report(frame: pl.DataFrame) -> dict[str, Any]:
    """Profile direction evidence among physical in-play pitch keys."""

    exact_unique = frame.unique()
    pitches = collapse_direction_evidence(exact_unique)

    conflict_counts: dict[str, int] = {}
    for field in AUDITED_SOURCE_FIELDS:
        conflict_column = f"{field}__conflict"
        if conflict_column in pitches.columns:
            conflict_counts[field] = pitches.filter(pl.col(conflict_column)).height
    conflict_columns = [
        f"{field}__conflict"
        for field in AUDITED_SOURCE_FIELDS
        if f"{field}__conflict" in pitches.columns
    ]
    conflicting_pitch_keys = (
        pitches.filter(pl.any_horizontal([pl.col(column) for column in conflict_columns])).height
        if conflict_columns
        else 0
    )

    # A conflicting/unknown pitch result cannot safely enter the denominator.
    bip = pitches.filter(pl.col("type").cast(pl.String) == "X")

    coordinate_available = {"hc_x", "hc_y", "stand"} <= set(bip.columns)
    location_available = {"hit_location", "stand"} <= set(bip.columns)

    bip = bip.with_columns(
        [
            batted_ball_direction_expr(
                pl.col("hc_x"), pl.col("hc_y"), pl.col("stand")
            ).alias("coordinate_direction")
            if coordinate_available
            else pl.lit(None, dtype=pl.String).alias("coordinate_direction"),
            field_location_direction_expr(
                pl.col("hit_location"), pl.col("stand")
            ).alias("location_direction")
            if location_available
            else pl.lit(None, dtype=pl.String).alias("location_direction"),
        ]
    )

    denominator = bip.height
    coverage_counts: dict[str, int] = {}
    for field in ("bb_type", "hit_location", "stand"):
        coverage_counts[field] = (
            bip.filter(_nonblank_expr(field)).height if field in bip.columns else 0
        )
    coverage_counts["hc_x_and_hc_y"] = (
        bip.filter(_nonblank_expr("hc_x") & _nonblank_expr("hc_y")).height
        if {"hc_x", "hc_y"} <= set(bip.columns)
        else 0
    )
    coverage_counts["coordinate_direction"] = bip.filter(
        pl.col("coordinate_direction").is_not_null()
    ).height
    coverage_counts["location_direction"] = bip.filter(
        pl.col("location_direction").is_not_null()
    ).height

    coverage_rates = {
        field: count / denominator if denominator else None
        for field, count in coverage_counts.items()
    }

    both = bip.filter(
        pl.col("coordinate_direction").is_not_null()
        & pl.col("location_direction").is_not_null()
    )
    agreements = both.filter(
        pl.col("coordinate_direction") == pl.col("location_direction")
    ).height

    agreement_by_trajectory: dict[str, Any] = {}
    if "bb_type" in both.columns:
        rows = (
            both.filter(_nonblank_expr("bb_type"))
            .group_by("bb_type")
            .agg(
                [
                    pl.len().alias("both_count"),
                    (pl.col("coordinate_direction") == pl.col("location_direction"))
                    .sum()
                    .alias("agreement_count"),
                ]
            )
            .sort(["both_count", "bb_type"], descending=[True, False])
            .to_dicts()
        )
        for row in rows:
            count = int(row["both_count"])
            matched = int(row["agreement_count"])
            agreement_by_trajectory[str(row["bb_type"])] = {
                "both_count": count,
                "agreement_count": matched,
                "agreement_rate": matched / count if count else None,
            }

    return {
        "raw_row_count": frame.height,
        "exact_unique_row_count": exact_unique.height,
        "natural_pitch_key_count": pitches.height,
        "in_play_pitch_key_count": denominator,
        "audited_field_conflicts": {
            "conflicting_pitch_key_count": conflicting_pitch_keys,
            "field_conflict_counts": conflict_counts,
        },
        "coverage_counts": coverage_counts,
        "coverage_rates": coverage_rates,
        "trajectory_counts": _trajectory_breakdown(bip),
        "coordinate_direction_counts": _direction_counts(bip, "coordinate_direction"),
        "location_direction_counts": _direction_counts(bip, "location_direction"),
        "coordinate_location_both_count": both.height,
        "coordinate_location_agreement_count": agreements,
        "coordinate_location_agreement_rate": (
            agreements / both.height if both.height else None
        ),
        "agreement_by_trajectory": agreement_by_trajectory,
    }
