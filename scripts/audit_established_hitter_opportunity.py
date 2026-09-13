#!/usr/bin/env python3
"""Test recent MLB history and regressed batting quality for incumbent opportunity."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.preprocessing import StandardScaler


HISTORY = Path(
    "reports/generated/career-mlb-outcome-inventory-2009-2025/"
    "tables/mlb_hitting_components_2009_2025.parquet"
)
DEMOGRAPHICS = Path("reports/generated/player-demographics/tables/player-demographics.parquet")
CURRENT = Path(
    "reports/generated/current-mlb-skill-source/2026-09-08/"
    "tables/mlb_hitting_components.parquet"
)
OUT = Path("reports/generated/established-hitter-opportunity-audit")
ARTIFACT = Path("model_artifacts/established-hitter-opportunity-v1.json")
COMPONENT_REGRESSION_PA = 1200.0
ESTABLISHED_SEASON_PA = 200.0
WEIGHTS = {
    "ubb": 0.69,
    "hbp": 0.72,
    "single": 0.89,
    "double": 1.27,
    "triple": 1.62,
    "hr": 2.10,
}
BASE_FEATURES = ("target_age", "log_current_pa")
CANDIDATE_FEATURES = (
    "target_age",
    "log_current_pa",
    "log_prior_1_pa",
    "log_prior_2_pa",
    "regressed_batting_value",
)
HORIZONS = tuple(range(1, 7))
EVALUATION_ORIGINS = (2018, 2019, 2021, 2022, 2023, 2024)


@dataclass(frozen=True)
class Fit:
    features: tuple[str, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]
    logistic_intercept: float
    logistic_coefficients: tuple[float, ...]
    ridge_intercept: float
    ridge_coefficients: tuple[float, ...]


def _season_rows(raw: pl.DataFrame) -> pl.DataFrame:
    return (
        raw.group_by("season", "player_id")
        .agg(
            pl.col("player_name").first(),
            pl.col("batting_plate_appearances").sum().cast(pl.Float64).alias("pa"),
            pl.col("batting_hits").sum().alias("hits"),
            pl.col("batting_doubles").sum().alias("double"),
            pl.col("batting_triples").sum().alias("triple"),
            pl.col("batting_home_runs").sum().alias("hr"),
            pl.col("batting_base_on_balls").sum().alias("bb"),
            pl.col("batting_intentional_walks").sum().alias("ibb"),
            pl.col("batting_hit_by_pitch").sum().alias("hbp"),
        )
        .with_columns(
            (pl.col("bb") - pl.col("ibb")).alias("ubb"),
            (pl.col("hits") - pl.col("double") - pl.col("triple") - pl.col("hr"))
            .alias("single"),
        )
        .with_columns(
            sum(pl.col(key) * value for key, value in WEIGHTS.items()).alias(
                "batting_value"
            )
        )
    )


def _features(raw: pl.DataFrame, demographics: pl.DataFrame) -> pl.DataFrame:
    rows = _season_rows(raw)
    league = rows.group_by("season").agg(
        (pl.col("batting_value").sum() / pl.col("pa").sum()).alias("league_value_rate")
    )
    prior_1 = rows.select(
        "player_id", (pl.col("season") + 1).alias("season"), pl.col("pa").alias("prior_1_pa")
    )
    prior_2 = rows.select(
        "player_id", (pl.col("season") + 2).alias("season"), pl.col("pa").alias("prior_2_pa")
    )
    birth = demographics.select("player_id", pl.col("birth_date").dt.year().alias("birth_year"))
    return (
        rows.join(league, on="season", validate="m:1")
        .join(prior_1, on=["season", "player_id"], how="left", validate="1:1")
        .join(prior_2, on=["season", "player_id"], how="left", validate="1:1")
        .join(birth, on="player_id", how="left", validate="m:1")
        .with_columns(
            pl.col("prior_1_pa").fill_null(0.0),
            pl.col("prior_2_pa").fill_null(0.0),
            (
                (pl.col("batting_value") + COMPONENT_REGRESSION_PA * pl.col("league_value_rate"))
                / (pl.col("pa") + COMPONENT_REGRESSION_PA)
                - pl.col("league_value_rate")
            ).alias("regressed_batting_value"),
            (pl.col("season") - pl.col("birth_year")).cast(pl.Float64).alias("origin_age"),
            pl.col("pa").log1p().alias("log_current_pa"),
        )
        .with_columns(
            pl.col("prior_1_pa").log1p().alias("log_prior_1_pa"),
            pl.col("prior_2_pa").log1p().alias("log_prior_2_pa"),
            (pl.max_horizontal("prior_1_pa", "prior_2_pa") >= ESTABLISHED_SEASON_PA)
            .alias("has_established_mlb_history"),
        )
        .filter(
            pl.col("origin_age").is_not_null()
            & (pl.col("pa") > 0)
            & pl.col("has_established_mlb_history")
        )
    )


def _dataset(features: pl.DataFrame, outcomes: pl.DataFrame, horizon: int) -> pl.DataFrame:
    future = outcomes.select(
        "player_id", (pl.col("season") - horizon).alias("season"), pl.col("pa").alias("future_pa")
    )
    return (
        features.join(future, on=["season", "player_id"], how="left", validate="1:1")
        .with_columns(
            pl.col("future_pa").fill_null(0.0),
            (pl.col("origin_age") + horizon).alias("target_age"),
        )
    )


def _fit(frame: pl.DataFrame, features: tuple[str, ...]) -> Fit:
    x = frame.select(features).to_numpy()
    y = frame.get_column("future_pa").to_numpy()
    scaler = StandardScaler().fit(x)
    z = scaler.transform(x)
    logistic = LogisticRegression(C=1.0, max_iter=2000, random_state=0).fit(z, y > 0)
    positive = y > 0
    ridge = Ridge(alpha=10.0).fit(z[positive], np.log1p(y[positive]))
    return Fit(
        features=features,
        means=tuple(float(value) for value in scaler.mean_),
        scales=tuple(float(value) for value in scaler.scale_),
        logistic_intercept=float(logistic.intercept_[0]),
        logistic_coefficients=tuple(float(value) for value in logistic.coef_[0]),
        ridge_intercept=float(ridge.intercept_),
        ridge_coefficients=tuple(float(value) for value in ridge.coef_),
    )


def _score(frame: pl.DataFrame, fit: Fit) -> pl.DataFrame:
    x = frame.select(fit.features).to_numpy()
    z = (x - np.asarray(fit.means)) / np.asarray(fit.scales)
    logits = fit.logistic_intercept + z @ np.asarray(fit.logistic_coefficients)
    probability = 1.0 / (1.0 + np.exp(-np.clip(logits, -30.0, 30.0)))
    conditional = np.expm1(fit.ridge_intercept + z @ np.asarray(fit.ridge_coefficients))
    conditional = np.clip(conditional, 1.0, 700.0)
    return frame.with_columns(
        pl.Series("predicted_probability", probability),
        pl.Series("predicted_conditional_pa", conditional),
        pl.Series("predicted_pa", probability * conditional),
    )


def _metrics(scored: pl.DataFrame) -> dict[str, float]:
    observed = scored.get_column("future_pa").to_numpy()
    active = observed > 0
    probability = np.clip(scored.get_column("predicted_probability").to_numpy(), 1e-12, 1 - 1e-12)
    predicted = scored.get_column("predicted_pa").to_numpy()
    predicted_conditional = scored.get_column("predicted_conditional_pa").to_numpy()
    return {
        "players": float(scored.height),
        "active_rate": float(active.mean()),
        "brier": float(np.mean((probability - active) ** 2)),
        "log_loss": float(-np.mean(active * np.log(probability) + (~active) * np.log(1 - probability))),
        "pa_mae": float(np.mean(np.abs(predicted - observed))),
        "conditional_pa_mae_active": float(
            np.mean(np.abs(predicted_conditional[active] - observed[active]))
        ),
        "mean_observed_pa": float(observed.mean()),
        "mean_predicted_pa": float(predicted.mean()),
    }


def main() -> int:
    raw = pl.read_parquet(HISTORY)
    demographics = pl.read_parquet(DEMOGRAPHICS)
    season_rows = _season_rows(raw)
    features = _features(raw, demographics)
    evaluations = []
    pooled: dict[str, list[pl.DataFrame]] = {"baseline": [], "candidate": []}
    for horizon in HORIZONS:
        data = _dataset(features, season_rows, horizon)
        for origin in EVALUATION_ORIGINS:
            if origin + horizon > 2025:
                continue
            train = data.filter(
                (pl.col("season") >= 2012)
                & (pl.col("season") < origin)
                & (pl.col("season") != 2020)
            )
            test = data.filter(pl.col("season") == origin)
            if train.is_empty() or test.is_empty():
                continue
            for name, columns in (("baseline", BASE_FEATURES), ("candidate", CANDIDATE_FEATURES)):
                scored = _score(test, _fit(train, columns)).with_columns(
                    pl.lit(name).alias("model"),
                    pl.lit(horizon).alias("horizon"),
                    pl.lit(origin).alias("evaluation_origin"),
                )
                pooled[name].append(scored)
                evaluations.append({
                    "model": name,
                    "horizon": horizon,
                    "evaluation_origin": origin,
                    **_metrics(scored),
                })
    pooled_metrics = {name: _metrics(pl.concat(rows)) for name, rows in pooled.items()}
    horizon_metrics = []
    for horizon in HORIZONS:
        for name in ("baseline", "candidate"):
            selected = [row for row in pooled[name] if row.item(0, "horizon") == horizon]
            if selected:
                horizon_metrics.append({"horizon": horizon, "model": name, **_metrics(pl.concat(selected))})
    final_fits = {}
    current_scores = []
    all_current = pl.concat(
        [
            raw,
            pl.read_parquet(CURRENT)
            .filter(pl.col("season") == 2026)
            .select(raw.columns),
        ],
        how="vertical_relaxed",
    )
    current_features = _features(all_current, demographics).filter(pl.col("season") == 2026)
    for horizon in HORIZONS:
        data = _dataset(features, season_rows, horizon)
        train = data.filter(
            (pl.col("season") >= 2012)
            & (pl.col("season") + horizon <= 2025)
            & (pl.col("season") != 2020)
        )
        fit = _fit(train, CANDIDATE_FEATURES)
        final_fits[str(horizon)] = asdict(fit)
        score_input = current_features.with_columns(
            (pl.col("origin_age") + horizon).alias("target_age")
        )
        current_scores.append(
            _score(score_input, fit).select(
                "player_id", "player_name", pl.lit(horizon).alias("horizon"),
                "pa", "prior_1_pa", "prior_2_pa", "regressed_batting_value",
                "predicted_probability", "predicted_conditional_pa", "predicted_pa",
            )
        )
    candidate = pooled_metrics["candidate"]
    baseline = pooled_metrics["baseline"]
    probability_wins = sum(
        row["log_loss"] < next(
            other["log_loss"] for other in horizon_metrics
            if other["horizon"] == row["horizon"] and other["model"] == "baseline"
        )
        and row["brier"] < next(
            other["brier"] for other in horizon_metrics
            if other["horizon"] == row["horizon"] and other["model"] == "baseline"
        )
        for row in horizon_metrics if row["model"] == "candidate"
    )
    promotion = (
        candidate["log_loss"] < baseline["log_loss"]
        and candidate["brier"] < baseline["brier"]
        and probability_wins == len(HORIZONS)
    )
    OUT.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(evaluations).write_parquet(OUT / "fold_metrics.parquet")
    pl.DataFrame(horizon_metrics).write_parquet(OUT / "horizon_metrics.parquet")
    current = pl.concat(current_scores).sort(["player_id", "horizon"])
    current.write_parquet(OUT / "current_scores.parquet")
    report = {
        "report_schema_version": "0.1",
        "gate": "established_hitter_recent_history_and_talent_opportunity",
        "population": (
            "players with MLB PA in the origin season and at least one 200-PA "
            "MLB season in the prior two years"
        ),
        "established_season_pa": ESTABLISHED_SEASON_PA,
        "component_regression_pa": COMPONENT_REGRESSION_PA,
        "baseline_features": BASE_FEATURES,
        "candidate_features": CANDIDATE_FEATURES,
        "pooled_metrics": pooled_metrics,
        "horizon_metrics": horizon_metrics,
        "promotion": "pass_probability_only" if promotion else "reject",
        "boundaries": {
            "publication_rank_or_fv_used": False,
            "contract_terms_used": False,
            "future_information_used_as_predictor": False,
            "2020_origin_excluded": True,
            "quality_is_heavily_regressed": True,
            "conditional_workload_promoted": False,
            "existing_validated_conditional_workload_retained": True,
        },
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if promotion:
        ARTIFACT.write_text(
            json.dumps({
                "artifact_schema_version": "0.1",
                "status": "promoted_established_hitter_active_probability_challenger",
                "source_report": (OUT / "report.json").as_posix(),
                "fits": final_fits,
            }, indent=2) + "\n",
            encoding="utf-8",
        )
    judge = current.filter(pl.col("player_id") == 592450)
    print(json.dumps({
        "promotion": report["promotion"],
        "pooled_metrics": pooled_metrics,
        "horizon_metrics": horizon_metrics,
        "aaron_judge": judge.to_dicts(),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
