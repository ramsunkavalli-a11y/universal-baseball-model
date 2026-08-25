#!/usr/bin/env python3
"""Run the authorized disclosed-data postmortem after H0's final failure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_v2_evaluation import score_hitter_predictions
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_stage2f import (
    probabilities_from_links,
    probability_links,
    translation_age_band,
)
from universal_baseball.hitter_v2_stage2f_scoring import translate_target_to_reference
from universal_baseball.hitter_v2_validation import (
    build_evaluation_subgroups,
    score_subgroup,
)
from universal_baseball.storage import sha256_file


FOLDS = ("V2022", "V2023", "V2024")
PRIMARY = (
    "terminal_log_loss",
    "terminal_brier_score",
    "woba_rmse",
    "runs_per_600_rmse",
)
DIMENSIONS = {
    "level": "primary_target_level_group",
    "age": "age_band",
    "evidence": "evidence_band",
    "movement": "movement_band",
    "K": "k_band",
    "power": "hr_power_band",
}


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--contract", type=Path, default=Path("docs/hitter-v2-post-H0-diagnostic-contract.json")
    )
    parser.add_argument(
        "--selection-report",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2f-H0-selection/report.json"),
    )
    parser.add_argument(
        "--selection-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2f-H0-selection/tables"),
    )
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-final-validation/tables"),
    )
    parser.add_argument(
        "--prescore-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-prescore/tables"),
    )
    parser.add_argument(
        "--age-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-age/tables"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/generated/hitter-v2-post-H0-diagnostic/report.json"),
    )
    return parser.parse_args()


def _verify_contract(contract: dict[str, object], runner: Path) -> None:
    if contract["status"] != "frozen_before_diagnostic_execution":
        raise ValueError("post-H0 diagnostic contract is not frozen")
    if sha256_file(runner) != contract["runner_sha256"]:
        raise ValueError("post-H0 diagnostic runner changed after freeze")
    if contract["diagnostic_execution_authorized"] is not True:
        raise ValueError("post-H0 diagnostic execution is not authorized")
    for boundary in (
        "candidate_fit_authorized",
        "candidate_scoring_authorized",
        "protected_confirmation_access_authorized",
        "stage3_authorized",
        "full_war_authorized",
    ):
        if contract[boundary] is not False:
            raise ValueError(f"improperly opened boundary: {boundary}")


def age_translation_only(
    wrapped_c0: pl.DataFrame,
    ages: pl.DataFrame,
    offsets: pl.DataFrame | None,
) -> pl.DataFrame:
    """Replace the ALL translation on wrapped C0 with its frozen age-band form."""

    if offsets is None or offsets.is_empty():
        return wrapped_c0.with_columns(pl.lit("L1_AGE_TRANSLATION_ONLY").alias("model_id"))
    lookup = {
        (str(row["component"]), str(row["level"]), str(row["age_band"])): float(
            row["link_offset_to_MLB"]
        )
        for row in offsets.iter_rows(named=True)
    }
    joined = wrapped_c0.join(
        ages.select("player_id", "age_years"), on="player_id", how="left", validate="1:1"
    )
    rows: list[dict[str, object]] = []
    for row in joined.iter_rows(named=True):
        probabilities = {
            outcome: float(row[f"p_{outcome}"]) for outcome in HITTER_TALENT_OUTCOMES
        }
        links = probability_links(probabilities)
        age_band = translation_age_band(row["age_years"])
        level = str(row["prior_level"])
        adjusted = {
            component: value
            + lookup.get((component, level, age_band), lookup.get((component, level, "ALL"), 0.0))
            - lookup.get((component, level, "ALL"), 0.0)
            for component, value in links.items()
        }
        translated = probabilities_from_links(adjusted)
        rows.append(
            {
                **{key: value for key, value in row.items() if key != "age_years"},
                "model_id": "L1_AGE_TRANSLATION_ONLY",
                **{f"p_{outcome}": translated[outcome] for outcome in HITTER_TALENT_OUTCOMES},
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None).sort("player_id")


def _component_rows(
    predictions: pl.DataFrame, target: pl.DataFrame, weighting: str
) -> list[dict[str, object]]:
    joined = target.join(predictions, on="player_id", how="inner", validate="1:1")
    pa = joined["hitter_talent_pa"].to_numpy().astype(float)
    weights = np.ones(joined.height) if weighting == "player" else pa
    rows = []
    for outcome in HITTER_TALENT_OUTCOMES:
        actual = joined[outcome].to_numpy().astype(float) / pa
        predicted = joined[f"p_{outcome}"].to_numpy().astype(float)
        clipped = np.clip(predicted, 1e-12, 1.0 - 1e-12)
        rows.append(
            {
                "outcome": outcome,
                "actual_rate": float(np.average(actual, weights=weights)),
                "predicted_rate": float(np.average(predicted, weights=weights)),
                "bias": float(np.average(predicted - actual, weights=weights)),
                "binary_log_loss": float(
                    np.average(
                        -(actual * np.log(clipped) + (1.0 - actual) * np.log(1.0 - clipped)),
                        weights=weights,
                    )
                ),
                "binary_brier": float(np.average((predicted - actual) ** 2, weights=weights)),
            }
        )
    return rows


def _subgroups(c0: pl.DataFrame, marcel: pl.DataFrame, target: pl.DataFrame, labels: pl.DataFrame) -> list[dict[str, object]]:
    rows = []
    for dimension, column in DIMENSIONS.items():
        for label in sorted(str(value) for value in labels[column].drop_nulls().unique()):
            ids = labels.filter(pl.col(column) == label)["player_id"].to_list()
            scores = {
                "C0_NESTED_EB": score_subgroup(c0, target, ids),
                "B1_MARCEL_345_K1200": score_subgroup(marcel, target, ids),
            }
            players = int(scores["C0_NESTED_EB"]["players"])
            target_pa = int(scores["C0_NESTED_EB"]["target_pa"])
            supported = players >= (100 if dimension == "level" else 50) and target_pa >= (
                10_000 if dimension == "level" else 5_000
            )
            deltas = {
                view: {
                    metric: float(scores["C0_NESTED_EB"]["metrics"][view][metric])
                    - float(scores["B1_MARCEL_345_K1200"]["metrics"][view][metric])
                    for metric in PRIMARY
                }
                for view in ("player", "pa")
            } if supported else {}
            rows.append({
                "dimension": dimension, "label": label, "players": players,
                "target_pa": target_pa, "supported": supported, "C0_minus_Marcel": deltas,
            })
    return rows


def _layer_attribution(layers: dict[str, pl.DataFrame], target: pl.DataFrame) -> dict[str, object]:
    order = list(layers)
    metrics = {
        name: {view: score_hitter_predictions(frame, target, weighting=view) for view in ("player", "pa")}
        for name, frame in layers.items()
    }
    increments = []
    for before, after in zip(order, order[1:]):
        increments.append({
            "from": before,
            "to": after,
            "metric_delta": {
                view: {metric: float(metrics[after][view][metric]) - float(metrics[before][view][metric]) for metric in PRIMARY}
                for view in ("player", "pa")
            },
            "outcome_binary_log_loss_delta": {
                view: {
                    after_row["outcome"]: after_row["binary_log_loss"] - before_row["binary_log_loss"]
                    for before_row, after_row in zip(
                        _component_rows(layers[before], target, view),
                        _component_rows(layers[after], target, view),
                    )
                }
                for view in ("player", "pa")
            },
        })
    return {"order": order, "metrics": metrics, "increments": increments}


def main() -> int:
    args = _args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    _verify_contract(contract, Path(__file__))
    selection = json.loads(args.selection_report.read_text(encoding="utf-8"))
    selected = {row["fold_id"]: row for row in selection["folds"]}
    fold_rows = []
    for fold in FOLDS:
        slug = fold.lower()
        target = pl.read_parquet(args.prescore_root / slug / "target_players.parquet")
        training = pl.read_parquet(args.prescore_root / slug / "training_player_league_seasons.parquet")
        ages = pl.read_parquet(args.age_root / slug / "forecast_player_ages.parquet")
        c0 = pl.read_parquet(args.raw_root / slug / "c0_nested_eb_predictions.parquet")
        marcel = pl.read_parquet(args.raw_root / slug / "b1_marcel_345_k1200_predictions.parquet")
        root = args.selection_root / slug
        offsets_path = root / "translation_offsets.parquet"
        offsets = pl.read_parquet(offsets_path) if offsets_path.exists() else None
        reference_target = translate_target_to_reference(target, offsets)
        l0 = pl.read_parquet(root / "reference_wrapped_c0.parquet")
        layers = {
            "L0_REFERENCE_WRAPPED_C0": l0,
            "L1_AGE_TRANSLATION_ONLY": age_translation_only(l0, ages, offsets),
            "L2_PLUS_DEVELOPMENT": pl.read_parquet(root / "h0_precal_predictions.parquet"),
            "L3_PLUS_CALIBRATION_H0": pl.read_parquet(root / "h0_predictions.parquet"),
        }
        fold_rows.append({
            "fold_id": fold,
            "raw_C0_vs_Marcel": {
                "overall": {
                    model: {view: score_hitter_predictions(frame, target, weighting=view) for view in ("player", "pa")}
                    for model, frame in {"C0_NESTED_EB": c0, "B1_MARCEL_345_K1200": marcel}.items()
                },
                "components": {
                    model: {view: _component_rows(frame, target, view) for view in ("player", "pa")}
                    for model, frame in {"C0_NESTED_EB": c0, "B1_MARCEL_345_K1200": marcel}.items()
                },
                "subgroups": _subgroups(c0, marcel, target, build_evaluation_subgroups(training, target, ages)),
            },
            "H0_layer_attribution": _layer_attribution(layers, reference_target),
            "selected_surface": selected[fold]["selected_surface"],
        })
    report = {
        "schema_version": "0.1", "program": "hitter_v2", "stage": "post_H0_diagnostic",
        "status": "diagnostic_complete_no_candidate_fit_or_selection", "folds": fold_rows,
        "selection_report_sha256": sha256_file(args.selection_report),
        "protected_confirmation_opened": False, "candidate_fit": False, "candidate_scored": False,
        "next_gate": "document_findings_and_preregister_distinct_increment_ladder_then_stop_before_fit",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "folds": FOLDS}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
