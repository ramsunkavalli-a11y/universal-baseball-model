#!/usr/bin/env python3
"""Materialize a private prospect value sensitivity over position probabilities."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from audit_prospect_position_transition import _cohort
from universal_baseball.model_fv import display_fv, model_fv_from_expected_war
from universal_baseball.player_value_positional_adjustment import POSITIONAL_RUNS_PER_162
from universal_baseball.prospect_position_transition import (
    POSITION_GROUPS,
    adjust_war_rate_for_position,
    position_group,
)
from universal_baseball.prospect_value import numeric_fv
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--transition-result", type=Path,
        default=Path("docs/prospect-position-transition-result.json"),
    )
    parser.add_argument(
        "--historical-path", type=Path,
        default=Path(
            "reports/generated/position-capacity-source/historical/reports/generated/"
            "position-role-historical-source/tables/historical_fielding_usage.parquet"
        ),
    )
    parser.add_argument(
        "--confirmation-path", type=Path,
        default=Path(
            "reports/generated/position-capacity-source/2025/reports/generated/"
            "position-role-2025-confirmation-source/tables/"
            "position_role_2025_fielding_usage.parquet"
        ),
    )
    parser.add_argument(
        "--generated-root", type=Path, default=Path("reports/generated")
    )
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/prospect-position-value-sensitivity-result.json"),
    )
    return parser.parse_args()


def _group_position_runs(usage: pl.DataFrame) -> dict[str, float]:
    cohort = pl.concat(
        [
            _cohort(usage, year)
            .select("player_id", "destination_group")
            .with_columns(pl.lit(year).alias("origin_year"))
            for year in (2021, 2022)
        ]
    )
    frames = []
    for year in (2021, 2022):
        players = cohort.filter(pl.col("origin_year") == year)
        frames.append(
            usage.filter(
                pl.col("season").is_between(year + 1, year + 2)
                & (pl.col("level_group") == "MLB")
                & pl.col("position_abbreviation").is_in(
                    list(POSITIONAL_RUNS_PER_162)
                )
            )
            .join(players, on="player_id", how="inner", validate="m:1")
            .with_columns(
                pl.when(pl.col("games_started") > 0)
                .then(pl.col("games_started"))
                .otherwise(pl.col("games_played"))
                .alias("position_exposure"),
                pl.col("position_abbreviation")
                .replace_strict(
                    dict(POSITIONAL_RUNS_PER_162), return_dtype=pl.Float64
                )
                .alias("position_runs"),
            )
        )
    return {
        str(row["destination_group"]): float(row["position_runs"])
        for row in (
            pl.concat(frames)
            .group_by("destination_group")
            .agg(
                (
                    (pl.col("position_runs") * pl.col("position_exposure")).sum()
                    / pl.col("position_exposure").sum()
                ).alias("position_runs")
            )
            .iter_rows(named=True)
        )
    }


def main() -> int:
    args = _args()
    dated = args.as_of_date.isoformat()
    transition = json.loads(args.transition_result.read_text(encoding="utf-8"))
    probabilities = transition["outer"]["transition_probabilities"]
    for origin in POSITION_GROUPS:
        if abs(sum(probabilities[origin].values()) - 1.0) > 1e-9:
            raise ValueError(f"transition probability does not sum to one: {origin}")
    usage = pl.concat(
        [pl.read_parquet(args.historical_path), pl.read_parquet(args.confirmation_path)],
        how="vertical_relaxed",
    )
    group_runs = _group_position_runs(usage)
    if set(group_runs) != set(POSITION_GROUPS):
        raise ValueError("position-run training source is missing a destination group")
    war_root = args.generated_root / "phase2-conditional-war-paths" / dated
    war_report = json.loads((war_root / "report.json").read_text(encoding="utf-8"))
    runs_per_win = float(war_report["reference_environment"]["runs_per_win"])
    paths = pl.read_parquet(war_root / "tables/hitter_expected_war_paths.parquet")
    if paths.group_by("player_id").len().filter(pl.col("len") != 6).height:
        raise ValueError("hitter conditional path does not contain six rows per player")
    arrival = pl.read_parquet(
        args.generated_root / "phase2-prospect-arrival" / dated
        / "hitter-arrival-probabilities.parquet"
    ).select("player_id", "role_tier")
    values = pl.read_parquet(
        args.generated_root / "phase2-nested-career-fv" / dated
        / "nested-career-model-fv.parquet"
    ).filter(
        (pl.col("model_player_type") == "hitter")
        & pl.col("ordered_arrival_probability").is_not_null()
    ).join(arrival, on="player_id", how="inner", validate="1:1")
    path_lookup = {
        int(player_key[0]): frame
        for player_key, frame in paths.group_by("player_id", maintain_order=True)
    }
    rows = []
    for row in values.iter_rows(named=True):
        origin = str(row["role_tier"])
        listed_origin = position_group(row["primary_position"])

        def expected_runs(source_group: str) -> float:
            return sum(
                float(probabilities[source_group][destination])
                * group_runs[destination]
                for destination in POSITION_GROUPS
            )

        expected_position_runs = expected_runs(origin)
        listed_expected_position_runs = (
            expected_runs(listed_origin) if listed_origin is not None else None
        )
        player_paths = path_lookup[int(row["player_id"])]
        path_rows = player_paths.iter_rows(named=True)
        adjusted_rates = []
        listed_adjusted_rates = []
        for path in path_rows:
            adjusted_rates.append(
                adjust_war_rate_for_position(
                    float(path["conditional_war_per_600_pa"]),
                    current_position_runs_per_600=float(
                        path["positional_runs_per_600"]
                    ),
                    expected_position_runs_per_600=expected_position_runs,
                    runs_per_win=runs_per_win,
                )
            )
            if listed_expected_position_runs is not None:
                listed_adjusted_rates.append(
                    adjust_war_rate_for_position(
                        float(path["conditional_war_per_600_pa"]),
                        current_position_runs_per_600=float(
                            path["positional_runs_per_600"]
                        ),
                        expected_position_runs_per_600=listed_expected_position_runs,
                        runs_per_win=runs_per_win,
                    )
                )
        expected_war = (
            float(row["three_tier_expected_workload"])
            * sum(adjusted_rates) / len(adjusted_rates) / 600.0
        )
        listed_expected_war = (
            float(row["three_tier_expected_workload"])
            * sum(listed_adjusted_rates) / len(listed_adjusted_rates) / 600.0
            if listed_adjusted_rates
            else None
        )
        granular = model_fv_from_expected_war(expected_war, "hitter")
        listed_granular = (
            model_fv_from_expected_war(listed_expected_war, "hitter")
            if listed_expected_war is not None
            else None
        )
        incumbent = float(row["three_tier_expected_six_year_war"])
        rows.append(
            {
                "player_id": int(row["player_id"]),
                "player_name": row["player_name"],
                "origin_group": origin,
                "listed_origin_group": listed_origin,
                "origin_source_matches": listed_origin == origin,
                "current_primary_position": row["primary_position"],
                "expected_destination_position_runs_per_600": expected_position_runs,
                "incumbent_expected_six_year_war": incumbent,
                "transition_expected_six_year_war": expected_war,
                "war_delta": expected_war - incumbent,
                "incumbent_fv": int(row["three_tier_model_fv_display"]),
                "incumbent_model_fv_granular": float(
                    row["three_tier_model_fv_granular"]
                ),
                "transition_fv": display_fv(granular),
                "transition_model_fv_granular": granular,
                "fv_delta": display_fv(granular)
                - int(row["three_tier_model_fv_display"]),
                "listed_source_transition_expected_six_year_war": listed_expected_war,
                "listed_source_transition_fv": (
                    display_fv(listed_granular) if listed_granular is not None else None
                ),
            }
        )
    result = pl.DataFrame(rows).sort("player_id")
    output = args.generated_root / "prospect-position-value-sensitivity" / dated
    output.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        result, output / "prospect-position-value-sensitivity.parquet",
        table_name="prospect_position_value_sensitivity",
    ).as_record()
    summary = (
        result.group_by("origin_group")
        .agg(
            pl.len().alias("players"),
            pl.col("war_delta").mean().alias("mean_war_delta"),
            pl.col("war_delta").median().alias("median_war_delta"),
            pl.col("fv_delta").abs().gt(0).sum().alias("fv_changed_players"),
        )
        .sort("origin_group")
        .to_dicts()
    )
    top_movers = (
        result.with_columns(pl.col("war_delta").abs().alias("absolute_war_delta"))
        .sort("absolute_war_delta", descending=True)
        .head(20)
        .drop("absolute_war_delta")
        .to_dicts()
    )
    examples = result.filter(pl.col("player_name") == "Josuar Gonzalez").to_dicts()
    external_check = None
    external_path = args.generated_root / "phase2-prospect-source/2026-09-08/fangraphs-top-100.parquet"
    if external_path.exists():
        external = (
            pl.read_parquet(external_path)
            .filter(pl.col("player_id").is_not_null())
            .with_columns(
                pl.col("future_value").map_elements(
                    numeric_fv, return_dtype=pl.Float64
                ).alias("external_fv")
            )
        )
        joined = external.join(result, on="player_id", how="inner")
        external_check = {
            "role": "diagnostic_only_not_model_input",
            "players": joined.height,
            "incumbent_granular_mae": float(
                (
                    joined["incumbent_model_fv_granular"]
                    - joined["external_fv"]
                ).abs().mean()
            ),
            "transition_granular_mae": float(
                (
                    joined["transition_model_fv_granular"]
                    - joined["external_fv"]
                ).abs().mean()
            ),
        }
    report = {
        "report_schema_version": "0.1",
        "as_of_date": dated,
        "status": "private_prospect_position_value_sensitivity_complete",
        "contract": "docs/prospect-position-value-sensitivity-plan.md",
        "players": result.height,
        "runs_per_win": runs_per_win,
        "destination_group_position_runs_per_600": group_runs,
        "by_origin_group": summary,
        "threshold_counts": {
            "incumbent_45_plus": result.filter(pl.col("incumbent_fv") >= 45).height,
            "transition_45_plus": result.filter(pl.col("transition_fv") >= 45).height,
            "incumbent_50_plus": result.filter(pl.col("incumbent_fv") >= 50).height,
            "transition_50_plus": result.filter(pl.col("transition_fv") >= 50).height,
            "listed_source_transition_45_plus": result.filter(
                pl.col("listed_source_transition_fv") >= 45
            ).height,
            "listed_source_transition_50_plus": result.filter(
                pl.col("listed_source_transition_fv") >= 50
            ).height,
        },
        "position_source_comparison": {
            "comparable_players": result.filter(
                pl.col("listed_origin_group").is_not_null()
            ).height,
            "mismatched_players": result.filter(
                pl.col("listed_origin_group").is_not_null()
                & ~pl.col("origin_source_matches")
            ).height,
        },
        "fv_changed_players": result.filter(pl.col("fv_delta") != 0).height,
        "mean_war_delta": float(result.get_column("war_delta").mean()),
        "median_war_delta": float(result.get_column("war_delta").median()),
        "top_absolute_war_movers": top_movers,
        "requested_examples": examples,
        "external_fv_check": external_check,
        "storage": storage,
        "boundaries": {
            "playable_default_changed": False,
            "outside_fv_used": False,
            "skill_or_workload_changed": False,
            "subjective_position_penalty_used": False,
        },
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
