"""League-season-centered component park effects from exact home/away splits."""

from __future__ import annotations

import math

import numpy as np
import polars as pl


def build_component_park_observations(
    frame: pl.DataFrame,
    context: pl.DataFrame,
    *,
    exposure_column: str,
    component_columns: tuple[str, ...],
    minimum_split_exposure: int = 100,
    pseudocount: float = 0.5,
) -> pl.DataFrame:
    """Build one centered home-minus-away CLR observation per team-season."""

    required = {
        "season", "sport_id", "team_id", "split_code", exposure_column,
        *component_columns,
    }
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"component park source missing fields: {missing}")
    if minimum_split_exposure <= 0 or pseudocount <= 0:
        raise ValueError("component park thresholds must be positive")
    grouped = frame.group_by("season", "sport_id", "team_id", "split_code").agg(
        pl.col(exposure_column).sum().alias(exposure_column),
        *(pl.col(column).sum().alias(column) for column in component_columns),
    )
    if grouped.filter(
        (pl.sum_horizontal(*component_columns) != pl.col(exposure_column))
        | pl.any_horizontal(*(pl.col(column) < 0 for column in component_columns))
    ).height:
        raise ValueError("component park counts do not reconcile to exposure")
    home = grouped.filter(pl.col("split_code") == "h").drop("split_code").rename({
        exposure_column: "home_exposure",
        **{column: f"home_{column}" for column in component_columns},
    })
    away = grouped.filter(pl.col("split_code") == "a").drop("split_code").rename({
        exposure_column: "away_exposure",
        **{column: f"away_{column}" for column in component_columns},
    })
    joined = home.join(
        away, on=["season", "sport_id", "team_id"], how="inner", validate="1:1"
    ).filter(
        (pl.col("home_exposure") >= minimum_split_exposure)
        & (pl.col("away_exposure") >= minimum_split_exposure)
    ).join(
        context.select("season", "sport_id", "team_id", "league_id", "venue_id"),
        on=["season", "sport_id", "team_id"], how="left", validate="1:1",
    )
    if joined.filter(pl.col("venue_id").is_null() | pl.col("league_id").is_null()).height:
        raise ValueError("component park observations lack team context")
    rows = []
    for row in joined.iter_rows(named=True):
        home_values = np.asarray(
            [float(row[f"home_{value}"]) + pseudocount for value in component_columns]
        )
        away_values = np.asarray(
            [float(row[f"away_{value}"]) + pseudocount for value in component_columns]
        )
        home_probability = home_values / home_values.sum()
        away_probability = away_values / away_values.sum()
        effect = (
            np.log(home_probability) - np.log(home_probability).mean()
            - np.log(away_probability) + np.log(away_probability).mean()
        )
        precision = 2.0 / (
            1.0 / float(row["home_exposure"])
            + 1.0 / float(row["away_exposure"])
        )
        base = {
            key: row[key] for key in (
                "season", "sport_id", "team_id", "league_id", "venue_id",
                "home_exposure", "away_exposure",
            )
        }
        base.update({
            f"home_{value}": row[f"home_{value}"] for value in component_columns
        })
        base.update({
            f"away_{value}": row[f"away_{value}"] for value in component_columns
        })
        base["precision_exposure"] = precision
        base.update({
            f"raw_effect_{value}": float(effect[index])
            for index, value in enumerate(component_columns)
        })
        rows.append(base)
    result = pl.DataFrame(rows)
    # Remove the weighted league-season mean. This prevents league/ball conditions
    # from being mislabeled as physical venue effects.
    for component in component_columns:
        mean_name = f"_mean_{component}"
        means = result.group_by("season", "league_id").agg(
            (
                (pl.col(f"raw_effect_{component}") * pl.col("precision_exposure")).sum()
                / pl.col("precision_exposure").sum()
            ).alias(mean_name)
        )
        result = result.join(means, on=["season", "league_id"], validate="m:1").with_columns(
            (pl.col(f"raw_effect_{component}") - pl.col(mean_name)).alias(
                f"effect_{component}"
            )
        ).drop(mean_name)
    return result.sort(["season", "sport_id", "venue_id", "team_id"])


def fit_component_park_factors(
    observations: pl.DataFrame,
    *,
    through_season: int,
    component_columns: tuple[str, ...],
    prior_exposure: float,
) -> pl.DataFrame:
    """Partially pool venue CLR effects toward neutral."""

    if not math.isfinite(prior_exposure) or prior_exposure < 0:
        raise ValueError("park prior exposure must be nonnegative")
    training = observations.filter(pl.col("season") <= through_season)
    rows = []
    for component in component_columns:
        fitted = training.group_by("venue_id").agg(
            pl.col("precision_exposure").sum().alias("training_precision"),
            pl.col("season").n_unique().alias("training_seasons"),
            (
                pl.col(f"effect_{component}") * pl.col("precision_exposure")
            ).sum().alias("weighted_effect"),
        ).with_columns(
            (
                pl.col("weighted_effect")
                / (pl.col("training_precision") + prior_exposure)
            ).alias("park_clr_effect")
        ).select(
            "venue_id", pl.lit(component).alias("component"),
            "training_precision", "training_seasons", "park_clr_effect",
        )
        rows.append(fitted)
    return pl.concat(rows, how="vertical").sort(["venue_id", "component"])


