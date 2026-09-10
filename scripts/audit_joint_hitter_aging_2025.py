#!/usr/bin/env python3
"""Score Marcel hitter aging on the zero-inclusive 2025 production target."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.historical_war_scoring import score_hitter_neutral_war
from universal_baseball.hitter_v2_evaluation import NEUTRAL_WOBA_SCALE, NEUTRAL_WOBA_WEIGHTS
from universal_baseball.hitter_v2_model import marcel_age_factor


EVENTS = ("ubb", "hbp", "single", "double", "triple", "hr", "other")
PROJECTION_ROOT = Path("reports/generated/historical-projection-paths/2025-03-27")
SKILL_ROOT = Path("reports/generated/free-agent-historical-skill-source/2025-12-31")
OUTPUT = Path("docs/joint-hitter-aging-2025-result.json")


def _counterfactual_no_aging(
    projections: pl.DataFrame, reference: pl.DataFrame, *, runs_per_win: float
) -> pl.DataFrame:
    total_pa = float(reference.get_column("batting_plate_appearances").sum())
    prior = {
        "ubb": float(reference.get_column("batting_base_on_balls").sum()
                     - reference.get_column("batting_intentional_walks").sum()) / total_pa,
        "hbp": float(reference.get_column("batting_hit_by_pitch").sum()) / total_pa,
        "single": float(
            reference.get_column("batting_hits").sum()
            - reference.get_column("batting_doubles").sum()
            - reference.get_column("batting_triples").sum()
            - reference.get_column("batting_home_runs").sum()
        ) / total_pa,
        "double": float(reference.get_column("batting_doubles").sum()) / total_pa,
        "triple": float(reference.get_column("batting_triples").sum()) / total_pa,
        "hr": float(reference.get_column("batting_home_runs").sum()) / total_pa,
    }
    prior["other"] = 1.0 - sum(prior.values())
    weights = {
        "ubb": NEUTRAL_WOBA_WEIGHTS["UBB"], "hbp": NEUTRAL_WOBA_WEIGHTS["HBP"],
        "single": NEUTRAL_WOBA_WEIGHTS["1B"], "double": NEUTRAL_WOBA_WEIGHTS["2B"],
        "triple": NEUTRAL_WOBA_WEIGHTS["3B"], "hr": NEUTRAL_WOBA_WEIGHTS["HR"],
        "other": 0.0,
    }
    reference_woba = sum(prior[event] * weights[event] for event in EVENTS)
    rows = []
    for row in projections.iter_rows(named=True):
        aged = {event: float(row[f"predicted_{event}_rate"]) for event in EVENTS}
        factor = marcel_age_factor(row["target_age"])
        raw = {
            event: aged[event] / factor if event != "other" else aged[event]
            for event in EVENTS
        }
        total = sum(raw.values())
        base = {event: raw[event] / total for event in EVENTS}
        woba = sum(base[event] * weights[event] for event in EVENTS)
        batting_runs = (woba - reference_woba) * 600.0 / NEUTRAL_WOBA_SCALE
        per_600 = (
            batting_runs + float(row["baserunning_runs_per_600"])
            + float(row["defense_runs_per_600"])
            + float(row["positional_runs_per_600"])
            + float(row["replacement_runs_per_600"])
        ) / runs_per_win
        rows.append({
            **row,
            **{f"predicted_{event}_rate": base[event] for event in EVENTS},
            "batting_runs_per_600": batting_runs,
            "conditional_war_per_600_pa": per_600,
            "expected_war": float(row["expected_mlb_pa"]) / 600.0 * per_600,
        })
    return pl.DataFrame(rows, schema=projections.schema).sort("player_id")


def _bootstrap(candidate: pl.DataFrame, incumbent: pl.DataFrame) -> dict[str, object]:
    values = candidate.select(
        "player_id", pl.col("war_error").alias("candidate")
    ).join(
        incumbent.select("player_id", pl.col("war_error").alias("incumbent")),
        on="player_id", validate="1:1",
    ).select(
        (pl.col("candidate").abs() - pl.col("incumbent").abs()).alias("mae"),
        (pl.col("candidate") ** 2 - pl.col("incumbent") ** 2).alias("mse"),
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
        for column, name in enumerate(("mae_delta_no_aging_minus_marcel", "mse_delta_no_aging_minus_marcel"))
    }


def main() -> int:
    projections = pl.read_parquet(
        PROJECTION_ROOT / "tables/hitter-expected-war-paths.parquet"
    ).filter(pl.col("season") == 2025)
    source = pl.read_parquet(SKILL_ROOT / "tables/mlb_hitting_components.parquet")
    outcomes = source.filter(pl.col("season") == 2025)
    reference = source.filter(pl.col("season") == 2024)
    skill_report = json.loads((SKILL_ROOT / "report.json").read_text(encoding="utf-8"))
    runs_per_win = float(skill_report["reference_environment"]["runs_per_win"])
    no_aging = _counterfactual_no_aging(projections, reference, runs_per_win=runs_per_win)
    marcel_scores, marcel_metrics = score_hitter_neutral_war(
        projections, outcomes, reference, runs_per_win=runs_per_win
    )
    no_aging_scores, no_aging_metrics = score_hitter_neutral_war(
        no_aging, outcomes, reference, runs_per_win=runs_per_win
    )
    report = {
        "report_schema_version": "0.1",
        "status": "joint_zero_inclusive_aging_replay_complete",
        "target_season": 2025,
        "population": "all 3,891 hitter rows in the frozen March 27 projection",
        "marcel_aging": marcel_metrics,
        "no_aging": no_aging_metrics,
        "no_aging_minus_marcel": {
            key: float(no_aging_metrics[key]) - float(marcel_metrics[key])
            for key in ("predicted_total_war", "war_mae", "war_rmse", "model_component_log_loss")
        },
        "player_bootstrap": _bootstrap(no_aging_scores, marcel_scores),
        "method": "invert only the Marcel age multiplier while keeping frozen opportunity, position, replacement and run environment identical",
        "nonreturners_retained": True,
        "outside_fv_used": False,
        "production_changed": False,
    }
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
