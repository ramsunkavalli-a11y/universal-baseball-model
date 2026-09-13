#!/usr/bin/env python3
"""Test whether workload can replace the rejected full-service-season shortcut."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.isotonic import IsotonicRegression


SEASONS = (2022, 2023, 2024)
MIN_CELL = 20


def _service_labels() -> pl.DataFrame:
    root = Path("reports/generated/fangraphs-opening-day-workbooks")
    debut = pl.read_parquet(
        "reports/generated/career-mlb-outcome-inventory-2009-2025/"
        "tables/people-debut-dates.parquet"
    ).select("player_id", pl.col("mlb_debut_date").dt.year().alias("debut_year"))
    rows: list[pl.DataFrame] = []
    for season in SEASONS:
        following = pl.read_parquet(
            root / str(season + 1) / "opening-day-control-baseline.parquet"
        ).select(
            "player_id", pl.col("service_days").alias("following_service_days")
        )
        if season == SEASONS[0]:
            prior = pl.DataFrame(
                schema={"player_id": pl.Int64, "prior_service_days": pl.Int64}
            )
        else:
            prior = pl.read_parquet(
                root / str(season) / "opening-day-control-baseline.parquet"
            ).select(
                "player_id", pl.col("service_days").alias("prior_service_days")
            )
        label = (
            following.join(prior, on="player_id", how="left")
            .join(debut, on="player_id", how="left", validate="m:1")
            .with_columns(
                pl.when(pl.col("prior_service_days").is_not_null())
                .then(
                    pl.col("following_service_days") - pl.col("prior_service_days")
                )
                .when(pl.col("debut_year") == season)
                .then(pl.col("following_service_days"))
                .otherwise(pl.lit(None, dtype=pl.Int64))
                .alias("service_days")
            )
            .filter(pl.col("service_days").is_between(0, 172))
            .select(
                "player_id", pl.lit(season).alias("season"), "debut_year",
                "service_days",
            )
        )
        rows.append(label)
    return pl.concat(rows).sort(["season", "player_id"])


def _workload() -> pl.DataFrame:
    root = Path("reports/generated/career-mlb-outcome-inventory-2009-2025/tables")
    batting = (
        pl.read_parquet(root / "mlb_batting_2009_2025.parquet")
        .filter(pl.col("season").is_in(SEASONS))
        .select("player_id", "season", "batting_pa")
    )
    pitching = (
        pl.read_parquet(root / "mlb_pitching_2009_2025.parquet")
        .filter(pl.col("season").is_in(SEASONS))
        .select("player_id", "season", "pitching_bf")
    )
    return (
        batting.join(pitching, on=["player_id", "season"], how="full", coalesce=True)
        .with_columns(
            pl.col("batting_pa").fill_null(0),
            pl.col("pitching_bf").fill_null(0),
        )
    )


def _model_frame() -> pl.DataFrame:
    return (
        _service_labels()
        .join(_workload(), on=["player_id", "season"], how="left")
        .with_columns(
            pl.col("batting_pa").fill_null(0),
            pl.col("pitching_bf").fill_null(0),
        )
        .with_columns(
            pl.when(pl.col("batting_pa") / 600 >= pl.col("pitching_bf") / 800)
            .then(pl.lit("hitter"))
            .otherwise(pl.lit("pitcher"))
            .alias("player_type"),
            (pl.col("debut_year") == pl.col("season"))
            .fill_null(False)
            .alias("first_mlb_season"),
        )
        .with_columns(
            pl.when(pl.col("player_type") == "hitter")
            .then(pl.col("batting_pa"))
            .otherwise(pl.col("pitching_bf"))
            .cast(pl.Float64)
            .alias("workload")
        )
        .sort(["season", "player_id"])
    )


def _predict(train: pl.DataFrame, test: pl.DataFrame) -> np.ndarray:
    predictions = np.full(test.height, np.nan, dtype=float)
    global_mean = float(train.get_column("service_days").mean())
    indexed = test.with_row_index("row_index")
    for player_type in ("hitter", "pitcher"):
        for first in (False, True):
            cell = train.filter(
                (pl.col("player_type") == player_type)
                & (pl.col("first_mlb_season") == first)
            )
            targets = indexed.filter(
                (pl.col("player_type") == player_type)
                & (pl.col("first_mlb_season") == first)
            )
            if not targets.height:
                continue
            if cell.height < MIN_CELL:
                value = float(cell.get_column("service_days").mean()) if cell.height else global_mean
                predictions[targets.get_column("row_index").to_numpy()] = value
                continue
            model = IsotonicRegression(y_min=0.0, y_max=172.0, out_of_bounds="clip")
            model.fit(
                cell.get_column("workload").to_numpy(),
                cell.get_column("service_days").to_numpy(),
            )
            predictions[targets.get_column("row_index").to_numpy()] = model.predict(
                targets.get_column("workload").to_numpy()
            )
    if not np.isfinite(predictions).all():
        raise RuntimeError("service mapping left an unsupported prediction cell")
    return predictions


def _scores(observed: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    error = predicted - observed
    return {
        "bias_days": float(error.mean()),
        "mae_days": float(np.abs(error).mean()),
        "rmse_days": float(np.sqrt(np.square(error).mean())),
    }


def main() -> int:
    frame = _model_frame()
    folds: dict[str, object] = {}
    passes = []
    evaluations = (
        (2023, True, "2023_first_mlb_season"),
        (2024, True, "2024_first_mlb_season"),
        (2024, False, "2024_returning_player"),
    )
    for target_season, first_mlb_season, label in evaluations:
        train = frame.filter(
            (pl.col("season") < target_season)
            & (pl.col("first_mlb_season") == first_mlb_season)
        )
        test = frame.filter(
            (pl.col("season") == target_season)
            & (pl.col("first_mlb_season") == first_mlb_season)
        )
        observed = test.get_column("service_days").to_numpy().astype(float)
        old = np.where(test.get_column("workload").to_numpy() > 0, 172.0, 0.0)
        candidate = _predict(train, test)
        old_scores = _scores(observed, old)
        candidate_scores = _scores(observed, candidate)
        passed = (
            candidate_scores["mae_days"] < old_scores["mae_days"]
            and candidate_scores["rmse_days"] < old_scores["rmse_days"]
        )
        passes.append(passed)
        folds[label] = {
            "target_season": target_season,
            "first_mlb_season": first_mlb_season,
            "training_seasons": sorted(train.get_column("season").unique().to_list()),
            "players": test.height,
            "first_mlb_season_players": test.filter(pl.col("first_mlb_season")).height,
            "old_full_season_shortcut": old_scores,
            "monotone_workload_mapping": candidate_scores,
            "passed": passed,
        }
    report = {
        "status": "workload_service_mapping_audited",
        "decision": "retain_for_next_joint_path_replay" if all(passes) else "reject",
        "label_source": "year_over_year_fangraphs_opening_service_balance",
        "rows": frame.height,
        "seasons": list(SEASONS),
        "folds": folds,
        "model": {
            "form": "monotone_isotonic_service_days_from_workload",
            "cells": ["player_type", "first_mlb_season"],
            "minimum_training_cell": MIN_CELL,
            "outside_fv_used": False,
        },
        "boundaries": {
            "opening_balance_source_is_later_retrieved": True,
            "players_missing_next_opening_balance_are_not_labeled": True,
            "survivorship_selection_remains": True,
            "service_mapping_not_yet_joined_to_career_paths": True,
            "super_two_and_salary_not_tested": True,
            "player_value_unchanged": True,
        },
    }
    output_json = Path("docs/prospect-service-day-mapping-result.json")
    output_md = Path("docs/prospect-service-day-mapping-result.md")
    output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Prospect service-day mapping result",
        "",
        f"**Decision:** `{report['decision']}`",
        "",
        "The test replaces the old assumption that any active MLB season earns 172 service days. "
        "It uses only workload, player type and whether the season is the player's first MLB season.",
        "",
        "| Test season | Players | Old MAE | Candidate MAE | Old RMSE | Candidate RMSE |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for label, result in folds.items():
        old = result["old_full_season_shortcut"]
        candidate = result["monotone_workload_mapping"]
        lines.append(
            f"| {label} | {result['players']:,} | {old['mae_days']:.1f} | "
            f"{candidate['mae_days']:.1f} | {old['rmse_days']:.1f} | "
            f"{candidate['rmse_days']:.1f} |"
        )
    lines.extend([
        "",
        "This is not a controlled-value result. The labeled sample omits players absent from the "
        "following opening tracker, so the mapping must next be tested inside the complete career path.",
        "",
    ])
    output_md.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
