"""Pure ranking/validation logic for the predeclared Current Talent grid."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import polars as pl


EXPECTED_TRANSLATION_VARIANTS = {"fitted_translation", "zero_offset_translation"}


@dataclass(frozen=True, slots=True)
class SelectionGridSummary:
    ranked_candidates: pl.DataFrame
    selected_candidate: dict[str, Any]
    metrics: dict[str, Any]


def _require_columns(frame: pl.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing fields: {missing}")


def _validate_candidate_configuration(frame: pl.DataFrame) -> None:
    config = [
        "candidate_id",
        "half_life_days",
        "prior_strength_core_events",
        "translation_variant",
    ]
    duplicate_config = frame.select(config).unique().group_by("candidate_id").len().filter(
        pl.col("len") != 1
    )
    if not duplicate_config.is_empty():
        raise ValueError("candidate_id maps to more than one grid configuration")
    variants = set(frame.get_column("translation_variant").unique().to_list())
    if not variants.issubset(EXPECTED_TRANSLATION_VARIANTS):
        raise ValueError(f"unsupported selection-grid translation variants: {sorted(variants)}")


def _validate_coverage(frame: pl.DataFrame) -> None:
    coverage_columns = [
        "scored_player_count",
        "scored_target_environment_count",
        "future_core_events",
    ]
    fold_key = ["season", "as_of_date"]
    for row in frame.group_by(fold_key).agg(
        *[pl.col(column).n_unique().alias(column) for column in coverage_columns]
    ).iter_rows(named=True):
        bad = [column for column in coverage_columns if int(row[column]) != 1]
        if bad:
            raise ValueError(
                "selection-grid candidate coverage differs inside fold "
                f"season={row['season']} cutoff={row['as_of_date']}: {bad}"
            )


def _pareto_frontier(rows: list[dict[str, Any]]) -> set[str]:
    frontier: set[str] = set()
    for candidate in rows:
        candidate_id = str(candidate["candidate_id"])
        log_loss = float(candidate["mean_baseline1_log_loss"])
        brier = float(candidate["mean_baseline1_brier"])
        dominated = False
        for other in rows:
            if other is candidate:
                continue
            other_log_loss = float(other["mean_baseline1_log_loss"])
            other_brier = float(other["mean_baseline1_brier"])
            if (
                other_log_loss <= log_loss
                and other_brier <= brier
                and (other_log_loss < log_loss or other_brier < brier)
            ):
                dominated = True
                break
        if not dominated:
            frontier.add(candidate_id)
    return frontier


def summarize_selection_grid(
    fold_metrics: pl.DataFrame,
    *,
    expected_fold_count: int,
    expected_candidate_count: int | None = None,
) -> SelectionGridSummary:
    """Validate and rank one development-only Current Talent candidate grid.

    Each fold is equally weighted across chronology. Event weighting has already
    happened inside each fold's proper score.
    """

    required = {
        "candidate_id",
        "season",
        "as_of_date",
        "half_life_days",
        "prior_strength_core_events",
        "translation_variant",
        "scored_player_count",
        "scored_target_environment_count",
        "future_core_events",
        "baseline0_log_loss",
        "baseline1_log_loss",
        "baseline1_minus_baseline0_log_loss",
        "baseline0_brier",
        "baseline1_brier",
        "baseline1_minus_baseline0_brier",
        "baseline0_mean_abs_calibration_intercept_error",
        "baseline1_mean_abs_calibration_intercept_error",
        "baseline0_mean_abs_calibration_slope_error",
        "baseline1_mean_abs_calibration_slope_error",
        "baseline0_mean_ece",
        "baseline1_mean_ece",
    }
    _require_columns(fold_metrics, required, "selection-grid fold metrics")
    if expected_fold_count < 1:
        raise ValueError("expected_fold_count must be positive")
    if fold_metrics.is_empty():
        raise ValueError("selection-grid fold metrics cannot be empty")

    _validate_candidate_configuration(fold_metrics)
    _validate_coverage(fold_metrics)

    duplicate = fold_metrics.group_by(["candidate_id", "season", "as_of_date"]).len().filter(
        pl.col("len") != 1
    )
    if not duplicate.is_empty():
        raise ValueError("selection-grid fold metrics violate candidate + fold grain")

    candidate_count = fold_metrics.get_column("candidate_id").n_unique()
    if expected_candidate_count is not None and candidate_count != expected_candidate_count:
        raise ValueError(
            f"expected {expected_candidate_count} candidates, observed {candidate_count}"
        )
    fold_counts = fold_metrics.group_by("candidate_id").len().filter(
        pl.col("len") != expected_fold_count
    )
    if not fold_counts.is_empty():
        raise ValueError(
            f"every candidate must have exactly {expected_fold_count} development folds"
        )

    ranked = (
        fold_metrics.group_by(
            [
                "candidate_id",
                "half_life_days",
                "prior_strength_core_events",
                "translation_variant",
            ]
        )
        .agg(
            pl.len().cast(pl.Int64).alias("fold_count"),
            pl.col("baseline1_log_loss").mean().alias("mean_baseline1_log_loss"),
            pl.col("baseline1_brier").mean().alias("mean_baseline1_brier"),
            pl.col("baseline1_minus_baseline0_log_loss")
            .mean()
            .alias("mean_baseline1_minus_baseline0_log_loss"),
            pl.col("baseline1_minus_baseline0_brier")
            .mean()
            .alias("mean_baseline1_minus_baseline0_brier"),
            (pl.col("baseline1_minus_baseline0_log_loss") < 0)
            .sum()
            .cast(pl.Int64)
            .alias("baseline1_log_loss_win_fold_count"),
            (pl.col("baseline1_minus_baseline0_brier") < 0)
            .sum()
            .cast(pl.Int64)
            .alias("baseline1_brier_win_fold_count"),
            pl.col("baseline1_log_loss").min().alias("best_fold_baseline1_log_loss"),
            pl.col("baseline1_log_loss").max().alias("worst_fold_baseline1_log_loss"),
            pl.col("baseline1_brier").min().alias("best_fold_baseline1_brier"),
            pl.col("baseline1_brier").max().alias("worst_fold_baseline1_brier"),
            pl.col("baseline1_mean_abs_calibration_intercept_error")
            .mean()
            .alias("mean_abs_calibration_intercept_error"),
            pl.col("baseline1_mean_abs_calibration_slope_error")
            .mean()
            .alias("mean_abs_calibration_slope_error"),
            pl.col("baseline1_mean_ece").mean().alias("mean_ece"),
            (
                pl.col("baseline1_mean_abs_calibration_intercept_error")
                - pl.col("baseline0_mean_abs_calibration_intercept_error")
            )
            .mean()
            .alias("mean_b1_minus_b0_abs_intercept_error"),
            (
                pl.col("baseline1_mean_abs_calibration_slope_error")
                - pl.col("baseline0_mean_abs_calibration_slope_error")
            )
            .mean()
            .alias("mean_b1_minus_b0_abs_slope_error"),
            (pl.col("baseline1_mean_ece") - pl.col("baseline0_mean_ece"))
            .mean()
            .alias("mean_b1_minus_b0_ece"),
        )
    )

    row_dicts = ranked.to_dicts()
    frontier = _pareto_frontier(row_dicts)
    ranked = ranked.with_columns(
        pl.col("candidate_id").is_in(sorted(frontier)).alias("proper_score_pareto_frontier"),
        pl.col("mean_baseline1_log_loss")
        .rank(method="min")
        .cast(pl.Int64)
        .alias("log_loss_rank"),
        pl.col("mean_baseline1_brier")
        .rank(method="min")
        .cast(pl.Int64)
        .alias("brier_rank"),
    )

    # Primary objective is mean log loss. These only resolve literal/numerical
    # ties and do not form a hidden weighted composite objective.
    ranked = ranked.with_columns(
        pl.when(pl.col("translation_variant") == "zero_offset_translation")
        .then(pl.lit(0))
        .otherwise(pl.lit(1))
        .cast(pl.Int64)
        .alias("_simplicity_translation"),
        (-pl.col("prior_strength_core_events")).alias("_simplicity_prior"),
        (-pl.col("half_life_days")).alias("_simplicity_half_life"),
    ).sort(
        [
            "mean_baseline1_log_loss",
            "_simplicity_translation",
            "_simplicity_prior",
            "_simplicity_half_life",
            "candidate_id",
        ]
    )
    selected = ranked.row(0, named=True)
    ranked = ranked.drop(
        "_simplicity_translation",
        "_simplicity_prior",
        "_simplicity_half_life",
    ).with_row_index("selection_order", offset=1)

    metrics = {
        "candidate_count": int(candidate_count),
        "expected_fold_count": int(expected_fold_count),
        "candidate_fold_row_count": int(fold_metrics.height),
        "pareto_frontier_count": len(frontier),
        "selection_primary_objective": "equal_fold_mean_event_weighted_multinomial_log_loss",
        "selection_secondary_report": "equal_fold_mean_event_weighted_multinomial_brier",
        "selection_uses_2023": False,
    }
    return SelectionGridSummary(
        ranked_candidates=ranked,
        selected_candidate={
            key: value
            for key, value in selected.items()
            if not key.startswith("_simplicity_")
        },
        metrics=metrics,
    )
