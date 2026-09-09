"""Chronology-safe hitter contact-shape features for prospect research."""

from __future__ import annotations

from datetime import date
from math import log

import numpy as np
import polars as pl


CONTACT_BINS = (
    "IFFB",
    "PULL_OFFB", "CENTER_OFFB", "OPPO_OFFB",
    "PULL_LD", "CENTER_LD", "OPPO_LD",
    "PULL_GB", "CENTER_GB", "OPPO_GB",
)
PROFILE_BINS = (*CONTACT_BINS, "BB_HBP", "K")
FEATURE_FAMILIES = ("coverage", "trajectory", "direction", "combined")
SHAPE_FIELDS = ("gb_count", "ld_count", "iffb_count", "pull_count", "oppo_count")


def aggregate_prospect_pbp_features(
    profile: pl.DataFrame,
    summary: pl.DataFrame,
    *,
    predictor_year: int,
) -> pl.DataFrame:
    """Aggregate one completed predictor season without crossing its time boundary."""

    profile_required = {
        "season", "game_date", "game_pk", "player_id", "core_bin", "occurrence_count"
    }
    summary_required = {
        "season", "game_date", "game_pk", "player_id", "core_profile_event_count"
    }
    if missing := sorted(profile_required - set(profile.columns)):
        raise ValueError(f"PBP profile missing fields: {missing}")
    if missing := sorted(summary_required - set(summary.columns)):
        raise ValueError(f"PBP summary missing fields: {missing}")
    if profile.filter(pl.col("season") != predictor_year).height:
        raise ValueError("PBP profile crosses the predictor season")
    if summary.filter(pl.col("season") != predictor_year).height:
        raise ValueError("PBP summary crosses the predictor season")
    boundary = date(predictor_year + 1, 1, 1)
    if profile.filter(pl.col("game_date").is_null() | (pl.col("game_date") >= boundary)).height:
        raise ValueError("PBP profile contains a future or missing game date")
    if summary.filter(pl.col("game_date").is_null() | (pl.col("game_date") >= boundary)).height:
        raise ValueError("PBP summary contains a future or missing game date")
    if profile.filter(~pl.col("core_bin").is_in(PROFILE_BINS)).height:
        raise ValueError("PBP profile contains an unknown core bin")
    duplicate_summary = summary.group_by("game_pk", "player_id").len().filter(pl.col("len") > 1)
    if not duplicate_summary.is_empty():
        raise ValueError("PBP summary duplicates a player-game")

    contact = (
        profile.filter(pl.col("core_bin").is_in(CONTACT_BINS))
        .group_by("player_id")
        .agg(
            pl.col("occurrence_count").sum().cast(pl.Float64).alias("pbp_contact_count"),
            pl.col("occurrence_count")
            .filter(pl.col("core_bin").str.ends_with("_GB"))
            .sum().cast(pl.Float64).alias("gb_count"),
            pl.col("occurrence_count")
            .filter(pl.col("core_bin").str.ends_with("_LD"))
            .sum().cast(pl.Float64).alias("ld_count"),
            pl.col("occurrence_count")
            .filter(pl.col("core_bin") == "IFFB")
            .sum().cast(pl.Float64).alias("iffb_count"),
            pl.col("occurrence_count")
            .filter(pl.col("core_bin").str.starts_with("PULL_"))
            .sum().cast(pl.Float64).alias("pull_count"),
            pl.col("occurrence_count")
            .filter(pl.col("core_bin").str.starts_with("OPPO_"))
            .sum().cast(pl.Float64).alias("oppo_count"),
            pl.col("occurrence_count")
            .filter(pl.col("core_bin").str.starts_with("CENTER_"))
            .sum().cast(pl.Float64).alias("center_count"),
        )
    )
    coverage = summary.group_by("player_id").agg(
        pl.col("core_profile_event_count").sum().cast(pl.Float64).alias("pbp_core_event_count")
    )
    return (
        coverage.join(contact, on="player_id", how="left", validate="1:1")
        .with_columns(
            pl.col("pbp_contact_count").fill_null(0.0),
            pl.col("gb_count").fill_null(0.0),
            pl.col("ld_count").fill_null(0.0),
            pl.col("iffb_count").fill_null(0.0),
            pl.col("pull_count").fill_null(0.0),
            pl.col("oppo_count").fill_null(0.0),
            pl.col("center_count").fill_null(0.0),
        )
        .with_columns((pl.col("pbp_contact_count") > 0).alias("pbp_observed"))
        .sort("player_id")
    )


def attach_prospect_pbp_features(
    cohort: pl.DataFrame, features: pl.DataFrame
) -> pl.DataFrame:
    """Keep the full cohort and encode absent source coverage explicitly."""

    result = cohort.join(features, on="player_id", how="left", validate="1:1")
    return result.with_columns(
        pl.col("pbp_contact_count").fill_null(0.0),
        pl.col("pbp_core_event_count").fill_null(0.0),
        pl.col("pbp_observed").fill_null(False),
        *[pl.col(field).fill_null(0.0) for field in (*SHAPE_FIELDS, "center_count")],
    )


def contact_shape_priors(frame: pl.DataFrame) -> dict[str, float]:
    """Estimate comparison-population shares from training rows only."""

    contacts = float(frame.get_column("pbp_contact_count").sum())
    directional = float(
        frame.select(pl.sum_horizontal("pull_count", "oppo_count", "center_count").sum()).item()
    )
    if contacts <= 0 or directional <= 0:
        raise ValueError("training PBP evidence must contain contact and directional events")
    return {
        "gb_count": float(frame.get_column("gb_count").sum()) / contacts,
        "ld_count": float(frame.get_column("ld_count").sum()) / contacts,
        "iffb_count": float(frame.get_column("iffb_count").sum()) / contacts,
        "pull_count": float(frame.get_column("pull_count").sum()) / directional,
        "oppo_count": float(frame.get_column("oppo_count").sum()) / directional,
    }


def contact_shape_design(
    frame: pl.DataFrame,
    *,
    feature_family: str,
    priors: dict[str, float],
    regression_strength: float,
) -> np.ndarray:
    """Return coverage plus regressed shape features for one frozen family."""

    if feature_family not in FEATURE_FAMILIES:
        raise ValueError(f"unsupported PBP feature family: {feature_family}")
    if regression_strength < 0:
        raise ValueError("contact regression strength cannot be negative")
    if set(priors) != set(SHAPE_FIELDS):
        raise ValueError("contact priors do not match the frozen shape fields")
    rows: list[list[float]] = []
    for row in frame.iter_rows(named=True):
        contacts = float(row["pbp_contact_count"])
        directional = float(row["pull_count"] + row["oppo_count"] + row["center_count"])
        values = [
            log(1.0 + contacts) / log(601.0),
            float(bool(row["pbp_observed"])),
        ]
        regressed = {}
        for field in SHAPE_FIELDS:
            denominator = directional if field in {"pull_count", "oppo_count"} else contacts
            regressed[field] = (
                (float(row[field]) + regression_strength * float(priors[field]))
                / (denominator + regression_strength)
                if denominator + regression_strength > 0
                else float(priors[field])
            )
        if feature_family in {"trajectory", "combined"}:
            values.extend(regressed[field] for field in SHAPE_FIELDS[:3])
        if feature_family in {"direction", "combined"}:
            values.extend(regressed[field] for field in SHAPE_FIELDS[3:])
        rows.append(values)
    return np.asarray(rows, dtype=float)
