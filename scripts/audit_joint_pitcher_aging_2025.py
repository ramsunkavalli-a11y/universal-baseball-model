#!/usr/bin/env python3
"""Score Tango pitcher aging on the zero-inclusive 2025 production target."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.conditional_war_rates import apply_tango_pitcher_aging
from universal_baseball.historical_war_scoring import score_pitcher_neutral_war
from universal_baseball.hitter_v2_evaluation import NEUTRAL_WOBA_SCALE, NEUTRAL_WOBA_WEIGHTS


EVENTS = ("so", "ubb", "hbp", "hr", "other")
PROJECTION_ROOT = Path("reports/generated/historical-projection-paths/2025-03-27")
SKILL_ROOT = Path("reports/generated/free-agent-historical-skill-source/2025-12-31")
OUTPUT = Path("docs/joint-pitcher-aging-2025-result.json")


def _counterfactual_no_aging(
    projections: pl.DataFrame, reference: pl.DataFrame, *, runs_per_win: float
) -> pl.DataFrame:
    total_bf = float(reference.get_column("pitching_batters_faced").sum())
    prior = {
        "ubb": float(reference.get_column("pitching_base_on_balls").sum()
                     - reference.get_column("pitching_intentional_walks").sum()) / total_bf,
        "hbp": float(reference.get_column("pitching_hit_batsmen").sum()) / total_bf,
        "hr": float(reference.get_column("pitching_home_runs").sum()) / total_bf,
    }
    prior["so"] = float(reference.get_column("pitching_strike_outs").sum()) / total_bf
    prior["other"] = 1.0 - sum(prior.values())
    known = (
        prior["ubb"] * NEUTRAL_WOBA_WEIGHTS["UBB"]
        + prior["hbp"] * NEUTRAL_WOBA_WEIGHTS["HBP"]
        + prior["hr"] * NEUTRAL_WOBA_WEIGHTS["HR"]
    )
    weights = {
        "so": 0.0, "ubb": NEUTRAL_WOBA_WEIGHTS["UBB"],
        "hbp": NEUTRAL_WOBA_WEIGHTS["HBP"], "hr": NEUTRAL_WOBA_WEIGHTS["HR"],
        "other": (0.3188 - known) / prior["other"],
    }
    rows = []
    for row in projections.iter_rows(named=True):
        aged = {event: float(row[f"predicted_{event}_rate"]) for event in EVENTS}
        age = row["target_age"]
        base = aged if age is None else apply_tango_pitcher_aging(
            aged, current_age=float(age), target_age=float(age) - 1.0
        )
        woba = sum(base[event] * weights[event] for event in EVENTS)
        raa = -(woba - 0.3188) * 800.0 / NEUTRAL_WOBA_SCALE
        replacement = float(row["replacement_runs_per_800"])
        expected_war = float(row["expected_mlb_bf"]) / 800.0 * (
            raa + replacement
        ) / runs_per_win
        rows.append({
            **row,
            **{f"predicted_{event}_rate": base[event] for event in EVENTS},
            "pitching_runs_above_average_per_800": raa,
            "conditional_war_per_800_bf": (raa + replacement) / runs_per_win,
            "expected_war": expected_war,
            "aging_source": "no_aging_counterfactual",
        })
    return pl.DataFrame(rows, schema=projections.schema).sort("player_id")


def _bootstrap(candidate: pl.DataFrame, incumbent: pl.DataFrame) -> dict[str, object]:
    joined = candidate.select(
        "player_id", pl.col("war_error").alias("candidate_error")
    ).join(
        incumbent.select("player_id", pl.col("war_error").alias("incumbent_error")),
        on="player_id", validate="1:1",
    )
    values = joined.select(
        (pl.col("candidate_error").abs() - pl.col("incumbent_error").abs()).alias("mae"),
        (pl.col("candidate_error") ** 2 - pl.col("incumbent_error") ** 2).alias("mse"),
    ).to_numpy()
    rng = np.random.default_rng(20250910)
    samples = np.empty((2000, 2))
    for index in range(len(samples)):
        samples[index] = values[rng.integers(0, len(values), len(values))].mean(axis=0)
    return {
        name: {
            "point": float(values[:, column].mean()),
            "lower_95": float(np.quantile(samples[:, column], 0.025)),
            "upper_95": float(np.quantile(samples[:, column], 0.975)),
        }
        for column, name in enumerate(("mae_delta_no_aging_minus_tango", "mse_delta_no_aging_minus_tango"))
    }


def main() -> int:
    projections = pl.read_parquet(
        PROJECTION_ROOT / "tables/pitcher-expected-war-paths.parquet"
    ).filter(pl.col("season") == 2025)
    source = pl.read_parquet(SKILL_ROOT / "tables/mlb_pitching_components.parquet")
    outcomes = source.filter(pl.col("season") == 2025)
    reference = source.filter(pl.col("season") == 2024)
    skill_report = json.loads((SKILL_ROOT / "report.json").read_text(encoding="utf-8"))
    runs_per_win = float(skill_report["reference_environment"]["runs_per_win"])
    no_aging = _counterfactual_no_aging(projections, reference, runs_per_win=runs_per_win)
    tango_scores, tango_metrics = score_pitcher_neutral_war(
        projections, outcomes, reference, runs_per_win=runs_per_win
    )
    no_aging_scores, no_aging_metrics = score_pitcher_neutral_war(
        no_aging, outcomes, reference, runs_per_win=runs_per_win
    )
    report = {
        "report_schema_version": "0.1",
        "status": "joint_zero_inclusive_aging_replay_complete",
        "target_season": 2025,
        "population": "all 5,090 pitcher rows in the frozen March 27 projection",
        "tango_aging": tango_metrics,
        "no_aging": no_aging_metrics,
        "no_aging_minus_tango": {
            key: float(no_aging_metrics[key]) - float(tango_metrics[key])
            for key in (
                "predicted_total_war", "war_mae", "war_rmse",
                "model_component_log_loss",
            )
        },
        "player_bootstrap": _bootstrap(no_aging_scores, tango_scores),
        "method": "invert the one-year Tango rate adjustment while keeping the frozen opportunity, role, replacement and run environment identical",
        "nonreturners_retained": True,
        "outside_fv_used": False,
        "production_changed": False,
    }
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
