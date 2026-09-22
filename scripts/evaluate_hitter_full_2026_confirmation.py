#!/usr/bin/env python3
"""Run the once-only protected 2026 full-hitter confirmation."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file, write_canonical_parquet


ACTUAL_COLUMNS = (
    "actual_mlb_pa",
    "actual_batting_replacement_war",
    "actual_position_war",
    "actual_steal_war",
    "actual_advancement_war",
    "actual_catcher_defense_war",
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--completed-2026-targets", type=Path, required=True)
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--season-complete",
        action="store_true",
        help="Required declaration that the 2026 regular season is complete.",
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("docs/hitter-full-2026-confirmation-contract.json"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/hitter-full-2026-confirmation"),
    )
    return parser.parse_args()


def _metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    residual = predicted - actual
    return {
        "rmse": float(np.sqrt(np.mean(residual**2))),
        "mae": float(np.mean(np.abs(residual))),
        "bias": float(np.mean(residual)),
    }


def _probability_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    probability = np.clip(predicted, 1e-12, 1 - 1e-12)
    return {
        "brier": float(np.mean((probability - actual) ** 2)),
        "log_loss": float(
            -np.mean(actual * np.log(probability) + (1 - actual) * np.log(1 - probability))
        ),
    }


def _paired_rmse_bootstrap(
    actual: np.ndarray,
    baseline: np.ndarray,
    candidate: np.ndarray,
    *,
    repetitions: int,
    seed: int,
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    count = len(actual)
    deltas: list[np.ndarray] = []
    remaining = repetitions
    while remaining:
        batch = min(250, remaining)
        selected = rng.integers(0, count, size=(batch, count))
        baseline_rmse = np.sqrt(np.mean((baseline[selected] - actual[selected]) ** 2, axis=1))
        candidate_rmse = np.sqrt(np.mean((candidate[selected] - actual[selected]) ** 2, axis=1))
        deltas.append(candidate_rmse - baseline_rmse)
        remaining -= batch
    values = np.concatenate(deltas)
    return {
        "lower_95": float(np.quantile(values, 0.025)),
        "median": float(np.quantile(values, 0.5)),
        "upper_95": float(np.quantile(values, 0.975)),
        "probability_routed_better": float(np.mean(values < 0)),
    }


def _rmse_delta(frame: pl.DataFrame, actual: str, candidate: str, baseline: str) -> float:
    values = frame.select(actual, candidate, baseline).to_numpy()
    return _metrics(values[:, 0], values[:, 1])["rmse"] - _metrics(
        values[:, 0], values[:, 2]
    )["rmse"]


def main() -> int:
    args = _args()
    # These guards run before the protected target path is opened.
    if not args.season_complete:
        raise RuntimeError("refusing to open 2026 targets without --season-complete")
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if args.as_of_date < date.fromisoformat(contract["earliest_evaluation_date"]):
        raise RuntimeError("confirmation date precedes the locked evaluation date")
    forecast_path = Path(contract["forecast_path"])
    if sha256_file(forecast_path) != contract["forecast_sha256"]:
        raise RuntimeError("frozen forecast hash does not match the contract")
    manifest_path = Path(contract["manifest_path"])
    if sha256_file(manifest_path) != contract["manifest_sha256"]:
        raise RuntimeError("frozen manifest hash does not match the contract")

    forecast = pl.read_parquet(forecast_path)
    targets = pl.read_parquet(args.completed_2026_targets)
    required = {"player_id", *ACTUAL_COLUMNS}
    if missing := sorted(required - set(targets.columns)):
        raise ValueError(f"completed targets missing fields: {missing}")
    if targets["player_id"].n_unique() != targets.height:
        raise ValueError("completed targets contain duplicate player IDs")
    if set(targets["player_id"]) != set(forecast["player_id"]):
        raise ValueError("completed targets must contain exactly the frozen player universe")
    if targets.select(pl.any_horizontal(pl.col(ACTUAL_COLUMNS).is_null())).to_series().any():
        raise ValueError("completed targets contain null outcomes")
    target_values = targets.select(ACTUAL_COLUMNS).to_numpy()
    if not np.isfinite(target_values).all():
        raise ValueError("completed targets contain non-finite outcomes")
    if targets.filter(pl.col("actual_mlb_pa") < 0).height:
        raise ValueError("completed targets contain negative MLB plate appearances")

    rows = forecast.join(targets.select("player_id", *ACTUAL_COLUMNS), on="player_id", validate="1:1")
    rows = rows.with_columns(
        (pl.col("actual_mlb_pa") > 0).cast(pl.Int8).alias("actual_mlb_active"),
        (pl.col("actual_steal_war") + pl.col("actual_advancement_war")).alias(
            "actual_baserunning_war"
        ),
        (
            pl.col("actual_batting_replacement_war")
            + pl.col("actual_position_war")
            + pl.col("actual_steal_war")
            + pl.col("actual_advancement_war")
            + pl.col("actual_catcher_defense_war")
        ).alias("actual_selected_partial_war"),
        pl.when(pl.col("prediction_expected_mlb_pa") == 0)
        .then(pl.lit("0"))
        .when(pl.col("prediction_expected_mlb_pa") < 100)
        .then(pl.lit("1-99"))
        .when(pl.col("prediction_expected_mlb_pa") < 300)
        .then(pl.lit("100-299"))
        .otherwise(pl.lit("300+"))
        .alias("forecast_pa_band"),
        pl.col("lag0__contact_feature_available")
        .fill_null(0)
        .cast(pl.String)
        .alias("contact_available_group"),
    )

    actual_active = rows["actual_mlb_active"].to_numpy()
    opportunity_models = {
        "selected": ("prediction_mlb_active_probability", "prediction_expected_mlb_pa"),
        "incumbent": (
            "benchmark_incumbent_active_probability",
            "benchmark_incumbent_expected_mlb_pa",
        ),
        "parametric": (
            "benchmark_parametric_active_probability",
            "benchmark_parametric_expected_mlb_pa",
        ),
    }
    opportunity = {}
    for name, (probability_column, pa_column) in opportunity_models.items():
        opportunity[name] = {
            **_probability_metrics(actual_active, rows[probability_column].to_numpy()),
            **{
                f"pa_{key}": value
                for key, value in _metrics(
                    rows["actual_mlb_pa"].to_numpy(), rows[pa_column].to_numpy()
                ).items()
            },
        }

    batting_models = {
        "selected": "prediction_batting_replacement_war",
        "routed": "prediction_routed_batting_replacement_war",
        "previous_season": "benchmark_previous_batting_replacement_war",
        "training_mean": "benchmark_training_mean_batting_replacement_war",
        "zero": "benchmark_zero_batting_replacement_war",
    }
    batting = {
        name: _metrics(
            rows["actual_batting_replacement_war"].to_numpy(), rows[column].to_numpy()
        )
        for name, column in batting_models.items()
    }
    partial = {
        name: _metrics(
            rows["actual_selected_partial_war"].to_numpy(), rows[column].to_numpy()
        )
        for name, column in {
            "selected": "prediction_selected_partial_war",
            "routed": "prediction_routed_partial_war",
        }.items()
    }
    component_pairs = {
        "position": ("actual_position_war", "prediction_position_war"),
        "steal": ("actual_steal_war", "prediction_steal_war"),
        "advancement": ("actual_advancement_war", "prediction_advancement_war"),
        "baserunning": ("actual_baserunning_war", "prediction_baserunning_war"),
        "catcher_defense": (
            "actual_catcher_defense_war",
            "prediction_catcher_defense_war",
        ),
    }
    components = {}
    for name, (actual_column, prediction_column) in component_pairs.items():
        actual = rows[actual_column].to_numpy()
        components[name] = {
            "model": _metrics(actual, rows[prediction_column].to_numpy()),
            "zero": _metrics(actual, np.zeros(len(actual))),
        }

    repetitions = int(contract["bootstrap_repetitions"])
    seed = int(contract["bootstrap_seed"])
    bootstrap = {
        "batting": _paired_rmse_bootstrap(
            rows["actual_batting_replacement_war"].to_numpy(),
            rows["prediction_batting_replacement_war"].to_numpy(),
            rows["prediction_routed_batting_replacement_war"].to_numpy(),
            repetitions=repetitions,
            seed=seed,
        ),
        "partial_war": _paired_rmse_bootstrap(
            rows["actual_selected_partial_war"].to_numpy(),
            rows["prediction_selected_partial_war"].to_numpy(),
            rows["prediction_routed_partial_war"].to_numpy(),
            repetitions=repetitions,
            seed=seed + 1,
        ),
    }
    subgroup_results = []
    for group_type, column in (
        ("player_stage", "player_stage"),
        ("batting_evidence", "batting_evidence_tier"),
        ("contact_available", "contact_available_group"),
        ("forecast_pa", "forecast_pa_band"),
    ):
        for value in sorted(str(value) for value in rows[column].unique()):
            selected = rows.filter(pl.col(column) == value)
            subgroup_results.append(
                {
                    "group_type": group_type,
                    "group": value,
                    "players": selected.height,
                    "routed_minus_selected_partial_rmse": _rmse_delta(
                        selected,
                        "actual_selected_partial_war",
                        "prediction_routed_partial_war",
                        "prediction_selected_partial_war",
                    ),
                }
            )
    supported_harm = [
        row
        for row in subgroup_results
        if row["players"] >= int(contract["minimum_supported_subgroup_players"])
        and row["routed_minus_selected_partial_rmse"]
        > float(contract["material_subgroup_rmse_harm"])
    ]
    gates = {
        "partial_rmse_improved": partial["routed"]["rmse"] < partial["selected"]["rmse"],
        "partial_rmse_interval_below_zero": bootstrap["partial_war"]["upper_95"] < 0,
        "batting_rmse_not_worse": batting["routed"]["rmse"] <= batting["selected"]["rmse"],
        "no_supported_material_subgroup_harm": not supported_harm,
    }
    interval_coverage = {}
    actual_partial = rows["actual_selected_partial_war"].to_numpy()
    for level in (50, 80, 90):
        interval_coverage[str(level)] = float(
            np.mean(
                (actual_partial >= rows[f"selected_lower_{level}"].to_numpy())
                & (actual_partial <= rows[f"selected_upper_{level}"].to_numpy())
            )
        )

    args.output_root.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        rows.sort("player_id"),
        args.output_root / "scored-players.parquet",
        table_name="hitter_full_2026_confirmation_scored_players",
    ).as_record()
    report = {
        "schema_version": "1.0",
        "status": "2026_confirmation_complete",
        "as_of_date": args.as_of_date.isoformat(),
        "forecast_sha256": contract["forecast_sha256"],
        "target_sha256": sha256_file(args.completed_2026_targets),
        "players": rows.height,
        "opportunity": opportunity,
        "batting": batting,
        "partial_war": partial,
        "components": components,
        "paired_player_bootstrap": bootstrap,
        "interval_coverage": interval_coverage,
        "subgroups": subgroup_results,
        "supported_material_harm": supported_harm,
        "routed_promotion_gates": gates,
        "routed_promoted": all(gates.values()),
        "artifact": artifact,
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
