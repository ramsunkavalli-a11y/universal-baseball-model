"""Reusable MiLB source helpers for historical Current Talent materialization.

These transformations are deliberately independent of season-level Performance
calibration. They turn resolved/authorized reusable contact evidence into the
same contact-profile taxonomy used by the frozen Performance layer and provide
strict actual-league coverage checks for an explicitly supplied era map.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from universal_baseball.contact_profile import classify_contact_profile_events


AUTHORIZED_CONTACT_REQUIRED = frozenset(
    {
        "game_date",
        "league_id",
        "game_pk",
        "at_bat_index",
        "pitch_number",
        "batter_mlbam_id",
        "participant_authority",
        "batter_side",
        "bb_type",
        "hc_x",
        "hc_y",
        "result_description",
    }
)


def validate_expected_actual_leagues(
    frame: pl.DataFrame,
    *,
    league_column: str,
    expected_league_ids: frozenset[int],
    label: str,
) -> dict[str, Any]:
    """Require exact non-null actual-league coverage for one historical slice."""

    if league_column not in frame.columns:
        raise ValueError(f"{label} missing actual-league column {league_column!r}")
    if not expected_league_ids:
        raise ValueError(f"{label} expected actual-league set cannot be empty")
    observed = {
        int(value)
        for value in frame.get_column(league_column).drop_nulls().cast(pl.Int64).unique().to_list()
    }
    expected = {int(value) for value in expected_league_ids}
    if observed != expected:
        raise ValueError(
            f"{label} actual-league coverage mismatch: "
            f"observed={sorted(observed)}, expected={sorted(expected)}"
        )
    return {
        "observed_league_ids": sorted(observed),
        "expected_league_ids": sorted(expected),
        "exact_actual_league_coverage": True,
    }


def classify_milb_current_talent_contacts(
    authorized_contacts: pl.DataFrame,
) -> pl.DataFrame:
    """Classify authorized historical physical contacts into frozen profile bins.

    No run values or season-end Performance totals are consulted. ``season`` is
    derived only from the retained event date, and source geometry/narrative is
    preserved as the contact-classification evidence.
    """

    missing = sorted(AUTHORIZED_CONTACT_REQUIRED - set(authorized_contacts.columns))
    if missing:
        raise ValueError(f"authorized MiLB contacts missing profile fields: {missing}")
    if authorized_contacts.is_empty():
        raise ValueError("authorized MiLB contacts cannot be empty")

    input_frame = (
        authorized_contacts.with_columns(
            pl.col("game_date").cast(pl.String).str.slice(0, 4).cast(pl.Int64, strict=False).alias("season"),
            pl.lit("source_certified_mirror").alias("result_description_authority"),
        )
        .select(
            "season",
            "league_id",
            "game_pk",
            "at_bat_index",
            "pitch_number",
            "batter_mlbam_id",
            "participant_authority",
            "result_description_authority",
            "batter_side",
            "bb_type",
            "hc_x",
            "hc_y",
            "result_description",
        )
    )
    if input_frame.filter(pl.col("season").is_null()).height:
        raise ValueError("authorized MiLB contacts contain unparseable event year")

    classified = classify_contact_profile_events(input_frame)
    if classified.height != authorized_contacts.height:
        raise ValueError(
            "MiLB Current Talent contact classification changed physical row count: "
            f"{classified.height} vs {authorized_contacts.height}"
        )
    return classified
