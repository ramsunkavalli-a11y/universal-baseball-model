"""Direct league-season Performance-bin calibration from contextual RE24.

This module contains only the reproducible aggregation step between certified
Performance events and the level-specific pooling policy. It does not fetch
PBP, estimate run-expectancy matrices, choose game samples, or select shrinkage
strengths. Those concerns remain explicit upstream inputs / frozen policy.
"""

from __future__ import annotations

import polars as pl

from universal_baseball.performance_season import ALL_CORE_BINS


DIRECT_BIN_VALUE_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "league_id": pl.Int64,
    "core_bin": pl.String,
    "occurrence_count": pl.Int64,
    "mean_run_value": pl.Float64,
    "run_value_std_dev": pl.Float64,
    "standard_error": pl.Float64,
}


def summarize_direct_bin_values(events: pl.DataFrame) -> pl.DataFrame:
    """Estimate direct league-season-bin contextual value means.

    Required input is one row per valued Performance occurrence with ``re24``.
    Only the frozen 12-bin core taxonomy is accepted. Null ``re24`` values are
    excluded explicitly; callers should separately audit RE24 coverage before
    considering a calibration sample certified.
    """

    required = {"season", "league_id", "core_bin", "re24"}
    missing = sorted(required - set(events.columns))
    if missing:
        raise ValueError(f"bin calibration events missing columns: {missing}")
    if events.is_empty():
        return pl.DataFrame(schema=DIRECT_BIN_VALUE_SCHEMA)

    working = events.select(
        pl.col("season").cast(pl.Int64, strict=False),
        pl.col("league_id").cast(pl.Int64, strict=False),
        pl.col("core_bin").cast(pl.String),
        pl.col("re24").cast(pl.Float64, strict=False),
    ).drop_nulls(["season", "league_id", "core_bin"])

    invalid = working.filter(~pl.col("core_bin").is_in(list(ALL_CORE_BINS)))
    if not invalid.is_empty():
        raise ValueError("bin calibration events contain non-core Performance bins")

    valued = working.filter(pl.col("re24").is_not_null())
    if valued.is_empty():
        return pl.DataFrame(schema=DIRECT_BIN_VALUE_SCHEMA)

    result = (
        valued.group_by(["season", "league_id", "core_bin"])
        .agg(
            pl.len().alias("occurrence_count"),
            pl.col("re24").mean().alias("mean_run_value"),
            pl.col("re24").std(ddof=1).alias("run_value_std_dev"),
        )
        .with_columns(
            pl.when(pl.col("occurrence_count") > 1)
            .then(
                pl.col("run_value_std_dev")
                / pl.col("occurrence_count").cast(pl.Float64).sqrt()
            )
            .otherwise(pl.lit(None, dtype=pl.Float64))
            .alias("standard_error")
        )
        .cast(DIRECT_BIN_VALUE_SCHEMA, strict=True)
        .sort(["season", "league_id", "core_bin"])
    )
    return result


def bin_calibration_coverage(events: pl.DataFrame) -> pl.DataFrame:
    """Report RE24 availability by league-season-bin before direct aggregation."""

    required = {"season", "league_id", "core_bin", "re24"}
    missing = sorted(required - set(events.columns))
    if missing:
        raise ValueError(f"bin calibration events missing columns: {missing}")
    if events.is_empty():
        return pl.DataFrame(
            schema={
                "season": pl.Int64,
                "league_id": pl.Int64,
                "core_bin": pl.String,
                "event_count": pl.Int64,
                "valued_event_count": pl.Int64,
                "missing_re24_count": pl.Int64,
                "re24_coverage_rate": pl.Float64,
            }
        )

    return (
        events.select(
            pl.col("season").cast(pl.Int64, strict=False),
            pl.col("league_id").cast(pl.Int64, strict=False),
            pl.col("core_bin").cast(pl.String),
            pl.col("re24").cast(pl.Float64, strict=False),
        )
        .drop_nulls(["season", "league_id", "core_bin"])
        .group_by(["season", "league_id", "core_bin"])
        .agg(
            pl.len().alias("event_count"),
            pl.col("re24").is_not_null().cast(pl.Int64).sum().alias("valued_event_count"),
        )
        .with_columns(
            (pl.col("event_count") - pl.col("valued_event_count")).alias(
                "missing_re24_count"
            ),
            (pl.col("valued_event_count") / pl.col("event_count")).alias(
                "re24_coverage_rate"
            ),
        )
        .sort(["season", "league_id", "core_bin"])
    )
