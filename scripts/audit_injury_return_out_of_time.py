#!/usr/bin/env python3
"""Test the existing IL-type/elapsed cells on later seasons."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.injury_return import (
    fit_injury_return_references,
    score_injury_return_references,
)


SOURCE = Path(
    "reports/generated/injury-return-history/tables/injury-return-cohort.parquet"
)
OUTPUT = Path("docs/injury-return-out-of-time-result.json")


def main() -> int:
    cohort = pl.read_parquet(SOURCE)
    development = cohort.filter(pl.col("season").is_between(2022, 2023))
    validation = cohort.filter(pl.col("season").is_between(2024, 2025))
    fit = fit_injury_return_references(development, prior_players=25.0)
    scored, metrics = score_injury_return_references(validation, fit)
    yearly = {}
    for season in (2024, 2025):
        _, season_metrics = score_injury_return_references(
            validation.filter(pl.col("season") == season), fit
        )
        yearly[str(season)] = season_metrics
    cell = metrics["cell_model"]
    baseline = metrics["population_baseline"]
    selected = (
        cell["brier"] < baseline["brier"]
        and cell["log_loss"] < baseline["log_loss"]
        and cell["availability_mae"] <= baseline["availability_mae"]
        and cell["availability_rmse"] <= baseline["availability_rmse"]
    )
    report = {
        "report_schema_version": "0.1",
        "status": "out_of_time_injury_return_test_complete",
        "development_seasons": [2022, 2023],
        "validation_seasons": [2024, 2025],
        "development_players": development.height,
        "validation_players": validation.height,
        "validation_cell_coverage": int(
            scored.filter(pl.col("prediction_reference_level") == "cell").height
        ),
        "pooled_validation": metrics,
        "annual_validation": yearly,
        "selection_rule": (
            "IL-type/elapsed cells must improve Brier, log loss, availability MAE "
            "and availability RMSE versus the development population mean"
        ),
        "cell_model_selected": selected,
        "features": ["injury_list_type", "days_on_il_at_cutoff"],
        "diagnosis_age_recurrence_used": False,
        "production_changed": False,
    }
    OUTPUT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
