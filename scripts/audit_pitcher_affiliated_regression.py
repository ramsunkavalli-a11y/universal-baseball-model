#!/usr/bin/env python3
"""Select pitcher affiliated-profile shrinkage on 2024 and confirm once on 2025."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_v2_evaluation import (
    NEUTRAL_WOBA_SCALE,
    NEUTRAL_WOBA_WEIGHTS,
)
from universal_baseball.level_component_translation import (
    build_translated_affiliated_profiles,
    fit_same_season_component_translation,
    score_component_profiles,
)


COMPONENTS = ("so", "ubb", "hbp", "hr", "other")
CANDIDATES = (100.0, 200.0, 400.0, 600.0, 800.0, 1200.0, 1600.0)
INCUMBENT = 800.0
SOURCE = Path(
    "reports/generated/affiliated-skill-source/tables/"
    "affiliated_pitching_components.parquet"
)
OUTPUT = Path("docs/pitcher-affiliated-regression-audit-result.json")


def _components(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        pl.col("strike_outs").alias("so"),
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        pl.col("hit_batters").alias("hbp"),
        pl.col("home_runs").alias("hr"),
    ).with_columns(
        (pl.col("batters_faced") - pl.sum_horizontal(*COMPONENTS[:-1])).alias(
            "other"
        )
    )


def _fold_inputs(
    source: pl.DataFrame, target_season: int
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, dict[str, float]]:
    cutoff = target_season - 1
    prior_evidence = source.filter(pl.col("season") <= cutoff)
    fit = fit_same_season_component_translation(
        source,
        exposure_column="batters_faced",
        component_columns=COMPONENTS,
        completed_seasons=tuple(
            int(value)
            for value in prior_evidence.get_column("season").unique().sort().to_list()
        ),
        minimum_level_exposure=30,
    )
    exposure = prior_evidence.group_by("player_id").agg(
        pl.col("batters_faced").sum().alias("all_bf"),
        pl.col("batters_faced")
        .filter(pl.col("level_group") == "MLB")
        .sum()
        .alias("mlb_bf"),
    )
    players = exposure.filter(
        (pl.col("all_bf") > 0) & (pl.col("mlb_bf") == 0)
    ).select("player_id")
    target = source.filter(
        (pl.col("season") == target_season) & (pl.col("level_group") == "MLB")
    )
    reference = prior_evidence.filter(
        (pl.col("season") == cutoff) & (pl.col("level_group") == "MLB")
    )
    total = float(reference.get_column("batters_faced").sum())
    prior = {
        component: float(reference.get_column(component).sum()) / total
        for component in COMPONENTS
    }
    return players, prior_evidence, target, prior | {"offsets": fit.offsets}


def _score_rows(
    predictions: pl.DataFrame, target: pl.DataFrame
) -> pl.DataFrame:
    actual = target.group_by("player_id").agg(
        pl.col("batters_faced").sum(),
        *(pl.col(component).sum() for component in COMPONENTS),
    ).filter(pl.col("batters_faced") > 0)
    return actual.join(predictions, on="player_id", how="inner", validate="1:1").sort(
        "player_id"
    ).with_columns(
        pl.sum_horizontal(
            *(
                -pl.col(component) * pl.col(f"p_{component}").log()
                for component in COMPONENTS
            )
        ).alias("log_loss_total"),
        (
            pl.col("batters_faced")
            * (
                1.0
                + pl.sum_horizontal(
                    *(pl.col(f"p_{component}") ** 2 for component in COMPONENTS)
                )
            )
            - 2.0
            * pl.sum_horizontal(
                *(
                    pl.col(component) * pl.col(f"p_{component}")
                    for component in COMPONENTS
                )
            )
        ).alias("brier_total"),
    )


def _bootstrap_delta(
    candidate: pl.DataFrame, incumbent: pl.DataFrame, *, seed: int = 20250909
) -> dict[str, dict[str, float]]:
    joined = candidate.select(
        "player_id", "batters_faced", "log_loss_total", "brier_total"
    ).join(
        incumbent.select(
            "player_id",
            pl.col("log_loss_total").alias("incumbent_log_loss_total"),
            pl.col("brier_total").alias("incumbent_brier_total"),
        ),
        on="player_id",
        how="inner",
        validate="1:1",
    )
    values = joined.select(
        "batters_faced",
        (pl.col("log_loss_total") - pl.col("incumbent_log_loss_total")).alias(
            "log_loss_delta"
        ),
        (pl.col("brier_total") - pl.col("incumbent_brier_total")).alias(
            "brier_delta"
        ),
    ).to_numpy()
    rng = np.random.default_rng(seed)
    samples = np.empty((2000, 2), dtype=float)
    for index in range(samples.shape[0]):
        chosen = rng.integers(0, len(values), len(values))
        draw = values[chosen]
        denominator = draw[:, 0].sum()
        samples[index] = draw[:, 1:].sum(axis=0) / denominator
    result = {}
    for index, name in enumerate(("component_log_loss", "component_brier")):
        result[name] = {
            "lower_95": float(np.quantile(samples[:, index], 0.025)),
            "median": float(np.quantile(samples[:, index], 0.5)),
            "upper_95": float(np.quantile(samples[:, index], 0.975)),
        }
    return result


def _run_rate_diagnostic(
    predictions: pl.DataFrame,
    target: pl.DataFrame,
    prior: dict[str, float],
) -> dict[str, object]:
    known = (
        prior["ubb"] * NEUTRAL_WOBA_WEIGHTS["UBB"]
        + prior["hbp"] * NEUTRAL_WOBA_WEIGHTS["HBP"]
        + prior["hr"] * NEUTRAL_WOBA_WEIGHTS["HR"]
    )
    weights = {
        "so": 0.0,
        "ubb": NEUTRAL_WOBA_WEIGHTS["UBB"],
        "hbp": NEUTRAL_WOBA_WEIGHTS["HBP"],
        "hr": NEUTRAL_WOBA_WEIGHTS["HR"],
        "other": (0.3188 - known) / prior["other"],
    }
    rows = _score_rows(predictions, target).with_columns(
        (
            -(pl.sum_horizontal(
                *(pl.col(f"p_{key}") * value for key, value in weights.items())
            ) - 0.3188)
            * 800.0
            / NEUTRAL_WOBA_SCALE
        ).alias("predicted_raa_per_800"),
        (
            -(pl.sum_horizontal(
                *(
                    pl.col(key) / pl.col("batters_faced") * value
                    for key, value in weights.items()
                )
            ) - 0.3188)
            * 800.0
            / NEUTRAL_WOBA_SCALE
        ).alias("observed_raa_per_800"),
    )
    weights_bf = rows.get_column("batters_faced").to_numpy()
    predicted = rows.get_column("predicted_raa_per_800").to_numpy()
    observed = rows.get_column("observed_raa_per_800").to_numpy()
    order = np.argsort(predicted, kind="stable")
    quintiles = []
    for number, indices in enumerate(np.array_split(order, 5), start=1):
        quintiles.append(
            {
                "quintile": number,
                "players": int(len(indices)),
                "target_bf": int(weights_bf[indices].sum()),
                "predicted_raa_per_800": float(
                    np.average(predicted[indices], weights=weights_bf[indices])
                ),
                "observed_raa_per_800": float(
                    np.average(observed[indices], weights=weights_bf[indices])
                ),
            }
        )
    return {
        "predicted_player_rate_sd": float(np.std(predicted, ddof=1)),
        "observed_player_rate_sd": float(np.std(observed, ddof=1)),
        "bf_weighted_predicted_mean": float(np.average(predicted, weights=weights_bf)),
        "bf_weighted_observed_mean": float(np.average(observed, weights=weights_bf)),
        "quintiles": quintiles,
    }


def _fold(source: pl.DataFrame, target_season: int) -> dict[str, object]:
    players, evidence, target, support = _fold_inputs(source, target_season)
    offsets = support.pop("offsets")
    predictions = {
        int(regression): build_translated_affiliated_profiles(
            players,
            evidence,
            offsets,
            exposure_column="batters_faced",
            component_columns=COMPONENTS,
            current_season=target_season - 1,
            reference_season=target_season - 1,
            regression_exposure=regression,
        )
        for regression in CANDIDATES
    }
    return {
        "target_season": target_season,
        "scores": {
            str(int(regression)): score_component_profiles(
                predictions[int(regression)],
                target,
                exposure_column="batters_faced",
                component_columns=COMPONENTS,
            )
            for regression in CANDIDATES
        },
        "predictions": predictions,
        "target": target,
        "prior": support,
    }


def main() -> int:
    source = _components(pl.read_parquet(SOURCE))
    development = _fold(source, 2024)
    incumbent_score = development["scores"][str(int(INCUMBENT))]
    eligible = [
        regression
        for regression in CANDIDATES
        if float(development["scores"][str(int(regression))]["component_brier_score"])
        < float(incumbent_score["component_brier_score"])
    ]
    selected = min(
        eligible,
        key=lambda value: (
            float(development["scores"][str(int(value))]["component_log_loss"]),
            abs(value - INCUMBENT),
        ),
    ) if eligible else INCUMBENT
    confirmation = _fold(source, 2025)
    selected_key = str(int(selected))
    incumbent_key = str(int(INCUMBENT))
    selected_score = confirmation["scores"][selected_key]
    confirmation_incumbent = confirmation["scores"][incumbent_key]
    log_loss_delta = float(selected_score["component_log_loss"]) - float(
        confirmation_incumbent["component_log_loss"]
    )
    brier_delta = float(selected_score["component_brier_score"]) - float(
        confirmation_incumbent["component_brier_score"]
    )
    promoted = selected != INCUMBENT and log_loss_delta < 0 and brier_delta < 0
    selected_rows = _score_rows(
        confirmation["predictions"][int(selected)], confirmation["target"]
    )
    incumbent_rows = _score_rows(
        confirmation["predictions"][int(INCUMBENT)], confirmation["target"]
    )
    report = {
        "report_schema_version": "0.1",
        "status": "pitcher_affiliated_regression_audit_complete",
        "contract": "docs/pitcher-affiliated-regression-audit-plan.md",
        "development_2024": {"scores": development["scores"]},
        "selection": {
            "selected_regression_bf": int(selected),
            "incumbent_regression_bf": int(INCUMBENT),
            "rule_applied_before_confirmation": True,
        },
        "confirmation_2025": {
            "selected_score": selected_score,
            "incumbent_score": confirmation_incumbent,
            "selected_minus_incumbent_component_log_loss": log_loss_delta,
            "selected_minus_incumbent_component_brier": brier_delta,
            "bootstrap_selected_minus_incumbent": _bootstrap_delta(
                selected_rows, incumbent_rows
            ),
            "selected_run_rate_diagnostic": _run_rate_diagnostic(
                confirmation["predictions"][int(selected)],
                confirmation["target"],
                confirmation["prior"],
            ),
            "incumbent_run_rate_diagnostic": _run_rate_diagnostic(
                confirmation["predictions"][int(INCUMBENT)],
                confirmation["target"],
                confirmation["prior"],
            ),
        },
        "decision": {
            "promoted": promoted,
            "regression_bf": int(selected if promoted else INCUMBENT),
        },
        "boundaries": {
            "current_2026_outcomes_used": False,
            "outside_fv_used": False,
            "contract_or_subjective_labels_used": False,
        },
    }
    OUTPUT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "selected_regression_bf": int(selected),
                "confirmation_log_loss_delta": log_loss_delta,
                "confirmation_brier_delta": brier_delta,
                "promoted": promoted,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
