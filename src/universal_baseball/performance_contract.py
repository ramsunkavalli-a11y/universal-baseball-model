"""Stable contract for batting Performance outputs consumed by later layers.

The Performance layer is evidence/result description, not Current Talent.  This
module freezes the minimum columns and invariants that downstream talent,
projection, and value code may rely on without depending on POC-only orchestration
or incidental extra columns.
"""

from __future__ import annotations

from typing import Any

import polars as pl


BATTING_PERFORMANCE_CONTRACT_VERSION = "batting_performance_v1"

SUMMARY_KEY = ("season", "league_id", "player_id")
PROFILE_KEY = (*SUMMARY_KEY, "core_bin")
BIN_VALUE_KEY = ("season", "league_id", "core_bin")

SUMMARY_REQUIRED_COLUMNS = frozenset(
    {
        *SUMMARY_KEY,
        "batting_plate_appearances",
        "bb_hbp_count",
        "strikeout_count",
        "aggregate_contact_count",
        "contact_event_count",
        "core_contact_count",
        "bunt_contact_count",
        "foul_air_excluded_count",
        "unknown_contact_count",
        "official_overlay_contact_count",
        "core_profile_event_count",
        "core_profile_uncovered_pa_count",
        "core_profile_coverage_rate",
        "contact_count_residual_vs_aggregate",
        "valued_core_event_count",
        "unvalued_core_event_count",
        "core_expected_run_value_total",
        "core_expected_run_value_per_100_pa",
        "has_uncertified_or_missing_bin_value",
    }
)

PROFILE_REQUIRED_COLUMNS = frozenset(
    {
        *PROFILE_KEY,
        "occurrence_count",
        "batting_plate_appearances",
        "share_of_plate_appearances",
        "estimated_mean_run_value",
        "expected_run_value",
        "estimator_method",
        "estimator_certified",
    }
)

BIN_VALUE_REQUIRED_COLUMNS = frozenset(
    {
        *BIN_VALUE_KEY,
        "estimated_mean_run_value",
        "estimator_method",
        "estimator_certified",
        "prior_strength",
        "direct_occurrence_count",
    }
)


