#!/usr/bin/env python3
"""Score the annually linked terminal career state at a cutoff-safe 2021 origin."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from audit_prospect_ordered_transition_path import _data
from audit_prospect_post_arrival_workload import _rows
from universal_baseball.prospect_arrival import fit_arrival_model, predict_arrival
from universal_baseball.prospect_career_state import add_career_state
from universal_baseball.prospect_linked_paths import (
    compile_linked_donor_library,
    simulate_linked_tail_blocks,
)
from universal_baseball.prospect_mlb_progression import (
    PROGRESSION_FEATURE_NAMES,
    fit_progression,
)


DONORS = Path(
    "model_artifacts/prospect-linked-career-state-paths-2009-2025/"
    "annual-state-paths.parquet"
)
OUTPUT_JSON = Path("docs/annually-linked-terminal-state-replay-result.json")
OUTPUT_MD = Path("docs/annually-linked-terminal-state-replay-result.md")
DRAWS = 256
BOOTSTRAPS = 2000
STATE_COLUMNS = ("p_no_mlb", "p_fringe_mlb", "p_meaningful_mlb", "p_established_mlb")


def _four_year(value: pl.Expr) -> pl.Expr:
    return 1.0 - (1.0 - value) ** 2


def _cutoff_coefficients(player_type: str) -> pl.DataFrame:
    rows = _rows(player_type).filter(pl.col("outcome_year") <= 2021)
    output = []
    for origin, feature_set in (
        ("FRINGE_MLB", "age_elapsed_prior_workload"),
        ("MEANINGFUL_MLB", "age_elapsed"),
    ):
        fit = fit_progression(
            rows,
            origin_state=origin,
            feature_set=feature_set,
            regularization_c=1.0,
        )
        output.append(
            {
                "player_type": player_type,
                "origin_state": origin,
                "feature_set": feature_set,
                "term": "intercept",
                "coefficient": float(fit.model.intercept_[0]),
            }
        )
        output.extend(
            {
                "player_type": player_type,
                "origin_state": origin,
                "feature_set": feature_set,
                "term": term,
                "coefficient": float(value),
            }
            for term, value in zip(
                PROGRESSION_FEATURE_NAMES[feature_set], fit.model.coef_[0], strict=True
            )
        )
    return pl.DataFrame(output)


def _destination_probability(player_type: str) -> tuple[float, int]:
    rows = _rows(player_type).filter(
        (pl.col("outcome_year") <= 2021)
        & (pl.col("from_state") == "FRINGE_MLB")
        & (pl.col("advanced") == 1)
    )
    direct = rows.filter(pl.col("to_state") == "ESTABLISHED_MLB").height
    return (direct + 0.5) / (rows.height + 1.0), rows.height


def _baseline(player_type: str) -> pl.DataFrame:
    data = _data(player_type)
    training = data[2018][2]
    evaluation = data[2021][4]
    scored = evaluation
    for name, target in (
        ("arrival", "arrived_within_horizon"),
        ("meaningful", "meaningful_role_within_horizon"),
        ("established", "established_role_within_horizon"),
    ):
        scored = predict_arrival(
            fit_arrival_model(
                training,
                player_type=player_type,
                target_column=target,
                outcome_name=name,
                feature_set="core",
            ),
            scored,
        )
    return scored.with_columns(
        _four_year(pl.col("predicted_two_year_arrival_probability")).alias("_a"),
        _four_year(pl.col("predicted_two_year_meaningful_probability")).alias("_m0"),
        _four_year(pl.col("predicted_two_year_established_probability")).alias("_e0"),
    ).with_columns(
        pl.min_horizontal("_a", "_m0").alias("_m")
    ).with_columns(
        pl.min_horizontal("_m", "_e0").alias("_e")
    ).with_columns(
        (1.0 - pl.col("_a")).alias("p_no_mlb"),
        (pl.col("_a") - pl.col("_m")).alias("p_fringe_mlb"),
        (pl.col("_m") - pl.col("_e")).alias("p_meaningful_mlb"),
        pl.col("_e").alias("p_established_mlb"),
    )


def _losses(frame: pl.DataFrame, prefix: str) -> tuple[np.ndarray, np.ndarray]:
    truth_state = add_career_state(frame)["career_state"].to_list()
    truth_index = np.asarray(
        [{"NO_MLB": 0, "FRINGE_MLB": 1, "MEANINGFUL_MLB": 2, "ESTABLISHED_MLB": 3}[x]
         for x in truth_state]
    )
    probabilities = np.column_stack(
        [frame[f"{prefix}{column}"].to_numpy() for column in STATE_COLUMNS]
    )
    chosen = probabilities[np.arange(frame.height), truth_index]
    truth = np.eye(4)[truth_index]
    return -np.log(np.clip(chosen, 1e-12, 1.0)), np.sum((probabilities - truth) ** 2, axis=1)


def _one(player_type: str, donors: pl.DataFrame) -> tuple[dict[str, object], pl.DataFrame]:
    baseline = _baseline(player_type)
    coefficients = _cutoff_coefficients(player_type)
    destination, destination_support = _destination_probability(player_type)
    eligible_ids = donors.filter(
        (pl.col("player_type") == player_type)
        & (pl.col("path_year") == 1)
        & (pl.col("raw_workload") > 0.0)
        & (pl.col("window_end_year") <= 2021)
    )["path_player_id"]
    library = compile_linked_donor_library(
        donors.filter(pl.col("path_player_id").is_in(eligible_ids.to_list())),
        player_type=player_type,
    )
    rows = []
    for row in baseline.iter_rows(named=True):
        simulation = simulate_linked_tail_blocks(
            np.random.default_rng(20260910 + int(row["player_id"])),
            library,
            coefficients,
            player_type=player_type,
            initial_age_years=float(row["age_years"]),
            direct_established_probability=destination,
            draws=DRAWS,
        )
        counts = np.bincount(simulation.states[:, 3], minlength=4) / DRAWS
        arrival = float(row["_a"])
        candidate = counts * arrival
        candidate[0] += 1.0 - arrival
        rows.append(
            {
                "player_id": int(row["player_id"]),
                **{f"candidate_{column}": float(candidate[index]) for index, column in enumerate(STATE_COLUMNS)},
                "tail_resamples_per_draw": simulation.tail_resamples / DRAWS,
            }
        )
    scored = baseline.join(pl.DataFrame(rows), on="player_id", validate="1:1")
    base_log, base_brier = _losses(scored, "")
    candidate_log, candidate_brier = _losses(scored, "candidate_")
    delta_log = candidate_log - base_log
    delta_brier = candidate_brier - base_brier
    rng = np.random.default_rng(20260920 + (0 if player_type == "hitter" else 1))
    indices = rng.integers(0, scored.height, size=(BOOTSTRAPS, scored.height))
    def summary(delta: np.ndarray) -> dict[str, float]:
        means = delta[indices].mean(axis=1)
        return {
            "difference": float(delta.mean()),
            "ci_low": float(np.quantile(means, 0.025)),
            "ci_high": float(np.quantile(means, 0.975)),
        }
    return {
        "players": scored.height,
        "donor_paths": len(library.player_ids),
        "simulation_draws": DRAWS,
        "destination_training_advances": destination_support,
        "direct_established_probability": destination,
        "baseline_log_loss": float(base_log.mean()),
        "candidate_log_loss": float(candidate_log.mean()),
        "baseline_brier": float(base_brier.mean()),
        "candidate_brier": float(candidate_brier.mean()),
        "candidate_minus_baseline_log_loss": summary(delta_log),
        "candidate_minus_baseline_brier": summary(delta_brier),
        "mean_tail_resamples_per_draw": float(
            scored["tail_resamples_per_draw"].mean()
        ),
    }, scored


def main() -> int:
    donors = pl.read_parquet(DONORS)
    results = {}
    for player_type in ("hitter", "pitcher"):
        results[player_type], _ = _one(player_type, donors)
    passed = all(
        results[player_type][f"candidate_minus_baseline_{metric}"]["ci_high"] < 0
        for player_type in ("hitter", "pitcher")
        for metric in ("log_loss", "brier")
    )
    report = {
        "report_schema_version": "0.1",
        "status": "annually_linked_terminal_state_replay_complete",
        "forecast_origin": 2021,
        "target_years": [2022, 2023, 2024, 2025],
        "current_2026_used": False,
        "candidate_passed": passed,
        "decision": "advance_to_war_replay" if passed else "reject_terminal_state_candidate",
        "production_changed": False,
        **results,
    }
    OUTPUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    OUTPUT_MD.write_text(
        "# Annually linked terminal-state replay\n\n"
        "Status: development replay complete; no current value changed. Negative score differences are better.\n\n"
        "| Type | Players | Log-loss delta [95% interval] | Brier delta [95% interval] |\n"
        "|---|---:|---:|---:|\n"
        + "\n".join(
            f"| {pt.title()} | {results[pt]['players']:,} | "
            f"{results[pt]['candidate_minus_baseline_log_loss']['difference']:+.6f} "
            f"[{results[pt]['candidate_minus_baseline_log_loss']['ci_low']:+.6f}, {results[pt]['candidate_minus_baseline_log_loss']['ci_high']:+.6f}] | "
            f"{results[pt]['candidate_minus_baseline_brier']['difference']:+.6f} "
            f"[{results[pt]['candidate_minus_baseline_brier']['ci_low']:+.6f}, {results[pt]['candidate_minus_baseline_brier']['ci_high']:+.6f}] |"
            for pt in ("hitter", "pitcher")
        )
        + f"\n\nDecision: **{report['decision'].replace('_', ' ')}**. This disclosed cohort cannot promote production.\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
