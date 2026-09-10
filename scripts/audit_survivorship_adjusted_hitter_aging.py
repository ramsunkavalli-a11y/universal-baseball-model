#!/usr/bin/env python3
"""Fit and test a survivor-weighted hitter component aging curve."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_v2_model import marcel_age_factor


EVENTS = ("ubb", "hbp", "single", "double", "triple", "hr", "other")
MODELED = EVENTS[:-1]
DEVELOPMENT_MAX_TARGET = 2021
VALIDATION_START = 2022
OUTPUT = Path("docs/survivorship-adjusted-hitter-aging-result.json")


def _ages(roots: tuple[Path, ...]) -> pl.DataFrame:
    rows: dict[tuple[int, int], float] = {}
    for root in roots:
        for path in sorted(root.glob("hitting-*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            for block in payload.get("stats") or []:
                for split in block.get("splits") or []:
                    player = split.get("player") or split.get("person") or {}
                    stat = split.get("stat") or {}
                    if player.get("id") is None or stat.get("age") is None:
                        continue
                    key = (int(split.get("season") or path.name.split("-")[1]), int(player["id"]))
                    age = float(stat["age"])
                    if key in rows and rows[key] != age:
                        raise ValueError(f"conflicting hitter age for {key}")
                    rows[key] = age
    return pl.DataFrame([
        {"season": season, "player_id": player_id, "age": age}
        for (season, player_id), age in sorted(rows.items())
    ])


def _profiles(history: pl.DataFrame, ages: pl.DataFrame) -> pl.DataFrame:
    source = history.filter(pl.col("season") >= 2015).select(
        "season",
        "player_id",
        pl.col("batting_plate_appearances").alias("pa"),
        (pl.col("batting_base_on_balls") - pl.col("batting_intentional_walks")).alias("ubb"),
        pl.col("batting_hit_by_pitch").alias("hbp"),
        (
            pl.col("batting_hits") - pl.col("batting_doubles")
            - pl.col("batting_triples") - pl.col("batting_home_runs")
        ).alias("single"),
        pl.col("batting_doubles").alias("double"),
        pl.col("batting_triples").alias("triple"),
        pl.col("batting_home_runs").alias("hr"),
    ).with_columns(
        (pl.col("pa") - pl.sum_horizontal(*MODELED)).alias("other")
    ).filter(pl.col("pa") > 0)
    if source.filter(
        pl.any_horizontal(*(pl.col(event) < 0 for event in EVENTS))
        | (pl.sum_horizontal(*EVENTS) != pl.col("pa"))
    ).height:
        raise ValueError("hitter component history does not reconcile")
    priors = source.group_by("season").agg(
        pl.col("pa").sum().alias("league_pa"),
        *(pl.col(event).sum().alias(f"league_{event}") for event in EVENTS),
    ).with_columns(
        *((pl.col(f"league_{event}") / pl.col("league_pa")).alias(f"prior_{event}") for event in EVENTS)
    )
    return source.join(priors, on="season", validate="m:1").with_columns(
        *(
            (
                (pl.col(event) + 200.0 * pl.col(f"prior_{event}"))
                / (pl.col("pa") + 200.0)
            ).alias(f"p_{event}")
            for event in EVENTS
        )
    ).join(ages, on=["season", "player_id"], how="inner", validate="1:1")


def _pairs(profiles: pl.DataFrame) -> pl.DataFrame:
    target = profiles.select(
        pl.col("season").alias("target_season"), "player_id",
        pl.col("age").alias("target_age"), pl.col("pa").alias("target_pa"),
        *(pl.col(event).alias(f"target_count_{event}") for event in EVENTS),
        *(pl.col(f"p_{event}").alias(f"target_p_{event}") for event in EVENTS),
    )
    return profiles.select(
        pl.col("season").alias("source_season"), "player_id",
        pl.col("age").alias("source_age"), pl.col("pa").alias("source_pa"),
        *(pl.col(f"p_{event}").alias(f"source_p_{event}") for event in EVENTS),
    ).with_columns((pl.col("source_season") + 1).alias("target_season")).join(
        target, on=["target_season", "player_id"], validate="1:1"
    ).with_columns(
        (2.0 * pl.col("source_pa") * pl.col("target_pa")
         / (pl.col("source_pa") + pl.col("target_pa"))).clip(upper_bound=600.0).alias("pair_weight")
    ).filter(pl.col("source_age").is_between(18, 45)).sort(["target_season", "player_id"])


def _pa_band(pa: float) -> str:
    if pa < 100:
        return "001_099"
    if pa < 300:
        return "100_299"
    if pa < 600:
        return "300_599"
    return "600_plus"


def _return_weights(profiles: pl.DataFrame, pairs: pl.DataFrame) -> tuple[pl.DataFrame, dict[str, object]]:
    keys = set(profiles.select("season", "player_id").iter_rows())
    rows = []
    for row in profiles.iter_rows(named=True):
        target = int(row["season"]) + 1
        if target > 2025:
            continue
        rows.append({
            "target_season": target,
            "player_id": int(row["player_id"]),
            "age_band": int(math.floor(float(row["age"]) / 3.0) * 3),
            "pa_band": _pa_band(float(row["pa"])),
            "returned": (target, int(row["player_id"])) in keys,
        })
    returns = pl.DataFrame(rows)
    train = returns.filter(pl.col("target_season") <= DEVELOPMENT_MAX_TARGET)
    population = float(train["returned"].mean())
    lookup: dict[tuple[str, int | None], float] = {}
    for band_rows in train.partition_by("pa_band"):
        band = str(band_rows.item(0, "pa_band"))
        band_p = (float(band_rows["returned"].sum()) + 50 * population) / (band_rows.height + 50)
        lookup[(band, None)] = band_p
        for age_rows in band_rows.partition_by("age_band"):
            age = int(age_rows.item(0, "age_band"))
            lookup[(band, age)] = (float(age_rows["returned"].sum()) + 50 * band_p) / (age_rows.height + 50)
    weights = []
    probabilities = []
    for row in pairs.iter_rows(named=True):
        band = _pa_band(float(row["source_pa"]))
        age = int(math.floor(float(row["source_age"]) / 3.0) * 3)
        probability = lookup.get((band, age), lookup.get((band, None), population))
        probabilities.append(probability)
        weights.append(min(4.0, population / max(0.05, probability)))
    weighted = pairs.with_columns(
        pl.Series("predicted_return_probability", probabilities),
        pl.Series("survivorship_weight", weights),
    )
    validation = returns.filter(pl.col("target_season") >= VALIDATION_START)
    validation_predictions = []
    for row in validation.iter_rows(named=True):
        validation_predictions.append(lookup.get(
            (str(row["pa_band"]), int(row["age_band"])),
            lookup.get((str(row["pa_band"]), None), population),
        ))
    p = np.clip(np.asarray(validation_predictions), 1e-12, 1 - 1e-12)
    y = validation["returned"].cast(pl.Float64).to_numpy()
    return weighted, {
        "development_rows": train.height,
        "validation_rows": validation.height,
        "development_population_probability": population,
        "validation_return_rate": float(y.mean()),
        "model_brier": float(np.mean((p - y) ** 2)),
        "population_brier": float(np.mean((population - y) ** 2)),
        "model_log_loss": float(np.mean(-(y * np.log(p) + (1 - y) * np.log(1 - p)))),
        "population_log_loss": float(np.mean(-(y * math.log(population) + (1 - y) * math.log(1 - population)))),
    }


def _fit(pairs: pl.DataFrame, weight_column: str | None) -> dict[str, tuple[float, float, float]]:
    train = pairs.filter(pl.col("target_season") <= DEVELOPMENT_MAX_TARGET)
    x = (train["source_age"].to_numpy() - 28.0) / 10.0
    design = np.column_stack([np.ones(len(x)), x, x * x])
    weights = train["pair_weight"].to_numpy()
    if weight_column:
        weights = weights * train[weight_column].to_numpy()
    coefficients = {}
    for event in MODELED:
        response = np.log(train[f"target_p_{event}"].to_numpy() / train["target_p_other"].to_numpy()) - np.log(train[f"source_p_{event}"].to_numpy() / train["source_p_other"].to_numpy())
        coefficients[event] = tuple(float(v) for v in np.linalg.solve(
            (design * weights[:, None]).T @ design + np.eye(3) * 20_000.0,
            (design * weights[:, None]).T @ response,
        ))
    return coefficients


def _predict(source: dict[str, float], source_age: float, target_age: float, method, coefficients=None) -> dict[str, float]:
    if method == "none":
        return source
    if method == "marcel":
        factor = marcel_age_factor(target_age)
        raw = {event: source[event] * (factor if event != "other" else 1.0) for event in EVENTS}
        total = sum(raw.values())
        return {event: raw[event] / total for event in EVENTS}
    assert coefficients is not None
    x = (source_age - 28.0) / 10.0
    ratios = {}
    for event in MODELED:
        beta = coefficients[event]
        shift = beta[0] + beta[1] * x + beta[2] * x * x
        ratios[event] = math.exp(math.log(source[event] / source["other"]) + shift)
    other = 1.0 / (1.0 + sum(ratios.values()))
    return {**{event: ratio * other for event, ratio in ratios.items()}, "other": other}


def _loss(pairs: pl.DataFrame, method: str, coefficients=None, weighted: bool = False) -> float:
    loss = 0.0
    exposure = 0.0
    for row in pairs.iter_rows(named=True):
        source = {event: float(row[f"source_p_{event}"]) for event in EVENTS}
        predicted = _predict(source, float(row["source_age"]), float(row["target_age"]), method, coefficients)
        weight = float(row["survivorship_weight"]) if weighted else 1.0
        exposure += float(row["target_pa"]) * weight
        loss -= sum(float(row[f"target_count_{event}"]) * weight * math.log(predicted[event]) for event in EVENTS)
    return loss / exposure


def main() -> int:
    root = Path("reports/generated")
    history = pl.read_parquet(root / "career-mlb-outcome-inventory-2009-2025/tables/mlb_hitting_components_2009_2025.parquet")
    ages = _ages((
        root / "career-mlb-outcome-inventory/raw",
        root / "current-mlb-skill-source/2026-09-08/raw",
    ))
    profiles = _profiles(history, ages)
    pairs, return_scores = _return_weights(profiles, _pairs(profiles))
    validation = pairs.filter(pl.col("target_season") >= VALIDATION_START)
    unweighted = _fit(pairs, None)
    adjusted = _fit(pairs, "survivorship_weight")
    scoreboards = {}
    for weighted in (False, True):
        scoreboards["survival_standardized" if weighted else "raw_returner"] = {
            "no_aging": _loss(validation, "none", weighted=weighted),
            "marcel": _loss(validation, "marcel", weighted=weighted),
            "unweighted_fitted": _loss(validation, "fitted", unweighted, weighted),
            "survivorship_adjusted_fitted": _loss(validation, "fitted", adjusted, weighted),
        }
    standard = scoreboards["survival_standardized"]
    selected = standard["survivorship_adjusted_fitted"] < min(
        standard["no_aging"], standard["marcel"], standard["unweighted_fitted"]
    )
    report = {
        "report_schema_version": "0.1",
        "status": "survivorship_adjusted_hitter_aging_test_complete",
        "development_target_seasons": [2016, DEVELOPMENT_MAX_TARGET],
        "validation_target_seasons": [VALIDATION_START, 2025],
        "validation_pairs": validation.height,
        "return_model": return_scores,
        "log_loss": scoreboards,
        "adjusted_selected": selected,
        "selection_rule": "adjusted curve must beat no aging, Marcel and the unweighted fitted curve on survival-standardized validation log loss",
        "outside_fv_used": False,
        "production_changed": False,
    }
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
