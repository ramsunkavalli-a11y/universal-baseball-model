"""Leakage-safe snapshot/target dataset for Current Talent validation.

This module assembles the already-frozen predictor evidence surface with future
outcomes while preserving the environment in which those future outcomes
actually occurred. It does not estimate talent, fit environment translations,
or apply the 200-PA aggregate diagnostic cap.

The primary proper-score path uses all eligible future core evidence inside the
calendar horizon, as required by the validation contract. Exact 200-PA capped
player-aggregate diagnostics require PA-grain future events and remain a later
validation step; game-level evidence must not invent a partial-game split merely
to hit that cap.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import polars as pl

from universal_baseball.current_talent_evidence import (
    EvidenceWindow,
    LEVEL_ORDINAL,
    build_predictor_snapshot,
    validate_player_game_evidence,
)
from universal_baseball.current_talent_validation import (
    FutureHorizon,
    PRIMARY_FUTURE_HORIZON,
    future_window,
)


TARGET_ENVIRONMENT_KEY = (
    "player_id",
    "target_season",
    "target_league_id",
    "target_level_group",
)


@dataclass(frozen=True, slots=True)
class ValidationSnapshotDataset:
    """One deterministic as-of validation surface."""

    predictor_summary: pl.DataFrame
    predictor_profile: pl.DataFrame
    target_summary: pl.DataFrame
    target_profile: pl.DataFrame
    scoring_rows: pl.DataFrame
    metrics: dict[str, Any]


def _with_game_date(frame: pl.DataFrame, alias: str) -> pl.DataFrame:
    return frame.with_columns(
        pl.col("game_date").cast(pl.String).str.to_date(strict=False).alias(alias)
    )


def _build_as_of_context(summary: pl.DataFrame, *, cutoff: date) -> pl.DataFrame:
    """Freeze actual pre-cutoff environment without inventing same-day order.

    If a player's latest pre-cutoff date contains more than one actual league,
    the environment is intentionally left null and flagged ambiguous. Game PK is
    not used as a surrogate timestamp because historical sources do not guarantee
    that it encodes within-day chronology.
    """

    pre = _with_game_date(summary, "_context_date").filter(
        pl.col("_context_date") < pl.lit(cutoff)
    )
    schema = {
        "player_id": pl.Int64,
        "as_of_context_date": pl.Date,
        "as_of_season": pl.Int64,
        "as_of_league_id": pl.Int64,
        "as_of_level_group": pl.String,
        "as_of_environment_ambiguous": pl.Boolean,
        "prior_mlb_evidence": pl.Boolean,
    }
    if pre.is_empty():
        return pl.DataFrame(schema=schema)

    latest_dates = pre.group_by("player_id").agg(
        pl.col("_context_date").max().alias("as_of_context_date")
    )
    latest = pre.join(latest_dates, on="player_id", how="inner").filter(
        pl.col("_context_date") == pl.col("as_of_context_date")
    )
    latest_context = (
        latest.group_by("player_id")
        .agg(
            pl.col("as_of_context_date").first(),
            pl.col("season").n_unique().alias("_season_count"),
            pl.col("season").first().cast(pl.Int64).alias("_season"),
            pl.col("league_id").n_unique().alias("_league_count"),
            pl.col("league_id").first().cast(pl.Int64).alias("_league"),
            pl.col("level_group").n_unique().alias("_level_count"),
            pl.col("level_group").first().cast(pl.String).alias("_level"),
        )
        .with_columns(
            (
                (pl.col("_season_count") != 1)
                | (pl.col("_league_count") != 1)
                | (pl.col("_level_count") != 1)
            ).alias("as_of_environment_ambiguous")
        )
        .with_columns(
            pl.when(~pl.col("as_of_environment_ambiguous"))
            .then(pl.col("_season"))
            .otherwise(None)
            .cast(pl.Int64)
            .alias("as_of_season"),
            pl.when(~pl.col("as_of_environment_ambiguous"))
            .then(pl.col("_league"))
            .otherwise(None)
            .cast(pl.Int64)
            .alias("as_of_league_id"),
            pl.when(~pl.col("as_of_environment_ambiguous"))
            .then(pl.col("_level"))
            .otherwise(None)
            .cast(pl.String)
            .alias("as_of_level_group"),
        )
    )
    prior_mlb = pre.group_by("player_id").agg(
        (pl.col("level_group") == "MLB").any().alias("prior_mlb_evidence")
    )
    return (
        latest_context.join(prior_mlb, on="player_id", how="left")
        .select(list(schema))
        .cast(schema, strict=True)
        .sort("player_id")
    )


def build_future_target(
    summary: pl.DataFrame,
    profile: pl.DataFrame,
    *,
    cutoff: date,
    horizon: FutureHorizon = PRIMARY_FUTURE_HORIZON,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Aggregate future evidence by the actual season/league/level environment.

    PA/result opportunity and contact/profile evidence remain separate. A target
    environment may therefore carry core profile evidence even when its PA
    denominator is sparse or imperfect; consumers must use the named denominator
    appropriate to the metric rather than forcing one channel to partition the
    other.
    """

    validate_player_game_evidence(summary, profile)
    start, end = future_window(cutoff, horizon)
    future = _with_game_date(summary, "_target_date").filter(
        (pl.col("_target_date") >= pl.lit(start))
        & (pl.col("_target_date") < pl.lit(end))
    )

    summary_schema = {
        "as_of_date": pl.Date,
        "horizon_label": pl.String,
        "horizon_calendar_days": pl.Int64,
        "aggregate_pa_cap": pl.Int64,
        "aggregate_pa_cap_applied": pl.Boolean,
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
        "horizon_label": pl.String,
        "player_id": pl.Int64,
        "target_season": pl.Int64,
        "target_league_id": pl.Int64,
        "target_level_group": pl.String,
        "core_bin": pl.String,
        "future_occurrence_count": pl.Int64,
        "future_core_profile_rate": pl.Float64,
    }
    if future.is_empty():
        return pl.DataFrame(schema=summary_schema), pl.DataFrame(schema=profile_schema)

    target_summary = (
        future.group_by(["player_id", "season", "league_id", "level_group"])
        .agg(
            pl.col("batting_plate_appearances").sum().alias("future_plate_appearances"),
            pl.col("expected_contact_count").sum().alias("future_expected_contacts"),
            pl.col("observed_contact_count").sum().alias("future_observed_contacts"),
            pl.col("contact_count_residual").sum().alias("future_contact_count_residual"),
            pl.col("core_profile_event_count").sum().alias("future_core_events"),
            pl.col("bunt_contact_count").sum().alias("future_bunt_contacts"),
            pl.col("foul_air_excluded_count")
            .sum()
            .alias("future_foul_air_excluded_contacts"),
            pl.col("unknown_contact_count").sum().alias("future_unknown_contacts"),
            pl.col("special_noncontact_count")
            .sum()
            .alias("future_special_noncontact_events"),
            pl.col("pa_accounting_residual").sum().alias("future_pa_accounting_residual"),
            pl.col("game_pk").n_unique().cast(pl.Int64).alias("future_game_count"),
            pl.col("_target_date").min().alias("first_target_date"),
            pl.col("_target_date").max().alias("last_target_date"),
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
            ).alias("future_profile_observations"),
            (pl.col("future_plate_appearances") > 0).alias("has_future_pa"),
            (pl.col("future_core_events") > 0).alias("has_future_core_profile_evidence"),
            pl.lit(cutoff).alias("as_of_date"),
            pl.lit(horizon.label).alias("horizon_label"),
            pl.lit(int(horizon.calendar_days)).cast(pl.Int64).alias("horizon_calendar_days"),
            pl.lit(horizon.aggregate_pa_cap)
            .cast(pl.Int64)
            .alias("aggregate_pa_cap"),
            pl.lit(False).alias("aggregate_pa_cap_applied"),
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
        .agg(pl.col("occurrence_count").sum().alias("future_occurrence_count"))
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
            .alias("future_core_profile_rate"),
            pl.lit(cutoff).alias("as_of_date"),
            pl.lit(horizon.label).alias("horizon_label"),
        )
        .select(list(profile_schema))
        .cast(profile_schema, strict=True)
        .sort([*TARGET_ENVIRONMENT_KEY, "core_bin"])
    )

    check = (
        target_profile.group_by(list(TARGET_ENVIRONMENT_KEY))
        .agg(pl.col("future_occurrence_count").sum().alias("_profile_count"))
        .join(
            target_summary.select(*TARGET_ENVIRONMENT_KEY, "future_core_events"),
            on=list(TARGET_ENVIRONMENT_KEY),
            how="right",
        )
        .with_columns(pl.col("_profile_count").fill_null(0).cast(pl.Int64))
    )
    if check.filter(pl.col("_profile_count") != pl.col("future_core_events")).height:
        raise ValueError("future target profile counts do not reconcile to target summary")

    return target_summary, target_profile


