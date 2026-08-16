#!/usr/bin/env python
"""Independent-season confirmation of the pre-specified AAA pooling rule.

The 2025 AAA diagnostics identified 25 prior-equivalent occurrences as a
conservative strength inside the robust region shared by the split-half and
five-fold tests. This audit does *not* re-select that strength on 2024 data.
It asks one primary question on an independent season:

    Does same-level leave-one-league-out shrinkage with lambda=25 improve
    direct league bin means on all four held-out predictive error summaries?

The source is the 2024 June AAA reusable PBP asset. PCL and IL are each capped
at 45 games, sorted chronologically, and assigned to five interleaved folds.
For every fold, 36 target-league games estimate RE24 and direct bin means; the
other AAA league's 36 training games supply the same-bin prior; the remaining
9 target-league games are held out completely and valued with the target
training RE24 matrix. Every selected game is held out exactly once.

This remains a certification diagnostic. It does not itself promote production
weights or player scores.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from typing import Any

import polars as pl

import audit_milb_bin_run_values as base
import audit_milb_bin_value_cross_validation as cv
import audit_milb_bin_value_stability as stability
from universal_baseball.bin_value_pooling import DEFAULT_PRIOR_STRENGTHS, shrink_mean
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.official_capture import new_official_session


ASSET = "2024_6_aaa_pbp.csv"
TARGET_LEAGUES = {112: "PCL", 117: "IL"}
POOL_GROUP = "AAA"
FOLD_COUNT = 5
DEFAULT_GAMES_PER_LEAGUE = 45
CONFIRMATION_STRENGTH = 25


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--games-per-league",
        type=int,
        default=DEFAULT_GAMES_PER_LEAGUE,
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/aaa-bin-value-independent-validation"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/aaa-bin-value-independent-validation"),
    )
    return parser.parse_args()


def _concat(frames: list[pl.DataFrame]) -> pl.DataFrame:
    if not frames:
        raise ValueError("cannot concatenate empty frame list")
    return pl.concat(frames, how="vertical_relaxed")


def _score_strength(
    *,
    strength: int,
    target_environment: str,
    target_weights: dict[str, dict[str, float | int]],
    peer_weights: dict[str, dict[str, float | int]],
    holdout_values: dict[str, list[float]],
    fold_index: int,
    meta: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bin_name, values in sorted(holdout_values.items()):
        if bin_name not in target_weights:
            raise RuntimeError(
                f"target training fold lacks held-out bin {target_environment} {bin_name}"
            )
        if bin_name not in peer_weights:
            raise RuntimeError(
                f"peer AAA training fold lacks prior bin {target_environment} {bin_name}"
            )
        target = target_weights[bin_name]
        peer = peer_weights[bin_name]
        prediction = shrink_mean(
            float(target["mean"]),
            int(target["n"]),
            float(peer["mean"]),
            strength,
        )
        rows.append(
            {
                "fold": fold_index,
                "environment_id": target_environment,
                "season": int(meta["season"]),
                "league_id": int(meta["league_id"]),
                "league_name": str(meta["league_name"]),
                "pool_group": POOL_GROUP,
                "bin": bin_name,
                "prior_strength": strength,
                "training_mean_re24": float(target["mean"]),
                "training_count": int(target["n"]),
                "prior_mean_re24": float(peer["mean"]),
                "prior_candidate_count": int(peer["n"]),
                "prior_environment_count": 1,
                "prediction": prediction,
                **cv._cell_error_summary(values, prediction),
            }
        )
    return rows


def _metric_comparison(
    direct: dict[str, Any],
    confirmation: dict[str, Any],
) -> dict[str, Any]:
    metrics = ("cell_mae", "cell_rmse", "event_mae", "event_rmse")
    return {
        metric: {
            "direct": float(direct[metric]),
            "confirmation": float(confirmation[metric]),
            "delta": float(confirmation[metric]) - float(direct[metric]),
            "improved_or_tied": float(confirmation[metric]) <= float(direct[metric]),
        }
        for metric in metrics
    }


def main() -> int:
    args = parse_args()
    if args.games_per_league < FOLD_COUNT * 4:
        raise ValueError("games-per-league is too small for five-fold validation")
    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)

    path = args.work_dir / ASSET
    metadata = download_file(f"{base.BASE_URL}/{ASSET}", path, timeout_seconds=240)
    source_frame = read_quarantined_csv(path)
    if source_frame.is_empty():
        raise RuntimeError(f"independent AAA source asset is empty: {ASSET}")
    snapshot_id, normalization = base._asset_source_identity(
        ASSET, str(metadata["sha256"])
    )

    inventory = stability._inventory_orders(
        source_frame,
        ASSET,
        max_games=args.games_per_league,
    )
    environment_orders = {
        key: order
        for key, order in inventory.items()
        if int(key[1]) in TARGET_LEAGUES
    }
    observed_leagues = {int(key[1]) for key in environment_orders}
    if observed_leagues != set(TARGET_LEAGUES):
        raise RuntimeError(
            f"expected 2024 AAA leagues {sorted(TARGET_LEAGUES)}, observed {sorted(observed_leagues)}"
        )
    insufficient = {
        f"{key[0]}:{key[1]}": len(order)
        for key, order in environment_orders.items()
        if len(order) < args.games_per_league
    }
    if insufficient:
        raise RuntimeError(
            f"independent asset lacks requested game target: {insufficient}"
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
                    source_frame=source_frame,
                    source_snapshot_id=snapshot_id,
                    source_normalization=normalization,
                    session=session,
                )
                per_environment_frames[key].append((game, performance, transitions))
    finally:
        session.close()

    environment_meta: dict[str, dict[str, Any]] = {}
    folds_by_environment: dict[
        str, list[list[tuple[dict[str, Any], pl.DataFrame, pl.DataFrame]]]
    ] = {}
    for key, game_frames in sorted(per_environment_frames.items()):
        season, league_id, league_name = key
        environment_id = f"{season}:{league_id}"
        folds = cv._fold_assignment(game_frames, FOLD_COUNT)
        if any(len(fold) == 0 for fold in folds):
            raise RuntimeError(f"empty fold for {environment_id}")
        folds_by_environment[environment_id] = folds
        environment_meta[environment_id] = {
            "season": int(season),
            "league_id": int(league_id),
            "league_name": str(league_name),
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

    if len(folds_by_environment) != 2:
        raise RuntimeError(
            f"independent AAA confirmation requires exactly two environments; got {sorted(folds_by_environment)}"
        )

    strengths = list(DEFAULT_PRIOR_STRENGTHS)
    if CONFIRMATION_STRENGTH not in strengths:
        strengths.append(CONFIRMATION_STRENGTH)
        strengths.sort()

    prediction_rows: list[dict[str, Any]] = []
    fold_diagnostics: list[dict[str, Any]] = []
    environment_ids = sorted(folds_by_environment)

    for fold_index in range(FOLD_COUNT):
        training_weights: dict[str, dict[str, dict[str, float | int]]] = {}
        holdout_values: dict[str, dict[str, list[float]]] = {}
        fold_environment_diagnostics: list[dict[str, Any]] = []

        for environment_id in environment_ids:
            folds = folds_by_environment[environment_id]
            holdout = folds[fold_index]
            training = [
                item
                for index, fold in enumerate(folds)
                if index != fold_index
                for item in fold
            ]
            matrix, weights, training_diag = cv._training_summary(
                [item[1] for item in training],
                [item[2] for item in training],
            )
            values, holdout_diag = cv._holdout_summary(
                [item[1] for item in holdout],
                [item[2] for item in holdout],
                matrix,
            )
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

        for target_environment in environment_ids:
            peer_environment = next(
                value for value in environment_ids if value != target_environment
            )
            for strength in strengths:
                prediction_rows.extend(
                    _score_strength(
                        strength=int(strength),
                        target_environment=target_environment,
                        target_weights=training_weights[target_environment],
                        peer_weights=training_weights[peer_environment],
                        holdout_values=holdout_values[target_environment],
                        fold_index=fold_index,
                        meta=environment_meta[target_environment],
                    )
                )

        fold_diagnostics.append(
            {
                "fold": fold_index,
                "environments": fold_environment_diagnostics,
            }
        )

    evaluations: list[dict[str, Any]] = []
    for strength in strengths:
        rows = [
            row for row in prediction_rows if int(row["prior_strength"]) == int(strength)
        ]
        evaluations.append(
            {
                "prior_strength": int(strength),
                **cv._metrics(rows),
            }
        )

    direct = next(row for row in evaluations if int(row["prior_strength"]) == 0)
    confirmation = next(
        row
        for row in evaluations
        if int(row["prior_strength"]) == CONFIRMATION_STRENGTH
    )
    comparisons = _metric_comparison(direct, confirmation)
    confirmation_pass = all(
        bool(value["improved_or_tied"]) for value in comparisons.values()
    )
    robust_strengths = cv._robust_strengths(evaluations)
    best_by_metric = {
        metric: {
            "prior_strength": int(
                min(
                    evaluations,
                    key=lambda row: (float(row[metric]), int(row["prior_strength"])),
                )["prior_strength"]
            ),
            metric: float(
                min(
                    evaluations,
                    key=lambda row: (float(row[metric]), int(row["prior_strength"])),
                )[metric]
            ),
        }
        for metric in ("cell_mae", "cell_rmse", "event_mae", "event_rmse")
    }

    payload = {
        "report_schema_version": 1,
        "status": "independent_aaa_confirmation_not_production_weights",
        "source_asset": ASSET,
        "source_sha256": str(metadata["sha256"]),
        "games_per_league": args.games_per_league,
        "fold_count": FOLD_COUNT,
        "target_leagues": TARGET_LEAGUES,
        "pre_specified_confirmation_strength": CONFIRMATION_STRENGTH,
        "environment_meta": environment_meta,
        "fold_diagnostics": fold_diagnostics,
        "evaluations": evaluations,
        "robust_improvement_strengths": robust_strengths,
        "best_strength_by_metric": best_by_metric,
        "confirmation_comparison": comparisons,
        "confirmation_pass": confirmation_pass,
        "prediction_cells": prediction_rows,
        "interpretation": (
            "The primary test is pre-specified: lambda=25 must match or improve direct "
            "league means on cell MAE, cell RMSE, event MAE, and event RMSE in the "
            "independent 2024 AAA season. The full strength grid is secondary diagnostic "
            "evidence and does not change the primary confirmation rule."
        ),
    }
    (args.report_dir / "aaa_bin_value_independent_validation.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# Independent 2024 AAA Performance-bin pooling confirmation",
        "",
        "**Pre-specified confirmation diagnostic; no production weights are promoted by this script.**",
        "",
        f"- Source asset: `{ASSET}`",
        f"- Source SHA-256: `{metadata['sha256']}`",
        f"- Games per AAA league: {args.games_per_league}",
        f"- Folds: {FOLD_COUNT}; every selected game held out exactly once",
        f"- Pre-specified confirmation strength: **{CONFIRMATION_STRENGTH}** prior-equivalent occurrences",
        f"- Confirmation pass: **{confirmation_pass}**",
        "",
        "## Primary comparison",
        "",
        f"- Direct: cell MAE={direct['cell_mae']:.4f}, cell RMSE={direct['cell_rmse']:.4f}, event MAE={direct['event_mae']:.4f}, event RMSE={direct['event_rmse']:.4f}",
        f"- Lambda {CONFIRMATION_STRENGTH}: cell MAE={confirmation['cell_mae']:.4f}, cell RMSE={confirmation['cell_rmse']:.4f}, event MAE={confirmation['event_mae']:.4f}, event RMSE={confirmation['event_rmse']:.4f}",
        "",
    ]
    for metric, result in comparisons.items():
        lines.append(
            f"- {metric}: delta={result['delta']:+.6f}; improved_or_tied={result['improved_or_tied']}"
        )
    lines.extend(
        [
            "",
            "## Secondary grid diagnostic",
            "",
            f"- Robust positive strengths: {robust_strengths}",
            f"- Best strength by metric: `{best_by_metric}`",
            "",
            "The confirmation decision is based on the pre-specified lambda=25 comparison above, not on whichever strength happens to fit 2024 best.",
            "",
        ]
    )
    summary = "\n".join(lines)
    (args.report_dir / "aaa_bin_value_independent_validation.md").write_text(
        summary, encoding="utf-8"
    )
    print(summary)
    return 0 if confirmation_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
