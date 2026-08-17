#!/usr/bin/env python3
"""Fit the frozen Challenger-2 additive baseline on accepted valued evidence.

This is a pre-scoring implementation gate.  It consumes the already-accepted
combined 2021-22 valued contact artifact and fits, at each predeclared cutoff, the
exact event-weighted additive baseline:

    terminal_value ~ contact_bin + level_group

using cell sufficient statistics proven equivalent to the original row-wise
normal equations.  It writes coefficients and cell support only.  It does not
predict future rows, attach richer features, compute MSE/MAE, or access 2023.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.current_talent_contact_value_baseline import (
    fit_contact_value_baseline_sufficient_statistics,
)
from universal_baseball.current_talent_contact_value_evidence import (
    CONTACT_VALUE_FROZEN_CUTOFFS,
)
from universal_baseball.performance_season import CONTACT_CORE_BINS


EXPECTED_LEVELS = {"MLB", "AAA", "AA", "HIGH_A", "SINGLE_A", "ROOKIE_COMPLEX"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chronology-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-talent-contact-value-baseline-fits"),
    )
    return parser.parse_args()


def _find_combined(root: Path) -> Path:
    paths = sorted(root.glob("**/current_talent_contact_value_combined_2021_2022.parquet"))
    if len(paths) != 1:
        raise RuntimeError(f"expected one accepted combined valued parquet, found {len(paths)}")
    return paths[0]


def main() -> int:
    args = _parse_args()
    combined_path = _find_combined(args.chronology_root)
    contacts = pl.read_parquet(combined_path)
    if contacts.is_empty():
        raise RuntimeError("accepted combined valued evidence is empty")
    if "terminal_value" not in contacts.columns:
        raise RuntimeError("accepted chronology artifact lacks frozen terminal values")
    if set(contacts.get_column("event_date").dt.year().unique().to_list()) != {2021, 2022}:
        raise RuntimeError("baseline fit evidence must contain exactly 2021 and 2022")

    output_root = args.output_root
    table_dir = output_root / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)

    fits: list[dict[str, object]] = []
    coefficient_rows: list[dict[str, object]] = []
    for cutoff in CONTACT_VALUE_FROZEN_CUTOFFS:
        fitted, cells = fit_contact_value_baseline_sufficient_statistics(
            contacts,
            cutoff_date=cutoff,
        )
        observed_bins = set(cells.get_column("contact_bin").unique().to_list())
        observed_levels = set(cells.get_column("level_group").unique().to_list())
        if observed_bins != set(CONTACT_CORE_BINS):
            raise RuntimeError(
                f"baseline fit {cutoff} lost contact-bin support: {sorted(observed_bins)}"
            )
        if observed_levels != EXPECTED_LEVELS:
            raise RuntimeError(
                f"baseline fit {cutoff} lost level support: {sorted(observed_levels)}"
            )
        if cells.height != len(CONTACT_CORE_BINS) * len(EXPECTED_LEVELS):
            raise RuntimeError(f"baseline fit {cutoff} does not contain all 60 bin-level cells")
        if fitted.max_training_event_date >= cutoff:
            raise RuntimeError(f"baseline fit {cutoff} contains leakage")
        if fitted.fitted_event_count != int(cells.get_column("event_count").sum()):
            raise RuntimeError(f"baseline fit {cutoff} event count disagrees with cells")

        slug = cutoff.isoformat()
        cells.write_csv(table_dir / f"baseline_cells_{slug}.csv")
        coefficients = {
            "intercept": fitted.intercept,
            "contact_bin_effects": fitted.contact_bin_effects,
            "level_group_effects": fitted.level_group_effects,
        }
        fits.append(
            {
                "cutoff_date": cutoff.isoformat(),
                "fitted_event_count": int(fitted.fitted_event_count),
                "max_training_event_date": fitted.max_training_event_date.isoformat(),
                "parameter_count": int(fitted.parameter_count),
                "fitted_level_groups": list(fitted.fitted_level_groups),
                "cell_count": int(cells.height),
                "cell_event_count": int(cells.get_column("event_count").sum()),
                "coefficients": coefficients,
                "full_rank": True,
                "cutoff_safe": True,
            }
        )
        coefficient_rows.append(
            {
                "cutoff_date": cutoff.isoformat(),
                "term_type": "intercept",
                "term": "INTERCEPT",
                "coefficient": float(fitted.intercept),
            }
        )
        coefficient_rows.extend(
            {
                "cutoff_date": cutoff.isoformat(),
                "term_type": "contact_bin",
                "term": key,
                "coefficient": float(value),
            }
            for key, value in fitted.contact_bin_effects.items()
        )
        coefficient_rows.extend(
            {
                "cutoff_date": cutoff.isoformat(),
                "term_type": "level_group",
                "term": key,
                "coefficient": float(value),
            }
            for key, value in fitted.level_group_effects.items()
        )

    pl.DataFrame(coefficient_rows).write_csv(table_dir / "baseline_coefficients.csv")
    report = {
        "report_schema_version": "0.1",
        "gate": "current_talent_contact_value_baseline_fit_pre_scoring",
        "source_chronology_run_id": 32074805618,
        "combined_source_row_count": int(contacts.height),
        "fit_method": "exact_event_weighted_ols_via_bin_level_sufficient_statistics",
        "formula": "terminal_value ~ contact_bin + level_group",
        "reference_contact_bin": "IFFB",
        "reference_level_group": "MLB",
        "fits": fits,
        "boundary": {
            "network_requests_performed": False,
            "model_scoring": False,
            "future_predictions_computed": False,
            "richer_features_attached": False,
            "richer_residual_fitted": False,
            "accessed_2023": False,
            "terminal_values_attached_upstream": True,
            "baseline_fitted": True,
        },
    }
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
