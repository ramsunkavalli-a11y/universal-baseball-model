#!/usr/bin/env python3
"""Create an explainable post-model comparison with the external prospect list."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl


ROOT = Path("reports/generated/current-peak-talent/2026-09-08/tables")
OUTPUT = Path("reports/generated/current-prospect-talent-comparison/2026-09-08")


def _quality_percentiles(frame: pl.DataFrame, *, player_type: str) -> pl.DataFrame:
    eligible = frame.filter(pl.col("prospect_peak_rate_rank").is_not_null())
    directions = (
        {
            "so": False,
            "ubb": True,
            "single": True,
            "double": True,
            "triple": True,
            "hr": True,
        }
        if player_type == "hitter"
        else {"so": True, "ubb": False, "hbp": False, "hr": False}
    )
    denominator = max(eligible.height - 1, 1)
    quality = eligible.select(
        "player_id",
        *(
            (
                1.0
                - (pl.col(f"peak_{component}_rate").rank(
                    method="average", descending=descending
                ) - 1.0)
                / denominator
            ).alias(f"{component}_quality_percentile")
            for component, descending in directions.items()
        ),
    )
    return frame.join(quality, on="player_id", how="left", validate="1:1")


def _logic_summary(row: dict[str, object], *, player_type: str) -> str:
    strength_labels = (
        {
            "so": "avoids strikeouts",
            "ubb": "draws walks",
            "single": "hits for average",
            "double": "drives extra-base hits",
            "triple": "adds triples",
            "hr": "shows home-run power",
        }
        if player_type == "hitter"
        else {
            "so": "misses bats",
            "ubb": "limits walks",
            "hbp": "limits hit batters",
            "hr": "limits home runs",
        }
    )
    risk_labels = (
        {
            "so": "strikes out often",
            "ubb": "rarely walks",
            "single": "low singles rate",
            "double": "low doubles rate",
            "triple": "low triples rate",
            "hr": "limited home-run rate",
        }
        if player_type == "hitter"
        else {
            "so": "misses few bats",
            "ubb": "walks too many hitters",
            "hbp": "hits too many batters",
            "hr": "allows too many home runs",
        }
    )
    strengths = [
        label
        for component, label in strength_labels.items()
        if row.get(f"{component}_quality_percentile") is not None
        and float(row[f"{component}_quality_percentile"]) >= 0.75
    ]
    weaknesses = [
        risk_labels[component]
        for component in strength_labels
        if row.get(f"{component}_quality_percentile") is not None
        and float(row[f"{component}_quality_percentile"]) <= 0.25
    ]
    facts = []
    relative_age = row.get("age_relative_to_level")
    if relative_age is not None and float(relative_age) <= -1.0:
        facts.append("young for level")
    if strengths:
        facts.append("strengths: " + ", ".join(strengths))
    if weaknesses:
        facts.append("risks: " + ", ".join(weaknesses))
    if float(row.get("effective_evidence") or 0.0) < 200.0:
        facts.append("limited performance sample")
    direction = row.get("recent_component_direction_runs")
    if direction is not None and float(direction) >= 2.0:
        facts.append("recent component direction improving")
    elif direction is not None and float(direction) <= -2.0:
        facts.append("recent component direction declining")
    if player_type == "pitcher" and str(row.get("as_of_level_group")) != "AAA":
        facts.append("raw pitch quality unavailable")
    return "; ".join(facts) or "near the middle of the measured component distribution"


def _reason(frame: pl.DataFrame, *, player_type: str) -> pl.DataFrame:
    status = (
        pl.when(pl.col("as_of_level_group") == "MLB")
        .then(pl.lit("promoted_to_mlb_outside_prospect_board"))
        .when(pl.col("age_years") > 23)
        .then(pl.lit("outside_peak_model_age_support"))
        .when(pl.col("ranking_status") != "ranked")
        .then(pl.lit("insufficient_effective_evidence"))
        .when(
            pl.col("external_rank_audit_only").is_not_null()
            & (pl.col("external_rank_audit_only") <= 50)
            & (
                pl.col("prospect_peak_rate_rank").is_null()
                | (pl.col("prospect_peak_rate_rank") > 100)
            )
        )
        .then(pl.lit("external_high_model_low"))
        .when(
            (pl.col("prospect_peak_rate_rank") <= 25)
            & (
                pl.col("external_rank_audit_only").is_null()
                | (pl.col("external_rank_audit_only") > 50)
            )
        )
        .then(pl.lit("model_high_external_low"))
        .otherwise(pl.lit("broad_agreement_or_moderate_gap"))
        .alias("comparison_status")
    )
    if player_type == "hitter":
        return frame.with_columns(
            status,
            (pl.col("peak_so_rate") - pl.col("present_so_rate")).alias(
                "strikeout_rate_change"
            ),
            (pl.col("peak_ubb_rate") - pl.col("present_ubb_rate")).alias(
                "walk_rate_change"
            ),
            (pl.col("peak_hr_rate") - pl.col("present_hr_rate")).alias(
                "home_run_rate_change"
            ),
            pl.lit("position, defense, physical tools and scouting absent").alias(
                "known_missing_evidence"
            ),
        )
    return frame.with_columns(
        status,
        (pl.col("peak_so_rate") - pl.col("present_so_rate")).alias(
            "strikeout_rate_change"
        ),
        (pl.col("peak_ubb_rate") - pl.col("present_ubb_rate")).alias(
            "walk_rate_change"
        ),
        (pl.col("peak_hr_rate") - pl.col("present_hr_rate")).alias(
            "home_run_rate_change"
        ),
        pl.when(pl.col("as_of_level_group") == "AAA")
        .then(pl.lit("AAA pitch tracking exists but is not yet a validated peak input"))
        .otherwise(
            pl.lit("official velocity, movement and pitch type unavailable below AAA")
        )
        .alias("known_missing_evidence"),
    )


def _audit(path: Path, *, player_type: str) -> pl.DataFrame:
    frame = _quality_percentiles(pl.read_parquet(path), player_type=player_type)
    union = frame.filter(
        (pl.col("prospect_peak_rate_rank").is_not_null()
         & (pl.col("prospect_peak_rate_rank") <= 25))
        | (pl.col("external_rank_audit_only").is_not_null()
           & (pl.col("external_rank_audit_only") <= 50))
    )
    explained = _reason(union, player_type=player_type)
    explained = explained.with_columns(
        pl.Series(
            "baseball_logic_summary",
            [
                _logic_summary(row, player_type=player_type)
                for row in explained.to_dicts()
            ],
        )
    )
    return explained.sort(
        ["comparison_status", "external_rank_audit_only", "prospect_peak_rate_rank"],
        nulls_last=True,
    )


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    outputs = {
        "hitters": _audit(ROOT / "current_peak_hitters.parquet", player_type="hitter"),
        "pitchers": _audit(ROOT / "current_peak_pitchers.parquet", player_type="pitcher"),
    }
    summary = {}
    for name, frame in outputs.items():
        frame.write_csv(OUTPUT / f"{name}_model_top25_external_top50.csv")
        summary[name] = {
            "players": frame.height,
            "status_counts": {
                str(row["comparison_status"]): int(row["len"])
                for row in frame.group_by("comparison_status").len().to_dicts()
            },
        }
    report = {
        "report_schema_version": "0.1",
        "status": "post_model_error_audit",
        "external_rank_used_in_model": False,
        "comparison": "union of model top 25 and external top 50",
        **summary,
    }
    (OUTPUT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
