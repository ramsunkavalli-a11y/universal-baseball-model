"""Leakage-safe validation primitives for the future Current Talent layer.

This module does **not** estimate talent. It freezes the date/window semantics
from ``docs/current-talent-validation-contract.md`` so future baselines and
richer models are evaluated on exactly the same chronological surface.

Historical public sources often have a reliable baseball ``game_date`` but not
a trustworthy universal game timestamp. Therefore a snapshot dated May 1 is a
boundary at the *start* of May 1:

- predictor evidence: ``game_date < 2024-05-01``;
- future target evidence: ``game_date >= 2024-05-01`` and before the exclusive
  horizon end.

This avoids using a May 1 game both as predictor and target and is reproducible
across MLB through DSL without inventing game times.

The certified historical BB/HBP/K backbone is currently player-game aggregate,
not one row per plate appearance. Future likelihood evidence therefore remains
at the complete player-game/profile grain. The 200-PA player-aggregate
diagnostic cap may retain only complete chronological games whose cumulative PA
do not exceed the cap; it never splits a game's outcome vector or fabricates PA
order inside a box score. A separate PA-event cap helper remains available for
future source tiers that truly have one canonical row per PA.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import polars as pl

from universal_baseball.current_talent_evidence import (
    PLAYER_GAME_KEY,
    validate_player_game_evidence,
)


IN_SEASON_SNAPSHOT_MONTHS = (5, 6, 7, 8, 9)
COMPLETE_GAME_AGGREGATE_CAP_POLICY = "complete_game_chronological_pa_cap_v1"


@dataclass(frozen=True, slots=True)
class FutureHorizon:
    label: str
    calendar_days: int
    aggregate_pa_cap: int | None
    primary: bool = False

    def __post_init__(self) -> None:
        if self.calendar_days <= 0:
            raise ValueError("future horizon calendar_days must be positive")
        if self.aggregate_pa_cap is not None and self.aggregate_pa_cap <= 0:
            raise ValueError("aggregate_pa_cap must be positive when supplied")


PRIMARY_FUTURE_HORIZON = FutureHorizon(
    label="future_90d",
    calendar_days=90,
    aggregate_pa_cap=200,
    primary=True,
)
SECONDARY_FUTURE_HORIZONS = (
    FutureHorizon("future_30d", 30, 200),
    FutureHorizon("future_180d", 180, 200),
    FutureHorizon("future_365d_bridge", 365, 200),
)


def in_season_snapshot_dates(season: int) -> tuple[date, ...]:
    """Return deterministic month-start validation cutoffs May through September."""

    if int(season) < 1900:
        raise ValueError(f"invalid baseball season: {season}")
    return tuple(date(int(season), month, 1) for month in IN_SEASON_SNAPSHOT_MONTHS)


def future_window(cutoff: date, horizon: FutureHorizon) -> tuple[date, date]:
    """Return ``[cutoff, exclusive_end)`` for one future target horizon."""

    return cutoff, cutoff + timedelta(days=int(horizon.calendar_days))


def add_cutoff_membership(
    frame: pl.DataFrame,
    *,
    cutoff: date,
    horizon: FutureHorizon = PRIMARY_FUTURE_HORIZON,
    game_date_column: str = "game_date",
) -> pl.DataFrame:
    """Annotate rows as predictor/target/outside using date-only chronology."""

    if game_date_column not in frame.columns:
        raise ValueError(f"validation frame missing game-date column: {game_date_column}")
    start, end = future_window(cutoff, horizon)
    parsed = pl.col(game_date_column).cast(pl.String).str.to_date(strict=False)
    return frame.with_columns(
        parsed.alias("validation_game_date"),
    ).with_columns(
        (pl.col("validation_game_date") < pl.lit(cutoff)).alias("is_predictor_evidence"),
        (
            (pl.col("validation_game_date") >= pl.lit(start))
            & (pl.col("validation_game_date") < pl.lit(end))
        ).alias("is_future_target_evidence"),
    ).with_columns(
        (~pl.col("is_predictor_evidence") & ~pl.col("is_future_target_evidence")).alias(
            "is_outside_validation_window"
        )
    )


def build_future_target_window(
    summary: pl.DataFrame,
    profile: pl.DataFrame,
    *,
    cutoff: date,
    horizon: FutureHorizon = PRIMARY_FUTURE_HORIZON,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    """Slice one leakage-safe future target window at certified player-game grain.

    All eligible future player-games inside ``[cutoff, cutoff + horizon)`` are
    retained. No playing-time minimum is imposed: players with no realized
    future PA simply have no target rows. Actual future league/level context is
    preserved so downstream scoring can distinguish same-level, promotion, and
    demotion opportunities after a training-only environment translation is fit.

    The returned rows are *uncapped* and are the canonical future evidence for
    proper likelihood scoring. Use :func:`cap_future_player_games_for_aggregate_metrics`
    only for the player-aggregate secondary diagnostic surface.
    """

    validate_player_game_evidence(summary, profile)
    start, end = future_window(cutoff, horizon)
    annotated = add_cutoff_membership(summary, cutoff=cutoff, horizon=horizon)
    target_summary_base = annotated.filter(pl.col("is_future_target_evidence")).drop(
        "validation_game_date",
        "is_predictor_evidence",
        "is_future_target_evidence",
        "is_outside_validation_window",
    )

    target_profile_base = profile.join(
        target_summary_base.select(*PLAYER_GAME_KEY),
        on=list(PLAYER_GAME_KEY),
        how="inner",
    )
    if not target_summary_base.is_empty():
        # Re-run the evidence contract on the sliced surface. This catches any
        # accidental profile orphaning or count drift introduced by windowing.
        validate_player_game_evidence(target_summary_base, target_profile_base)
    elif not target_profile_base.is_empty():
        raise ValueError("future target profile exists without future target summary rows")

    target_summary = target_summary_base.with_columns(
        pl.lit(cutoff).alias("as_of_date"),
        pl.lit(horizon.label).alias("future_horizon"),
        pl.lit(end).alias("future_window_end"),
        (
            pl.col("game_date").cast(pl.String).str.to_date(strict=False) - pl.lit(start)
        )
        .dt.total_days()
        .cast(pl.Int64)
        .alias("days_after_cutoff"),
    ).sort(["player_id", "game_date", "game_pk", "league_id"])

    target_profile = target_profile_base.with_columns(
        pl.lit(cutoff).alias("as_of_date"),
        pl.lit(horizon.label).alias("future_horizon"),
        pl.lit(end).alias("future_window_end"),
        (
            pl.col("game_date").cast(pl.String).str.to_date(strict=False) - pl.lit(start)
        )
        .dt.total_days()
        .cast(pl.Int64)
        .alias("days_after_cutoff"),
    ).sort(["player_id", "game_date", "game_pk", "league_id", "core_bin"])

    metrics: dict[str, Any] = {
        "as_of_date": cutoff.isoformat(),
        "future_horizon": horizon.label,
        "future_window_end": end.isoformat(),
        "calendar_days": int(horizon.calendar_days),
        "aggregate_pa_cap": horizon.aggregate_pa_cap,
        "future_player_game_count": int(target_summary.height),
        "future_profile_row_count": int(target_profile.height),
        "future_player_count": int(target_summary.get_column("player_id").n_unique())
        if not target_summary.is_empty()
        else 0,
        "future_plate_appearances": int(
            target_summary.get_column("batting_plate_appearances").sum() or 0
        )
        if not target_summary.is_empty()
        else 0,
        "future_core_events": int(target_summary.get_column("core_profile_event_count").sum() or 0)
        if not target_summary.is_empty()
        else 0,
        "future_actual_league_count": int(target_summary.get_column("league_id").n_unique())
        if not target_summary.is_empty()
        else 0,
        "future_level_count": int(target_summary.get_column("level_group").n_unique())
        if not target_summary.is_empty()
        else 0,
        "likelihood_surface": "all_realized_future_player_game_evidence_uncapped",
    }
    return target_summary, target_profile, metrics


def cap_future_player_games_for_aggregate_metrics(
    future_summary: pl.DataFrame,
    future_profile: pl.DataFrame,
    *,
    cap: int = 200,
    player_columns: tuple[str, ...] = ("as_of_date", "future_horizon", "player_id"),
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    """Cap player-aggregate targets without splitting certified game vectors.

    The historical outcome backbone does not expose canonical PA order for
    BB/HBP/K. A game whose inclusion would push cumulative future PA above the
    cap is therefore excluded, as are all later games for that player/window.
    This produces ``<= cap`` retained PA while preserving complete game vectors.

    The difference between an ideal exact PA cap and the complete-game cap is
    returned as ``complete_game_cap_shortfall_pa`` so the approximation remains
    measurable rather than hidden. This function must not be used to discard
    rows from event/profile likelihood scoring.
    """

    if cap <= 0:
        raise ValueError("future player-game PA cap must be positive")
    required_summary = {
        *PLAYER_GAME_KEY,
        *player_columns,
        "batting_plate_appearances",
    }
    missing_summary = sorted(required_summary - set(future_summary.columns))
    if missing_summary:
        raise ValueError(
            f"future player-game summary missing aggregate-cap fields: {missing_summary}"
        )
    missing_profile = sorted(set(PLAYER_GAME_KEY) - set(future_profile.columns))
    if missing_profile:
        raise ValueError(
            f"future player-game profile missing aggregate-cap keys: {missing_profile}"
        )
    if future_summary.is_empty():
        if not future_profile.is_empty():
            raise ValueError("future profile cannot be nonempty when future summary is empty")
        return future_summary, future_profile, {
            "aggregate_cap_policy": COMPLETE_GAME_AGGREGATE_CAP_POLICY,
            "aggregate_pa_cap": int(cap),
            "uncapped_player_game_count": 0,
            "capped_player_game_count": 0,
            "uncapped_plate_appearances": 0,
            "capped_plate_appearances": 0,
            "player_window_count": 0,
            "player_window_over_cap_count": 0,
            "complete_game_cap_shortfall_pa": 0,
        }

    if future_summary.filter(pl.col("batting_plate_appearances") <= 0).height:
        raise ValueError("future player-game aggregate cap requires positive-PA game rows")

    parsed = future_summary.with_columns(
        pl.col("game_date").cast(pl.String).str.to_date(strict=False).alias("_game_date_order"),
        pl.col("game_pk").cast(pl.Int64, strict=False).alias("_game_pk_order"),
        pl.col("league_id").cast(pl.Int64, strict=False).alias("_league_id_order"),
        pl.col("batting_plate_appearances").cast(pl.Int64, strict=False).alias("_pa_order"),
    )
    if parsed.filter(
        pl.any_horizontal(
            [
                pl.col("_game_date_order").is_null(),
                pl.col("_game_pk_order").is_null(),
                pl.col("_league_id_order").is_null(),
                pl.col("_pa_order").is_null(),
            ]
        )
    ).height:
        raise ValueError("future player-game frame contains unorderable game keys or PA")

    group_columns = list(player_columns)
    sort_columns = [
        *group_columns,
        "_game_date_order",
        "_game_pk_order",
        "_league_id_order",
    ]
    ordered = parsed.sort(sort_columns).with_columns(
        pl.col("_pa_order").cum_sum().over(group_columns).alias("_cumulative_future_pa")
    )
    capped = ordered.filter(pl.col("_cumulative_future_pa") <= int(cap)).drop(
        "_game_date_order",
        "_game_pk_order",
        "_league_id_order",
        "_pa_order",
        "_cumulative_future_pa",
    )

    capped_keys = capped.select(*PLAYER_GAME_KEY)
    capped_profile = future_profile.join(capped_keys, on=list(PLAYER_GAME_KEY), how="inner")

    uncapped_totals = future_summary.group_by(group_columns).agg(
        pl.col("batting_plate_appearances").sum().cast(pl.Int64).alias("_uncapped_pa")
    )
    capped_totals = capped.group_by(group_columns).agg(
        pl.col("batting_plate_appearances").sum().cast(pl.Int64).alias("_capped_pa")
    )
    comparison = uncapped_totals.join(capped_totals, on=group_columns, how="left").with_columns(
        pl.col("_capped_pa").fill_null(0).cast(pl.Int64),
        pl.when(pl.col("_uncapped_pa") < int(cap))
        .then(pl.col("_uncapped_pa"))
        .otherwise(pl.lit(int(cap)))
        .cast(pl.Int64)
        .alias("_ideal_capped_pa"),
    )
    shortfall = int(
        comparison.select((pl.col("_ideal_capped_pa") - pl.col("_capped_pa")).sum()).item()
        or 0
    )

    metrics = {
        "aggregate_cap_policy": COMPLETE_GAME_AGGREGATE_CAP_POLICY,
        "aggregate_pa_cap": int(cap),
        "uncapped_player_game_count": int(future_summary.height),
        "capped_player_game_count": int(capped.height),
        "uncapped_plate_appearances": int(
            future_summary.get_column("batting_plate_appearances").sum() or 0
        ),
        "capped_plate_appearances": int(capped.get_column("batting_plate_appearances").sum() or 0),
        "player_window_count": int(comparison.height),
        "player_window_over_cap_count": int(
            comparison.filter(pl.col("_uncapped_pa") > int(cap)).height
        ),
        "complete_game_cap_shortfall_pa": shortfall,
    }
    return (
        capped.sort([*group_columns, "game_date", "game_pk", "league_id"]),
        capped_profile.sort([*group_columns, "game_date", "game_pk", "league_id", "core_bin"]),
        metrics,
    )


def cap_future_pa_for_aggregate_metrics(
    future_events: pl.DataFrame,
    *,
    cap: int = 200,
    player_columns: tuple[str, ...] = ("player_id",),
) -> pl.DataFrame:
    """Deterministically cap true PA-event rows for aggregate secondary metrics.

    Proper event-level likelihood scoring should use all eligible future PA.
    This helper is reserved for source tiers that genuinely expose one canonical
    row per plate appearance. The certified historical player-game outcome layer
    should instead use :func:`cap_future_player_games_for_aggregate_metrics`.
    """

    if cap <= 0:
        raise ValueError("future PA cap must be positive")
    required = {*player_columns, "game_date", "game_pk", "at_bat_index"}
    missing = sorted(required - set(future_events.columns))
    if missing:
        raise ValueError(f"future event frame missing cap-order fields: {missing}")
    if future_events.is_empty():
        return future_events

    working = future_events.with_row_index("_original_row_index").with_columns(
        pl.col("game_date").cast(pl.String).str.to_date(strict=False).alias("_game_date_order"),
        pl.col("game_pk").cast(pl.Int64, strict=False).alias("_game_pk_order"),
        pl.col("at_bat_index").cast(pl.Int64, strict=False).alias("_at_bat_order"),
    )
    if working.filter(
        pl.any_horizontal(
            [
                pl.col("_game_date_order").is_null(),
                pl.col("_game_pk_order").is_null(),
                pl.col("_at_bat_order").is_null(),
            ]
        )
    ).height:
        raise ValueError("future event frame contains unorderable game/play keys")

    sort_columns = [
        *player_columns,
        "_game_date_order",
        "_game_pk_order",
        "_at_bat_order",
        "_original_row_index",
    ]
    ranked = (
        working.sort(sort_columns)
        .with_columns(
            pl.int_range(pl.len()).over(list(player_columns)).alias("_player_future_pa_index")
        )
        .filter(pl.col("_player_future_pa_index") < int(cap))
    )
    return ranked.drop(
        "_original_row_index",
        "_game_date_order",
        "_game_pk_order",
        "_at_bat_order",
        "_player_future_pa_index",
    )
