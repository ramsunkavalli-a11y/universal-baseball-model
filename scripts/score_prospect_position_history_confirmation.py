#!/usr/bin/env python3
"""Score the frozen 2019 prospect position-history confirmation."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

try:
    from scripts.audit_prospect_comparable_chronology import _deduplicate, _sources
    from scripts.audit_prospect_position_adjusted_outcomes import _cohort
    from scripts.audit_prospect_position_history_challenger import (
        _attach_origins,
        _fold,
    )
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from audit_prospect_comparable_chronology import _deduplicate, _sources
    from audit_prospect_position_adjusted_outcomes import _cohort
    from audit_prospect_position_history_challenger import _attach_origins, _fold


REFERENCE_ORIGINS = (2008, 2013)
TARGET_ORIGIN = 2019


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--target-skill-path",
        type=Path,
        default=Path(
            "reports/generated/affiliated-skill-source-2019/tables/"
            "affiliated_hitting_components.parquet"
        ),
    )
    parser.add_argument(
        "--origin-fielding-path",
        type=Path,
        default=Path(
            "reports/generated/milb-fielding-origin-inventory/tables/"
            "milb_fielding_usage_at_origins.parquet"
        ),
    )
    parser.add_argument(
        "--mlb-fielding-path",
        type=Path,
        default=Path(
            "reports/generated/mlb-fielding-outcome-inventory-2004-2025/tables/"
            "mlb_fielding_usage_2004_2025.parquet"
        ),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/prospect-position-history-confirmation-result.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/prospect-position-history-confirmation-result.md"),
    )
    return parser.parse_args()


def _passes(fold: dict[str, object]) -> bool:
    position = fold["position_component"]
    combined = fold["position_adjusted_partial_war"]
    position_base = position["level_baseline"]
    position_new = position["position_history_candidate"]
    combined_base = combined["level_baseline"]
    combined_new = combined["position_history_candidate"]
    return bool(
        fold["target_position_coverage"] >= 0.95
        and position_new["rmse"] < position_base["rmse"]
        and combined_new["rmse"] < combined_base["rmse"]
        and abs(position_new["bias"]) <= abs(position_base["bias"])
        and abs(combined_new["bias"]) <= abs(combined_base["bias"])
    )


def main() -> int:
    args = _args()
    root = Path("reports/generated")
    runs_per_win = float(
        json.loads(Path("docs/prospect-component-uncertainty-result.json").read_text())[
            "runs_per_win"
        ]
    )
    snapshots, skill, hitting, debut = _sources(root, "hitter")
    skill = (
        pl.concat([skill, pl.read_parquet(args.target_skill_path)], how="vertical_relaxed")
        .sort(["season", "player_id", "sport_id", "team_id"])
        .unique(
            ["season", "player_id", "sport_id", "team_id"],
            keep="last",
            maintain_order=True,
        )
    )
    origin_fielding = pl.read_parquet(args.origin_fielding_path)
    mlb_fielding = pl.read_parquet(args.mlb_fielding_path)

    def cohort(origin: int) -> pl.DataFrame:
        return _attach_origins(
            _cohort(
                snapshots,
                skill,
                hitting,
                debut,
                mlb_fielding,
                origin=origin,
                runs_per_win=runs_per_win,
            ),
            origin_fielding,
            origin=origin,
        )

    references = [cohort(origin) for origin in REFERENCE_ORIGINS]
    reference = _deduplicate(references)
    fold = _fold(reference, cohort(TARGET_ORIGIN))
    passed = _passes(fold)
    report = {
        "status": "prospect_position_history_confirmation_scored",
        "as_of_date": args.as_of_date.isoformat(),
        "contract": "docs/prospect-position-history-confirmation-contract.md",
        "reference_origins": list(REFERENCE_ORIGINS),
        "target_origin": TARGET_ORIGIN,
        "decision": "promote_position_history" if passed else "withhold_position_history",
        "passed": passed,
        "outside_fv_used": False,
        "fold": fold,
    }
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    position = fold["position_component"]
    combined = fold["position_adjusted_partial_war"]
    args.output_md.write_text(
        "\n".join(
            [
                "# Prospect position-history confirmation",
                "",
                f"**Decision:** `{report['decision']}`",
                "",
                f"Official 2019 origin-position coverage is {fold['target_position_coverage']:.1%}.",
                "",
                "| Expected-value target | Candidate RMSE | Baseline RMSE | Candidate bias | Baseline bias |",
                "|---|---:|---:|---:|---:|",
                f"| Position WAR | {position['position_history_candidate']['rmse']:.4f} | {position['level_baseline']['rmse']:.4f} | {position['position_history_candidate']['bias']:.4f} | {position['level_baseline']['bias']:.4f} |",
                f"| Position-adjusted partial WAR | {combined['position_history_candidate']['rmse']:.4f} | {combined['level_baseline']['rmse']:.4f} | {combined['position_history_candidate']['bias']:.4f} | {combined['level_baseline']['bias']:.4f} |",
                "",
                "MAE is retained in the machine-readable result but is not a veto for the mean expected-value target. No FV, public rank, name or 2026 outcome was used.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
