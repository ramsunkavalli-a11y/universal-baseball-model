#!/usr/bin/env python3
"""Rank the predeclared 2021–2022 Current Talent development grid."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.current_talent_selection import summarize_selection_grid


EXPECTED_CANDIDATE_COUNT = 18
EXPECTED_FOLD_COUNT = 6
EXPECTED_SELECTION_SEASONS = {2021, 2022}
REFERENCE_CANDIDATE_ID = "hl90_ps100_fitted"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def _read_all(input_root: Path, filename: str) -> pl.DataFrame:
    paths = sorted(input_root.rglob(filename))
    if not paths:
        raise FileNotFoundError(f"no {filename} files found under {input_root}")
    frames = [pl.read_csv(path, try_parse_dates=True) for path in paths]
    return pl.concat(frames, how="vertical_relaxed")


def _write(frame: pl.DataFrame, output_dir: Path, name: str) -> dict[str, object]:
    parquet = output_dir / f"{name}.parquet"
    csv = output_dir / f"{name}.csv"
    frame.write_parquet(parquet, compression="zstd")
    frame.write_csv(csv)
    return {
        "parquet": str(parquet),
        "csv": str(csv),
        "row_count": int(frame.height),
        "column_count": len(frame.columns),
    }


def _selected_guardrails(
    candidate_id: str,
    component_metrics: pl.DataFrame,
    stratum_metrics: pl.DataFrame,
) -> dict[str, object]:
    component = component_metrics.filter(pl.col("candidate_id") == candidate_id)
    strata = stratum_metrics.filter(pl.col("candidate_id") == candidate_id)
    if component.is_empty() or strata.is_empty():
        raise ValueError(f"missing guardrail metrics for selected candidate {candidate_id}")

    component_keys = ["season", "as_of_date", "core_bin"]
    b0_components = component.filter(pl.col("model") == "baseline0").select(
        *component_keys,
        pl.col("multinomial_log_loss_contribution").alias("b0_ll"),
        pl.col("binary_brier_contribution").alias("b0_brier"),
    )
    b1_components = component.filter(pl.col("model") == "baseline1").select(
        *component_keys,
        pl.col("multinomial_log_loss_contribution").alias("b1_ll"),
        pl.col("binary_brier_contribution").alias("b1_brier"),
    )
    component_compare = b0_components.join(b1_components, on=component_keys, how="inner")
    if component_compare.height != b0_components.height or component_compare.height != b1_components.height:
        raise ValueError("selected candidate component comparison coverage mismatch")

    stratum_keys = ["season", "as_of_date", "stratum_type", "stratum_value"]
    b0_strata = strata.filter(pl.col("model") == "baseline0").select(
        *stratum_keys,
        pl.col("event_weighted_log_loss").alias("b0_ll"),
        pl.col("event_weighted_multinomial_brier").alias("b0_brier"),
    )
    b1_strata = strata.filter(pl.col("model") == "baseline1").select(
        *stratum_keys,
        pl.col("event_weighted_log_loss").alias("b1_ll"),
        pl.col("event_weighted_multinomial_brier").alias("b1_brier"),
    )
    stratum_compare = b0_strata.join(b1_strata, on=stratum_keys, how="inner")
    if stratum_compare.height != b0_strata.height or stratum_compare.height != b1_strata.height:
        raise ValueError("selected candidate stratum comparison coverage mismatch")

    return {
        "component_comparison_count": int(component_compare.height),
        "component_log_loss_win_count": int(
            component_compare.filter(pl.col("b1_ll") < pl.col("b0_ll")).height
        ),
        "component_brier_win_count": int(
            component_compare.filter(pl.col("b1_brier") < pl.col("b0_brier")).height
        ),
        "stratum_comparison_count": int(stratum_compare.height),
        "stratum_log_loss_win_count": int(
            stratum_compare.filter(pl.col("b1_ll") < pl.col("b0_ll")).height
        ),
        "stratum_brier_win_count": int(
            stratum_compare.filter(pl.col("b1_brier") < pl.col("b0_brier")).height
        ),
    }


def main() -> int:
    args = _parse_args()
    fold_metrics = _read_all(args.input_root, "candidate_fold_metrics.csv")
    component_metrics = _read_all(args.input_root, "candidate_component_metrics.csv")
    stratum_metrics = _read_all(args.input_root, "candidate_stratum_metrics.csv")

    seasons = set(int(value) for value in fold_metrics.get_column("season").unique().to_list())
    if seasons != EXPECTED_SELECTION_SEASONS:
        raise ValueError(
            f"selection grid must use only 2021–2022; observed seasons={sorted(seasons)}"
        )
    summary = summarize_selection_grid(
        fold_metrics,
        expected_fold_count=EXPECTED_FOLD_COUNT,
        expected_candidate_count=EXPECTED_CANDIDATE_COUNT,
    )
    ranked = summary.ranked_candidates
    selected = dict(summary.selected_candidate)
    selected_id = str(selected["candidate_id"])

    reference = ranked.filter(pl.col("candidate_id") == REFERENCE_CANDIDATE_ID)
    if reference.height != 1:
        raise ValueError(f"missing reference candidate {REFERENCE_CANDIDATE_ID}")
    reference_row = reference.to_dicts()[0]
    selected["reference_candidate_id"] = REFERENCE_CANDIDATE_ID
    selected["selected_minus_reference_mean_log_loss"] = float(
        selected["mean_baseline1_log_loss"] - reference_row["mean_baseline1_log_loss"]
    )
    selected["selected_minus_reference_mean_brier"] = float(
        selected["mean_baseline1_brier"] - reference_row["mean_baseline1_brier"]
    )
    selected["guardrails"] = _selected_guardrails(
        selected_id,
        component_metrics,
        stratum_metrics,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "ranked_candidates": _write(ranked, args.output_dir, "ranked_candidates"),
        "fold_metrics": _write(fold_metrics, args.output_dir, "development_fold_metrics"),
    }
    (args.output_dir / "selected_candidate.json").write_text(
        json.dumps(selected, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    report = {
        "report_schema_version": "0.1",
        "selection_plan": "docs/current-talent-baseline-selection-plan.md",
        "selection_seasons": sorted(EXPECTED_SELECTION_SEASONS),
        "selection_uses_2023": False,
        "summary_metrics": summary.metrics,
        "selected_candidate": selected,
        "reference_candidate": reference_row,
        "pareto_frontier": ranked.filter(pl.col("proper_score_pareto_frontier")).to_dicts(),
        "top_five_by_primary_log_loss": ranked.head(5).to_dicts(),
        "outputs": outputs,
        "interpretation": (
            "Development-grid selection only. The primary candidate was chosen from 2021–2022 "
            "equal-fold mean log loss under the predeclared plan. Do not substitute a different "
            "candidate after inspecting 2023 confirmation results."
        ),
    }
    (args.output_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
