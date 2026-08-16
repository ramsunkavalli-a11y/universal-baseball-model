"""Combine certified level outputs into an affiliated Performance materialization.

The first production batting Performance transform is built independently by
filename level so source and calibration failures stay localized. This module
combines those canonical outputs without collapsing actual league or level
context. A player who appears at multiple levels therefore has multiple
player-league-season rows; cross-level talent inference belongs to the later
Current Talent layer, not here.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import polars as pl

from universal_baseball.bin_value_policy import LEAGUE_LEVEL_GROUP
from universal_baseball.performance_level_config import PERFORMANCE_LEVEL_SPECS_2024


LEAGUE_FILENAME_LEVEL: dict[int, str] = {
    int(league_id): slug
    for slug, spec in PERFORMANCE_LEVEL_SPECS_2024.items()
    for league_id in spec.league_ids
}


def _validate_unique(frame: pl.DataFrame, key: list[str], label: str) -> None:
    missing = sorted(set(key) - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing canonical key columns: {missing}")
    duplicates = frame.group_by(key).len().filter(pl.col("len") > 1)
    if not duplicates.is_empty():
        raise ValueError(f"{label} contains duplicate canonical keys: {key}")


def _add_level_context(frame: pl.DataFrame, label: str) -> pl.DataFrame:
    if "league_id" not in frame.columns:
        raise ValueError(f"{label} missing league_id")
    league_ids = frame.get_column("league_id").cast(pl.Int64, strict=False)
    unknown = sorted(
        int(value)
        for value in league_ids.drop_nulls().unique().to_list()
        if int(value) not in LEAGUE_LEVEL_GROUP
    )
    if unknown:
        raise ValueError(f"{label} contains uncertified affiliated league IDs: {unknown}")

    level_group_map = {int(k): str(v) for k, v in LEAGUE_LEVEL_GROUP.items()}
    filename_map = dict(LEAGUE_FILENAME_LEVEL)
    return frame.with_columns(
        pl.col("league_id").cast(pl.Int64),
        pl.col("league_id")
        .cast(pl.Int64)
        .replace_strict(level_group_map, default=None, return_dtype=pl.String)
        .alias("level_group"),
        pl.col("league_id")
        .cast(pl.Int64)
        .replace_strict(filename_map, default=None, return_dtype=pl.String)
        .alias("filename_level"),
    )


def _concat(frames: Iterable[pl.DataFrame], label: str) -> pl.DataFrame:
    materialized = list(frames)
    if not materialized:
        raise ValueError(f"no {label} frames supplied")
    if any(frame.is_empty() for frame in materialized):
        raise ValueError(f"{label} contains an empty level frame")
    return pl.concat(materialized, how="vertical_relaxed")


def combine_batting_performance_frames(
    summaries: Iterable[pl.DataFrame],
    profiles: Iterable[pl.DataFrame],
    bin_values: Iterable[pl.DataFrame],
    *,
    expected_season: int | None = None,
    require_all_certified_leagues: bool = True,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    """Combine level outputs while enforcing canonical affiliated grains."""

    summary = _add_level_context(_concat(summaries, "summary"), "summary")
    profile = _add_level_context(_concat(profiles, "profile"), "profile")
    values = _add_level_context(_concat(bin_values, "bin-value"), "bin-value")

    if expected_season is not None:
        for label, frame in (("summary", summary), ("profile", profile), ("bin-value", values)):
            seasons = sorted(
                int(value)
                for value in frame.get_column("season").cast(pl.Int64).unique().to_list()
            )
            if seasons != [int(expected_season)]:
                raise ValueError(
                    f"{label} season coverage mismatch: observed={seasons}, "
                    f"expected={[int(expected_season)]}"
                )

    _validate_unique(summary, ["season", "league_id", "player_id"], "summary")
    _validate_unique(
        profile,
        ["season", "league_id", "player_id", "core_bin"],
        "profile",
    )
    _validate_unique(values, ["season", "league_id", "core_bin"], "bin-value")

    expected_leagues = set(int(value) for value in LEAGUE_LEVEL_GROUP)
    observed_summary_leagues = set(
        int(value) for value in summary.get_column("league_id").unique().to_list()
    )
    observed_profile_leagues = set(
        int(value) for value in profile.get_column("league_id").unique().to_list()
    )
    observed_value_leagues = set(
        int(value) for value in values.get_column("league_id").unique().to_list()
    )
    if require_all_certified_leagues:
        for label, observed in (
            ("summary", observed_summary_leagues),
            ("profile", observed_profile_leagues),
            ("bin-value", observed_value_leagues),
        ):
            if observed != expected_leagues:
                raise ValueError(
                    f"{label} affiliated league coverage mismatch: "
                    f"missing={sorted(expected_leagues - observed)}, "
                    f"extra={sorted(observed - expected_leagues)}"
                )

    summary_keys = summary.select("season", "league_id", "player_id")
    orphan_profile = profile.select("season", "league_id", "player_id").unique().join(
        summary_keys,
        on=["season", "league_id", "player_id"],
        how="anti",
    )
    if not orphan_profile.is_empty():
        raise ValueError("profile contains player-league-season keys absent from summary")

    value_keys = values.select("season", "league_id", "core_bin")
    orphan_profile_bins = profile.filter(pl.col("occurrence_count") > 0).select(
        "season", "league_id", "core_bin"
    ).unique().join(
        value_keys,
        on=["season", "league_id", "core_bin"],
        how="anti",
    )
    if not orphan_profile_bins.is_empty():
        raise ValueError("profile contains valued core bins absent from league bin-value table")

    total_pa = int(summary.get_column("batting_plate_appearances").sum() or 0)
    core_events = int(summary.get_column("core_profile_event_count").sum() or 0)
    contacts = int(summary.get_column("contact_event_count").sum() or 0)
    residual = int(summary.get_column("contact_count_residual_vs_aggregate").sum() or 0)
    unknown_contacts = int(summary.get_column("unknown_contact_count").sum() or 0)
    overlay_contacts = int(summary.get_column("official_overlay_contact_count").sum() or 0)
    changed_levels = sorted(summary.get_column("level_group").unique().to_list())

    metrics: dict[str, Any] = {
        "summary_row_count": summary.height,
        "profile_row_count": profile.height,
        "bin_value_row_count": values.height,
        "actual_league_count": len(observed_summary_leagues),
        "level_group_count": len(changed_levels),
        "level_groups": changed_levels,
        "total_plate_appearances": total_pa,
        "total_contact_events": contacts,
        "total_core_profile_events": core_events,
        "core_profile_coverage_rate": core_events / total_pa if total_pa else None,
        "total_contact_count_residual_vs_aggregate": residual,
        "contact_residual_rate_vs_contact_events": residual / contacts if contacts else None,
        "unknown_contact_count": unknown_contacts,
        "unknown_contact_rate": unknown_contacts / contacts if contacts else None,
        "official_overlay_contact_count": overlay_contacts,
        "official_overlay_contact_rate": overlay_contacts / contacts if contacts else None,
        "uncertified_or_missing_bin_value_player_rows": summary.filter(
            pl.col("has_uncertified_or_missing_bin_value")
        ).height,
        "unvalued_core_event_count": int(
            summary.get_column("unvalued_core_event_count").sum() or 0
        ),
    }

    return (
        summary.sort(["season", "league_id", "player_id"]),
        profile.sort(["season", "league_id", "player_id", "core_bin"]),
        values.sort(["season", "league_id", "core_bin"]),
        metrics,
    )
