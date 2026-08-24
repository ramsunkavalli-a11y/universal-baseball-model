#!/usr/bin/env python3
"""Select nested Hitter v2 component grids from earlier origins only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_v2_evaluation import (
    score_nested_component_log_loss,
)
from universal_baseball.hitter_v2_model import (
    NESTED_NODES,
    predict_c0_nested_eb,
    select_component_hyperparameters,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


FOLDS = ("V2022", "V2023", "V2024")
HALF_LIFE_GRID = (1.0, 2.0, 3.0)
PRIOR_PA_GRID = (50.0, 100.0, 200.0, 400.0, 800.0)
NO_ORIGIN_DEFAULT = {"half_life_seasons": 3.0, "component_prior_pa": 800.0}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prescore-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-prescore/tables"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-component-selection"),
    )
    return parser.parse_args()


def _fold_inputs(root: Path, fold_id: str) -> tuple[pl.DataFrame, list[int], pl.DataFrame]:
    fold_root = root / fold_id.lower()
    training = pl.read_parquet(fold_root / "training_player_league_seasons.parquet")
    forecast = pl.read_parquet(fold_root / "forecast_population.parquet")
    target = pl.read_parquet(fold_root / "target_players.parquet")
    return training, [int(value) for value in forecast["player_id"].to_list()], target


def _selection_rows(
    root: Path,
    earlier_folds: tuple[str, ...],
) -> list[dict[str, object]]:
    rows = []
    for half_life in HALF_LIFE_GRID:
        for prior_pa in PRIOR_PA_GRID:
            totals = {
                node.name: {"loss": 0.0, "events": 0}
                for node in NESTED_NODES
            }
            origin_records = []
            for origin in earlier_folds:
                training, player_ids, target = _fold_inputs(root, origin)
                cutoff = int(training["season"].max())
                predictions = predict_c0_nested_eb(
                    training,
                    player_ids,
                    predictor_cutoff_season=cutoff,
                    half_life_seasons=half_life,
                    component_prior_pa={node.name: prior_pa for node in NESTED_NODES},
                )
                for node in NESTED_NODES:
                    score = score_nested_component_log_loss(
                        predictions,
                        target,
                        component=node.name,
                    )
                    events = int(score["events"])
                    loss = float(score["event_log_loss"])
                    totals[node.name]["loss"] += loss * events
                    totals[node.name]["events"] += events
                    origin_records.append(
                        {
                            "origin_fold": origin,
                            "component": node.name,
                            "events": events,
                            "event_log_loss": loss,
                        }
                    )
            for node in NESTED_NODES:
                events = int(totals[node.name]["events"])
                rows.append(
                    {
                        "component": node.name,
                        "half_life_seasons": half_life,
                        "component_prior_pa": prior_pa,
                        "selection_events": events,
                        "event_log_loss": float(totals[node.name]["loss"]) / events,
                        "origin_count": len(earlier_folds),
                        "origin_detail_json": json.dumps(
                            [
                                record
                                for record in origin_records
                                if record["component"] == node.name
                            ],
                            separators=(",", ":"),
                            sort_keys=True,
                        ),
                    }
                )
    return rows


def main() -> int:
    args = _parse_args()
    fold_reports = []
    for index, fold_id in enumerate(FOLDS):
        earlier = FOLDS[:index]
        if earlier:
            scores = pl.DataFrame(_selection_rows(args.prescore_root, earlier))
            selected = select_component_hyperparameters(scores)
            score_artifact = write_canonical_parquet(
                scores,
                args.report_root / "tables" / fold_id.lower() / "component_grid_scores.parquet",
                table_name=f"hitter_v2_{fold_id.lower()}_component_grid_scores",
            ).as_record()
            selection_source = "earlier_origin_event_log_loss"
        else:
            scores = pl.DataFrame()
            selected = {
                node.name: {
                    **NO_ORIGIN_DEFAULT,
                    "event_log_loss": None,
                }
                for node in NESTED_NODES
            }
            score_artifact = None
            selection_source = "no_earlier_origin_literal_tie_default"
        fold_reports.append(
            {
                "fold_id": fold_id,
                "earlier_origin_folds": list(earlier),
                "selection_source": selection_source,
                "grid_rows": scores.height,
                "selected": selected,
                "grid_artifact": score_artifact,
            }
        )
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": 2,
        "status": "nested_component_training_origin_selection_complete",
        "candidate_scored_on_training_origins": True,
        "final_validation_scored": False,
        "protected_2026_opened": False,
        "grid": {
            "half_life_seasons": list(HALF_LIFE_GRID),
            "component_prior_pa": list(PRIOR_PA_GRID),
        },
        "tie_rule": (
            "within 1e-8 choose larger component prior PA, then longer half-life"
        ),
        "prescore_report_sha256": sha256_file(
            args.prescore_root.parent / "report.json"
        ),
        "folds": fold_reports,
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
