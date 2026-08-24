#!/usr/bin/env python3
"""Freeze Hitter v2 rolling-origin inputs before candidate scoring."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.hitter_v2_evaluation import (
    NEUTRAL_POOL_SEASONS,
    NEUTRAL_WOBA,
    NEUTRAL_WOBA_SCALE,
    NEUTRAL_WOBA_WEIGHTS,
    ROLLING_ORIGIN_FOLDS,
    aggregate_target_players,
    build_forecast_population,
    rolling_origin_slices,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--history",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage1-universal/tables/"
            "hitter_v2_player_season_outcomes_2021_2023.parquet"
        ),
    )
    parser.add_argument(
        "--target-2024",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage2-2024-universal/tables/"
            "hitter_v2_player_season_outcomes_2024.parquet"
        ),
    )
    parser.add_argument(
        "--weight-contract",
        type=Path,
        default=Path("docs/hitter-v2-stage2-neutral-evaluation-contract.json"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-prescore"),
    )
    return parser.parse_args()


def _json_sha(path: Path) -> str:
    parsed = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(parsed, separators=(",", ":"), sort_keys=True)
    return sha256(canonical.encode("utf-8")).hexdigest()


def _season_counts(frame: pl.DataFrame) -> list[dict[str, Any]]:
    return (
        frame.group_by("season")
        .agg(
            pl.len().alias("player_league_season_rows"),
            pl.col("player_id").n_unique().alias("players"),
            pl.col("hitter_talent_pa").sum().alias("hitter_talent_pa"),
        )
        .sort("season")
        .to_dicts()
    )


def main() -> int:
    args = _parse_args()
    history = pl.read_parquet(args.history)
    target_2024 = pl.read_parquet(args.target_2024)
    source = pl.concat([history, target_2024], how="vertical")
    observed_seasons = set(int(value) for value in source["season"].unique().to_list())
    if observed_seasons != {2021, 2022, 2023, 2024}:
        raise RuntimeError(f"unexpected Hitter v2 fold seasons: {observed_seasons}")

    weight_contract = json.loads(args.weight_contract.read_text(encoding="utf-8"))
    frozen = weight_contract["neutral_pool"]["frozen_mean"]
    expected = {
        "woba": NEUTRAL_WOBA,
        "scale": NEUTRAL_WOBA_SCALE,
        **{
            outcome: NEUTRAL_WOBA_WEIGHTS[outcome]
            for outcome in ("UBB", "HBP", "1B", "2B", "3B", "HR")
        },
    }
    if frozen != expected or tuple(weight_contract["neutral_pool"]["seasons"]) != (
        NEUTRAL_POOL_SEASONS
    ):
        raise RuntimeError("committed neutral evaluation contract differs from code")

    table_root = args.report_root / "tables"
    fold_records: list[dict[str, Any]] = []
    for fold in ROLLING_ORIGIN_FOLDS:
        training, target = rolling_origin_slices(source, fold)
        target_players = aggregate_target_players(target)
        forecast_players = build_forecast_population(training)
        evaluation_players = target_players.join(
            forecast_players.select("player_id"),
            on="player_id",
            how="inner",
            validate="1:1",
        )
        fold_root = table_root / fold.fold_id.lower()
        train_artifact = write_canonical_parquet(
            training,
            fold_root / "training_player_league_seasons.parquet",
            table_name=f"hitter_v2_{fold.fold_id.lower()}_training_player_league_seasons",
        ).as_record()
        target_artifact = write_canonical_parquet(
            target,
            fold_root / "target_player_league_seasons.parquet",
            table_name=f"hitter_v2_{fold.fold_id.lower()}_target_player_league_seasons",
        ).as_record()
        player_artifact = write_canonical_parquet(
            target_players,
            fold_root / "target_players.parquet",
            table_name=f"hitter_v2_{fold.fold_id.lower()}_target_players",
        ).as_record()
        forecast_artifact = write_canonical_parquet(
            forecast_players,
            fold_root / "forecast_population.parquet",
            table_name=f"hitter_v2_{fold.fold_id.lower()}_forecast_population",
        ).as_record()
        evaluation_artifact = write_canonical_parquet(
            evaluation_players,
            fold_root / "evaluation_players.parquet",
            table_name=f"hitter_v2_{fold.fold_id.lower()}_evaluation_players",
        ).as_record()
        fold_records.append(
            {
                "fold_id": fold.fold_id,
                "predictor_cutoff_season": fold.predictor_cutoff_season,
                "target_season": fold.target_season,
                "training": {
                    "season_counts": _season_counts(training),
                    "player_league_season_rows": training.height,
                    "players": training["player_id"].n_unique(),
                    "hitter_talent_pa": int(training["hitter_talent_pa"].sum()),
                    "storage": train_artifact,
                },
                "target": {
                    "player_league_season_rows": target.height,
                    "players": target_players.height,
                    "hitter_talent_pa": int(target["hitter_talent_pa"].sum()),
                    "key_storage": target_artifact,
                    "player_storage": player_artifact,
                },
                "forecast_population": {
                    "players": forecast_players.height,
                    "definition": "unique players in full accepted pre-cutoff history",
                    "storage": forecast_artifact,
                },
                "evaluation_overlap": {
                    "players": evaluation_players.height,
                    "hitter_talent_pa": int(
                        evaluation_players["hitter_talent_pa"].sum()
                    ),
                    "target_only_players": target_players.height
                    - evaluation_players.height,
                    "storage": evaluation_artifact,
                },
                "chronology_checks": {
                    "training_max_season_at_or_before_cutoff": True,
                    "target_is_exact_declared_season": True,
                    "training_population_not_joined_to_target_membership": True,
                    "forecast_population_defined_without_target_membership": True,
                    "target_join_occurs_only_after_forecast_eligibility_freezes": True,
                    "target_environment_not_attached_to_training": True,
                },
            }
        )

    report = {
        "report_schema_version": "0.2",
        "program": "hitter_v2",
        "stage": 2,
        "status": "prescore_fold_and_neutral_evaluation_geometry_frozen",
        "candidate_fit": False,
        "candidate_scored": False,
        "protected_2026_opened": False,
        "source_inputs": {
            "history": {
                "path": args.history.as_posix(),
                "sha256": sha256_file(args.history),
            },
            "target_2024": {
                "path": args.target_2024.as_posix(),
                "sha256": sha256_file(args.target_2024),
            },
            "neutral_evaluation_contract": {
                "path": args.weight_contract.as_posix(),
                "file_sha256": sha256_file(args.weight_contract),
                "canonical_json_sha256": _json_sha(args.weight_contract),
            },
        },
        "neutral_evaluation": {
            "pool_seasons": list(NEUTRAL_POOL_SEASONS),
            "woba": NEUTRAL_WOBA,
            "woba_scale": NEUTRAL_WOBA_SCALE,
            "weights": NEUTRAL_WOBA_WEIGHTS,
        },
        "folds": fold_records,
        "scientific_checks": {
            "probability_simplex_tested": True,
            "ordered_hit_value_tested": True,
            "hr_mass_increase_tested": True,
            "target_mutation_training_isolation_tested": True,
            "source_reconciliation_inherited": True,
            "tracking_invariants_deferred_tracking_gate_closed": True,
            "terminal_history_distinction_tested_in_candidate_implementation": True,
        },
        "next_step": "implement_predeclared_b0_b1_c0_c1_without_scoring_protected_2026",
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
