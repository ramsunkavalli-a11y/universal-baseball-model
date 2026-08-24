"""Frozen disclosed-validation diagnostics and promotion rules for Hitter v2."""

from __future__ import annotations

from collections.abc import Mapping
from math import isfinite

import numpy as np
import polars as pl

from universal_baseball.hitter_v2_evaluation import (
    NEUTRAL_WOBA,
    NEUTRAL_WOBA_SCALE,
    NEUTRAL_WOBA_WEIGHTS,
    SCORING_PROBABILITY_FLOOR,
    score_hitter_predictions,
)
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES


PRIMARY_LOSS_METRICS = (
    "terminal_log_loss",
    "terminal_brier_score",
    "woba_mae",
    "woba_rmse",
    "runs_per_600_mae",
    "runs_per_600_rmse",
)
LEVEL_SUPPORT_PLAYERS = 100
LEVEL_SUPPORT_PA = 10_000
OTHER_SUPPORT_PLAYERS = 50
OTHER_SUPPORT_PA = 5_000
BOOTSTRAP_SEED = 20260823
BOOTSTRAP_RESAMPLES = 10_000
LEVEL_ORDER = {
    "complex": 0,
    "rookie": 0,
    "rk": 0,
    "a": 1,
    "low-a": 1,
    "high-a": 2,
    "a+": 2,
    "aa": 3,
    "aaa": 4,
    "mlb": 5,
}


def build_player_scoring_surface(
    predictions: pl.DataFrame,
    target_players: pl.DataFrame,
    *,
    model_id: str,
    fold_id: str,
) -> pl.DataFrame:
    """Materialize paired player errors without changing the eligible cohort."""

    probability_columns = [f"p_{outcome}" for outcome in HITTER_TALENT_OUTCOMES]
    required_predictions = {"player_id", *probability_columns}
    required_targets = {"player_id", "hitter_talent_pa", *HITTER_TALENT_OUTCOMES}
    if missing := sorted(required_predictions - set(predictions.columns)):
        raise ValueError(f"predictions missing scoring columns: {missing}")
    if missing := sorted(required_targets - set(target_players.columns)):
        raise ValueError(f"targets missing scoring columns: {missing}")
    joined = target_players.join(
        predictions.select("player_id", *probability_columns),
        on="player_id",
        how="inner",
        validate="1:1",
    ).sort("player_id")
    if joined.is_empty():
        raise ValueError("prediction and target surfaces do not overlap")
    woba_terms = [
        pl.col(outcome) * pl.lit(NEUTRAL_WOBA_WEIGHTS[outcome])
        for outcome in HITTER_TALENT_OUTCOMES
    ]
    predicted_woba_terms = [
        pl.col(f"p_{outcome}") * pl.lit(NEUTRAL_WOBA_WEIGHTS[outcome])
        for outcome in HITTER_TALENT_OUTCOMES
    ]
    actual_probability = {
        outcome: pl.col(outcome) / pl.col("hitter_talent_pa")
        for outcome in HITTER_TALENT_OUTCOMES
    }
    terminal_log_loss = -pl.sum_horizontal(
        *[
            actual_probability[outcome]
            * pl.col(f"p_{outcome}").clip(lower_bound=SCORING_PROBABILITY_FLOOR).log()
            for outcome in HITTER_TALENT_OUTCOMES
        ]
    )
    terminal_brier = (
        pl.lit(1.0)
        - pl.lit(2.0)
        * pl.sum_horizontal(
            *[
                actual_probability[outcome] * pl.col(f"p_{outcome}")
                for outcome in HITTER_TALENT_OUTCOMES
            ]
        )
        + pl.sum_horizontal(
            *[pl.col(f"p_{outcome}") ** 2 for outcome in HITTER_TALENT_OUTCOMES]
        )
    )
    surface = joined.with_columns(
        pl.lit(model_id).alias("model_id"),
        pl.lit(fold_id).alias("fold_id"),
        pl.sum_horizontal(*woba_terms)
        .truediv(pl.col("hitter_talent_pa"))
        .alias("actual_woba"),
        pl.sum_horizontal(*predicted_woba_terms).alias("predicted_woba"),
        terminal_log_loss.alias("terminal_log_loss"),
        terminal_brier.alias("terminal_brier_score"),
    ).with_columns(
        (
            (pl.col("actual_woba") - pl.lit(NEUTRAL_WOBA))
            / pl.lit(NEUTRAL_WOBA_SCALE)
            * pl.lit(600.0)
        ).alias("actual_runs_per_600"),
        (
            (pl.col("predicted_woba") - pl.lit(NEUTRAL_WOBA))
            / pl.lit(NEUTRAL_WOBA_SCALE)
            * pl.lit(600.0)
        ).alias("predicted_runs_per_600"),
    ).with_columns(
        (pl.col("predicted_woba") - pl.col("actual_woba")).alias("woba_error"),
        (
            pl.col("predicted_runs_per_600") - pl.col("actual_runs_per_600")
        ).alias("runs_per_600_error"),
    )
    if surface.filter(
        pl.sum_horizontal(*[pl.col(outcome) for outcome in HITTER_TALENT_OUTCOMES])
        != pl.col("hitter_talent_pa")
    ).height:
        raise ValueError("target surface does not reconcile to target PA")
    return surface


