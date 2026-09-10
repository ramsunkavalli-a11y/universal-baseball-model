#!/usr/bin/env python3
"""Run structural and statistical-law checks on the private preview."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.model_law_audit import audit_private_preview_laws


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--generated-root", type=Path, default=Path("reports/generated"))
    parser.add_argument(
        "--output", type=Path,
        default=Path("docs/private-preview-model-law-audit-result.json"),
    )
    args = parser.parse_args()
    dated = args.as_of_date.isoformat()
    root = args.generated_root
    path_root = root / "phase2-conditional-war-paths" / dated / "tables"
    report = audit_private_preview_laws(
        pl.read_parquet(path_root / "hitter_expected_war_paths.parquet"),
        pl.read_parquet(path_root / "pitcher_expected_war_paths.parquet"),
        pl.read_parquet(root / "phase2-nested-career-fv" / dated / "nested-career-model-fv.parquet"),
        pl.read_parquet(root / "phase2-current-value" / dated / "value-records.parquet"),
    )
    report.update(
        {
            "report_schema_version": "0.1",
            "as_of_date": dated,
            "status": "private_preview_model_law_audit_complete",
            "warnings": [
                "The nested six-year hurdle repeats two-year hazards approximately; it is not a joint path simulation.",
                "Organization-neutral value is not a current-team playing-time allocation; team capacity is a separate research view.",
                "Annual WAR and value ranges are sensitivity bounds; their full-universe 2025 coverage was dominated by nonparticipants.",
                "Passing identities does not replace prospective outcome validation after the protected 2026 season is complete.",
            ],
            "boundaries": {
                "model_refit": False,
                "current_2026_outcomes_read": False,
                "outside_fv_used": False,
                "contract_values_changed": False,
            },
        }
    )
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "failed": report["failed"]}, indent=2))
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
