#!/usr/bin/env python3
"""Rolling audit of conditional performance uncertainty at observed workload."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import NormalDist

import polars as pl

from universal_baseball.conditional_war_rates import (
    build_hitter_conditional_war_rates,
    build_pitcher_conditional_war_rates,
)
from universal_baseball.historical_war_scoring import (
    score_hitter_neutral_war,
    score_pitcher_neutral_war,
)
from universal_baseball.war_uncertainty_validation import (
    summarize_interval_coverage,
    summarize_named_slices,
)


SOURCE = Path("reports/generated/opportunity-history-sources-v2/tables")
SKILL = Path("reports/generated/free-agent-historical-skill-source/2025-12-31/tables")
OUTPUT = Path("reports/generated/rolling-conditional-war-uncertainty")
TARGETS = (2022, 2023, 2024, 2025)
RUNS_PER_WIN = 10.0
Z80 = NormalDist().inv_cdf(0.90)


def _hitter_players(snapshot: int, universe: pl.DataFrame) -> pl.DataFrame:
    stats = pl.read_parquet(SOURCE / str(snapshot) / "affiliated_season_stats.parquet")
    positions = (
        stats.filter(pl.col("stat_group") == "hitting")
        .group_by("player_id", "position_code")
        .agg(pl.col("plate_appearances").sum().alias("position_pa"))
        .sort(
            ["player_id", "position_pa", "position_code"],
            descending=[False, True, False],
        )
        .unique("player_id", keep="first", maintain_order=True)
        .select("player_id", "position_code")
    )
    return (
        universe.select("player_id", (pl.col("age_years") + 1.0).alias("age_years"))
        .join(positions, on="player_id", how="left", validate="1:1")
        .with_columns(pl.col("position_code").fill_null(""))
    )


def _active_interval(
    scored: pl.DataFrame,
    rates: pl.DataFrame,
    *,
    workload_column: str,
) -> pl.DataFrame:
    source = scored.join(
        rates.select(
            "player_id",
            "event_run_variance",
            "posterior_run_rate_variance",
            "evidence_tier",
        ),
        on="player_id",
        how="inner",
        validate="1:1",
    ).filter(pl.col(workload_column) > 0)
    return source.with_columns(
        (
            (
                pl.col(workload_column) * pl.col("event_run_variance")
                + (pl.col(workload_column) ** 2 - pl.col(workload_column))
                * pl.col("posterior_run_rate_variance")
            )
            / (RUNS_PER_WIN * RUNS_PER_WIN)
        ).alias("annual_war_variance")
    ).with_columns(
        (Z80 * pl.col("annual_war_variance").sqrt()).alias("_spread")
    ).with_columns(
        (pl.col("expected_war") - pl.col("_spread")).alias("projected_war_lower"),
        (pl.col("expected_war") + pl.col("_spread")).alias("projected_war_upper"),
        pl.col("expected_war").alias("projected_war_mean"),
    )


def _fold(target: int, component: str, history: pl.DataFrame) -> pl.DataFrame:
    snapshot = target - 1
    if component == "hitter":
        universe = pl.read_parquet(SOURCE / "hitter_snapshots.parquet").filter(
            pl.col("snapshot_year") == snapshot
        )
        players = _hitter_players(snapshot, universe)
        reference_workload = int(
            history.filter(pl.col("season") == snapshot)
            .get_column("batting_plate_appearances")
            .sum()
        )
        rates = build_hitter_conditional_war_rates(
            players,
            history.filter(pl.col("season") <= snapshot),
            current_season=target,
            forecast_seasons=(target,),
            reference_plate_appearances=reference_workload,
            runs_per_win=RUNS_PER_WIN,
            evidence_anchor_season=snapshot,
            reference_season=snapshot,
        )
        outcomes = history.filter(pl.col("season") == target)
        workload = outcomes.group_by("player_id").agg(
            pl.col("batting_plate_appearances").sum()
        )
        projections = rates.join(workload, on="player_id", how="left").with_columns(
            pl.col("batting_plate_appearances").fill_null(0.0)
        ).with_columns(
            (
                pl.col("conditional_war_per_600_pa")
                * pl.col("batting_plate_appearances")
                / 600.0
            ).alias("expected_war")
        )
        scored, _ = score_hitter_neutral_war(
            projections,
            outcomes,
            history.filter(pl.col("season") == snapshot),
            runs_per_win=RUNS_PER_WIN,
        )
        result = _active_interval(
            scored, rates, workload_column="batting_plate_appearances"
        )
    else:
        universe = pl.read_parquet(SOURCE / "pitcher_snapshots.parquet").filter(
            pl.col("snapshot_year") == snapshot
        )
        players = universe.select(
            "player_id", (pl.col("age_years") + 1.0).alias("age_years")
        )
        reference_workload = int(
            history.filter(pl.col("season") == snapshot)
            .get_column("pitching_batters_faced")
            .sum()
        )
        rates = build_pitcher_conditional_war_rates(
            players,
            history.filter(pl.col("season") <= snapshot),
            current_season=target,
            forecast_seasons=(target,),
            reference_batters_faced=reference_workload,
            runs_per_win=RUNS_PER_WIN,
            evidence_anchor_season=snapshot,
            reference_season=snapshot,
        )
        outcomes = history.filter(pl.col("season") == target)
        workload = outcomes.group_by("player_id").agg(
            pl.col("pitching_batters_faced").sum()
        )
        projections = rates.join(workload, on="player_id", how="left").with_columns(
            pl.col("pitching_batters_faced").fill_null(0.0)
        ).with_columns(
            (
                pl.col("conditional_war_per_800_bf")
                * pl.col("pitching_batters_faced")
                / 800.0
            ).alias("expected_war")
        )
        scored, _ = score_pitcher_neutral_war(
            projections,
            outcomes,
            history.filter(pl.col("season") == snapshot),
            runs_per_win=RUNS_PER_WIN,
        )
        result = _active_interval(
            scored, rates, workload_column="pitching_batters_faced"
        )
    return result.with_columns(pl.lit(target).alias("target_season"))


def _report(frame: pl.DataFrame) -> dict[str, object]:
    calibrated_frames = []
    scale_rows = []
    for target in TARGETS:
        validation = frame.filter(pl.col("target_season") == target)
        if target == TARGETS[0]:
            multiplier = 1.0
            status = "warmup_no_prior_origin"
        else:
            prior = frame.filter(pl.col("target_season") < target).with_columns(
                (
                    (pl.col("observed_neutral_war") - pl.col("projected_war_mean"))
                    / pl.col("annual_war_variance").sqrt()
                ).alias("standardized_error")
            )
            multiplier = float(
                prior.select((pl.col("standardized_error") ** 2).mean().sqrt()).item()
            )
            status = "prior_origins_only"
        calibrated = validation.with_columns(
            (pl.col("annual_war_variance") * multiplier * multiplier).alias(
                "annual_war_variance"
            )
        ).with_columns(
            (Z80 * pl.col("annual_war_variance").sqrt()).alias("_scaled_spread")
        ).with_columns(
            (pl.col("projected_war_mean") - pl.col("_scaled_spread")).alias(
                "projected_war_lower"
            ),
            (pl.col("projected_war_mean") + pl.col("_scaled_spread")).alias(
                "projected_war_upper"
            ),
        )
        calibrated_frames.append(calibrated)
        raw_score = summarize_interval_coverage(validation)
        scaled_score = summarize_interval_coverage(calibrated)
        scale_rows.append(
            {
                "target_season": target,
                "status": status,
                "standard_deviation_multiplier": multiplier,
                "raw": raw_score,
                "scaled": scaled_score,
                "scaled_minus_raw_interval_score": float(
                    scaled_score["mean_interval_score"]
                )
                - float(raw_score["mean_interval_score"]),
            }
        )
    rolling = pl.concat(calibrated_frames)
    evaluation = frame.filter(pl.col("target_season") > TARGETS[0])
    rolling_evaluation = rolling.filter(pl.col("target_season") > TARGETS[0])
    raw_evaluation = summarize_interval_coverage(evaluation)
    scaled_evaluation = summarize_interval_coverage(rolling_evaluation)
    return {
        "pooled": summarize_interval_coverage(frame),
        "annual": {
            str(target): summarize_interval_coverage(
                frame.filter(pl.col("target_season") == target)
            )
            for target in TARGETS
        },
        "evidence_tier": summarize_named_slices(frame, slice_column="evidence_tier"),
        "rolling_scale": {
            "method": "prior-origin standardized-error RMSE; point mean unchanged",
            "annual": scale_rows,
            "pooled_2023_2025": {
                "raw": raw_evaluation,
                "scaled": scaled_evaluation,
                "scaled_minus_raw_interval_score": float(
                    scaled_evaluation["mean_interval_score"]
                )
                - float(raw_evaluation["mean_interval_score"]),
                "scaled_minus_raw_absolute_coverage_error": abs(
                    float(scaled_evaluation["coverage"]) - 0.80
                )
                - abs(float(raw_evaluation["coverage"]) - 0.80),
            },
        },
    }


def main() -> int:
    hitter_history = pl.read_parquet(SKILL / "mlb_hitting_components.parquet")
    pitcher_history = pl.read_parquet(SKILL / "mlb_pitching_components.parquet")
    hitters = pl.concat([_fold(target, "hitter", hitter_history) for target in TARGETS])
    pitchers = pl.concat([_fold(target, "pitcher", pitcher_history) for target in TARGETS])
    report = {
        "report_schema_version": "0.1",
        "gate": "rolling_conditional_war_performance_uncertainty",
        "targets": list(TARGETS),
        "hitter": _report(hitters),
        "pitcher": _report(pitchers),
        "production_changed": False,
        "boundaries": {
            "observed_workload_used_only_to_isolate_rate_error": True,
            "future_components_used_as_predictors": False,
            "defense_and_baserunning": "neutral_zero_in_prediction_and_outcome",
            "runs_per_win": RUNS_PER_WIN,
            "nominal_central_coverage": 0.80,
        },
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                component: {
                    "pooled": report[component]["pooled"],
                    "annual_coverage": {
                        year: values["coverage"]
                        for year, values in report[component]["annual"].items()
                    },
                    "rolling_scale": report[component]["rolling_scale"][
                        "pooled_2023_2025"
                    ],
                }
                for component in ("hitter", "pitcher")
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