def terminal_component_calibration(
    predictions: pl.DataFrame,
    target_players: pl.DataFrame,
    *,
    weighting: str,
) -> list[dict[str, object]]:
    """Return weighted intercept/slope for every identifiable terminal component."""

    joined = target_players.join(predictions, on="player_id", how="inner", validate="1:1")
    pa = joined["hitter_talent_pa"].to_numpy().astype(float)
    weights = np.ones(joined.height) if weighting == "player" else pa
    rows = []
    for outcome in HITTER_TALENT_OUTCOMES:
        predicted = joined[f"p_{outcome}"].to_numpy().astype(float)
        actual = joined[outcome].to_numpy().astype(float) / pa
        design = np.column_stack([np.ones(joined.height), predicted])
        weighted_design = design * np.sqrt(weights)[:, None]
        identifiable = bool(np.linalg.matrix_rank(weighted_design) == 2)
        if identifiable:
            coefficients = np.linalg.lstsq(
                weighted_design, actual * np.sqrt(weights), rcond=None
            )[0]
            intercept, slope = map(float, coefficients)
        else:
            intercept, slope = None, None
        rows.append(
            {
                "outcome": outcome,
                "weighting": weighting,
                "identifiable": identifiable,
                "intercept": intercept,
                "slope": slope,
                "slope_guardrail_pass": (
                    None if slope is None else 0.80 <= slope <= 1.20
                ),
            }
        )
    return rows


