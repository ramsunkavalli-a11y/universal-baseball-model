"""Build model-working pitch fields without mutating source observations.

Reusable MiLB PBP supplies broad historical pitch evidence. Official structured
play sequences are authoritative for matchup identity and handedness when
available. This module combines those layers in a derived view while preserving
both inputs and recording which authority supplied each working field.
"""

from __future__ import annotations

import polars as pl


PITCH_KEY = ("game_pk", "at_bat_index", "pitch_number")
SEQUENCE_KEY = ("game_pk", "at_bat_index")

_SOURCE_FIELDS = {
    "source_batter_mlbam_id",
    "source_pitcher_mlbam_id",
    "batter_side",
    "pitcher_hand",
}
_OFFICIAL_FIELDS = {
    "batter_mlbam_id",
    "pitcher_mlbam_id",
    "batter_side",
    "pitcher_hand",
    "classification_status",
}


def _assert_unique(frame: pl.DataFrame, key: tuple[str, ...], label: str) -> None:
    duplicates = frame.group_by(list(key)).len().filter(pl.col("len") > 1)
    if not duplicates.is_empty():
        raise ValueError(f"{label} is not unique by {list(key)}")


def _mismatch_expr(source: str, official: str) -> pl.Expr:
    return (
        pl.col(source).is_not_null()
        & pl.col(official).is_not_null()
        & (pl.col(source) != pl.col(official))
    )


def build_pitch_authority_view(
    source_resolved_pitches: pl.DataFrame,
    official_sequences: pl.DataFrame,
) -> pl.DataFrame:
    """Overlay official matchup fields onto source-resolved physical pitches.

    Rules are deliberately field-scoped:

    - source observations and source-consensus values are never rewritten;
    - official sequence participant IDs and handedness take precedence when
      present because those fields are directly represented in structured MLB
      matchup evidence;
    - when an official field is absent, a non-null source-consensus value may be
      used as a fallback and is labeled ``reusable_source_only``;
    - if neither layer supplies a value, the working field remains null;
    - disagreements remain visible through explicit mismatch flags.

    The output is a derived working view. It is not an immutable observation
    table and does not establish historical information availability for strict
    vintage backtests.
    """

    missing_pitch_key = sorted(set(PITCH_KEY) - set(source_resolved_pitches.columns))
    if missing_pitch_key:
        raise ValueError(f"source-resolved pitches missing key columns: {missing_pitch_key}")
    missing_source = sorted(_SOURCE_FIELDS - set(source_resolved_pitches.columns))
    if missing_source:
        raise ValueError(f"source-resolved pitches missing authority fields: {missing_source}")

    missing_sequence_key = sorted(set(SEQUENCE_KEY) - set(official_sequences.columns))
    if missing_sequence_key:
        raise ValueError(f"official sequences missing key columns: {missing_sequence_key}")
    missing_official = sorted(_OFFICIAL_FIELDS - set(official_sequences.columns))
    if missing_official:
        raise ValueError(f"official sequences missing authority fields: {missing_official}")

    _assert_unique(source_resolved_pitches, PITCH_KEY, "source-resolved pitch view")
    _assert_unique(official_sequences, SEQUENCE_KEY, "official sequence view")

    official = official_sequences.select(
        [
            *SEQUENCE_KEY,
            pl.col("classification_status").alias("official_classification_status"),
            pl.col("batter_mlbam_id").alias("official_batter_mlbam_id"),
            pl.col("pitcher_mlbam_id").alias("official_pitcher_mlbam_id"),
            pl.col("batter_side").alias("official_batter_side"),
            pl.col("pitcher_hand").alias("official_pitcher_hand"),
        ]
    ).with_columns(pl.lit(True).alias("official_sequence_found"))

    joined = source_resolved_pitches.rename(
        {
            "batter_side": "source_consensus_batter_side",
            "pitcher_hand": "source_consensus_pitcher_hand",
        }
    ).join(official, on=list(SEQUENCE_KEY), how="left")

    joined = joined.with_columns(
        pl.col("official_sequence_found").fill_null(False),
        _mismatch_expr(
            "source_batter_mlbam_id", "official_batter_mlbam_id"
        ).alias("batter_id_mismatch"),
        _mismatch_expr(
            "source_pitcher_mlbam_id", "official_pitcher_mlbam_id"
        ).alias("pitcher_id_mismatch"),
        _mismatch_expr(
            "source_consensus_batter_side", "official_batter_side"
        ).alias("batter_side_mismatch"),
        _mismatch_expr(
            "source_consensus_pitcher_hand", "official_pitcher_hand"
        ).alias("pitcher_hand_mismatch"),
    )

    joined = joined.with_columns(
        pl.coalesce(
            ["official_batter_mlbam_id", "source_batter_mlbam_id"]
        ).alias("working_batter_mlbam_id"),
        pl.coalesce(
            ["official_pitcher_mlbam_id", "source_pitcher_mlbam_id"]
        ).alias("working_pitcher_mlbam_id"),
        pl.coalesce(
            ["official_batter_side", "source_consensus_batter_side"]
        ).alias("working_batter_side"),
        pl.coalesce(
            ["official_pitcher_hand", "source_consensus_pitcher_hand"]
        ).alias("working_pitcher_hand"),
    )

    joined = joined.with_columns(
        pl.when(
            pl.col("official_batter_mlbam_id").is_not_null()
            & pl.col("official_pitcher_mlbam_id").is_not_null()
        )
        .then(pl.lit("official_matchup"))
        .when(
            pl.col("source_batter_mlbam_id").is_not_null()
            & pl.col("source_pitcher_mlbam_id").is_not_null()
        )
        .then(pl.lit("reusable_source_only"))
        .otherwise(pl.lit("incomplete"))
        .alias("working_identity_authority"),
        pl.when(
            pl.col("official_batter_side").is_not_null()
            & pl.col("official_pitcher_hand").is_not_null()
        )
        .then(pl.lit("official_matchup"))
        .when(
            pl.col("source_consensus_batter_side").is_not_null()
            & pl.col("source_consensus_pitcher_hand").is_not_null()
        )
        .then(pl.lit("reusable_source_only"))
        .otherwise(pl.lit("mixed_or_incomplete"))
        .alias("working_handedness_authority"),
    )

    return joined.sort(list(PITCH_KEY))
