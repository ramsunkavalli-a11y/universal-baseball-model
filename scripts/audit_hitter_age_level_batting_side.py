#!/usr/bin/env python3
"""Test age-for-level and batting side on future MLB hitter components."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
from scipy.optimize import minimize

from universal_baseball.level_component_translation import (
    LEVEL_ORDER,
    build_translated_affiliated_profiles,
    fit_same_season_component_translation,
    score_component_profiles,
)


COMPONENTS = ("ubb", "hbp", "single", "double", "triple", "hr", "other")
SOURCE = Path(
    "reports/generated/affiliated-skill-source/tables/affiliated_hitting_components.parquet"
)
DEMOGRAPHICS = Path(
    "reports/generated/player-demographics/tables/player-demographics.parquet"
)
OUTPUT = Path("docs/hitter-age-level-batting-side-result.json")
REGRESSION_PA = 1200.0
L2_PENALTY = 1.0
FAMILIES = {
    "age_relative": ("age_relative",),
    "batting_side": ("left_handed", "switch_hitter"),
    "age_and_side": ("age_relative", "left_handed", "switch_hitter"),
    "age_side_interaction": (
        "age_relative", "left_handed", "switch_hitter",
        "age_x_left", "age_x_switch",
    ),
}


def _components(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        pl.col("hit_by_pitch").alias("hbp"),
        (
            pl.col("hits") - pl.col("doubles") - pl.col("triples")
            - pl.col("home_runs")
        ).alias("single"),
        pl.col("doubles").alias("double"),
        pl.col("triples").alias("triple"),
        pl.col("home_runs").alias("hr"),
    ).with_columns(
        (pl.col("plate_appearances") - pl.sum_horizontal(*COMPONENTS[:-1])).alias(
            "other"
        )
    )


def _fold_inputs(source: pl.DataFrame, target_season: int):
    cutoff = target_season - 1
    evidence = source.filter(pl.col("season") <= cutoff)
    seasons = tuple(
        int(value) for value in evidence["season"].unique().sort().to_list()
    )
    offsets = fit_same_season_component_translation(
        source,
        exposure_column="plate_appearances",
        component_columns=COMPONENTS,
        completed_seasons=seasons,
        minimum_level_exposure=30,
    ).offsets
    exposure = evidence.group_by("player_id").agg(
        pl.col("plate_appearances").sum().alias("all_pa"),
        pl.col("plate_appearances")
        .filter(pl.col("level_group") == "MLB")
        .sum()
        .alias("mlb_pa"),
    )
    players = exposure.filter(
        (pl.col("all_pa") > 0) & (pl.col("mlb_pa") == 0)
    ).select("player_id")
    target = source.filter(
        (pl.col("season") == target_season) & (pl.col("level_group") == "MLB")
    )
    predictions = build_translated_affiliated_profiles(
        players,
        evidence,
        offsets,
        exposure_column="plate_appearances",
        component_columns=COMPONENTS,
        current_season=cutoff,
        reference_season=cutoff,
        regression_exposure=REGRESSION_PA,
    )
    return players, predictions, target


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
    current = (
        eligible.join(latest, on=["player_id", "season"], how="inner")
        .group_by("player_id", "season", "level_group", "reported_age")
        .agg(pl.col("plate_appearances").sum())
        .with_columns(
            pl.col("level_group").replace_strict(LEVEL_ORDER).alias("level_order")
        )
        .sort(
            ["player_id", "plate_appearances", "level_order"],
            descending=[False, True, True],
        )
        .unique("player_id", keep="first")
    )
    reference = (
        eligible.group_by("season", "player_id", "level_group", "reported_age")
        .agg(pl.col("plate_appearances").sum())
        .filter(pl.col("plate_appearances") >= 30)
        .group_by("season", "level_group")
        .agg(pl.col("reported_age").median().alias("level_median_age"))
    )
    return (
        players.join(current, on="player_id", how="left", validate="1:1")
        .join(reference, on=["season", "level_group"], how="left", validate="m:1")
        .join(
            demographics.select("player_id", "bat_side"),
            on="player_id", how="left", validate="1:1",
        )
        .with_columns(
            ((pl.col("reported_age") - pl.col("level_median_age")) / 3.0)
            .fill_null(0.0).clip(-2.0, 2.0).alias("age_relative"),
            (pl.col("bat_side") == "L").fill_null(False).cast(pl.Float64)
            .alias("left_handed"),
            (pl.col("bat_side") == "S").fill_null(False).cast(pl.Float64)
            .alias("switch_hitter"),
        )
        .with_columns(
            (pl.col("age_relative") * pl.col("left_handed")).alias("age_x_left"),
            (pl.col("age_relative") * pl.col("switch_hitter")).alias("age_x_switch"),
        )
        .select("player_id", *FAMILIES["age_side_interaction"])
        .sort("player_id")
    )


def _score_rows(predictions: pl.DataFrame, target: pl.DataFrame) -> pl.DataFrame:
    actual = target.group_by("player_id").agg(
        pl.col("plate_appearances").sum(),
        *(pl.col(component).sum() for component in COMPONENTS),
    ).filter(pl.col("plate_appearances") > 0)
    return actual.join(predictions, on="player_id", how="inner", validate="1:1").with_columns(
        pl.sum_horizontal(
            *(
                -pl.col(component) * pl.col(f"p_{component}").log()
                for component in COMPONENTS
            )
        ).alias("log_loss_total"),
        (
            pl.col("plate_appearances")
            * (1.0 + pl.sum_horizontal(*(pl.col(f"p_{c}") ** 2 for c in COMPONENTS)))
            - 2.0 * pl.sum_horizontal(
                *(pl.col(c) * pl.col(f"p_{c}") for c in COMPONENTS)
            )
        ).alias("brier_total"),
    ).sort("player_id")


def _fit(
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
    base = np.log(rows.select(*(f"p_{c}" for c in COMPONENTS)).to_numpy())
    exposure = counts.sum(axis=1)
    scale = len(rows) / exposure.sum()
    free_components = len(COMPONENTS) - 1

    def objective(flat: np.ndarray):
        beta = flat.reshape(len(columns), free_components)
        logits = base + np.column_stack([x @ beta, np.zeros(len(x))])
        logits -= logits.max(axis=1, keepdims=True)
        probability = np.exp(logits)
        probability /= probability.sum(axis=1, keepdims=True)
        loss = -scale * float((counts * np.log(probability)).sum())
        loss += 0.5 * L2_PENALTY * float((beta * beta).sum())
        residual = probability * exposure[:, None] - counts
        gradient = scale * x.T @ residual[:, :free_components] + L2_PENALTY * beta
        return loss, gradient.ravel()

    fit = minimize(
        objective,
        np.zeros(len(columns) * free_components),
        method="L-BFGS-B", jac=True,
    )
    if not fit.success:
        raise RuntimeError(f"hitter demographic adjustment failed: {fit.message}")
    return fit.x.reshape(len(columns), free_components)


def _apply(
    predictions: pl.DataFrame,
    features: pl.DataFrame,
    columns: tuple[str, ...],
    beta: np.ndarray,
) -> pl.DataFrame:
    source = predictions.join(features, on="player_id", how="left", validate="1:1")
    rows = []
    for row in source.iter_rows(named=True):
        x = np.asarray([float(row.get(column) or 0.0) for column in columns])
        adjustment = np.append(x @ beta, 0.0)
        logits = np.asarray(
            [np.log(float(row[f"p_{component}"])) for component in COMPONENTS]
        ) + adjustment
        probability = np.exp(logits - logits.max())
        probability /= probability.sum()
        rows.append(
            {
                **{column: row[column] for column in predictions.columns},
                **{f"p_{c}": float(probability[i]) for i, c in enumerate(COMPONENTS)},
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None).sort("player_id")


def _bootstrap(candidate: pl.DataFrame, incumbent: pl.DataFrame) -> dict[str, object]:
    joined = candidate.select(
        "player_id", "plate_appearances", "log_loss_total", "brier_total"
    ).join(
        incumbent.select(
            "player_id",
            pl.col("log_loss_total").alias("base_ll"),
            pl.col("brier_total").alias("base_brier"),
        ),
        on="player_id", validate="1:1",
    ).select(
        "plate_appearances",
        (pl.col("log_loss_total") - pl.col("base_ll")).alias("ll"),
        (pl.col("brier_total") - pl.col("base_brier")).alias("brier"),
    ).to_numpy()
    rng = np.random.default_rng(20250912)
    draws = np.empty((2000, 2))
    for index in range(len(draws)):
        sample = joined[rng.integers(0, len(joined), len(joined))]
        draws[index] = sample[:, 1:].sum(axis=0) / sample[:, 0].sum()
    return {
        name: {
            "lower_95": float(np.quantile(draws[:, column], 0.025)),
            "median": float(np.quantile(draws[:, column], 0.5)),
            "upper_95": float(np.quantile(draws[:, column], 0.975)),
        }
        for column, name in enumerate(("component_log_loss", "component_brier"))
    }


def _subgroups(
    candidate: pl.DataFrame,
    incumbent: pl.DataFrame,
    target: pl.DataFrame,
    features: pl.DataFrame,
) -> list[dict[str, object]]:
    rows = _score_rows(candidate, target).join(features, on="player_id").join(
        _score_rows(incumbent, target).select(
            "player_id", pl.col("log_loss_total").alias("base_ll"),
            pl.col("brier_total").alias("base_brier"),
        ), on="player_id", validate="1:1",
    )
    age_median = float(rows["age_relative"].median())
    groups = {
        "younger_for_level": pl.col("age_relative") < age_median,
        "older_for_level": pl.col("age_relative") >= age_median,
        "right_handed": (pl.col("left_handed") == 0) & (pl.col("switch_hitter") == 0),
        "left_handed": pl.col("left_handed") == 1,
        "switch_hitter": pl.col("switch_hitter") == 1,
    }
    output = []
    for name, condition in groups.items():
        group = rows.filter(condition)
        pa = float(group["plate_appearances"].sum())
        output.append(
            {
                "group": name, "players": group.height, "target_pa": int(pa),
                "log_loss_delta": float(
                    (group["log_loss_total"] - group["base_ll"]).sum() / pa
                ),
                "brier_delta": float(
                    (group["brier_total"] - group["base_brier"]).sum() / pa
                ),
            }
        )
    return output


def main() -> int:
    source = _components(pl.read_parquet(SOURCE))
    demographics = pl.read_parquet(DEMOGRAPHICS)
    dev_players, dev_base, dev_target = _fold_inputs(source, 2024)
    dev_features = _features(source, demographics, dev_players, 2023)
    dev_base_score = score_component_profiles(
        dev_base, dev_target,
        exposure_column="plate_appearances", component_columns=COMPONENTS,
    )
    fitted = {}
    dev_scores = {"incumbent": dev_base_score}
    for name, columns in FAMILIES.items():
        fitted[name] = _fit(dev_base, dev_target, dev_features, columns)
        candidate = _apply(dev_base, dev_features, columns, fitted[name])
        dev_scores[name] = score_component_profiles(
            candidate, dev_target,
            exposure_column="plate_appearances", component_columns=COMPONENTS,
        )
    eligible = [
        name for name in FAMILIES
        if dev_scores[name]["component_log_loss"] < dev_base_score["component_log_loss"]
        and dev_scores[name]["component_brier_score"] < dev_base_score["component_brier_score"]
    ]
    selected = min(
        eligible, key=lambda name: dev_scores[name]["component_log_loss"]
    ) if eligible else "incumbent"

    outer_players, outer_base, outer_target = _fold_inputs(source, 2025)
    outer_features = _features(source, demographics, outer_players, 2024)
    outer_candidate = (
        outer_base if selected == "incumbent" else
        _apply(outer_base, outer_features, FAMILIES[selected], fitted[selected])
    )
    base_score = score_component_profiles(
        outer_base, outer_target,
        exposure_column="plate_appearances", component_columns=COMPONENTS,
    )
    candidate_score = score_component_profiles(
        outer_candidate, outer_target,
        exposure_column="plate_appearances", component_columns=COMPONENTS,
    )
    bootstrap = _bootstrap(
        _score_rows(outer_candidate, outer_target),
        _score_rows(outer_base, outer_target),
    )
    ll_delta = candidate_score["component_log_loss"] - base_score["component_log_loss"]
    brier_delta = candidate_score["component_brier_score"] - base_score["component_brier_score"]
    promoted = bool(
        selected != "incumbent" and ll_delta < 0 and brier_delta < 0
        and bootstrap["component_log_loss"]["upper_95"] <= 0
        and bootstrap["component_brier"]["upper_95"] <= 0
    )
    report = {
        "report_schema_version": "0.1",
        "status": "hitter_age_level_batting_side_test_complete",
        "contract": "docs/hitter-age-level-batting-side-plan.md",
        "development_2024": {
            "scores": dev_scores, "selected_family": selected,
            "selected_coefficients": None if selected == "incumbent" else {
                feature: {
                    component: float(fitted[selected][i, j])
                    for j, component in enumerate(COMPONENTS[:-1])
                }
                for i, feature in enumerate(FAMILIES[selected])
            },
        },
        "confirmation_2025": {
            "incumbent_score": base_score, "candidate_score": candidate_score,
            "candidate_minus_incumbent_log_loss": ll_delta,
            "candidate_minus_incumbent_brier": brier_delta,
            "player_bootstrap": bootstrap,
            "subgroups": _subgroups(
                outer_candidate, outer_base, outer_target, outer_features
            ),
        },
        "decision": {"promoted": promoted, "selected_family": selected},
        "boundaries": {
            "current_2026_outcomes_used": False,
            "current_physical_measurements_used": False,
            "birth_country_used": False, "outside_fv_used": False,
            "current_values_changed": False,
        },
    }
    OUTPUT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "selected_family": selected, "confirmation_log_loss_delta": ll_delta,
        "confirmation_brier_delta": brier_delta, "bootstrap": bootstrap,
        "promoted": promoted,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
