#!/usr/bin/env python
"""Evaluate additive, baseball-interaction and low-rank matchup models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from universal_baseball.historical_battery_support import (
    classify_battery_plate_appearances,
)
from universal_baseball.historical_matchup_profiles import (
    LEVEL_RANK,
    PROFILE_SPECS,
    TARGET_SPECS,
    add_matchup_outcomes,
    build_matchup_cells,
    build_prior_profiles,
    build_prior_split_profiles,
)


TARGET_YEARS = (2017, 2018, 2019, 2021, 2022, 2023, 2024)
EVALUATION_YEARS = (2019, 2021, 2022, 2023, 2024)
ALPHAS = (0.0001, 0.001, 0.01, 0.1)
DEFAULT_ALPHA = 0.1
CHUNK_SIZE = 50_000
PROFILE_NAMES = tuple(PROFILE_SPECS)
LEVELS = tuple(LEVEL_RANK)
HAND_CELLS = ("RR", "RL", "LR", "LL", "other")
MODEL_NAMES = (
    "additive",
    "handed_additive",
    "baseball_interactions",
    "handed_interactions",
    "full_bilinear",
    "rank2_bilinear",
)

EXPLICIT_INTERACTIONS = (
    ("k", "k"),
    ("control", "control"),
    ("hr", "hr"),
    ("hit_bip", "hit_bip"),
    ("damage_bip", "damage_bip"),
    ("gb_bip", "gb_bip"),
    ("air_bip", "air_bip"),
    ("ld_bip", "ld_bip"),
    ("pu_bip", "pu_bip"),
    ("hr", "air_bip"),
    ("air_bip", "hr"),
    ("damage_bip", "gb_bip"),
    ("gb_bip", "damage_bip"),
    ("k", "control"),
    ("control", "k"),
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path("data/working/pbp-opportunity-foundation-v1"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/all-level-matchup-challenger-v1"),
    )
    return parser


def _read_terminal(root: Path) -> pl.DataFrame:
    paths = sorted(root.glob("season=*/level=*/terminal/*.parquet"))
    if not paths:
        raise FileNotFoundError(f"no terminal partitions under {root}")
    columns = [
        "season",
        "level",
        "game_pk",
        "at_bat_index",
        "batter",
        "pitcher",
        "fielder_2",
        "stand",
        "p_throws",
        "park_key",
        "bb_type",
        "pa_description",
        "terminal_outcome_group",
        "terminal_outcome_status",
        "source_asset",
    ]
    frame = pl.concat(
        [pl.read_parquet(path, columns=columns) for path in paths],
        how="diagonal_relaxed",
    )
    return frame.sort("game_pk", "at_bat_index", "source_asset").unique(
        subset=["game_pk", "at_bat_index"], keep="first", maintain_order=True
    )


def _continuous_matrix(frame: pl.DataFrame) -> np.ndarray:
    overall_columns = [
        *(f"h_{name}" for name in PROFILE_NAMES),
        *(f"p_{name}" for name in PROFILE_NAMES),
    ]
    overall = frame.select(overall_columns).to_numpy().astype(np.float64, copy=False)
    history = np.column_stack(
        [
            np.log1p(frame.get_column("h_history_pa").to_numpy()),
            np.log1p(frame.get_column("p_history_pa").to_numpy()),
            frame.get_column("level_rank").to_numpy()
            - frame.get_column("h_last_level_rank").to_numpy(),
            frame.get_column("level_rank").to_numpy()
            - frame.get_column("p_last_level_rank").to_numpy(),
        ]
    )
    split_columns = [
        *(f"hs_{name}" for name in PROFILE_NAMES),
        *(f"ps_{name}" for name in PROFILE_NAMES),
    ]
    split = frame.select(split_columns).to_numpy().astype(np.float64, copy=False)
    split_history = np.column_stack(
        [
            np.log1p(frame.get_column("hs_history_pa").to_numpy()),
            np.log1p(frame.get_column("ps_history_pa").to_numpy()),
        ]
    )
    return np.column_stack([overall, history, split, split_history])


def _weighted_scaler(frames: list[pl.DataFrame]) -> tuple[np.ndarray, np.ndarray]:
    total_weight = 0.0
    total = np.zeros(len(PROFILE_NAMES) * 4 + 6, dtype=float)
    total_square = np.zeros_like(total)
    for frame in frames:
        for offset in range(0, frame.height, CHUNK_SIZE):
            chunk = frame.slice(offset, CHUNK_SIZE)
            values = _continuous_matrix(chunk)
            weight = chunk.get_column("pa").to_numpy().astype(float)
            total_weight += float(weight.sum())
            total += (values * weight[:, None]).sum(axis=0)
            total_square += (values**2 * weight[:, None]).sum(axis=0)
    mean = total / total_weight
    variance = np.maximum(total_square / total_weight - mean**2, 1e-12)
    return mean, np.sqrt(variance)


def _base_design(
    frame: pl.DataFrame, mean: np.ndarray, scale: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    continuous = (_continuous_matrix(frame) - mean) / scale
    hitter = continuous[:, : len(PROFILE_NAMES)]
    pitcher = continuous[
        :, len(PROFILE_NAMES) : 2 * len(PROFILE_NAMES)
    ]
    base_continuous_end = 2 * len(PROFILE_NAMES) + 4
    split_hitter = continuous[
        :, base_continuous_end : base_continuous_end + len(PROFILE_NAMES)
    ]
    split_pitcher = continuous[
        :,
        base_continuous_end + len(PROFILE_NAMES) : base_continuous_end
        + 2 * len(PROFILE_NAMES),
    ]
    split_history = continuous[:, -2:]
    hand = (
        frame.get_column("pitcher_hand").fill_null("U").to_numpy().astype(str)
        + frame.get_column("batter_side").fill_null("U").to_numpy().astype(str)
    )
    hand = np.where(np.isin(hand, HAND_CELLS[:-1]), hand, "other")
    level = frame.get_column("level").to_numpy().astype(str)
    categories = np.column_stack(
        [
            *(hand == value for value in HAND_CELLS),
            *(level == value for value in LEVELS),
        ]
    ).astype(float)
    base = np.column_stack(
        [np.ones(frame.height), continuous[:, :base_continuous_end], categories]
    )
    return base, hitter, pitcher, split_hitter, split_pitcher, split_history


def _design(
    frame: pl.DataFrame,
    mean: np.ndarray,
    scale: np.ndarray,
    model: str,
) -> np.ndarray:
    base, hitter, pitcher, split_hitter, split_pitcher, split_history = _base_design(
        frame, mean, scale
    )
    if model == "additive":
        return base
    handed_base = np.column_stack(
        [base, split_hitter, split_pitcher, split_history]
    )
    if model == "handed_additive":
        return handed_base
    if model == "baseball_interactions":
        index = {name: position for position, name in enumerate(PROFILE_NAMES)}
        products = np.column_stack(
            [hitter[:, index[left]] * pitcher[:, index[right]] for left, right in EXPLICIT_INTERACTIONS]
        )
        return np.column_stack([base, products])
    if model == "handed_interactions":
        index = {name: position for position, name in enumerate(PROFILE_NAMES)}
        products = np.column_stack(
            [
                split_hitter[:, index[left]] * split_pitcher[:, index[right]]
                for left, right in EXPLICIT_INTERACTIONS
            ]
        )
        return np.column_stack([handed_base, products])
    if model in {"full_bilinear", "rank2_bilinear"}:
        products = np.einsum("bi,bj->bij", hitter, pitcher).reshape(
            frame.height, -1
        )
        return np.column_stack([base, products])
    raise ValueError(f"unknown matchup model {model}")


def _target_arrays(frame: pl.DataFrame, target: str) -> tuple[np.ndarray, np.ndarray]:
    numerator, denominator = TARGET_SPECS[target]
    successes = frame.get_column(numerator).to_numpy().astype(float)
    opportunities = frame.get_column(denominator).to_numpy().astype(float)
    return successes, opportunities


def _normal_equations(
    frames: list[pl.DataFrame],
    *,
    mean: np.ndarray,
    scale: np.ndarray,
    model: str,
) -> dict[str, tuple[np.ndarray, np.ndarray, float]]:
    sample = _design(frames[0].head(1), mean, scale, model)
    dimension = sample.shape[1]
    equations = {
        target: (
            np.zeros((dimension, dimension), dtype=float),
            np.zeros(dimension, dtype=float),
            0.0,
        )
        for target in TARGET_SPECS
    }
    for frame in frames:
        for offset in range(0, frame.height, CHUNK_SIZE):
            chunk = frame.slice(offset, CHUNK_SIZE)
            design = _design(chunk, mean, scale, model)
            for target in TARGET_SPECS:
                successes, opportunities = _target_arrays(chunk, target)
                valid = opportunities > 0
                if not valid.any():
                    continue
                x = design[valid]
                weight = opportunities[valid]
                response = successes[valid] / weight
                xtx, xty, total_weight = equations[target]
                xtx += x.T @ (x * weight[:, None])
                xty += x.T @ (response * weight)
                equations[target] = (xtx, xty, total_weight + float(weight.sum()))
    return equations


def _fit_coefficients(
    equations: dict[str, tuple[np.ndarray, np.ndarray, float]],
    *,
    model: str,
    base_dimension: int,
) -> dict[tuple[str, float], np.ndarray]:
    fitted: dict[tuple[str, float], np.ndarray] = {}
    for target, (xtx, xty, total_weight) in equations.items():
        average_xtx = xtx / total_weight
        average_xty = xty / total_weight
        for alpha in ALPHAS:
            penalty = np.eye(xtx.shape[0]) * alpha
            penalty[0, 0] = 0.0
            beta = np.linalg.solve(average_xtx + penalty, average_xty)
            if model == "rank2_bilinear":
                interaction = beta[base_dimension:].reshape(
                    len(PROFILE_NAMES), len(PROFILE_NAMES)
                )
                left, singular, right = np.linalg.svd(interaction, full_matrices=False)
                reduced = (left[:, :2] * singular[:2]) @ right[:2]
                beta = beta.copy()
                beta[base_dimension:] = reduced.reshape(-1)
            fitted[(target, alpha)] = beta
    return fitted


def _binary_metrics(
    successes: np.ndarray, opportunities: np.ndarray, prediction: np.ndarray
) -> tuple[float, float, float]:
    prediction = np.clip(prediction, 1e-6, 1.0 - 1e-6)
    failures = opportunities - successes
    log_loss = -float(
        (successes * np.log(prediction) + failures * np.log1p(-prediction)).sum()
    )
    brier = float(
        (successes * (1.0 - prediction) ** 2 + failures * prediction**2).sum()
    )
    return log_loss, brier, float(opportunities.sum())


def _selected_alpha(
    history: list[dict[str, Any]], *, model: str, target: str
) -> float:
    prior = [
        row for row in history if row["model"] == model and row["target"] == target
    ]
    if not prior:
        return DEFAULT_ALPHA
    scores = []
    for alpha in ALPHAS:
        rows = [row for row in prior if row["alpha"] == alpha]
        scores.append(
            (
                sum(float(row["log_loss_sum"]) for row in rows)
                / sum(float(row["opportunities"]) for row in rows),
                alpha,
            )
        )
    return min(scores)[1]


def _evaluate_fold(
    test: pl.DataFrame,
    *,
    mean: np.ndarray,
    scale: np.ndarray,
    coefficients: dict[str, dict[tuple[str, float], np.ndarray]],
    tuning_history: list[dict[str, Any]],
    target_year: int,
) -> tuple[list[dict[str, Any]], list[pl.DataFrame], list[dict[str, Any]]]:
    all_alpha_rows: list[dict[str, Any]] = []
    selected_player_chunks: list[pl.DataFrame] = []
    segment_sums: dict[tuple[str, str, str], list[float]] = {}
    selections = {
        (model, target): _selected_alpha(tuning_history, model=model, target=target)
        for model in MODEL_NAMES
        for target in TARGET_SPECS
    }

    for offset in range(0, test.height, CHUNK_SIZE):
        chunk = test.slice(offset, CHUNK_SIZE)
        designs = {
            model: _design(chunk, mean, scale, model)
            for model in (
                "additive",
                "handed_additive",
                "baseball_interactions",
                "handed_interactions",
                "full_bilinear",
            )
        }
        designs["rank2_bilinear"] = designs["full_bilinear"]
        predictions: dict[tuple[str, str], np.ndarray] = {}
        for model in MODEL_NAMES:
            x = designs[model]
            for target in TARGET_SPECS:
                selected = selections[(model, target)]
                predictions[(model, target)] = np.clip(
                    x @ coefficients[model][(target, selected)], 1e-6, 1 - 1e-6
                )
                successes, opportunities = _target_arrays(chunk, target)
                valid = opportunities > 0
                for alpha in ALPHAS:
                    estimate = x @ coefficients[model][(target, alpha)]
                    ll, brier, count = _binary_metrics(
                        successes[valid], opportunities[valid], estimate[valid]
                    )
                    all_alpha_rows.append(
                        {
                            "target_season": target_year,
                            "model": model,
                            "target": target,
                            "alpha": alpha,
                            "log_loss_sum": ll,
                            "brier_sum": brier,
                            "opportunities": count,
                            "selected_for_fold": alpha == selected,
                        }
                    )

                for segment_name, mask in (
                    ("all", np.ones(chunk.height, dtype=bool)),
                    ("new_pair", chunk.get_column("new_pair").to_numpy()),
                    (
                        "hitter_advanced",
                        chunk.get_column("hitter_advanced").to_numpy(),
                    ),
                    (
                        "pitcher_advanced",
                        chunk.get_column("pitcher_advanced").to_numpy(),
                    ),
                ):
                    use = valid & mask
                    if not use.any():
                        continue
                    ll, brier, count = _binary_metrics(
                        successes[use],
                        opportunities[use],
                        predictions[(model, target)][use],
                    )
                    key = (model, target, segment_name)
                    values = segment_sums.setdefault(key, [0.0, 0.0, 0.0])
                    values[0] += ll
                    values[1] += brier
                    values[2] += count

        for target in TARGET_SPECS:
            successes, opportunities = _target_arrays(chunk, target)
            valid = opportunities > 0
            selected_player_chunks.append(
                pl.DataFrame(
                    {
                        "target_season": np.full(valid.sum(), target_year),
                        "target": np.full(valid.sum(), target),
                        "batter_id": chunk.get_column("batter_id").to_numpy()[valid],
                        "pitcher_id": chunk.get_column("pitcher_id").to_numpy()[valid],
                        "successes": successes[valid],
                        "opportunities": opportunities[valid],
                        **{
                            f"prediction_{model}": predictions[(model, target)][valid]
                            * opportunities[valid]
                            for model in MODEL_NAMES
                        },
                    }
                )
            )

    segments = [
        {
            "target_season": target_year,
            "model": model,
            "target": target,
            "segment": segment,
            "log_loss": values[0] / values[2],
            "brier": values[1] / values[2],
            "opportunities": int(values[2]),
            "selected_alpha": selections[(model, target)],
        }
        for (model, target, segment), values in segment_sums.items()
    ]
    return all_alpha_rows, selected_player_chunks, segments


def _collapse_fold_metrics(rows: list[dict[str, Any]]) -> pl.DataFrame:
    return (
        pl.DataFrame(rows)
        .group_by("target_season", "model", "target", "alpha", "selected_for_fold")
        .agg(
            pl.col("log_loss_sum").sum(),
            pl.col("brier_sum").sum(),
            pl.col("opportunities").sum(),
        )
        .with_columns(
            (pl.col("log_loss_sum") / pl.col("opportunities")).alias("log_loss"),
            (pl.col("brier_sum") / pl.col("opportunities")).alias("brier"),
        )
        .sort("target_season", "target", "model", "alpha")
    )


def _player_metrics(chunks: list[pl.DataFrame]) -> tuple[pl.DataFrame, pl.DataFrame]:
    cells = pl.concat(chunks, how="vertical_relaxed")
    rows = []
    fold_rows = []
    for role, player_column in (("hitter", "batter_id"), ("pitcher", "pitcher_id")):
        grouped = cells.group_by("target_season", "target", player_column).agg(
            pl.col("successes").sum(),
            pl.col("opportunities").sum(),
            *(pl.col(f"prediction_{model}").sum() for model in MODEL_NAMES),
        ).filter(pl.col("opportunities") >= 100)
        for target in TARGET_SPECS:
            target_rows = grouped.filter(pl.col("target") == target)
            for model in MODEL_NAMES:
                values = target_rows.select(
                    (
                        pl.col("successes") / pl.col("opportunities")
                        - pl.col(f"prediction_{model}") / pl.col("opportunities")
                    )
                    .pow(2)
                    .mean()
                    .sqrt()
                    .alias("rmse"),
                    pl.len().alias("player_tests"),
                ).row(0, named=True)
                rows.append(
                    {
                        "role": role,
                        "target": target,
                        "model": model,
                        "rmse": float(values["rmse"]),
                        "player_tests": int(values["player_tests"]),
                    }
                )
                for target_season in EVALUATION_YEARS:
                    fold = target_rows.filter(
                        pl.col("target_season") == target_season
                    )
                    fold_values = fold.select(
                        (
                            pl.col("successes") / pl.col("opportunities")
                            - pl.col(f"prediction_{model}")
                            / pl.col("opportunities")
                        )
                        .pow(2)
                        .mean()
                        .sqrt()
                        .alias("rmse"),
                        pl.len().alias("player_tests"),
                    ).row(0, named=True)
                    fold_rows.append(
                        {
                            "target_season": target_season,
                            "role": role,
                            "target": target,
                            "model": model,
                            "rmse": float(fold_values["rmse"]),
                            "player_tests": int(fold_values["player_tests"]),
                        }
                    )
    return pl.DataFrame(rows), pl.DataFrame(fold_rows)


def _report(
    *,
    events: pl.DataFrame,
    cells: pl.DataFrame,
    fold_metrics: pl.DataFrame,
    player_metrics: pl.DataFrame,
    segments: pl.DataFrame,
) -> dict[str, Any]:
    selected = fold_metrics.filter(pl.col("selected_for_fold"))
    pooled = (
        selected.group_by("model", "target")
        .agg(
            pl.col("log_loss_sum").sum(),
            pl.col("brier_sum").sum(),
            pl.col("opportunities").sum(),
            pl.col("target_season").n_unique().alias("folds"),
        )
        .with_columns(
            (pl.col("log_loss_sum") / pl.col("opportunities")).alias("log_loss"),
            (pl.col("brier_sum") / pl.col("opportunities")).alias("brier"),
        )
    )
    comparisons = []
    comparison_baselines = {
        "handed_additive": "additive",
        "baseball_interactions": "additive",
        "handed_interactions": "handed_additive",
        "full_bilinear": "additive",
        "rank2_bilinear": "additive",
    }
    for target in TARGET_SPECS:
        table = pooled.filter(pl.col("target") == target)
        for model, baseline_name in comparison_baselines.items():
            baseline = table.filter(pl.col("model") == baseline_name).row(
                0, named=True
            )
            candidate = table.filter(pl.col("model") == model).row(0, named=True)
            fold_pairs = (
                selected.filter(
                    (pl.col("target") == target)
                    & pl.col("model").is_in([baseline_name, model])
                )
                .select("target_season", "model", "log_loss")
                .pivot(on="model", index="target_season", values="log_loss")
                .with_columns(
                    (pl.col(model) - pl.col(baseline_name)).alias("change")
                )
            )
            comparisons.append(
                {
                    "target": target,
                    "model": model,
                    "baseline": baseline_name,
                    "log_loss_change": float(
                        candidate["log_loss"] - baseline["log_loss"]
                    ),
                    "brier_change": float(candidate["brier"] - baseline["brier"]),
                    "improved_folds": int(
                        fold_pairs.get_column("change").lt(0).sum()
                    ),
                    "fold_count": int(fold_pairs.height),
                }
            )
    return {
        "report_schema_version": "0.1",
        "component": "all_level_profile_matchup_challenger_v1",
        "eligible_plate_appearances": int(events.height),
        "matchup_cells": int(cells.height),
        "source_seasons": sorted(events.get_column("season").unique().to_list()),
        "evaluation_seasons": list(EVALUATION_YEARS),
        "levels": sorted(events.get_column("level").unique().to_list()),
        "models": list(MODEL_NAMES),
        "targets": list(TARGET_SPECS),
        "comparisons_to_additive": comparisons,
        "player_projection_metrics": player_metrics.to_dicts(),
        "segment_metrics": segments.to_dicts(),
        "protected_2026_accessed": False,
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# All-level hitter-pitcher matchup challenger v1",
        "",
        f"- Eligible PAs: {report['eligible_plate_appearances']:,}",
        f"- Aggregated matchup cells: {report['matchup_cells']:,}",
        f"- Evaluation seasons: {report['evaluation_seasons']}",
        f"- Levels: {report['levels']}",
        "- 2026 outcomes accessed: **false**",
        "",
        "Negative changes beat the additive hitter-plus-pitcher profile baseline.",
        "",
        "| Target | Challenger | Baseline | Log-loss change | Brier change | Better folds |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in report["comparisons_to_additive"]:
        lines.append(
            f"| {row['target']} | {row['model']} | {row['baseline']} | "
            f"{row['log_loss_change']:+.8f} | "
            f"{row['brier_change']:+.8f} | {row['improved_folds']}/{row['fold_count']} |"
        )
    lines.extend(
        [
            "",
            "The baseball challenger contains only predeclared profile interactions.",
            "Handed models add heavily regressed hitter-vs-pitcher-hand and",
            "pitcher-vs-batter-side profiles; handed interactions are judged against",
            "the handed additive baseline, not against the weaker overall baseline.",
            "The full bilinear model estimates every hitter-profile by pitcher-profile",
            "product; rank-2 retains only its two strongest latent interaction patterns.",
            "All profiles use only seasons before the predicted plate appearance.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = _parser().parse_args()
    terminal = _read_terminal(args.input_root)
    events = add_matchup_outcomes(classify_battery_plate_appearances(terminal))
    hitters = build_prior_profiles(
        events,
        player_column="batter_id",
        prefix="h",
        target_seasons=TARGET_YEARS,
    )
    pitchers = build_prior_profiles(
        events,
        player_column="pitcher_id",
        prefix="p",
        target_seasons=TARGET_YEARS,
    )
    hitter_splits = build_prior_split_profiles(
        events,
        player_column="batter_id",
        split_column="pitcher_hand",
        prefix="hs",
        overall_profiles=hitters,
        target_seasons=TARGET_YEARS,
    )
    pitcher_splits = build_prior_split_profiles(
        events,
        player_column="pitcher_id",
        split_column="batter_side",
        prefix="ps",
        overall_profiles=pitchers,
        target_seasons=TARGET_YEARS,
    )
    cells = build_matchup_cells(
        events, hitter_profiles=hitters, pitcher_profiles=pitchers
    )
    cells = (
        cells.join(
            hitter_splits.rename(
                {"target_season": "season", "player_id": "batter_id"}
            ),
            on=["season", "batter_id", "pitcher_hand"],
            how="left",
            validate="m:1",
        )
        .join(
            pitcher_splits.rename(
                {"target_season": "season", "player_id": "pitcher_id"}
            ),
            on=["season", "pitcher_id", "batter_side"],
            how="left",
            validate="m:1",
        )
        .with_columns(
            *[
                pl.col(f"hs_{name}").fill_null(pl.col(f"h_{name}"))
                for name in PROFILE_NAMES
            ],
            *[
                pl.col(f"ps_{name}").fill_null(pl.col(f"p_{name}"))
                for name in PROFILE_NAMES
            ],
            pl.col("hs_history_pa").fill_null(0.0),
            pl.col("ps_history_pa").fill_null(0.0),
        )
        .filter(pl.col("season").is_in(TARGET_YEARS))
    )

    all_fold_rows: list[dict[str, Any]] = []
    tuning_history: list[dict[str, Any]] = []
    player_chunks: list[pl.DataFrame] = []
    segment_rows: list[dict[str, Any]] = []
    for target_year in EVALUATION_YEARS:
        train = [
            cells.filter(pl.col("season") == year)
            for year in TARGET_YEARS
            if year < target_year
        ]
        test = cells.filter(pl.col("season") == target_year)
        mean, scale = _weighted_scaler(train)
        base_dimension = _design(train[0].head(1), mean, scale, "additive").shape[1]
        coefficients: dict[str, dict[tuple[str, float], np.ndarray]] = {}
        for model in (
            "additive",
            "handed_additive",
            "baseball_interactions",
            "handed_interactions",
            "full_bilinear",
        ):
            equations = _normal_equations(
                train, mean=mean, scale=scale, model=model
            )
            coefficients[model] = _fit_coefficients(
                equations,
                model=model,
                base_dimension=base_dimension,
            )
            if model == "full_bilinear":
                coefficients["rank2_bilinear"] = _fit_coefficients(
                    equations,
                    model="rank2_bilinear",
                    base_dimension=base_dimension,
                )
        fold_rows, fold_player_chunks, fold_segments = _evaluate_fold(
            test,
            mean=mean,
            scale=scale,
            coefficients=coefficients,
            tuning_history=tuning_history,
            target_year=target_year,
        )
        collapsed = _collapse_fold_metrics(fold_rows)
        tuning_history.extend(collapsed.to_dicts())
        all_fold_rows.extend(fold_rows)
        player_chunks.extend(fold_player_chunks)
        segment_rows.extend(fold_segments)

    fold_metrics = _collapse_fold_metrics(all_fold_rows)
    players, player_folds = _player_metrics(player_chunks)
    segments = pl.DataFrame(segment_rows)
    report = _report(
        events=events,
        cells=cells,
        fold_metrics=fold_metrics,
        player_metrics=players,
        segments=segments,
    )
    args.output_root.mkdir(parents=True, exist_ok=True)
    fold_metrics.write_parquet(args.output_root / "fold-metrics.parquet")
    players.write_parquet(args.output_root / "player-projection-metrics.parquet")
    player_folds.write_parquet(
        args.output_root / "player-projection-fold-metrics.parquet"
    )
    segments.write_parquet(args.output_root / "segment-metrics.parquet")
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    markdown = _markdown(report)
    (args.output_root / "report.md").write_text(markdown, encoding="utf-8")
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
