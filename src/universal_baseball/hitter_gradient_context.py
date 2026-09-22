"""Chronology-safe event context for gradient hitter challengers.

This module only assembles observed context and labels.  It does not estimate a
park factor, neutralize a player, fit a forecast, or inspect a protected season.
Keeping that boundary explicit prevents a good park measurement from being
confused with (or selected by) a noisy next-season WAR result.
"""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from universal_baseball.hitter_v2_outcomes import TERMINAL_OUTCOMES


EVENT_KEY = ("season", "game_pk", "at_bat_index")
CONTACT_OUTCOMES = frozenset(
    {
        "HR",
        "3B",
        "2B",
        "1B",
        "ROE",
        "FC_REACH",
        "SF",
        "MULTI_OUT",
        "OTHER_OUT",
    }
)
NONCONTACT_OUTCOMES = frozenset(set(TERMINAL_OUTCOMES) - CONTACT_OUTCOMES)
PROTECTED_SEASON = 2026


@dataclass(frozen=True, slots=True)
class ChronologicalContextSplit:
    """Development rows strictly before, and evaluation rows within, one season."""

    training: pl.DataFrame
    evaluation: pl.DataFrame
    evaluation_season: int


def _require(frame: pl.DataFrame, fields: set[str], label: str) -> None:
    missing = sorted(fields - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing fields: {missing}")


def _assert_unique(frame: pl.DataFrame, key: list[str], label: str) -> None:
    duplicate = frame.group_by(key).len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError(f"{label} is not unique at {'/'.join(key)} grain")


def build_hitter_gradient_context_events(
    labeled_pas: pl.DataFrame,
    venue_context: pl.DataFrame,
    terminal_contacts: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Build the target/context table used before any gradient-model fitting.

    ``terminal_contacts`` must contain at most one result-producing contact per
    PA.  It must not be the all-pitches contact table, which can contain foul
    contacts before a strikeout or walk.
    """

    pa_required = {
        *EVENT_KEY,
        "game_date",
        "league_id",
        "level_group",
        "player_id",
        "pitcher_id",
        "batter_side",
        "pitcher_hand",
        "canonical_outcome",
        "context_label_ready",
    }
    venue_required = {
        "season",
        "game_id",
        "venue_id",
        "away_team_id",
        "home_team_id",
        "venue_context_eligible",
    }
    _require(labeled_pas, pa_required, "labeled PA context")
    _require(venue_context, venue_required, "venue context")
    _assert_unique(labeled_pas, list(EVENT_KEY), "labeled PA context")
    _assert_unique(venue_context, ["season", "game_id"], "venue context")

    unsupported = sorted(
        set(labeled_pas["canonical_outcome"].drop_nulls().unique().to_list())
        - set(TERMINAL_OUTCOMES)
    )
    if unsupported:
        raise ValueError(f"unsupported terminal outcomes: {unsupported}")

    events = labeled_pas.join(
        venue_context.select(*venue_required),
        left_on=["season", "game_pk"],
        right_on=["season", "game_id"],
        how="left",
        validate="m:1",
    )

    if terminal_contacts is None:
        events = events.with_columns(
            pl.lit(None, dtype=pl.String).alias("contact_bin"),
            pl.lit(False).alias("core_profile_eligible"),
        )
    else:
        contact_required = {*EVENT_KEY, "contact_bin", "core_profile_eligible"}
        _require(terminal_contacts, contact_required, "terminal contact context")
        _assert_unique(
            terminal_contacts, list(EVENT_KEY), "terminal contact context"
        )
        contacts = terminal_contacts.select(*contact_required)
        invalid = contacts.join(
            labeled_pas.select(*EVENT_KEY, "canonical_outcome"),
            on=list(EVENT_KEY),
            how="left",
            validate="1:1",
        ).filter(
            pl.col("canonical_outcome").is_null()
            | ~pl.col("canonical_outcome").is_in(sorted(CONTACT_OUTCOMES))
        )
        if not invalid.is_empty():
            raise ValueError(
                "terminal contact context includes a non-contact or unmatched PA"
            )
        events = events.join(
            contacts, on=list(EVENT_KEY), how="left", validate="1:1"
        ).with_columns(pl.col("core_profile_eligible").fill_null(False))

    valid_hands = pl.col("batter_side").is_in(["L", "R"]) & pl.col(
        "pitcher_hand"
    ).is_in(["L", "R"])
    venue_ready = (
        pl.col("venue_context_eligible").fill_null(False)
        & pl.col("venue_id").is_not_null()
    )
    contact_outcome = pl.col("canonical_outcome").is_in(sorted(CONTACT_OUTCOMES))
    contact_ready = (
        pl.col("context_label_ready")
        & venue_ready
        & valid_hands
        & contact_outcome
        & pl.col("core_profile_eligible")
        & pl.col("contact_bin").is_not_null()
    )
    return (
        events.with_columns(
            (
                pl.col("context_label_ready") & venue_ready & valid_hands
            ).alias("pa_context_ready"),
            contact_outcome.alias("is_contact_outcome"),
            contact_ready.alias("contact_context_ready"),
            pl.concat_str(
                [pl.col("venue_id"), pl.col("batter_side")], separator=":"
            ).alias("park_batter_side_cell"),
            pl.concat_str(
                [pl.col("batter_side"), pl.col("pitcher_hand")], separator=":"
            ).alias("platoon_cell"),
            pl.when(contact_ready)
            .then(
                pl.concat_str(
                    [pl.col("contact_bin"), pl.col("canonical_outcome")],
                    separator=":",
                )
            )
            .otherwise(pl.lit(None, dtype=pl.String))
            .alias("observed_contact_result_cell"),
        )
        .sort(list(EVENT_KEY))
    )


def chronological_context_split(
    events: pl.DataFrame,
    *,
    evaluation_season: int,
    protected_season: int = PROTECTED_SEASON,
) -> ChronologicalContextSplit:
    """Create a strict past-to-future development split and seal 2026 by default."""

    _require(events, {"season", *EVENT_KEY}, "gradient context events")
    if evaluation_season >= protected_season:
        raise ValueError(
            f"evaluation season {evaluation_season} is protected; "
            f"must be earlier than {protected_season}"
        )
    if events.filter(pl.col("season") >= protected_season).height:
        raise ValueError(
            f"context input contains protected season {protected_season} or later"
        )
    training = events.filter(pl.col("season") < evaluation_season)
    evaluation = events.filter(pl.col("season") == evaluation_season)
    if training.is_empty() or evaluation.is_empty():
        raise ValueError("chronological split requires nonempty training and evaluation")
    return ChronologicalContextSplit(
        training=training,
        evaluation=evaluation,
        evaluation_season=int(evaluation_season),
    )
