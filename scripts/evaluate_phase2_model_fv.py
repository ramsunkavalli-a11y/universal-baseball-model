#!/usr/bin/env python3
"""Validate internal Model FV and report league distributions without quotas."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_value import numeric_fv


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--model-root", type=Path,
        default=Path("reports/generated/phase2-model-fv"),
    )
    parser.add_argument(
        "--external-root", type=Path,
        default=Path("reports/generated/phase2-prospect-source"),
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/phase2-model-fv-evaluation"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    dated = args.as_of_date.isoformat()
    model = pl.read_parquet(args.model_root / dated / "model-fv.parquet")
    external = pl.read_parquet(
        args.external_root / dated / "fangraphs-top-100.parquet"
    ).filter(pl.col("player_id").is_not_null()).select(
        "player_id", "rank",
        pl.col("future_value").map_elements(numeric_fv, return_dtype=pl.Float64)
        .alias("external_fv"),
    )
    comparison = external.join(model, on="player_id", how="inner", validate="1:1").with_columns(
        (pl.col("model_fv_granular") - pl.col("external_fv")).alias("fv_error")
    )
    output = args.output_root / dated
    output.mkdir(parents=True, exist_ok=True)
    comparison.write_parquet(output / "external-validation.parquet")
    distribution = (
        model.group_by(
            "model_player_type", "model_role", "diagnostic_role_bucket", "model_fv_display"
        )
        .len().sort(
            "model_player_type", "model_role", "diagnostic_role_bucket", "model_fv_display"
        )
    )
    distribution.write_parquet(output / "league-role-fv-distribution.parquet")
    report = {
        "report_schema_version": "0.1", "gate": "phase2_model_fv_diagnostics",
        "as_of_date": dated,
        "external_validation": {
            "matched_players": comparison.height,
            "mean_error": float(comparison.get_column("fv_error").mean()),
            "mae": float(comparison.get_column("fv_error").abs().mean()),
            "within_five_points": float(
                comparison.select((pl.col("fv_error").abs() <= 5).mean()).item()
            ),
        },
        "league_distribution_rows": distribution.height,
        "policy": (
            "Role, position and FV counts are diagnostics only. No player grade is "
            "forced or rescaled to match a quota."
        ),
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
