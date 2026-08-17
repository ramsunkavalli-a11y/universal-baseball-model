"""Deterministic primitives for Current Talent richer challenger 2.

This module implements only the frozen mathematics needed before the 2022
contact-value development evaluator is allowed to exist:

- the accepted pre-2021-07-15 MLB terminal-outcome value scale;
- a cutoff-safe additive OLS control on contact bin + level group; and
- a two-feature, no-intercept weighted least-squares player residual.

It performs no development-fold selection and imports no 2023 evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import Any

import polars as pl

from universal_baseball.performance_season import CONTACT_CORE_BINS


CONTACT_VALUE_METHOD = "baseline2_plus_ev_sweet_spot_contact_value_residual_v1"
CONTACT_VALUE_REFERENCE_BIN = "IFFB"
CONTACT_VALUE_REFERENCE_LEVEL = "MLB"

FROZEN_TERMINAL_OUTCOME_VALUES: dict[str, float] = {
    "1B": 0.4651970407443663,
    "2B": 0.7665843002990237,
    "3B": 1.0004100521698496,
    "HR": 1.3834396983847337,
    "ROE": 0.43273757678346964,
    "FC_REACH": 0.1558534038205505,
    "SF": -0.06260868067734615,
    "MULTI_OUT": -0.8151401718384932,
    "OUT": -0.24975231369042597,
}
FROZEN_TERMINAL_OUTCOME_GROUPS = tuple(FROZEN_TERMINAL_OUTCOME_VALUES)


@dataclass(frozen=True, slots=True)
class ContactValueBaselineFit:
    """Additive OLS fit for ``terminal_value ~ contact_bin + level_group``."""

    cutoff_date: date
    intercept: float
    contact_bin_effects: dict[str, float]
    level_group_effects: dict[str, float]
    fitted_event_count: int
    parameter_count: int
    fitted_level_groups: tuple[str, ...]
    max_training_event_date: date

    def __post_init__(self) -> None:
        if self.fitted_event_count <= 0:
            raise ValueError("contact-value baseline requires positive fitted_event_count")
        if self.parameter_count <= 0:
            raise ValueError("contact-value baseline requires positive parameter_count")
        if not isfinite(self.intercept):
            raise ValueError("contact-value baseline intercept must be finite")
        if self.max_training_event_date >= self.cutoff_date:
            raise ValueError("contact-value baseline contains on/after-cutoff training evidence")
        if self.contact_bin_effects.get(CONTACT_VALUE_REFERENCE_BIN) != 0.0:
            raise ValueError("reference contact-bin effect must be exactly zero")
        if self.level_group_effects.get(CONTACT_VALUE_REFERENCE_LEVEL) != 0.0:
            raise ValueError("reference level-group effect must be exactly zero")


@dataclass(frozen=True, slots=True)
class ContactValueResidualFit:
    """Frozen two-feature no-intercept WLS fit."""

    beta_mean_exit_velocity: float
    beta_sweet_spot_share: float
    fitted_player_count: int
    fitted_future_contact_count: int
    determinant: float

    def __post_init__(self) -> None:
        if self.fitted_player_count < 2:
            raise ValueError("contact-value residual fit requires at least two training players")
        if self.fitted_future_contact_count <= 0:
            raise ValueError("contact-value residual fit requires positive future-contact weight")
        if not all(
            isfinite(value)
            for value in (
                self.beta_mean_exit_velocity,
                self.beta_sweet_spot_share,
                self.determinant,
            )
        ):
            raise ValueError("contact-value residual fit must be finite")
        if self.determinant <= 0:
            raise ValueError("contact-value residual fit must be full rank")


def _require_columns(frame: pl.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing fields: {missing}")


def attach_frozen_terminal_values(
    events: pl.DataFrame,
    *,
    group_column: str = "terminal_outcome_group",
    output_column: str = "terminal_value",
    require_supported: bool = True,
) -> pl.DataFrame:
    """Attach the accepted nine-group MLB-scale values.

    Unknown non-null groups always fail closed. Null groups are allowed only when
    ``require_supported=False`` so a caller can retain them for diagnostics before
    symmetric target exclusion.
    """

    _require_columns(events, {group_column}, "terminal contact events")
    groups = events.get_column(group_column).cast(pl.String, strict=False)
    unknown = sorted(
        {
            str(value)
            for value in groups.drop_nulls().unique().to_list()
            if str(value) not in FROZEN_TERMINAL_OUTCOME_VALUES
        }
    )
    if unknown:
        raise ValueError(f"unsupported terminal outcome groups: {unknown}")
    if require_supported and groups.null_count():
        raise ValueError("terminal contact events contain unsupported/null outcome group")

    mapping = pl.DataFrame(
        {
            group_column: list(FROZEN_TERMINAL_OUTCOME_VALUES),
            output_column: list(FROZEN_TERMINAL_OUTCOME_VALUES.values()),
        },
        schema={group_column: pl.String, output_column: pl.Float64},
    )
    result = events.with_columns(pl.col(group_column).cast(pl.String, strict=False)).join(
        mapping,
        on=group_column,
        how="left",
        validate="m:1",
    )
    if require_supported and result.get_column(output_column).null_count():
        raise ValueError("terminal contact value assignment is incomplete")
    return result


def _solve_full_rank_normal_equations(
    matrix: list[list[float]],
    vector: list[float],
    *,
    pivot_tolerance: float = 1e-12,
) -> list[float]:
    """Solve a small symmetric normal-equation system by pivoted elimination."""

    size = len(vector)
    if size == 0 or len(matrix) != size or any(len(row) != size for row in matrix):
        raise ValueError("linear system must be nonempty and square")
    if pivot_tolerance <= 0:
        raise ValueError("pivot_tolerance must be positive")

    augmented = [
        [float(matrix[row][column]) for column in range(size)] + [float(vector[row])]
        for row in range(size)
    ]
    scale = max((abs(value) for row in matrix for value in row), default=0.0)
    if scale <= 0 or not isfinite(scale):
        raise ValueError("contact-value linear system has no finite information")
    threshold = pivot_tolerance * max(1.0, scale)

    for column in range(size):
        pivot_row = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        pivot = augmented[pivot_row][column]
        if not isfinite(pivot) or abs(pivot) <= threshold:
            raise ValueError("contact-value linear system is rank deficient")
        if pivot_row != column:
            augmented[column], augmented[pivot_row] = augmented[pivot_row], augmented[column]

        pivot = augmented[column][column]
        for index in range(column, size + 1):
            augmented[column][index] /= pivot

        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            if factor == 0:
                continue
            for index in range(column, size + 1):
                augmented[row][index] -= factor * augmented[column][index]

    solution = [augmented[row][size] for row in range(size)]
    if any(not isfinite(value) for value in solution):
        raise ValueError("contact-value linear solve produced non-finite coefficients")
    return solution


def fit_contact_value_baseline(
    historical_contacts: pl.DataFrame,
    *,
    cutoff_date: date,
) -> ContactValueBaselineFit:
    """Fit the frozen additive pre-cutoff contact-bin + level OLS control.

    Rows on or after ``cutoff_date`` are deterministically excluded. All retained
    rows receive one event weight. Reference coding is fixed at IFFB and MLB.
    """

    _require_columns(
        historical_contacts,
        {"event_date", "contact_bin", "level_group", "terminal_value"},
        "historical contact values",
    )
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

    observed_bins = set(working.get_column("contact_bin").unique().to_list())
    observed_levels = set(working.get_column("level_group").unique().to_list())
    if CONTACT_VALUE_REFERENCE_BIN not in observed_bins:
        raise ValueError("contact-value baseline training lacks reference IFFB events")
    if CONTACT_VALUE_REFERENCE_LEVEL not in observed_levels:
        raise ValueError("contact-value baseline training lacks reference MLB events")

    bin_columns = [
        core_bin for core_bin in CONTACT_CORE_BINS if core_bin != CONTACT_VALUE_REFERENCE_BIN
    ]
    level_columns = sorted(level for level in observed_levels if level != CONTACT_VALUE_REFERENCE_LEVEL)
    parameter_count = 1 + len(bin_columns) + len(level_columns)
    xtx = [[0.0 for _ in range(parameter_count)] for _ in range(parameter_count)]
    xty = [0.0 for _ in range(parameter_count)]

    for row in working.iter_rows(named=True):
        contact_bin = str(row["contact_bin"])
        level_group = str(row["level_group"])
        y = float(row["terminal_value"])
        x = [1.0]
        x.extend(1.0 if contact_bin == core_bin else 0.0 for core_bin in bin_columns)
        x.extend(1.0 if level_group == level else 0.0 for level in level_columns)
        for left in range(parameter_count):
            xty[left] += x[left] * y
            for right in range(parameter_count):
                xtx[left][right] += x[left] * x[right]

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
    return ContactValueBaselineFit(
        cutoff_date=cutoff_date,
        intercept=float(coefficients[0]),
        contact_bin_effects=contact_effects,
        level_group_effects=level_effects,
        fitted_event_count=working.height,
        parameter_count=parameter_count,
        fitted_level_groups=tuple([CONTACT_VALUE_REFERENCE_LEVEL, *level_columns]),
        max_training_event_date=working.get_column("event_date").max(),
    )


def predict_contact_value_baseline(
    contacts: pl.DataFrame,
    fitted: ContactValueBaselineFit,
    *,
    output_column: str = "baseline_contact_value",
) -> pl.DataFrame:
    """Apply the fixed additive contact baseline to supported contact events."""

    _require_columns(contacts, {"contact_bin", "level_group"}, "contact-value target events")
    rows: list[dict[str, Any]] = []
    for row in contacts.iter_rows(named=True):
        contact_bin = str(row["contact_bin"])
        level_group = str(row["level_group"])
        if contact_bin not in fitted.contact_bin_effects:
            raise ValueError(f"contact-value target has unsupported/unfitted contact bin: {contact_bin}")
        if level_group not in fitted.level_group_effects:
            raise ValueError(f"contact-value target has unsupported/unfitted level group: {level_group}")
        enriched = dict(row)
        enriched[output_column] = (
            fitted.intercept
            + fitted.contact_bin_effects[contact_bin]
            + fitted.level_group_effects[level_group]
        )
        rows.append(enriched)
    if not rows:
        return contacts.with_columns(pl.lit(None, dtype=pl.Float64).alias(output_column)).head(0)
    return pl.DataFrame(rows).with_columns(pl.col(output_column).cast(pl.Float64))


def build_contact_value_residual_player_training(
    future_contacts: pl.DataFrame,
) -> pl.DataFrame:
    """Aggregate event residuals to the sufficient player-level WLS table."""

    _require_columns(
        future_contacts,
        {
            "player_id",
            "z_mean_exit_velocity",
            "z_sweet_spot_share",
            "contact_value_residual",
        },
        "contact-value residual training events",
    )
    working = future_contacts.select(
        pl.col("player_id").cast(pl.Int64, strict=False),
        pl.col("z_mean_exit_velocity").cast(pl.Float64, strict=False),
        pl.col("z_sweet_spot_share").cast(pl.Float64, strict=False),
        pl.col("contact_value_residual").cast(pl.Float64, strict=False),
    )
    invalid = working.filter(
        pl.col("player_id").is_null()
        | pl.col("z_mean_exit_velocity").is_null()
        | ~pl.col("z_mean_exit_velocity").is_finite()
        | pl.col("z_sweet_spot_share").is_null()
        | ~pl.col("z_sweet_spot_share").is_finite()
        | pl.col("contact_value_residual").is_null()
        | ~pl.col("contact_value_residual").is_finite()
    )
    if not invalid.is_empty():
        raise ValueError("contact-value residual training events contain invalid fields")
    if working.is_empty():
        raise ValueError("contact-value residual training requires future contacts")

    feature_consistency = (
        working.group_by("player_id")
        .agg(
            pl.col("z_mean_exit_velocity").n_unique().alias("ev_n"),
            pl.col("z_sweet_spot_share").n_unique().alias("ss_n"),
        )
        .filter((pl.col("ev_n") != 1) | (pl.col("ss_n") != 1))
    )
    if not feature_consistency.is_empty():
        raise ValueError("standardized richer features must be constant within training player")

    return (
        working.group_by("player_id")
        .agg(
            pl.col("z_mean_exit_velocity").first().alias("z_mean_exit_velocity"),
            pl.col("z_sweet_spot_share").first().alias("z_sweet_spot_share"),
            pl.col("contact_value_residual").mean().alias("mean_future_contact_value_residual"),
            pl.len().cast(pl.Int64).alias("supported_future_target_contacts"),
        )
        .sort("player_id")
    )


def fit_contact_value_residual_wls(
    player_training: pl.DataFrame,
    *,
    determinant_tolerance: float = 1e-12,
) -> ContactValueResidualFit:
    """Fit the frozen two-coefficient no-intercept player-weighted WLS model."""

    _require_columns(
        player_training,
        {
            "player_id",
            "z_mean_exit_velocity",
            "z_sweet_spot_share",
            "mean_future_contact_value_residual",
            "supported_future_target_contacts",
        },
        "contact-value player training",
    )
    if determinant_tolerance <= 0:
        raise ValueError("determinant_tolerance must be positive")
    duplicate = player_training.group_by("player_id").len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError("contact-value player training violates player_id grain")
    if player_training.height < 2:
        raise ValueError("contact-value residual fit requires at least two training players")

    s11 = s12 = s22 = t1 = t2 = 0.0
    total_weight = 0
    for row in player_training.iter_rows(named=True):
        x1 = float(row["z_mean_exit_velocity"])
        x2 = float(row["z_sweet_spot_share"])
        y = float(row["mean_future_contact_value_residual"])
        weight = int(row["supported_future_target_contacts"])
        if not all(isfinite(value) for value in (x1, x2, y)):
            raise ValueError("contact-value player training contains non-finite values")
        if weight <= 0:
            raise ValueError("supported_future_target_contacts must be positive")
        total_weight += weight
        s11 += weight * x1 * x1
        s12 += weight * x1 * x2
        s22 += weight * x2 * x2
        t1 += weight * x1 * y
        t2 += weight * x2 * y

    determinant = s11 * s22 - s12 * s12
    scale = max(abs(s11 * s22), abs(s12 * s12), 1.0)
    if not isfinite(determinant) or determinant <= determinant_tolerance * scale:
        raise ValueError("contact-value residual WLS design is not finite/full-rank")
    beta_ev = (t1 * s22 - t2 * s12) / determinant
    beta_ss = (s11 * t2 - s12 * t1) / determinant
    return ContactValueResidualFit(
        beta_mean_exit_velocity=float(beta_ev),
        beta_sweet_spot_share=float(beta_ss),
        fitted_player_count=player_training.height,
        fitted_future_contact_count=total_weight,
        determinant=float(determinant),
    )


def apply_contact_value_residual(
    standardized_features: pl.DataFrame,
    fitted: ContactValueResidualFit,
) -> pl.DataFrame:
    """Apply the richer residual with exact zero fallback when it is unavailable."""

    _require_columns(
        standardized_features,
        {
            "player_id",
            "tracked_bbe_eligible",
            "z_mean_exit_velocity",
            "z_sweet_spot_share",
        },
        "standardized contact-value features",
    )
    grain = ["as_of_date", "player_id"] if "as_of_date" in standardized_features.columns else ["player_id"]
    duplicate = standardized_features.group_by(grain).len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError(f"standardized contact-value features violate {' + '.join(grain)} grain")

    eligible = (
        pl.col("tracked_bbe_eligible")
        & pl.col("z_mean_exit_velocity").is_not_null()
        & pl.col("z_mean_exit_velocity").is_finite()
        & pl.col("z_sweet_spot_share").is_not_null()
        & pl.col("z_sweet_spot_share").is_finite()
    )
    return standardized_features.with_columns(
        eligible.alias("contact_value_residual_applies"),
        pl.when(eligible)
        .then(
            fitted.beta_mean_exit_velocity * pl.col("z_mean_exit_velocity")
            + fitted.beta_sweet_spot_share * pl.col("z_sweet_spot_share")
        )
        .otherwise(pl.lit(0.0))
        .cast(pl.Float64)
        .alias("player_contact_value_residual"),
    )
