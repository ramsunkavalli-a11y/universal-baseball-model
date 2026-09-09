#!/usr/bin/env python3
"""Build a private FV sensitivity using mature post-debut workload outcomes."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.model_fv import apply_pre_mlb_outcome_quality_workload
from universal_baseball.prospect_value import numeric_fv
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--model-fv-root", type=Path,
        default=Path("reports/generated/phase2-model-fv"),
    )
    parser.add_argument(
        "--control-root", type=Path,
        default=Path("reports/generated/league-control"),
    )
    parser.add_argument(
        "--prior-path", type=Path,
        default=Path(
            "reports/generated/prospect-outcome-quality/"
            "post-debut-workload-priors.parquet"
        ),
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/phase2-outcome-quality-fv"),
    )
    parser.add_argument(
        "--external-check-path", type=Path,
        default=Path(
            "reports/generated/phase2-prospect-source/2026-09-08/"
            "fangraphs-top-100.parquet"
        ),
    )
    return parser.parse_args()


def _threshold_counts(frame: pl.DataFrame, column: str) -> dict[str, int]:
    return {
        str(threshold): frame.filter(pl.col(column) >= threshold).height
        for threshold in (40, 45, 50, 55, 60)
    }


def main() -> int:
    args = _args()
    dated = args.as_of_date.isoformat()
    control = pl.read_parquet(
        args.control_root / dated / "league-control-snapshot.parquet"
    )
    pre_mlb = control.filter(pl.col("mlb_debut_date").is_null()).select(
        "player_id", "player_name", "organization_id"
    )
    values = pl.read_parquet(args.model_fv_root / dated / "model-fv.parquet")
    challenger = apply_pre_mlb_outcome_quality_workload(
        values,
        pl.read_parquet(args.prior_path),
        pre_mlb_player_ids=set(pre_mlb.get_column("player_id").to_list()),
    ).join(pre_mlb, on="player_id", how="left", validate="1:1")
    evaluated = challenger.filter(pl.col("player_name").is_not_null())
    output = args.output_root / dated
    output.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        challenger,
        output / "outcome-quality-model-fv.parquet",
        table_name="phase2_outcome_quality_model_fv",
    ).as_record()
    by_type = {}
    for player_type in ("hitter", "pitcher"):
        typed = evaluated.filter(pl.col("model_player_type") == player_type)
        by_type[player_type] = {
            "players": typed.height,
            "incumbent_war": float(
                typed.get_column("incumbent_expected_six_year_war").sum()
            ),
            "challenger_war": float(
                typed.get_column("outcome_quality_expected_six_year_war").sum()
            ),
            "incumbent_fv_counts": _threshold_counts(typed, "model_fv_display"),
            "challenger_fv_counts": _threshold_counts(
                typed, "outcome_quality_model_fv_display"
            ),
        }
    largest_reductions = (
        evaluated.with_columns(
            (
                pl.col("outcome_quality_expected_six_year_war")
                - pl.col("incumbent_expected_six_year_war")
            ).alias("war_change")
        )
        .sort("war_change")
        .select(
            "player_id", "player_name", "model_player_type",
            "model_arrival_probability", "model_meaningful_role_probability",
            "incumbent_expected_six_year_war",
            "outcome_quality_expected_six_year_war", "model_fv_display",
            "outcome_quality_model_fv_display", "war_change",
        )
        .head(25)
        .to_dicts()
    )
    requested_examples = (
        evaluated.filter(pl.col("player_id").is_in([829034, 657277]))
        .select(
            "player_id", "player_name", "model_player_type",
            "model_arrival_probability", "model_meaningful_role_probability",
            "incumbent_expected_six_year_war",
            "outcome_quality_expected_six_year_war", "model_fv_display",
            "outcome_quality_model_fv_display",
        )
        .to_dicts()
    )
    external_check: dict[str, object] | None = None
    if args.external_check_path.exists():
        external = (
            pl.read_parquet(args.external_check_path)
            .filter(pl.col("player_id").is_not_null())
            .with_columns(
                pl.col("future_value").map_elements(
                    numeric_fv, return_dtype=pl.Float64
                ).alias("external_fv")
            )
        )
        joined = external.join(evaluated, on="player_id", how="inner")
        external_check = {
            "role": "diagnostic_only_not_model_input",
            "players": joined.height,
            "incumbent_mae": float(
                (joined["model_fv_granular"] - joined["external_fv"])
                .abs().mean()
            ),
            "challenger_mae": float(
                (
                    joined["outcome_quality_model_fv_granular"]
                    - joined["external_fv"]
                ).abs().mean()
            ),
            "incumbent_bias": float(
                (joined["model_fv_granular"] - joined["external_fv"]).mean()
            ),
            "challenger_bias": float(
                (
                    joined["outcome_quality_model_fv_granular"]
                    - joined["external_fv"]
                ).mean()
            ),
        }
    report = {
        "report_schema_version": "0.1",
        "as_of_date": dated,
        "status": "private_outcome_quality_sensitivity_not_promoted",
        "method": (
            "disjoint six-year any-arrival-only and meaningful-role workload paths "
            "multiplied by the existing conditional WAR rate"
        ),
        "boundaries": {
            "publication_grades_used": False,
            "historical_workload_not_historical_war": True,
            "2020_scaled_to_162_game_equivalent": True,
            "current_values_changed": False,
            "fresh_confirmation_required": True,
        },
        "by_player_type": by_type,
        "largest_war_reductions": largest_reductions,
        "requested_examples": requested_examples,
        "external_fv_check": external_check,
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