def _require_columns(frame: pl.DataFrame, required: frozenset[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing Performance contract columns: {missing}")


def _require_unique(frame: pl.DataFrame, key: tuple[str, ...], label: str) -> None:
    duplicates = frame.group_by(list(key)).len().filter(pl.col("len") > 1)
    if not duplicates.is_empty():
        raise ValueError(f"{label} violates Performance contract key {key}")


def validate_batting_performance_contract(
    summary: pl.DataFrame,
    profile: pl.DataFrame,
    bin_values: pl.DataFrame,
    *,
    require_certified_values: bool = True,
) -> dict[str, Any]:
    """Validate the stable Performance boundary and return compact metrics.

    Extra columns are allowed so source/provenance details can evolve without a
    contract bump.  Downstream code should depend only on the required surface.
    A contract-version change is required when the meaning of one of these
    fields changes, not when an additive diagnostic column is introduced.
    """

    _require_columns(summary, SUMMARY_REQUIRED_COLUMNS, "summary")
    _require_columns(profile, PROFILE_REQUIRED_COLUMNS, "profile")
    _require_columns(bin_values, BIN_VALUE_REQUIRED_COLUMNS, "bin values")
    _require_unique(summary, SUMMARY_KEY, "summary")
    _require_unique(profile, PROFILE_KEY, "profile")
    _require_unique(bin_values, BIN_VALUE_KEY, "bin values")

    if summary.is_empty():
        raise ValueError("batting Performance summary is empty")

    count_columns = [
        "batting_plate_appearances",
        "bb_hbp_count",
        "strikeout_count",
        "aggregate_contact_count",
        "contact_event_count",
        "core_contact_count",
        "bunt_contact_count",
        "foul_air_excluded_count",
        "unknown_contact_count",
        "official_overlay_contact_count",
        "core_profile_event_count",
        "core_profile_uncovered_pa_count",
        "valued_core_event_count",
        "unvalued_core_event_count",
    ]
    negative_counts = summary.filter(
        pl.any_horizontal([pl.col(column) < 0 for column in count_columns])
    )
    if not negative_counts.is_empty():
        raise ValueError("batting Performance summary contains negative count fields")

    bad_coverage = summary.filter(
        pl.col("core_profile_coverage_rate").is_not_null()
        & (
            (pl.col("core_profile_coverage_rate") < 0)
            | (pl.col("core_profile_coverage_rate") > 1)
        )
    )
    if not bad_coverage.is_empty():
        raise ValueError("core_profile_coverage_rate must lie in [0, 1]")

    bad_core_accounting = summary.filter(
        pl.col("core_profile_event_count") + pl.col("core_profile_uncovered_pa_count")
        != pl.col("batting_plate_appearances")
    )
    if not bad_core_accounting.is_empty():
        raise ValueError("core profile covered + uncovered counts must equal PA")

    bad_value_accounting = summary.filter(
        pl.col("valued_core_event_count") + pl.col("unvalued_core_event_count")
        != pl.col("core_profile_event_count")
    )
    if not bad_value_accounting.is_empty():
        raise ValueError("valued + unvalued core counts must equal core event count")

    summary_keys = summary.select(list(SUMMARY_KEY))
    orphan_profile = profile.select(list(SUMMARY_KEY)).unique().join(
        summary_keys, on=list(SUMMARY_KEY), how="anti"
    )
    if not orphan_profile.is_empty():
        raise ValueError("Performance profile contains player keys absent from summary")

    value_keys = bin_values.select(list(BIN_VALUE_KEY))
    orphan_bins = (
        profile.filter(pl.col("occurrence_count") > 0)
        .select(list(BIN_VALUE_KEY))
        .unique()
        .join(value_keys, on=list(BIN_VALUE_KEY), how="anti")
    )
    if not orphan_bins.is_empty():
        raise ValueError("Performance profile contains core bins absent from value table")

    bad_profile_share = profile.filter(
        pl.col("share_of_plate_appearances").is_not_null()
        & (
            (pl.col("share_of_plate_appearances") < 0)
            | (pl.col("share_of_plate_appearances") > 1)
        )
    )
    if not bad_profile_share.is_empty():
        raise ValueError("profile share_of_plate_appearances must lie in [0, 1]")

    if require_certified_values:
        uncertified_summary = summary.filter(
            pl.col("has_uncertified_or_missing_bin_value")
            | (pl.col("unvalued_core_event_count") > 0)
        )
        uncertified_bins = bin_values.filter(~pl.col("estimator_certified").fill_null(False))
        uncertified_profile = profile.filter(
            (pl.col("occurrence_count") > 0)
            & ~pl.col("estimator_certified").fill_null(False)
        )
        if (
            not uncertified_summary.is_empty()
            or not uncertified_bins.is_empty()
            or not uncertified_profile.is_empty()
        ):
            raise ValueError("production Performance contract requires certified bin values")

    total_pa = int(summary.get_column("batting_plate_appearances").sum() or 0)
    core_events = int(summary.get_column("core_profile_event_count").sum() or 0)
    contacts = int(summary.get_column("contact_event_count").sum() or 0)
    unknown = int(summary.get_column("unknown_contact_count").sum() or 0)
    return {
        "contract_version": BATTING_PERFORMANCE_CONTRACT_VERSION,
        "summary_row_count": summary.height,
        "profile_row_count": profile.height,
        "bin_value_row_count": bin_values.height,
        "total_plate_appearances": total_pa,
        "total_core_profile_events": core_events,
        "core_profile_coverage_rate": core_events / total_pa if total_pa else None,
        "total_contact_events": contacts,
        "unknown_contact_count": unknown,
        "unknown_contact_rate": unknown / contacts if contacts else None,
        "certified_values_required": bool(require_certified_values),
    }
