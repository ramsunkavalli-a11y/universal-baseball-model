#!/usr/bin/env python3
"""Audit whether the deployed translation compresses dominant MiLB pitchers."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from audit_pitcher_affiliated_regression import COMPONENTS, _components, _fold
from universal_baseball.hitter_v2_evaluation import (
    NEUTRAL_WOBA_SCALE,
    NEUTRAL_WOBA_WEIGHTS,
)
from universal_baseball.prospect_ranking_audit import build_recent_pitcher_evidence


SOURCE = Path(
    "reports/generated/affiliated-skill-source/tables/"
    "affiliated_pitching_components.parquet"
)
OUTPUT = Path("docs/pitcher-dominance-tail-audit-result.json")
REGRESSION_BF = 800


def _scored_rows(source: pl.DataFrame, target_season: int) -> pl.DataFrame:
    fold = _fold(source, target_season)
    predictions = fold["predictions"][REGRESSION_BF]
    target = fold["target"].group_by("player_id").agg(
        pl.col("batters_faced").sum(),
        *(pl.col(component).sum() for component in COMPONENTS),
    ).filter(pl.col("batters_faced") > 0)
    raw = build_recent_pitcher_evidence(source, current_season=target_season - 1)
    prior = fold["prior"]
    known = (
        prior["ubb"] * NEUTRAL_WOBA_WEIGHTS["UBB"]
        + prior["hbp"] * NEUTRAL_WOBA_WEIGHTS["HBP"]
        + prior["hr"] * NEUTRAL_WOBA_WEIGHTS["HR"]
    )
    weights = {
        "so": 0.0,
        "ubb": NEUTRAL_WOBA_WEIGHTS["UBB"],
        "hbp": NEUTRAL_WOBA_WEIGHTS["HBP"],
        "hr": NEUTRAL_WOBA_WEIGHTS["HR"],
        "other": (0.3188 - known) / prior["other"],
    }
    return (
        predictions.join(raw, on="player_id", how="left", validate="1:1")
        .join(target, on="player_id", how="inner", validate="1:1")
        .with_columns(
            (
                -(pl.sum_horizontal(
                    *(pl.col(f"p_{key}") * value for key, value in weights.items())
                ) - 0.3188)
                * 800.0
                / NEUTRAL_WOBA_SCALE
            ).alias("predicted_raa_per_800"),
            (
                -(pl.sum_horizontal(
                    *(
                        pl.col(key) / pl.col("batters_faced") * value
                        for key, value in weights.items()
                    )
                ) - 0.3188)
                * 800.0
                / NEUTRAL_WOBA_SCALE
            ).alias("observed_raa_per_800"),
            (pl.col("raw_pitcher_so_rate") - pl.col("raw_pitcher_ubb_rate"))
            .alias("raw_k_minus_bb"),
        )
    )


def _summary(rows: pl.DataFrame) -> dict[str, object]:
    if rows.is_empty():
        return {"players": 0, "target_bf": 0}
    return {
        "players": rows.height,
        "target_bf": int(rows.get_column("batters_faced").sum()),
        "raw_bf_mean": float(rows.get_column("raw_pitcher_bf").mean()),
        "raw_k_rate_mean": float(rows.get_column("raw_pitcher_so_rate").mean()),
        "raw_bb_rate_mean": float(rows.get_column("raw_pitcher_ubb_rate").mean()),
        "raw_hr_rate_mean": float(rows.get_column("raw_pitcher_hr_rate").mean()),
        "projected_k_rate_mean": float(rows.get_column("p_so").mean()),
        "projected_bb_rate_mean": float(rows.get_column("p_ubb").mean()),
        "projected_hr_rate_mean": float(rows.get_column("p_hr").mean()),
        "bf_weighted_predicted_raa_per_800": float(
            (rows.get_column("predicted_raa_per_800")
             * rows.get_column("batters_faced")).sum()
            / rows.get_column("batters_faced").sum()
        ),
        "bf_weighted_observed_raa_per_800": float(
            (rows.get_column("observed_raa_per_800")
             * rows.get_column("batters_faced")).sum()
            / rows.get_column("batters_faced").sum()
        ),
    }


def _audit_fold(source: pl.DataFrame, target_season: int) -> dict[str, object]:
    rows = _scored_rows(source, target_season)
    sufficient = rows.filter(pl.col("raw_pitcher_bf") >= 300)
    kbb_cut = float(sufficient.get_column("raw_k_minus_bb").quantile(0.75))
    high_kbb = sufficient.filter(pl.col("raw_k_minus_bb") >= kbb_cut)
    dominance = sufficient.filter(
        (pl.col("raw_k_minus_bb") >= 0.20)
        & (pl.col("raw_pitcher_hr_rate") <= 0.025)
    )
    return {
        "target_season": target_season,
        "all_arrivals": _summary(rows),
        "sufficient_history": _summary(sufficient),
        "top_quartile_k_minus_bb": {
            "input_cutoff": kbb_cut,
            **_summary(high_kbb),
        },
        "fixed_dominance_group": {
            "definition": "raw BF >= 300, K-BB >= 20 points, HR/BF <= 2.5%",
            **_summary(dominance),
        },
    }


def main() -> int:
    source = _components(pl.read_parquet(SOURCE))
    folds = [_audit_fold(source, season) for season in (2024, 2025)]
    report = {
        "report_schema_version": "0.1",
        "status": "diagnostic_only_no_model_change",
        "question": (
            "Does the deployed level translation plus 800-BF prior systematically "
            "understate later MLB run prevention for dominant MiLB pitchers?"
        ),
        "folds": folds,
        "boundaries": {
            "skill_conditioned_on_positive_target_mlb_bf": True,
            "arrival_probability_evaluated_here": False,
            "subgroups_defined_only_from_prior_milb_results": True,
            "outside_rank_or_fv_used": False,
            "2026_outcomes_used": False,
            "promotion_authorized": False,
        },
    }
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
