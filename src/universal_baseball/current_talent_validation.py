"""Leakage-safe validation primitives for the future Current Talent layer.

This module does **not** estimate talent.  It freezes the date/window semantics
from ``docs/current-talent-validation-contract.md`` so future baselines and
richer models are evaluated on exactly the same chronological surface.

Historical public sources often have a reliable baseball ``game_date`` but not
a trustworthy universal game timestamp.  Therefore a snapshot dated May 1 is a
boundary at the *start* of May 1:

- predictor evidence: ``game_date < 2024-05-01``;
- future target evidence: ``game_date >= 2024-05-01`` and before the exclusive
  horizon end.

This avoids using a May 1 game both as predictor and target and is reproducible
across MLB through DSL without inventing game times.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import polars as pl


IN_SEASON_SNAPSHOT_MONTHS = (5, 6, 7, 8, 9)


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


def cap_future_pa_for_aggregate_metrics(
    future_events: pl.DataFrame,
    *,
    cap: int = 200,
    player_columns: tuple[str, ...] = ("player_id",),
) -> pl.DataFrame:
    """Deterministically cap future PA for *aggregate* secondary metrics.

    Proper event-level likelihood scoring should use all eligible future PA.
    This helper exists only for player-aggregate MAE/RMSE style diagnostics, per
    the validation contract.  Rows are ordered chronologically and then by
    canonical play key so everyday MLB players do not dominate merely through
    opportunity volume.
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

    sort_columns = [*player_columns, "_game_date_order", "_game_pk_order", "_at_bat_order", "_original_row_index"]
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
