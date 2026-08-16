#!/usr/bin/env python
"""Confirm Performance-bin value estimation after the certified foul-air screen.

Earlier stability/pooling audits intentionally used
``fabio_core_bin_pre_foul_screen`` while foul-air eligibility was still open.
ADR 015 closes that gate. This audit rebuilds fresh Performance rows, then feeds
**screened** ``fabio_core_bin`` evidence into the already-tested stability and
cross-validation helpers by aliasing the final bin onto the legacy diagnostic
column only inside this script.

It performs three checks from fresh official PBP:

1. 45-game split-half stability/pooling on the five established environments;
2. five-fold predictive pooling on the same environments;
3. a pre-specified lambda=25 independent 2024 AAA confirmation on a separate
   June 2024 AAA source snapshot.

The target decision is deliberately asymmetric: AAA lambda=25 must remain
supported after screening; Rookie/complex is reported but is not required to
adopt positive shrinkage. No player score is produced.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from typing import Any, Mapping

import polars as pl

import audit_milb_bin_run_values as base
import audit_milb_bin_value_cross_validation as cv
import audit_milb_bin_value_stability as stability
from universal_baseball.bin_value_pooling import (
    DEFAULT_PRIOR_STRENGTHS,
    evaluate_split_half_pooling,
    shrink_mean,
)
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.official_capture import new_official_session


POOL_GROUP_BY_LEAGUE = {
    112: "AAA",
    117: "AAA",
    121: "ROOKIE_COMPLEX",
    124: "ROOKIE_COMPLEX",
    130: "ROOKIE_COMPLEX",
}
INDEPENDENT_AAA_ASSET = "2024_6_aaa_pbp.csv"
FOLD_COUNT = 5
GAMES_PER_ENVIRONMENT = 45
AAA_CONFIRMATION_STRENGTH = 25


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/screened-bin-value-confirmation"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/screened-bin-value-confirmation"),
    )
    return parser.parse_args()


def _screen_for_legacy_helpers(performance: pl.DataFrame) -> pl.DataFrame:
    """Point legacy value helpers at the final screened bin, not old evidence."""

    required = {
        "fabio_core_bin",
        "core_profile_eligible",
        "fabio_core_bin_pre_foul_screen",
        "core_profile_eligible_pre_foul_screen",
        "is_foul_air_out",
    }
    missing = sorted(required - set(performance.columns))
    if missing:
        raise ValueError(f"Performance frame missing screened-bin fields: {missing}")
    return performance.with_columns(
        pl.col("fabio_core_bin").alias("fabio_core_bin_pre_foul_screen"),
        pl.col("core_profile_eligible").alias(
            "core_profile_eligible_pre_foul_screen"
        ),
    )


def _screen_counts(performance: pl.DataFrame) -> dict[str, int]:
    pre = int(performance.get_column("core_profile_eligible_pre_foul_screen").sum())
    final = int(performance.get_column("core_profile_eligible").sum())
    foul = int(
        performance.select(
            pl.col("is_foul_air_out").fill_null(False).sum().alias("n")
        ).item()
        or 0
    )
    unknown_pre_core = int(
        performance.filter(
            pl.col("core_profile_eligible_pre_foul_screen")
            & pl.col("is_foul_air_out").is_null()
        ).height
    )
    return {
        "pre_screen_core_count": pre,
        "screened_core_count": final,
        "excluded_from_core_count": pre - final,
        "explicit_foul_air_count": foul,
        "unknown_foul_status_pre_core_count": unknown_pre_core,
    }


def _load_environment_frames(
    *,
    assets: tuple[str, ...],
    work_dir: Path,
    allowed_leagues: set[int] | None = None,
) -> tuple[
    dict[str, list[tuple[dict[str, Any], pl.DataFrame, pl.DataFrame]]],
    dict[str, dict[str, Any]],
]:
    asset_frames: dict[str, pl.DataFrame] = {}
    asset_snapshots: dict[str, str] = {}
    asset_normalizations: dict[str, Any] = {}
    environment_orders: dict[tuple[int, int, str], list[dict[str, Any]]] = {}

    for asset in assets:
        path = work_dir / asset
        metadata = download_file(f"{base.BASE_URL}/{asset}", path, timeout_seconds=240)
        frame = read_quarantined_csv(path)
        if frame.is_empty():
            raise RuntimeError(f"source asset is empty: {asset}")
        snapshot_id, normalization = base._asset_source_identity(
            asset, str(metadata["sha256"])
        )
        asset_frames[asset] = frame
        asset_snapshots[asset] = snapshot_id
        asset_normalizations[asset] = normalization
        for key, order in stability._inventory_orders(
            frame, asset, max_games=GAMES_PER_ENVIRONMENT
        ).items():
            league_id = int(key[1])
            if allowed_leagues is not None and league_id not in allowed_leagues:
                continue
            if key in environment_orders:
                raise RuntimeError(f"environment spans multiple selected assets: {key}")
            environment_orders[key] = order

    insufficient = {
        f"{key[0]}:{key[1]}": len(order)
        for key, order in environment_orders.items()
        if len(order) < GAMES_PER_ENVIRONMENT
    }
    if insufficient:
        raise RuntimeError(
            f"selected source assets lack {GAMES_PER_ENVIRONMENT}-game target: {insufficient}"
        )

    frames: dict[
        str, list[tuple[dict[str, Any], pl.DataFrame, pl.DataFrame]]
    ] = defaultdict(list)
    meta: dict[str, dict[str, Any]] = {}
    screen_accumulator: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "pre_screen_core_count": 0,
            "screened_core_count": 0,
            "excluded_from_core_count": 0,
            "explicit_foul_air_count": 0,
            "unknown_foul_status_pre_core_count": 0,
        }
    )

    session = new_official_session()
    try:
        for key in sorted(environment_orders):
            season, league_id, league_name = key
            environment_id = f"{int(season)}:{int(league_id)}"
            if int(league_id) not in POOL_GROUP_BY_LEAGUE:
                raise RuntimeError(f"pool group missing for league_id={league_id}")
            meta[environment_id] = {
                "season": int(season),
                "league_id": int(league_id),
                "league_name": str(league_name),
                "pool_group": POOL_GROUP_BY_LEAGUE[int(league_id)],
            }
            for game in environment_orders[key]:
                performance, transitions = stability._process_game(
                    game,
                    source_frame=asset_frames[str(game["asset"])],
                    source_snapshot_id=asset_snapshots[str(game["asset"])],
                    source_normalization=asset_normalizations[str(game["asset"])],
                    session=session,
                )
                counts = _screen_counts(performance)
                for name, value in counts.items():
                    screen_accumulator[environment_id][name] += int(value)
                frames[environment_id].append(
                    (game, _screen_for_legacy_helpers(performance), transitions)
                )
    finally:
        session.close()

    for environment_id in meta:
        meta[environment_id]["game_count"] = len(frames[environment_id])
        meta[environment_id]["screen"] = dict(screen_accumulator[environment_id])
    return dict(frames), meta


def _split_half_reports(
    frames: Mapping[str, list[tuple[dict[str, Any], pl.DataFrame, pl.DataFrame]]],
    meta: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for environment_id in sorted(frames):
        game_frames = frames[environment_id]
        split_a = game_frames[0::2]
        split_b = game_frames[1::2]
        a = stability._sample_value_result(
            [item[1] for item in split_a], [item[2] for item in split_a]
        )
        b = stability._sample_value_result(
            [item[1] for item in split_b], [item[2] for item in split_b]
        )
        reports.append(
            {
                "season": int(meta[environment_id]["season"]),
                "league_id": int(meta[environment_id]["league_id"]),
                "league_name": str(meta[environment_id]["league_name"]),
                "split_half": {
                    "candidate": {
                        "game_count": len(split_a),
                        **{key: value for key, value in a.items() if key != "weights"},
                    },
                    "reference": {
                        "game_count": len(split_b),
                        **{key: value for key, value in b.items() if key != "weights"},
                    },
                    "comparison": stability._compare_weights(a, b),
                },
            }
        )
    pooling = evaluate_split_half_pooling(
        reports,
        pool_group_by_league=POOL_GROUP_BY_LEAGUE,
        prior_strengths=DEFAULT_PRIOR_STRENGTHS,
        scope="group",
    )
    return reports, pooling


def _fivefold(
    frames: Mapping[str, list[tuple[dict[str, Any], pl.DataFrame, pl.DataFrame]]],
    meta: Mapping[str, Mapping[str, Any]],
    *,
    groups_to_score: set[str] | None = None,
) -> dict[str, Any]:
    folds_by_environment = {
        environment_id: cv._fold_assignment(list(game_frames), FOLD_COUNT)
        for environment_id, game_frames in frames.items()
    }
    if any(
        any(len(fold) == 0 for fold in folds)
        for folds in folds_by_environment.values()
    ):
        raise RuntimeError("empty five-fold validation fold")

    group_by_environment = {
        environment_id: str(meta[environment_id]["pool_group"])
        for environment_id in frames
    }
    prediction_rows: list[dict[str, Any]] = []
    fold_diagnostics: list[dict[str, Any]] = []

    for fold_index in range(FOLD_COUNT):
        training_weights: dict[str, dict[str, dict[str, float | int]]] = {}
        holdout_values: dict[str, dict[str, list[float]]] = {}
        environment_diag: list[dict[str, Any]] = []

        for environment_id, folds in sorted(folds_by_environment.items()):
            holdout = folds[fold_index]
            training = [
                item
                for index, fold in enumerate(folds)
                if index != fold_index
                for item in fold
            ]
            matrix, weights, training_diag = cv._training_summary(
                [item[1] for item in training], [item[2] for item in training]
            )
            values, holdout_diag = cv._holdout_summary(
                [item[1] for item in holdout],
                [item[2] for item in holdout],
                matrix,
            )
            training_weights[environment_id] = weights
            holdout_values[environment_id] = values
            environment_diag.append(
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
            if groups_to_score is not None and target_group not in groups_to_score:
                continue
            target_weights = training_weights[environment_id]
            for bin_name, values in sorted(values_by_bin.items()):
                if bin_name not in target_weights:
                    raise RuntimeError(
                        f"target training lacks held-out bin {environment_id} {bin_name}"
                    )
                prior_mean, prior_n, prior_environment_count = cv._prior_for_bin(
                    training_weights,
                    target_environment=environment_id,
                    target_group=target_group,
                    bin_name=bin_name,
                    group_by_environment=group_by_environment,
                )
                target = target_weights[bin_name]
                for strength in DEFAULT_PRIOR_STRENGTHS:
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
                            "pool_group": target_group,
                            "bin": bin_name,
                            "prior_strength": int(strength),
                            "training_mean_re24": float(target["mean"]),
                            "training_count": int(target["n"]),
                            "prior_mean_re24": prior_mean,
                            "prior_candidate_count": prior_n,
                            "prior_environment_count": prior_environment_count,
                            "prediction": prediction,
                            **cv._cell_error_summary(values, prediction),
                        }
                    )
        fold_diagnostics.append({"fold": fold_index, "environments": environment_diag})

    groups = sorted({row["pool_group"] for row in prediction_rows})
    evaluations: dict[str, list[dict[str, Any]]] = {}
    decisions: dict[str, Any] = {}
    for group in groups:
        rows_for_group: list[dict[str, Any]] = []
        for strength in DEFAULT_PRIOR_STRENGTHS:
            rows = [
                row
                for row in prediction_rows
                if row["pool_group"] == group
                and int(row["prior_strength"]) == int(strength)
            ]
            rows_for_group.append(
                {
                    "pool_group": group,
                    "prior_strength": int(strength),
                    **cv._metrics(rows),
                }
            )
        direct = next(row for row in rows_for_group if row["prior_strength"] == 0)
        for row in rows_for_group:
            for metric in ("cell_mae", "cell_rmse", "event_mae", "event_rmse"):
                row[f"{metric}_delta_vs_direct"] = float(row[metric]) - float(
                    direct[metric]
                )
        evaluations[group] = rows_for_group
        decisions[group] = {
            "robust_improvement_strengths": cv._robust_strengths(rows_for_group),
            "candidate": cv._candidate(rows_for_group),
        }

    return {
        "fold_count": FOLD_COUNT,
        "group_evaluations": evaluations,
        "decisions": decisions,
        "fold_diagnostics": fold_diagnostics,
        "prediction_cells": prediction_rows,
    }


def _aaa_confirmation(fivefold: Mapping[str, Any]) -> dict[str, Any]:
    evaluations = list(fivefold["group_evaluations"]["AAA"])
    direct = next(row for row in evaluations if int(row["prior_strength"]) == 0)
    lam25 = next(
        row
        for row in evaluations
        if int(row["prior_strength"]) == AAA_CONFIRMATION_STRENGTH
    )
    metrics = ("cell_mae", "cell_rmse", "event_mae", "event_rmse")
    comparison = {
        metric: {
            "direct": float(direct[metric]),
            "lambda_25": float(lam25[metric]),
            "delta": float(lam25[metric]) - float(direct[metric]),
            "improved_or_tied": float(lam25[metric]) <= float(direct[metric]),
        }
        for metric in metrics
    }
    return {
        "pre_specified_strength": AAA_CONFIRMATION_STRENGTH,
        "comparison": comparison,
        "pass": all(value["improved_or_tied"] for value in comparison.values()),
        "robust_improvement_strengths": cv._robust_strengths(evaluations),
    }


def main() -> int:
    args = parse_args()
    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)

    primary_frames, primary_meta = _load_environment_frames(
        assets=tuple(base.DEFAULT_ASSETS),
        work_dir=args.work_dir / "primary",
    )
    if set(primary_frames) != {"2025:112", "2025:117", "2024:121", "2024:124", "2024:130"}:
        raise RuntimeError(f"unexpected primary environments: {sorted(primary_frames)}")

    split_reports, split_pooling = _split_half_reports(primary_frames, primary_meta)
    primary_fivefold = _fivefold(primary_frames, primary_meta)

    independent_frames, independent_meta = _load_environment_frames(
        assets=(INDEPENDENT_AAA_ASSET,),
        work_dir=args.work_dir / "independent-2024-aaa",
        allowed_leagues={112, 117},
    )
    if set(independent_frames) != {"2024:112", "2024:117"}:
        raise RuntimeError(
            f"unexpected independent AAA environments: {sorted(independent_frames)}"
        )
    independent_fivefold = _fivefold(
        independent_frames,
        independent_meta,
        groups_to_score={"AAA"},
    )
    independent_confirmation = _aaa_confirmation(independent_fivefold)

    primary_aaa_eval = primary_fivefold["group_evaluations"]["AAA"]
    primary_aaa_robust = cv._robust_strengths(primary_aaa_eval)
    split_aaa_robust = set(
        split_pooling["best_strength_by_group"]["AAA"] and [
            int(row["prior_strength"])
            for row in split_pooling["group_evaluations"]
            if row["pool_group"] == "AAA"
            and int(row["prior_strength"]) > 0
            and float(row["mae_delta_vs_direct"]) <= 0
            and float(row["rmse_delta_vs_direct"]) <= 0
            and float(row["occurrence_weighted_mae_delta_vs_direct"]) <= 0
        ]
    )
    aaa_lambda25_primary_supported = AAA_CONFIRMATION_STRENGTH in primary_aaa_robust
    aaa_lambda25_split_supported = AAA_CONFIRMATION_STRENGTH in split_aaa_robust
    aaa_estimator_reconfirmed = (
        aaa_lambda25_primary_supported
        and aaa_lambda25_split_supported
        and bool(independent_confirmation["pass"])
    )

    screen_totals = {
        "primary": {
            name: sum(int(meta["screen"][name]) for meta in primary_meta.values())
            for name in next(iter(primary_meta.values()))["screen"]
        },
        "independent_2024_aaa": {
            name: sum(
                int(meta["screen"][name]) for meta in independent_meta.values()
            )
            for name in next(iter(independent_meta.values()))["screen"]
        },
    }

    payload = {
        "report_schema_version": 1,
        "status": "final_foul_screen_bin_value_confirmation",
        "screen_input": "fabio_core_bin",
        "legacy_helper_alias_note": (
            "Within this script only, final fabio_core_bin/core_profile_eligible are "
            "aliased onto legacy pre-foul-screen helper column names so existing tested "
            "RE24/stability functions operate on screened evidence without modification."
        ),
        "games_per_environment": GAMES_PER_ENVIRONMENT,
        "screen_totals": screen_totals,
        "primary_environment_meta": primary_meta,
        "primary_split_half_reports": split_reports,
        "primary_split_half_pooling": split_pooling,
        "primary_fivefold": primary_fivefold,
        "independent_2024_aaa_meta": independent_meta,
        "independent_2024_aaa_fivefold": independent_fivefold,
        "independent_2024_aaa_confirmation": independent_confirmation,
        "aaa_lambda25_split_supported": aaa_lambda25_split_supported,
        "aaa_lambda25_primary_fivefold_supported": aaa_lambda25_primary_supported,
        "aaa_estimator_reconfirmed_after_foul_screen": aaa_estimator_reconfirmed,
        "interpretation": (
            "AAA lambda=25 is considered reconfirmed only if it remains inside the robust "
            "region of the screened split-half and screened primary five-fold audits and "
            "the pre-specified independent 2024 AAA lambda=25 comparison improves or ties "
            "all four predictive metrics. Rookie/complex results remain diagnostic and do "
            "not force positive shrinkage."
        ),
    }
    (args.report_dir / "screened_bin_value_confirmation.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# Screened Performance-bin value confirmation",
        "",
        "**Final foul-air-screen evidence only; no player scores are produced.**",
        "",
        f"- Primary environments: {len(primary_meta)} × {GAMES_PER_ENVIRONMENT} games",
        f"- Independent 2024 AAA: {len(independent_meta)} × {GAMES_PER_ENVIRONMENT} games",
        f"- Primary pre-screen core PAs: {screen_totals['primary']['pre_screen_core_count']:,}",
        f"- Primary screened core PAs: {screen_totals['primary']['screened_core_count']:,}",
        f"- Primary excluded from core: {screen_totals['primary']['excluded_from_core_count']:,}",
        f"- Primary explicit foul-air events: {screen_totals['primary']['explicit_foul_air_count']:,}",
        f"- Primary unknown foul status among pre-core: {screen_totals['primary']['unknown_foul_status_pre_core_count']:,}",
        "",
        "## AAA post-screen confirmation",
        "",
        f"- Split-half robust positive strengths: {sorted(split_aaa_robust)}",
        f"- Primary five-fold robust positive strengths: {primary_aaa_robust}",
        f"- Lambda 25 supported by split-half: **{aaa_lambda25_split_supported}**",
        f"- Lambda 25 supported by primary five-fold: **{aaa_lambda25_primary_supported}**",
        f"- Independent 2024 lambda 25 pass: **{independent_confirmation['pass']}**",
        f"- AAA estimator reconfirmed after foul screen: **{aaa_estimator_reconfirmed}**",
        "",
        "### Independent 2024 AAA lambda=25 deltas",
        "",
    ]
    for metric, result in independent_confirmation["comparison"].items():
        lines.append(
            f"- {metric}: direct={result['direct']:.6f}, lambda25={result['lambda_25']:.6f}, delta={result['delta']:+.6f}, improved_or_tied={result['improved_or_tied']}"
        )
    lines.extend(
        [
            "",
            "## Rookie/complex diagnostic",
            "",
            f"- Split-half best/robust evidence: `{split_pooling['best_strength_by_group'].get('ROOKIE_COMPLEX')}`",
            f"- Five-fold decision: `{primary_fivefold['decisions'].get('ROOKIE_COMPLEX')}`",
            "",
            "The production architecture keeps Rookie/complex direct unless independent evidence resolves prior disagreement. This audit is allowed to confirm that conservative choice even if one screened diagnostic favors small positive shrinkage.",
            "",
        ]
    )
    summary = "\n".join(lines)
    (args.report_dir / "screened_bin_value_confirmation.md").write_text(
        summary, encoding="utf-8"
    )
    print(summary)
    return 0 if aaa_estimator_reconfirmed else 1


if __name__ == "__main__":
    raise SystemExit(main())
