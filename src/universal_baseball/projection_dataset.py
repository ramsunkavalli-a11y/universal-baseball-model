"""Leakage-safe batting Projection v1 snapshot and target surfaces.

The predictor side deliberately reuses the frozen Current Talent evidence
snapshot/context machinery. Projection owns a different future target: all
eligible regular-season player-game/profile evidence in the *next calendar
year*, rather than Current Talent's 90-day horizon.

The 2025 confirmation fold is blocked by default. This module performs no age
curve fitting, no model scoring, no playing-time inference, and no source I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import polars as pl

from universal_baseball.current_talent_evidence import (
    EvidenceWindow,
    build_predictor_snapshot,
    validate_player_game_evidence,
)
from universal_baseball.current_talent_validation_dataset import (
    TARGET_ENVIRONMENT_KEY,
    _add_transition_labels,
    _build_as_of_context,
)
from universal_baseball.projection_validation import ProjectionFold


@dataclass(frozen=True, slots=True)
class ProjectionSnapshotDataset:
    """One deterministic Projection snapshot with next-year realized outcomes."""

    predictor_summary: pl.DataFrame
    predictor_profile: pl.DataFrame
    target_summary: pl.DataFrame
    target_profile: pl.DataFrame
    scoring_rows: pl.DataFrame
    metrics: dict[str, Any]


def _require_fold_access(fold: ProjectionFold, *, allow_confirmation: bool) -> None:
    if fold.confirmation and not allow_confirmation:
        raise ValueError("2025 Projection confirmation outcomes are quarantined")


def _with_parsed_game_date(frame: pl.DataFrame) -> pl.DataFrame:
    parsed = frame.with_columns(
        pl.col("game_date").cast(pl.String).str.to_date(strict=False).alias("_projection_date")
    )
    if parsed.filter(pl.col("_projection_date").is_null()).height:
        raise ValueError("Projection evidence contains unparseable game dates")
    return parsed


def build_projection_future_target(
    summary: pl.DataFrame,
    profile: pl.DataFrame,
    *,
    fold: ProjectionFold,
    allow_confirmation: bool = False,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    """Aggregate one next-calendar-year target by actual future environment."""

    _require_fold_access(fold, allow_confirmation=allow_confirmation)
    validate_player_game_evidence(summary, profile)

    future = _with_parsed_game_date(summary).filter(
        (pl.col("_projection_date") >= pl.lit(fold.target_start))
        & (pl.col("_projection_date") < pl.lit(fold.target_end))
    )

    summary_schema = {
        "as_of_date": pl.Date,
        "projection_fold": pl.String,
        "player_id": pl.Int64,
        "target_season": pl.Int64,
        "target_league_id": pl.Int64,
        "target_level_group": pl.String,
        "future_plate_appearances": pl.Int64,
        "future_expected_contacts": pl.Int64,
        "future_observed_contacts": pl.Int64,
        "future_contact_count_residual": pl.Int64,
        "future_core_events": pl.Int64,
        "future_bunt_contacts": pl.Int64,
        "future_foul_air_excluded_contacts": pl.Int64,
        "future_unknown_contacts": pl.Int64,
        "future_special_noncontact_events": pl.Int64,
        "future_pa_accounting_residual": pl.Int64,
        "future_profile_observations": pl.Int64,
        "future_game_count": pl.Int64,
        "first_target_date": pl.Date,
        "last_target_date": pl.Date,
        "has_future_pa": pl.Boolean,
        "has_future_core_profile_evidence": pl.Boolean,
    }
    profile_schema = {
        "as_of_date": pl.Date,
        "projection_fold": pl.String,
        "player_id": pl.Int64,
        "target_season": pl.Int64,
        "target_league_id": pl.Int64,
        "target_level_group": pl.String,
        "core_bin": pl.String,
        "future_occurrence_count": pl.Int64,
        "future_core_profile_rate": pl.Float64,
    }

    if future.is_empty():
        empty_summary = pl.DataFrame(schema=summary_schema)
        empty_profile = pl.DataFrame(schema=profile_schema)
        return empty_summary, empty_profile, {
            "fold": fold.label,
            "as_of_date": fold.snapshot_date.isoformat(),
            "target_start": fold.target_start.isoformat(),
            "target_end": fold.target_end.isoformat(),
            "confirmation": fold.confirmation,
            "future_player_count": 0,
            "future_environment_row_count": 0,
            "future_plate_appearances": 0,
            "future_core_events": 0,
        }

    target_summary = (
        future.group_by(["player_id", "season", "league_id", "level_group"])
        .agg(
            pl.col("batting_plate_appearances").sum().cast(pl.Int64).alias("future_plate_appearances"),
            pl.col("expected_contact_count").sum().cast(pl.Int64).alias("future_expected_contacts"),
            pl.col("observed_contact_count").sum().cast(pl.Int64).alias("future_observed_contacts"),
            pl.col("contact_count_residual").sum().cast(pl.Int64).alias("future_contact_count_residual"),
            pl.col("core_profile_event_count").sum().cast(pl.Int64).alias("future_core_events"),
            pl.col("bunt_contact_count").sum().cast(pl.Int64).alias("future_bunt_contacts"),
            pl.col("foul_air_excluded_count")
            .sum()
            .cast(pl.Int64)
            .alias("future_foul_air_excluded_contacts"),
            pl.col("unknown_contact_count").sum().cast(pl.Int64).alias("future_unknown_contacts"),
            pl.col("special_noncontact_count")
            .sum()
            .cast(pl.Int64)
            .alias("future_special_noncontact_events"),
            pl.col("pa_accounting_residual")
            .sum()
            .cast(pl.Int64)
            .alias("future_pa_accounting_residual"),
            pl.col("game_pk").n_unique().cast(pl.Int64).alias("future_game_count"),
            pl.col("_projection_date").min().alias("first_target_date"),
            pl.col("_projection_date").max().alias("last_target_date"),
        )
        .rename(
            {
                "season": "target_season",
                "league_id": "target_league_id",
                "level_group": "target_level_group",
            }
        )
        .with_columns(
            (
                pl.col("future_core_events")
                + pl.col("future_bunt_contacts")
                + pl.col("future_foul_air_excluded_contacts")
                + pl.col("future_unknown_contacts")
                + pl.col("future_special_noncontact_events")
            ).cast(pl.Int64).alias("future_profile_observations"),
            (pl.col("future_plate_appearances") > 0).alias("has_future_pa"),
            (pl.col("future_core_events") > 0).alias("has_future_core_profile_evidence"),
            pl.lit(fold.snapshot_date).alias("as_of_date"),
            pl.lit(fold.label).alias("projection_fold"),
        )
        .select(list(summary_schema))
        .cast(summary_schema, strict=True)
        .sort(list(TARGET_ENVIRONMENT_KEY))
    )

    future_keys = future.select(
        "season", "game_date", "game_pk", "league_id", "player_id"
    ).unique()
    future_profile = profile.join(
        future_keys,
        on=["season", "game_date", "game_pk", "league_id", "player_id"],
        how="inner",
    )
    target_profile = (
        future_profile.group_by(
            ["player_id", "season", "league_id", "level_group", "core_bin"]
        )
        .agg(pl.col("occurrence_count").sum().cast(pl.Int64).alias("future_occurrence_count"))
        .rename(
            {
                "season": "target_season",
                "league_id": "target_league_id",
                "level_group": "target_level_group",
            }
        )
        .join(
            target_summary.select(*TARGET_ENVIRONMENT_KEY, "future_core_events"),
            on=list(TARGET_ENVIRONMENT_KEY),
            how="left",
        )
        .with_columns(
            pl.when(pl.col("future_core_events") > 0)
            .then(pl.col("future_occurrence_count") / pl.col("future_core_events"))
            .otherwise(None)
            .cast(pl.Float64)
            .alias("future_core_profile_rate"),
            pl.lit(fold.snapshot_date).alias("as_of_date"),
            pl.lit(fold.label).alias("projection_fold"),
        )
        .select(list(profile_schema))
        .cast(profile_schema, strict=True)
        .sort([*TARGET_ENVIRONMENT_KEY, "core_bin"])
    )

    reconciliation = (
        target_profile.group_by(list(TARGET_ENVIRONMENT_KEY))
        .agg(pl.col("future_occurrence_count").sum().cast(pl.Int64).alias("_profile_count"))
        .join(
            target_summary.select(*TARGET_ENVIRONMENT_KEY, "future_core_events"),
            on=list(TARGET_ENVIRONMENT_KEY),
            how="right",
        )
        .with_columns(pl.col("_profile_count").fill_null(0).cast(pl.Int64))
    )
    if reconciliation.filter(pl.col("_profile_count") != pl.col("future_core_events")).height:
        raise ValueError("Projection future profile counts do not reconcile to target summary")

    metrics: dict[str, Any] = {
        "fold": fold.label,
        "as_of_date": fold.snapshot_date.isoformat(),
        "target_start": fold.target_start.isoformat(),
        "target_end": fold.target_end.isoformat(),
        "confirmation": fold.confirmation,
        "future_player_count": int(target_summary.get_column("player_id").n_unique()),
        "future_environment_row_count": int(target_summary.height),
        "future_plate_appearances": int(target_summary.get_column("future_plate_appearances").sum() or 0),
        "future_core_events": int(target_summary.get_column("future_core_events").sum() or 0),
        "future_actual_league_count": int(target_summary.get_column("target_league_id").n_unique()),
        "future_level_count": int(target_summary.get_column("target_level_group").n_unique()),
        "confirmation_access_explicitly_authorized": bool(fold.confirmation and allow_confirmation),
    }
    return target_summary, target_profile, metrics


def build_projection_snapshot_dataset(
    summary: pl.DataFrame,
    profile: pl.DataFrame,
    *,
    fold: ProjectionFold,
    window: EvidenceWindow,
    allow_confirmation: bool = False,
) -> ProjectionSnapshotDataset:
    """Build one frozen-chronology Projection predictor/next-year target surface."""

    _require_fold_access(fold, allow_confirmation=allow_confirmation)
    validate_player_game_evidence(summary, profile)

    predictor_summary, predictor_profile = build_predictor_snapshot(
        summary,
        profile,
        cutoff=fold.snapshot_date,
        window=window,
    )
    context = _build_as_of_context(summary, cutoff=fold.snapshot_date)
    predictor_summary = predictor_summary.join(context, on="player_id", how="left")

    target_summary, target_profile, target_metrics = build_projection_future_target(
        summary,
        profile,
        fold=fold,
        allow_confirmation=allow_confirmation,
    )
    scoring = target_summary.join(predictor_summary, on="player_id", how="inner")
    if not scoring.is_empty():
        scoring = _add_transition_labels(scoring).sort(list(TARGET_ENVIRONMENT_KEY))

    predictor_players = set(predictor_summary.get_column("player_id").to_list())
    target_players = set(target_summary.get_column("player_id").to_list())
    scored_players = predictor_players & target_players

    transition_counts: dict[str, int] = {}
    if not scoring.is_empty() and "target_transition" in scoring.columns:
        transition_counts = {
            str(row["target_transition"]): int(row["len"])
            for row in scoring.group_by("target_transition").len().iter_rows(named=True)
        }

    metrics: dict[str, Any] = {
        **target_metrics,
        "window_label": window.label,
        "predictor_player_count": len(predictor_players),
        "target_player_count": len(target_players),
        "scored_player_count": len(scored_players),
        "target_player_without_predictor_count": len(target_players - predictor_players),
        "predictor_player_without_target_count": len(predictor_players - target_players),
        "scoring_environment_row_count": int(scoring.height),
        "transition_counts": transition_counts,
        "playing_time_modeled": False,
        "zero_future_opportunity_treated_as_bad_skill": False,
        "retrospective_event_cutoff": True,
        "vintage_information_set": False,
    }
    return ProjectionSnapshotDataset(
        predictor_summary=predictor_summary,
        predictor_profile=predictor_profile,
        target_summary=target_summary,
        target_profile=target_profile,
        scoring_rows=scoring,
        metrics=metrics,
    )