def predicted_woba_decile_calibration(surface: pl.DataFrame) -> list[dict[str, object]]:
    """Create ten deterministic equal-player bins ordered by predicted wOBA."""

    ordered = surface.sort(["predicted_woba", "player_id"]).with_row_index("rank")
    binned = ordered.with_columns(
        ((pl.col("rank") * 10) // pl.lit(max(ordered.height, 1)))
        .clip(upper_bound=9)
        .alias("predicted_decile")
    )
    rows = (
        binned.group_by("predicted_decile")
        .agg(
            pl.len().alias("players"),
            pl.col("hitter_talent_pa").sum().alias("target_pa"),
            pl.col("predicted_woba").mean().alias("mean_predicted_woba"),
            pl.col("actual_woba").mean().alias("mean_actual_woba"),
        )
        .sort("predicted_decile")
        .with_columns(
            (pl.col("mean_predicted_woba") - pl.col("mean_actual_woba"))
            .abs()
            .alias("absolute_woba_error")
        )
        .to_dicts()
    )
    for row in rows:
        row["guardrail_pass"] = float(row["absolute_woba_error"]) <= 0.010
    return rows


def level_aggregate_calibration(
    predictions: pl.DataFrame,
    target_players: pl.DataFrame,
) -> list[dict[str, object]]:
    """Report PA-weighted outcome and wOBA calibration by target level."""

    surface = build_player_scoring_surface(
        predictions, target_players, model_id="diagnostic", fold_id="diagnostic"
    )
    level_column = "primary_target_level_group"
    if level_column not in surface.columns:
        raise ValueError("target surface is missing primary target level")
    rows = []
    for level in sorted(str(value) for value in surface[level_column].unique()):
        group = surface.filter(pl.col(level_column) == level)
        target_pa = int(group["hitter_talent_pa"].sum())
        players = group.height
        predicted_woba = float(
            (group["predicted_woba"] * group["hitter_talent_pa"]).sum() / target_pa
        )
        actual_woba = float(
            (group["actual_woba"] * group["hitter_talent_pa"]).sum() / target_pa
        )
        outcome_errors = {}
        maximum_outcome_error = 0.0
        for outcome in HITTER_TALENT_OUTCOMES:
            predicted_rate = float(
                (group[f"p_{outcome}"] * group["hitter_talent_pa"]).sum()
                / target_pa
            )
            actual_rate = float(group[outcome].sum() / target_pa)
            error = abs(predicted_rate - actual_rate)
            outcome_errors[outcome] = error
            maximum_outcome_error = max(maximum_outcome_error, error)
        supported = players >= LEVEL_SUPPORT_PLAYERS and target_pa >= LEVEL_SUPPORT_PA
        rows.append(
            {
                "level_group": level,
                "players": players,
                "target_pa": target_pa,
                "supported": supported,
                "absolute_woba_error": abs(predicted_woba - actual_woba),
                "maximum_outcome_rate_error": maximum_outcome_error,
                "outcome_absolute_errors": outcome_errors,
                "guardrail_pass": (
                    None
                    if not supported
                    else abs(predicted_woba - actual_woba) <= 0.005
                    and maximum_outcome_error <= 0.005
                ),
            }
        )
    return rows


def paired_player_bootstrap_rmse_delta(
    candidate_surface: pl.DataFrame,
    baseline_surface: pl.DataFrame,
    *,
    error_column: str,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, float | int | bool]:
    """Bootstrap paired player-fold rows for candidate-minus-baseline RMSE."""

    keys = ["fold_id", "player_id"]
    paired = candidate_surface.select(*keys, error_column).join(
        baseline_surface.select(*keys, error_column),
        on=keys,
        how="inner",
        suffix="_baseline",
        validate="1:1",
    )
    if paired.height != candidate_surface.height or paired.height != baseline_surface.height:
        raise ValueError("bootstrap surfaces do not use identical player-fold keys")
    candidate = paired[error_column].to_numpy().astype(float)
    baseline = paired[f"{error_column}_baseline"].to_numpy().astype(float)
    if resamples <= 0:
        raise ValueError("bootstrap resamples must be positive")
    rng = np.random.default_rng(seed)
    deltas = np.empty(resamples, dtype=float)
    for start in range(0, resamples, 250):
        count = min(250, resamples - start)
        indexes = rng.integers(0, paired.height, size=(count, paired.height))
        candidate_rmse = np.sqrt(np.mean(candidate[indexes] ** 2, axis=1))
        baseline_rmse = np.sqrt(np.mean(baseline[indexes] ** 2, axis=1))
        deltas[start : start + count] = candidate_rmse - baseline_rmse
    lower, upper = np.quantile(deltas, [0.05, 0.95])
    observed = float(np.sqrt(np.mean(candidate**2)) - np.sqrt(np.mean(baseline**2)))
    return {
        "paired_rows": paired.height,
        "resamples": resamples,
        "seed": seed,
        "observed_candidate_minus_baseline_rmse": observed,
        "ci90_lower": float(lower),
        "ci90_upper": float(upper),
        "upper_bound_below_zero": bool(upper < 0.0),
    }


def strongest_simple_baseline(
    b0_metrics: Mapping[str, float | int | None],
    b1_metrics: Mapping[str, float | int | None],
    metric: str,
) -> tuple[str, float]:
    """Return the lower-loss permanent baseline for one primary metric."""

    b0 = b0_metrics.get(metric)
    b1 = b1_metrics.get(metric)
    if b0 is None or b1 is None:
        raise ValueError(f"baseline metric is unavailable: {metric}")
    b0_value = float(b0)
    b1_value = float(b1)
    if not isfinite(b0_value) or not isfinite(b1_value):
        raise ValueError(f"baseline metric is nonfinite: {metric}")
    return ("B0_ONE_YEAR_EB", b0_value) if b0_value <= b1_value else (
        "B1_MARCEL_345_K1200",
        b1_value,
    )


def fold_primary_gate(
    candidate_metrics: Mapping[str, float | int | None],
    b0_metrics: Mapping[str, float | int | None],
    b1_metrics: Mapping[str, float | int | None],
) -> dict[str, object]:
    """Apply strict per-fold primary gates against the metric-wise baseline."""

    comparisons = {}
    for metric in PRIMARY_LOSS_METRICS:
        baseline_id, baseline_value = strongest_simple_baseline(
            b0_metrics, b1_metrics, metric
        )
        candidate_value = float(candidate_metrics[metric])
        delta = candidate_value - baseline_value
        comparisons[metric] = {
            "candidate": candidate_value,
            "baseline_id": baseline_id,
            "baseline": baseline_value,
            "candidate_minus_baseline": delta,
            "pass": delta < -1e-8,
        }
    return {
        "comparisons": comparisons,
        "pass": all(bool(value["pass"]) for value in comparisons.values()),
    }


def score_subgroup(
    predictions: pl.DataFrame,
    target_players: pl.DataFrame,
    player_ids: list[int],
) -> dict[str, object]:
    """Score one fixed subgroup in both weighting views."""

    target = target_players.filter(pl.col("player_id").is_in(player_ids))
    prediction = predictions.filter(pl.col("player_id").is_in(player_ids))
    players = target.height
    target_pa = int(target["hitter_talent_pa"].sum()) if players else 0
    if players == 0:
        return {"players": 0, "target_pa": 0, "supported": False, "metrics": None}
    supported = players >= OTHER_SUPPORT_PLAYERS and target_pa >= OTHER_SUPPORT_PA
    return {
        "players": players,
        "target_pa": target_pa,
        "supported": supported,
        "metrics": {
            weighting: score_hitter_predictions(
                prediction, target, weighting=weighting
            )
            for weighting in ("player", "pa")
        },
    }


def summarize_scoring_surface(
    surface: pl.DataFrame,
    *,
    weighting: str,
) -> dict[str, float | int | None]:
    """Summarize already-paired rows, including pooled cross-fold surfaces."""

    if weighting not in {"player", "pa"}:
        raise ValueError("weighting must be 'player' or 'pa'")
    if surface.is_empty():
        raise ValueError("scoring surface cannot be empty")
    weight = (
        np.ones(surface.height, dtype=float)
        if weighting == "player"
        else surface["hitter_talent_pa"].to_numpy().astype(float)
    )
    result: dict[str, float | int | None] = {
        "players": surface.height,
        "target_hitter_talent_pa": int(surface["hitter_talent_pa"].sum()),
        "terminal_log_loss": float(
            np.average(surface["terminal_log_loss"].to_numpy(), weights=weight)
        ),
        "terminal_brier_score": float(
            np.average(surface["terminal_brier_score"].to_numpy(), weights=weight)
        ),
    }
    for prefix, error_column in (
        ("woba", "woba_error"),
        ("runs_per_600", "runs_per_600_error"),
    ):
        errors = surface[error_column].to_numpy().astype(float)
        result[f"{prefix}_mae"] = float(np.average(np.abs(errors), weights=weight))
        result[f"{prefix}_rmse"] = float(np.sqrt(np.average(errors**2, weights=weight)))
        predicted = surface[f"predicted_{prefix}"].to_numpy().astype(float)
        actual = surface[f"actual_{prefix}"].to_numpy().astype(float)
        predicted_centered = predicted - np.average(predicted, weights=weight)
        actual_centered = actual - np.average(actual, weights=weight)
        denominator = np.sqrt(
            np.sum(weight * predicted_centered**2)
            * np.sum(weight * actual_centered**2)
        )
        result[f"{prefix}_pearson"] = (
            None
            if denominator <= 0.0
            else float(
                np.sum(weight * predicted_centered * actual_centered) / denominator
            )
        )
        predicted_rank = (
            pl.Series(predicted).rank(method="average").to_numpy().astype(float)
        )
        actual_rank = pl.Series(actual).rank(method="average").to_numpy().astype(float)
        predicted_rank -= np.average(predicted_rank, weights=weight)
        actual_rank -= np.average(actual_rank, weights=weight)
        rank_denominator = np.sqrt(
            np.sum(weight * predicted_rank**2) * np.sum(weight * actual_rank**2)
        )
        result[f"{prefix}_spearman"] = (
            None
            if rank_denominator <= 0.0
            else float(np.sum(weight * predicted_rank * actual_rank) / rank_denominator)
        )
    return result


def build_evaluation_subgroups(
    training: pl.DataFrame,
    target_players: pl.DataFrame,
    forecast_ages: pl.DataFrame,
) -> pl.DataFrame:
    """Build evaluation-only subgroup labels from frozen training and target context."""

    required_training = {
        "player_id", "season", "level_group", "hitter_talent_pa", "K", "HR",
    }
    if missing := sorted(required_training - set(training.columns)):
        raise ValueError(f"training missing subgroup columns: {missing}")
    latest = (
        training.sort(
            ["player_id", "season", "hitter_talent_pa", "league_id"],
            descending=[False, True, True, False],
        )
        .unique("player_id", keep="first", maintain_order=True)
        .select(
            "player_id",
            pl.col("level_group").alias("latest_training_level_group"),
        )
    )
    history = training.group_by("player_id").agg(
        pl.col("hitter_talent_pa").sum().alias("prior_hitter_talent_pa"),
        pl.col("K").sum().alias("prior_K"),
        pl.col("HR").sum().alias("prior_HR"),
    ).with_columns(
        (pl.col("prior_K") / pl.col("prior_hitter_talent_pa")).alias("prior_K_rate"),
        (pl.col("prior_HR") / pl.col("prior_hitter_talent_pa")).alias("prior_HR_rate"),
    )
    k_low, k_high = history["prior_K_rate"].quantile(0.25), history[
        "prior_K_rate"
    ].quantile(0.75)
    hr_low, hr_high = history["prior_HR_rate"].quantile(0.25), history[
        "prior_HR_rate"
    ].quantile(0.75)
    joined = (
        target_players.select(
            "player_id", "primary_target_level_group", "hitter_talent_pa"
        )
        .join(history, on="player_id", how="inner", validate="1:1")
        .join(latest, on="player_id", how="left", validate="1:1")
        .join(
            forecast_ages.select("player_id", "age_years"),
            on="player_id",
            how="left",
            validate="1:1",
        )
    )

    def level_rank(value: object) -> int | None:
        if value is None:
            return None
        return LEVEL_ORDER.get(str(value).strip().lower())

    rows = []
    for row in joined.iter_rows(named=True):
        age = row["age_years"]
        if age is None:
            age_band = "missing_age"
        elif float(age) < 20.0:
            age_band = "<20"
        elif float(age) < 23.0:
            age_band = "20-22"
        elif float(age) < 26.0:
            age_band = "23-25"
        elif float(age) < 30.0:
            age_band = "26-29"
        else:
            age_band = "30+"
        evidence = float(row["prior_hitter_talent_pa"])
        if evidence < 100.0:
            evidence_band = "<100"
        elif evidence < 250.0:
            evidence_band = "100-249"
        elif evidence < 500.0:
            evidence_band = "250-499"
        elif evidence < 1000.0:
            evidence_band = "500-999"
        else:
            evidence_band = "1000+"
        source_rank = level_rank(row["latest_training_level_group"])
        target_rank = level_rank(row["primary_target_level_group"])
        if source_rank is None or target_rank is None or source_rank == target_rank:
            movement_band = "other_mover_or_same_level"
        elif target_rank > source_rank:
            movement_band = "promotion"
        else:
            movement_band = "demotion"
        k_rate = float(row["prior_K_rate"])
        hr_rate = float(row["prior_HR_rate"])
        k_band = "low_K" if k_rate <= float(k_low) else "high_K" if k_rate >= float(k_high) else "middle_K"
        hr_band = "low_power" if hr_rate <= float(hr_low) else "high_power" if hr_rate >= float(hr_high) else "middle_power"
        rows.append(
            {
                **row,
                "age_band": age_band,
                "evidence_band": evidence_band,
                "movement_band": movement_band,
                "k_band": k_band,
                "hr_power_band": hr_band,
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None).sort("player_id")


def subgroup_reversal_gate(
    candidate: Mapping[str, float | int | None],
    b0: Mapping[str, float | int | None],
    b1: Mapping[str, float | int | None],
) -> dict[str, object]:
    """Apply the frozen material supported-subgroup reversal definition."""

    deltas = {
        metric: float(candidate[metric]) - min(float(b0[metric]), float(b1[metric]))
        for metric in (
            "woba_rmse",
            "runs_per_600_rmse",
            "terminal_log_loss",
            "terminal_brier_score",
        )
    }
    rate_reversal = (
        deltas["woba_rmse"] > 0.002
        and deltas["runs_per_600_rmse"] > 0.5
    )
    proper_score_reversal = (
        deltas["terminal_log_loss"] > 0.0005
        and deltas["terminal_brier_score"] > 0.0005
    )
    return {
        "candidate_minus_strongest_baseline": deltas,
        "rate_reversal": rate_reversal,
        "proper_score_reversal": proper_score_reversal,
        "pass": not rate_reversal and not proper_score_reversal,
    }
