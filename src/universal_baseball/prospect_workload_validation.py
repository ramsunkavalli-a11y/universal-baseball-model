"""Retrospective cohort diagnostics for conditional prospect workload distributions."""

from __future__ import annotations

import math

import numpy as np
import polars as pl


ERA_WEIGHTING_RULES = ("equal", "half_life_1", "half_life_2", "latest_2")
ROLE_RULES = ("supported_role", "pooled")


def classify_pitcher_path_role(starts: float, games: float, workload: float) -> str:
    """Classify a pitcher path without treating every recorded start as rotation work."""

    if not all(math.isfinite(value) and value >= 0 for value in (starts, games, workload)):
        raise ValueError("pitcher role inputs must be finite and nonnegative")
    if workload <= 0 or games <= 0:
        return "inactive"
    if starts <= 0:
        return "relief"
    start_share = starts / games
    workload_per_start = workload / starts
    if start_share >= 0.5 and workload_per_start >= 18.0:
        return "rotation"
    if start_share >= 0.5:
        return "opener"
    return "bulk_swing"


def build_pitcher_environment_asof_scores(
    annual_paths: pl.DataFrame,
    pitcher_seasons: pl.DataFrame,
    *,
    evaluation_years: tuple[int, ...] = (2018, 2019),
    minimum_role_players: int = 30,
    trend_years: int = 5,
) -> pl.DataFrame:
    """Score raw and league-environment-scaled complete pitcher workload paths."""

    required_paths = {
        "path_player_id", "player_type", "debut_year", "window_end_year",
        "outcome_tier_v2", "path_year", "source_season", "adjusted_workload",
        "games", "starts",
    }
    required_seasons = {"season", "player_id", "pitching_bf"}
    if missing := sorted(required_paths - set(annual_paths.columns)):
        raise ValueError(f"annual workload paths missing fields: {missing}")
    if missing := sorted(required_seasons - set(pitcher_seasons.columns)):
        raise ValueError(f"pitcher seasons missing fields: {missing}")
    if not evaluation_years or minimum_role_players < 1 or trend_years < 3:
        raise ValueError("invalid environment-score configuration")

    paths = annual_paths.filter(pl.col("player_type") == "pitcher")
    environment = (
        pitcher_seasons.filter(pl.col("pitching_bf") > 0)
        .group_by("season")
        .agg(
            pl.col("pitching_bf").sum().alias("league_bf"),
            pl.col("player_id").n_unique().alias("active_pitchers"),
        )
        .with_columns(
            (pl.col("league_bf") / pl.col("active_pitchers")).alias("mean_bf")
        )
        .sort("season")
    )
    environment_lookup = {
        int(row["season"]): float(row["mean_bf"])
        for row in environment.iter_rows(named=True)
    }
    rows: list[dict[str, object]] = []
    for evaluation_year in evaluation_years:
        training = paths.filter(pl.col("window_end_year") < evaluation_year)
        evaluation = paths.filter(pl.col("debut_year") == evaluation_year)
        if training.is_empty() or evaluation.is_empty():
            raise ValueError(f"empty pitcher environment fold {evaluation_year}")
        history = environment.filter(
            (pl.col("season") < evaluation_year) & (pl.col("season") != 2020)
        ).tail(trend_years)
        if history.height < 3:
            raise ValueError(f"insufficient environment history for {evaluation_year}")
        years = history["season"].to_numpy().astype(float)
        log_mean = np.log(history["mean_bf"].to_numpy().astype(float))
        slope, intercept = np.polyfit(years, log_mean, 1)
        slope = float(np.clip(slope, math.log(0.95), math.log(1.05)))
        forecast_environment = {
            season: float(math.exp(intercept + slope * season))
            for season in range(evaluation_year, evaluation_year + 6)
        }

        training_players = []
        for key, group in training.group_by("path_player_id", maintain_order=True):
            player_id = int(key[0] if isinstance(key, tuple) else key)
            first = group.row(0, named=True)
            total_workload = float(group["adjusted_workload"].sum())
            total_games = float(group["games"].sum())
            total_starts = float(group["starts"].sum())
            scaled_total = 0.0
            for annual in group.iter_rows(named=True):
                source_mean = environment_lookup.get(int(annual["source_season"]))
                if source_mean is None or source_mean <= 0:
                    raise ValueError("missing source-season pitcher environment")
                target_season = evaluation_year + int(annual["path_year"]) - 1
                scaled_total += (
                    float(annual["adjusted_workload"])
                    / source_mean
                    * forecast_environment[target_season]
                )
            training_players.append(
                {
                    "path_player_id": player_id,
                    "outcome_tier_v2": str(first["outcome_tier_v2"]),
                    "role": classify_pitcher_path_role(
                        total_starts, total_games, total_workload
                    ),
                    "raw_total": total_workload,
                    "scaled_total": scaled_total,
                }
            )
        samples = pl.DataFrame(training_players, infer_schema_length=None)
        for player_id_group in evaluation.partition_by("path_player_id"):
            first = player_id_group.row(0, named=True)
            actual = float(player_id_group["adjusted_workload"].sum())
            eval_role = classify_pitcher_path_role(
                float(player_id_group["starts"].sum()),
                float(player_id_group["games"].sum()),
                actual,
            )
            pooled = samples.filter(
                pl.col("outcome_tier_v2") == first["outcome_tier_v2"]
            )
            role = pooled.filter(pl.col("role") == eval_role)
            for candidate_id, value_column, use_granular_role in (
                ("raw_pooled_tier", "raw_total", False),
                ("environment_pooled_tier", "scaled_total", False),
                ("environment_granular_role", "scaled_total", True),
            ):
                selected = (
                    role if use_granular_role and role.height >= minimum_role_players
                    else pooled
                )
                values = selected[value_column].to_numpy()
                weights = np.ones(selected.height)
                p10, p50, p90 = np.quantile(values, (0.1, 0.5, 0.9))
                rows.append(
                    {
                        "candidate_id": candidate_id,
                        "evaluation_year": evaluation_year,
                        "player_id": int(first["path_player_id"]),
                        "outcome_tier_v2": str(first["outcome_tier_v2"]),
                        "granular_role": eval_role,
                        "sample_source": "role" if selected is role else "pooled",
                        "training_players": selected.height,
                        "maximum_training_window_end": int(training["window_end_year"].max()),
                        "actual_workload": actual,
                        "predicted_p50": float(p50),
                        "crps": empirical_crps(values, weights, actual),
                        "covered_80": bool(p10 <= actual <= p90),
                        "median_error": float(p50) - actual,
                        "environment_slope": slope,
                    }
                )
    return pl.DataFrame(rows, infer_schema_length=None).sort(
        "candidate_id", "evaluation_year", "player_id"
    )


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Return a Wilson score interval for a binomial proportion."""

    if total < 1 or not 0 <= successes <= total or not math.isfinite(z) or z <= 0:
        raise ValueError("invalid Wilson interval inputs")
    rate = successes / total
    denominator = 1.0 + z * z / total
    center = (rate + z * z / (2.0 * total)) / denominator
    half = z * math.sqrt(rate * (1.0 - rate) / total + z * z / (4.0 * total * total)) / denominator
    return center - half, center + half


def build_workload_holdout_predictions(
    paths: pl.DataFrame,
    *,
    training_end_year: int = 2017,
    evaluation_start_year: int = 2018,
    minimum_role_players: int = 30,
) -> pl.DataFrame:
    """Score later debut cohorts from earlier conditional workload distributions."""

    required = {
        "player_id", "player_type", "debut_year", "outcome_tier_v2",
        "career_role", "adjusted_total_workload",
    }
    if missing := sorted(required - set(paths.columns)):
        raise ValueError(f"workload paths missing fields: {missing}")
    if evaluation_start_year <= training_end_year or minimum_role_players < 1:
        raise ValueError("invalid chronology or minimum role count")
    training = paths.filter(pl.col("debut_year") <= training_end_year)
    evaluation = paths.filter(pl.col("debut_year") >= evaluation_start_year)
    if training.is_empty() or evaluation.is_empty():
        raise ValueError("training and evaluation cohorts must be nonempty")

    rows = []
    for row in evaluation.iter_rows(named=True):
        pooled = training.filter(
            (pl.col("player_type") == row["player_type"])
            & (pl.col("outcome_tier_v2") == row["outcome_tier_v2"])
        )
        role = pooled.filter(pl.col("career_role") == row["career_role"])
        selected = role if role.height >= minimum_role_players else pooled
        source = "role" if role.height >= minimum_role_players else "pooled"
        if selected.is_empty():
            raise ValueError(
                "missing training cell for "
                f"{row['player_type']}/{row['outcome_tier_v2']}/{row['career_role']}"
            )
        samples = selected.get_column("adjusted_total_workload").to_numpy()
        actual = float(row["adjusted_total_workload"])
        p10, p25, p50, p75, p90 = np.quantile(
            samples, [0.10, 0.25, 0.50, 0.75, 0.90], method="linear"
        )
        rows.append(
            {
                "player_id": int(row["player_id"]),
                "player_type": str(row["player_type"]),
                "debut_year": int(row["debut_year"]),
                "outcome_tier_v2": str(row["outcome_tier_v2"]),
                "career_role": str(row["career_role"]),
                "sample_source": source,
                "training_players": selected.height,
                "actual_workload": actual,
                "predicted_p10": float(p10),
                "predicted_p25": float(p25),
                "predicted_p50": float(p50),
                "predicted_p75": float(p75),
                "predicted_p90": float(p90),
                "covered_80": bool(p10 <= actual <= p90),
                "covered_50": bool(p25 <= actual <= p75),
                "absolute_median_error": abs(actual - float(p50)),
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None).sort("player_id")


def build_workload_asof_predictions(
    paths: pl.DataFrame,
    *,
    evaluation_years: tuple[int, ...] = (2018, 2019),
    minimum_role_players: int = 30,
) -> pl.DataFrame:
    """Score conditional workload using only fully matured pre-cutoff paths."""

    required = {
        "player_id", "player_type", "debut_year", "window_end_year",
        "outcome_tier_v2", "career_role", "adjusted_total_workload",
    }
    if missing := sorted(required - set(paths.columns)):
        raise ValueError(f"workload paths missing fields: {missing}")
    if not evaluation_years or minimum_role_players < 1:
        raise ValueError("invalid as-of workload configuration")
    rows = []
    for evaluation_year in evaluation_years:
        training = paths.filter(pl.col("window_end_year") < evaluation_year)
        evaluation = paths.filter(pl.col("debut_year") == evaluation_year)
        if training.is_empty() or evaluation.is_empty():
            raise ValueError(f"empty workload as-of fold {evaluation_year}")
        maximum_training_end = int(training["window_end_year"].max())
        if maximum_training_end >= evaluation_year:
            raise ValueError("workload as-of chronology violation")
        for row in evaluation.iter_rows(named=True):
            pooled = training.filter(
                (pl.col("player_type") == row["player_type"])
                & (pl.col("outcome_tier_v2") == row["outcome_tier_v2"])
            )
            role = pooled.filter(pl.col("career_role") == row["career_role"])
            selected = role if role.height >= minimum_role_players else pooled
            source = "role" if role.height >= minimum_role_players else "pooled"
            if selected.is_empty():
                raise ValueError(
                    "missing as-of workload training cell: "
                    f"{evaluation_year}/{row['player_type']}/"
                    f"{row['outcome_tier_v2']}/{row['career_role']}"
                )
            samples = selected["adjusted_total_workload"].to_numpy()
            actual = float(row["adjusted_total_workload"])
            p10, p25, p50, p75, p90 = np.quantile(
                samples, [0.10, 0.25, 0.50, 0.75, 0.90], method="linear"
            )
            rows.append(
                {
                    "evaluation_year": evaluation_year,
                    "player_id": int(row["player_id"]),
                    "player_type": str(row["player_type"]),
                    "outcome_tier_v2": str(row["outcome_tier_v2"]),
                    "career_role": str(row["career_role"]),
                    "sample_source": source,
                    "training_players": selected.height,
                    "maximum_training_window_end": maximum_training_end,
                    "actual_workload": actual,
                    "predicted_p10": float(p10),
                    "predicted_p25": float(p25),
                    "predicted_p50": float(p50),
                    "predicted_p75": float(p75),
                    "predicted_p90": float(p90),
                    "covered_80": bool(p10 <= actual <= p90),
                    "covered_50": bool(p25 <= actual <= p75),
                    "median_error": float(p50) - actual,
                    "absolute_median_error": abs(actual - float(p50)),
                }
            )
    return pl.DataFrame(rows, infer_schema_length=None).sort(
        "evaluation_year", "player_type", "player_id"
    )


def summarize_workload_coverage(
    predictions: pl.DataFrame,
    group_columns: list[str],
) -> pl.DataFrame:
    """Summarize empirical coverage and Wilson uncertainty by declared groups."""

    required = {
        *group_columns, "covered_80", "covered_50", "absolute_median_error"
    }
    if missing := sorted(required - set(predictions.columns)):
        raise ValueError(f"predictions missing fields: {missing}")
    rows = []
    for key, group in predictions.partition_by(group_columns, as_dict=True).items():
        keys = key if isinstance(key, tuple) else (key,)
        total = group.height
        hits80 = int(group["covered_80"].sum())
        hits50 = int(group["covered_50"].sum())
        low80, high80 = wilson_interval(hits80, total)
        low50, high50 = wilson_interval(hits50, total)
        row = dict(zip(group_columns, keys, strict=True))
        row.update(
            {
                "players": total,
                "coverage_80": hits80 / total,
                "coverage_80_wilson_low": low80,
                "coverage_80_wilson_high": high80,
                "target_80_inside_wilson": low80 <= 0.8 <= high80,
                "coverage_50": hits50 / total,
                "coverage_50_wilson_low": low50,
                "coverage_50_wilson_high": high50,
                "target_50_inside_wilson": low50 <= 0.5 <= high50,
                "median_absolute_error": float(
                    group["absolute_median_error"].median()
                ),
            }
        )
        rows.append(row)
    return pl.DataFrame(rows, infer_schema_length=None).sort(group_columns)


def empirical_crps(
    samples: np.ndarray, weights: np.ndarray, observed: float
) -> float:
    """Return weighted empirical continuous ranked probability score."""

    values = np.asarray(samples, dtype=float)
    probability = np.asarray(weights, dtype=float)
    if (
        values.ndim != 1
        or probability.shape != values.shape
        or values.size == 0
        or not np.isfinite(values).all()
        or not np.isfinite(probability).all()
        or (probability < 0).any()
        or probability.sum() <= 0
        or not math.isfinite(observed)
    ):
        raise ValueError("invalid empirical CRPS inputs")
    probability = probability / probability.sum()
    first = float(np.sum(probability * np.abs(values - observed)))
    order = np.argsort(values, kind="stable")
    ordered_values = values[order]
    ordered_probability = probability[order]
    prior_probability = np.cumsum(ordered_probability) - ordered_probability
    prior_weighted_value = (
        np.cumsum(ordered_probability * ordered_values)
        - ordered_probability * ordered_values
    )
    second = float(
        np.sum(
            ordered_probability
            * (ordered_values * prior_probability - prior_weighted_value)
        )
    )
    return first - second


def _weighted_quantile(
    samples: np.ndarray, weights: np.ndarray, quantile: float
) -> float:
    order = np.argsort(samples, kind="stable")
    values = samples[order]
    probability = weights[order] / weights.sum()
    return float(values[np.searchsorted(np.cumsum(probability), quantile, side="left")])


def build_pitcher_workload_era_scores(
    paths: pl.DataFrame,
    *,
    evaluation_years: tuple[int, ...] = (2017, 2018, 2019),
    minimum_role_players: int = 30,
) -> pl.DataFrame:
    """Retrospectively score the frozen pitcher workload era candidate grid."""

    required = {
        "player_id", "player_type", "debut_year", "outcome_tier_v2",
        "career_role", "adjusted_total_workload",
    }
    if missing := sorted(required - set(paths.columns)):
        raise ValueError(f"workload paths missing fields: {missing}")
    if minimum_role_players < 1 or not evaluation_years:
        raise ValueError("invalid era-score configuration")
    pitchers = paths.filter(pl.col("player_type") == "pitcher")
    rows = []
    for evaluation_year in evaluation_years:
        training = pitchers.filter(pl.col("debut_year") < evaluation_year)
        evaluation = pitchers.filter(pl.col("debut_year") == evaluation_year)
        if training.is_empty() or evaluation.is_empty():
            raise ValueError(f"empty pitcher era fold {evaluation_year}")
        latest_training_year = evaluation_year - 1
        for row in evaluation.iter_rows(named=True):
            pooled = training.filter(
                pl.col("outcome_tier_v2") == row["outcome_tier_v2"]
            )
            role = pooled.filter(pl.col("career_role") == row["career_role"])
            for role_rule in ROLE_RULES:
                selected = (
                    role
                    if role_rule == "supported_role"
                    and role.height >= minimum_role_players
                    else pooled
                )
                source = "role" if selected is role else "pooled"
                if selected.is_empty():
                    raise ValueError("missing pitcher era training tier")
                for weighting in ERA_WEIGHTING_RULES:
                    candidate = selected
                    if weighting == "latest_2":
                        candidate = selected.filter(
                            pl.col("debut_year") >= latest_training_year - 1
                        )
                    years = candidate.get_column("debut_year").to_numpy()
                    if weighting == "half_life_1":
                        weights = np.power(0.5, latest_training_year - years)
                    elif weighting == "half_life_2":
                        weights = np.power(0.5, (latest_training_year - years) / 2.0)
                    else:
                        weights = np.ones(candidate.height)
                    samples = candidate.get_column(
                        "adjusted_total_workload"
                    ).to_numpy()
                    actual = float(row["adjusted_total_workload"])
                    p10, p25, p50, p75, p90 = [
                        _weighted_quantile(samples, weights, quantile)
                        for quantile in (0.10, 0.25, 0.50, 0.75, 0.90)
                    ]
                    rows.append(
                        {
                            "candidate_id": f"{weighting}__{role_rule}",
                            "weighting_rule": weighting,
                            "role_rule": role_rule,
                            "evaluation_year": evaluation_year,
                            "player_id": int(row["player_id"]),
                            "outcome_tier_v2": str(row["outcome_tier_v2"]),
                            "career_role": str(row["career_role"]),
                            "sample_source": source,
                            "training_players": candidate.height,
                            "actual_workload": actual,
                            "predicted_p50": p50,
                            "crps": empirical_crps(samples, weights, actual),
                            "covered_80": p10 <= actual <= p90,
                            "covered_50": p25 <= actual <= p75,
                            "median_error": p50 - actual,
                        }
                    )
    return pl.DataFrame(rows, infer_schema_length=None).sort(
        "candidate_id", "evaluation_year", "player_id"
    )
