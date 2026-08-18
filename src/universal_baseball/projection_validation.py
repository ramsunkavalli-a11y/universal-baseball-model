"""Leakage-safe chronology primitives for batting Projection v1.

Projection v1 starts from the frozen Current Talent state at an October 15
snapshot and evaluates rate/profile predictions on the following calendar-year
regular-season outcomes.  The 2025 outcome surface is deliberately quarantined
as the untouched confirmation period.

This module contains chronology only.  It does not fit an age curve, score a
projection model, infer playing time, or access any data source.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import polars as pl


@dataclass(frozen=True, slots=True)
class ProjectionFold:
    """One frozen Projection snapshot and its exclusive future target window."""

    label: str
    snapshot_date: date
    target_start: date
    target_end: date
    confirmation: bool = False

    def __post_init__(self) -> None:
        if not self.label:
            raise ValueError("projection fold label must be nonempty")
        if self.target_start >= self.target_end:
            raise ValueError("projection target window must have positive width")
        if self.snapshot_date >= self.target_start:
            raise ValueError("projection snapshot must precede target window")
        expected_start = date(self.snapshot_date.year + 1, 1, 1)
        expected_end = date(self.snapshot_date.year + 2, 1, 1)
        if self.target_start != expected_start or self.target_end != expected_end:
            raise ValueError(
                "Projection v1 target must be the full calendar year after the snapshot season"
            )
        if self.snapshot_date != date(self.snapshot_date.year, 10, 15):
            raise ValueError("Projection v1 snapshot must be October 15")


PROJECTION_V1_DEVELOPMENT_FOLDS = (
    ProjectionFold(
        label="projection_2021_to_2022",
        snapshot_date=date(2021, 10, 15),
        target_start=date(2022, 1, 1),
        target_end=date(2023, 1, 1),
    ),
    ProjectionFold(
        label="projection_2022_to_2023",
        snapshot_date=date(2022, 10, 15),
        target_start=date(2023, 1, 1),
        target_end=date(2024, 1, 1),
    ),
    ProjectionFold(
        label="projection_2023_to_2024",
        snapshot_date=date(2023, 10, 15),
        target_start=date(2024, 1, 1),
        target_end=date(2025, 1, 1),
    ),
)

PROJECTION_V1_CONFIRMATION_FOLD = ProjectionFold(
    label="projection_2024_to_2025_confirmation",
    snapshot_date=date(2024, 10, 15),
    target_start=date(2025, 1, 1),
    target_end=date(2026, 1, 1),
    confirmation=True,
)


def development_fold_for_snapshot(snapshot_date: date) -> ProjectionFold:
    """Return the frozen development fold for one October 15 snapshot."""

    matches = [
        fold for fold in PROJECTION_V1_DEVELOPMENT_FOLDS if fold.snapshot_date == snapshot_date
    ]
    if len(matches) != 1:
        raise ValueError(f"snapshot is not a frozen Projection v1 development fold: {snapshot_date}")
    return matches[0]


def require_development_fold(fold: ProjectionFold) -> None:
    """Fail closed if confirmation evidence is passed to development code."""

    if fold.confirmation:
        raise ValueError("2025 Projection confirmation outcomes are quarantined from development")
    if fold not in PROJECTION_V1_DEVELOPMENT_FOLDS:
        raise ValueError("fold is not part of the frozen Projection v1 development contract")


def add_projection_membership(
    frame: pl.DataFrame,
    *,
    fold: ProjectionFold,
    game_date_column: str = "game_date",
    allow_confirmation: bool = False,
) -> pl.DataFrame:
    """Annotate predictor/target/outside membership for one frozen Projection fold.

    Predictor evidence is strictly before the October 15 snapshot boundary.
    Target evidence is the following calendar year ``[target_start, target_end)``.
    Confirmation rows cannot be touched unless a caller explicitly opts in after
    the confirmation contract has been frozen.
    """

    if fold.confirmation and not allow_confirmation:
        raise ValueError("2025 Projection confirmation outcomes are quarantined")
    if game_date_column not in frame.columns:
        raise ValueError(f"projection frame missing game-date column: {game_date_column}")

    parsed_name = "projection_game_date"
    annotated = frame.with_columns(
        pl.col(game_date_column).cast(pl.String).str.to_date(strict=False).alias(parsed_name)
    )
    if annotated.filter(pl.col(parsed_name).is_null()).height:
        raise ValueError("projection frame contains unparseable game dates")

    return annotated.with_columns(
        (pl.col(parsed_name) < pl.lit(fold.snapshot_date)).alias("is_projection_predictor_evidence"),
        (
            (pl.col(parsed_name) >= pl.lit(fold.target_start))
            & (pl.col(parsed_name) < pl.lit(fold.target_end))
        ).alias("is_projection_target_evidence"),
    ).with_columns(
        (
            ~pl.col("is_projection_predictor_evidence")
            & ~pl.col("is_projection_target_evidence")
        ).alias("is_outside_projection_window")
    )


def select_projection_target_events(
    frame: pl.DataFrame,
    *,
    fold: ProjectionFold,
    game_date_column: str = "game_date",
    allow_confirmation: bool = False,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Select the complete future target surface for one Projection fold."""

    annotated = add_projection_membership(
        frame,
        fold=fold,
        game_date_column=game_date_column,
        allow_confirmation=allow_confirmation,
    )
    target = annotated.filter(pl.col("is_projection_target_evidence")).drop(
        "projection_game_date",
        "is_projection_predictor_evidence",
        "is_projection_target_evidence",
        "is_outside_projection_window",
    )
    metrics: dict[str, Any] = {
        "fold": fold.label,
        "snapshot_date": fold.snapshot_date.isoformat(),
        "target_start": fold.target_start.isoformat(),
        "target_end": fold.target_end.isoformat(),
        "confirmation": fold.confirmation,
        "target_row_count": int(target.height),
        "confirmation_access_explicitly_authorized": bool(fold.confirmation and allow_confirmation),
    }
    return target, metrics