def score_component_park_factors(
    observations: pl.DataFrame,
    factors: pl.DataFrame,
    *,
    season: int,
    component_columns: tuple[str, ...],
    pseudocount: float = 0.5,
) -> dict[str, float | int]:
    """Predict target home components from target away talent plus prior park effect."""

    target = observations.filter(pl.col("season") == season)
    lookup = {
        (int(row["venue_id"]), str(row["component"])): float(row["park_clr_effect"])
        for row in factors.iter_rows(named=True)
    }
    baseline_nll = candidate_nll = baseline_brier = candidate_brier = 0.0
    total = 0.0
    for row in target.iter_rows(named=True):
        away = np.asarray(
            [float(row[f"away_{value}"]) + pseudocount for value in component_columns]
        )
        baseline = away / away.sum()
        clr = np.log(baseline) - np.log(baseline).mean()
        effect = np.asarray([
            lookup.get((int(row["venue_id"]), value), 0.0)
            for value in component_columns
        ])
        exponentials = np.exp(clr + effect - np.max(clr + effect))
        candidate = exponentials / exponentials.sum()
        counts = np.asarray(
            [float(row[f"home_{value}"]) for value in component_columns]
        )
        exposure = counts.sum()
        observed = counts / exposure
        baseline_nll -= float(np.dot(counts, np.log(baseline)))
        candidate_nll -= float(np.dot(counts, np.log(candidate)))
        baseline_brier += exposure * float(np.sum((baseline - observed) ** 2))
        candidate_brier += exposure * float(np.sum((candidate - observed) ** 2))
        total += exposure
    if total <= 0:
        raise ValueError(f"no component park observations for {season}")
    return {
        "season": season, "team_venue_cells": target.height,
        "venues": target.get_column("venue_id").n_unique(),
        "home_exposure": int(total),
        "baseline_log_loss": baseline_nll / total,
        "candidate_log_loss": candidate_nll / total,
        "baseline_brier": baseline_brier / total,
        "candidate_brier": candidate_brier / total,
    }


def build_park_neutral_player_rows(
    frame: pl.DataFrame,
    context: pl.DataFrame,
    factors: pl.DataFrame,
    *,
    exposure_column: str,
    component_columns: tuple[str, ...],
    level_by_sport: dict[int, str],
    pseudocount: float = 0.5,
) -> pl.DataFrame:
    """Neutralize exact player home exposure and retain road exposure unchanged."""

    required = {
        "season", "sport_id", "team_id", "player_id", "split_code",
        exposure_column, *component_columns,
    }
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"player park source missing fields: {missing}")
    joined = frame.join(
        context.select("season", "sport_id", "team_id", "venue_id"),
        on=["season", "sport_id", "team_id"], how="left", validate="m:1",
    )
    if joined.filter(pl.col("venue_id").is_null()).height:
        raise ValueError("player park rows lack venue context")
    factor_lookup = {
        (int(row["venue_id"]), str(row["component"])): float(row["park_clr_effect"])
        for row in factors.iter_rows(named=True)
    }
    rows = []
    for row in joined.iter_rows(named=True):
        exposure = float(row[exposure_column])
        if exposure <= 0:
            continue
        counts = np.asarray([float(row[value]) for value in component_columns])
        if np.any(counts < 0) or not math.isclose(float(counts.sum()), exposure, abs_tol=1e-8):
            raise ValueError("player park components do not reconcile")
        if row["split_code"] == "h":
            probabilities = (counts + pseudocount) / (
                exposure + pseudocount * len(component_columns)
            )
            clr = np.log(probabilities) - np.log(probabilities).mean()
            effect = np.asarray([
                factor_lookup.get((int(row["venue_id"]), value), 0.0)
                for value in component_columns
            ])
            exponentials = np.exp(clr - effect - np.max(clr - effect))
            counts = exposure * exponentials / exponentials.sum()
        result = {
            "season": int(row["season"]), "player_id": int(row["player_id"]),
            "level_group": level_by_sport[int(row["sport_id"])],
            exposure_column: exposure,
        }
        result.update({
            value: float(counts[index]) for index, value in enumerate(component_columns)
        })
        rows.append(result)
    aggregated = pl.DataFrame(rows).group_by(
        "season", "player_id", "level_group"
    ).agg(
        pl.col(exposure_column).sum().alias(exposure_column),
        *(pl.col(value).sum().alias(value) for value in component_columns[:-1]),
    ).with_columns(
        (
            pl.col(exposure_column) - pl.sum_horizontal(*component_columns[:-1])
        ).alias(component_columns[-1])
    )
    return aggregated.sort(["season", "player_id", "level_group"])
