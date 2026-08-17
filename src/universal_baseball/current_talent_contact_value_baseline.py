"""Efficient sufficient-statistics fit for the frozen Challenger-2 baseline.

The model is unchanged from ``fit_contact_value_baseline``:

    terminal_value ~ contact_bin + level_group

with one weight per event and fixed reference levels IFFB and MLB.  Because both
predictors are categorical, the event-level normal equations depend only on each
``contact_bin × level_group`` cell's event count and sum of terminal values.  This
module computes those exact sufficient statistics in Polars and solves the same
normal equations as the original row-wise implementation.

It exists only to make million-row pre-scoring fits practical.  It performs no
future scoring, no richer feature fitting, no 2023 access, and no model search.
"""

from __future__ import annotations

from datetime import date

import polars as pl

from universal_baseball.current_talent_contact_value import (
    CONTACT_VALUE_REFERENCE_BIN,
    CONTACT_VALUE_REFERENCE_LEVEL,
    ContactValueBaselineFit,
    _solve_full_rank_normal_equations,
)
from universal_baseball.performance_season import CONTACT_CORE_BINS


BASELINE_CELL_SCHEMA: dict[str, pl.DataType] = {
    "contact_bin": pl.String,
    "level_group": pl.String,
    "event_count": pl.Int64,
    "terminal_value_sum": pl.Float64,
}


def summarize_contact_value_baseline_cells(
    historical_contacts: pl.DataFrame,
    *,
    cutoff_date: date,
) -> tuple[pl.DataFrame, date, int]:
    """Return exact event-weighted cell sufficient statistics before ``cutoff``."""

    required = {"event_date", "contact_bin", "level_group", "terminal_value"}
    missing = sorted(required - set(historical_contacts.columns))
    if missing:
        raise ValueError(f"historical contact values missing fields: {missing}")

    working = historical_contacts.select(
        pl.col("event_date").cast(pl.Date, strict=False),
        pl.col("contact_bin").cast(pl.String),
        pl.col("level_group").cast(pl.String),
        pl.col("terminal_value").cast(pl.Float64, strict=False),
    )
    invalid = working.filter(
        pl.col("event_date").is_null()
        | pl.col("contact_bin").is_null()
        | pl.col("level_group").is_null()
        | pl.col("terminal_value").is_null()
        | ~pl.col("terminal_value").is_finite()
    )
    if not invalid.is_empty():
        raise ValueError("historical contact values contain invalid required fields")

    working = working.filter(pl.col("event_date") < pl.lit(cutoff_date))
    if working.is_empty():
        raise ValueError("contact-value baseline has no pre-cutoff training contacts")

    invalid_bins = working.filter(~pl.col("contact_bin").is_in(list(CONTACT_CORE_BINS)))
    if not invalid_bins.is_empty():
        values = sorted(invalid_bins.get_column("contact_bin").unique().to_list())
        raise ValueError(f"unsupported contact bins in baseline fit: {values}")

    max_event_date = working.get_column("event_date").max()
    if max_event_date >= cutoff_date:
        raise ValueError("contact-value baseline cell summary contains on/after-cutoff evidence")

    cells = (
        working.group_by("contact_bin", "level_group")
        .agg(
            pl.len().cast(pl.Int64).alias("event_count"),
            pl.col("terminal_value").sum().cast(pl.Float64).alias("terminal_value_sum"),
        )
        .sort("contact_bin", "level_group")
    )
    return cells, max_event_date, int(working.height)


