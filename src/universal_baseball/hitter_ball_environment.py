"""Chronology-safe diagnostics for changing baseball flight environments."""

from __future__ import annotations

import math

import numpy as np
import polars as pl


AIR_CONTACT_BINS = (
    "PULL_LD",
    "CENTER_LD",
    "OPPO_LD",
    "PULL_OFFB",
    "CENTER_OFFB",
    "OPPO_OFFB",
)
BALL_FEATURE_COLUMNS = (
    "ball_air_contacts",
    "ball_raw_air_hr_rate",
    "ball_neutralized_air_hr_rate",
    "ball_mean_regime_log_odds",
    "ball_mean_probability_effect",
    "ball_positive_environment_share",
)


def _require(frame: pl.DataFrame, columns: set[str], label: str) -> None:
    if missing := sorted(columns - set(frame.columns)):
        raise ValueError(f"{label} missing fields: {missing}")


def _logit_probability(value: pl.Expr) -> pl.Expr:
    clipped = value.clip(1e-6, 1.0 - 1e-6)
    return (clipped / (1.0 - clipped)).log()


def prepare_air_contact_history(
    events: pl.DataFrame,
    *,
    prior_exposure: float = 150.0,
    prior_rate: float | None = None,
    window_days: int = 14,
) -> pl.DataFrame:
    """Add strictly-prior batter/pitcher quality and a level/date regime key."""

    _require(
        events,
        {
            "season",
            "league_id",
            "level",
            "game_date",
            "game_pk",
            "at_bat_index",
            "player_id",
            "pitcher",
            "core_bin",
            "canonical_outcome",
        },
        "air-contact events",
    )
    if events.filter(pl.col("season") >= 2026).height:
        raise ValueError("protected 2026 events are not allowed")
    if prior_exposure <= 0 or window_days <= 0:
        raise ValueError("prior exposure and window length must be positive")
    air = (
        events.filter(pl.col("core_bin").is_in(AIR_CONTACT_BINS))
        .with_columns(
            pl.col("game_date").cast(pl.Date),
            (pl.col("canonical_outcome") == "HR").cast(pl.Int8).alias("is_hr"),
        )
        .sort(["game_date", "game_pk", "at_bat_index"])
    )
    if air.is_empty():
        raise ValueError("no eligible air contacts")
    baseline = float(air["is_hr"].mean()) if prior_rate is None else float(prior_rate)
    if not 0 < baseline < 1:
        raise ValueError("prior rate must be strictly between zero and one")

    result = air
    for actor, prefix in (("player_id", "hitter"), ("pitcher", "pitcher")):
        daily = (
            air.group_by(actor, "game_date")
            .agg(
                pl.len().alias("_daily_n"),
                pl.col("is_hr").sum().alias("_daily_hr"),
            )
            .sort([actor, "game_date"])
            .with_columns(
                (pl.col("_daily_n").cum_sum().over(actor) - pl.col("_daily_n")).alias(
                    f"prior_{prefix}_air_contacts"
                ),
                (pl.col("_daily_hr").cum_sum().over(actor) - pl.col("_daily_hr")).alias(
                    f"prior_{prefix}_air_hr"
                ),
            )
            .select(
                actor,
                "game_date",
                f"prior_{prefix}_air_contacts",
                f"prior_{prefix}_air_hr",
            )
        )
        result = result.join(daily, on=[actor, "game_date"], validate="m:1")
        posterior = (pl.col(f"prior_{prefix}_air_hr") + prior_exposure * baseline) / (
            pl.col(f"prior_{prefix}_air_contacts") + prior_exposure
        )
        result = result.with_columns(
            (
                _logit_probability(posterior) - math.log(baseline / (1.0 - baseline))
            ).alias(f"prior_{prefix}_air_hr_log_odds_residual")
        )

    return result.with_columns(
        ((pl.col("game_date").dt.ordinal_day() - 1) // window_days)
        .cast(pl.Int16)
        .alias("ball_window"),
        ((pl.col("game_pk").cast(pl.UInt64) * 1_000_003 + 97) % 2)
        .cast(pl.Int8)
        .alias("ball_crossfit_fold"),
    ).with_columns(
        pl.concat_str(
            [
                pl.col("level").cast(pl.String).str.to_uppercase(),
                pl.col("season").cast(pl.String),
                pl.col("ball_window").cast(pl.String),
            ],
            separator="|",
        ).alias("ball_regime_key")
    )


def fit_regime_log_odds_adjustments(
    events: pl.DataFrame,
    *,
    estimation_fold: int,
    prior_exposure: float = 1_000.0,
) -> pl.DataFrame:
    """Fit shrunk observed-minus-expected shifts on one independent game fold."""

    _require(
        events,
        {
            "ball_regime_key",
            "ball_crossfit_fold",
            "is_hr",
            "base_hr_probability",
        },
        "ball-regime events",
    )
    if estimation_fold not in (0, 1) or prior_exposure <= 0:
        raise ValueError("estimation fold must be 0/1 and prior exposure positive")
    grouped = (
        events.filter(pl.col("ball_crossfit_fold") == estimation_fold)
        .group_by("ball_regime_key")
        .agg(
            pl.len().alias("regime_events"),
            pl.col("is_hr").sum().alias("regime_home_runs"),
            pl.col("base_hr_probability").sum().alias("regime_expected_home_runs"),
        )
        .with_columns(
            (pl.col("regime_expected_home_runs") / pl.col("regime_events")).alias(
                "_expected_rate"
            )
        )
        .with_columns(
            (
                (pl.col("regime_home_runs") + prior_exposure * pl.col("_expected_rate"))
                / (pl.col("regime_events") + prior_exposure)
            ).alias("_observed_shrunk_rate")
        )
        .with_columns(
            (
                _logit_probability(pl.col("_observed_shrunk_rate"))
                - _logit_probability(pl.col("_expected_rate"))
            ).alias("ball_regime_log_odds")
        )
        .drop("_expected_rate", "_observed_shrunk_rate")
        .with_columns(pl.lit(estimation_fold).alias("adjustment_estimation_fold"))
    )
    return grouped.sort("ball_regime_key")


def apply_crossfit_regime_adjustments(
    events: pl.DataFrame,
    *,
    prior_exposure: float = 1_000.0,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Estimate each regime on one set of games and score it on the other set."""

    adjustments = pl.concat(
        [
            fit_regime_log_odds_adjustments(
                events, estimation_fold=fold, prior_exposure=prior_exposure
            )
            for fold in (0, 1)
        ],
        how="vertical_relaxed",
    )
    applications: list[pl.DataFrame] = []
    for target_fold in (0, 1):
        fitted = adjustments.filter(
            pl.col("adjustment_estimation_fold") == 1 - target_fold
        ).drop("adjustment_estimation_fold")
        applications.append(
            events.filter(pl.col("ball_crossfit_fold") == target_fold)
            .join(fitted, on="ball_regime_key", how="left", validate="m:1")
            .with_columns(pl.col("ball_regime_log_odds").fill_null(0.0))
        )
    result = pl.concat(applications, how="vertical_relaxed").sort(
        ["game_date", "game_pk", "at_bat_index"]
    )
    base_logit = _logit_probability(pl.col("base_hr_probability"))
    result = result.with_columns(
        (1.0 / (1.0 + (-(base_logit + pl.col("ball_regime_log_odds"))).exp())).alias(
            "regime_hr_probability"
        )
    ).with_columns(
        (pl.col("regime_hr_probability") - pl.col("base_hr_probability")).alias(
            "ball_probability_effect"
        )
    )
    return result, adjustments


def aggregate_player_ball_features(events: pl.DataFrame) -> pl.DataFrame:
    """Summarize cross-fitted ball exposure and neutralized HR credit by player-year."""

    _require(
        events,
        {
            "season",
            "player_id",
            "is_hr",
            "ball_regime_log_odds",
            "ball_probability_effect",
        },
        "adjusted ball events",
    )
    return (
        events.group_by("season", "player_id")
        .agg(
            pl.len().alias("ball_air_contacts"),
            pl.col("is_hr").mean().alias("ball_raw_air_hr_rate"),
            (
                (pl.col("is_hr") - pl.col("ball_probability_effect")).sum() / pl.len()
            ).alias("ball_neutralized_air_hr_rate"),
            pl.col("ball_regime_log_odds").mean().alias("ball_mean_regime_log_odds"),
            pl.col("ball_probability_effect")
            .mean()
            .alias("ball_mean_probability_effect"),
            (pl.col("ball_regime_log_odds") > 0)
            .mean()
            .alias("ball_positive_environment_share"),
        )
        .sort(["season", "player_id"])
    )


def add_ball_environment_history(
    panel: pl.DataFrame,
    annual: pl.DataFrame,
    *,
    lags: tuple[int, ...] = (0, 1, 2),
) -> pl.DataFrame:
    """Attach exact calendar lags without inventing missing ball evidence."""

    _require(panel, {"origin_year", "player_id"}, "hitter panel")
    _require(
        annual,
        {"season", "player_id", *BALL_FEATURE_COLUMNS},
        "annual ball features",
    )
    if annual.group_by("season", "player_id").len().filter(pl.col("len") > 1).height:
        raise ValueError("annual ball features must be unique by player-season")
    result = panel
    for lag in lags:
        history = (
            annual.select("season", "player_id", *BALL_FEATURE_COLUMNS)
            .with_columns(
                (pl.col("season") + lag).alias("origin_year"),
                pl.lit(1).cast(pl.Int8).alias(f"lag{lag}__ball__available"),
            )
            .drop("season")
            .rename(
                {column: f"lag{lag}__ball__{column}" for column in BALL_FEATURE_COLUMNS}
            )
        )
        result = result.join(history, on=["origin_year", "player_id"], how="left")
        result = result.with_columns(pl.col(f"lag{lag}__ball__available").fill_null(0))
    if result.height != panel.height:
        raise ValueError("ball history join changed panel row count")
    return result


def binary_metrics(actual: np.ndarray, probability: np.ndarray) -> dict[str, float]:
    """Return event-weighted binary proper scores."""

    y = np.asarray(actual, dtype=np.float64)
    p = np.clip(np.asarray(probability, dtype=np.float64), 1e-7, 1.0 - 1e-7)
    return {
        "log_loss": float(-np.mean(y * np.log(p) + (1.0 - y) * np.log(1.0 - p))),
        "brier": float(np.mean(np.square(y - p))),
        "actual_rate": float(np.mean(y)),
        "predicted_rate": float(np.mean(p)),
    }
