#!/usr/bin/env python3
"""Add calibration intercept/slope diagnostics to one validation fold."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import polars as pl

from materialize_current_talent_baseline_validation import (
    _load_universal_evidence,
    _write_table,
)
from universal_baseball.current_talent_calibration import (
    build_component_calibration_coefficients,
)
from universal_baseball.current_talent_evidence import EvidenceWindow
from universal_baseball.current_talent_validation_dataset import (
    build_validation_snapshot_dataset,
)


VARIANTS = ("fitted_translation", "zero_offset_translation")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--mlb-input-root", type=Path, required=True)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--as-of-date", required=True)
    parser.add_argument("--validation-output-dir", type=Path, required=True)
    parser.add_argument("--half-life-days", type=float, default=90.0)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    cutoff = date.fromisoformat(args.as_of_date)
    summary, profile, _, _ = _load_universal_evidence(
        args.input_root,
        args.mlb_input_root,
        int(args.season),
    )
    window = EvidenceWindow(
        label=f"season_to_date_half_life_{args.half_life_days:g}d",
        lookback_days=None,
        half_life_days=float(args.half_life_days),
    )
    validation = build_validation_snapshot_dataset(
        summary,
        profile,
        cutoff=cutoff,
        window=window,
    )

    report: dict[str, object] = {
        "report_schema_version": "0.1",
        "season": int(args.season),
        "as_of_date": cutoff.isoformat(),
        "ideal_calibration_intercept": 0.0,
        "ideal_calibration_slope": 1.0,
        "variants": {},
    }
    for variant in VARIANTS:
        variant_dir = args.validation_output_dir / variant
        projected_path = variant_dir / "projected_target_profile.parquet"
        if not projected_path.exists():
            raise FileNotFoundError(
                f"missing projected profile for calibration variant {variant}: {projected_path}"
            )
        projected = pl.read_parquet(projected_path)
        coefficients = build_component_calibration_coefficients(
            projected,
            validation.target_profile,
        )
        nonconverged = coefficients.filter(~pl.col("converged"))
        if not nonconverged.is_empty():
            raise ValueError(
                "component calibration coefficient fit did not converge: "
                f"variant={variant}, rows={nonconverged.select('model', 'core_bin', 'fit_status').to_dicts()}"
            )
        table = _write_table(
            coefficients,
            variant_dir,
            "calibration_coefficients",
        )
        report["variants"][variant] = {
            "table": table,
            "model_component_count": int(coefficients.height),
            "converged_count": int(coefficients.filter(pl.col("converged")).height),
            "max_absolute_intercept_error": float(
                coefficients.get_column("absolute_intercept_error").max() or 0.0
            ),
            "max_absolute_slope_error": float(
                coefficients.get_column("absolute_slope_error").max() or 0.0
            ),
        }

    (args.validation_output_dir / "calibration_coefficients_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