def fit_contact_value_baseline_from_cells(
    cells: pl.DataFrame,
    *,
    cutoff_date: date,
    max_training_event_date: date,
    fitted_event_count: int | None = None,
) -> ContactValueBaselineFit:
    """Solve the frozen event-weighted additive OLS from exact cell statistics."""

    required = set(BASELINE_CELL_SCHEMA)
    missing = sorted(required - set(cells.columns))
    if missing:
        raise ValueError(f"contact-value baseline cells missing fields: {missing}")
    if cells.is_empty():
        raise ValueError("contact-value baseline cells are empty")
    if max_training_event_date >= cutoff_date:
        raise ValueError("contact-value baseline cells contain on/after-cutoff evidence")

    working = cells.select(
        pl.col("contact_bin").cast(pl.String),
        pl.col("level_group").cast(pl.String),
        pl.col("event_count").cast(pl.Int64, strict=False),
        pl.col("terminal_value_sum").cast(pl.Float64, strict=False),
    )
    invalid = working.filter(
        pl.col("contact_bin").is_null()
        | pl.col("level_group").is_null()
        | pl.col("event_count").is_null()
        | (pl.col("event_count") <= 0)
        | pl.col("terminal_value_sum").is_null()
        | ~pl.col("terminal_value_sum").is_finite()
    )
    if not invalid.is_empty():
        raise ValueError("contact-value baseline cells contain invalid sufficient statistics")

    duplicate_cells = (
        working.group_by("contact_bin", "level_group")
        .len()
        .filter(pl.col("len") > 1)
    )
    if not duplicate_cells.is_empty():
        raise ValueError("contact-value baseline cells contain duplicate bin-level cells")

    observed_bins = set(working.get_column("contact_bin").unique().to_list())
    invalid_bins = sorted(observed_bins - set(CONTACT_CORE_BINS))
    if invalid_bins:
        raise ValueError(f"unsupported contact bins in baseline cells: {invalid_bins}")
    if CONTACT_VALUE_REFERENCE_BIN not in observed_bins:
        raise ValueError("contact-value baseline training lacks reference IFFB events")

    observed_levels = set(working.get_column("level_group").unique().to_list())
    if CONTACT_VALUE_REFERENCE_LEVEL not in observed_levels:
        raise ValueError("contact-value baseline training lacks reference MLB events")

    bin_columns = [
        core_bin for core_bin in CONTACT_CORE_BINS if core_bin != CONTACT_VALUE_REFERENCE_BIN
    ]
    level_columns = sorted(
        level for level in observed_levels if level != CONTACT_VALUE_REFERENCE_LEVEL
    )
    parameter_count = 1 + len(bin_columns) + len(level_columns)
    xtx = [[0.0 for _ in range(parameter_count)] for _ in range(parameter_count)]
    xty = [0.0 for _ in range(parameter_count)]

    for row in working.iter_rows(named=True):
        contact_bin = str(row["contact_bin"])
        level_group = str(row["level_group"])
        weight = float(row["event_count"])
        value_sum = float(row["terminal_value_sum"])
        x = [1.0]
        x.extend(1.0 if contact_bin == core_bin else 0.0 for core_bin in bin_columns)
        x.extend(1.0 if level_group == level else 0.0 for level in level_columns)
        for left in range(parameter_count):
            xty[left] += x[left] * value_sum
            for right in range(parameter_count):
                xtx[left][right] += weight * x[left] * x[right]

    coefficients = _solve_full_rank_normal_equations(xtx, xty)
    contact_effects = {CONTACT_VALUE_REFERENCE_BIN: 0.0}
    contact_effects.update(
        {
            core_bin: float(coefficients[1 + index])
            for index, core_bin in enumerate(bin_columns)
        }
    )
    level_offset = 1 + len(bin_columns)
    level_effects = {CONTACT_VALUE_REFERENCE_LEVEL: 0.0}
    level_effects.update(
        {
            level: float(coefficients[level_offset + index])
            for index, level in enumerate(level_columns)
        }
    )

    cell_event_count = int(working.get_column("event_count").sum())
    if fitted_event_count is not None and int(fitted_event_count) != cell_event_count:
        raise ValueError(
            "contact-value baseline fitted_event_count disagrees with cell sufficient statistics"
        )

    return ContactValueBaselineFit(
        cutoff_date=cutoff_date,
        intercept=float(coefficients[0]),
        contact_bin_effects=contact_effects,
        level_group_effects=level_effects,
        fitted_event_count=cell_event_count,
        parameter_count=parameter_count,
        fitted_level_groups=tuple([CONTACT_VALUE_REFERENCE_LEVEL, *level_columns]),
        max_training_event_date=max_training_event_date,
    )


def fit_contact_value_baseline_sufficient_statistics(
    historical_contacts: pl.DataFrame,
    *,
    cutoff_date: date,
) -> tuple[ContactValueBaselineFit, pl.DataFrame]:
    """Fast exact equivalent of the frozen event-level baseline fit."""

    cells, max_event_date, event_count = summarize_contact_value_baseline_cells(
        historical_contacts,
        cutoff_date=cutoff_date,
    )
    fitted = fit_contact_value_baseline_from_cells(
        cells,
        cutoff_date=cutoff_date,
        max_training_event_date=max_event_date,
        fitted_event_count=event_count,
    )
    return fitted, cells
