"""Certified MLB Performance-bin value policy.

MLB uses the same contextual RE24 definition and frozen 12-bin Performance
taxonomy as affiliated MiLB, but its environment estimator is certified
separately.  The 2024 primary AL/NL held-out audit nominated a modest same-bin
peer-league prior of five equivalent occurrences; that exact strength improved
or tied every pre-specified split-half and five-fold metric in an independent
2023 confirmation.

This module deliberately does not modify the affiliated ``LEAGUE_LEVEL_GROUP``
map.  MLB is a reporting anchor, not an affiliated level, and the already-frozen
MiLB materialization should not change its expected league coverage simply
because MLB is added to the universal Performance surface.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from universal_baseball.bin_value_pooling import shrink_mean
from universal_baseball.performance_season import ALL_CORE_BINS, BIN_VALUE_SCHEMA


MLB_LEAGUE_IDS = frozenset({103, 104})
MLB_LEVEL_GROUP = "MLB"
MLB_PRIOR_STRENGTH = 5
MLB_POLICY_EVIDENCE = (
    "2024 AL/NL split-half + five-fold primary audit nominated lambda=5; "
    "pre-specified independent 2023 confirmation improved or tied every "
    "primary metric"
)


def estimate_certified_mlb_bin_values(direct_values: pl.DataFrame) -> pl.DataFrame:
    """Apply the frozen AL<->NL same-bin pooling policy.

    ``direct_values`` contains one row per ``season + league_id + core_bin``
    with ``occurrence_count`` and ``mean_run_value``.  Each AL/NL estimate is
    shrunk toward the corresponding bin in the other MLB league by exactly five
    prior-equivalent occurrences.  There is no adjacent-season or MiLB fallback.

    If the peer league/bin is absent, the direct estimate is retained for
    transparency but explicitly marked uncertified.
    """

    required = {
        "season",
        "league_id",
        "core_bin",
        "occurrence_count",
        "mean_run_value",
    }
    missing = sorted(required - set(direct_values.columns))
    if missing:
        raise ValueError(f"MLB direct bin values missing columns: {missing}")
    if direct_values.is_empty():
        return pl.DataFrame(schema=BIN_VALUE_SCHEMA)

    working = direct_values.select(
        pl.col("season").cast(pl.Int64, strict=False),
        pl.col("league_id").cast(pl.Int64, strict=False),
        pl.col("core_bin").cast(pl.String),
        pl.col("occurrence_count").cast(pl.Int64, strict=False),
        pl.col("mean_run_value").cast(pl.Float64, strict=False),
    ).drop_nulls(["season", "league_id", "core_bin", "occurrence_count", "mean_run_value"])

    unknown_leagues = sorted(
        int(value)
        for value in working.get_column("league_id").unique().to_list()
        if int(value) not in MLB_LEAGUE_IDS
    )
    if unknown_leagues:
        raise ValueError(f"MLB bin values contain non-MLB league IDs: {unknown_leagues}")
    invalid_bins = working.filter(~pl.col("core_bin").is_in(list(ALL_CORE_BINS)))
    if not invalid_bins.is_empty():
        raise ValueError("MLB direct bin values contain bins outside the certified core taxonomy")
    nonpositive = working.filter(pl.col("occurrence_count") <= 0)
    if not nonpositive.is_empty():
        raise ValueError("MLB direct bin occurrence_count must be positive")
    duplicates = (
        working.group_by(["season", "league_id", "core_bin"])
        .len()
        .filter(pl.col("len") > 1)
    )
    if not duplicates.is_empty():
        raise ValueError("MLB direct bin values contain duplicate league-season-bin keys")

    rows = working.to_dicts()
    result_rows: list[dict[str, Any]] = []
    for row in rows:
        season = int(row["season"])
        league_id = int(row["league_id"])
        core_bin = str(row["core_bin"])
        direct_count = int(row["occurrence_count"])
        direct_mean = float(row["mean_run_value"])
        peers = [
            peer
            for peer in rows
            if int(peer["season"]) == season
            and int(peer["league_id"]) != league_id
            and int(peer["league_id"]) in MLB_LEAGUE_IDS
            and str(peer["core_bin"]) == core_bin
            and int(peer["occurrence_count"]) > 0
        ]

        if peers:
            prior_source_n = sum(int(peer["occurrence_count"]) for peer in peers)
            prior_mean = sum(
                float(peer["mean_run_value"]) * int(peer["occurrence_count"])
                for peer in peers
            ) / prior_source_n
            estimated = shrink_mean(
                direct_mean,
                direct_count,
                prior_mean,
                MLB_PRIOR_STRENGTH,
            )
            method = "certified_same_level_peer_pooling"
            certified = True
            prior_environment_count = len({int(peer["league_id"]) for peer in peers})
        else:
            prior_source_n = 0
            prior_mean = None
            estimated = direct_mean
            method = "direct_missing_required_peer_support"
            certified = False
            prior_environment_count = 0

        result_rows.append(
            {
                "season": season,
                "league_id": league_id,
                "level_group": MLB_LEVEL_GROUP,
                "core_bin": core_bin,
                "direct_occurrence_count": direct_count,
                "direct_mean_run_value": direct_mean,
                "prior_mean_run_value": prior_mean,
                "prior_source_occurrence_count": prior_source_n,
                "prior_environment_count": prior_environment_count,
                "prior_strength": MLB_PRIOR_STRENGTH,
                "estimated_mean_run_value": estimated,
                "estimator_method": method,
                "estimator_certified": certified,
            }
        )

    return (
        pl.DataFrame(result_rows, schema=BIN_VALUE_SCHEMA)
        .sort(["season", "league_id", "core_bin"])
    )
