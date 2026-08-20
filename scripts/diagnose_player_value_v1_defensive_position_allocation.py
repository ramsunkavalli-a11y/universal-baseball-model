#!/usr/bin/env python3
"""Select Player Value v1 defensive position-share allocation on pre-2025 folds.

Keeps total projected defensive outs fixed at prior-year raw persistence and compares:
S0 prior defensive-out-share persistence, R1 a deterministic defensive normalization of the
already-frozen Position/Role forecast, and H1 a fixed 50/50 share hybrid.

This script does not access 2025, refit upstream models, convert Defense skill to runs, calculate
positional adjustment, or calculate WAR/value.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from math import sqrt
from pathlib import Path

import numpy as np
import polars as pl

CONTRACT_SHA256 = "867fed7b3adfd81e5c34ec75aa99f52f4178f1f23dfaf9cc23983ebf06d21bf1"
POSITION_ROLE_RUN_ID = 32152125644
POSITION_ROLE_ARTIFACT = "position-role-transition-challenger-development"
POSITION_ROLE_DIGEST = "sha256:4e98081cb1800d45f3668595e4e61a169dbce68a8b565aa1e8f60d7dcd1417e5"
FIELDING_RUN_ID = 32148467330
FIELDING_ARTIFACT = "position-role-historical-source-2021-2024"
FIELDING_DIGEST = "sha256:908022d38b3652db1c2b68a7ba2768954c32f8973f0ace85c9557d30522adaf3"
PRIMARY_SHARE_THRESHOLD = 0.65
DEFENSIVE_POSITIONS = ("C", "1B", "2B", "3B", "SS", "LF", "CF", "RF")
BATTING_ROLE_POSITIONS = DEFENSIVE_POSITIONS + ("DH",)
FORMS = (
    "S0_prior_defensive_share_persistence",
    "R1_frozen_role_defensive_normalization",
    "H1_fixed_50_50_share_hybrid",
)
FOLDS = ((2022, 2023), (2023, 2024))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--position-role-root", type=Path, required=True)
    parser.add_argument("--fielding-root", type=Path, required=True)
    parser.add_argument(
        "--contract-path",
        type=Path,
        default=Path("docs/player-value-v1-defensive-position-allocation-contract.md"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/player-value-v1-defensive-position-allocation"),
    )
    return parser.parse_args()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_contract(path: Path) -> str:
    observed = _sha256(path)
    if observed != CONTRACT_SHA256:
        raise RuntimeError(
            f"allocation contract hash mismatch: expected {CONTRACT_SHA256}, observed {observed}"
        )
    return observed


def _unique_file(root: Path, filename: str) -> Path:
    matches = sorted(path for path in root.rglob(filename) if path.is_file())
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {filename!r} under {root}; found {len(matches)}")
    return matches[0]


def _load_role_predictions(root: Path) -> pl.DataFrame:
    path = _unique_file(root, "predictions.parquet")
    frame = pl.read_parquet(path)
    required = {"current_season", "next_season", "player_id", "current_primary_share"}
    for position in BATTING_ROLE_POSITIONS:
        required.add(f"current_{position}")
        required.add(f"candidate_{position}")
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"Position/Role predictions missing required columns: {missing}")

    frame = frame.select(
        pl.col("current_season").cast(pl.Int64),
        pl.col("next_season").cast(pl.Int64),
        pl.col("player_id").cast(pl.Int64),
        pl.col("current_primary_share").cast(pl.Float64),
        *[
            pl.col(column).cast(pl.Float64)
            for position in BATTING_ROLE_POSITIONS
            for column in (f"current_{position}", f"candidate_{position}")
        ],
    )
    duplicate = frame.group_by(["current_season", "next_season", "player_id"]).len().filter(
        pl.col("len") != 1
    )
    if duplicate.height:
        raise RuntimeError("Position/Role predictions violate fold/player grain")
    inventory = sorted(
        set(
            (int(row[0]), int(row[1]))
            for row in frame.select("current_season", "next_season").unique().iter_rows()
        )
    )
    if inventory != list(FOLDS):
        raise RuntimeError(f"unexpected Position/Role fold inventory: {inventory}")
    return frame


def _load_fielding_usage(root: Path) -> pl.DataFrame:
    path = _unique_file(root, "historical_fielding_usage.parquet")
    frame = pl.read_parquet(path)
    required = {"season", "level_group", "player_id", "position_abbreviation", "fielding_outs"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"historical fielding usage missing required columns: {missing}")
    frame = frame.select(
        pl.col("season").cast(pl.Int64),
        pl.col("level_group").cast(pl.Utf8),
        pl.col("player_id").cast(pl.Int64),
        pl.col("position_abbreviation").cast(pl.Utf8),
        pl.col("fielding_outs").cast(pl.Int64),
    )
    if frame.filter(pl.col("fielding_outs") < 0).height:
        raise RuntimeError("historical fielding usage contains negative fielding_outs")
    return frame


def _position_outs(
    fielding: pl.DataFrame,
    *,
    season: int,
    position: str,
    alias: str,
) -> pl.DataFrame:
    return (
        fielding.filter(
            (pl.col("season") == season)
            & (pl.col("level_group") == "MLB")
            & (pl.col("position_abbreviation") == position)
        )
        .group_by("player_id")
        .agg(pl.col("fielding_outs").sum().cast(pl.Int64).alias(alias))
    )


def _build_fold(
    role_predictions: pl.DataFrame,
    fielding: pl.DataFrame,
    *,
    source_year: int,
    target_year: int,
) -> tuple[pl.DataFrame, dict[str, object]]:
    frame = role_predictions.filter(
        (pl.col("current_season") == source_year) & (pl.col("next_season") == target_year)
    )
    if frame.is_empty():
        raise RuntimeError(f"empty Position/Role fold {source_year}->{target_year}")

    for position in DEFENSIVE_POSITIONS:
        frame = frame.join(
            _position_outs(
                fielding,
                season=source_year,
                position=position,
                alias=f"prior_outs_{position}",
            ),
            on="player_id",
            how="left",
        ).join(
            _position_outs(
                fielding,
                season=target_year,
                position=position,
                alias=f"target_outs_{position}",
            ),
            on="player_id",
            how="left",
        )

    frame = frame.with_columns(
        *[
            pl.col(f"{prefix}_outs_{position}").fill_null(0).cast(pl.Int64)
            for prefix in ("prior", "target")
            for position in DEFENSIVE_POSITIONS
        ]
    ).with_columns(
        pl.sum_horizontal([pl.col(f"prior_outs_{p}") for p in DEFENSIVE_POSITIONS])
        .cast(pl.Int64)
        .alias("prior_total_defensive_outs"),
        pl.sum_horizontal([pl.col(f"target_outs_{p}") for p in DEFENSIVE_POSITIONS])
        .cast(pl.Int64)
        .alias("target_total_defensive_outs"),
    )

    selective_exprs = []
    for position in BATTING_ROLE_POSITIONS:
        selective_exprs.append(
            pl.when(pl.col("current_primary_share") >= PRIMARY_SHARE_THRESHOLD)
            .then(pl.col(f"candidate_{position}"))
            .otherwise(pl.col(f"current_{position}"))
            .cast(pl.Float64)
            .alias(f"frozen_role_{position}")
        )
    frame = frame.with_columns(*selective_exprs).with_columns(
        pl.sum_horizontal([pl.col(f"frozen_role_{p}") for p in DEFENSIVE_POSITIONS])
        .cast(pl.Float64)
        .alias("defensive_role_mass")
    )

    share_exprs = []
    for position in DEFENSIVE_POSITIONS:
        share_exprs.extend(
            [
                pl.when(pl.col("prior_total_defensive_outs") > 0)
                .then(pl.col(f"prior_outs_{position}") / pl.col("prior_total_defensive_outs"))
                .otherwise(pl.lit(0.0))
                .cast(pl.Float64)
                .alias(f"S0_share_{position}"),
                pl.when(pl.col("target_total_defensive_outs") > 0)
                .then(pl.col(f"target_outs_{position}") / pl.col("target_total_defensive_outs"))
                .otherwise(pl.lit(0.0))
                .cast(pl.Float64)
                .alias(f"observed_share_{position}"),
            ]
        )
    frame = frame.with_columns(*share_exprs)

    r1_exprs = []
    for position in DEFENSIVE_POSITIONS:
        r1_exprs.append(
            pl.when(pl.col("defensive_role_mass") > 1e-12)
            .then(pl.col(f"frozen_role_{position}") / pl.col("defensive_role_mass"))
            .otherwise(pl.col(f"S0_share_{position}"))
            .cast(pl.Float64)
            .alias(f"R1_share_{position}")
        )
    frame = frame.with_columns(*r1_exprs)

    frame = frame.with_columns(
        *[
            (0.5 * pl.col(f"S0_share_{position}") + 0.5 * pl.col(f"R1_share_{position}"))
            .cast(pl.Float64)
            .alias(f"H1_share_{position}")
            for position in DEFENSIVE_POSITIONS
        ],
        (
            (pl.col("prior_total_defensive_outs") > 0)
            & (pl.col("target_total_defensive_outs") > 0)
        ).alias("allocation_scoring_eligible"),
        (
            (pl.col("prior_total_defensive_outs") > 0)
            & (pl.col("defensive_role_mass") <= 1e-12)
        ).alias("R1_fallback_to_S0"),
    )

    for prefix in ("S0", "R1", "H1"):
        frame = frame.with_columns(
            *[
                (
                    pl.col("prior_total_defensive_outs").cast(pl.Float64)
                    * pl.col(f"{prefix}_share_{position}")
                ).alias(f"{prefix}_predicted_outs_{position}")
                for position in DEFENSIVE_POSITIONS
            ]
        )

    eligible = frame.filter(pl.col("allocation_scoring_eligible"))
    if eligible.is_empty():
        raise RuntimeError(f"no continuing defenders in fold {source_year}->{target_year}")

    for prefix in ("S0", "R1", "H1"):
        sums = eligible.select(
            pl.sum_horizontal([pl.col(f"{prefix}_share_{p}") for p in DEFENSIVE_POSITIONS]).alias(
                "share_sum"
            )
        )
        if sums.filter((pl.col("share_sum") - 1.0).abs() > 1e-9).height:
            raise RuntimeError(f"{prefix} shares fail reconciliation in {source_year}->{target_year}")
        outs_sums = eligible.select(
            pl.sum_horizontal(
                [pl.col(f"{prefix}_predicted_outs_{p}") for p in DEFENSIVE_POSITIONS]
            ).alias("predicted_total"),
            pl.col("prior_total_defensive_outs").cast(pl.Float64).alias("expected_total"),
        )
        if outs_sums.filter((pl.col("predicted_total") - pl.col("expected_total")).abs() > 1e-9).height:
            raise RuntimeError(
                f"{prefix} projected position outs fail fixed-total reconciliation in "
                f"{source_year}->{target_year}"
            )

    observed_sums = eligible.select(
        pl.sum_horizontal([pl.col(f"observed_share_{p}") for p in DEFENSIVE_POSITIONS]).alias(
            "share_sum"
        )
    )
    if observed_sums.filter((pl.col("share_sum") - 1.0).abs() > 1e-9).height:
        raise RuntimeError(f"observed shares fail reconciliation in {source_year}->{target_year}")

    full_n = int(frame.height)
    prior_positive = frame.get_column("prior_total_defensive_outs").to_numpy() > 0
    target_positive = frame.get_column("target_total_defensive_outs").to_numpy() > 0
    coverage = {
        "full_position_role_fold_players": full_n,
        "continuing_defenders": int(np.sum(prior_positive & target_positive)),
        "source_only_positive_defenders": int(np.sum(prior_positive & ~target_positive)),
        "target_only_positive_defenders": int(np.sum(~prior_positive & target_positive)),
        "zero_zero_defenders": int(np.sum(~prior_positive & ~target_positive)),
        "R1_fallback_to_S0_full_fold": int(frame.get_column("R1_fallback_to_S0").sum()),
        "R1_fallback_to_S0_continuing": int(eligible.get_column("R1_fallback_to_S0").sum()),
    }
    return frame, coverage


def _metrics(frame: pl.DataFrame, prefix: str) -> dict[str, object]:
    eligible = frame.filter(pl.col("allocation_scoring_eligible"))
    observed_share = np.column_stack(
        [eligible.get_column(f"observed_share_{p}").to_numpy() for p in DEFENSIVE_POSITIONS]
    ).astype(np.float64)
    predicted_share = np.column_stack(
        [eligible.get_column(f"{prefix}_share_{p}").to_numpy() for p in DEFENSIVE_POSITIONS]
    ).astype(np.float64)
    observed_outs = np.column_stack(
        [eligible.get_column(f"target_outs_{p}").to_numpy() for p in DEFENSIVE_POSITIONS]
    ).astype(np.float64)
    predicted_outs = np.column_stack(
        [eligible.get_column(f"{prefix}_predicted_outs_{p}").to_numpy() for p in DEFENSIVE_POSITIONS]
    ).astype(np.float64)

    share_error = predicted_share - observed_share
    outs_error = predicted_outs - observed_outs
    tv_by_player = 0.5 * np.abs(share_error).sum(axis=1)
    sse_by_player = np.square(share_error).sum(axis=1)
    l1_outs_by_player = np.abs(outs_error).sum(axis=1)
    predicted_primary = np.argmax(predicted_share, axis=1)
    observed_primary = np.argmax(observed_share, axis=1)

    per_position_mae = {
        position: float(np.abs(outs_error[:, index]).mean())
        for index, position in enumerate(DEFENSIVE_POSITIONS)
    }
    return {
        "n": int(eligible.height),
        "mean_share_tv": float(tv_by_player.mean()),
        "mean_share_sse": float(sse_by_player.mean()),
        "primary_position_match_rate": float((predicted_primary == observed_primary).mean()),
        "position_out_cell_mae": float(np.abs(outs_error).mean()),
        "position_out_cell_rmse": float(sqrt(float(np.square(outs_error).mean()))),
        "mean_player_l1_position_outs_error": float(l1_outs_by_player.mean()),
        "predicted_mean_total_defensive_outs": float(predicted_outs.sum(axis=1).mean()),
        "observed_mean_total_defensive_outs": float(observed_outs.sum(axis=1).mean()),
        "per_position_mae": per_position_mae,
    }


def _equal_fold_means(
    fold_metrics: dict[str, dict[str, dict[str, object]]]
) -> dict[str, dict[str, float]]:
    metric_names = (
        "mean_share_tv",
        "mean_share_sse",
        "position_out_cell_mae",
        "position_out_cell_rmse",
        "primary_position_match_rate",
    )
    output: dict[str, dict[str, float]] = {}
    for form in FORMS:
        output[form] = {
            metric: float(
                sum(float(fold_metrics[fold][form][metric]) for fold in fold_metrics)
                / len(fold_metrics)
            )
            for metric in metric_names
        }
    return output


def _recommendation(
    fold_metrics: dict[str, dict[str, dict[str, object]]],
    equal_fold: dict[str, dict[str, float]],
) -> dict[str, object]:
    baseline = "S0_prior_defensive_share_persistence"
    challengers = (
        "R1_frozen_role_defensive_normalization",
        "H1_fixed_50_50_share_hybrid",
    )
    evaluations: dict[str, dict[str, object]] = {}
    passing: list[str] = []

    for challenger in challengers:
        fold_mae_within_2pct = True
        fold_share_tv_no_worse = True
        primary_match_guardrail = True
        per_fold: dict[str, dict[str, object]] = {}
        for fold_name, forms in fold_metrics.items():
            b0 = forms[baseline]
            c = forms[challenger]
            mae_ok = float(c["position_out_cell_mae"]) <= 1.02 * float(
                b0["position_out_cell_mae"]
            )
            tv_ok = float(c["mean_share_tv"]) <= float(b0["mean_share_tv"]) + 1e-12
            primary_ok = float(c["primary_position_match_rate"]) >= (
                float(b0["primary_position_match_rate"]) - 0.01
            )
            fold_mae_within_2pct = fold_mae_within_2pct and mae_ok
            fold_share_tv_no_worse = fold_share_tv_no_worse and tv_ok
            primary_match_guardrail = primary_match_guardrail and primary_ok
            per_fold[fold_name] = {
                "position_out_cell_mae_within_2pct_of_S0": mae_ok,
                "mean_share_tv_no_worse_than_S0": tv_ok,
                "primary_match_no_more_than_0_01_below_S0": primary_ok,
            }

        equal_mae_lower = (
            equal_fold[challenger]["position_out_cell_mae"]
            < equal_fold[baseline]["position_out_cell_mae"]
        )
        equal_rmse_lower = (
            equal_fold[challenger]["position_out_cell_rmse"]
            < equal_fold[baseline]["position_out_cell_rmse"]
        )
        equal_tv_lower = (
            equal_fold[challenger]["mean_share_tv"] < equal_fold[baseline]["mean_share_tv"]
        )
        passed = bool(
            fold_mae_within_2pct
            and equal_mae_lower
            and equal_rmse_lower
            and fold_share_tv_no_worse
            and equal_tv_lower
            and primary_match_guardrail
        )
        evaluations[challenger] = {
            "per_fold": per_fold,
            "fold_specific_position_out_mae_within_2pct": fold_mae_within_2pct,
            "equal_fold_position_out_mae_strictly_lower": equal_mae_lower,
            "equal_fold_position_out_rmse_strictly_lower": equal_rmse_lower,
            "fold_specific_share_tv_no_worse": fold_share_tv_no_worse,
            "equal_fold_share_tv_strictly_lower": equal_tv_lower,
            "primary_match_guardrail": primary_match_guardrail,
            "passes": passed,
        }
        if passed:
            passing.append(challenger)

    if not passing:
        selected = baseline
        reason = "no challenger satisfied all predeclared position-allocation gates"
    elif len(passing) == 1:
        selected = passing[0]
        reason = "only challenger satisfying all predeclared position-allocation gates"
    else:
        r1, h1 = challengers
        mae_delta = abs(
            equal_fold[r1]["position_out_cell_mae"] - equal_fold[h1]["position_out_cell_mae"]
        )
        if mae_delta > 1e-9:
            selected = min(passing, key=lambda form: equal_fold[form]["position_out_cell_mae"])
            reason = "both challengers passed; lower equal-fold position-out cell MAE wins"
        else:
            tv_delta = abs(equal_fold[r1]["mean_share_tv"] - equal_fold[h1]["mean_share_tv"])
            if tv_delta > 1e-9:
                selected = min(passing, key=lambda form: equal_fold[form]["mean_share_tv"])
                reason = "both challengers passed and MAE tied; lower equal-fold share TV wins"
            else:
                selected = r1
                reason = "both challengers tied within 1e-9; simpler direct R1 mapping wins"

    return {
        "selected_position_share_form": selected,
        "reason": reason,
        "challenger_evaluations": evaluations,
        "position_allocation_selected": True,
        "total_outs_form": "B0_raw_persistence",
        "total_outs_form_changed": False,
    }


def _write_markdown(report: dict[str, object], path: Path) -> None:
    selected = report["recommendation"]["selected_position_share_form"]
    lines = [
        "# Player Value v1 defensive position allocation diagnostic",
        "",
        f"Selected position-share form: **{selected}**",
        "",
        "Total projected defensive outs remain fixed at **B0_raw_persistence**.",
        "",
        "## Fold metrics",
        "",
    ]
    for fold_name, forms in report["fold_metrics"].items():
        lines.append(f"### {fold_name}")
        lines.append("")
        for form in FORMS:
            metric = forms[form]
            lines.append(
                f"- `{form}`: share TV {metric['mean_share_tv']:.6f}; "
                f"position-out MAE {metric['position_out_cell_mae']:.3f}; "
                f"RMSE {metric['position_out_cell_rmse']:.3f}; "
                f"primary match {metric['primary_position_match_rate']:.4f}"
            )
        lines.append("")
    lines.extend(
        [
            "## Boundaries",
            "",
            "- 2025 fielding outcomes accessed: false",
            "- total-outs form changed: false",
            "- upstream refit: false",
            "- run conversion performed: false",
            "- positional adjustment calculated: false",
            "- WAR/value calculated: false",
            "",
        ]
    )
    path.write_text("\n".join(lines))


def main() -> None:
    args = _parse_args()
    contract_hash = _verify_contract(args.contract_path)
    role_predictions = _load_role_predictions(args.position_role_root)
    fielding = _load_fielding_usage(args.fielding_root)

    fold_metrics: dict[str, dict[str, dict[str, object]]] = {}
    fold_coverage: dict[str, dict[str, object]] = {}
    scored_frames: list[pl.DataFrame] = []

    prefix_by_form = {
        "S0_prior_defensive_share_persistence": "S0",
        "R1_frozen_role_defensive_normalization": "R1",
        "H1_fixed_50_50_share_hybrid": "H1",
    }
    for source_year, target_year in FOLDS:
        fold_name = f"allocation_{source_year}_to_{target_year}"
        frame, coverage = _build_fold(
            role_predictions,
            fielding,
            source_year=source_year,
            target_year=target_year,
        )
        scored_frames.append(frame.with_columns(pl.lit(fold_name).alias("fold")))
        fold_coverage[fold_name] = coverage
        fold_metrics[fold_name] = {
            form: _metrics(frame, prefix_by_form[form]) for form in FORMS
        }

    equal_fold = _equal_fold_means(fold_metrics)
    recommendation = _recommendation(fold_metrics, equal_fold)
    report = {
        "report_schema_version": "0.1",
        "gate": "player_value_v1_defensive_position_allocation_selection",
        "status": "binding_v1_position_allocation_selection_complete",
        "contract": "docs/player-value-v1-defensive-position-allocation-contract.md",
        "contract_sha256": contract_hash,
        "sources": {
            "position_role": {
                "run_id": POSITION_ROLE_RUN_ID,
                "artifact_name": POSITION_ROLE_ARTIFACT,
                "artifact_digest": POSITION_ROLE_DIGEST,
                "frozen_form": "primary_share_thresholded_transition_mean_v1",
                "primary_share_threshold": PRIMARY_SHARE_THRESHOLD,
            },
            "fielding": {
                "run_id": FIELDING_RUN_ID,
                "artifact_name": FIELDING_ARTIFACT,
                "artifact_digest": FIELDING_DIGEST,
                "observed_unit": "official_fielding_outs",
            },
            "total_outs": {
                "form": "B0_raw_persistence",
                "source": "docs/player-value-v1-defensive-exposure-diagnostic-result.json",
            },
        },
        "fold_coverage": fold_coverage,
        "fold_metrics": fold_metrics,
        "equal_fold_means": equal_fold,
        "recommendation": recommendation,
        "boundary": {
            "2025_fielding_outcomes_accessed": False,
            "untouched_confirmation_claimed": False,
            "total_outs_form_changed": False,
            "playing_time_refit": False,
            "position_role_refit": False,
            "defense_refit": False,
            "run_conversion_performed": False,
            "positional_adjustment_calculated": False,
            "war_value_calculated": False,
        },
    }

    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    pl.concat(scored_frames, how="vertical_relaxed").sort(
        ["current_season", "next_season", "player_id"]
    ).write_parquet(args.output_root / "allocation_scored.parquet")
    _write_markdown(report, args.output_root / "report.md")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
