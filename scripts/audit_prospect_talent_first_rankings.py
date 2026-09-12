#!/usr/bin/env python3
"""Rank pre-MLB players by regressed conditional talent, excluding opportunity."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_v2_evaluation import (
    NEUTRAL_WOBA_SCALE,
    NEUTRAL_WOBA_WEIGHTS,
)
from universal_baseball.hitter_v2_model import marcel_age_factor
from universal_baseball.prospect_ranking_audit import build_recent_pitcher_evidence
from universal_baseball.storage import write_canonical_parquet


SUPPORTED_RELIABILITY = 0.20


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--generated-root", type=Path, default=Path("reports/generated"))
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/prospect-talent-first-audit-result.json"),
    )
    return parser.parse_args()


def _hitter_rates(root: Path, dated: str, runs_per_win: float) -> pl.DataFrame:
    paths = pl.read_parquet(
        root / "phase2-conditional-war-paths" / dated / "tables"
        / "hitter_expected_war_paths.parquet"
    )
    first_season = int(paths.get_column("season").min())
    rates = paths.filter(pl.col("season") == first_season)

    positive_columns = (
        "predicted_ubb_rate",
        "predicted_hbp_rate",
        "predicted_single_rate",
        "predicted_double_rate",
        "predicted_triple_rate",
        "predicted_hr_rate",
    )
    weights = {
        "predicted_ubb_rate": NEUTRAL_WOBA_WEIGHTS["UBB"],
        "predicted_hbp_rate": NEUTRAL_WOBA_WEIGHTS["HBP"],
        "predicted_single_rate": NEUTRAL_WOBA_WEIGHTS["1B"],
        "predicted_double_rate": NEUTRAL_WOBA_WEIGHTS["2B"],
        "predicted_triple_rate": NEUTRAL_WOBA_WEIGHTS["3B"],
        "predicted_hr_rate": NEUTRAL_WOBA_WEIGHTS["HR"],
    }
    age_factor = pl.col("target_age").map_elements(
        marcel_age_factor, return_dtype=pl.Float64
    )
    neutral_denominator = (
        sum(pl.col(column) / age_factor for column in positive_columns)
        + pl.col("predicted_other_rate")
    )
    aged_woba = sum(pl.col(column) * weights[column] for column in positive_columns)
    neutral_woba = sum(
        (pl.col(column) / age_factor) / neutral_denominator * weights[column]
        for column in positive_columns
    )
    rates = (
        rates.with_columns(
            (
                (aged_woba - neutral_woba) * 600.0 / NEUTRAL_WOBA_SCALE
            ).alias("future_age_runs_per_600")
        )
        .with_columns(
            (
                pl.col("batting_runs_per_600")
                - pl.col("future_age_runs_per_600")
            ).alias("current_batting_runs_per_600"),
            pl.col("positional_runs_per_600").alias("incumbent_position_runs"),
            pl.col("weighted_history_pa").alias("weighted_skill_workload"),
            pl.col("reliability").alias("skill_reliability"),
            pl.col("evidence_tier").alias("skill_evidence_tier"),
        )
        .with_columns(
            (
                pl.col("current_batting_runs_per_600")
                + pl.col("baserunning_runs_per_600").fill_null(0.0)
                + pl.col("defense_runs_per_600").fill_null(0.0)
            ).alias("current_skill_runs")
        )
    )
    position = pl.read_parquet(
        root / "prospect-shortstop-sensitivity" / dated
        / "prospect-shortstop-sensitivity.parquet"
    ).select(
        "player_id",
        "dominant_current_position",
        "predicted_position_runs_per_600",
        "position_evidence_available",
    )
    return (
        rates.join(position, on="player_id", how="left", validate="1:1")
        .with_columns(
            pl.when(pl.col("position_evidence_available").fill_null(False))
            .then(pl.col("predicted_position_runs_per_600"))
            .otherwise(pl.col("incumbent_position_runs"))
            .alias("talent_position_runs")
        )
        .with_columns(
            (pl.col("current_skill_runs") / runs_per_win).alias("talent_war_rate"),
            pl.lit("current skill WAR above average per 600 PA").alias("talent_rate_unit"),
            pl.lit("hitter").alias("rate_player_type"),
        )
    )


def _pitcher_rates(root: Path, dated: str, runs_per_win: float) -> pl.DataFrame:
    paths = pl.read_parquet(
        root / "phase2-conditional-war-paths" / dated / "tables"
        / "pitcher_expected_war_paths.parquet"
    )
    first_season = int(paths.get_column("season").min())
    return paths.filter(pl.col("season") == first_season).with_columns(
        pl.col("pitching_runs_above_average_per_800").alias("current_skill_runs"),
        (pl.col("pitching_runs_above_average_per_800") / runs_per_win).alias(
            "talent_war_rate"
        ),
        pl.col("weighted_history_bf").alias("weighted_skill_workload"),
        pl.col("reliability").alias("skill_reliability"),
        pl.col("evidence_tier").alias("skill_evidence_tier"),
        pl.lit("current pitching runs above average per 800 BF").alias("talent_rate_unit"),
        pl.lit("pitcher").alias("rate_player_type"),
    )


def _flags(row: dict[str, object]) -> list[str]:
    flags = []
    if float(row.get("skill_reliability") or 0.0) < SUPPORTED_RELIABILITY:
        flags.append("thin_evidence")
    evidence = str(row.get("skill_evidence_tier") or "").lower()
    if any(value in evidence for value in ("fallback", "population", "missing")):
        flags.append("fallback_evidence")
    if row.get("model_player_type") == "hitter":
        if float(row.get("current_batting_runs_per_600") or 0.0) < 0.0:
            flags.append("below_average_batting")
        position = float(row.get("talent_position_runs") or 0.0)
        if position >= 7.5:
            flags.append("premium_position_material")
    elif float(row.get("pitching_runs_above_average_per_800") or 0.0) < 0.0:
        flags.append("below_average_pitching_raa")
    return flags


def main() -> int:
    args = _args()
    dated = args.as_of_date.isoformat()
    root = args.generated_root
    war_report = json.loads(
        (root / "phase2-conditional-war-paths" / dated / "report.json").read_text(
            encoding="utf-8"
        )
    )
    runs_per_win = float(war_report["reference_environment"]["runs_per_win"])
    rates = pl.concat(
        [_hitter_rates(root, dated, runs_per_win), _pitcher_rates(root, dated, runs_per_win)],
        how="diagonal_relaxed",
    )
    nested = pl.read_parquet(
        root / "phase2-nested-career-fv" / dated / "nested-career-model-fv.parquet"
    ).filter(
        pl.col("player_name").is_not_null()
        & pl.col("ordered_arrival_probability").is_not_null()
    ).select(
        "player_id", "player_name", "organization_id", "model_player_type",
        "primary_position",
    )
    talent = nested.join(
        rates,
        left_on=["player_id", "model_player_type"],
        right_on=["player_id", "rate_player_type"],
        how="inner",
        validate="1:1",
    )
    raw_pitcher = build_recent_pitcher_evidence(
        pl.read_parquet(
            root / "affiliated-skill-source" / "tables"
            / "affiliated_pitching_components.parquet"
        ),
        current_season=args.as_of_date.year,
    )
    source = pl.read_parquet(
        root / "phase2-prospect-source" / dated / "fangraphs-top-100.parquet"
    ).select(
        "player_id",
        pl.col("rank").alias("source_rank"),
        pl.col("future_value").alias("source_fv"),
    )
    talent = (
        talent.join(raw_pitcher, on="player_id", how="left", validate="m:1")
        .join(source, on="player_id", how="left", validate="1:1")
        .with_columns(
            pl.struct(pl.all()).map_elements(_flags, return_dtype=pl.List(pl.String)).alias(
                "review_flags"
            ),
            pl.when(pl.col("skill_reliability") >= SUPPORTED_RELIABILITY)
            .then(pl.lit("supported"))
            .otherwise(pl.lit("unresolved_thin_evidence"))
            .alias("ranking_status"),
        )
    )
    supported = (
        talent.filter(pl.col("ranking_status") == "supported")
        .sort(
            ["talent_war_rate", "skill_reliability", "player_id"],
            descending=[True, True, False],
            nulls_last=True,
        )
        .with_row_index("talent_rank", offset=1)
    )
    unresolved = (
        talent.filter(pl.col("ranking_status") != "supported")
        .sort(
            ["skill_reliability", "talent_war_rate", "player_id"],
            descending=[True, True, False],
            nulls_last=True,
        )
    )
    top = supported.head(50)
    control = pl.read_parquet(
        root / "league-control" / dated / "league-control-snapshot.parquet"
    ).select("player_id", "mlb_debut_date")
    source_top = (
        source.filter((pl.col("source_rank") <= 50) & pl.col("player_id").is_not_null())
        .join(control, on="player_id", how="left", validate="1:1")
        .filter(pl.col("mlb_debut_date").is_null())
        .join(
            supported.select("player_id", "talent_rank"),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .join(
            talent.drop("talent_rank", strict=False),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .sort("source_rank")
    )
    output = root / "prospect-talent-first-audit" / dated
    output.mkdir(parents=True, exist_ok=True)
    top.with_columns(pl.col("review_flags").list.join("|")).write_csv(
        output / "talent-top-50.csv"
    )
    source_top.with_columns(pl.col("review_flags").list.join("|")).write_csv(
        output / "source-top-50-talent-check.csv"
    )
    unresolved.head(100).with_columns(
        pl.col("review_flags").list.join("|")
    ).write_csv(output / "unresolved-thin-evidence.csv")
    storage = write_canonical_parquet(
        top,
        output / "talent-top-50.parquet",
        table_name="prospect_talent_first_top_50",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "as_of_date": dated,
        "status": "prospect_talent_first_diagnostic_complete",
        "contract": "docs/prospect-talent-first-audit-plan.md",
        "eligible_players": talent.height,
        "supported_players": supported.height,
        "unresolved_thin_evidence_players": unresolved.height,
        "supported_reliability_floor": SUPPORTED_RELIABILITY,
        "top_50_source_overlap": top.filter(pl.col("source_rank") <= 50).height,
        "top_50_by_player_type": top.group_by("model_player_type").len().sort(
            "model_player_type"
        ).to_dicts(),
        "top_50_flag_counts": (
            top.explode("review_flags")
            .filter(pl.col("review_flags").is_not_null())
            .group_by("review_flags")
            .len()
            .sort("len", descending=True)
            .to_dicts()
        ),
        "source_top_50_talent_rank_summary": {
            "still_eligible": source_top.height,
            "supported_count": source_top.filter(pl.col("talent_rank").is_not_null()).height,
            "unresolved_count": source_top.filter(pl.col("talent_rank").is_null()).height,
            "median_supported_talent_rank": (
                float(source_top["talent_rank"].median())
                if source_top.get_column("talent_rank").drop_nulls().len()
                else None
            ),
        },
        "boundaries": {
            "arrival_probability_used": False,
            "expected_workload_used": False,
            "contract_control_or_dollars_used": False,
            "outside_rank_used_as_model_input": False,
            "position_sensitivity_is_private": True,
            "future_aging_used": False,
            "position_or_replacement_used_in_talent": False,
            "thin_evidence_ranked": False,
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
