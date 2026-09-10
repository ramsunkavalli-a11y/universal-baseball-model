#!/usr/bin/env python3
"""Apply the passing player-level position model as a private ranking sensitivity."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from audit_prospect_shortstop_retention import (
    _cohort,
    _fit_predict,
    _position_profile,
)
from universal_baseball.model_fv import display_fv, model_fv_from_expected_war
from universal_baseball.prospect_value import benchmark_value_from_model_fv
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--retention-result",
        type=Path,
        default=Path("docs/prospect-shortstop-retention-result.json"),
    )
    parser.add_argument(
        "--historical-path",
        type=Path,
        default=Path(
            "reports/generated/position-capacity-source/historical/reports/generated/"
            "position-role-historical-source/tables/historical_fielding_usage.parquet"
        ),
    )
    parser.add_argument(
        "--confirmation-path",
        type=Path,
        default=Path(
            "reports/generated/position-capacity-source/2025/reports/generated/"
            "position-role-2025-confirmation-source/tables/"
            "position_role_2025_fielding_usage.parquet"
        ),
    )
    parser.add_argument(
        "--people-path",
        type=Path,
        default=Path(
            "reports/generated/historical-people-control/2025-10-15/tables/people.parquet"
        ),
    )
    parser.add_argument(
        "--current-fielding-path",
        type=Path,
        default=Path(
            "reports/generated/current-defense-rates/2026-09-08/tables/"
            "current-fielding-profiles.parquet"
        ),
    )
    parser.add_argument("--generated-root", type=Path, default=Path("reports/generated"))
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/prospect-shortstop-sensitivity-result.json"),
    )
    return parser.parse_args()


def _current_features(
    fielding: pl.DataFrame, people: pl.DataFrame, season: int
) -> pl.DataFrame:
    usage = fielding.select(
        pl.lit(season).alias("season"),
        "player_id",
        pl.col("position").alias("position_abbreviation"),
        pl.col("fielding_outs").alias("games_started"),
        pl.col("fielding_outs").alias("games_played"),
        pl.col("current_level_group").alias("level_group"),
    ).filter(pl.col("level_group") != "MLB")
    ages = people.select("player_id", "birth_date").with_columns(
        (
            (pl.date(season, 7, 1) - pl.col("birth_date")).dt.total_days()
            / 365.2425
        ).alias("age")
    ).select("player_id", "age")
    return (
        _position_profile(usage, origin_year=season)
        .join(ages, on="player_id", how="left")
        .drop_nulls(["age", "level_score"])
    )


def main() -> int:
    args = _args()
    dated = args.as_of_date.isoformat()
    selection = json.loads(args.retention_result.read_text(encoding="utf-8"))
    if not selection["decision"]["private_position_sensitivity_authorized"]:
        raise ValueError("player-level position challenger did not pass its outer gate")
    selected = selection["selected"]
    features = tuple(selected["features"])
    alpha = float(selected["alpha"])
    usage = pl.concat(
        [pl.read_parquet(args.historical_path), pl.read_parquet(args.confirmation_path)],
        how="vertical_relaxed",
    )
    people = pl.read_parquet(args.people_path)
    training = pl.concat([_cohort(usage, people, year) for year in range(2021, 2025)])
    current = _current_features(
        pl.read_parquet(args.current_fielding_path), people, args.as_of_date.year
    )
    model, predicted_runs = _fit_predict(training, current, features, alpha)
    current = current.with_columns(
        pl.Series("predicted_position_runs_per_600", predicted_runs)
    )

    root = args.generated_root
    nested = pl.read_parquet(
        root / "phase2-nested-career-fv" / dated / "nested-career-model-fv.parquet"
    ).filter(pl.col("ordered_arrival_probability").is_not_null())
    values = pl.read_parquet(
        root / "phase2-current-value" / dated / "value-records.parquet"
    ).select("player_id", "transferable_value_dollars")
    paths_root = root / "phase2-conditional-war-paths" / dated
    paths = pl.read_parquet(paths_root / "tables/hitter_expected_war_paths.parquet")
    war_report = json.loads((paths_root / "report.json").read_text(encoding="utf-8"))
    runs_per_win = float(war_report["reference_environment"]["runs_per_win"])
    path_lookup = {
        int(key[0]): frame for key, frame in paths.group_by("player_id", maintain_order=True)
    }
    current_lookup = {
        int(row["player_id"]): row for row in current.iter_rows(named=True)
    }
    rows = []
    for row in nested.join(values, on="player_id", how="inner").iter_rows(named=True):
        player_id = int(row["player_id"])
        evidence = current_lookup.get(player_id)
        eligible = row["model_player_type"] == "hitter" and evidence is not None
        adjusted_war = float(row["three_tier_expected_six_year_war"])
        if eligible:
            incumbent_position_runs = float(
                path_lookup[player_id].get_column("positional_runs_per_600").mean()
            )
            position_war_delta = (
                float(row["three_tier_expected_workload"])
                * (
                    float(evidence["predicted_position_runs_per_600"])
                    - incumbent_position_runs
                )
                / 600.0
                / runs_per_win
            )
            adjusted_war += position_war_delta
        adjusted_fv = model_fv_from_expected_war(
            adjusted_war, str(row["model_player_type"])
        )
        adjusted_value = (
            benchmark_value_from_model_fv(adjusted_fv, str(row["model_player_type"]))
            if eligible
            else float(row["transferable_value_dollars"])
        )
        rows.append(
            {
                "player_id": player_id,
                "player_name": row["player_name"],
                "model_player_type": row["model_player_type"],
                "primary_position": row["primary_position"],
                "position_evidence_available": eligible,
                "dominant_current_position": (
                    evidence["dominant_position"] if evidence is not None else None
                ),
                "current_position_share": (
                    evidence[f"share_{evidence['dominant_position']}"]
                    if evidence is not None
                    else None
                ),
                "current_level_score": evidence["level_score"] if evidence is not None else None,
                "current_age": evidence["age"] if evidence is not None else None,
                "incumbent_position_runs_per_600": (
                    evidence["baseline_runs"] if evidence is not None else None
                ),
                "predicted_position_runs_per_600": (
                    evidence["predicted_position_runs_per_600"]
                    if evidence is not None
                    else None
                ),
                "incumbent_expected_six_year_war": float(
                    row["three_tier_expected_six_year_war"]
                ),
                "adjusted_expected_six_year_war": adjusted_war,
                "war_delta": adjusted_war
                - float(row["three_tier_expected_six_year_war"]),
                "incumbent_fv_granular": float(row["three_tier_model_fv_granular"]),
                "adjusted_fv_granular": adjusted_fv,
                "incumbent_fv_display": int(row["three_tier_model_fv_display"]),
                "adjusted_fv_display": display_fv(adjusted_fv),
                "incumbent_value_dollars": float(row["transferable_value_dollars"]),
                "adjusted_value_dollars": adjusted_value,
            }
        )
    result = pl.DataFrame(rows).sort("player_id")
    incumbent_ranks = (
        result.sort(
            ["incumbent_value_dollars", "incumbent_expected_six_year_war", "player_id"],
            descending=[True, True, False],
        )
        .with_row_index("incumbent_rank", offset=1)
        .select("player_id", "incumbent_rank")
    )
    adjusted_ranks = (
        result.sort(
            ["adjusted_value_dollars", "adjusted_expected_six_year_war", "player_id"],
            descending=[True, True, False],
        )
        .with_row_index("adjusted_rank", offset=1)
        .select("player_id", "adjusted_rank")
    )
    result = result.join(incumbent_ranks, on="player_id").join(
        adjusted_ranks, on="player_id"
    )
    output = root / "prospect-shortstop-sensitivity" / dated
    output.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        result,
        output / "prospect-shortstop-sensitivity.parquet",
        table_name="prospect_shortstop_sensitivity",
    ).as_record()

    source = pl.read_parquet(
        root / "phase2-prospect-source" / dated / "fangraphs-top-100.parquet"
    ).filter((pl.col("rank") <= 50) & pl.col("player_id").is_not_null())
    source_ids = set(source.get_column("player_id").to_list())
    incumbent_ids = set(
        result.filter(pl.col("incumbent_rank") <= 50).get_column("player_id").to_list()
    )
    adjusted_ids = set(
        result.filter(pl.col("adjusted_rank") <= 50).get_column("player_id").to_list()
    )
    model_only = pl.read_parquet(
        root / "prospect-top50-ranking-audit" / dated / "model-top-50-comparison.parquet"
    ).filter(pl.col("review_flags").list.contains("position_value_dominant"))
    suspect_cases = (
        model_only.select("player_id", "source_rank", "model_rank", "difference_reason")
        .join(result, on="player_id", how="left")
        .sort("model_rank")
        .to_dicts()
    )
    movement_columns = [
        "player_id",
        "player_name",
        "model_player_type",
        "primary_position",
        "dominant_current_position",
        "incumbent_rank",
        "adjusted_rank",
        "war_delta",
    ]
    entering = (
        result.filter(pl.col("player_id").is_in(adjusted_ids - incumbent_ids))
        .select(movement_columns)
        .sort("adjusted_rank")
        .to_dicts()
    )
    leaving = (
        result.filter(pl.col("player_id").is_in(incumbent_ids - adjusted_ids))
        .select(movement_columns)
        .sort("incumbent_rank")
        .to_dicts()
    )
    report = {
        "report_schema_version": "0.1",
        "as_of_date": dated,
        "status": "private_player_level_position_sensitivity_complete",
        "contract": "docs/prospect-shortstop-retention-plan.md",
        "players": result.height,
        "hitters_with_player_level_position_evidence": result.filter(
            pl.col("position_evidence_available")
        ).height,
        "selected_model": {
            "feature_set": selected["feature_set"],
            "alpha": alpha,
            "training_players": training.height,
            "standardized_coefficients": dict(
                zip(
                    features,
                    model.named_steps["ridge"].coef_.tolist(),
                    strict=True,
                )
            ),
        },
        "top_50": {
            "incumbent_fangraphs_overlap": len(incumbent_ids & source_ids),
            "adjusted_fangraphs_overlap": len(adjusted_ids & source_ids),
            "players_entering": entering,
            "players_leaving": leaving,
            "adjusted_player_type_counts": result.filter(
                pl.col("adjusted_rank") <= 50
            ).group_by("model_player_type").len().sort("model_player_type").to_dicts(),
        },
        "position_dominant_cases": suspect_cases,
        "decision": {
            "production_change_authorized": False,
            "next_gate": "player_by_player_case_review_and_full_value_sensitivity_checks",
        },
        "boundaries": {
            "outside_fv_used_as_input": False,
            "fangraphs_used_for_diagnostic_only": True,
            "named_player_adjustment_used": False,
            "pitcher_values_changed": False,
        },
        "storage": storage,
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
