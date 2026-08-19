"""Frozen Player Value v1 batting RE24 -> projected-runs conversion."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Mapping

import polars as pl

from universal_baseball.mlb_bin_value_policy import MLB_LEAGUE_IDS
from universal_baseball.performance_season import ALL_CORE_BINS


BATTING_RUN_CONVERSION_ID = "batting_re24_pooled_mlb_reference_v1"
PROBABILITY_TOLERANCE = 1e-9


@dataclass(frozen=True, slots=True)
class MlbBattingReference:
    season: int
    core_event_rate_per_pa: float
    reference_probabilities: Mapping[str, float]
    bin_run_values: Mapping[str, float]
    reference_run_value_per_core_event: float
    reference_run_value_per_pa: float
    batting_run_conversion_id: str = BATTING_RUN_CONVERSION_ID


@dataclass(frozen=True, slots=True)
class ProjectedBattingRuns:
    projected_batting_runs_above_mlb_reference: float
    projected_expected_mlb_pa: float
    projected_core_run_value_per_event: float
    mlb_reference_core_run_value_per_event: float
    mlb_reference_core_event_rate_per_pa: float
    batting_run_conversion_id: str = BATTING_RUN_CONVERSION_ID


def _require_columns(frame: pl.DataFrame, columns: set[str], label: str) -> None:
    missing = sorted(columns - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def _finite_nonnegative(value: object, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite nonnegative number") from exc
    if not isfinite(numeric) or numeric < 0:
        raise ValueError(f"{label} must be a finite nonnegative number")
    return numeric


def build_v1_mlb_batting_reference(
    summary: pl.DataFrame,
    profile: pl.DataFrame,
    bin_values: pl.DataFrame,
    *,
    season: int,
) -> MlbBattingReference:
    """Build the binding pooled-MLB RE24 reference for one certified season."""

    _require_columns(
        summary,
        {"season", "league_id", "batting_plate_appearances", "core_profile_event_count"},
        "MLB Performance summary",
    )
    _require_columns(
        profile,
        {"season", "league_id", "core_bin", "occurrence_count"},
        "MLB Performance profile",
    )
    _require_columns(
        bin_values,
        {"season", "league_id", "core_bin", "estimated_mean_run_value", "estimator_certified"},
        "MLB Performance bin values",
    )

    leagues = sorted(MLB_LEAGUE_IDS)
    season_summary = summary.filter(
        (pl.col("season").cast(pl.Int64) == int(season))
        & pl.col("league_id").cast(pl.Int64).is_in(leagues)
    )
    season_profile = profile.filter(
        (pl.col("season").cast(pl.Int64) == int(season))
        & pl.col("league_id").cast(pl.Int64).is_in(leagues)
    )
    season_values = bin_values.filter(
        (pl.col("season").cast(pl.Int64) == int(season))
        & pl.col("league_id").cast(pl.Int64).is_in(leagues)
    )

    if season_summary.is_empty() or season_profile.is_empty() or season_values.is_empty():
        raise ValueError("MLB Performance reference inputs are empty for requested season")

    observed_leagues = {
        int(value) for value in season_summary.get_column("league_id").unique().to_list()
    }
    if observed_leagues != set(MLB_LEAGUE_IDS):
        raise ValueError("MLB Performance reference must contain both AL and NL")

    duplicate_values = (
        season_values.group_by(["league_id", "core_bin"])
        .len()
        .filter(pl.col("len") != 1)
    )
    if not duplicate_values.is_empty():
        raise ValueError("MLB Performance bin values must have one row per league/core bin")

    expected_value_keys = {
        (league_id, core_bin) for league_id in MLB_LEAGUE_IDS for core_bin in ALL_CORE_BINS
    }
    observed_value_keys = {
        (int(row["league_id"]), str(row["core_bin"]))
        for row in season_values.select("league_id", "core_bin").iter_rows(named=True)
    }
    if observed_value_keys != expected_value_keys:
        raise ValueError("MLB Performance bin-value reference is incomplete")
    if season_values.filter(~pl.col("estimator_certified").fill_null(False)).height:
        raise ValueError("MLB Performance reference requires certified bin values")

    total_pa = int(season_summary.get_column("batting_plate_appearances").sum() or 0)
    summary_core_events = int(season_summary.get_column("core_profile_event_count").sum() or 0)
    if total_pa <= 0 or summary_core_events <= 0:
        raise ValueError("MLB Performance reference requires positive PA and core events")
    if summary_core_events > total_pa:
        raise ValueError("MLB Performance core events cannot exceed PA")

    counts = (
        season_profile.group_by(["league_id", "core_bin"])
        .agg(pl.col("occurrence_count").sum().cast(pl.Int64).alias("occurrence_count"))
    )
    profile_core_events = int(counts.get_column("occurrence_count").sum() or 0)
    if profile_core_events != summary_core_events:
        raise ValueError("MLB Performance profile core events do not reconcile to summary")

    count_lookup = {
        (int(row["league_id"]), str(row["core_bin"])): int(row["occurrence_count"])
        for row in counts.iter_rows(named=True)
    }
    value_lookup = {
        (int(row["league_id"]), str(row["core_bin"])): float(row["estimated_mean_run_value"])
        for row in season_values.iter_rows(named=True)
    }

    pooled_counts: dict[str, int] = {}
    pooled_values: dict[str, float] = {}
    for core_bin in ALL_CORE_BINS:
        bin_count = sum(count_lookup.get((league_id, core_bin), 0) for league_id in MLB_LEAGUE_IDS)
        if bin_count <= 0:
            raise ValueError(f"MLB Performance reference has no occurrences for core bin {core_bin}")
        weighted_value = sum(
            count_lookup.get((league_id, core_bin), 0) * value_lookup[(league_id, core_bin)]
            for league_id in MLB_LEAGUE_IDS
        ) / bin_count
        if not isfinite(weighted_value):
            raise ValueError("MLB Performance reference contains non-finite bin value")
        pooled_counts[core_bin] = bin_count
        pooled_values[core_bin] = weighted_value

    probabilities = {
        core_bin: pooled_counts[core_bin] / summary_core_events for core_bin in ALL_CORE_BINS
    }
    probability_sum = sum(probabilities.values())
    if abs(probability_sum - 1.0) > PROBABILITY_TOLERANCE:
        raise ValueError("MLB reference probabilities do not sum to one")

    coverage = summary_core_events / total_pa
    reference_per_core = sum(
        probabilities[core_bin] * pooled_values[core_bin] for core_bin in ALL_CORE_BINS
    )
    reference_per_pa = coverage * reference_per_core

    return MlbBattingReference(
        season=int(season),
        core_event_rate_per_pa=float(coverage),
        reference_probabilities=MappingProxyType(dict(probabilities)),
        bin_run_values=MappingProxyType(dict(pooled_values)),
        reference_run_value_per_core_event=float(reference_per_core),
        reference_run_value_per_pa=float(reference_per_pa),
    )


def calculate_v1_projected_batting_runs(
    projection_probabilities: Mapping[str, object],
    *,
    projected_expected_mlb_pa: object,
    reference: MlbBattingReference,
) -> ProjectedBattingRuns:
    """Convert frozen projected core composition + expected MLB PA into runs."""

    observed_bins = set(projection_probabilities)
    expected_bins = set(ALL_CORE_BINS)
    if observed_bins != expected_bins:
        missing = sorted(expected_bins - observed_bins)
        extra = sorted(observed_bins - expected_bins)
        raise ValueError(f"projection core-bin set mismatch: missing={missing}, extra={extra}")

    probabilities: dict[str, float] = {}
    for core_bin in ALL_CORE_BINS:
        try:
            probability = float(projection_probabilities[core_bin])
        except (TypeError, ValueError) as exc:
            raise ValueError("projection probabilities must be finite values in [0, 1]") from exc
        if not isfinite(probability) or probability < 0 or probability > 1:
            raise ValueError("projection probabilities must be finite values in [0, 1]")
        probabilities[core_bin] = probability

    if abs(sum(probabilities.values()) - 1.0) > PROBABILITY_TOLERANCE:
        raise ValueError("projection probabilities must sum to one")

    pa = _finite_nonnegative(projected_expected_mlb_pa, "projected_expected_mlb_pa")
    projected_per_core = sum(
        probabilities[core_bin] * float(reference.bin_run_values[core_bin])
        for core_bin in ALL_CORE_BINS
    )
    runs = (
        pa
        * float(reference.core_event_rate_per_pa)
        * (projected_per_core - float(reference.reference_run_value_per_core_event))
    )

    return ProjectedBattingRuns(
        projected_batting_runs_above_mlb_reference=float(runs),
        projected_expected_mlb_pa=pa,
        projected_core_run_value_per_event=float(projected_per_core),
        mlb_reference_core_run_value_per_event=float(reference.reference_run_value_per_core_event),
        mlb_reference_core_event_rate_per_pa=float(reference.core_event_rate_per_pa),
    )
