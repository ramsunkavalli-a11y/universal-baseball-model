#!/usr/bin/env python3
"""Build a self-contained local webpage for exploring Phase 1 results."""

from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl

from universal_baseball.model_law_audit import audit_private_preview_laws
from universal_baseball.results_explorer import write_explorer


REPORT_ROOTS = (
    Path("reports/generated/phase1-sequential-replay"),
    Path("reports/generated/current-and-future-contract-economics-v2"),
    Path("reports/generated/league-control"),
)
PHASE2_ROOT = Path("reports/generated/phase2-current-value")


def audit_phase2_checkpoint(as_of_date: str, value_path: Path) -> dict[str, object]:
    """Refuse to open a Phase 2 checkpoint that violates model identities."""

    generated = Path("reports/generated")
    conditional = generated / "phase2-conditional-war-paths" / as_of_date / "tables"
    paths = {
        "hitter": conditional / "hitter_expected_war_paths.parquet",
        "pitcher": conditional / "pitcher_expected_war_paths.parquet",
        "nested": generated / "phase2-nested-career-fv" / as_of_date
        / "nested-career-model-fv.parquet",
        "values": value_path,
    }
    if missing := [path for path in paths.values() if not path.exists()]:
        joined = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Phase 2 law-audit inputs are missing:\n{joined}")
    result = audit_private_preview_laws(
        pl.read_parquet(paths["hitter"]),
        pl.read_parquet(paths["pitcher"]),
        pl.read_parquet(paths["nested"]),
        pl.read_parquet(paths["values"]),
    )
    if result["failed"]:
        failures = ", ".join(
            str(check["name"])
            for check in result["checks"]
            if check["status"] == "fail"
        )
        raise RuntimeError(f"Phase 2 model-law audit failed: {failures}")
    return result


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--as-of-date",
        help="Checkpoint date; defaults to the latest date present in all inputs",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/generated/results-explorer/index.html"),
    )
    return parser.parse_args()


def latest_common_date(roots: tuple[Path, ...] = REPORT_ROOTS) -> str:
    date_sets = [
        {child.name for child in root.iterdir() if child.is_dir()}
        if root.exists()
        else set()
        for root in roots
    ]
    common = set.intersection(*date_sets)
    if not common:
        raise FileNotFoundError("No common dated current-results checkpoint was found")
    return max(common)


def main() -> int:
    args = _args()
    phase2_dates = (
        {child.name for child in PHASE2_ROOT.iterdir() if child.is_dir()}
        if PHASE2_ROOT.exists()
        else set()
    )
    as_of_date = args.as_of_date or (
        max(phase2_dates) if phase2_dates else latest_common_date()
    )
    phase2_dated = PHASE2_ROOT / as_of_date
    if (phase2_dated / "value-records.parquet").exists():
        value_path = phase2_dated / "value-records.parquet"
        annual_path = phase2_dated / "annual-contract-economics.parquet"
    else:
        value_path = (
            Path("reports/generated/phase1-sequential-replay")
            / as_of_date
            / "value-records.parquet"
        )
        annual_path = (
            Path("reports/generated/current-and-future-contract-economics-v2")
            / as_of_date
            / "annual-contract-economics.parquet"
        )
    names_path = (
        Path("reports/generated/league-control")
        / as_of_date
        / "league-control-snapshot.parquet"
    )
    missing = [path for path in (value_path, annual_path, names_path) if not path.exists()]
    if missing:
        joined = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Required model outputs are missing:\n{joined}")
    law_result = None
    if (phase2_dated / "value-records.parquet").exists():
        law_result = audit_phase2_checkpoint(as_of_date, value_path)
    payload = write_explorer(value_path, annual_path, names_path, args.output)
    print(f"Results explorer created: {args.output.resolve()}")
    print(
        f"Players: {payload['meta']['player_count']:,} | "
        f"usable: {payload['meta']['available_count']:,} | "
        f"review: {payload['meta']['review_count']:,}"
    )
    if law_result is not None:
        print(f"Model-law checks: {law_result['passed']} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
