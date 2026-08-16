"""Production assembly helpers for MLB batting Performance.

MLB uses the same stable player-season Performance contract as affiliated MiLB,
but its source assembly is simpler: Baseball Savant already carries official
participant/contact evidence and the bulk Stats API supplies the canonical AL/NL
outcome-count backbone.  This module keeps that source-specific preparation
outside the generic player-season scorer.
"""

from __future__ import annotations

import polars as pl

from universal_baseball.contact_profile import classify_contact_profile_events
from universal_baseball.mlb_performance import MLB_LEAGUE_IDS


MLB_CONTACT_PARTICIPANT_AUTHORITY = "savant_official"
MLB_CONTACT_NARRATIVE_AUTHORITY = "savant_official"


def classify_mlb_savant_contacts(savant: pl.DataFrame) -> pl.DataFrame:
    """Classify MLB Savant contacts into the frozen screened contact profile."""

    required = {
        "game_year",
        "league_id",
        "game_pk",
        "at_bat_index",
        "pitch_number",
        "batter_mlbam_id",
        "batter_side",
        "bb_type",
        "hc_x",
        "hc_y",
        "result_description",
        "is_contact",
    }
    missing = sorted(required - set(savant.columns))
    if missing:
        raise ValueError(f"MLB Savant Performance rows missing contact fields: {missing}")
    if savant.is_empty():
        return classify_contact_profile_events(
            pl.DataFrame(
                schema={
                    "season": pl.Int64,
                    "league_id": pl.Int64,
                    "game_pk": pl.Int64,
                    "at_bat_index": pl.Int64,
                    "pitch_number": pl.Int64,
                    "batter_mlbam_id": pl.Int64,
                    "participant_authority": pl.String,
                    "result_description_authority": pl.String,
                    "batter_side": pl.String,
                    "bb_type": pl.String,
                    "hc_x": pl.Float64,
                    "hc_y": pl.Float64,
                    "result_description": pl.String,
                }
            )
        )

    contacts = savant.filter(pl.col("is_contact"))
    if contacts.is_empty():
        return classify_mlb_savant_contacts(savant.head(0))
    unknown_leagues = sorted(
        int(value)
        for value in contacts.get_column("league_id").drop_nulls().unique().to_list()
        if int(value) not in MLB_LEAGUE_IDS
    )
    if unknown_leagues:
        raise ValueError(f"MLB Savant contacts contain non-MLB league IDs: {unknown_leagues}")

    input_frame = contacts.select(
        pl.col("game_year").cast(pl.Int64).alias("season"),
        pl.col("league_id").cast(pl.Int64),
        pl.col("game_pk").cast(pl.Int64),
        pl.col("at_bat_index").cast(pl.Int64),
        pl.col("pitch_number").cast(pl.Int64),
        pl.col("batter_mlbam_id").cast(pl.Int64),
        pl.lit(MLB_CONTACT_PARTICIPANT_AUTHORITY).alias("participant_authority"),
        pl.lit(MLB_CONTACT_NARRATIVE_AUTHORITY).alias("result_description_authority"),
        pl.col("batter_side").cast(pl.String),
        pl.col("bb_type").cast(pl.String),
        pl.col("hc_x").cast(pl.Float64, strict=False),
        pl.col("hc_y").cast(pl.Float64, strict=False),
        pl.col("result_description").cast(pl.String),
    )
    classified = classify_contact_profile_events(input_frame)
    if classified.height != contacts.height:
        raise ValueError(
            f"MLB contact classifier lost rows: {classified.height:,} vs {contacts.height:,}"
        )
    return classified
