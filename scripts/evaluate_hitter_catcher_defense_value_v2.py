#!/usr/bin/env python3
"""Test direct public catcher defense inside the clean-slate hitter value stack.

The test is intentionally independent of the rejected general-range defense layer.
It uses only source-season public throwing, blocking, and framing results, the
already-selected hitter workload forecast, and target-season public catcher results.
"""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_target_architecture import (
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


BASE_PATH = Path(
    "reports/generated/hitter-value-components-chronological-v2/"
    "chronological-predictions.parquet"
)
PANEL_PATH = Path(
    "reports/generated/hitter-value-panel-v2/tables/modeling-panel.parquet"
)
OLD_CATCHER_PATH = Path(
    "C:/Users/ramav/Documents/Codex/2026-08-19/i/work/centering-inputs/"
    "catcher-repair-source/tables/catcher_repair_development_targets_2022_2024.parquet"
)
OLD_FRAMING_PATH = Path(
    "C:/Users/ramav/Documents/Codex/2026-08-19/i/work/centering-inputs/"
    "framing-repair-source/tables/catcher_framing_targets_2022_2024.parquet"
)
THROWING_2025_PATH = Path(
    "reports/generated/defense-v1-2025-target-source/tables/"
    "catcher_throwing_targets_2025.parquet"
)
BLOCKING_2025_PATH = Path(
    "reports/generated/defense-v1-2025-target-source/tables/"
    "catcher_blocking_targets_2025.parquet"
)
FRAMING_2025_PATH = Path(
    "reports/generated/hitter-catcher-defense-value-v2/source/framing-2025/"
    "tables/catcher_framing_targets_2025.parquet"
)
CONVERSION_PATH = Path(
    "docs/player-value-v1-defense-native-run-conversion-parameters.json"
)
OUTPUT_ROOT = Path("reports/generated/hitter-catcher-defense-value-v2")
TARGET_YEARS = (2023, 2024, 2025)
COMPONENTS = ("throwing", "blocking", "framing")
RUNS_PER_WIN = 10.0
PRIMARY_PREDICTION = (
    "prediction_catcher_war_chronological_skill_pa_scaled_opportunity"
)


def _public_component_history() -> pl.DataFrame:
    catcher = pl.read_parquet(OLD_CATCHER_PATH).select(
        pl.col("target_year").alias("season"),
        pl.col("component"),
        pl.col("player_id"),
        pl.when(pl.col("component") == "throwing")
        .then(pl.col("sb_attempts"))
        .otherwise(pl.col("pitches"))
        .alias("opportunity"),
        pl.col("target_z").alias("skill_z"),
    )
    framing = pl.read_parquet(OLD_FRAMING_PATH).select(
        pl.col("target_year").alias("season"),
        pl.lit("framing").alias("component"),
        "player_id",
        pl.col("pitches").alias("opportunity"),
        pl.col("target_z").alias("skill_z"),
    )
    throwing_2025 = pl.read_parquet(THROWING_2025_PATH).select(
        pl.col("season"),
        pl.lit("throwing").alias("component"),
        "player_id",
        pl.col("sb_attempts").alias("opportunity"),
        pl.col("throwing_target_z").alias("skill_z"),
    )
    blocking_2025 = pl.read_parquet(BLOCKING_2025_PATH).select(
        pl.col("season"),
        pl.lit("blocking").alias("component"),
        "player_id",
        pl.col("pitches").alias("opportunity"),
        pl.col("blocking_target_z").alias("skill_z"),
    )
    framing_2025 = pl.read_parquet(FRAMING_2025_PATH).select(
        pl.col("target_year").alias("season"),
        pl.lit("framing").alias("component"),
        "player_id",
        pl.col("pitches").alias("opportunity"),
        pl.col("target_z").alias("skill_z"),
    )
    history = pl.concat(
        [catcher, framing, throwing_2025, blocking_2025, framing_2025],
        how="vertical_relaxed",
    ).sort(["season", "component", "player_id"])
    if history.group_by("season", "component", "player_id").len().filter(
        pl.col("len") != 1
    ).height:
        raise RuntimeError("public catcher history violates season/component/player grain")
    if history.filter(
        pl.col("opportunity").is_null()
        | ~pl.col("opportunity").is_finite()
        | (pl.col("opportunity") <= 0)
        | pl.col("skill_z").is_null()
        | ~pl.col("skill_z").is_finite()
    ).height:
        raise RuntimeError("public catcher history contains invalid values")
    return history


def _transition_history(history: pl.DataFrame) -> pl.DataFrame:
    source = history.select(
        pl.col("season").alias("origin_year"),
        "component",
        "player_id",
        pl.col("skill_z").alias("source_skill_z"),
    )
    target = history.select(
        (pl.col("season") - 1).alias("origin_year"),
        "component",
        "player_id",
        pl.col("skill_z").alias("target_skill_z"),
    )
    return source.join(
        target,
        on=["origin_year", "component", "player_id"],
        how="inner",
        validate="1:1",
    ).sort(["origin_year", "component", "player_id"])


def _chronological_slopes(transitions: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for target_year in TARGET_YEARS:
        origin_year = target_year - 1
        for component in COMPONENTS:
            prior = transitions.filter(
                (pl.col("component") == component)
                & (pl.col("origin_year") < origin_year)
            )
            if prior.is_empty():
                slope = 1.0
                source = "cold_start_raw_persistence"
            else:
                x = prior["source_skill_z"].to_numpy()
                y = prior["target_skill_z"].to_numpy()
                denominator = float(np.dot(x, x))
                slope = 0.0 if denominator <= 1e-12 else float(np.dot(x, y) / denominator)
                slope = float(np.clip(slope, 0.0, 1.0))
                source = "earlier_transitions_only_through_origin_slope"
            rows.append(
                {
                    "origin_year": origin_year,
                    "target_year": target_year,
                    "component": component,
                    "chronological_skill_slope": slope,
                    "slope_training_rows": prior.height,
                    "slope_source": source,
                }
            )
    return pl.DataFrame(rows)


def _component_frame(
    history: pl.DataFrame,
    slopes: pl.DataFrame,
    base: pl.DataFrame,
    panel: pl.DataFrame,
    run_rates: dict[str, float],
) -> pl.DataFrame:
    source = history.filter(pl.col("season").is_in([year - 1 for year in TARGET_YEARS])).select(
        pl.col("season").alias("origin_year"),
        "component",
        "player_id",
        pl.col("opportunity").alias("source_opportunity"),
        pl.col("skill_z").alias("source_skill_z"),
    )
    target = history.filter(pl.col("season").is_in(TARGET_YEARS)).select(
        (pl.col("season") - 1).alias("origin_year"),
        "component",
        "player_id",
        pl.col("opportunity").alias("target_opportunity"),
        pl.col("skill_z").alias("target_skill_z"),
    )
    population = base.select(
        "origin_year",
        "player_id",
        "player_stage",
        "actual_partial_war",
        "prediction_selected_partial_war",
        "prediction_candidate_expected_pa",
    ).filter(pl.col("origin_year").is_in([year - 1 for year in TARGET_YEARS]))
    current_pa = panel.select(
        "origin_year",
        "player_id",
        pl.col("lag0__pa_level__MLB").cast(pl.Float64).alias("source_mlb_pa"),
    )
    skeleton = population.select("origin_year", "player_id").join(
        pl.DataFrame({"component": list(COMPONENTS)}), how="cross"
    )
    frame = (
        skeleton.join(source, on=["origin_year", "component", "player_id"], how="left")
        .join(target, on=["origin_year", "component", "player_id"], how="left")
        .join(slopes, on=["origin_year", "component"], how="left", validate="m:1")
        .join(
            population.select(
                "origin_year", "player_id", "prediction_candidate_expected_pa"
            ),
            on=["origin_year", "player_id"],
            how="left",
            validate="m:1",
        )
        .join(
            current_pa,
            on=["origin_year", "player_id"],
            how="left",
            validate="m:1",
        )
        .with_columns(
            pl.col("source_mlb_pa").fill_null(0.0),
            pl.col("source_opportunity").fill_null(0.0),
            pl.col("source_skill_z").fill_null(0.0),
            pl.col("target_opportunity").fill_null(0.0),
            pl.col("target_skill_z").fill_null(0.0),
            pl.col("component")
            .replace_strict(run_rates, return_dtype=pl.Float64)
            .alias("run_rate_per_z_opportunity"),
        )
        .with_columns(
            pl.when(pl.col("source_mlb_pa") > 0)
            .then(
                pl.col("source_opportunity")
                * pl.col("prediction_candidate_expected_pa")
                / pl.col("source_mlb_pa")
            )
            .otherwise(0.0)
            .alias("prediction_opportunity_pa_scaled"),
            pl.col("source_opportunity").alias("prediction_opportunity_raw"),
            (
                pl.col("chronological_skill_slope") * pl.col("source_skill_z")
            ).alias("prediction_skill_z_chronological"),
            pl.col("source_skill_z").alias("prediction_skill_z_raw"),
        )
        .with_columns(
            (
                0.5
                * (
                    pl.col("prediction_opportunity_raw")
                    + pl.col("prediction_opportunity_pa_scaled")
                )
            ).alias("prediction_opportunity_hybrid"),
            (
                pl.col("target_skill_z")
                * pl.col("target_opportunity")
                * pl.col("run_rate_per_z_opportunity")
            ).alias("actual_component_runs"),
        )
    )
    for skill in ("raw", "chronological"):
        for opportunity in ("raw", "pa_scaled", "hybrid"):
            frame = frame.with_columns(
                (
                    pl.col(f"prediction_skill_z_{skill}")
                    * pl.col(f"prediction_opportunity_{opportunity}")
                    * pl.col("run_rate_per_z_opportunity")
                ).alias(f"prediction_runs_{skill}_skill_{opportunity}_opportunity")
            )
    return frame.sort(["origin_year", "player_id", "component"])


def _metrics_by_group(frame: pl.DataFrame, prediction: str) -> dict[str, object]:
    groups: dict[str, object] = {}
    for target_year in TARGET_YEARS:
        fold = frame.filter(pl.col("origin_year") == target_year - 1)
        groups[str(target_year)] = regression_metrics(
            fold["actual_partial_war_with_catcher"].to_numpy(),
            fold[prediction].to_numpy(),
        )
    return groups


def main() -> None:
    history = _public_component_history()
    transitions = _transition_history(history)
    slopes = _chronological_slopes(transitions)
    conversion = json.loads(CONVERSION_PATH.read_text(encoding="utf-8"))
    run_rates = {
        component: float(conversion[f"catcher_{component}"]["run_rate_per_z_opportunity"])
        for component in COMPONENTS
    }
    base = pl.read_parquet(BASE_PATH)
    panel = pl.read_parquet(PANEL_PATH)
    components = _component_frame(history, slopes, base, panel, run_rates)

    prediction_run_columns = [
        f"prediction_runs_{skill}_skill_{opportunity}_opportunity"
        for skill in ("raw", "chronological")
        for opportunity in ("raw", "pa_scaled", "hybrid")
    ]
    component_totals = components.group_by("origin_year", "player_id").agg(
        pl.col("actual_component_runs").sum().alias("actual_catcher_runs"),
        *[
            pl.col(column).sum().alias(column.replace("prediction_runs", "prediction_catcher_runs"))
            for column in prediction_run_columns
        ],
    )
    frame = (
        base.filter(pl.col("origin_year").is_in([year - 1 for year in TARGET_YEARS]))
        .join(component_totals, on=["origin_year", "player_id"], how="left", validate="1:1")
        .with_columns(
            pl.col("actual_catcher_runs").fill_null(0.0),
            *[
                pl.col(column.replace("prediction_runs", "prediction_catcher_runs")).fill_null(0.0)
                for column in prediction_run_columns
            ],
        )
        .with_columns(
            (pl.col("actual_catcher_runs") / RUNS_PER_WIN).alias("actual_catcher_war"),
            (
                pl.col("actual_partial_war")
                + pl.col("actual_catcher_runs") / RUNS_PER_WIN
            ).alias("actual_partial_war_with_catcher"),
            pl.col("prediction_selected_partial_war").alias("prediction_catcher_neutral"),
        )
    )
    for skill in ("raw", "chronological"):
        for opportunity in ("raw", "pa_scaled", "hybrid"):
            runs_column = (
                f"prediction_catcher_runs_{skill}_skill_{opportunity}_opportunity"
            )
            war_column = f"prediction_catcher_war_{skill}_skill_{opportunity}_opportunity"
            total_column = f"prediction_total_{skill}_skill_{opportunity}_opportunity"
            frame = frame.with_columns(
                (pl.col(runs_column) / RUNS_PER_WIN).alias(war_column),
                (
                    pl.col("prediction_selected_partial_war")
                    + pl.col(runs_column) / RUNS_PER_WIN
                ).alias(total_column),
            )

    primary_total = "prediction_total_chronological_skill_pa_scaled_opportunity"
    actual = frame["actual_partial_war_with_catcher"].to_numpy()
    baseline = frame["prediction_catcher_neutral"].to_numpy()
    player_ids = frame["player_id"].to_numpy()
    model_metrics: dict[str, object] = {
        "catcher_neutral": regression_metrics(actual, baseline)
    }
    for skill in ("raw", "chronological"):
        for opportunity in ("raw", "pa_scaled", "hybrid"):
            name = f"{skill}_skill_{opportunity}_opportunity"
            column = f"prediction_total_{name}"
            model_metrics[name] = regression_metrics(actual, frame[column].to_numpy())

    actual_component = frame["actual_catcher_war"].to_numpy()
    primary_component = frame[PRIMARY_PREDICTION].to_numpy()
    component_details: dict[str, object] = {}
    for component in COMPONENTS:
        subset = components.filter(pl.col("component") == component)
        component_actual = subset["actual_component_runs"].to_numpy() / RUNS_PER_WIN
        component_prediction = (
            subset[
                "prediction_runs_chronological_skill_pa_scaled_opportunity"
            ].to_numpy()
            / RUNS_PER_WIN
        )
        component_zero = np.zeros_like(component_actual)
        component_details[component] = {
            "neutral_zero": regression_metrics(component_actual, component_zero),
            "primary": regression_metrics(component_actual, component_prediction),
            "paired_comparison_vs_zero": paired_cluster_rmse_delta(
                component_actual,
                component_prediction,
                component_zero,
                subset["player_id"].to_numpy(),
            ),
        }
    target_coverage = (
        components.filter(pl.col("target_opportunity") > 0)
        .group_by("origin_year", "component")
        .len()
        .sort(["origin_year", "component"])
        .with_columns((pl.col("origin_year") + 1).alias("target_year"))
        .select("target_year", "component", pl.col("len").alias("eligible_players"))
        .to_dicts()
    )
    skill_diagnostics = []
    for row in slopes.iter_rows(named=True):
        origin_year = int(row["origin_year"])
        component = str(row["component"])
        observed = transitions.filter(
            (pl.col("origin_year") == origin_year)
            & (pl.col("component") == component)
        )
        if observed.is_empty():
            raw_rmse = None
            chronological_rmse = None
        else:
            y = observed["target_skill_z"].to_numpy()
            x = observed["source_skill_z"].to_numpy()
            raw_rmse = float(np.sqrt(np.mean(np.square(x - y))))
            chronological_rmse = float(
                np.sqrt(
                    np.mean(
                        np.square(float(row["chronological_skill_slope"]) * x - y)
                    )
                )
            )
        skill_diagnostics.append(
            {
                **row,
                "matched_players": observed.height,
                "raw_persistence_skill_rmse": raw_rmse,
                "chronological_shrink_skill_rmse": chronological_rmse,
            }
        )

    by_stage: dict[str, object] = {}
    for stage in ("current_mlb", "upper_minors", "lower_minors"):
        subset = frame.filter(pl.col("player_stage") == stage)
        stage_actual = subset["actual_partial_war_with_catcher"].to_numpy()
        by_stage[stage] = {
            "rows": subset.height,
            "neutral": regression_metrics(
                stage_actual, subset["prediction_catcher_neutral"].to_numpy()
            ),
            "primary": regression_metrics(
                stage_actual, subset[primary_total].to_numpy()
            ),
        }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    predictions_artifact = write_canonical_parquet(
        frame.sort(["origin_year", "player_id"]),
        OUTPUT_ROOT / "chronological-predictions.parquet",
        table_name="hitter_catcher_defense_value_v2_predictions",
    )
    components_artifact = write_canonical_parquet(
        components,
        OUTPUT_ROOT / "component-predictions.parquet",
        table_name="hitter_catcher_defense_value_v2_components",
    )
    history_artifact = write_canonical_parquet(
        history,
        OUTPUT_ROOT / "public-catcher-history-2022-2025.parquet",
        table_name="public_catcher_defense_history_2022_2025",
    )
    report = {
        "schema_version": "0.1",
        "status": "hitter_catcher_defense_whole_value_test_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "target_seasons": list(TARGET_YEARS),
        "population_rows": frame.height,
        "model": {
            "skill": (
                "source-season public catcher component z score, multiplied by a "
                "through-origin slope learned only from earlier season transitions"
            ),
            "opportunity": (
                "source public native opportunity scaled by selected expected MLB PA "
                "divided by source-season MLB PA"
            ),
            "primary_selected_before_scoring": (
                "chronological skill shrink plus PA-scaled native opportunity"
            ),
            "run_conversion": (
                "frozen public component-specific runs per z-opportunity; 10 runs per win"
            ),
            "missing_evidence": "neutral zero catcher defense",
        },
        "run_rates": run_rates,
        "metrics": model_metrics,
        "primary_paired_comparison_vs_neutral": paired_cluster_rmse_delta(
            actual,
            frame[primary_total].to_numpy(),
            baseline,
            player_ids,
        ),
        "component_metrics": {
            "neutral_zero": regression_metrics(
                actual_component, np.zeros_like(actual_component)
            ),
            "primary": regression_metrics(actual_component, primary_component),
            "by_component": component_details,
        },
        "component_paired_comparison_vs_zero": paired_cluster_rmse_delta(
            actual_component,
            primary_component,
            np.zeros_like(actual_component),
            player_ids,
        ),
        "primary_by_target_season": _metrics_by_group(frame, primary_total),
        "neutral_by_target_season": _metrics_by_group(
            frame, "prediction_catcher_neutral"
        ),
        "by_player_stage": by_stage,
        "skill_diagnostics": skill_diagnostics,
        "target_coverage": target_coverage,
        "sources": {
            str(path): sha256_file(path)
            for path in (
                BASE_PATH,
                PANEL_PATH,
                OLD_CATCHER_PATH,
                OLD_FRAMING_PATH,
                THROWING_2025_PATH,
                BLOCKING_2025_PATH,
                FRAMING_2025_PATH,
                CONVERSION_PATH,
            )
        },
        "artifacts": {
            "predictions": predictions_artifact.as_record(),
            "components": components_artifact.as_record(),
            "public_history": history_artifact.as_record(),
        },
        "limitations": [
            "Public component coverage begins in 2022, so this test covers 2023-2025 only.",
            "Players below each public leaderboard eligibility threshold receive zero realized and predicted value for that component.",
            "The first 2023 fold has no earlier transition from which to learn shrinkage and therefore uses raw persistence.",
            "The 2025 season is exposed development evidence; 2026 remains sealed.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "metrics": model_metrics,
                "paired": report["primary_paired_comparison_vs_neutral"],
                "component_metrics": report["component_metrics"],
                "component_paired": report[
                    "component_paired_comparison_vs_zero"
                ],
                "by_year": report["primary_by_target_season"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
