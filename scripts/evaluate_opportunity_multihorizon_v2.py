#!/usr/bin/env python3
"""Run the frozen direct opportunity tests for horizons two through four."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.opportunity_model_v2 import (
    build_universal_hitter_opportunity_fold,
)
from universal_baseball.opportunity_multihorizon_v2 import (
    MultiHorizonEvaluation,
    evaluate_multi_horizon_forms,
)
from universal_baseball.pitcher_opportunity_model_v2 import (
    build_universal_pitcher_opportunity_fold,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


ELIGIBLE_SNAPSHOTS = {
    2: (*range(2009, 2018), 2021, 2022, 2023),
    3: (*range(2009, 2017), 2021, 2022),
    4: (*range(2009, 2016), 2021),
}
EVALUATION_SNAPSHOTS = {
    2: (2017, 2021, 2022, 2023),
    3: (2015, 2016, 2021, 2022),
    4: (2013, 2014, 2015, 2021),
}
BF_METRIC_NAMES = {
    "unconditional_mlb_pa_mae": "unconditional_mlb_bf_mae",
    "unconditional_mlb_pa_rmse": "unconditional_mlb_bf_rmse",
    "observed_mean_mlb_pa": "observed_mean_mlb_bf",
    "predicted_mean_mlb_pa": "predicted_mean_mlb_bf",
}


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pre2020-source-root",
        type=Path,
        default=Path("reports/generated/opportunity-history-sources-pre2020"),
    )
    parser.add_argument(
        "--modern-source-root",
        type=Path,
        default=Path("reports/generated/opportunity-history-sources-v2"),
    )
    parser.add_argument(
        "--pre2020-membership-root",
        type=Path,
        default=Path("reports/generated/opportunity-40man-pre2020"),
    )
    parser.add_argument(
        "--modern-membership-root",
        type=Path,
        default=Path("reports/generated/opportunity-40man-history"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/opportunity-multihorizon-v2-development"),
    )
    return parser.parse_args()


def _stats_path(args: argparse.Namespace, year: int) -> Path:
    root = args.pre2020_source_root if year <= 2017 else args.modern_source_root
    return root / "tables" / str(year) / "affiliated_season_stats.parquet"


def _build_folds(
    args: argparse.Namespace,
    *,
    component: str,
    horizon: int,
    snapshots: pl.DataFrame,
    membership: pl.DataFrame,
) -> list:
    folds = []
    for snapshot_year in ELIGIBLE_SNAPSHOTS[horizon]:
        target_year = snapshot_year + horizon
        builder = (
            build_universal_hitter_opportunity_fold
            if component == "hitter"
            else build_universal_pitcher_opportunity_fold
        )
        folds.append(
            builder(
                snapshots,
                pl.read_parquet(_stats_path(args, snapshot_year)),
                pl.read_parquet(_stats_path(args, target_year)),
                membership,
                snapshot_year=snapshot_year,
                target_year=target_year,
            )
        )
    return folds


def _metric_frames(
    evaluations: list[MultiHorizonEvaluation], *, kind: str
) -> pl.DataFrame:
    frames = []
    for result in evaluations:
        frame = result.fold_metrics if kind == "fold" else result.pooled_metrics
        if result.component == "pitcher":
            frame = frame.rename(
                {old: new for old, new in BF_METRIC_NAMES.items() if old in frame.columns}
            )
        frames.append(frame)
    return pl.concat(frames, how="diagonal_relaxed").sort(
        ["component", "horizon", "form"]
    )


def main() -> int:
    args = _args()
    pre_tables = args.pre2020_source_root / "tables"
    modern_tables = args.modern_source_root / "tables"
    hitter_snapshots = pl.concat(
        [
            pl.read_parquet(pre_tables / "hitter_snapshots.parquet").filter(
                pl.col("snapshot_year") >= 2009
            ),
            pl.read_parquet(modern_tables / "hitter_snapshots.parquet").filter(
                pl.col("snapshot_year") >= 2021
            ),
        ]
    )
    pitcher_snapshots = pl.concat(
        [
            pl.read_parquet(pre_tables / "pitcher_snapshots.parquet").filter(
                pl.col("snapshot_year") >= 2009
            ),
            pl.read_parquet(modern_tables / "pitcher_snapshots.parquet").filter(
                pl.col("snapshot_year") >= 2021
            ),
        ]
    )
    membership = pl.concat(
        [
            pl.read_parquet(
                args.pre2020_membership_root
                / "tables/historical_40man_membership.parquet"
            ).filter(pl.col("season") >= 2009),
            pl.read_parquet(
                args.modern_membership_root
                / "tables/historical_40man_membership.parquet"
            ).filter(pl.col("season") >= 2021),
        ]
    )
    evaluations = []
    for component, snapshots in (
        ("hitter", hitter_snapshots),
        ("pitcher", pitcher_snapshots),
    ):
        for horizon in (2, 3, 4):
            evaluations.append(
                evaluate_multi_horizon_forms(
                    component,
                    _build_folds(
                        args,
                        component=component,
                        horizon=horizon,
                        snapshots=snapshots,
                        membership=membership,
                    ),
                    horizon=horizon,
                    evaluation_snapshot_years=EVALUATION_SNAPSHOTS[horizon],
                )
            )

    args.output_root.mkdir(parents=True, exist_ok=True)
    tables = args.output_root / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    storage = {
        "fold_metrics": write_canonical_parquet(
            _metric_frames(evaluations, kind="fold"),
            tables / "fold_metrics.parquet",
            table_name="opportunity_multihorizon_v2_fold_metrics",
        ).as_record(),
        "pooled_metrics": write_canonical_parquet(
            _metric_frames(evaluations, kind="pooled"),
            tables / "pooled_metrics.parquet",
            table_name="opportunity_multihorizon_v2_pooled_metrics",
        ).as_record(),
    }
    package_storage = {}
    for result in evaluations:
        if result.final_fit is None:
            continue
        package = tables / result.component / f"horizon-{result.horizon}"
        package.mkdir(parents=True, exist_ok=True)
        package_storage[f"{result.component}_horizon_{result.horizon}"] = {
            "coefficients": write_canonical_parquet(
                result.final_fit.coefficient_frame(),
                package / "selected_coefficients.parquet",
                table_name=(
                    f"{result.component}_opportunity_v2_h{result.horizon}_coefficients"
                ),
            ).as_record(),
            "standardization": write_canonical_parquet(
                result.final_fit.standardization_frame(),
                package / "selected_standardization.parquet",
                table_name=(
                    f"{result.component}_opportunity_v2_h{result.horizon}_standardization"
                ),
            ).as_record(),
        }
    storage["selected_packages"] = package_storage
    report = {
        "report_schema_version": "0.1",
        "gate": "opportunity_multihorizon_v2_rolling_development",
        "status": "development_only_not_production_confirmed",
        "contract": "docs/opportunity-multihorizon-v2-development-contract.md",
        "evaluated_horizons": [2, 3, 4],
        "source_gate_failed_horizons": {
            "5": "only one chronology-safe evaluation fold",
            "6": "no chronology-safe evaluation fold",
        },
        "selection": [
            {
                "component": result.component,
                "horizon": result.horizon,
                **result.selection,
                "final_training_players": (
                    result.final_fit.participation_training_players
                    if result.final_fit is not None
                    else None
                ),
                "final_positive_players": (
                    result.final_fit.positive_training_players
                    if result.final_fit is not None
                    else None
                ),
                "selected_nb_alpha": (
                    result.final_fit.nb_alpha if result.final_fit is not None else None
                ),
            }
            for result in evaluations
        ],
        "evaluation_snapshots": {
            str(horizon): list(years)
            for horizon, years in EVALUATION_SNAPSHOTS.items()
        },
        "source_hashes": {
            "pre2020_report": sha256_file(args.pre2020_source_root / "report.json"),
            "modern_report": sha256_file(args.modern_source_root / "report.json"),
            "pre2020_membership": sha256_file(
                args.pre2020_membership_root
                / "tables/historical_40man_membership.parquet"
            ),
            "modern_membership": sha256_file(
                args.modern_membership_root
                / "tables/historical_40man_membership.parquet"
            ),
        },
        "boundary": {
            "direct_not_recursive": True,
            "protected_2026_outcomes_used": False,
            "team_depth_or_future_team_used": False,
            "horizons_5_6_retain_incumbent": True,
            "production_promotion": False,
        },
        "storage": storage,
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "gate": report["gate"],
                "selection": report["selection"],
                "source_gate_failed_horizons": report[
                    "source_gate_failed_horizons"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

