"""Chronology-safe evidence assembly for frozen Current Talent challenger 2.

This module sits between accepted source materialization and any development
scoring.  It is source-agnostic: accepted MLB and MiLB target tables already
share one canonical schema, so this layer only:

- validates and concatenates those supported target contacts;
- attaches the frozen nine-group terminal-value scale;
- slices the four predeclared cutoff surfaces with exact half-open chronology;
- verifies baseline support before the frozen additive baseline may be fit; and
- exposes one canonical future-event key surface that both comparator and richer
  candidate must use.

It does not attach richer tracking features, fit the richer residual, compute
MSE/MAE, inspect 2023, or make a promotion decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable

import polars as pl

from universal_baseball.bin_value_policy import LEAGUE_LEVEL_GROUP
from universal_baseball.current_talent_contact_value import (
    FROZEN_TERMINAL_OUTCOME_VALUES,
    ContactValueBaselineFit,
    attach_frozen_terminal_values,
    fit_contact_value_baseline,
)
from universal_baseball.current_talent_validation import (
    PRIMARY_FUTURE_HORIZON,
    future_window,
)
from universal_baseball.performance_season import CONTACT_CORE_BINS


CONTACT_VALUE_TARGET_KEY = ("game_pk", "at_bat_index", "pitch_number")
CONTACT_VALUE_REQUIRED_SOURCE_COLUMNS = (
    "event_date",
    "game_pk",
    "at_bat_index",
    "pitch_number",
    "league_id",
    "level_group",
    "player_id",
    "participant_authority",
    "contact_bin",
    "terminal_outcome_group",
    "terminal_outcome_status",
)
CONTACT_VALUE_ALLOWED_SOURCE_YEARS = frozenset({2021, 2022})
CONTACT_VALUE_ALLOWED_LEVEL_GROUPS = frozenset(
    {"MLB", *set(LEAGUE_LEVEL_GROUP.values())}
)
CONTACT_VALUE_FROZEN_CUTOFFS = (
    date(2021, 7, 15),
    date(2022, 7, 15),
    date(2022, 8, 1),
    date(2022, 9, 1),
)
CONTACT_VALUE_FROZEN_CUTOFF_SET = frozenset(CONTACT_VALUE_FROZEN_CUTOFFS)


@dataclass(frozen=True, slots=True)
class ContactValueCutoffSurface:
    """One frozen cutoff's pre-scoring baseline/future target surface."""

    cutoff_date: date
    future_end_exclusive: date
    baseline_contacts: pl.DataFrame
    future_contacts: pl.DataFrame
    future_target_keys: pl.DataFrame
    baseline_fit: ContactValueBaselineFit
    metrics: dict[str, Any]


def _require_columns(frame: pl.DataFrame, required: Iterable[str], label: str) -> None:
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing fields: {missing}")


