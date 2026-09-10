#!/usr/bin/env python3
"""Test age-relative-to-level and throwing hand on future MLB pitcher components."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
from scipy.optimize import minimize

from audit_pitcher_affiliated_regression import (
    COMPONENTS,
    INCUMBENT,
    SOURCE,
    _bootstrap_delta,
    _components,
    _fold_inputs,
    _run_rate_diagnostic,
    _score_rows,
)
from universal_baseball.level_component_translation import (
    LEVEL_ORDER,
    build_translated_affiliated_profiles,
    score_component_profiles,
)


DEMOGRAPHICS = Path(
    "reports/generated/player-demographics/tables/player-demographics.parquet"
)
OUTPUT = Path("docs/pitcher-age-level-handedness-result.json")
FAMILIES = {
    "age_relative": ("age_relative",),
    "throwing_hand": ("left_handed",),
    "age_and_hand": ("age_relative", "left_handed"),
    "age_hand_interaction": (
        "age_relative", "left_handed", "age_x_left",
    ),
}
L2_PENALTY = 1.0


def _features(
    source: pl.DataFrame,
    demographics: pl.DataFrame,
    players: pl.DataFrame,
    cutoff: int,
) -> pl.DataFrame:
    eligible = source.filter(
        (pl.col("season") <= cutoff) & (pl.col("level_group") != "MLB")
    )
    latest = eligible.group_by("player_id").agg(pl.col("season").max().alias("season"))
    rows = (
        eligible.join(latest, on=["player_id", "season"], how="inner")
        .group_by("player_id", "season", "level_group", "reported_age")
        .agg(pl.col("batters_faced").sum())
        .with_columns(
            pl.col("level_group").replace_strict(LEVEL_ORDER).alias("level_order")
        )
        .sort(
            ["player_id", "batters_faced", "level_order"],
            descending=[False, True, True],
        )
        .unique("player_id", keep="first")
    )
    reference = (
        eligible.group_by("season", "player_id", "level_group", "reported_age")
        .agg(pl.col("batters_faced").sum())
        .filter(pl.col("batters_faced") >= 30)
        .group_by("season", "level_group")
        .agg(pl.col("reported_age").median().alias("level_median_age"))
    )
    return (
        players.join(rows, on="player_id", how="left", validate="1:1")
        .join(reference, on=["season", "level_group"], how="left", validate="m:1")
        .join(
            demographics.select("player_id", "pitch_hand"),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .with_columns(
            ((pl.col("reported_age") - pl.col("level_median_age")) / 3.0)
            .fill_null(0.0)
            .clip(-2.0, 2.0)
            .alias("age_relative"),
            (pl.col("pitch_hand") == "L").fill_null(False).cast(pl.Float64).alias(
                "left_handed"
            ),
            pl.col("level_group")
            .replace_strict(LEVEL_ORDER, default=0)
            .fill_null(0)
            .alias("level_order"),
        )
        .with_columns(
            (pl.col("age_relative") * pl.col("left_handed")).alias("age_x_left")
        )
        .select(
            "player_id", "age_relative", "left_handed", "age_x_left",
            "level_group", "level_order",
        )
        .sort("player_id")
    )


def _fit_adjustment(
    predictions: pl.DataFrame,
    target: pl.DataFrame,
    features: pl.DataFrame,
    columns: tuple[str, ...],
) -> np.ndarray:
    rows = _score_rows(predictions, target).join(
        features, on="player_id", how="inner", validate="1:1"
    )
    x = rows.select(columns).to_numpy()
    counts = rows.select(COMPONENTS).to_numpy().astype(float)
    base = np.log(rows.select(*(f"p_{value}" for value in COMPONENTS)).to_numpy())
    bf = counts.sum(axis=1)
    scale = len(rows) / bf.sum()
    component_count = len(COMPONENTS) - 1

    def objective(flat: np.ndarray) -> tuple[float, np.ndarray]:
        beta = flat.reshape(len(columns), component_count)
        adjustment = np.column_stack([x @ beta, np.zeros(len(x))])
        logits = base + adjustment
        logits -= logits.max(axis=1, keepdims=True)
        probabilities = np.exp(logits)
        probabilities /= probabilities.sum(axis=1, keepdims=True)
        loss = -scale * float((counts * np.log(probabilities)).sum())
        loss += 0.5 * L2_PENALTY * float((beta * beta).sum())
        residual = probabilities * bf[:, None] - counts
        gradient = scale * x.T @ residual[:, :component_count]
        gradient += L2_PENALTY * beta
        return loss, gradient.ravel()

    result = minimize(
        objective,
        np.zeros(len(columns) * component_count),
        method="L-BFGS-B",
        jac=True,
    )
    if not result.success:
        raise RuntimeError(f"demographic adjustment fit failed: {result.message}")
    return result.x.reshape(len(columns), component_count)


def _apply_adjustment(
    predictions: pl.DataFrame,
    features: pl.DataFrame,
    columns: tuple[str, ...],
    beta: np.ndarray,
) -> pl.DataFrame:
    source = predictions.join(features, on="player_id", how="left", validate="1:1")
    output = []
    for row in source.sort("player_id").iter_rows(named=True):
        x = np.asarray([float(row[value] or 0.0) for value in columns])
        adjustment = np.append(x @ beta, 0.0)
        logits = np.asarray(
            [np.log(float(row[f"p_{component}"])) for component in COMPONENTS]
        ) + adjustment
        probabilities = np.exp(logits - logits.max())
        probabilities /= probabilities.sum()
        output.append(
            {
                **{key: row[key] for key in predictions.columns},
                **{
                    f"p_{component}": float(probabilities[index])
                    for index, component in enumerate(COMPONENTS)
                },
            }
        )
    return pl.DataFrame(output).sort("player_id")


def _fold_base(
    source: pl.DataFrame,
    demographics: pl.DataFrame,
    target_season: int,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, dict[str, float]]:
    players, evidence, target, support = _fold_inputs(source, target_season)
    offsets = support.pop("offsets")
    predictions = build_translated_affiliated_profiles(
        players,
        evidence,
        offsets,
        exposure_column="batters_faced",
        component_columns=COMPONENTS,
        current_season=target_season - 1,
        reference_season=target_season - 1,
        regression_exposure=INCUMBENT,
    )
    feature_frame = _features(source, demographics, players, target_season - 1)
    return predictions, target, feature_frame, support


def _subgroups(
    candidate: pl.DataFrame,
    incumbent: pl.DataFrame,
    target: pl.DataFrame,
    features: pl.DataFrame,
) -> dict[str, object]:
    candidate_rows = _score_rows(candidate, target).join(features, on="player_id")
    incumbent_rows = _score_rows(incumbent, target).select(
        "player_id",
        pl.col("log_loss_total").alias("incumbent_ll"),
        pl.col("brier_total").alias("incumbent_brier"),
    )
    rows = candidate_rows.join(incumbent_rows, on="player_id", validate="1:1")
    age_median = float(rows.get_column("age_relative").median())
    definitions = {
        "younger_for_level": pl.col("age_relative") < age_median,
        "older_for_level": pl.col("age_relative") >= age_median,
        "left_handed": pl.col("left_handed") == 1.0,
        "right_or_other": pl.col("left_handed") == 0.0,
    }
    result = {}
    for name, condition in definitions.items():
        group = rows.filter(condition)
        total = float(group.get_column("batters_faced").sum())
        result[name] = {
            "players": group.height,
            "target_bf": int(total),
            "log_loss_delta": float(
                group.select(
                    (pl.col("log_loss_total") - pl.col("incumbent_ll")).sum()
                ).item()
                / total
            ),
            "brier_delta": float(
                group.select(
                    (pl.col("brier_total") - pl.col("incumbent_brier")).sum()
                ).item()
                / total
            ),
        }
    return result


def main() -> int:
    source = _components(pl.read_parquet(SOURCE))
    demographics = pl.read_parquet(DEMOGRAPHICS)
    dev_base, dev_target, dev_features, _ = _fold_base(source, demographics, 2024)
    base_score = score_component_profiles(
        dev_base, dev_target,
        exposure_column="batters_faced", component_columns=COMPONENTS,
    )
    fitted = {}
    development_scores = {"incumbent": base_score}
    for name, columns in FAMILIES.items():
        beta = _fit_adjustment(dev_base, dev_target, dev_features, columns)
        candidate = _apply_adjustment(dev_base, dev_features, columns, beta)
        fitted[name] = beta
        development_scores[name] = score_component_profiles(
            candidate, dev_target,
            exposure_column="batters_faced", component_columns=COMPONENTS,
        )
    eligible = [
        name for name in FAMILIES
        if float(development_scores[name]["component_log_loss"])
        < float(base_score["component_log_loss"])
        and float(development_scores[name]["component_brier_score"])
        < float(base_score["component_brier_score"])
    ]
    selected = min(
        eligible,
        key=lambda name: float(development_scores[name]["component_log_loss"]),
    ) if eligible else "incumbent"

    outer_base, outer_target, outer_features, prior = _fold_base(
        source, demographics, 2025
    )
    if selected == "incumbent":
        outer_candidate = outer_base
    else:
        outer_candidate = _apply_adjustment(
            outer_base, outer_features, FAMILIES[selected], fitted[selected]
        )
    outer_base_score = score_component_profiles(
        outer_base, outer_target,
        exposure_column="batters_faced", component_columns=COMPONENTS,
    )
    outer_candidate_score = score_component_profiles(
        outer_candidate, outer_target,
        exposure_column="batters_faced", component_columns=COMPONENTS,
    )
    ll_delta = float(outer_candidate_score["component_log_loss"]) - float(
        outer_base_score["component_log_loss"]
    )
    brier_delta = float(outer_candidate_score["component_brier_score"]) - float(
        outer_base_score["component_brier_score"]
    )
    promoted = selected != "incumbent" and ll_delta < 0 and brier_delta < 0
    report = {
        "report_schema_version": "0.1",
        "status": "pitcher_age_level_handedness_audit_complete",
        "contract": "docs/pitcher-age-level-handedness-plan.md",
        "development_2024": {
            "scores": development_scores,
            "selected_family": selected,
            "selected_coefficients": None if selected == "incumbent" else {
                feature: {
                    component: float(fitted[selected][feature_index, component_index])
                    for component_index, component in enumerate(COMPONENTS[:-1])
                }
                for feature_index, feature in enumerate(FAMILIES[selected])
            },
        },
        "confirmation_2025": {
            "incumbent_score": outer_base_score,
            "candidate_score": outer_candidate_score,
            "candidate_minus_incumbent_log_loss": ll_delta,
            "candidate_minus_incumbent_brier": brier_delta,
            "bootstrap_candidate_minus_incumbent": _bootstrap_delta(
                _score_rows(outer_candidate, outer_target),
                _score_rows(outer_base, outer_target),
                seed=20250911,
            ),
            "subgroups": _subgroups(
                outer_candidate, outer_base, outer_target, outer_features
            ),
            "candidate_run_rate_diagnostic": _run_rate_diagnostic(
                outer_candidate, outer_target, prior
            ),
            "incumbent_run_rate_diagnostic": _run_rate_diagnostic(
                outer_base, outer_target, prior
            ),
        },
        "decision": {"promoted": promoted, "selected_family": selected},
        "boundaries": {
            "current_2026_outcomes_used": False,
            "current_physical_measurements_used": False,
            "outside_fv_used": False,
            "target_grade_count_used": False,
        },
    }
    OUTPUT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "selected_family": selected,
        "confirmation_log_loss_delta": ll_delta,
        "confirmation_brier_delta": brier_delta,
        "promoted": promoted,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
