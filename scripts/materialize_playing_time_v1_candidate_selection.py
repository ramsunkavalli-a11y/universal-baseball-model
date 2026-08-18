#!/usr/bin/env python3
"""Run the frozen Playing Time / Role v1 candidate selection on 2022 only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.playing_time_model import (
    PT_FORMS,
    build_playing_time_design,
    fit_playing_time_hurdle,
    score_playing_time_hurdle,
)
from universal_baseball.playing_time_selection import (
    pooled_playing_time_metrics,
    select_playing_time_form,
)
from universal_baseball.projection_ridge import PROJECTION_CV_FOLD_COUNT, projection_cv_fold
from universal_baseball.storage import write_canonical_parquet


SELECTION_FOLD = "projection_2021_to_2022"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictor-root", type=Path, required=True)
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/playing-time-v1-candidate-selection"),
    )
    return parser.parse_args()


def _one(root: Path, filename: str, label: str) -> Path:
    matches = sorted(path for path in root.rglob(filename) if path.is_file())
    if len(matches) != 1:
        raise RuntimeError(f"expected one {label} named {filename}, found {len(matches)}")
    return matches[0]


def main() -> int:
    args = _parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    predictors = pl.read_parquet(
        _one(
            args.predictor_root / "tables" / SELECTION_FOLD,
            "predictors.parquet",
            "2022 selection predictors",
        )
    )
    targets = pl.read_parquet(
        _one(
            args.target_root / "tables" / SELECTION_FOLD,
            "next_year_mlb_pa_targets.parquet",
            "2022 selection MLB PA targets",
        )
    ).select("player_id", "next_year_mlb_pa")

    predictor_ids = set(int(value) for value in predictors.get_column("player_id").to_list())
    target_ids = set(int(value) for value in targets.get_column("player_id").to_list())
    if predictor_ids != target_ids:
        raise RuntimeError(
            "playing-time 2022 selection predictor/target player coverage differs: "
            f"predictors={len(predictor_ids)}, targets={len(target_ids)}, "
            f"predictor_only={len(predictor_ids-target_ids)}, target_only={len(target_ids-predictor_ids)}"
        )

    cv = pl.DataFrame(
        {
            "player_id": sorted(predictor_ids),
            "cv_fold": [projection_cv_fold(player_id) for player_id in sorted(predictor_ids)],
        }
    )
    fold_counts = cv.group_by("cv_fold").len().sort("cv_fold")
    if set(int(value) for value in fold_counts.get_column("cv_fold").to_list()) != set(
        range(PROJECTION_CV_FOLD_COUNT)
    ):
        raise RuntimeError("playing-time 2022 selection CV fold coverage is incomplete")

    form_result_rows: list[dict[str, object]] = []
    fold_metric_rows: list[dict[str, object]] = []
    scored_frames: list[pl.DataFrame] = []
    coefficient_frames: list[pl.DataFrame] = []
    standardization_frames: list[pl.DataFrame] = []

    for form in PT_FORMS:
        design = build_playing_time_design(predictors, form=form).join(cv, on="player_id")
        form_scored: list[pl.DataFrame] = []
        for cv_fold in range(PROJECTION_CV_FOLD_COUNT):
            train_design = design.filter(pl.col("cv_fold") != cv_fold).drop("cv_fold")
            heldout_design = design.filter(pl.col("cv_fold") == cv_fold).drop("cv_fold")
            train_ids = train_design.get_column("player_id")
            heldout_ids = heldout_design.get_column("player_id")
            if set(int(value) for value in train_ids.to_list()) & set(
                int(value) for value in heldout_ids.to_list()
            ):
                raise RuntimeError("playing-time CV train/heldout player overlap")
            train_targets = targets.filter(pl.col("player_id").is_in(train_ids))
            heldout_targets = targets.filter(pl.col("player_id").is_in(heldout_ids))

            fit = fit_playing_time_hurdle(train_design, train_targets, form=form)
            scored, metrics = score_playing_time_hurdle(
                fit, heldout_design, heldout_targets
            )
            scored = scored.with_columns(
                pl.lit(form).alias("form"),
                pl.lit(cv_fold).cast(pl.Int64).alias("cv_fold"),
            )
            form_scored.append(scored)
            scored_frames.append(scored)
            fold_metric_rows.append(
                {
                    "form": form,
                    "cv_fold": cv_fold,
                    **metrics,
                }
            )
            coefficient_frames.append(
                fit.coefficient_frame().with_columns(
                    pl.lit(form).alias("form"),
                    pl.lit(cv_fold).cast(pl.Int64).alias("cv_fold"),
                )
            )
            standardization_frames.append(
                fit.standardization_frame().with_columns(
                    pl.lit(form).alias("form"),
                    pl.lit(cv_fold).cast(pl.Int64).alias("cv_fold"),
                )
            )

        pooled = pooled_playing_time_metrics(
            pl.concat(form_scored, how="vertical_relaxed")
        )
        form_result_rows.append({"form": form, **pooled})

    form_results = pl.DataFrame(form_result_rows).sort("form")
    selection = select_playing_time_form(form_results)
    fold_metrics = pl.DataFrame(fold_metric_rows).sort(["form", "cv_fold"])
    all_scored = pl.concat(scored_frames, how="vertical_relaxed").sort(
        ["form", "cv_fold", "player_id"]
    )
    coefficients = pl.concat(coefficient_frames, how="vertical_relaxed").sort(
        ["form", "cv_fold", "component", "feature"]
    )
    standardization = pl.concat(
        standardization_frames, how="vertical_relaxed"
    ).sort(["form", "cv_fold", "feature"])

    storage = {
        "form_results": write_canonical_parquet(
            form_results,
            table_root / "form_results.parquet",
            table_name="playing_time_v1_2022_form_results",
        ).as_record(),
        "cv_fold_metrics": write_canonical_parquet(
            fold_metrics,
            table_root / "cv_fold_metrics.parquet",
            table_name="playing_time_v1_2022_cv_fold_metrics",
        ).as_record(),
        "cv_scored_rows": write_canonical_parquet(
            all_scored,
            table_root / "cv_scored_rows.parquet",
            table_name="playing_time_v1_2022_cv_scored_rows",
        ).as_record(),
        "cv_coefficients": write_canonical_parquet(
            coefficients,
            table_root / "cv_coefficients.parquet",
            table_name="playing_time_v1_2022_cv_coefficients",
        ).as_record(),
        "cv_standardization": write_canonical_parquet(
            standardization,
            table_root / "cv_standardization.parquet",
            table_name="playing_time_v1_2022_cv_standardization",
        ).as_record(),
    }

    baseline = form_results.filter(pl.col("form") == PT_FORMS[0]).row(0, named=True)
    selected = form_results.filter(pl.col("form") == selection.selected_form).row(
        0, named=True
    )
    report = {
        "report_schema_version": "0.1",
        "gate": "playing_time_v1_2022_candidate_selection",
        "selection_fold": SELECTION_FOLD,
        "authorized_target_years_used_for_model_selection": [2022],
        "candidate_forms": list(PT_FORMS),
        "cv_fold_count": PROJECTION_CV_FOLD_COUNT,
        "cv_fold_counts": fold_counts.to_dicts(),
        "selection": {
            "selected_form": selection.selected_form,
            "selected_full_nll": selection.selected_full_nll,
            "baseline0_full_nll": selection.baseline0_full_nll,
            "selected_minus_baseline0_full_nll": selection.selected_full_nll
            - selection.baseline0_full_nll,
            "selected_participation_log_loss": selection.selected_participation_log_loss,
            "selected_unconditional_pa_mae": selection.selected_unconditional_pa_mae,
            "baseline0_selected": selection.baseline0_selected,
            "advances_to_out_of_time_validation": selection.advances_to_out_of_time_validation,
            "tie_break_metrics": selection.metrics,
            "selected_pooled_metrics": {
                key: selected[key]
                for key in selected
                if key != "form"
            },
            "baseline0_pooled_metrics": {
                key: baseline[key]
                for key in baseline
                if key != "form"
            },
        },
        "storage": storage,
        "boundary": {
            "2023_candidate_scores_accessed": False,
            "2024_candidate_scores_accessed": False,
            "2025_accessed": False,
            "future_team_used": False,
            "future_level_used": False,
            "batting_rate_modified": False,
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Playing-time v1 — 2022-only candidate selection",
        "",
        f"- Selected form: {selection.selected_form}",
        f"- Selected full NLL: {selection.selected_full_nll:.9f}",
        f"- Level-only B0 full NLL: {selection.baseline0_full_nll:.9f}",
        f"- Delta full NLL: {selection.selected_full_nll - selection.baseline0_full_nll:+.9f}",
        f"- Selected participation log loss: {selection.selected_participation_log_loss:.9f}",
        f"- Selected unconditional MLB-PA MAE: {selection.selected_unconditional_pa_mae:.3f}",
        f"- B0 selected: {selection.baseline0_selected}",
        f"- Advances to OOT validation: {selection.advances_to_out_of_time_validation}",
        "- 2023 candidate scores accessed: False",
        "- 2024 candidate scores accessed: False",
        "- 2025 accessed: False",
        "",
    ]
    (args.output_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
