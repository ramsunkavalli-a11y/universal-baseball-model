#!/usr/bin/env python3
"""Audit whether aggregate RMSE hides important hitter-candidate failures."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from universal_baseball.hitter_target_architecture import (
    classification_metrics,
    regression_metrics,
)


PREDICTION_PATH = Path(
    "reports/generated/hitter-model-finalist-tuning-v2/tables/"
    "finalist-ensemble-predictions.parquet"
)
PANEL_PATH = Path(
    "reports/generated/hitter-value-panel-v2/tables/modeling-panel.parquet"
)
OUTPUT_ROOT = Path("reports/generated/hitter-candidate-blindspot-audit-v2")
ACTUAL = "actual_component_war"
CANDIDATE = "prediction_candidate_equal_mean"
REFERENCE = "prediction_best_single_lightgbm"


def _model_comparison(frame: pl.DataFrame) -> dict[str, object]:
    actual = frame[ACTUAL].to_numpy()
    candidate = frame[CANDIDATE].to_numpy()
    reference = frame[REFERENCE].to_numpy()
    return {
        "rows": frame.height,
        "candidate": regression_metrics(actual, candidate),
        "best_single_lightgbm": regression_metrics(actual, reference),
        "candidate_minus_reference_rmse": (
            regression_metrics(actual, candidate)["rmse"]
            - regression_metrics(actual, reference)["rmse"]
        ),
    }


def _segment_report(
    frame: pl.DataFrame, expressions: dict[str, pl.Expr]
) -> dict[str, object]:
    total_sse = float(
        frame.select(((pl.col(CANDIDATE) - pl.col(ACTUAL)) ** 2).sum()).item()
    )
    report: dict[str, object] = {}
    for label, expression in expressions.items():
        segment = frame.filter(expression)
        details = _model_comparison(segment)
        segment_sse = float(
            segment.select(
                ((pl.col(CANDIDATE) - pl.col(ACTUAL)) ** 2).sum()
            ).item()
        )
        details["candidate_sse_share"] = segment_sse / total_sse
        report[label] = details
    return report


def _top_n_report(frame: pl.DataFrame, top_n: int) -> dict[str, object]:
    fold_reports: dict[str, object] = {}
    overlaps = 0
    selected = 0
    candidate_actual_sum = 0.0
    reference_actual_sum = 0.0
    oracle_actual_sum = 0.0
    for origin in sorted(frame["origin_year"].unique().to_list()):
        fold = frame.filter(pl.col("origin_year") == origin)
        n = min(top_n, fold.height)
        actual = fold[ACTUAL].to_numpy()
        candidate = fold[CANDIDATE].to_numpy()
        reference = fold[REFERENCE].to_numpy()
        actual_top = set(np.argpartition(actual, -n)[-n:].tolist())
        candidate_top = set(np.argpartition(candidate, -n)[-n:].tolist())
        reference_top = set(np.argpartition(reference, -n)[-n:].tolist())
        candidate_overlap = len(actual_top & candidate_top)
        reference_overlap = len(actual_top & reference_top)
        candidate_sum = float(actual[list(candidate_top)].sum())
        reference_sum = float(actual[list(reference_top)].sum())
        oracle_sum = float(actual[list(actual_top)].sum())
        fold_reports[str(origin)] = {
            "players_selected": n,
            "candidate_top_actual_overlap": candidate_overlap / n,
            "reference_top_actual_overlap": reference_overlap / n,
            "candidate_realized_war": candidate_sum,
            "reference_realized_war": reference_sum,
            "oracle_top_realized_war": oracle_sum,
        }
        overlaps += candidate_overlap
        selected += n
        candidate_actual_sum += candidate_sum
        reference_actual_sum += reference_sum
        oracle_actual_sum += oracle_sum
    return {
        "top_n_per_origin": top_n,
        "candidate_overlap_rate": overlaps / selected,
        "candidate_realized_war_capture": candidate_actual_sum / oracle_actual_sum,
        "reference_realized_war_capture": reference_actual_sum / oracle_actual_sum,
        "folds": fold_reports,
    }


def _value_deciles(frame: pl.DataFrame) -> list[dict[str, float | int]]:
    rows: list[dict[str, float | int]] = []
    assignments: list[pl.DataFrame] = []
    for origin in sorted(frame["origin_year"].unique().to_list()):
        fold = frame.filter(pl.col("origin_year") == origin).sort(CANDIDATE)
        assignments.append(
            fold.with_row_index("rank").with_columns(
                (
                    pl.col("rank") * 10 / pl.lit(fold.height)
                ).floor().clip(0, 9).cast(pl.Int8).alias("prediction_decile")
            )
        )
    ranked = pl.concat(assignments)
    for row in (
        ranked.group_by("prediction_decile")
        .agg(
            pl.len().alias("rows"),
            pl.col(CANDIDATE).mean().alias("predicted_mean"),
            pl.col(ACTUAL).mean().alias("actual_mean"),
            pl.col("actual_active").mean().alias("actual_active_rate"),
        )
        .sort("prediction_decile")
        .iter_rows(named=True)
    ):
        rows.append(row)
    return rows


def main() -> None:
    predictions = pl.read_parquet(PREDICTION_PATH)
    panel = pl.read_parquet(PANEL_PATH).select(
        "origin_year",
        "player_id",
        pl.col("lag0__age").alias("current_age"),
        pl.col("lag0__plate_appearances").alias("current_pa"),
        pl.col("lag1__season_available").alias("lag1_season_available"),
        pl.col("lag2__season_available").alias("lag2_season_available"),
    )
    frame = predictions.join(panel, on=["origin_year", "player_id"], how="left")
    frame = frame.with_columns(
        pl.when(pl.col("origin_year") <= 2018)
        .then(pl.lit("pre_2020"))
        .otherwise(pl.lit("post_2020"))
        .alias("era")
    )

    segments = {
        "target_activity": _segment_report(
            frame,
            {
                "not_mlb_active_next_year": pl.col("actual_active") == 0,
                "mlb_active_next_year": pl.col("actual_active") == 1,
            },
        ),
        "actual_value": _segment_report(
            frame,
            {
                "negative_war": pl.col(ACTUAL) < 0,
                "zero_to_one_war": pl.col(ACTUAL).is_between(0, 1, closed="both"),
                "one_to_two_war": pl.col(ACTUAL).is_between(1, 2, closed="right"),
                "two_plus_war": pl.col(ACTUAL) > 2,
            },
        ),
        "player_stage": _segment_report(
            frame,
            {
                stage: pl.col("player_stage") == stage
                for stage in ("current_mlb", "upper_minors", "lower_minors")
            },
        ),
        "current_workload": _segment_report(
            frame,
            {
                "under_100_pa": pl.col("current_pa") < 100,
                "100_to_299_pa": pl.col("current_pa").is_between(100, 299),
                "300_plus_pa": pl.col("current_pa") >= 300,
            },
        ),
        "age": _segment_report(
            frame,
            {
                "20_or_younger": pl.col("current_age") <= 20,
                "21_to_23": pl.col("current_age").is_between(21, 23),
                "24_to_26": pl.col("current_age").is_between(24, 26),
                "27_or_older": pl.col("current_age") >= 27,
            },
        ),
        "era": _segment_report(
            frame,
            {
                "pre_2020": pl.col("era") == "pre_2020",
                "post_2020": pl.col("era") == "post_2020",
            },
        ),
        "contact_coverage": _segment_report(
            frame,
            {
                "available": pl.col("current_contact_feature_available") == 1,
                "unavailable": pl.col("current_contact_feature_available") == 0,
            },
        ),
        "history_depth": _segment_report(
            frame,
            {
                "current_only": (pl.col("lag1_season_available") == 0)
                & (pl.col("lag2_season_available") == 0),
                "at_least_one_prior": (pl.col("lag1_season_available") == 1)
                | (pl.col("lag2_season_available") == 1),
            },
        ),
    }

    actual = frame[ACTUAL].to_numpy()
    candidate = frame[CANDIDATE].to_numpy()
    quantiles = (0.0, 0.01, 0.1, 0.5, 0.9, 0.99, 1.0)
    distribution = {
        "actual_quantiles": {
            str(q): float(np.quantile(actual, q)) for q in quantiles
        },
        "prediction_quantiles": {
            str(q): float(np.quantile(candidate, q)) for q in quantiles
        },
        "negative_prediction_rate": float(np.mean(candidate < 0)),
        "zero_floor_sensitivity": regression_metrics(
            actual, np.maximum(candidate, 0.0)
        ),
        "unchanged_candidate": regression_metrics(actual, candidate),
    }
    rank_by_origin = {}
    for origin in sorted(frame["origin_year"].unique().to_list()):
        fold = frame.filter(pl.col("origin_year") == origin)
        rank_by_origin[str(origin)] = {
            "all_players_spearman": float(
                spearmanr(fold[ACTUAL].to_numpy(), fold[CANDIDATE].to_numpy()).statistic
            ),
            "current_mlb_spearman": float(
                spearmanr(
                    fold.filter(pl.col("player_stage") == "current_mlb")[ACTUAL].to_numpy(),
                    fold.filter(pl.col("player_stage") == "current_mlb")[CANDIDATE].to_numpy(),
                ).statistic
            ),
        }

    report = {
        "schema_version": "0.1",
        "status": "candidate_blindspot_audit_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "population_rows": frame.height,
        "overall": _model_comparison(frame),
        "segments": segments,
        "distribution": distribution,
        "prediction_deciles": _value_deciles(frame),
        "ranking": {
            "spearman_by_origin": rank_by_origin,
            "top_25": _top_n_report(frame, 25),
            "top_50": _top_n_report(frame, 50),
            "top_100": _top_n_report(frame, 100),
        },
        "mlb_active_probability": classification_metrics(
            frame["actual_active"].to_numpy(),
            frame["prediction_candidate_mlb_active_probability"].to_numpy(),
        ),
        "interpretation_guardrails": [
            "Outcome-defined segments diagnose failure modes but cannot be selected at forecast time.",
            "Aggregate RMSE must be read together with active-player, current-MLB, and top-player diagnostics.",
            "Flooring predictions at zero is a sensitivity only and is not selected on exposed development outcomes.",
        ],
    }
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
