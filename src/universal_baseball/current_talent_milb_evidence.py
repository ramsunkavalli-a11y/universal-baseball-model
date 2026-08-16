"""Build affiliated player-game Performance evidence for Current Talent snapshots.

The adapter reuses two already-certified public layers:

- armstjc player-game boxscores for PA / BB / HBP / K / catcher interference;
- resolved + participant-authorized contact-profile events for the 10 contact bins.

It intentionally does not replay every official PA.  Conflicting cumulative
boxscore snapshots are resolved only by component-wise statistical dominance.
Actual-league and game-type disagreement is a hard blocker.  A game-date
conflict is retained as a flag and assigned the *latest* observed date so a
completed suspended/resumed game cannot leak later events backward across a
Current Talent cutoff.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import polars as pl

from universal_baseball.bin_value_policy import LEAGUE_LEVEL_GROUP
from universal_baseball.current_talent_evidence import (
    PLAYER_GAME_PROFILE_REQUIRED,
    PLAYER_GAME_SUMMARY_REQUIRED,
    validate_player_game_evidence,
)
from universal_baseball.performance_season import CONTACT_CORE_BINS


OUTCOME_FIELDS = (
    "batting_PA",
    "batting_AB",
    "batting_BB",
    "batting_HBP",
    "batting_SO",
    "batting_SF",
    "batting_SH",
    "batting_CI",
)
OUTCOME_KEY = ("game_id", "player_id")
BLOCKING_METADATA = ("game_type", "league_id")
OUTCOME_RESOLUTION_POLICY = "componentwise_cumulative_outcomes_latest_safe_date_v1"


def _int_expr(column: str, alias: str | None = None) -> pl.Expr:
    numeric = pl.col(column).cast(pl.Float64, strict=False)
    return (
        pl.when(numeric.is_not_null() & (numeric == numeric.floor()))
        .then(numeric.cast(pl.Int64, strict=False))
        .otherwise(None)
        .alias(alias or column)
    )


def project_milb_player_game_outcomes(
    frame: pl.DataFrame,
    *,
    source_asset: str,
    season: int | None = None,
    game_type: str | None = "R",
) -> pl.DataFrame:
    """Project raw published player-game rows to Current Talent outcome evidence."""

    required = {
        "game_id",
        "game_date",
        "game_type",
        "league_id",
        "player_id",
        *OUTCOME_FIELDS,
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{source_asset} missing player-game outcome fields: {missing}")

    projected = frame.select(
        _int_expr("game_id"),
        pl.col("game_date").cast(pl.String),
        pl.col("game_type").cast(pl.String),
        _int_expr("league_id"),
        _int_expr("player_id"),
        *[_int_expr(column) for column in OUTCOME_FIELDS],
        pl.lit(str(source_asset)).alias("source_asset"),
    ).drop_nulls(list(OUTCOME_KEY))

    if season is not None:
        projected = projected.filter(pl.col("game_date").str.starts_with(f"{int(season)}-"))
    if game_type is not None:
        projected = projected.filter(pl.col("game_type") == str(game_type))
    return projected


def _dominates(candidate: dict[str, Any], other: dict[str, Any]) -> bool:
    for field in OUTCOME_FIELDS:
        lower = other[field]
        upper = candidate[field]
        if lower is None:
            continue
        if upper is None or int(upper) < int(lower):
            return False
    return True


def resolve_milb_player_game_outcomes(
    observations: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, int]]:
    """Resolve overlapping cumulative boxscore snapshots without filename chronology."""

    required = {*OUTCOME_KEY, "game_date", *BLOCKING_METADATA, *OUTCOME_FIELDS, "source_asset"}
    missing = sorted(required - set(observations.columns))
    if missing:
        raise ValueError(f"player-game outcome observations missing fields: {missing}")
    if observations.is_empty():
        raise ValueError("player-game outcome observations cannot be empty")

    raw_rows = observations.height
    exact = observations.unique(maintain_order=True)
    logical = exact.select(
        *OUTCOME_KEY,
        "game_date",
        *BLOCKING_METADATA,
        *OUTCOME_FIELDS,
    ).unique(maintain_order=True)

    rows: list[dict[str, Any]] = []
    dominance_count = 0
    unresolved_count = 0
    date_conflict_count = 0
    blocking_conflict_count = 0

    for group in logical.partition_by(list(OUTCOME_KEY), maintain_order=True):
        values = group.to_dicts()
        first = values[0]
        game_id = int(first["game_id"])
        player_id = int(first["player_id"])

        blocking_values = {
            field: {row[field] for row in values if row[field] is not None}
            for field in BLOCKING_METADATA
        }
        if any(len(field_values) > 1 for field_values in blocking_values.values()):
            blocking_conflict_count += 1
            unresolved_count += 1
            rows.append(
                {
                    "game_id": game_id,
                    "player_id": player_id,
                    "game_date": None,
                    "game_date_conflict": False,
                    "game_type": None,
                    "league_id": None,
                    **{field: None for field in OUTCOME_FIELDS},
                    "source_asset_count": int(
                        exact.filter(
                            (pl.col("game_id") == game_id) & (pl.col("player_id") == player_id)
                        ).get_column("source_asset").n_unique()
                    ),
                    "outcome_resolution": "unresolved_blocking_metadata_conflict",
                }
            )
            continue

        dates = sorted(
            {
                parsed
                for raw in (row["game_date"] for row in values)
                if raw is not None
                for parsed in [pl.Series([str(raw)]).str.to_date(strict=False).item()]
                if parsed is not None
            }
        )
        date_conflict = len(dates) > 1
        if date_conflict:
            date_conflict_count += 1
        safe_date = dates[-1] if dates else None

        vectors: dict[tuple[Any, ...], dict[str, Any]] = {}
        for row in values:
            vector = tuple(row[field] for field in OUTCOME_FIELDS)
            vectors.setdefault(vector, row)
        candidates = list(vectors.values())

        if len(candidates) == 1:
            selected = candidates[0]
            resolution = "consensus"
        else:
            dominators = [
                candidate
                for candidate in candidates
                if all(_dominates(candidate, other) for other in candidates)
            ]
            if len(dominators) != 1:
                unresolved_count += 1
                rows.append(
                    {
                        "game_id": game_id,
                        "player_id": player_id,
                        "game_date": safe_date,
                        "game_date_conflict": date_conflict,
                        "game_type": next(iter(blocking_values["game_type"]), None),
                        "league_id": next(iter(blocking_values["league_id"]), None),
                        **{field: None for field in OUTCOME_FIELDS},
                        "source_asset_count": int(
                            exact.filter(
                                (pl.col("game_id") == game_id) & (pl.col("player_id") == player_id)
                            ).get_column("source_asset").n_unique()
                        ),
                        "outcome_resolution": "unresolved_nonmonotonic_conflict",
                    }
                )
                continue
            selected = dominators[0]
            dominance_count += 1
            resolution = "componentwise_dominance"

        rows.append(
            {
                "game_id": game_id,
                "player_id": player_id,
                "game_date": safe_date,
                "game_date_conflict": date_conflict,
                "game_type": next(iter(blocking_values["game_type"]), None),
                "league_id": next(iter(blocking_values["league_id"]), None),
                **{field: selected[field] for field in OUTCOME_FIELDS},
                "source_asset_count": int(
                    exact.filter(
                        (pl.col("game_id") == game_id) & (pl.col("player_id") == player_id)
                    ).get_column("source_asset").n_unique()
                ),
                "outcome_resolution": resolution,
            }
        )

    resolved = pl.DataFrame(rows).with_columns(
        pl.col("game_id").cast(pl.Int64),
        pl.col("player_id").cast(pl.Int64),
        pl.col("game_date").cast(pl.Date),
        pl.col("game_date_conflict").cast(pl.Boolean),
        pl.col("game_type").cast(pl.String),
        pl.col("league_id").cast(pl.Int64, strict=False),
        *[pl.col(field).cast(pl.Int64, strict=False) for field in OUTCOME_FIELDS],
        pl.col("source_asset_count").cast(pl.Int64),
        pl.col("outcome_resolution").cast(pl.String),
    ).sort(list(OUTCOME_KEY))

    return resolved, {
        "raw_observation_count": raw_rows,
        "exact_duplicate_row_count": raw_rows - exact.height,
        "resolved_player_game_count": resolved.height,
        "resolved_by_componentwise_dominance_count": dominance_count,
        "game_date_conflict_player_game_count": date_conflict_count,
        "blocking_metadata_conflict_player_game_count": blocking_conflict_count,
        "unresolved_player_game_count": unresolved_count,
    }


def build_milb_current_talent_player_game_evidence(
    resolved_outcomes: pl.DataFrame,
    contact_profile: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    """Combine resolved boxscore outcomes + classified contacts at player-game grain."""

    outcome_required = {
        "game_id",
        "player_id",
        "game_date",
        "game_type",
        "league_id",
        *OUTCOME_FIELDS,
        "outcome_resolution",
    }
    contact_required = {
        "season",
        "league_id",
        "game_pk",
        "batter_mlbam_id",
        "participant_authority",
        "core_bin",
        "contact_profile_status",
    }
    missing_outcome = sorted(outcome_required - set(resolved_outcomes.columns))
    missing_contact = sorted(contact_required - set(contact_profile.columns))
    if missing_outcome:
        raise ValueError(f"resolved outcomes missing Current Talent fields: {missing_outcome}")
    if missing_contact:
        raise ValueError(f"contact profile missing Current Talent fields: {missing_contact}")

    outcomes = resolved_outcomes.filter(
        (pl.col("game_type") == "R")
        & pl.col("batting_PA").is_not_null()
        & (pl.col("batting_PA") > 0)
    )
    unresolved = outcomes.filter(
        pl.col("outcome_resolution").str.starts_with("unresolved")
        | pl.any_horizontal([pl.col(field).is_null() for field in OUTCOME_FIELDS])
    )
    if not unresolved.is_empty():
        raise ValueError("Current Talent player-game outcomes contain unresolved evidence")

    contact_counts = contact_profile.group_by(
        ["season", "league_id", "game_pk", "batter_mlbam_id"]
    ).agg(
        pl.len().alias("contact_event_count"),
        pl.col("core_bin").is_not_null().sum().alias("core_contact_count"),
        (pl.col("contact_profile_status") == "special_bunt").sum().alias("bunt_contact_count"),
        (pl.col("contact_profile_status") == "foul_air_excluded").sum().alias("foul_air_excluded_count"),
        pl.col("contact_profile_status").str.starts_with("unknown").sum().alias("unknown_contact_count"),
        (pl.col("participant_authority") != "source_default").sum().alias("official_overlay_contact_count"),
    )

    outcome_base = outcomes.with_columns(
        pl.col("game_date").dt.year().cast(pl.Int64).alias("season"),
        pl.col("league_id")
        .replace_strict(
            {int(k): str(v) for k, v in LEAGUE_LEVEL_GROUP.items()},
            default=None,
            return_dtype=pl.String,
        )
        .alias("level_group"),
        (pl.col("batting_BB") + pl.col("batting_HBP")).alias("bb_hbp_count"),
        pl.col("batting_SO").alias("strikeout_count"),
    )
    unknown_leagues = outcome_base.filter(pl.col("level_group").is_null())
    if not unknown_leagues.is_empty():
        raise ValueError("Current Talent MiLB evidence contains uncertified league IDs")

    joined = outcome_base.join(
        contact_counts,
        left_on=["season", "league_id", "game_id", "player_id"],
        right_on=["season", "league_id", "game_pk", "batter_mlbam_id"],
        how="left",
    ).with_columns(
        *[
            pl.col(column).fill_null(0).cast(pl.Int64)
            for column in (
                "contact_event_count",
                "core_contact_count",
                "bunt_contact_count",
                "foul_air_excluded_count",
                "unknown_contact_count",
                "official_overlay_contact_count",
            )
        ]
    )

    joined = joined.with_columns(
        (pl.col("bb_hbp_count") + pl.col("strikeout_count") + pl.col("core_contact_count")).alias(
            "core_profile_event_count"
        ),
        (pl.col("bunt_contact_count") + pl.col("foul_air_excluded_count") + pl.col("batting_CI")).alias(
            "known_non_core_event_count"
        ),
    ).with_columns(
        (
            pl.col("batting_PA")
            - pl.col("core_profile_event_count")
            - pl.col("known_non_core_event_count")
        ).alias("unknown_event_count")
    )
    invalid = joined.filter(pl.col("unknown_event_count") < 0)
    if not invalid.is_empty():
        raise ValueError("Current Talent MiLB evidence over-accounts player-game plate appearances")

    summary = joined.select(
        pl.col("season").cast(pl.Int64),
        pl.col("game_date").cast(pl.Date),
        pl.col("game_id").cast(pl.Int64).alias("game_pk"),
        pl.col("league_id").cast(pl.Int64),
        pl.col("player_id").cast(pl.Int64),
        pl.col("level_group").cast(pl.String),
        pl.col("batting_PA").cast(pl.Int64).alias("batting_plate_appearances"),
        pl.col("core_profile_event_count").cast(pl.Int64),
        pl.col("known_non_core_event_count").cast(pl.Int64).alias("non_core_event_count"),
        pl.col("unknown_event_count").cast(pl.Int64),
        pl.when(pl.col("contact_event_count") == 0)
        .then(pl.lit("no_contact_identity_needed"))
        .when(pl.col("official_overlay_contact_count") == 0)
        .then(pl.lit("source_default"))
        .when(pl.col("official_overlay_contact_count") == pl.col("contact_event_count"))
        .then(pl.lit("official_overlay"))
        .otherwise(pl.lit("mixed_source_and_official"))
        .alias("participant_authority_status"),
        pl.lit("universal_result_contact_profile_v1").alias("source_capability_tier"),
    )

    contact_profile_long = contact_profile.filter(pl.col("core_bin").is_not_null()).group_by(
        ["season", "league_id", "game_pk", "batter_mlbam_id", "core_bin"]
    ).agg(pl.len().alias("occurrence_count")).rename({"batter_mlbam_id": "player_id"})

    outcome_profile = pl.concat(
        [
            outcome_base.filter(pl.col("bb_hbp_count") > 0).select(
                "season",
                pl.col("game_date").cast(pl.Date),
                pl.col("game_id").alias("game_pk"),
                "league_id",
                "player_id",
                "level_group",
                pl.lit("BB_HBP").alias("core_bin"),
                pl.col("bb_hbp_count").cast(pl.Int64).alias("occurrence_count"),
            ),
            outcome_base.filter(pl.col("strikeout_count") > 0).select(
                "season",
                pl.col("game_date").cast(pl.Date),
                pl.col("game_id").alias("game_pk"),
                "league_id",
                "player_id",
                "level_group",
                pl.lit("K").alias("core_bin"),
                pl.col("strikeout_count").cast(pl.Int64).alias("occurrence_count"),
            ),
        ],
        how="vertical_relaxed",
    )

    contact_profile_long = contact_profile_long.join(
        summary.select("season", "game_date", "game_pk", "league_id", "player_id", "level_group"),
        on=["season", "game_pk", "league_id", "player_id"],
        how="inner",
    ).select(
        "season",
        "game_date",
        "game_pk",
        "league_id",
        "player_id",
        "level_group",
        "core_bin",
        pl.col("occurrence_count").cast(pl.Int64),
    )

    profile = pl.concat([outcome_profile, contact_profile_long], how="vertical_relaxed").sort(
        ["game_pk", "player_id", "core_bin"]
    )
    contract = validate_player_game_evidence(summary, profile)
    metrics = {
        **contract,
        "boxscore_player_game_count": outcomes.height,
        "contact_event_count": int(joined.get_column("contact_event_count").sum() or 0),
        "official_overlay_contact_count": int(
            joined.get_column("official_overlay_contact_count").sum() or 0
        ),
        "game_date_conflict_player_game_count": int(
            outcomes.get_column("game_date_conflict").sum() or 0
        ) if "game_date_conflict" in outcomes.columns else 0,
        "resolution_policy": OUTCOME_RESOLUTION_POLICY,
        "game_date_conflict_policy": "use latest observed date to prevent backward leakage",
    }
    return summary.sort(list(PLAYER_GAME_SUMMARY_REQUIRED & set(summary.columns))), profile, metrics
