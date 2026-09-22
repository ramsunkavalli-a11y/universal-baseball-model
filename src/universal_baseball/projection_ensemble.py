"""Chronology-safe helpers for simple projection ensembles."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import polars as pl


def _rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(predicted - actual))))


def greedy_equal_subset(
    frame: pl.DataFrame,
    prediction_columns: Sequence[str],
    *,
    actual_column: str,
    minimum_rmse_gain: float = 0.00025,
) -> tuple[str, ...]:
    """Drop ensemble members only when prior rows show a material RMSE gain."""

    selected = list(prediction_columns)
    if not selected:
        raise ValueError("prediction_columns must not be empty")
    if frame.is_empty():
        return tuple(selected)
    actual = frame[actual_column].to_numpy()
    while len(selected) > 1:
        current = np.mean([frame[column].to_numpy() for column in selected], axis=0)
        current_rmse = _rmse(actual, current)
        candidates: list[tuple[float, str, list[str]]] = []
        for column in selected:
            retained = [name for name in selected if name != column]
            prediction = np.mean(
                [frame[name].to_numpy() for name in retained], axis=0
            )
            candidates.append((_rmse(actual, prediction), column, retained))
        best_rmse, _, best_retained = min(candidates, key=lambda item: item[0])
        if current_rmse - best_rmse < minimum_rmse_gain:
            break
        selected = best_retained
    return tuple(selected)


def chronological_greedy_equal_ensemble(
    frame: pl.DataFrame,
    prediction_columns: Sequence[str],
    *,
    origin_column: str = "origin_year",
    actual_column: str = "actual_component_war",
    minimum_rmse_gain: float = 0.00025,
) -> tuple[pl.DataFrame, list[dict[str, object]]]:
    """Choose every test season's equal-weight subset from earlier folds only."""

    origins = sorted(int(value) for value in frame[origin_column].unique())
    pieces: list[pl.DataFrame] = []
    selections: list[dict[str, object]] = []
    for origin in origins:
        prior = frame.filter(pl.col(origin_column) < origin)
        selected = greedy_equal_subset(
            prior,
            prediction_columns,
            actual_column=actual_column,
            minimum_rmse_gain=minimum_rmse_gain,
        )
        test = frame.filter(pl.col(origin_column) == origin)
        prediction = np.mean(
            [test[column].to_numpy() for column in selected], axis=0
        )
        pieces.append(
            test.select(origin_column, "player_id", actual_column).with_columns(
                pl.Series("prediction_chronology_pruned_equal", prediction)
            )
        )
        selections.append(
            {
                "test_origin": origin,
                "prior_rows": prior.height,
                "selected_members": list(selected),
                "member_count": len(selected),
            }
        )
    return pl.concat(pieces), selections
