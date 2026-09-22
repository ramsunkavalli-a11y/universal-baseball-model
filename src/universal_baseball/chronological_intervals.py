"""Distribution-free next-season intervals calibrated only on earlier folds."""

from __future__ import annotations

import numpy as np
import polars as pl


def add_player_stage(frame: pl.DataFrame) -> pl.DataFrame:
    """Assign a forecast-time player stage without using the target season."""
    return frame.with_columns(
        pl.when(pl.col("current_mlb_pa") > 0)
        .then(pl.lit("current_mlb"))
        .when(pl.col("current_highest_level").is_in(["AA", "AAA"]))
        .then(pl.lit("upper_minors"))
        .otherwise(pl.lit("lower_minors"))
        .alias("player_stage")
    )


def chronological_residual_intervals(
    frame: pl.DataFrame,
    *,
    prediction_column: str,
    confidence_levels: tuple[float, ...] = (0.5, 0.8, 0.9),
    minimum_segment_rows: int = 200,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Calibrate asymmetric residual intervals on strictly earlier OOF seasons."""
    required = {
        "origin_year",
        "actual_component_war",
        "player_stage",
        prediction_column,
    }
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"interval frame missing fields: {missing}")
    origins = sorted(frame["origin_year"].unique().to_list())
    outputs: list[pl.DataFrame] = []
    calibration_rows: list[dict[str, object]] = []
    for origin in origins[1:]:
        history = frame.filter(pl.col("origin_year") < origin).with_columns(
            (pl.col("actual_component_war") - pl.col(prediction_column)).alias(
                "residual"
            )
        )
        test = frame.filter(pl.col("origin_year") == origin)
        staged_outputs: list[pl.DataFrame] = []
        for stage in test["player_stage"].unique().to_list():
            stage_test = test.filter(pl.col("player_stage") == stage)
            stage_history = history.filter(pl.col("player_stage") == stage)
            fallback = stage_history.height < minimum_segment_rows
            calibration = history if fallback else stage_history
            residual = calibration["residual"].to_numpy()
            columns: list[pl.Series] = []
            for confidence in confidence_levels:
                alpha = 1.0 - confidence
                lower_offset = float(np.quantile(residual, alpha / 2.0))
                upper_offset = float(np.quantile(residual, 1.0 - alpha / 2.0))
                label = str(int(round(confidence * 100)))
                columns.extend(
                    [
                        (stage_test[prediction_column] + lower_offset).alias(
                            f"lower_{label}"
                        ),
                        (stage_test[prediction_column] + upper_offset).alias(
                            f"upper_{label}"
                        ),
                    ]
                )
                calibration_rows.append(
                    {
                        "test_origin": origin,
                        "player_stage": stage,
                        "confidence": confidence,
                        "calibration_rows": calibration.height,
                        "used_all_stage_fallback": fallback,
                        "lower_residual_offset": lower_offset,
                        "upper_residual_offset": upper_offset,
                    }
                )
            staged_outputs.append(stage_test.with_columns(columns))
        outputs.append(pl.concat(staged_outputs))
    return pl.concat(outputs).sort(["origin_year", "player_id"]), pl.DataFrame(
        calibration_rows
    )


def interval_metrics(
    frame: pl.DataFrame, confidence_levels: tuple[float, ...] = (0.5, 0.8, 0.9)
) -> dict[str, dict[str, float]]:
    """Return empirical coverage and average width for each interval."""
    result: dict[str, dict[str, float]] = {}
    for confidence in confidence_levels:
        label = str(int(round(confidence * 100)))
        lower = frame[f"lower_{label}"].to_numpy()
        upper = frame[f"upper_{label}"].to_numpy()
        actual = frame["actual_component_war"].to_numpy()
        result[label] = {
            "nominal_coverage": confidence,
            "empirical_coverage": float(np.mean((actual >= lower) & (actual <= upper))),
            "mean_width": float(np.mean(upper - lower)),
        }
    return result
