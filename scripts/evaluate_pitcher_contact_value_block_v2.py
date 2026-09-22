#!/usr/bin/env python3
"""Test detailed hit types against a complete next-season result-value target."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import gzip
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.hitter_target_architecture import (
    expanding_year_folds,
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.pitcher_contact_value import (
    build_full_mlb_pitcher_value_targets,
    build_pitcher_contact_features,
)
from universal_baseball.pitcher_model_tournament import run_pitcher_engine_fold
from universal_baseball.pitcher_value_panel import MODEL_ORIGINS, build_pitcher_value_panel
from universal_baseball.opportunity_history_source import SPORT_LEVEL
from universal_baseball.storage import write_canonical_parquet


DEFAULT_ENGINES = ("ridge", "catboost", "lightgbm")
TARGET_SEASONS = {year + 1 for year in MODEL_ORIGINS}


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-root", type=Path, required=True)
    parser.add_argument(
        "--base-panel-root",
        type=Path,
        default=Path("reports/generated/pitcher-value-panel-v2"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/pitcher-contact-value-block-v2"),
    )
    parser.add_argument("--engines", default=",".join(DEFAULT_ENGINES))
    return parser.parse_args()


def _integer(stat: dict[str, Any], field: str) -> int:
    value = stat.get(field)
    if value is None or str(value).strip() == "":
        raise ValueError(f"cached MLB pitching split missing {field}")
    numeric = float(str(value))
    if not numeric.is_integer() or numeric < 0:
        raise ValueError(f"invalid cached MLB pitching {field}: {value!r}")
    return int(numeric)


def _load_cached_mlb_contact(raw_root: Path) -> tuple[pl.DataFrame, list[Path]]:
    rows: list[dict[str, int]] = []
    paths = sorted(raw_root.glob("pitching-*.json"))
    if not paths:
        raise FileNotFoundError(f"no cached MLB pitching captures under {raw_root}")
    used: list[Path] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        splits = payload.get("stats", [{}])[0].get("splits", [])
        for split in splits:
            season = int(split.get("season") or path.name.split("-")[1])
            if season not in TARGET_SEASONS:
                continue
            stat = split.get("stat") or {}
            person = split.get("player") or split.get("person") or {}
            walks = _integer(stat, "baseOnBalls")
            intentional = _integer(stat, "intentionalWalks")
            if intentional > walks:
                raise ValueError("cached MLB pitching IBB exceeds BB")
            rows.append(
                {
                    "season": season,
                    "player_id": int(person["id"]),
                    "pitching_bf": _integer(stat, "battersFaced"),
                    "pitching_so": _integer(stat, "strikeOuts"),
                    "pitching_ubb": walks - intentional,
                    "pitching_hbp": _integer(stat, "hitBatsmen"),
                    "pitching_hits": _integer(stat, "hits"),
                    "pitching_doubles": _integer(stat, "doubles"),
                    "pitching_triples": _integer(stat, "triples"),
                    "pitching_hr": _integer(stat, "homeRuns"),
                }
            )
        if splits:
            used.append(path)
    result = pl.DataFrame(rows).group_by("season", "player_id").agg(
        pl.all().exclude("season", "player_id").sum()
    )
    if set(result["season"].unique()) != TARGET_SEASONS:
        missing = sorted(TARGET_SEASONS - set(result["season"].unique()))
        raise ValueError(f"cached MLB detailed outcomes missing seasons: {missing}")
    return result.sort("season", "player_id"), used


def _load_cached_affiliated_contact(root: Path) -> tuple[pl.DataFrame, list[Path]]:
    specifications = (
        (
            root / "affiliated-skill-source-2003-2007/captures",
            (2007,),
        ),
        (
            root / "affiliated-skill-source-2008-2017/captures",
            tuple(range(2008, 2018)),
        ),
        (
            root / "affiliated-skill-source-2018-2022/captures",
            (2018, 2019, 2021, 2022),
        ),
        (
            root / "affiliated-skill-source/captures",
            (2023, 2024),
        ),
    )
    rows: list[dict[str, int | str]] = []
    used: list[Path] = []
    for capture_root, years in specifications:
        for season in years:
            paths = sorted((capture_root / str(season)).glob("pitching-*.json.gz"))
            if not paths:
                raise FileNotFoundError(f"no cached affiliated pitching captures for {season}")
            for path in paths:
                with gzip.open(path, "rt", encoding="utf-8") as handle:
                    payload = json.load(handle)
                splits = payload.get("stats", [{}])[0].get("splits", [])
                for split in splits:
                    stat = split.get("stat") or {}
                    person = split.get("player") or split.get("person") or {}
                    sport_id = int((split.get("sport") or {})["id"])
                    if sport_id not in SPORT_LEVEL:
                        raise ValueError(f"unsupported affiliated sport id {sport_id}")
                    walks = _integer(stat, "baseOnBalls")
                    intentional = _integer(stat, "intentionalWalks")
                    if intentional > walks:
                        raise ValueError("cached affiliated pitching IBB exceeds BB")
                    rows.append(
                        {
                            "season": season,
                            "player_id": int(person["id"]),
                            "level_group": SPORT_LEVEL[sport_id],
                            "batters_faced": _integer(stat, "battersFaced"),
                            "strike_outs": _integer(stat, "strikeOuts"),
                            "base_on_balls": walks,
                            "intentional_walks": intentional,
                            "hit_batters": _integer(stat, "hitBatsmen"),
                            "hits": _integer(stat, "hits"),
                            "doubles": _integer(stat, "doubles"),
                            "triples": _integer(stat, "triples"),
                            "home_runs": _integer(stat, "homeRuns"),
                        }
                    )
                used.append(path)
    return pl.DataFrame(rows), used


def _score(panel: pl.DataFrame, engine: str) -> pl.DataFrame:
    folds = expanding_year_folds(panel["origin_year"].unique().to_list(), minimum_train_years=8)
    predictions = [
        run_pitcher_engine_fold(panel, fold, engine)[0]
        for fold in folds
    ]
    return pl.concat(predictions).sort("origin_year", "player_id")


def _fold_metrics(comparison: pl.DataFrame) -> list[dict[str, float | int]]:
    rows: list[dict[str, float | int]] = []
    for origin, fold in comparison.partition_by("origin_year", as_dict=True).items():
        rows.append(
            {
                "origin_year": int(origin[0]),
                "base_rmse": regression_metrics(
                    fold["actual_component_war"].to_numpy(),
                    fold["prediction_base"].to_numpy(),
                )["rmse"],
                "detailed_rmse": regression_metrics(
                    fold["actual_component_war"].to_numpy(),
                    fold["prediction_detailed"].to_numpy(),
                )["rmse"],
            }
        )
    return rows


def main() -> int:
    args = _args()
    stat_features = pl.read_parquet(
        args.base_panel_root / "tables/pitcher-stat-features.parquet"
    )
    affiliated, affiliated_capture_paths = _load_cached_affiliated_contact(
        args.generated_root
    )
    contact_features = build_pitcher_contact_features(affiliated)
    detailed_features = stat_features.join(
        contact_features, on=["season", "player_id"], how="left", validate="1:1"
    )
    cached, capture_paths = _load_cached_mlb_contact(
        args.generated_root / "career-mlb-outcome-inventory-2009-2025/raw"
    )
    targets = build_full_mlb_pitcher_value_targets(cached)
    base_panel = build_pitcher_value_panel(stat_features, targets, origins=MODEL_ORIGINS)
    detailed_panel = build_pitcher_value_panel(
        detailed_features, targets, origins=MODEL_ORIGINS
    )

    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    engines = [value.strip() for value in args.engines.split(",") if value.strip()]
    report: dict[str, Any] = {
        "schema_version": "0.1",
        "status": "pitcher_contact_value_block_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "target": "next-season zero-inclusive full hit-type MLB pitcher result value",
        "target_note": (
            "Descriptive full result value includes fielding and park effects; it is a "
            "test target, not yet the final definition of pitcher talent."
        ),
        "feature_block": [
            "season/level-relative singles allowed",
            "doubles allowed",
            "triples allowed",
            "non-hit other batters faced",
        ],
        "rows": base_panel.height,
        "target_rows": targets.height,
        "cached_capture_count": len(capture_paths),
        "cached_affiliated_capture_count": len(affiliated_capture_paths),
        "engines": {},
    }
    for engine in engines:
        print(f"starting contact-value engine {engine}", flush=True)
        base = _score(base_panel, engine)
        detailed = _score(detailed_panel, engine)
        keys = ["origin_year", "target_season", "player_id"]
        comparison = base.select(
            *keys,
            "actual_component_war",
            pl.col("predicted_component_war").alias("prediction_base"),
        ).join(
            detailed.select(
                *keys,
                pl.col("predicted_component_war").alias("prediction_detailed"),
            ),
            on=keys,
            validate="1:1",
        )
        actual = comparison["actual_component_war"].to_numpy()
        base_prediction = comparison["prediction_base"].to_numpy()
        detailed_prediction = comparison["prediction_detailed"].to_numpy()
        report["engines"][engine] = {
            "base": regression_metrics(actual, base_prediction),
            "detailed_contact": regression_metrics(actual, detailed_prediction),
            "detailed_minus_base": paired_cluster_rmse_delta(
                actual,
                detailed_prediction,
                base_prediction,
                comparison["player_id"].to_numpy(),
                bootstrap_samples=5_000,
            ),
            "folds": _fold_metrics(comparison),
        }
        write_canonical_parquet(
            comparison,
            table_root / f"{engine}-predictions.parquet",
            table_name=f"pitcher_contact_value_v2_{engine}_predictions",
        )
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["engines"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
