#!/usr/bin/env python3
"""Materialize independent Model FV from projected player production."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.model_fv import MODEL_FV_ID, build_model_fv
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--war-root", type=Path,
        default=Path("reports/generated/phase2-conditional-war-paths"),
    )
    parser.add_argument(
        "--uncertainty-root", type=Path,
        default=Path("reports/generated/phase2-war-uncertainty"),
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/phase2-model-fv"),
    )
    parser.add_argument(
        "--control-root", type=Path,
        default=Path("reports/generated/league-control"),
    )
    parser.add_argument(
        "--arrival-root", type=Path,
        default=Path("reports/generated/phase2-prospect-arrival"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    dated = args.as_of_date.isoformat()
    war_tables = args.war_root / dated / "tables"
    uncertainty = (
        args.uncertainty_root / dated / "tables/whole-player-war-uncertainty.parquet"
    )
    control = pl.read_parquet(
        args.control_root / dated / "league-control-snapshot.parquet"
    )
    pre_mlb_ids = set(
        control.filter(pl.col("mlb_debut_date").is_null())
        .get_column("player_id").to_list()
    )
    arrival_probabilities: dict[tuple[str, int], float] = {}
    meaningful_role_probabilities: dict[tuple[str, int], float] = {}
    established_role_probabilities: dict[tuple[str, int], float] = {}
    for player_type in ("hitter", "pitcher"):
        arrival = pl.read_parquet(
            args.arrival_root / dated / f"{player_type}-arrival-probabilities.parquet"
        )
        arrival_probabilities.update(
            {
                (player_type, int(row["player_id"])): float(
                    row["predicted_six_year_arrival_probability"]
                )
                for row in arrival.iter_rows(named=True)
            }
        )
        meaningful_role_probabilities.update(
            {
                (player_type, int(row["player_id"])): float(
                    row["predicted_six_year_meaningful_role_probability"]
                )
                for row in arrival.iter_rows(named=True)
            }
        )
        established_role_probabilities.update(
            {
                (player_type, int(row["player_id"])): float(
                    row["predicted_six_year_established_role_probability"]
                )
                for row in arrival.iter_rows(named=True)
            }
        )
    values = build_model_fv(
        pl.read_parquet(war_tables / "hitter_expected_war_paths.parquet"),
        pl.read_parquet(war_tables / "pitcher_expected_war_paths.parquet"),
        pl.read_parquet(uncertainty),
        pre_mlb_player_ids=pre_mlb_ids,
        pre_mlb_arrival_probabilities=arrival_probabilities,
        pre_mlb_meaningful_role_probabilities=meaningful_role_probabilities,
        pre_mlb_established_role_probabilities=established_role_probabilities,
    )
    output = args.output_root / dated
    output.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        values, output / "model-fv.parquet", table_name="phase2_model_fv"
    ).as_record()
    report = {
        "report_schema_version": "0.1", "gate": "phase2_model_fv",
        "as_of_date": dated, "model_fv_id": MODEL_FV_ID, "players": values.height,
        "method": (
            "our production and historical cumulative MLB-arrival probability mapped "
            "to six team-control seasons, granular Model FV, and nearest-five display"
        ),
        "boundaries": {
            "publication_player_grades_used_as_inputs": False,
            "contract_status_or_salary_used_in_fv": False,
            "generic_second_risk_discount_used": False,
            "fangraphs_cohort_war_and_dollar_benchmarks_used": True,
            "pre_mlb_calendar_horizon_truncation_used": False,
            "annual_active_probabilities_treated_as_independent_hazards": False,
            "historical_arrival_model_used": True,
            "meaningful_role_probability_is_diagnostic_only": True,
            "established_role_probability_is_diagnostic_only": True,
            "role_workload_pa": {"catcher": 450.0, "other_hitter": 550.0},
        },
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
