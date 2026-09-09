#!/usr/bin/env python3
"""Score current hitters and pitchers with direct horizon 2-4 packages."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.opportunity_history_source import build_opportunity_snapshots
from universal_baseball.opportunity_model_v2 import (
    build_universal_hitter_opportunity_predictors,
)
from universal_baseball.pitcher_opportunity_model_v2 import (
    build_universal_pitcher_opportunity_predictors,
)
from universal_baseball.playing_time_confirmation import load_frozen_playing_time_fit
from universal_baseball.playing_time_model import (
    build_playing_time_design,
    predict_playing_time_hurdle,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


HORIZONS = (2, 3, 4)
MODEL_STATUS = "provisional_direct_multihorizon_not_2026_confirmed"


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--current-source-root", type=Path, required=True)
    parser.add_argument("--membership-root", type=Path, required=True)
    parser.add_argument(
        "--package-root",
        type=Path,
        default=Path(
            "model_artifacts/opportunity-multihorizon-v2-development-2026-09-09"
        ),
    )
    parser.add_argument(
        "--fallback-root",
        type=Path,
        default=Path("reports/generated/current-opportunity-paths/2026-09-08/tables"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-opportunity-multihorizon-v2"),
    )
    return parser.parse_args()


def _fit(
    package_root: Path,
    selection: dict[str, object],
    *,
    component: str,
    horizon: int,
):
    root = package_root / "tables" / component / f"horizon-{horizon}"
    return load_frozen_playing_time_fit(
        pl.read_parquet(root / "selected_coefficients.parquet"),
        pl.read_parquet(root / "selected_standardization.parquet"),
        form=str(selection["selected_model"]),
        expected_nb_alpha=float(selection["selected_nb_alpha"]),
        participation_training_players=int(selection["final_training_players"]),
        positive_training_players=int(selection["final_positive_players"]),
    )


def _summary(comparison: pl.DataFrame, *, unit: str) -> list[dict[str, object]]:
    difference = f"expected_mlb_{unit}_difference"
    return (
        comparison.group_by("horizon")
        .agg(
            pl.len().alias("players"),
            pl.col(f"predicted_expected_mlb_{unit}").mean().alias("v2_mean"),
            pl.col(f"fallback_expected_mlb_{unit}").mean().alias("fallback_mean"),
            pl.col(difference).mean().alias("mean_difference"),
            pl.col(difference).median().alias("median_difference"),
        )
        .sort("horizon")
        .to_dicts()
    )


def main() -> int:
    args = _args()
    tables = args.current_source_root / "tables" / str(args.as_of_date.year)
    roster_path = tables / "full_roster_details.parquet"
    stats_path = tables / "affiliated_season_stats.parquet"
    membership_path = (
        args.membership_root / "tables" / "historical_40man_membership.parquet"
    )
    stats = pl.read_parquet(stats_path)
    hitters, pitchers = build_opportunity_snapshots(pl.read_parquet(roster_path), stats)
    membership = pl.read_parquet(membership_path)
    hitter_predictors = build_universal_hitter_opportunity_predictors(
        hitters, stats, membership, snapshot_year=args.as_of_date.year
    )
    pitcher_predictors = build_universal_pitcher_opportunity_predictors(
        pitchers, stats, membership, snapshot_year=args.as_of_date.year
    )
    package_report = json.loads(
        (args.package_root / "report.json").read_text(encoding="utf-8")
    )
    selection = {
        (str(row["component"]), int(row["horizon"])): row
        for row in package_report["selection"]
    }
    hitter_frames = []
    pitcher_frames = []
    for component, predictors, output_frames in (
        ("hitter", hitter_predictors, hitter_frames),
        ("pitcher", pitcher_predictors, pitcher_frames),
    ):
        for horizon in HORIZONS:
            fit = _fit(
                args.package_root,
                selection[(component, horizon)],
                component=component,
                horizon=horizon,
            )
            predicted = predict_playing_time_hurdle(
                fit, build_playing_time_design(predictors, form=fit.form)
            )
            if component == "pitcher":
                predicted = predicted.rename(
                    {
                        "predicted_any_mlb_pa_probability": (
                            "predicted_any_mlb_bf_probability"
                        ),
                        "predicted_positive_mlb_pa_mean": (
                            "predicted_positive_mlb_bf_mean"
                        ),
                        "predicted_expected_mlb_pa": "predicted_expected_mlb_bf",
                    }
                )
            output_frames.append(
                predicted.with_columns(
                    pl.lit(horizon).cast(pl.Int64).alias("horizon"),
                    pl.lit(f"{fit.form}:direct_h{horizon}").alias("model_id"),
                    pl.lit(fit.nb_alpha).alias("model_nb_alpha"),
                    pl.lit(MODEL_STATUS).alias("model_status"),
                )
            )
    hitter_predictions = pl.concat(hitter_frames).sort(["player_id", "horizon"])
    pitcher_predictions = pl.concat(pitcher_frames).sort(["player_id", "horizon"])
    hitter_comparison = hitter_predictions.join(
        pl.read_parquet(args.fallback_root / "hitter_opportunity_paths.parquet")
        .filter(pl.col("horizon").is_in(HORIZONS))
        .select(
            "player_id",
            "horizon",
            pl.col("expected_mlb_pa").alias("fallback_expected_mlb_pa"),
        ),
        on=["player_id", "horizon"],
        validate="1:1",
    ).with_columns(
        (pl.col("predicted_expected_mlb_pa") - pl.col("fallback_expected_mlb_pa")).alias(
            "expected_mlb_pa_difference"
        )
    )
    pitcher_comparison = pitcher_predictions.join(
        pl.read_parquet(args.fallback_root / "pitcher_opportunity_paths.parquet")
        .filter(pl.col("horizon").is_in(HORIZONS))
        .select(
            "player_id",
            "horizon",
            pl.col("expected_mlb_bf").alias("fallback_expected_mlb_bf"),
        ),
        on=["player_id", "horizon"],
        validate="1:1",
    ).with_columns(
        (pl.col("predicted_expected_mlb_bf") - pl.col("fallback_expected_mlb_bf")).alias(
            "expected_mlb_bf_difference"
        )
    )
    output = args.output_root / args.as_of_date.isoformat()
    output.mkdir(parents=True, exist_ok=True)
    storage = {
        "hitter_predictions": write_canonical_parquet(
            hitter_predictions,
            output / "hitter-predictions.parquet",
            table_name="current_hitter_opportunity_multihorizon_v2_predictions",
        ).as_record(),
        "pitcher_predictions": write_canonical_parquet(
            pitcher_predictions,
            output / "pitcher-predictions.parquet",
            table_name="current_pitcher_opportunity_multihorizon_v2_predictions",
        ).as_record(),
        "hitter_comparison": write_canonical_parquet(
            hitter_comparison,
            output / "hitter-fallback-comparison.parquet",
            table_name="current_hitter_opportunity_multihorizon_v2_comparison",
        ).as_record(),
        "pitcher_comparison": write_canonical_parquet(
            pitcher_comparison,
            output / "pitcher-fallback-comparison.parquet",
            table_name="current_pitcher_opportunity_multihorizon_v2_comparison",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "current_opportunity_multihorizon_v2_provisional_score",
        "as_of_date": args.as_of_date.isoformat(),
        "horizons": list(HORIZONS),
        "model_status": MODEL_STATUS,
        "hitter": _summary(hitter_comparison, unit="pa"),
        "pitcher": _summary(pitcher_comparison, unit="bf"),
        "source_hashes": {
            "roster": sha256_file(roster_path),
            "stats": sha256_file(stats_path),
            "membership": sha256_file(membership_path),
            "package_report": sha256_file(args.package_root / "report.json"),
        },
        "boundary": {
            "direct_not_recursive": True,
            "protected_2026_outcomes_used_for_evaluation": False,
            "current_2026_evidence_used_as_predictor": True,
            "team_depth_or_future_team_used": False,
            "horizons_5_6_retain_historical_fallback": True,
            "production_promotion": False,
        },
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

