#!/usr/bin/env python3
"""Test one chronology-safe residual adjustment for dominant MiLB pitchers."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import polars as pl

from audit_pitcher_affiliated_regression import COMPONENTS, _components, _fold
from universal_baseball.level_component_translation import score_component_profiles
from universal_baseball.prospect_ranking_audit import build_recent_pitcher_evidence


SOURCE = Path(
    "reports/generated/affiliated-skill-source/tables/"
    "affiliated_pitching_components.parquet"
)
OUTPUT = Path("docs/pitcher-dominance-residual-audit-result.json")
REGRESSION_BF = 800
ALPHAS = (0.0, 0.025, 0.05, 0.075, 0.10, 0.15, 0.20)


def _adjust(
    predictions: pl.DataFrame,
    raw: pl.DataFrame,
    *,
    alpha: float,
) -> pl.DataFrame:
    evidence = raw.with_columns(
        (pl.col("raw_pitcher_so_rate") - pl.col("raw_pitcher_ubb_rate")).alias(
            "raw_k_minus_bb"
        )
    )
    supported = evidence.filter(pl.col("raw_pitcher_bf") >= 300)
    center = float(supported.get_column("raw_k_minus_bb").median())
    q25 = float(supported.get_column("raw_k_minus_bb").quantile(0.25))
    q75 = float(supported.get_column("raw_k_minus_bb").quantile(0.75))
    scale = max(q75 - q25, 0.01)
    joined = predictions.join(
        evidence.select("player_id", "raw_pitcher_bf", "raw_k_minus_bb"),
        on="player_id",
        how="left",
        validate="1:1",
    )
    rows = []
    for row in joined.iter_rows(named=True):
        z = 0.0
        if float(row.get("raw_pitcher_bf") or 0.0) >= 300:
            z = float(np.clip((float(row["raw_k_minus_bb"]) - center) / scale, -3, 3))
        logits = {component: math.log(float(row[f"p_{component}"])) for component in COMPONENTS}
        logits["so"] += alpha * z
        logits["ubb"] -= alpha * z
        peak = max(logits.values())
        denominator = sum(math.exp(value - peak) for value in logits.values())
        rows.append(
            {
                **{column: row[column] for column in predictions.columns},
                **{
                    f"p_{component}": math.exp(logits[component] - peak) / denominator
                    for component in COMPONENTS
                },
                "dominance_z": z,
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None).sort("player_id")


def _fold_scores(source: pl.DataFrame, target_season: int) -> dict[str, object]:
    fold = _fold(source, target_season)
    incumbent = fold["predictions"][REGRESSION_BF]
    raw = build_recent_pitcher_evidence(source, current_season=target_season - 1)
    predictions = {
        alpha: _adjust(incumbent, raw, alpha=alpha) for alpha in ALPHAS
    }
    scores = {
        str(alpha): score_component_profiles(
            prediction,
            fold["target"],
            exposure_column="batters_faced",
            component_columns=COMPONENTS,
        )
        for alpha, prediction in predictions.items()
    }
    return {"scores": scores, "predictions": predictions, "target": fold["target"]}


def main() -> int:
    source = _components(pl.read_parquet(SOURCE))
    development = _fold_scores(source, 2024)
    base = development["scores"]["0.0"]
    eligible = [
        alpha
        for alpha in ALPHAS
        if development["scores"][str(alpha)]["component_log_loss"]
        < base["component_log_loss"]
        and development["scores"][str(alpha)]["component_brier_score"]
        < base["component_brier_score"]
    ]
    selected = min(
        eligible,
        key=lambda alpha: development["scores"][str(alpha)]["component_log_loss"],
    ) if eligible else 0.0
    confirmation = _fold_scores(source, 2025)
    candidate = confirmation["scores"][str(selected)]
    incumbent = confirmation["scores"]["0.0"]
    log_loss_delta = float(candidate["component_log_loss"] - incumbent["component_log_loss"])
    brier_delta = float(candidate["component_brier_score"] - incumbent["component_brier_score"])
    report = {
        "report_schema_version": "0.1",
        "status": "pitcher_dominance_residual_audit_complete",
        "candidate": (
            "For pitchers with at least 300 prior MiLB BF, add one clipped, "
            "population-standardized raw K-BB residual to K and subtract it from BB "
            "in coherent component-logit space."
        ),
        "development_2024": {
            "scores": development["scores"],
            "selected_alpha": selected,
        },
        "confirmation_2025": {
            "incumbent": incumbent,
            "candidate": candidate,
            "candidate_minus_incumbent_log_loss": log_loss_delta,
            "candidate_minus_incumbent_brier": brier_delta,
        },
        "decision": {
            "promoted": selected > 0 and log_loss_delta < 0 and brier_delta < 0,
            "reason": (
                "requires lower component log loss and Brier in untouched 2025"
            ),
        },
        "boundaries": {
            "2026_outcomes_used": False,
            "outside_rank_or_fv_used": False,
            "target_year_team_or_contract_used": False,
            "arrival_probability_changed": False,
            "component_probabilities_remain_coherent": True,
        },
    }
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
