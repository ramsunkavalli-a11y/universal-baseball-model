#!/usr/bin/env python3
"""Verify the frozen full-hitter forecast without opening 2026 results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("docs/hitter-full-2026-confirmation-contract.json"),
    )
    return parser.parse_args()


def _resolve(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else Path.cwd() / path


def _assert_close(frame: pl.DataFrame, actual: str, expected: pl.Expr) -> None:
    difference = frame.select((pl.col(actual) - expected).abs().max()).item()
    if difference is None or float(difference) > 1e-10:
        raise ValueError(f"{actual} does not recompose; maximum error={difference}")


def main() -> int:
    args = _args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    forecast_path = _resolve(contract["forecast_path"])
    manifest_path = _resolve(contract["manifest_path"])
    if sha256_file(forecast_path) != contract["forecast_sha256"]:
        raise ValueError("forecast hash differs from the locked contract")
    if sha256_file(manifest_path) != contract["manifest_sha256"]:
        raise ValueError("manifest hash differs from the locked contract")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["protected_2026_participants_or_outcomes_opened"]:
        raise ValueError("manifest says protected 2026 evidence was opened")
    verified_files = 0
    for group in (manifest["artifacts"].values(), manifest["input_files"]):
        for record in group:
            if isinstance(record, str):
                record = manifest["artifacts"][record]
            path = _resolve(record["path"])
            if not path.is_file():
                raise FileNotFoundError(path)
            if sha256_file(path) != record.get("file_sha256", record.get("sha256")):
                raise ValueError(f"hash mismatch: {path}")
            verified_files += 1

    locked_opportunity = _resolve(contract["locked_opportunity_path"])
    if sha256_file(locked_opportunity) != contract["locked_opportunity_sha256"]:
        raise ValueError("locked opportunity file hash differs from contract")
    forecast = pl.read_parquet(forecast_path)
    opportunity = pl.read_parquet(locked_opportunity)
    expected_rows = int(contract["forecast_players"])
    if forecast.height != expected_rows or forecast["player_id"].n_unique() != expected_rows:
        raise ValueError("forecast population is not the locked unique-player population")
    if set(forecast["player_id"]) != set(opportunity["player_id"]):
        raise ValueError("forecast IDs differ from the locked opportunity universe")
    if forecast["source_season"].unique().to_list() != [2025]:
        raise ValueError("source season is not exactly 2025")
    if forecast["forecast_season"].unique().to_list() != [2026]:
        raise ValueError("forecast season is not exactly 2026")
    tier_counts = {
        row["batting_evidence_tier"]: row["len"]
        for row in forecast.group_by("batting_evidence_tier").len().to_dicts()
    }
    expected_tier_counts = {
        "five_model_detailed_contact": int(
            manifest["population"]["five_model_batting_rows"]
        ),
        "opportunity_scaled_population_rate_prior": int(
            manifest["population"]["population_prior_rows"]
        ),
    }
    if tier_counts != expected_tier_counts:
        raise ValueError("batting evidence tiers differ from the frozen manifest")
    forbidden = [
        column
        for column in forecast.columns
        if column.startswith(("actual_", "target_"))
    ]
    if forbidden:
        raise ValueError(f"outcome-like columns found in forecast: {forbidden}")

    prediction_columns = [
        column
        for column, dtype in forecast.schema.items()
        if column.startswith(("prediction_", "benchmark_", "selected_"))
        and dtype.is_numeric()
    ]
    values = forecast.select(prediction_columns).to_numpy()
    if not np.isfinite(values).all():
        raise ValueError("non-finite numeric forecast values found")
    if forecast.filter(pl.col("prediction_general_defense_war") != 0).height:
        raise ValueError("general defense must remain the locked neutral zero")
    _assert_close(
        forecast,
        "prediction_baserunning_war",
        pl.col("prediction_steal_war") + pl.col("prediction_advancement_war"),
    )
    _assert_close(
        forecast,
        "prediction_selected_partial_war",
        pl.col("prediction_batting_replacement_war")
        + pl.col("prediction_position_war")
        + pl.col("prediction_baserunning_war")
        + pl.col("prediction_catcher_defense_war"),
    )
    _assert_close(
        forecast,
        "prediction_routed_partial_war",
        pl.col("prediction_routed_batting_replacement_war")
        + pl.col("prediction_position_war")
        + pl.col("prediction_baserunning_war")
        + pl.col("prediction_catcher_defense_war"),
    )
    for level in (50, 80, 90):
        invalid = forecast.filter(
            pl.col(f"selected_lower_{level}") > pl.col(f"selected_upper_{level}")
        )
        if invalid.height:
            raise ValueError(f"selected {level}% interval has reversed bounds")
    invalid_nesting = forecast.filter(
        (pl.col("selected_lower_90") > pl.col("selected_lower_80"))
        | (pl.col("selected_lower_80") > pl.col("selected_lower_50"))
        | (pl.col("selected_upper_90") < pl.col("selected_upper_80"))
        | (pl.col("selected_upper_80") < pl.col("selected_upper_50"))
    )
    if invalid_nesting.height:
        raise ValueError("forecast intervals are not properly nested")

    report = {
        "status": "verified",
        "forecast_sha256": contract["forecast_sha256"],
        "players": forecast.height,
        "five_model_rows": tier_counts["five_model_detailed_contact"],
        "population_prior_rows": tier_counts[
            "opportunity_scaled_population_rate_prior"
        ],
        "contact_available_rows": int(
            forecast["lag0__contact_feature_available"].fill_null(0).sum()
        ),
        "verified_files": verified_files,
        "protected_2026_opened": False,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
