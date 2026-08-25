#!/usr/bin/env python3
"""Select and fit S0 from frozen predictors and strictly earlier training origins."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_v2_evaluation import score_hitter_predictions
from universal_baseball.hitter_v2_model import (
    predict_b1_marcel_345_k1200,
    predict_c0_nested_eb,
)
from universal_baseball.hitter_v2_s0 import (
    blend_outcome_predictions,
    select_c0_weight,
)
from universal_baseball.hitter_v2_stage2f_selection import (
    aggregate_training_origin_target,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


FOLDS = ("V2022", "V2023", "V2024")
WEIGHT_GRID = (0.5, 0.625, 0.75, 0.875, 1.0)
NO_ORIGIN_C0_WEIGHT = 1.0


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--execution-contract",
        type=Path,
        default=Path("docs/hitter-v2-S0-fit-execution-contract.json"),
    )
    parser.add_argument(
        "--component-selection",
        type=Path,
        default=Path("docs/hitter-v2-stage2-component-selection-result.json"),
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
        "--baseline-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-final-validation/tables"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-S0-fit"),
    )
    return parser.parse_args()


def _verify_execution_contract(contract: dict[str, object], runner: Path) -> None:
    if contract["status"] != "frozen_before_first_S0_fit_execution":
        raise ValueError("S0 fit execution contract is not frozen")
    if sha256_file(runner) != contract["runner_sha256"]:
        raise ValueError("S0 fit runner changed after freeze")
    if contract["target_free_fit_authorized"] is not True:
        raise ValueError("S0 target-free fit is not authorized")
    for boundary in (
        "disclosed_validation_scoring_authorized",
        "protected_confirmation_access_authorized",
        "later_increment_fit_authorized",
        "stage3_authorized",
        "full_war_authorized",
    ):
        if contract[boundary] is not False:
            raise ValueError(f"S0 fit improperly opened {boundary}")
    for fold in FOLDS:
        for record in contract["folds"][fold]["inputs"]:
            path = Path(record["path"])
            if sha256_file(path) != record["sha256"]:
                raise ValueError(f"S0 frozen input changed: {path}")
    for record in contract["shared_inputs"]:
        path = Path(record["path"])
        if sha256_file(path) != record["sha256"]:
            raise ValueError(f"S0 frozen shared input changed: {path}")


def _component_parameters(
    selection: dict[str, object], fold_id: str
) -> tuple[dict[str, float], dict[str, float]]:
    selected = selection["folds"][fold_id]["selected"]
    return (
        {
            component: float(values["half_life_seasons"])
            for component, values in selected.items()
        },
        {
            component: float(values["component_prior_pa"])
            for component, values in selected.items()
        },
    )


def _latest_origin_ages(age_root: Path, origin: int) -> dict[int, float]:
    ages = pl.read_parquet(age_root / f"v{origin}" / "forecast_player_ages.parquet")
    return {
        int(row["player_id"]): float(row["age_years"])
        for row in ages.iter_rows(named=True)
        if row["age_years"] is not None
    }


def _selection_scores(
    training: pl.DataFrame,
    *,
    cutoff: int,
    half_lives: dict[str, float],
    component_priors: dict[str, float],
    age_root: Path,
) -> tuple[pl.DataFrame, list[int]]:
    origins = list(range(int(training["season"].min()) + 1, cutoff + 1))
    if not origins:
        return pl.DataFrame(), []
    rows = []
    for weight in WEIGHT_GRID:
        details = []
        losses = []
        for origin in origins:
            history = training.filter(pl.col("season") < origin)
            players = sorted(
                int(value) for value in history["player_id"].unique().to_list()
            )
            origin_outcomes = aggregate_training_origin_target(
                training.filter(pl.col("season") <= origin),
                origin_season=origin,
                eligible_player_ids=set(players),
            )
            c0 = predict_c0_nested_eb(
                history,
                players,
                predictor_cutoff_season=origin - 1,
                half_life_seasons=half_lives,
                component_prior_pa=component_priors,
            )
            marcel = predict_b1_marcel_345_k1200(
                history,
                players,
                predictor_cutoff_season=origin - 1,
                ages_at_target=_latest_origin_ages(age_root, origin),
            )
            blended = blend_outcome_predictions(c0, marcel, c0_weight=weight)
            origin_scores = {}
            for view in ("player", "pa"):
                loss = float(
                    score_hitter_predictions(
                        blended, origin_outcomes, weighting=view
                    )["terminal_log_loss"]
                )
                losses.append(loss)
                origin_scores[f"{view}_terminal_log_loss"] = loss
            details.append({"origin_season": origin, **origin_scores})
        rows.append(
            {
                "c0_weight": weight,
                "marcel_weight": 1.0 - weight,
                "mean_player_pa_terminal_log_loss": sum(losses) / len(losses),
                "origin_count": len(origins),
                "origin_detail_json": json.dumps(
                    details, separators=(",", ":"), sort_keys=True
                ),
            }
        )
    return pl.DataFrame(rows).sort("c0_weight"), origins


def _probability_health(frame: pl.DataFrame) -> dict[str, object]:
    columns = [column for column in frame.columns if column.startswith("p_")]
    sums = frame.select(pl.sum_horizontal(*columns).alias("sum"))["sum"]
    return {
        "rows": frame.height,
        "all_finite": all(
            frame.select(pl.col(column).is_finite().all() for column in columns).row(0)
        ),
        "all_nonnegative": all(
            frame.select((pl.col(column) >= 0.0).all() for column in columns).row(0)
        ),
        "maximum_simplex_error": float((sums - 1.0).abs().max()),
    }


def main() -> int:
    args = _args()
    contract = json.loads(args.execution_contract.read_text(encoding="utf-8"))
    _verify_execution_contract(contract, Path(__file__))
    component_selection = json.loads(
        args.component_selection.read_text(encoding="utf-8")
    )
    fold_reports = []
    for fold_id in FOLDS:
        slug = fold_id.lower()
        training = pl.read_parquet(
            args.prescore_root / slug / "training_player_league_seasons.parquet"
        )
        forecast = pl.read_parquet(args.prescore_root / slug / "forecast_population.parquet")
        cutoff = int(training["season"].max())
        half_lives, component_priors = _component_parameters(
            component_selection, fold_id
        )
        scores, origins = _selection_scores(
            training,
            cutoff=cutoff,
            half_lives=half_lives,
            component_priors=component_priors,
            age_root=args.age_root,
        )
        if scores.is_empty():
            selected = {
                "c0_weight": NO_ORIGIN_C0_WEIGHT,
                "marcel_weight": 0.0,
                "mean_player_pa_terminal_log_loss": None,
            }
            score_artifact = None
            selection_source = "no_earlier_origin_preregistered_pure_C0_fallback"
        else:
            selected = select_c0_weight(scores)
            score_artifact = write_canonical_parquet(
                scores,
                args.report_root / "tables" / slug / "weight_selection_scores.parquet",
                table_name=f"hitter_v2_S0_{slug}_weight_selection_scores",
            ).as_record()
            selection_source = "strictly_earlier_training_origin_mean_player_pa_log_loss"
        c0 = pl.read_parquet(
            args.baseline_root / slug / "c0_nested_eb_predictions.parquet"
        )
        marcel = pl.read_parquet(
            args.baseline_root / slug / "b1_marcel_345_k1200_predictions.parquet"
        )
        prediction = blend_outcome_predictions(
            c0, marcel, c0_weight=float(selected["c0_weight"])
        )
        if set(prediction["player_id"].to_list()) != set(
            forecast["player_id"].to_list()
        ):
            raise ValueError("S0 changed the frozen forecast population")
        prediction_artifact = write_canonical_parquet(
            prediction,
            args.report_root / "tables" / slug / "s0_predictions.parquet",
            table_name=f"hitter_v2_S0_{slug}_predictions",
        ).as_record()
        fold_reports.append(
            {
                "fold_id": fold_id,
                "predictor_cutoff_season": cutoff,
                "training_origin_seasons": origins,
                "selection_source": selection_source,
                "selected": selected,
                "component_half_lives": half_lives,
                "component_priors": component_priors,
                "forecast_players": prediction.height,
                "forecast_population_unchanged": True,
                "probability_health": _probability_health(prediction),
                "weight_selection_artifact": score_artifact,
                "prediction_artifact": prediction_artifact,
                "disclosed_validation_outcomes_loaded": False,
                "disclosed_validation_metrics_computed": False,
            }
        )
    report = {
        "schema_version": "0.1",
        "program": "hitter_v2",
        "stage": "S0_target_free_fit",
        "status": "fit_complete_unscored",
        "model_id": "S0_C0_MARCEL_STABILITY_BLEND",
        "weight_grid_C0": list(WEIGHT_GRID),
        "no_origin_C0_weight": NO_ORIGIN_C0_WEIGHT,
        "selection_metric": "arithmetic_mean_of_player_and_PA_terminal_log_loss_across_strictly_earlier_training_origins",
        "folds": fold_reports,
        "disclosed_validation_outcomes_loaded": False,
        "protected_confirmation_opened": False,
        "candidate_scored": False,
        "next_gate": "freeze_fit_artifacts_then_require_separate_disclosed_scoring_authorization",
    }
    args.report_root.mkdir(parents=True, exist_ok=True)
    report_path = args.report_root / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
