#!/usr/bin/env python3
"""Test whether prior MiLB RE24 runner skill improves the hitter value stack."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import polars as pl

from universal_baseball.historical_runner_arm import (
    evaluate_effect_projection,
    project_effects,
)
from universal_baseball.hitter_target_architecture import (
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.runner_value_bridge import (
    build_runner_bridge_candidates,
    candidate_columns,
    select_from_prior_targets,
)
from universal_baseball.storage import write_canonical_parquet


BASE_PATH = Path(
    "reports/generated/hitter-value-components-chronological-v2/"
    "chronological-predictions.parquet"
)
RUNNER_EFFECTS_PATH = Path(
    "reports/generated/pbp-runner-re24-v1/runner-season-effects.parquet"
)
REFERENCE_PATH = Path("docs/player-value-v1-baserunning-run-conversion-2024.json")
OUTPUT_ROOT = Path("reports/generated/milb-runner-hitter-value-bridge-v1")
REGRESSION_GRID = (25.0, 50.0, 100.0, 200.0, 400.0, 800.0, 1200.0)
TARGET_SEASONS = (2022, 2023, 2024, 2025)
RUNS_PER_WIN = 10.0


def _select_effect_regression(
    effects: pl.DataFrame, target_season: int
) -> tuple[float, int, float]:
    choices: list[tuple[float, float, int]] = []
    for regression in REGRESSION_GRID:
        frames = []
        for year in sorted(effects["season"].unique().to_list()):
            if int(year) >= target_season:
                continue
            paired, _ = evaluate_effect_projection(
                effects,
                target_season=int(year),
                regression_opportunities=regression,
                minimum_target_opportunities=8,
            )
            if not paired.is_empty():
                frames.append(paired)
        if not frames:
            continue
        pooled = pl.concat(frames)
        choices.append(
            (
                float(pooled["candidate_error"].pow(2).sum()),
                regression,
                pooled.height,
            )
        )
    if not choices:
        raise ValueError(f"no prior MiLB runner folds for {target_season}")
    sse, regression, rows = min(choices)
    return regression, rows, sse


def _runner_projections(effects: pl.DataFrame) -> tuple[pl.DataFrame, list[dict[str, float | int]]]:
    frames = []
    decisions: list[dict[str, float | int]] = []
    for target_season in TARGET_SEASONS:
        regression, prior_rows, prior_sse = _select_effect_regression(
            effects, target_season
        )
        frames.append(
            project_effects(
                effects,
                target_season=target_season,
                regression_opportunities=regression,
            )
        )
        decisions.append(
            {
                "target_season": target_season,
                "selected_regression_opportunities": regression,
                "prior_player_seasons": prior_rows,
                "prior_sse": prior_sse,
            }
        )
    return pl.concat(frames), decisions


def main() -> int:
    base = pl.read_parquet(BASE_PATH).with_columns(
        (pl.col("origin_year") + 1).alias("target_season")
    )
    effects = pl.read_parquet(RUNNER_EFFECTS_PATH)
    reference = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))["reference"]
    milb, regression_decisions = _runner_projections(effects)
    candidates = build_runner_bridge_candidates(
        base,
        milb,
        advancement_opportunities_per_pa=float(
            reference["advancement_opportunities_per_pa"]
        ),
        runs_per_win=RUNS_PER_WIN,
    )
    candidate_names = candidate_columns()
    selected_frames = []
    selection = []
    for target_season in TARGET_SEASONS:
        selected, prior_rows, prior_sse = select_from_prior_targets(
            candidates,
            target_season=target_season,
            candidates=candidate_names,
        )
        fold = candidates.filter(pl.col("target_season") == target_season).with_columns(
            pl.col(selected).alias("prediction_bridge_advancement_war"),
            pl.lit(selected).alias("selected_bridge_candidate"),
        ).with_columns(
            (
                pl.col("prediction_selected_partial_war")
                - pl.col("prediction_advancement_war")
                + pl.col("prediction_bridge_advancement_war")
            ).alias("prediction_bridge_partial_war")
        )
        selected_frames.append(fold)
        selection.append(
            {
                "target_season": target_season,
                "selected_candidate": selected,
                "prior_mlb_target_rows": prior_rows,
                "prior_component_sse": prior_sse,
            }
        )
    frame = pl.concat(selected_frames).sort("target_season", "player_id")
    actual_total = frame["actual_partial_war"].to_numpy()
    baseline_total = frame["prediction_selected_partial_war"].to_numpy()
    bridge_total = frame["prediction_bridge_partial_war"].to_numpy()
    actual_component = frame["later_advancement_war"].to_numpy()
    baseline_component = frame["prediction_advancement_war"].to_numpy()
    bridge_component = frame["prediction_bridge_advancement_war"].to_numpy()
    player_ids = frame["player_id"].to_numpy()

    by_season = []
    for target_season in TARGET_SEASONS:
        fold = frame.filter(pl.col("target_season") == target_season)
        by_season.append(
            {
                "target_season": target_season,
                "rows": fold.height,
                "milb_coverage": int(
                    fold["prediction_milb_advancement_war"].is_not_null().sum()
                ),
                "baseline_total": regression_metrics(
                    fold["actual_partial_war"].to_numpy(),
                    fold["prediction_selected_partial_war"].to_numpy(),
                ),
                "bridge_total": regression_metrics(
                    fold["actual_partial_war"].to_numpy(),
                    fold["prediction_bridge_partial_war"].to_numpy(),
                ),
            }
        )

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        frame,
        OUTPUT_ROOT / "predictions.parquet",
        table_name="milb_runner_hitter_value_bridge_v1_predictions",
    )
    report = {
        "schema_version": "0.1",
        "status": "milb_runner_hitter_value_bridge_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "population_rows": frame.height,
        "target_seasons": list(TARGET_SEASONS),
        "selection_rule": (
            "MiLB effect shrinkage uses prior MiLB folds; bridge form and weight use "
            "only earlier MLB target seasons and advancement-component squared error."
        ),
        "runner_effect_regression": regression_decisions,
        "bridge_selection": selection,
        "whole_value": {
            "baseline": regression_metrics(actual_total, baseline_total),
            "bridge": regression_metrics(actual_total, bridge_total),
            "bridge_minus_baseline": paired_cluster_rmse_delta(
                actual_total, bridge_total, baseline_total, player_ids,
                bootstrap_samples=5_000,
            ),
        },
        "advancement_component": {
            "baseline": regression_metrics(actual_component, baseline_component),
            "bridge": regression_metrics(actual_component, bridge_component),
            "bridge_minus_baseline": paired_cluster_rmse_delta(
                actual_component,
                bridge_component,
                baseline_component,
                player_ids,
                bootstrap_samples=5_000,
            ),
        },
        "by_target_season": by_season,
        "milb_projection_coverage": int(
            frame["prediction_milb_advancement_war"].is_not_null().sum()
        ),
        "artifact": artifact.as_record(),
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