def _duplicates(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.group_by(list(CONTACT_VALUE_TARGET_KEY)).len().filter(pl.col("len") > 1)


def prepare_contact_value_evidence(
    source_frames: Iterable[pl.DataFrame],
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Validate, combine, and value accepted 2021-22 target-contact sources."""

    frames = list(source_frames)
    if not frames:
        raise ValueError("contact-value evidence requires at least one source frame")
    normalized: list[pl.DataFrame] = []
    for index, frame in enumerate(frames):
        _require_columns(
            frame,
            CONTACT_VALUE_REQUIRED_SOURCE_COLUMNS,
            f"contact-value source frame {index}",
        )
        normalized.append(
            frame.select(*CONTACT_VALUE_REQUIRED_SOURCE_COLUMNS).with_columns(
                pl.col("event_date").cast(pl.Date, strict=False),
                pl.col("game_pk").cast(pl.Int64, strict=False),
                pl.col("at_bat_index").cast(pl.Int64, strict=False),
                pl.col("pitch_number").cast(pl.Int64, strict=False),
                pl.col("league_id").cast(pl.Int64, strict=False),
                pl.col("level_group").cast(pl.String),
                pl.col("player_id").cast(pl.Int64, strict=False),
                pl.col("participant_authority").cast(pl.String),
                pl.col("contact_bin").cast(pl.String),
                pl.col("terminal_outcome_group").cast(pl.String),
                pl.col("terminal_outcome_status").cast(pl.String),
            )
        )

    combined = pl.concat(normalized, how="vertical_relaxed")
    if combined.is_empty():
        raise ValueError("contact-value combined source evidence is empty")

    required_nonnull = [
        "event_date",
        "game_pk",
        "at_bat_index",
        "pitch_number",
        "league_id",
        "level_group",
        "player_id",
        "contact_bin",
        "terminal_outcome_group",
    ]
    if combined.select(pl.any_horizontal([pl.col(c).is_null() for c in required_nonnull])).to_series().any():
        raise ValueError("contact-value source evidence contains null required fields")

    duplicate = _duplicates(combined)
    if not duplicate.is_empty():
        raise ValueError(
            "combined contact-value evidence contains duplicate target contact keys: "
            f"{duplicate.height}"
        )

    years = {
        int(value)
        for value in combined.get_column("event_date").dt.year().unique().to_list()
    }
    unauthorized_years = sorted(years - set(CONTACT_VALUE_ALLOWED_SOURCE_YEARS))
    if unauthorized_years:
        raise ValueError(
            "contact-value pre-scoring evidence rejects unauthorized source years: "
            f"{unauthorized_years}"
        )

    groups = set(combined.get_column("terminal_outcome_group").unique().to_list())
    unknown_groups = sorted(groups - set(FROZEN_TERMINAL_OUTCOME_VALUES))
    if unknown_groups:
        raise ValueError(f"contact-value evidence has unsupported terminal groups: {unknown_groups}")

    bins = set(combined.get_column("contact_bin").unique().to_list())
    unknown_bins = sorted(bins - set(CONTACT_CORE_BINS))
    if unknown_bins:
        raise ValueError(f"contact-value evidence has unsupported contact bins: {unknown_bins}")

    levels = set(combined.get_column("level_group").unique().to_list())
    unknown_levels = sorted(levels - set(CONTACT_VALUE_ALLOWED_LEVEL_GROUPS))
    if unknown_levels:
        raise ValueError(f"contact-value evidence has unsupported level groups: {unknown_levels}")

    valued = attach_frozen_terminal_values(combined, require_supported=True).sort(
        ["event_date", *CONTACT_VALUE_TARGET_KEY]
    )
    if valued.get_column("terminal_value").null_count():
        raise ValueError("contact-value frozen terminal-value attachment is incomplete")

    metrics: dict[str, Any] = {
        "source_frame_count": len(frames),
        "combined_target_contact_count": int(valued.height),
        "first_event_date": valued.get_column("event_date").min().isoformat(),
        "last_event_date": valued.get_column("event_date").max().isoformat(),
        "observed_source_years": sorted(years),
        "observed_level_groups": sorted(str(value) for value in levels),
        "observed_contact_bins": sorted(str(value) for value in bins),
        "observed_terminal_groups": sorted(str(value) for value in groups),
        "duplicate_target_key_count": 0,
        "terminal_values_attached": True,
        "model_scoring": False,
        "richer_features_attached": False,
        "richer_residual_fitted": False,
        "accessed_2023": False,
    }
    return valued, metrics


def build_contact_value_cutoff_surface(
    valued_contacts: pl.DataFrame,
    *,
    cutoff_date: date,
) -> ContactValueCutoffSurface:
    """Build one frozen, leakage-safe pre-scoring baseline/future surface.

    Baseline evidence is strictly ``event_date < cutoff``.  The target is exactly
    ``[cutoff, cutoff + 90 calendar days)`` using the existing Current Talent
    validation horizon.  A deterministic additive baseline is fit only to prove
    support/rank/chronology before scoring code exists; no prediction loss is
    calculated here.
    """

    if cutoff_date not in CONTACT_VALUE_FROZEN_CUTOFF_SET:
        raise ValueError(f"contact-value cutoff is not frozen/authorized: {cutoff_date.isoformat()}")
    _require_columns(
        valued_contacts,
        [*CONTACT_VALUE_REQUIRED_SOURCE_COLUMNS, "terminal_value"],
        "valued contact evidence",
    )
    if valued_contacts.is_empty():
        raise ValueError("valued contact evidence is empty")

    working = valued_contacts.with_columns(
        pl.col("event_date").cast(pl.Date, strict=False),
        pl.col("terminal_value").cast(pl.Float64, strict=False),
    )
    if working.filter(pl.col("event_date").is_null()).height:
        raise ValueError("valued contact evidence contains invalid event dates")
    if _duplicates(working).height:
        raise ValueError("valued contact evidence contains duplicate target contact keys")

    target_start, target_end = future_window(cutoff_date, PRIMARY_FUTURE_HORIZON)
    baseline = working.filter(pl.col("event_date") < pl.lit(cutoff_date)).sort(
        ["event_date", *CONTACT_VALUE_TARGET_KEY]
    )
    future = working.filter(
        (pl.col("event_date") >= pl.lit(target_start))
        & (pl.col("event_date") < pl.lit(target_end))
    ).sort(["event_date", *CONTACT_VALUE_TARGET_KEY])
    if baseline.is_empty():
        raise ValueError("contact-value cutoff has no pre-cutoff baseline evidence")
    if future.is_empty():
        raise ValueError("contact-value cutoff has no future target evidence")

    if baseline.get_column("event_date").max() >= cutoff_date:
        raise ValueError("baseline chronology includes on/after-cutoff evidence")
    if future.get_column("event_date").min() < cutoff_date:
        raise ValueError("future chronology includes pre-cutoff evidence")
    if future.get_column("event_date").max() >= target_end:
        raise ValueError("future chronology includes evidence at/after exclusive end")

    baseline_bins = set(baseline.get_column("contact_bin").unique().to_list())
    future_bins = set(future.get_column("contact_bin").unique().to_list())
    missing_frozen_bins = sorted(set(CONTACT_CORE_BINS) - baseline_bins)
    if missing_frozen_bins:
        raise ValueError(
            f"contact-value baseline lacks frozen contact-bin support: {missing_frozen_bins}"
        )
    unsupported_future_bins = sorted(future_bins - baseline_bins)
    if unsupported_future_bins:
        raise ValueError(
            f"contact-value future has contact bins absent from baseline: {unsupported_future_bins}"
        )

    baseline_levels = set(baseline.get_column("level_group").unique().to_list())
    future_levels = set(future.get_column("level_group").unique().to_list())
    if "MLB" not in baseline_levels:
        raise ValueError("contact-value baseline lacks frozen MLB reference level")
    unsupported_future_levels = sorted(future_levels - baseline_levels)
    if unsupported_future_levels:
        raise ValueError(
            "contact-value future has level groups absent from baseline: "
            f"{unsupported_future_levels}"
        )

    fit = fit_contact_value_baseline(baseline, cutoff_date=cutoff_date)
    if set(fit.fitted_level_groups) != baseline_levels:
        raise ValueError("contact-value baseline fit lost observed level-group support")

    key_columns = [*CONTACT_VALUE_TARGET_KEY]
    future_keys = future.select(*key_columns).sort(key_columns)
    if _duplicates(future_keys).height:
        raise ValueError("future target key surface contains duplicates")

    baseline_key_set = set(map(tuple, baseline.select(*key_columns).iter_rows()))
    future_key_set = set(map(tuple, future_keys.iter_rows()))
    if baseline_key_set & future_key_set:
        raise ValueError("baseline and future target contact keys overlap")

    metrics: dict[str, Any] = {
        "cutoff_date": cutoff_date.isoformat(),
        "future_window_start": target_start.isoformat(),
        "future_window_end_exclusive": target_end.isoformat(),
        "future_window_calendar_days": int(PRIMARY_FUTURE_HORIZON.calendar_days),
        "baseline_contact_count": int(baseline.height),
        "future_target_contact_count": int(future.height),
        "baseline_first_event_date": baseline.get_column("event_date").min().isoformat(),
        "baseline_last_event_date": baseline.get_column("event_date").max().isoformat(),
        "future_first_event_date": future.get_column("event_date").min().isoformat(),
        "future_last_event_date": future.get_column("event_date").max().isoformat(),
        "baseline_contact_bins": sorted(str(value) for value in baseline_bins),
        "future_contact_bins": sorted(str(value) for value in future_bins),
        "baseline_level_groups": sorted(str(value) for value in baseline_levels),
        "future_level_groups": sorted(str(value) for value in future_levels),
        "baseline_fit_event_count": int(fit.fitted_event_count),
        "baseline_parameter_count": int(fit.parameter_count),
        "baseline_fit_max_event_date": fit.max_training_event_date.isoformat(),
        "future_target_key_count": int(future_keys.height),
        "comparator_richer_paired_key_contract": "same_future_target_key_surface_required",
        "baseline_fitted": True,
        "model_scoring": False,
        "richer_features_attached": False,
        "richer_residual_fitted": False,
        "accessed_2023": False,
    }
    return ContactValueCutoffSurface(
        cutoff_date=cutoff_date,
        future_end_exclusive=target_end,
        baseline_contacts=baseline,
        future_contacts=future,
        future_target_keys=future_keys,
        baseline_fit=fit,
        metrics=metrics,
    )
