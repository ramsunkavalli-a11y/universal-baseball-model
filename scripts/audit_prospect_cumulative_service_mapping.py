#!/usr/bin/env python3
"""Audit workload-mapped service against later FanGraphs cumulative balances."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

try:
    from scripts.audit_prospect_service_day_mapping import _model_frame, _predict
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from audit_prospect_service_day_mapping import _model_frame, _predict


START_DEBUT_YEAR = 2009
END_DEBUT_YEAR = 2019
LAST_SEASON = 2024
CONTROL_SERVICE_DAYS = 6 * 172


def _metrics(observed: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    error = predicted - observed
    return {
        "bias_days": float(error.mean()),
        "mae_days": float(np.abs(error).mean()),
        "rmse_days": float(np.sqrt(np.square(error).mean())),
    }


def _classification(observed: np.ndarray, predicted: np.ndarray) -> dict[str, float | int]:
    actual = observed >= CONTROL_SERVICE_DAYS
    estimate = predicted >= CONTROL_SERVICE_DAYS
    true_positive = int(np.sum(actual & estimate))
    false_positive = int(np.sum(~actual & estimate))
    false_negative = int(np.sum(actual & ~estimate))
    return {
        "players": len(actual),
        "actual_exhausted": int(actual.sum()),
        "predicted_exhausted": int(estimate.sum()),
        "accuracy": float(np.mean(actual == estimate)),
        "precision": true_positive / max(true_positive + false_positive, 1),
        "recall": true_positive / max(true_positive + false_negative, 1),
    }


def _annual_paths() -> pl.DataFrame:
    root = Path("reports/generated/career-mlb-outcome-inventory-2009-2025/tables")
    debut = (
        pl.read_parquet(root / "people-debut-dates.parquet")
        .filter(
            pl.col("mlb_debut_date")
            .dt.year()
            .is_between(START_DEBUT_YEAR, END_DEBUT_YEAR)
        )
        .select(
            "player_id", pl.col("mlb_debut_date").dt.year().alias("debut_year")
        )
    )
    batting = pl.read_parquet(root / "mlb_batting_2009_2025.parquet").select(
        "player_id", "season", "batting_pa"
    )
    pitching = pl.read_parquet(root / "mlb_pitching_2009_2025.parquet").select(
        "player_id", "season", "pitching_bf"
    )
    activity = batting.join(
        pitching, on=["player_id", "season"], how="full", coalesce=True
    ).with_columns(
        pl.col("batting_pa").fill_null(0),
        pl.col("pitching_bf").fill_null(0),
    )
    grid = pl.concat(
        [
            debut.with_columns(pl.lit(season).alias("season"))
            for season in range(START_DEBUT_YEAR, LAST_SEASON + 1)
        ]
    ).filter(pl.col("season") >= pl.col("debut_year"))
    return (
        grid.join(activity, on=["player_id", "season"], how="left")
        .with_columns(
            pl.col("batting_pa").fill_null(0),
            pl.col("pitching_bf").fill_null(0),
        )
        .with_columns(
            pl.when(pl.col("batting_pa") / 600 >= pl.col("pitching_bf") / 800)
            .then(pl.lit("hitter"))
            .otherwise(pl.lit("pitcher"))
            .alias("player_type"),
            (pl.col("debut_year") == pl.col("season")).alias("first_mlb_season"),
        )
        .with_columns(
            pl.when(pl.col("player_type") == "hitter")
            .then(pl.col("batting_pa"))
            .otherwise(pl.col("pitching_bf"))
            .cast(pl.Float64)
            .alias("raw_workload")
        )
        .with_columns(
            pl.when(pl.col("season") == 2020)
            .then(pl.col("raw_workload") * 2.7)
            .otherwise(pl.col("raw_workload"))
            .alias("workload")
        )
        .sort("player_id", "season")
    )


def apply_service_predictions(paths: pl.DataFrame, training: pl.DataFrame) -> pl.DataFrame:
    """Apply the monotone map without inventing injured-list or roster presence."""

    predicted = _predict(
        training,
        paths.select("player_type", "first_mlb_season", "workload"),
    )
    return paths.with_columns(
        pl.Series("mapped_service_days", predicted)
    ).with_columns(
        pl.when(pl.col("raw_workload") > 0)
        .then(pl.col("mapped_service_days"))
        .otherwise(0.0)
        .alias("mapped_service_days"),
        pl.when(pl.col("raw_workload") > 0)
        .then(172.0)
        .otherwise(0.0)
        .alias("active_season_shortcut_days"),
    )


def main() -> int:
    service_training = _model_frame().filter(pl.col("season") <= 2023)
    paths = apply_service_predictions(_annual_paths(), service_training)
    summary = paths.group_by("player_id").agg(
        pl.col("mapped_service_days").sum().alias("mapped_service_days"),
        pl.col("active_season_shortcut_days").sum().alias(
            "active_season_shortcut_days"
        ),
        pl.col("raw_workload").gt(0).sum().alias("mlb_active_seasons"),
    )
    fg = pl.read_parquet(
        "reports/generated/fangraphs-opening-day-workbooks/2025/"
        "opening-day-control-baseline.parquet"
    ).select("player_id", pl.col("service_days").alias("observed_service_days"))
    scored = summary.join(fg, on="player_id", how="inner", validate="1:1")
    observed = scored["observed_service_days"].to_numpy().astype(float)
    shortcut = scored["active_season_shortcut_days"].to_numpy()
    mapped = scored["mapped_service_days"].to_numpy()
    capped_observed = np.minimum(observed, CONTROL_SERVICE_DAYS)
    capped_shortcut = np.minimum(shortcut, CONTROL_SERVICE_DAYS)
    capped_mapped = np.minimum(mapped, CONTROL_SERVICE_DAYS)
    report = {
        "status": "prospect_cumulative_service_mapping_audited",
        "label": "fangraphs_2025_opening_service_balance",
        "players": scored.height,
        "mapping_training_seasons": sorted(
            service_training["season"].unique().to_list()
        ),
        "raw_cumulative_service": {
            "active_season_shortcut": _metrics(observed, shortcut),
            "workload_mapping": _metrics(observed, mapped),
        },
        "six_year_control_cap": {
            "active_season_shortcut": _metrics(capped_observed, capped_shortcut),
            "workload_mapping": _metrics(capped_observed, capped_mapped),
        },
        "control_exhaustion": {
            "active_season_shortcut": _classification(observed, shortcut),
            "workload_mapping": _classification(observed, mapped),
        },
        "decision": "diagnostic_only_pending_missing_zero_workload_state",
        "boundaries": {
            "zero_workload_service_days_forced_zero": True,
            "injured_list_state_inferred": False,
            "outside_fv_used": False,
            "survivorship_selection_remains": True,
            "salary_or_value_assigned": False,
        },
    }
    Path("docs/prospect-cumulative-service-mapping-result.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    raw = report["raw_cumulative_service"]
    cap = report["six_year_control_cap"]
    control = report["control_exhaustion"]
    Path("docs/prospect-cumulative-service-mapping-result.md").write_text(
        "\n".join(
            [
                "# Prospect cumulative service mapping",
                "",
                f"The endpoint audit covers {scored.height:,} players with exact FanGraphs 2025 opening service balances.",
                "",
                "| Target | Full-season shortcut MAE | Workload-map MAE | Full-season RMSE | Workload-map RMSE |",
                "|---|---:|---:|---:|---:|",
                f"| Raw cumulative days | {raw['active_season_shortcut']['mae_days']:.1f} | {raw['workload_mapping']['mae_days']:.1f} | {raw['active_season_shortcut']['rmse_days']:.1f} | {raw['workload_mapping']['rmse_days']:.1f} |",
                f"| Six-year capped days | {cap['active_season_shortcut']['mae_days']:.1f} | {cap['workload_mapping']['mae_days']:.1f} | {cap['active_season_shortcut']['rmse_days']:.1f} | {cap['workload_mapping']['rmse_days']:.1f} |",
                "",
                f"Control-exhaustion accuracy is {control['workload_mapping']['accuracy']:.1%} for the workload map versus {control['active_season_shortcut']['accuracy']:.1%} for the shortcut.",
                "",
                "This remains diagnostic. Zero-workload seasons are forced to zero because the current historical roster feed cannot distinguish an injured controlled player from someone out of baseball. That choice is conservative and its undercount remains visible in bias.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
