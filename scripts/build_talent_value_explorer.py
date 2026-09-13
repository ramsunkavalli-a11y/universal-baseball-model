#!/usr/bin/env python3
"""Build the separate prospect talent-versus-value explorer."""

from __future__ import annotations

import argparse
from pathlib import Path

from build_results_explorer import (
    PHASE2_ROOT,
    audit_phase2_checkpoint,
    phase2_model_details,
)
from universal_baseball.results_explorer import write_talent_value_explorer


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", default=None)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/generated/talent-value-explorer/index.html"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    dates = {child.name for child in PHASE2_ROOT.iterdir() if child.is_dir()}
    if not dates:
        raise FileNotFoundError("No Phase 2 value checkpoint was found")
    as_of_date = args.as_of_date or max(dates)
    dated = PHASE2_ROOT / as_of_date
    value_path = dated / "value-records.parquet"
    annual_path = dated / "annual-contract-economics.parquet"
    names_path = (
        Path("reports/generated/league-control") / as_of_date
        / "league-control-snapshot.parquet"
    )
    audit_phase2_checkpoint(as_of_date, value_path, annual_path)
    payload = write_talent_value_explorer(
        value_path,
        annual_path,
        names_path,
        args.output,
        model_details=phase2_model_details(as_of_date),
    )
    prospects = sum(player["is_pre_mlb_value"] for player in payload["players"])
    print(f"Talent-value explorer created: {args.output.resolve()}")
    print(f"Prospects: {prospects:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
