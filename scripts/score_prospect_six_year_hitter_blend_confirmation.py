#!/usr/bin/env python3
"""Score the frozen 2017 six-year hitter blend confirmation."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

try:
    from scripts.audit_prospect_comparable_chronology import (
        _deduplicate,
        _sources,
    )
    from scripts.audit_prospect_six_year_strict import (
        BIAS_MARGIN_WAR,
        _cohort,
    )
    from scripts.materialize_prospect_hitter_comparables import _validation_summary
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from audit_prospect_comparable_chronology import _deduplicate, _sources
    from audit_prospect_six_year_strict import BIAS_MARGIN_WAR, _cohort
    from materialize_prospect_hitter_comparables import _validation_summary
from universal_baseball.prospect_historical_comparables import (
    DEFAULT_COMPARABLES,
    score_hitter_comparables,
)


TARGET_ORIGIN = 2017
REFERENCE_ORIGINS = (2003, 2008)
LOCAL_CONDITIONAL_WEIGHT = 0.40


def _metrics(actual: np.ndarray, prediction: np.ndarray) -> dict[str, float]:
    error = prediction - actual
    return {
        "bias": float(error.mean()),
        "mae": float(np.abs(error).mean()),
        "rmse": float(np.sqrt(np.square(error).mean())),
    }


def blended_expected_war(
    arrival_probability: np.ndarray,
    local_conditional_war: np.ndarray,
    global_conditional_war: float,
) -> np.ndarray:
    return arrival_probability * (
        LOCAL_CONDITIONAL_WEIGHT * local_conditional_war
        + (1.0 - LOCAL_CONDITIONAL_WEIGHT) * global_conditional_war
    )


def main() -> int:
    root = Path("reports/generated")
    runs_per_win = float(
        json.loads(Path("docs/prospect-component-uncertainty-result.json").read_text())[
            "runs_per_win"
        ]
    )
    snapshots, skill, outcomes, debut = _sources(root, "hitter")
    cohorts = {
        origin: _cohort(
            snapshots,
            skill,
            outcomes,
            debut,
            origin=origin,
            player_type="hitter",
            runs_per_win=runs_per_win,
        )
        for origin in (*REFERENCE_ORIGINS, TARGET_ORIGIN)
    }
    target = cohorts[TARGET_ORIGIN]
    reference = _deduplicate(
        [cohorts[origin] for origin in REFERENCE_ORIGINS]
    ).join(target.select("player_id"), on="player_id", how="anti")
    scored = score_hitter_comparables(
        reference, target, comparable_count=DEFAULT_COMPARABLES
    ).join(
        target.select("player_id", "later_component_war", "later_mlb_workload"),
        on="player_id",
        validate="1:1",
    )
    global_conditional = float(
        reference.filter(pl.col("later_mlb_workload") > 0)[
            "later_component_war"
        ].mean()
    )
    actual = scored["later_component_war"].to_numpy()
    blended = blended_expected_war(
        scored["historical_arrival_rate_4y"].to_numpy(),
        scored["historical_conditional_component_war_4y"].to_numpy(),
        global_conditional,
    )
    baseline = np.full(scored.height, float(reference["later_component_war"].mean()))
    blend_scores = _metrics(actual, blended)
    baseline_scores = _metrics(actual, baseline)
    standard = _validation_summary(scored, reference, rate_basis=600.0)
    arrival = standard["arrival_historical_comparables"]
    arrival_base = standard["arrival_population_baseline"]
    conditional = standard["conditional_support_sensitivity"]["10"]
    passed = bool(
        blend_scores["rmse"] < baseline_scores["rmse"]
        and abs(blend_scores["bias"])
        <= abs(baseline_scores["bias"]) + BIAS_MARGIN_WAR
        and arrival["brier"] < arrival_base["brier"]
        and arrival["log_loss"] < arrival_base["log_loss"]
        and conditional["arrivals"] >= 20
        and conditional["historical_comparables_rmse"]
        < conditional["population_baseline_rmse"]
    )
    report = {
        "status": "prospect_six_year_hitter_blend_confirmation_scored",
        "contract": "docs/prospect-six-year-hitter-blend-confirmation-contract.md",
        "target_origin": TARGET_ORIGIN,
        "reference_origins": list(REFERENCE_ORIGINS),
        "reference_players": reference.height,
        "target_players": target.height,
        "local_conditional_weight": LOCAL_CONDITIONAL_WEIGHT,
        "global_conditional_weight": 1.0 - LOCAL_CONDITIONAL_WEIGHT,
        "global_conditional_war": global_conditional,
        "blended_expected_war": blend_scores,
        "population_baseline": baseline_scores,
        "arrival": {"candidate": arrival, "baseline": arrival_base},
        "supported_conditional_rate": conditional,
        "passed": passed,
        "decision": "promote_hitter_six_year_mean" if passed else "withhold_hitter_six_year_mean",
        "outside_fv_used": False,
    }
    Path("docs/prospect-six-year-hitter-blend-confirmation-result.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    Path("docs/prospect-six-year-hitter-blend-confirmation-result.md").write_text(
        "\n".join(
            [
                "# Six-year hitter blend confirmation",
                "",
                f"**Decision:** `{report['decision']}`",
                "",
                f"The untouched 2017 cohort contains {target.height:,} hitters. References are limited to 2003 and 2008, with all outcomes complete before 2017 and self-comparisons removed.",
                "",
                "| Measure | Frozen blend | Population baseline |",
                "|---|---:|---:|",
                f"| Expected-WAR RMSE | {blend_scores['rmse']:.3f} | {baseline_scores['rmse']:.3f} |",
                f"| Expected-WAR bias | {blend_scores['bias']:.3f} | {baseline_scores['bias']:.3f} |",
                f"| Arrival Brier | {arrival['brier']:.3f} | {arrival_base['brier']:.3f} |",
                f"| Arrival log loss | {arrival['log_loss']:.3f} | {arrival_base['log_loss']:.3f} |",
                f"| Supported conditional RMSE | {conditional['historical_comparables_rmse']:.3f} | {conditional['population_baseline_rmse']:.3f} |",
                "",
                "Passing authorizes only the six-year hitter partial-WAR mean. It does not authorize whole-player WAR, dollars or FV.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
