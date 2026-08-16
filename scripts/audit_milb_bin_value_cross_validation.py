#!/usr/bin/env python
"""Five-fold predictive validation for MiLB Performance-bin pooling.

This is a stronger follow-up to the split-half pooling diagnostic. Each selected
45-game league-season environment is sorted chronologically and assigned to five
interleaved folds. For each fold:

- 36 games estimate the target environment's RE24 matrix and direct bin means;
- the same training fold in *other* same-level environments supplies the pooling
  prior, excluding the target environment entirely;
- the remaining 9 target-environment games are valued with the training RE24
  matrix and used only as held-out outcomes.

Every selected game is held out exactly once. The audit compares direct bin
means with fixed prior-equivalent-count shrinkage by level. It is diagnostic and
does not itself promote production weights.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from math import sqrt
import json
from pathlib import Path
from typing import Any, Mapping

import polars as pl

import audit_milb_bin_run_values as base
import audit_milb_bin_value_stability as stability
from universal_baseball.bin_value_pooling import (
    DEFAULT_PRIOR_STRENGTHS,
    shrink_mean,
)
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.official_capture import new_official_session
from universal_baseball.run_expectancy import (
    attach_re24,
    estimate_run_expectancy,
    run_expectancy_coverage,
)


POOL_GROUP_BY_LEAGUE = {
    112: "AAA",
    117: "AAA",
    121: "ROOKIE_COMPLEX",
    124: "ROOKIE_COMPLEX",
    130: "ROOKIE_COMPLEX",
}
FOLD_COUNT = 5
DEFAULT_GAMES_PER_ENVIRONMENT = 45


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--games-per-environment",
        type=int,
        default=DEFAULT_GAMES_PER_ENVIRONMENT,
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/milb-bin-value-cross-validation"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/milb-bin-value-cross-validation"),
    )
    return parser.parse_args()


def _concat(frames: list[pl.DataFrame]) -> pl.DataFrame:
    if not frames:
        raise ValueError("cannot concatenate an empty frame list")
    return pl.concat(frames, how="vertical_relaxed")


def _terminal_core_join(
    performance: pl.DataFrame,
    valued_transitions: pl.DataFrame,
) -> tuple[pl.DataFrame, int]:
    terminal = valued_transitions.filter(
        pl.col("is_plate_appearance_result") & pl.col("re24_available")
    ).select(["game_pk", "at_bat_index", "re24"])
    core = performance.filter(
        pl.col("fabio_core_bin_pre_foul_screen").is_not_null()
    )
    joined = core.join(terminal, on=["game_pk", "at_bat_index"], how="inner")
    return joined, core.height


def _training_summary(
    performance_frames: list[pl.DataFrame],
    transition_frames: list[pl.DataFrame],
) -> tuple[pl.DataFrame, dict[str, dict[str, float | int]], dict[str, Any]]:
    performance = _concat(performance_frames)
    transitions = _concat(transition_frames)
    matrix = estimate_run_expectancy(transitions)
    if matrix.height != 24:
        raise RuntimeError(
            f"training fold observed {matrix.height}/24 RE states; refusing sparse-state validation"
        )
    valued = attach_re24(transitions, matrix)
    coverage = run_expectancy_coverage(valued)
    if coverage["re24_missing_count"] != 0:
        raise RuntimeError(f"training RE24 coverage is incomplete: {coverage}")
    joined, core_count = _terminal_core_join(performance, valued)
    if joined.height != core_count:
        raise RuntimeError(
            f"training core join incomplete: {joined.height}/{core_count}"
        )
    weights_frame = (
        joined.group_by("fabio_core_bin_pre_foul_screen")
        .agg(
            pl.len().alias("occurrence_count"),
            pl.col("re24").mean().alias("mean_re24"),
        )
        .sort("fabio_core_bin_pre_foul_screen")
    )
    weights = {
        str(row["fabio_core_bin_pre_foul_screen"]): {
            "mean": float(row["mean_re24"]),
            "n": int(row["occurrence_count"]),
        }
        for row in weights_frame.to_dicts()
    }
    return matrix, weights, {
        "game_count": transitions.get_column("game_pk").n_unique(),
        "transition_count": transitions.height,
        "performance_pa_count": performance.height,
        "core_pa_count": core_count,
        "core_joined_count": joined.height,
        "observed_state_count": matrix.height,
        "re24_coverage": coverage,
    }


def _holdout_summary(
    performance_frames: list[pl.DataFrame],
    transition_frames: list[pl.DataFrame],
    training_matrix: pl.DataFrame,
) -> tuple[dict[str, list[float]], dict[str, Any]]:
    performance = _concat(performance_frames)
    transitions = _concat(transition_frames)
    valued = attach_re24(transitions, training_matrix)
    coverage = run_expectancy_coverage(valued)
    if coverage["re24_missing_count"] != 0:
        raise RuntimeError(f"holdout RE24 coverage is incomplete: {coverage}")
    joined, core_count = _terminal_core_join(performance, valued)
    if joined.height != core_count:
        raise RuntimeError(
            f"holdout core join incomplete: {joined.height}/{core_count}"
        )
    by_bin: dict[str, list[float]] = defaultdict(list)
    for row in joined.select(
        ["fabio_core_bin_pre_foul_screen", "re24"]
    ).to_dicts():
        by_bin[str(row["fabio_core_bin_pre_foul_screen"])].append(float(row["re24"]))
    return dict(by_bin), {
        "game_count": transitions.get_column("game_pk").n_unique(),
        "transition_count": transitions.height,
        "performance_pa_count": performance.height,
        "core_pa_count": core_count,
        "core_joined_count": joined.height,
        "re24_coverage": coverage,
    }


def _fold_assignment(
    game_frames: list[tuple[dict[str, Any], pl.DataFrame, pl.DataFrame]],
    fold_count: int,
) -> list[list[tuple[dict[str, Any], pl.DataFrame, pl.DataFrame]]]:
    ordered = sorted(
        game_frames,
        key=lambda item: (str(item[0]["game_date"]), int(item[0]["game_pk"])),
    )
    folds: list[list[tuple[dict[str, Any], pl.DataFrame, pl.DataFrame]]] = [
        [] for _ in range(fold_count)
    ]
    for index, item in enumerate(ordered):
        folds[index % fold_count].append(item)
    return folds


def _prior_for_bin(
    training_weights: Mapping[str, Mapping[str, Mapping[str, float | int]]],
    *,
    target_environment: str,
    target_group: str,
    bin_name: str,
    group_by_environment: Mapping[str, str],
) -> tuple[float, int, int]:
    peers: list[Mapping[str, float | int]] = []
    peer_environments: list[str] = []
    for environment_id, weights in training_weights.items():
        if environment_id == target_environment:
            continue
        if group_by_environment[environment_id] != target_group:
            continue
        if bin_name not in weights:
            continue
        peers.append(weights[bin_name])
        peer_environments.append(environment_id)
    if not peers:
        raise RuntimeError(
            f"no same-group training prior for {target_environment} {bin_name}"
        )
    total_n = sum(int(row["n"]) for row in peers)
    prior_mean = sum(float(row["mean"]) * int(row["n"]) for row in peers) / total_n
    return prior_mean, total_n, len(peer_environments)


def _cell_error_summary(
    values: list[float],
    prediction: float,
) -> dict[str, float | int]:
    if not values:
        raise ValueError("held-out bin has no values")
    mean_value = sum(values) / len(values)
    event_errors = [prediction - value for value in values]
    return {
        "holdout_count": len(values),
        "holdout_mean_re24": mean_value,
        "cell_error": prediction - mean_value,
        "cell_absolute_error": abs(prediction - mean_value),
        "event_absolute_error_sum": sum(abs(value) for value in event_errors),
        "event_squared_error_sum": sum(value * value for value in event_errors),
    }


def _metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("cannot score an empty cross-validation result")
    event_count = sum(int(row["holdout_count"]) for row in rows)
    return {
        "cell_count": len(rows),
        "event_count": event_count,
        "cell_mae": sum(float(row["cell_absolute_error"]) for row in rows) / len(rows),
        "cell_rmse": sqrt(
            sum(float(row["cell_error"]) ** 2 for row in rows) / len(rows)
        ),
        "event_mae": sum(float(row["event_absolute_error_sum"]) for row in rows)
        / event_count,
        "event_rmse": sqrt(
            sum(float(row["event_squared_error_sum"]) for row in rows) / event_count
        ),
        "max_cell_absolute_error": max(
            float(row["cell_absolute_error"]) for row in rows
        ),
    }


def _robust_strengths(evaluations: list[dict[str, Any]]) -> list[int]:
    direct = next(row for row in evaluations if int(row["prior_strength"]) == 0)
    metrics = ("cell_mae", "cell_rmse", "event_mae", "event_rmse")
    return [
        int(row["prior_strength"])
        for row in evaluations
        if int(row["prior_strength"]) > 0
        and all(float(row[metric]) <= float(direct[metric]) for metric in metrics)
    ]


def _candidate(evaluations: list[dict[str, Any]]) -> dict[str, Any]:
    robust = set(_robust_strengths(evaluations))
    if not robust:
        direct = next(row for row in evaluations if int(row["prior_strength"]) == 0)
        return {
            "prior_strength": 0,
            "reason": "no positive strength improved cell MAE/RMSE and event MAE/RMSE together",
            "metrics": {key: direct[key] for key in ("cell_mae", "cell_rmse", "event_mae", "event_rmse")},
        }
    eligible = [row for row in evaluations if int(row["prior_strength"]) in robust]
    best = min(
        eligible,
        key=lambda row: (float(row["cell_mae"]), int(row["prior_strength"])),
    )
    return {
        "prior_strength": int(best["prior_strength"]),
        "reason": "lowest cell MAE among strengths improving all four predictive error summaries",
        "metrics": {key: best[key] for key in ("cell_mae", "cell_rmse", "event_mae", "event_rmse")},
    }


def main() -> int:
    args = parse_args()
    if args.games_per_environment < FOLD_COUNT * 4:
        raise ValueError("games-per-environment is too small for five-fold validation")
    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)

    asset_frames: dict[str, pl.DataFrame] = {}
    asset_snapshots: dict[str, str] = {}
    asset_normalizations: dict[str, Any] = {}
    environment_orders: dict[tuple[int, int, str], list[dict[str, Any]]] = {}

    for asset in base.DEFAULT_ASSETS:
        path = args.work_dir / asset
        metadata = download_file(
            f"{base.BASE_URL}/{asset}", path, timeout_seconds=240
        )
        frame = read_quarantined_csv(path)
        snapshot_id, normalization = base._asset_source_identity(
            asset, str(metadata["sha256"])
        )
        asset_frames[asset] = frame
        asset_snapshots[asset] = snapshot_id
        asset_normalizations[asset] = normalization
        for key, order in stability._inventory_orders(
            frame,
            asset,
            max_games=args.games_per_environment,
        ).items():
            if key in environment_orders:
                raise RuntimeError(f"environment spans multiple selected assets: {key}")
            environment_orders[key] = order

    insufficient = {
        key: len(order)
        for key, order in environment_orders.items()
        if len(order) < args.games_per_environment
    }
    if insufficient:
        raise RuntimeError(
            f"selected source assets lack game target for environments: {insufficient}"
        )

    per_environment_frames: dict[
        tuple[int, int, str],
        list[tuple[dict[str, Any], pl.DataFrame, pl.DataFrame]],
    ] = defaultdict(list)
    session = new_official_session()
    try:
        for key in sorted(environment_orders):
            for game in environment_orders[key]:
                performance, transitions = stability._process_game(
                    game,
                    source_frame=asset_frames[str(game["asset"])],
                    source_snapshot_id=asset_snapshots[str(game["asset"])],
                    source_normalization=asset_normalizations[str(game["asset"])],
                    session=session,
                )
                per_environment_frames[key].append((game, performance, transitions))
    finally:
        session.close()

    environment_meta: dict[str, dict[str, Any]] = {}
    group_by_environment: dict[str, str] = {}
    folds_by_environment: dict[
        str, list[list[tuple[dict[str, Any], pl.DataFrame, pl.DataFrame]]]
    ] = {}
    for key, game_frames in sorted(per_environment_frames.items()):
        season, league_id, league_name = key
        if league_id not in POOL_GROUP_BY_LEAGUE:
            raise RuntimeError(f"pool group missing for league_id={league_id}")
        environment_id = f"{season}:{league_id}"
        folds = _fold_assignment(game_frames, FOLD_COUNT)
        if any(len(fold) == 0 for fold in folds):
            raise RuntimeError(f"empty cross-validation fold for {environment_id}")
        folds_by_environment[environment_id] = folds
        group_by_environment[environment_id] = POOL_GROUP_BY_LEAGUE[league_id]
        environment_meta[environment_id] = {
            "season": season,
            "league_id": league_id,
            "league_name": league_name,
            "pool_group": POOL_GROUP_BY_LEAGUE[league_id],
            "game_count": len(game_frames),
            "fold_game_counts": [len(fold) for fold in folds],
            "fold_games": [
                [
                    {
                        "game_pk": int(item[0]["game_pk"]),
                        "game_date": str(item[0]["game_date"]),
                    }
                    for item in fold
                ]
                for fold in folds
            ],
        }

    prediction_rows: list[dict[str, Any]] = []
    fold_diagnostics: list[dict[str, Any]] = []
    strengths = list(DEFAULT_PRIOR_STRENGTHS)

    for fold_index in range(FOLD_COUNT):
        training_weights: dict[str, dict[str, dict[str, float | int]]] = {}
        training_matrices: dict[str, pl.DataFrame] = {}
        holdout_values: dict[str, dict[str, list[float]]] = {}
        fold_environment_diagnostics: list[dict[str, Any]] = []

        for environment_id, folds in sorted(folds_by_environment.items()):
            holdout = folds[fold_index]
            training = [
                item
                for index, fold in enumerate(folds)
                if index != fold_index
                for item in fold
            ]
            matrix, weights, training_diag = _training_summary(
                [item[1] for item in training],
                [item[2] for item in training],
            )
            values, holdout_diag = _holdout_summary(
                [item[1] for item in holdout],
                [item[2] for item in holdout],
                matrix,
            )
            training_matrices[environment_id] = matrix
            training_weights[environment_id] = weights
            holdout_values[environment_id] = values
            fold_environment_diagnostics.append(
                {
                    "environment_id": environment_id,
                    "training": training_diag,
                    "holdout": holdout_diag,
                    "training_bin_count": len(weights),
                    "holdout_bin_count": len(values),
                }
            )

        for environment_id, values_by_bin in sorted(holdout_values.items()):
            target_group = group_by_environment[environment_id]
            target_weights = training_weights[environment_id]
            for bin_name, values in sorted(values_by_bin.items()):
                if bin_name not in target_weights:
                    raise RuntimeError(
                        f"target training fold lacks held-out bin {environment_id} {bin_name}"
                    )
                prior_mean, prior_n, prior_environment_count = _prior_for_bin(
                    training_weights,
                    target_environment=environment_id,
                    target_group=target_group,
                    bin_name=bin_name,
                    group_by_environment=group_by_environment,
                )
                target = target_weights[bin_name]
                for strength in strengths:
                    prediction = shrink_mean(
                        float(target["mean"]),
                        int(target["n"]),
                        prior_mean,
                        int(strength),
                    )
                    prediction_rows.append(
                        {
                            "fold": fold_index,
                            "environment_id": environment_id,
                            **environment_meta[environment_id],
                            "bin": bin_name,
                            "prior_strength": int(strength),
                            "training_mean_re24": float(target["mean"]),
                            "training_count": int(target["n"]),
                            "prior_mean_re24": prior_mean,
                            "prior_candidate_count": prior_n,
                            "prior_environment_count": prior_environment_count,
                            "prediction": prediction,
                            **_cell_error_summary(values, prediction),
                        }
                    )
        fold_diagnostics.append(
            {
                "fold": fold_index,
                "environments": fold_environment_diagnostics,
            }
        )

    groups = sorted(set(group_by_environment.values()))
    evaluations: dict[str, list[dict[str, Any]]] = {}
    decisions: dict[str, Any] = {}
    for group in groups:
        group_evaluations: list[dict[str, Any]] = []
        for strength in strengths:
            rows = [
                row
                for row in prediction_rows
                if row["pool_group"] == group
                and int(row["prior_strength"]) == int(strength)
            ]
            group_evaluations.append(
                {
                    "pool_group": group,
                    "prior_strength": int(strength),
                    **_metrics(rows),
                }
            )
        direct = next(
            row for row in group_evaluations if int(row["prior_strength"]) == 0
        )
        for row in group_evaluations:
            for metric in ("cell_mae", "cell_rmse", "event_mae", "event_rmse"):
                row[f"{metric}_delta_vs_direct"] = float(row[metric]) - float(direct[metric])
        evaluations[group] = group_evaluations
        decisions[group] = {
            "robust_improvement_strengths": _robust_strengths(group_evaluations),
            "candidate_for_next_validation": _candidate(group_evaluations),
            "best_strength_by_metric": {
                metric: {
                    "prior_strength": int(
                        min(
                            group_evaluations,
                            key=lambda row: (float(row[metric]), int(row["prior_strength"])),
                        )["prior_strength"]
                    ),
                    metric: float(
                        min(
                            group_evaluations,
                            key=lambda row: (float(row[metric]), int(row["prior_strength"])),
                        )[metric]
                    ),
                }
                for metric in ("cell_mae", "cell_rmse", "event_mae", "event_rmse")
            },
        }

    payload = {
        "report_schema_version": 1,
        "status": "five_fold_predictive_pooling_validation_not_production_weights",
        "fold_count": FOLD_COUNT,
        "games_per_environment": args.games_per_environment,
        "prior_strengths": strengths,
        "pool_group_by_league": {
            str(key): value for key, value in POOL_GROUP_BY_LEAGUE.items()
        },
        "environment_meta": environment_meta,
        "fold_diagnostics": fold_diagnostics,
        "group_evaluations": evaluations,
        "diagnostic_decisions": decisions,
        "prediction_cells": prediction_rows,
        "interpretation": (
            "Every selected game is held out exactly once. Target-environment held-out games "
            "never contribute to target bin means, the target environment never contributes "
            "to its same-level prior, and held-out data never contribute to any prior. Held-out "
            "transitions are valued with the target training fold's RE24 matrix. Candidate "
            "strengths remain diagnostic until a production-value ADR is accepted."
        ),
    }
    (args.report_dir / "milb_bin_value_cross_validation.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# MiLB Performance-bin pooling five-fold validation",
        "",
        "**Predictive diagnostic only. No sampled weight or shrinkage constant is production yet.**",
        "",
        f"- Environments: {len(environment_meta)}",
        f"- Games per environment: {args.games_per_environment}",
        f"- Folds: {FOLD_COUNT} (chronological interleaving; every game held out exactly once)",
        f"- Prior strengths: {strengths}",
        "- Target environment excluded from its same-level prior; all held-out data excluded from priors",
        "",
    ]
    for group in groups:
        rows = evaluations[group]
        direct = next(row for row in rows if int(row["prior_strength"]) == 0)
        decision = decisions[group]
        strength = int(decision["candidate_for_next_validation"]["prior_strength"])
        candidate = next(row for row in rows if int(row["prior_strength"]) == strength)
        lines.extend(
            [
                f"## {group}",
                "",
                f"- Direct: cell MAE={direct['cell_mae']:.4f}, cell RMSE={direct['cell_rmse']:.4f}, event MAE={direct['event_mae']:.4f}, event RMSE={direct['event_rmse']:.4f}",
                f"- Robust positive strengths: {decision['robust_improvement_strengths']}",
                f"- Cross-validation candidate: **{strength}** prior-equivalent occurrences",
                f"- Candidate: cell MAE={candidate['cell_mae']:.4f}, cell RMSE={candidate['cell_rmse']:.4f}, event MAE={candidate['event_mae']:.4f}, event RMSE={candidate['event_rmse']:.4f}",
                f"- Candidate reason: {decision['candidate_for_next_validation']['reason']}",
                "",
            ]
        )
    lines.extend(
        [
            "The split-half diagnostic and this five-fold predictive audit should agree before a positive shrinkage rule is considered for freezing. Disagreement is evidence to keep direct values or expand the sample rather than force a pooling rule.",
            "",
        ]
    )
    summary = "\n".join(lines)
    (args.report_dir / "milb_bin_value_cross_validation.md").write_text(
        summary, encoding="utf-8"
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
