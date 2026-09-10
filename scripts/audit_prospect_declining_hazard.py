#!/usr/bin/env python3
"""Test whether prospect arrival hazards should decline after the first window."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.prospect_arrival import (
    build_arrival_cohort,
    fit_arrival_model,
    predict_arrival,
)


DECAYS = (0.0, 0.25, 0.5, 0.75, 1.0)
OUTCOMES = {
    "arrival": "arrived_within_horizon",
    "meaningful_role": "meaningful_role_within_horizon",
    "established_role": "established_role_within_horizon",
}


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--history-root", type=Path,
        default=Path("reports/generated/opportunity-history-sources-v2/tables"),
    )
    parser.add_argument(
        "--membership-path", type=Path,
        default=Path("reports/generated/opportunity-40man-history/tables/historical_40man_membership.parquet"),
    )
    parser.add_argument(
        "--skill-root", type=Path,
        default=Path("reports/generated/phase2-arrival-skill-source/tables"),
    )
    parser.add_argument(
        "--demographics-path", type=Path,
        default=Path("reports/generated/player-demographics/tables/player-demographics.parquet"),
    )
    parser.add_argument(
        "--debut-dates-path", type=Path,
        default=Path("reports/generated/career-mlb-outcome-inventory-2009-2025/tables/people-debut-dates.parquet"),
    )
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/prospect-declining-hazard-result.json"),
    )
    parser.add_argument(
        "--output-md", type=Path,
        default=Path("docs/prospect-declining-hazard-result.md"),
    )
    return parser.parse_args()


def _history_stats(root: Path) -> pl.DataFrame:
    return pl.concat(
        [pl.read_parquet(path) for path in sorted(root.glob("*/affiliated_season_stats.parquet"))],
        how="vertical_relaxed",
    )


def _four_year_probability(probability: np.ndarray, decay: float) -> np.ndarray:
    return 1.0 - (1.0 - probability) * (1.0 - decay * probability)


def _metrics(probability: np.ndarray, observed: np.ndarray) -> dict[str, float]:
    probability = np.clip(probability, 1e-12, 1.0 - 1e-12)
    return {
        "players": int(len(observed)),
        "observed_rate": float(observed.mean()),
        "predicted_rate": float(probability.mean()),
        "brier": float(np.mean((probability - observed) ** 2)),
        "log_loss": float(np.mean(-observed * np.log(probability) - (1 - observed) * np.log(1 - probability))),
    }


def _feature_set(player_type: str, outcome: str) -> str:
    if player_type == "hitter" and outcome == "established_role":
        return "core"
    if player_type == "pitcher" and outcome == "established_role":
        return "development_path"
    return "level_exposure"


def main() -> int:
    args = _args()
    stats = _history_stats(args.history_root)
    membership = pl.read_parquet(args.membership_path)
    demographics = pl.read_parquet(args.demographics_path)
    debut_dates = pl.read_parquet(args.debut_dates_path)
    report: dict[str, object] = {
        "report_schema_version": "0.1",
        "as_of_date": args.as_of_date.isoformat(),
        "status": "declining_hazard_time_ordered_audit_complete",
        "method": "fit two-year model on 2018; select second-window decay on 2019; evaluate on 2021 four-year outcomes",
        "decay_candidates": list(DECAYS),
        "results": {},
        "boundaries": {
            "future_information_used": False,
            "outside_fv_used": False,
            "current_values_changed": False,
            "six_year_extension_tested_directly": False,
            "2020_snapshot_excluded_for_missing_cutoff_safe_age_coverage": True,
            "2019_current_production_components_available": False,
        },
    }
    for player_type in ("hitter", "pitcher"):
        snapshots = pl.read_parquet(args.history_root / f"{player_type}_snapshots.parquet")
        skill = pl.read_parquet(
            args.skill_root / f"affiliated_{'hitting' if player_type == 'hitter' else 'pitching'}_components.parquet"
        )
        two_year = {
            year: build_arrival_cohort(
                snapshots, stats, membership, skill, debut_dates,
                snapshot_year=year, horizon=2, player_type=player_type,
                demographics=demographics,
            )
            for year in (2018, 2019, 2021)
        }
        four_year = {
            year: build_arrival_cohort(
                snapshots, stats, membership, skill, debut_dates,
                snapshot_year=year, horizon=4, player_type=player_type,
                demographics=demographics,
            ).select("player_id", *OUTCOMES.values())
            for year in (2019, 2021)
        }
        type_results = {}
        for outcome, target in OUTCOMES.items():
            feature_set = _feature_set(player_type, outcome)
            fit = fit_arrival_model(
                two_year[2018], player_type=player_type, target_column=target,
                outcome_name=outcome, feature_set=feature_set,
            )
            folds = {}
            for year in (2019, 2021):
                scored = predict_arrival(fit, two_year[year]).join(
                    four_year[year], on="player_id", how="inner", validate="1:1",
                    suffix="_four_year",
                )
                p = scored.get_column(f"predicted_two_year_{outcome}_probability").to_numpy()
                y = scored.get_column(f"{target}_four_year").to_numpy()
                folds[str(year)] = {
                    str(decay): _metrics(_four_year_probability(p, decay), y)
                    for decay in DECAYS
                }
            selected_decay = min(
                DECAYS, key=lambda decay: folds["2019"][str(decay)]["log_loss"]
            )
            confirmed = all(
                folds["2021"][str(selected_decay)][metric]
                <= folds["2021"]["1.0"][metric]
                for metric in ("brier", "log_loss")
            )
            type_results[outcome] = {
                "feature_set": feature_set,
                "selected_decay": selected_decay,
                "confirmation_passed": confirmed,
                "folds": folds,
            }
        report["results"][player_type] = type_results
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Prospect declining-hazard result", "",
        "Status: completed time-ordered research audit; no current value changed.", "",
        "The two-year model was fit on 2018. A second-window hazard multiplier was",
        "selected on the 2019 snapshot, then checked on completed four-year outcomes",
        "from the 2021 snapshot. The 2020 snapshot lacks usable cutoff-safe age",
        "coverage and is excluded. A value of 1.0 is the current constant",
        "hazard; smaller values represent attrition after the first two-year window.", "",
        "| Player type | Outcome | Selected decay | 2021 passes? |", "|---|---|---:|---|",
    ]
    for player_type, outcomes in report["results"].items():
        for outcome, result in outcomes.items():
            lines.append(
                f"| {player_type} | {outcome} | {result['selected_decay']:.2f} | {'Yes' if result['confirmation_passed'] else 'No'} |"
            )
    lines.extend([
        "", "A six-year production change is not authorized by this test alone because",
        "only the second two-year window has complete directly tested outcomes. The",
        "third-window decay would still be an extrapolation. See the JSON for every",
        "candidate and fold score.", "",
        "No outside FV, manual prospect opinion, future depth, or player exception was used.",
        "The 2019 snapshot has age/level/roster history but no current-season component",
        "table, so this is a hazard-shape check rather than a full model confirmation.",
    ])
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        player_type: {
            outcome: {"decay": value["selected_decay"], "passed": value["confirmation_passed"]}
            for outcome, value in outcomes.items()
        }
        for player_type, outcomes in report["results"].items()
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
