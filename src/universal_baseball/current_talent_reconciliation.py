"""Reconcile game-grain Current Talent evidence to frozen season Performance.

The Current Talent evidence layer must be a chronology-safe decomposition of the
same observed Performance facts, not a second statistic. This module rolls
player-game evidence back to player x actual-league x season grain and requires
exact equality with the frozen Performance contract for:

- batting plate appearances;
- total 12-bin core-profile event count;
- every individual core-bin occurrence count; and
- source-derived contact/accounting fields whenever the frozen Performance
  summary exposes their corresponding season totals.

Run values are deliberately not compared here. Current Talent consumes evidence
counts; Performance owns contextual value calibration.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from universal_baseball.current_talent_evidence import validate_player_game_evidence
from universal_baseball.performance_season import ALL_CORE_BINS


SEASON_KEY = ("season", "league_id", "player_id")
PROFILE_KEY = (*SEASON_KEY, "core_bin")

# Game-evidence field -> frozen Performance summary field. These are compared
# only when the Performance artifact actually exposes the right-hand field.
OPTIONAL_SUMMARY_RECONCILIATION_FIELDS: tuple[tuple[str, str], ...] = (
    ("expected_contact_count", "aggregate_contact_count"),
    ("observed_contact_count", "contact_event_count"),
    ("contact_count_residual", "contact_count_residual_vs_aggregate"),
    ("bunt_contact_count", "bunt_contact_count"),
    ("foul_air_excluded_count", "foul_air_excluded_count"),
    ("unknown_contact_count", "unknown_contact_count"),
)


def reconcile_player_game_to_performance(
    game_summary: pl.DataFrame,
    game_profile: pl.DataFrame,
    performance_summary: pl.DataFrame,
    performance_profile: pl.DataFrame,
    *,
    require_exact: bool = True,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    """Return season comparisons and optionally fail on any evidence mismatch.

    ``require_exact=False`` is intended only for diagnostic materialization so a
    failed live gate can persist the exact mismatch rows before the caller raises.
    Production acceptance should retain the default exact requirement.
    """

    validate_player_game_evidence(game_summary, game_profile)

    required_summary = {*SEASON_KEY, "batting_plate_appearances", "core_profile_event_count"}
    required_profile = {*PROFILE_KEY, "occurrence_count"}
    missing_summary = sorted(required_summary - set(performance_summary.columns))
    missing_profile = sorted(required_profile - set(performance_profile.columns))
    if missing_summary:
        raise ValueError(f"Performance summary missing reconciliation fields: {missing_summary}")
    if missing_profile:
        raise ValueError(f"Performance profile missing reconciliation fields: {missing_profile}")

    perf_summary_dupes = (
        performance_summary.group_by(list(SEASON_KEY)).len().filter(pl.col("len") > 1)
    )
    perf_profile_dupes = (
        performance_profile.group_by(list(PROFILE_KEY)).len().filter(pl.col("len") > 1)
    )
    if not perf_summary_dupes.is_empty() or not perf_profile_dupes.is_empty():
        raise ValueError("Performance reconciliation input violates canonical season grain")

    optional_fields = [
        (game_field, performance_field)
        for game_field, performance_field in OPTIONAL_SUMMARY_RECONCILIATION_FIELDS
        if game_field in game_summary.columns and performance_field in performance_summary.columns
    ]

    game_rollup = (
        game_summary.group_by(list(SEASON_KEY))
        .agg(
            pl.col("batting_plate_appearances").sum().cast(pl.Int64).alias("game_pa"),
            pl.col("core_profile_event_count").sum().cast(pl.Int64).alias("game_core_events"),
            *[
                pl.col(game_field)
                .sum()
                .cast(pl.Int64)
                .alias(f"game_{performance_field}")
                for game_field, performance_field in optional_fields
            ],
        )
        .sort(list(SEASON_KEY))
    )
    perf_rollup = performance_summary.select(
        *SEASON_KEY,
        pl.col("batting_plate_appearances").cast(pl.Int64).alias("performance_pa"),
        pl.col("core_profile_event_count").cast(pl.Int64).alias("performance_core_events"),
        *[
            pl.col(performance_field)
            .cast(pl.Int64)
            .alias(f"performance_{performance_field}")
            for _, performance_field in optional_fields
        ],
    )

    fill_columns = [
        "game_pa",
        "game_core_events",
        "performance_pa",
        "performance_core_events",
        *[f"game_{performance_field}" for _, performance_field in optional_fields],
        *[f"performance_{performance_field}" for _, performance_field in optional_fields],
    ]
    difference_columns = [
        "pa_difference",
        "core_event_difference",
        *[f"{performance_field}_difference" for _, performance_field in optional_fields],
    ]
    summary_comparison = (
        game_rollup.join(perf_rollup, on=list(SEASON_KEY), how="full", coalesce=True)
        .with_columns(*[pl.col(column).fill_null(0).cast(pl.Int64) for column in fill_columns])
        .with_columns(
            (pl.col("game_pa") - pl.col("performance_pa")).alias("pa_difference"),
            (pl.col("game_core_events") - pl.col("performance_core_events")).alias(
                "core_event_difference"
            ),
            *[
                (
                    pl.col(f"game_{performance_field}")
                    - pl.col(f"performance_{performance_field}")
                ).alias(f"{performance_field}_difference")
                for _, performance_field in optional_fields
            ],
        )
        .with_columns(
            pl.any_horizontal([pl.col(column) != 0 for column in difference_columns]).alias(
                "has_any_mismatch"
            )
        )
        .sort(list(SEASON_KEY))
    )

    game_bins = (
        game_profile.group_by(list(PROFILE_KEY))
        .agg(pl.col("occurrence_count").sum().cast(pl.Int64).alias("game_occurrence_count"))
    )
    perf_bins = performance_profile.select(
        *PROFILE_KEY,
        pl.col("occurrence_count").cast(pl.Int64).alias("performance_occurrence_count"),
    )
    bin_comparison = (
        game_bins.join(perf_bins, on=list(PROFILE_KEY), how="full", coalesce=True)
        .with_columns(
            pl.col("game_occurrence_count").fill_null(0),
            pl.col("performance_occurrence_count").fill_null(0),
        )
        .with_columns(
            (pl.col("game_occurrence_count") - pl.col("performance_occurrence_count")).alias(
                "occurrence_difference"
            )
        )
        .sort(list(PROFILE_KEY))
    )

    invalid_bins = bin_comparison.filter(~pl.col("core_bin").is_in(list(ALL_CORE_BINS)))
    if not invalid_bins.is_empty():
        raise ValueError("reconciliation encountered bins outside the frozen 12-bin taxonomy")

    summary_mismatch = summary_comparison.filter(pl.col("has_any_mismatch"))
    bin_mismatch = bin_comparison.filter(pl.col("occurrence_difference") != 0)
    field_mismatch_counts = {
        column.removesuffix("_difference"): summary_comparison.filter(pl.col(column) != 0).height
        for column in difference_columns
    }

    metrics: dict[str, Any] = {
        "player_league_season_row_count": summary_comparison.height,
        "summary_mismatch_row_count": summary_mismatch.height,
        "summary_fields_compared": [
            "batting_plate_appearances",
            "core_profile_event_count",
            *[performance_field for _, performance_field in optional_fields],
        ],
        "summary_field_mismatch_counts": field_mismatch_counts,
        "profile_bin_row_count": bin_comparison.height,
        "profile_bin_mismatch_row_count": bin_mismatch.height,
        "game_plate_appearances": int(summary_comparison.get_column("game_pa").sum() or 0),
        "performance_plate_appearances": int(
            summary_comparison.get_column("performance_pa").sum() or 0
        ),
        "game_core_events": int(summary_comparison.get_column("game_core_events").sum() or 0),
        "performance_core_events": int(
            summary_comparison.get_column("performance_core_events").sum() or 0
        ),
        "exact_reconciliation": summary_mismatch.is_empty() and bin_mismatch.is_empty(),
    }
    if require_exact and not metrics["exact_reconciliation"]:
        raise ValueError(
            "player-game Current Talent evidence does not exactly reconcile to frozen Performance: "
            f"summary_mismatches={summary_mismatch.height}, bin_mismatches={bin_mismatch.height}"
        )
    return summary_comparison, bin_comparison, metrics
