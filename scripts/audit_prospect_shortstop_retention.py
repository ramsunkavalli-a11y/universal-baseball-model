#!/usr/bin/env python3
"""Test a chronology-safe player-level prospect position challenger."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from universal_baseball.player_value_positional_adjustment import (
    POSITIONAL_RUNS_PER_162,
)


LEVEL_SCORE = {
    "ROOKIE_COMPLEX": 0.0,
    "SINGLE_A": 1.0,
    "HIGH_A": 2.0,
    "AA": 3.0,
    "AAA": 4.0,
}
POSITIONS = tuple(POSITIONAL_RUNS_PER_162)
ALPHAS = (1.0, 10.0, 100.0)
FEATURE_SETS = {
    "workload": ("baseline_runs", "age", "level_score", "log_exposure"),
    "role_detail": (
        "baseline_runs",
        "age",
        "level_score",
        "log_exposure",
        "position_count",
        *(f"share_{position}" for position in POSITIONS),
    ),
}


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--historical-path",
        type=Path,
        default=Path(
            "reports/generated/position-capacity-source/historical/reports/generated/"
            "position-role-historical-source/tables/historical_fielding_usage.parquet"
        ),
    )
    parser.add_argument(
        "--confirmation-path",
        type=Path,
        default=Path(
            "reports/generated/position-capacity-source/2025/reports/generated/"
            "position-role-2025-confirmation-source/tables/"
            "position_role_2025_fielding_usage.parquet"
        ),
    )
    parser.add_argument(
        "--people-path",
        type=Path,
        default=Path(
            "reports/generated/historical-people-control/2025-10-15/tables/people.parquet"
        ),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/prospect-shortstop-retention-result.json"),
    )
    return parser.parse_args()


def _exposure_expression() -> pl.Expr:
    return (
        pl.when(pl.col("games_started") > 0)
        .then(pl.col("games_started"))
        .otherwise(pl.col("games_played"))
        .cast(pl.Float64)
    )


def _position_profile(frame: pl.DataFrame, *, origin_year: int) -> pl.DataFrame:
    grouped = (
        frame.filter(pl.col("position_abbreviation").is_in(POSITIONS))
        .with_columns(_exposure_expression().alias("exposure"))
        .group_by("player_id", "position_abbreviation")
        .agg(pl.col("exposure").sum())
    )
    totals = grouped.group_by("player_id").agg(
        pl.col("exposure").sum().alias("total_exposure"),
        pl.len().alias("position_count"),
    )
    dominant = (
        grouped.sort(
            ["player_id", "exposure", "position_abbreviation"],
            descending=[False, True, False],
        )
        .unique("player_id", keep="first", maintain_order=True)
        .select(
            "player_id",
            pl.col("position_abbreviation").alias("dominant_position"),
        )
    )
    shares = grouped.join(totals, on="player_id").with_columns(
        (pl.col("exposure") / pl.col("total_exposure")).alias("share")
    )
    wide = shares.pivot(
        on="position_abbreviation", index="player_id", values="share"
    )
    missing = [position for position in POSITIONS if position not in wide.columns]
    if missing:
        wide = wide.with_columns(*(pl.lit(0.0).alias(value) for value in missing))
    wide = wide.select(
        "player_id", *(pl.col(position).fill_null(0.0).alias(f"share_{position}") for position in POSITIONS)
    )
    runs = shares.with_columns(
        pl.col("position_abbreviation")
        .replace_strict(dict(POSITIONAL_RUNS_PER_162), return_dtype=pl.Float64)
        .alias("position_runs")
    ).group_by("player_id").agg(
        (pl.col("position_runs") * pl.col("share")).sum().alias("baseline_runs")
    )
    levels = (
        frame.with_columns(
            pl.col("level_group")
            .replace_strict(LEVEL_SCORE, default=None, return_dtype=pl.Float64)
            .alias("level_score")
        )
        .group_by("player_id")
        .agg(pl.col("level_score").max())
    )
    return (
        totals.join(dominant, on="player_id")
        .join(wide, on="player_id")
        .join(runs, on="player_id")
        .join(levels, on="player_id")
        .with_columns(
            pl.col("total_exposure").log1p().alias("log_exposure"),
            pl.lit(origin_year).alias("origin_year"),
        )
    )


def _target_profile(frame: pl.DataFrame) -> pl.DataFrame:
    grouped = (
        frame.filter(pl.col("position_abbreviation").is_in(POSITIONS))
        .with_columns(_exposure_expression().alias("exposure"))
        .group_by("player_id", "position_abbreviation")
        .agg(pl.col("exposure").sum())
        .with_columns(
            pl.col("position_abbreviation")
            .replace_strict(dict(POSITIONAL_RUNS_PER_162), return_dtype=pl.Float64)
            .alias("position_runs")
        )
    )
    totals = grouped.group_by("player_id").agg(pl.col("exposure").sum().alias("target_exposure"))
    weighted = grouped.join(totals, on="player_id").group_by("player_id").agg(
        (
            (pl.col("position_runs") * pl.col("exposure")).sum()
            / pl.col("target_exposure").first()
        ).alias("target_runs")
    )
    dominant = (
        grouped.sort(
            ["player_id", "exposure", "position_abbreviation"],
            descending=[False, True, False],
        )
        .unique("player_id", keep="first", maintain_order=True)
        .select(
            "player_id",
            pl.col("position_abbreviation").alias("target_dominant_position"),
        )
    )
    return weighted.join(dominant, on="player_id")


def _cohort(usage: pl.DataFrame, people: pl.DataFrame, origin_year: int) -> pl.DataFrame:
    origin_frame = usage.filter(
        (pl.col("season") == origin_year) & (pl.col("level_group") != "MLB")
    )
    target_frame = usage.filter(
        (pl.col("season") == origin_year + 1) & (pl.col("level_group") == "MLB")
    )
    age = people.select("player_id", "birth_date").with_columns(
        (
            (pl.date(origin_year, 7, 1) - pl.col("birth_date")).dt.total_days()
            / 365.2425
        ).alias("age")
    ).select("player_id", "age")
    return (
        _position_profile(origin_frame, origin_year=origin_year)
        .join(_target_profile(target_frame), on="player_id", how="inner")
        .join(age, on="player_id", how="inner")
        .drop_nulls(["age", "level_score"])
        .with_columns(
            (
                (pl.col("dominant_position") == "SS")
                & (pl.col("target_dominant_position") == "SS")
            ).alias("retained_shortstop")
        )
        .sort("player_id")
    )


def _scores(target: np.ndarray, prediction: np.ndarray) -> dict[str, float]:
    error = prediction - target
    return {
        "mae": float(np.abs(error).mean()),
        "rmse": float(np.sqrt(np.square(error).mean())),
        "bias": float(error.mean()),
    }


def _score_rows(frame: pl.DataFrame, prediction: np.ndarray) -> dict[str, object]:
    target = frame.get_column("target_runs").to_numpy()
    baseline = frame.get_column("baseline_runs").to_numpy()
    ss_mask = frame.get_column("dominant_position").to_numpy() == "SS"
    return {
        "players": frame.height,
        "shortstop_origin_players": int(ss_mask.sum()),
        "baseline": _scores(target, baseline),
        "candidate": _scores(target, prediction),
        "shortstop_baseline": _scores(target[ss_mask], baseline[ss_mask]),
        "shortstop_candidate": _scores(target[ss_mask], prediction[ss_mask]),
    }


def _passes(score: dict[str, object]) -> bool:
    return bool(
        score["candidate"]["mae"] < score["baseline"]["mae"]
        and score["candidate"]["rmse"] < score["baseline"]["rmse"]
        and score["shortstop_candidate"]["mae"] < score["shortstop_baseline"]["mae"]
        and score["shortstop_candidate"]["rmse"] < score["shortstop_baseline"]["rmse"]
    )


def _by_position(frame: pl.DataFrame, prediction: np.ndarray) -> list[dict[str, object]]:
    scored = frame.with_columns(pl.Series("candidate_prediction", prediction))
    rows = []
    for position in sorted(scored.get_column("dominant_position").unique().to_list()):
        group = scored.filter(pl.col("dominant_position") == position)
        target = group.get_column("target_runs").to_numpy()
        rows.append(
            {
                "dominant_position": position,
                "players": group.height,
                "baseline": _scores(target, group.get_column("baseline_runs").to_numpy()),
                "candidate": _scores(
                    target, group.get_column("candidate_prediction").to_numpy()
                ),
            }
        )
    return rows


def _fit_predict(
    training: pl.DataFrame,
    evaluation: pl.DataFrame,
    features: tuple[str, ...],
    alpha: float,
) -> tuple[object, np.ndarray]:
    model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
    model.fit(training.select(features).to_numpy(), training.get_column("target_runs").to_numpy())
    return model, model.predict(evaluation.select(features).to_numpy())


def _bootstrap(frame: pl.DataFrame, prediction: np.ndarray) -> dict[str, object]:
    target = frame.get_column("target_runs").to_numpy()
    baseline = frame.get_column("baseline_runs").to_numpy()
    rng = np.random.default_rng(20260910)

    def summarize(mask: np.ndarray) -> dict[str, object]:
        y, base, candidate = target[mask], baseline[mask], prediction[mask]
        indices = rng.integers(0, len(y), size=(2_000, len(y)))
        base_error = base[indices] - y[indices]
        candidate_error = candidate[indices] - y[indices]
        mae = np.abs(candidate_error).mean(axis=1) - np.abs(base_error).mean(axis=1)
        rmse = np.sqrt(np.square(candidate_error).mean(axis=1)) - np.sqrt(
            np.square(base_error).mean(axis=1)
        )

        def metric(values: np.ndarray) -> dict[str, float]:
            return {
                "difference": float(values.mean()),
                "ci_low": float(np.quantile(values, 0.025)),
                "ci_high": float(np.quantile(values, 0.975)),
                "probability_candidate_better": float(np.mean(values < 0)),
            }

        return {"players": len(y), "mae": metric(mae), "rmse": metric(rmse)}

    all_mask = np.ones(frame.height, dtype=bool)
    ss_mask = frame.get_column("dominant_position").to_numpy() == "SS"
    return {"all": summarize(all_mask), "shortstop_origin": summarize(ss_mask)}


def _retention_diagnostic(
    training: pl.DataFrame,
    evaluation: pl.DataFrame,
    features: tuple[str, ...],
) -> dict[str, object]:
    train = training.filter(pl.col("dominant_position") == "SS")
    evaluate = evaluation.filter(pl.col("dominant_position") == "SS")
    y_train = train.get_column("retained_shortstop").cast(pl.Int8).to_numpy()
    y = evaluate.get_column("retained_shortstop").cast(pl.Int8).to_numpy()
    baseline = np.repeat(float(y_train.mean()), len(y))
    model = make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=2_000))
    model.fit(train.select(features).to_numpy(), y_train)
    candidate = model.predict_proba(evaluate.select(features).to_numpy())[:, 1]

    def probability_scores(probability: np.ndarray) -> dict[str, float]:
        clipped = np.clip(probability, 1e-9, 1 - 1e-9)
        return {
            "log_loss": float(-(y * np.log(clipped) + (1 - y) * np.log(1 - clipped)).mean()),
            "brier": float(np.square(probability - y).mean()),
            "mean_probability": float(probability.mean()),
            "observed_rate": float(y.mean()),
        }

    return {
        "training_players": train.height,
        "evaluation_players": evaluate.height,
        "baseline": probability_scores(baseline),
        "candidate": probability_scores(candidate),
    }


def main() -> int:
    args = _args()
    usage = pl.concat(
        [pl.read_parquet(args.historical_path), pl.read_parquet(args.confirmation_path)],
        how="vertical_relaxed",
    )
    people = pl.read_parquet(args.people_path)
    cohorts = {year: _cohort(usage, people, year) for year in range(2021, 2025)}
    development_training = pl.concat([cohorts[2021], cohorts[2022]])
    development_rows = []
    for feature_name, features in FEATURE_SETS.items():
        for alpha in ALPHAS:
            _, prediction = _fit_predict(development_training, cohorts[2023], features, alpha)
            score = _score_rows(cohorts[2023], prediction)
            development_rows.append(
                {
                    "feature_set": feature_name,
                    "features": list(features),
                    "alpha": alpha,
                    **score,
                    "passed": _passes(score),
                }
            )
    order = {"workload": 0, "role_detail": 1}
    passing = [row for row in development_rows if row["passed"]]
    selected = min(
        passing,
        key=lambda row: (
            row["candidate"]["mae"],
            order[row["feature_set"]],
            -row["alpha"],
        ),
        default=None,
    )
    outer_training = pl.concat([cohorts[2021], cohorts[2022], cohorts[2023]])
    if selected is None:
        selected_name, selected_alpha = "workload", 100.0
    else:
        selected_name, selected_alpha = selected["feature_set"], selected["alpha"]
    selected_features = FEATURE_SETS[selected_name]
    model, outer_prediction = _fit_predict(
        outer_training, cohorts[2024], selected_features, selected_alpha
    )
    outer = _score_rows(cohorts[2024], outer_prediction)
    coefficients = dict(
        zip(
            selected_features,
            model.named_steps["ridge"].coef_.tolist(),
            strict=True,
        )
    )
    report = {
        "report_schema_version": "0.1",
        "as_of_date": args.as_of_date.isoformat(),
        "status": "prospect_shortstop_retention_outer_test_complete",
        "contract": "docs/prospect-shortstop-retention-plan.md",
        "chronology": {
            "development_train_origins": [2021, 2022],
            "development_evaluate_origin": 2023,
            "outer_train_origins": [2021, 2022, 2023],
            "outer_evaluate_origin": 2024,
            "destination_horizon_seasons": 1,
        },
        "cohort_players": {str(year): frame.height for year, frame in cohorts.items()},
        "development": development_rows,
        "selected": {
            "development_candidate_passed": selected is not None,
            "feature_set": selected_name,
            "features": list(selected_features),
            "alpha": selected_alpha,
            "standardized_coefficients": coefficients,
        },
        "outer": outer,
        "outer_by_dominant_position": _by_position(cohorts[2024], outer_prediction),
        "outer_bootstrap": _bootstrap(cohorts[2024], outer_prediction),
        "shortstop_retention_diagnostic": _retention_diagnostic(
            outer_training, cohorts[2024], selected_features
        ),
        "decision": {
            "private_position_sensitivity_authorized": selected is not None and _passes(outer),
            "published_value_change_authorized": False,
        },
        "boundaries": {
            "outside_fv_used": False,
            "non_arrivals_included": False,
            "future_label_overlap_used": False,
            "organization_or_depth_used": False,
            "named_player_adjustment_used": False,
        },
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