def _add_transition_labels(scoring: pl.DataFrame) -> pl.DataFrame:
    as_of_ordinal = pl.col("as_of_level_group").replace_strict(
        LEVEL_ORDINAL, default=None, return_dtype=pl.Int64
    )
    target_ordinal = pl.col("target_level_group").replace_strict(
        LEVEL_ORDINAL, default=None, return_dtype=pl.Int64
    )
    return scoring.with_columns(
        pl.when(pl.col("as_of_environment_ambiguous"))
        .then(pl.lit("AMBIGUOUS_AS_OF_ENVIRONMENT"))
        .when((pl.col("target_level_group") == "MLB") & ~pl.col("prior_mlb_evidence"))
        .then(pl.lit("MLB_DEBUT"))
        .when((pl.col("as_of_level_group") == "MLB") & (pl.col("target_level_group") != "MLB"))
        .then(pl.lit("MLB_TO_MILB"))
        .when(target_ordinal > as_of_ordinal)
        .then(pl.lit("PROMOTION"))
        .when(target_ordinal < as_of_ordinal)
        .then(pl.lit("DEMOTION"))
        .otherwise(pl.lit("SAME_LEVEL"))
        .alias("target_transition")
    )


def build_validation_snapshot_dataset(
    summary: pl.DataFrame,
    profile: pl.DataFrame,
    *,
    cutoff: date,
    window: EvidenceWindow,
    horizon: FutureHorizon = PRIMARY_FUTURE_HORIZON,
) -> ValidationSnapshotDataset:
    """Build one predictor/target validation dataset without future leakage."""

    validate_player_game_evidence(summary, profile)
    predictor_summary, predictor_profile = build_predictor_snapshot(
        summary,
        profile,
        cutoff=cutoff,
        window=window,
    )
    context = _build_as_of_context(summary, cutoff=cutoff)
    predictor_summary = predictor_summary.join(context, on="player_id", how="left")

    target_summary, target_profile = build_future_target(
        summary,
        profile,
        cutoff=cutoff,
        horizon=horizon,
    )
    scoring = target_summary.join(predictor_summary, on="player_id", how="inner")
    if not scoring.is_empty():
        scoring = _add_transition_labels(scoring).sort(list(TARGET_ENVIRONMENT_KEY))

    target_players = set(target_summary.get_column("player_id").unique().to_list())
    predictor_players = set(predictor_summary.get_column("player_id").unique().to_list())
    scored_players = target_players & predictor_players
    metrics = {
        "as_of_date": cutoff.isoformat(),
        "window_label": window.label,
        "horizon_label": horizon.label,
        "horizon_calendar_days": int(horizon.calendar_days),
        "aggregate_pa_cap": horizon.aggregate_pa_cap,
        "aggregate_pa_cap_applied": False,
        "aggregate_pa_cap_status": "requires_pa_grain_future_events",
        "predictor_player_count": len(predictor_players),
        "target_player_count": len(target_players),
        "scored_player_count": len(scored_players),
        "target_player_without_predictor_count": len(target_players - predictor_players),
        "target_environment_row_count": int(target_summary.height),
        "scoring_row_count": int(scoring.height),
        "ambiguous_as_of_environment_scoring_row_count": (
            int(scoring.filter(pl.col("as_of_environment_ambiguous")).height)
            if not scoring.is_empty()
            else 0
        ),
        "retrospective_event_cutoff": True,
        "vintage_information_set": False,
    }
    return ValidationSnapshotDataset(
        predictor_summary=predictor_summary,
        predictor_profile=predictor_profile,
        target_summary=target_summary,
        target_profile=target_profile,
        scoring_rows=scoring,
        metrics=metrics,
    )
