"""Production player-season Performance aggregation for the batting side.

This module is the first production bridge from the certified foundation into a
player-level output. It deliberately remains inside the *Performance* layer:
there is no age adjustment, talent shrinkage, projection, playing-time forecast,
or WAR conversion here.

The design keeps the certified evidence roles separate:

- season-player aggregates supply PA, BB/HBP, K, and broad contact totals;
- resolved reusable PBP supplies screened contact trajectory/direction bins;
- ADR 020 determines participant authority before contact rows enter here;
- league-season bin values use the level-specific policy in ``bin_value_policy``.

Outputs expose both counts/coverage and value-estimator provenance so later
Current Talent models do not confuse missing evidence with player skill.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from universal_baseball.bin_value_policy import (
    LEAGUE_LEVEL_GROUP,
    bin_value_policy_for_league,
)
from universal_baseball.bin_value_pooling import shrink_mean


OUTCOME_CORE_BINS = ("BB_HBP", "K")
CONTACT_CORE_BINS = (
    "IFFB",
    "PULL_OFFB",
    "CENTER_OFFB",
    "OPPO_OFFB",
    "PULL_LD",
    "CENTER_LD",
    "OPPO_LD",
    "PULL_GB",
    "CENTER_GB",
    "OPPO_GB",
)
ALL_CORE_BINS = OUTCOME_CORE_BINS + CONTACT_CORE_BINS

BIN_VALUE_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "league_id": pl.Int64,
    "level_group": pl.String,
    "core_bin": pl.String,
    "direct_occurrence_count": pl.Int64,
    "direct_mean_run_value": pl.Float64,
    "prior_mean_run_value": pl.Float64,
    "prior_source_occurrence_count": pl.Int64,
    "prior_environment_count": pl.Int64,
    "prior_strength": pl.Int64,
    "estimated_mean_run_value": pl.Float64,
    "estimator_method": pl.String,
    "estimator_certified": pl.Boolean,
}


def estimate_certified_bin_values(direct_values: pl.DataFrame) -> pl.DataFrame:
    """Apply the frozen level-specific policy to direct league-season bin means.

    ``direct_values`` must contain one observed row per
    ``season + league_id + core_bin`` with ``occurrence_count`` and
    ``mean_run_value``. For pooled policies, the prior is the occurrence-weighted
    same-bin mean from *other* leagues at the same affiliated level and season.
    No adjacent-level or adjacent-season fallback is allowed.

    If a pooled policy lacks same-level peer support, the direct estimate is
    retained for transparency but is explicitly marked uncertified.
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
        raise ValueError(f"direct bin values missing columns: {missing}")
    if direct_values.is_empty():
        return pl.DataFrame(schema=BIN_VALUE_SCHEMA)

    working = direct_values.select(
        pl.col("season").cast(pl.Int64, strict=False),
        pl.col("league_id").cast(pl.Int64, strict=False),
        pl.col("core_bin").cast(pl.String),
        pl.col("occurrence_count").cast(pl.Int64, strict=False),
        pl.col("mean_run_value").cast(pl.Float64, strict=False),
    ).drop_nulls(["season", "league_id", "core_bin", "occurrence_count", "mean_run_value"])

    invalid_bins = working.filter(~pl.col("core_bin").is_in(list(ALL_CORE_BINS)))
    if not invalid_bins.is_empty():
        raise ValueError("direct bin values contain bins outside the certified core taxonomy")
    nonpositive = working.filter(pl.col("occurrence_count") <= 0)
    if not nonpositive.is_empty():
        raise ValueError("direct bin occurrence_count must be positive")
    duplicates = (
        working.group_by(["season", "league_id", "core_bin"])
        .len()
        .filter(pl.col("len") > 1)
    )
    if not duplicates.is_empty():
        raise ValueError("direct bin values contain duplicate league-season-bin keys")

    rows = working.to_dicts()
    result_rows: list[dict[str, Any]] = []
    for row in rows:
        season = int(row["season"])
        league_id = int(row["league_id"])
        core_bin = str(row["core_bin"])
        direct_count = int(row["occurrence_count"])
        direct_mean = float(row["mean_run_value"])
        policy = bin_value_policy_for_league(league_id)

        if policy.uses_pooling:
            peers = [
                peer
                for peer in rows
                if int(peer["season"]) == season
                and int(peer["league_id"]) != league_id
                and str(peer["core_bin"]) == core_bin
                and LEAGUE_LEVEL_GROUP.get(int(peer["league_id"])) == policy.level_group
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
                    policy.prior_strength,
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
        else:
            prior_source_n = 0
            prior_mean = None
            estimated = direct_mean
            prior_environment_count = 0
            if policy.status == "certified_direct":
                method = "certified_direct"
                certified = True
            else:
                method = "direct_uncertified_league_policy"
                certified = False

        result_rows.append(
            {
                "season": season,
                "league_id": league_id,
                "level_group": policy.level_group,
                "core_bin": core_bin,
                "direct_occurrence_count": direct_count,
                "direct_mean_run_value": direct_mean,
                "prior_mean_run_value": prior_mean,
                "prior_source_occurrence_count": prior_source_n,
                "prior_environment_count": prior_environment_count,
                "prior_strength": int(policy.prior_strength),
                "estimated_mean_run_value": estimated,
                "estimator_method": method,
                "estimator_certified": certified,
            }
        )

    return (
        pl.DataFrame(result_rows, schema=BIN_VALUE_SCHEMA)
        .sort(["season", "league_id", "core_bin"])
    )


def aggregate_batting_outcomes(season_batting: pl.DataFrame) -> pl.DataFrame:
    """Collapse standardized team rows to player × actual league × season outcomes."""

    required = {
        "season",
        "league_id",
        "player_id",
        "batting_plate_appearances",
        "batting_base_on_balls",
        "batting_hit_by_pitch",
        "batting_strike_outs",
        "batting_balls_in_play",
    }
    missing = sorted(required - set(season_batting.columns))
    if missing:
        raise ValueError(f"standardized batting outcomes missing columns: {missing}")

    numeric = sorted(required - {"season", "league_id", "player_id"})
    working = season_batting.select(
        pl.col("season").cast(pl.Int64, strict=False),
        pl.col("league_id").cast(pl.Int64, strict=False),
        pl.col("player_id").cast(pl.Int64, strict=False),
        *[pl.col(column).cast(pl.Int64, strict=False) for column in numeric],
    ).drop_nulls(["season", "league_id", "player_id"])

    # A partially null team row is not silently converted to zero. The upstream
    # standardized aggregate layer is expected to provide complete certified
    # counting fields for these columns.
    incomplete = working.filter(pl.any_horizontal([pl.col(column).is_null() for column in numeric]))
    if not incomplete.is_empty():
        raise ValueError("batting outcome backbone contains null required counting fields")

    result = (
        working.group_by(["season", "league_id", "player_id"])
        .agg(*[pl.col(column).sum().alias(column) for column in numeric])
        .with_columns(
            (
                pl.col("batting_base_on_balls") + pl.col("batting_hit_by_pitch")
            ).alias("bb_hbp_count"),
            pl.col("batting_strike_outs").alias("strikeout_count"),
            pl.col("batting_balls_in_play").alias("aggregate_contact_count"),
        )
        .with_columns(
            (
                pl.col("batting_plate_appearances")
                - pl.col("bb_hbp_count")
                - pl.col("strikeout_count")
                - pl.col("aggregate_contact_count")
            ).alias("aggregate_noncontact_noncore_pa_count")
        )
        .sort(["season", "league_id", "player_id"])
    )
    return result


def _aggregate_contact_summary(contact_events: pl.DataFrame) -> pl.DataFrame:
    required = {
        "season",
        "league_id",
        "batter_mlbam_id",
        "participant_authority",
        "result_description_authority",
        "core_bin",
        "core_profile_eligible",
        "contact_profile_status",
    }
    missing = sorted(required - set(contact_events.columns))
    if missing:
        raise ValueError(f"classified contact events missing columns: {missing}")
    if contact_events.is_empty():
        return pl.DataFrame(
            schema={
                "season": pl.Int64,
                "league_id": pl.Int64,
                "player_id": pl.Int64,
                "contact_event_count": pl.Int64,
                "core_contact_count": pl.Int64,
                "bunt_contact_count": pl.Int64,
                "foul_air_excluded_count": pl.Int64,
                "unknown_contact_count": pl.Int64,
                "source_default_contact_count": pl.Int64,
                "official_overlay_contact_count": pl.Int64,
                "other_participant_authority_contact_count": pl.Int64,
                "source_mirror_narrative_contact_count": pl.Int64,
            }
        )

    known_noncore = {"special_bunt", "foul_air_excluded"}
    return (
        contact_events.with_columns(
            pl.col("season").cast(pl.Int64, strict=False),
            pl.col("league_id").cast(pl.Int64, strict=False),
            pl.col("batter_mlbam_id").cast(pl.Int64, strict=False).alias("player_id"),
        )
        .drop_nulls(["season", "league_id", "player_id"])
        .group_by(["season", "league_id", "player_id"])
        .agg(
            pl.len().alias("contact_event_count"),
            pl.col("core_profile_eligible").cast(pl.Int64).sum().alias("core_contact_count"),
            (pl.col("contact_profile_status") == "special_bunt").cast(pl.Int64).sum().alias("bunt_contact_count"),
            (pl.col("contact_profile_status") == "foul_air_excluded").cast(pl.Int64).sum().alias("foul_air_excluded_count"),
            (
                ~pl.col("contact_profile_status").is_in(["core_contact", *sorted(known_noncore)])
            ).cast(pl.Int64).sum().alias("unknown_contact_count"),
            (pl.col("participant_authority") == "source_default").cast(pl.Int64).sum().alias("source_default_contact_count"),
            (pl.col("participant_authority") == "official_exception_overlay").cast(pl.Int64).sum().alias("official_overlay_contact_count"),
            (~pl.col("participant_authority").is_in(["source_default", "official_exception_overlay"])).cast(pl.Int64).sum().alias("other_participant_authority_contact_count"),
            (pl.col("result_description_authority") == "source_certified_mirror").cast(pl.Int64).sum().alias("source_mirror_narrative_contact_count"),
        )
        .sort(["season", "league_id", "player_id"])
    )


def _player_core_bin_counts(
    outcomes: pl.DataFrame,
    contact_events: pl.DataFrame,
) -> pl.DataFrame:
    bb = outcomes.select(
        "season",
        "league_id",
        "player_id",
        pl.lit("BB_HBP").alias("core_bin"),
        pl.col("bb_hbp_count").alias("occurrence_count"),
    )
    strikeouts = outcomes.select(
        "season",
        "league_id",
        "player_id",
        pl.lit("K").alias("core_bin"),
        pl.col("strikeout_count").alias("occurrence_count"),
    )
    if contact_events.is_empty():
        contacts = pl.DataFrame(
            schema={
                "season": pl.Int64,
                "league_id": pl.Int64,
                "player_id": pl.Int64,
                "core_bin": pl.String,
                "occurrence_count": pl.Int64,
            }
        )
    else:
        contacts = (
            contact_events.filter(pl.col("core_bin").is_not_null())
            .with_columns(
                pl.col("batter_mlbam_id").cast(pl.Int64, strict=False).alias("player_id")
            )
            .drop_nulls(["season", "league_id", "player_id", "core_bin"])
            .group_by(["season", "league_id", "player_id", "core_bin"])
            .len(name="occurrence_count")
        )
    return (
        pl.concat([bb, strikeouts, contacts], how="vertical_relaxed")
        .filter(pl.col("occurrence_count") > 0)
        .sort(["season", "league_id", "player_id", "core_bin"])
    )


def build_batting_performance_season(
    season_batting: pl.DataFrame,
    contact_events: pl.DataFrame,
    bin_values: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Return batting Performance summary and long-form player-bin profile.

    ``season_batting`` is the standardized certified aggregate backbone.
    ``contact_events`` is the output of ``classify_contact_profile_events`` after
    participant authority has already been resolved. ``bin_values`` is the
    output of ``estimate_certified_bin_values``.
    """

    outcomes = aggregate_batting_outcomes(season_batting)
    contact_summary = _aggregate_contact_summary(contact_events)

    if not contact_events.is_empty():
        contact_keys = contact_events.select(
            pl.col("season").cast(pl.Int64),
            pl.col("league_id").cast(pl.Int64),
            pl.col("batter_mlbam_id").cast(pl.Int64).alias("player_id"),
        ).unique()
        outcome_keys = outcomes.select("season", "league_id", "player_id")
        orphan = contact_keys.join(
            outcome_keys,
            on=["season", "league_id", "player_id"],
            how="anti",
        )
        if not orphan.is_empty():
            raise ValueError("classified contacts contain player-league-season keys absent from aggregate backbone")

    summary = outcomes.join(
        contact_summary,
        on=["season", "league_id", "player_id"],
        how="left",
    )
    contact_count_columns = [
        "contact_event_count",
        "core_contact_count",
        "bunt_contact_count",
        "foul_air_excluded_count",
        "unknown_contact_count",
        "source_default_contact_count",
        "official_overlay_contact_count",
        "other_participant_authority_contact_count",
        "source_mirror_narrative_contact_count",
    ]
    summary = summary.with_columns(
        *[pl.col(column).fill_null(0).cast(pl.Int64) for column in contact_count_columns]
    ).with_columns(
        (
            pl.col("contact_event_count") - pl.col("aggregate_contact_count")
        ).alias("contact_count_residual_vs_aggregate"),
        (
            pl.col("bb_hbp_count")
            + pl.col("strikeout_count")
            + pl.col("core_contact_count")
        ).alias("core_profile_event_count"),
    ).with_columns(
        (
            pl.col("batting_plate_appearances") - pl.col("core_profile_event_count")
        ).alias("core_profile_uncovered_pa_count"),
        pl.when(pl.col("batting_plate_appearances") > 0)
        .then(pl.col("core_profile_event_count") / pl.col("batting_plate_appearances"))
        .otherwise(None)
        .alias("core_profile_coverage_rate"),
        pl.when(pl.col("aggregate_contact_count") > 0)
        .then(pl.col("contact_event_count") / pl.col("aggregate_contact_count"))
        .otherwise(None)
        .alias("contact_count_coverage_vs_aggregate"),
        pl.when(pl.col("contact_event_count") > 0)
        .then(pl.col("core_contact_count") / pl.col("contact_event_count"))
        .otherwise(None)
        .alias("core_contact_share"),
        pl.when(pl.col("contact_event_count") > 0)
        .then(pl.col("official_overlay_contact_count") / pl.col("contact_event_count"))
        .otherwise(None)
        .alias("official_overlay_contact_rate"),
    )

    bin_counts = _player_core_bin_counts(outcomes, contact_events)
    duplicate_values = (
        bin_values.group_by(["season", "league_id", "core_bin"])
        .len()
        .filter(pl.col("len") > 1)
    )
    if not duplicate_values.is_empty():
        raise ValueError("bin_values contain duplicate league-season-bin keys")

    profile = (
        bin_counts.join(
            bin_values,
            on=["season", "league_id", "core_bin"],
            how="left",
        )
        .join(
            outcomes.select("season", "league_id", "player_id", "batting_plate_appearances"),
            on=["season", "league_id", "player_id"],
            how="left",
        )
        .with_columns(
            pl.when(pl.col("batting_plate_appearances") > 0)
            .then(pl.col("occurrence_count") / pl.col("batting_plate_appearances"))
            .otherwise(None)
            .alias("share_of_plate_appearances"),
            (pl.col("occurrence_count") * pl.col("estimated_mean_run_value")).alias(
                "expected_run_value"
            ),
        )
        .sort(["season", "league_id", "player_id", "core_bin"])
    )

    value_summary = (
        profile.group_by(["season", "league_id", "player_id"])
        .agg(
            pl.col("occurrence_count")
            .filter(pl.col("estimated_mean_run_value").is_not_null())
            .sum()
            .fill_null(0)
            .cast(pl.Int64)
            .alias("valued_core_event_count"),
            pl.col("expected_run_value").sum().alias("core_expected_run_value_total"),
            (~pl.col("estimator_certified").fill_null(False))
            .any()
            .alias("has_uncertified_or_missing_bin_value"),
        )
    )
    summary = (
        summary.join(
            value_summary,
            on=["season", "league_id", "player_id"],
            how="left",
        )
        .with_columns(
            pl.col("valued_core_event_count").fill_null(0).cast(pl.Int64),
            pl.col("core_expected_run_value_total").fill_null(0.0),
            pl.col("has_uncertified_or_missing_bin_value").fill_null(
                pl.col("core_profile_event_count") > 0
            ),
        )
        .with_columns(
            (
                pl.col("core_profile_event_count") - pl.col("valued_core_event_count")
            ).alias("unvalued_core_event_count"),
            pl.when(pl.col("batting_plate_appearances") > 0)
            .then(
                100.0
                * pl.col("core_expected_run_value_total")
                / pl.col("batting_plate_appearances")
            )
            .otherwise(None)
            .alias("core_expected_run_value_per_100_pa"),
            pl.when(pl.col("valued_core_event_count") > 0)
            .then(
                pl.col("core_expected_run_value_total")
                / pl.col("valued_core_event_count")
            )
            .otherwise(None)
            .alias("mean_valued_core_bin_run_value"),
            (pl.col("core_profile_event_count") > pl.col("batting_plate_appearances")).alias(
                "core_profile_count_exceeds_pa"
            ),
        )
        .sort(["season", "league_id", "player_id"])
    )
    return summary, profile
