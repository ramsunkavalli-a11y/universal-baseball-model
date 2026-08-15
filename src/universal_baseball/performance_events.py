"""Minimum universal Performance event classification.

This module implements the first PA-level bridge between the accepted canonical
source contracts and the FaBIO-compatible Performance/Profile design in ADR 008.
It is deliberately descriptive: no run values, shrinkage, or projection logic
belongs here.

The top-level Performance accounting is exhaustive for official true plate
appearances. The 12-bin FaBIO-style view is a narrower core classification.
Airborne foul screening is intentionally *not* applied yet; the emitted core bin
is therefore a pre-foul-screen candidate suitable for coverage auditing and
later sensitivity analysis.
"""

from __future__ import annotations

import polars as pl

from universal_baseball.batted_ball_direction import (
    batted_ball_direction_expr,
    field_spray_angle_expr,
)
from universal_baseball.event_types import PLATE_APPEARANCE_EVENT_TYPES


BB_HBP_EVENT_TYPES = frozenset({"walk", "intent_walk", "hit_by_pitch"})
STRIKEOUT_EVENT_TYPES = frozenset(
    {"strikeout", "strike_out", "strikeout_double_play", "strikeout_triple_play"}
)
SPECIAL_NON_BIP_EVENT_TYPES = frozenset(
    {"catcher_interf", "batter_interference", "os_ruling_pending_primary"}
)
BIP_EXPECTED_EVENT_TYPES = frozenset(
    PLATE_APPEARANCE_EVENT_TYPES
    - BB_HBP_EVENT_TYPES
    - STRIKEOUT_EVENT_TYPES
    - SPECIAL_NON_BIP_EVENT_TYPES
)

TRAJECTORY_FAMILY = {
    "popup": "IFFB",
    "fly_ball": "OFFB",
    "line_drive": "LD",
    "ground_ball": "GB",
    "bunt_grounder": "BUNT",
    "bunt_popup": "BUNT",
    "bunt_line_drive": "BUNT",
}

PERFORMANCE_EVENT_SCHEMA: dict[str, pl.DataType] = {
    "game_pk": pl.Int64,
    "at_bat_index": pl.Int64,
    "batter_mlbam_id": pl.Int64,
    "pitcher_mlbam_id": pl.Int64,
    "official_event_type": pl.String,
    "performance_family": pl.String,
    "is_bip_expected": pl.Boolean,
    "in_play_pitch_count": pl.Int64,
    "unknown_in_play_flag_pitch_count": pl.Int64,
    "source_conflict_pitch_count": pl.Int64,
    "source_bip_pitch_number": pl.Int64,
    "source_bb_type": pl.String,
    "trajectory_family": pl.String,
    "spray_angle": pl.Float64,
    "direction": pl.String,
    "fabio_core_bin_pre_foul_screen": pl.String,
    "core_profile_eligible_pre_foul_screen": pl.Boolean,
    "evidence_status": pl.String,
}


def _trajectory_family_expr() -> pl.Expr:
    expression = pl.lit("UNKNOWN")
    for source_value, family in TRAJECTORY_FAMILY.items():
        expression = pl.when(pl.col("source_bb_type") == source_value).then(
            pl.lit(family)
        ).otherwise(expression)
    return expression.alias("trajectory_family")


def _empty_performance_frame() -> pl.DataFrame:
    return pl.DataFrame(schema=PERFORMANCE_EVENT_SCHEMA)


def build_performance_events(
    play_sequences: pl.DataFrame,
    pitch_consensus: pl.DataFrame,
) -> pl.DataFrame:
    """Classify official true PAs using official outcomes + reusable BIP evidence.

    Required authority split:
    - PA existence, outcome, batter identity and batting side come from the
      official structured play-sequence layer;
    - physical in-play pitch, trajectory and coordinates come from the resolved
      reusable pitch evidence;
    - source disagreements remain null/conflicted upstream and therefore reduce
      classification coverage here rather than being imputed.

    The function returns exactly one row per official true PA.
    """

    required_sequences = {
        "game_pk",
        "at_bat_index",
        "classification_status",
        "result_event_type",
        "batter_mlbam_id",
        "pitcher_mlbam_id",
        "batter_side",
    }
    required_pitches = {
        "game_pk",
        "at_bat_index",
        "pitch_number",
        "is_in_play",
        "bb_type",
        "hc_x",
        "hc_y",
    }
    missing_sequences = sorted(required_sequences - set(play_sequences.columns))
    missing_pitches = sorted(required_pitches - set(pitch_consensus.columns))
    if missing_sequences:
        raise ValueError(f"play sequences missing Performance fields: {missing_sequences}")
    if missing_pitches:
        raise ValueError(f"pitch consensus missing Performance fields: {missing_pitches}")

    pa = play_sequences.filter(pl.col("classification_status") == "official_true_pa")
    if pa.is_empty():
        return _empty_performance_frame()

    invalid_event = pa.filter(
        ~pl.col("result_event_type").is_in(sorted(PLATE_APPEARANCE_EVENT_TYPES))
    )
    if not invalid_event.is_empty():
        raise ValueError("official true PA contains event type outside frozen PA semantics")

    pitch_working = pitch_consensus
    if "conflict_field_count" not in pitch_working.columns:
        pitch_working = pitch_working.with_columns(
            pl.lit(0, dtype=pl.Int64).alias("conflict_field_count")
        )

    sequence_pitch_quality = pitch_working.group_by(["game_pk", "at_bat_index"]).agg(
        pl.col("is_in_play").is_null().sum().alias("unknown_in_play_flag_pitch_count"),
        (pl.col("conflict_field_count") > 0).sum().alias("source_conflict_pitch_count"),
    )

    in_play = pitch_working.filter(pl.col("is_in_play") == True)  # noqa: E712
    if in_play.is_empty():
        bip = pl.DataFrame(
            schema={
                "game_pk": pl.Int64,
                "at_bat_index": pl.Int64,
                "in_play_pitch_count": pl.Int64,
                "source_bip_pitch_number": pl.Int64,
                "source_bb_type": pl.String,
                "hc_x": pl.Float64,
                "hc_y": pl.Float64,
            }
        )
    else:
        bip = in_play.group_by(["game_pk", "at_bat_index"]).agg(
            pl.len().alias("in_play_pitch_count"),
            pl.when(pl.len() == 1)
            .then(pl.col("pitch_number").first())
            .otherwise(pl.lit(None, dtype=pl.Int64))
            .alias("source_bip_pitch_number"),
            pl.when(pl.len() == 1)
            .then(pl.col("bb_type").first())
            .otherwise(pl.lit(None, dtype=pl.String))
            .alias("source_bb_type"),
            pl.when(pl.len() == 1)
            .then(pl.col("hc_x").first())
            .otherwise(pl.lit(None, dtype=pl.Float64))
            .alias("hc_x"),
            pl.when(pl.len() == 1)
            .then(pl.col("hc_y").first())
            .otherwise(pl.lit(None, dtype=pl.Float64))
            .alias("hc_y"),
        )

    working = (
        pa.select(
            [
                "game_pk",
                "at_bat_index",
                "batter_mlbam_id",
                "pitcher_mlbam_id",
                "batter_side",
                pl.col("result_event_type").alias("official_event_type"),
            ]
        )
        .join(bip, on=["game_pk", "at_bat_index"], how="left")
        .join(sequence_pitch_quality, on=["game_pk", "at_bat_index"], how="left")
        .with_columns(
            pl.col("in_play_pitch_count").fill_null(0).cast(pl.Int64),
            pl.col("unknown_in_play_flag_pitch_count").fill_null(0).cast(pl.Int64),
            pl.col("source_conflict_pitch_count").fill_null(0).cast(pl.Int64),
        )
        .with_columns(_trajectory_family_expr())
        .with_columns(
            field_spray_angle_expr(pl.col("hc_x"), pl.col("hc_y")).alias("spray_angle"),
            batted_ball_direction_expr(
                pl.col("hc_x"), pl.col("hc_y"), pl.col("batter_side")
            ).alias("direction"),
        )
    )

    event = pl.col("official_event_type")
    in_play_count = pl.col("in_play_pitch_count")
    unknown_in_play = pl.col("unknown_in_play_flag_pitch_count")
    trajectory = pl.col("trajectory_family")
    direction = pl.col("direction")

    performance_family = (
        pl.when(event.is_in(sorted(BB_HBP_EVENT_TYPES)))
        .then(pl.lit("bb_hbp"))
        .when(event.is_in(sorted(STRIKEOUT_EVENT_TYPES)))
        .then(pl.lit("strikeout"))
        .when(event.is_in(sorted(SPECIAL_NON_BIP_EVENT_TYPES)))
        .then(pl.lit("special_non_bip"))
        .otherwise(pl.lit("batted_ball"))
    )
    is_bip_expected = event.is_in(sorted(BIP_EXPECTED_EVENT_TYPES))

    evidence_status = (
        pl.when(~is_bip_expected & (in_play_count > 0))
        .then(pl.lit("unexpected_in_play_non_bip"))
        .when(is_bip_expected & (unknown_in_play > 0) & (in_play_count == 0))
        .then(pl.lit("conflicted_in_play_flag"))
        .when(is_bip_expected & (in_play_count == 0))
        .then(pl.lit("missing_in_play_pitch"))
        .when(is_bip_expected & (in_play_count > 1))
        .then(pl.lit("multiple_in_play_pitches"))
        .when(event.is_in(sorted(SPECIAL_NON_BIP_EVENT_TYPES)))
        .then(pl.lit("special_non_bip"))
        .when(~is_bip_expected)
        .then(pl.lit("complete_non_bip"))
        .when(trajectory == "BUNT")
        .then(pl.lit("special_bunt"))
        .when(trajectory == "UNKNOWN")
        .then(pl.lit("missing_trajectory"))
        .when(trajectory.is_in(["OFFB", "LD", "GB"]) & direction.is_null())
        .then(pl.lit("missing_direction"))
        .otherwise(pl.lit("complete_bip"))
    )

    clean_non_bip = (
        ~is_bip_expected
        & ~event.is_in(sorted(SPECIAL_NON_BIP_EVENT_TYPES))
        & (in_play_count == 0)
        & (unknown_in_play == 0)
    )
    clean_bip = is_bip_expected & (in_play_count == 1)

    core_bin = (
        pl.when(clean_non_bip & event.is_in(sorted(BB_HBP_EVENT_TYPES)))
        .then(pl.lit("BB_HBP"))
        .when(clean_non_bip & event.is_in(sorted(STRIKEOUT_EVENT_TYPES)))
        .then(pl.lit("K"))
        .when(clean_bip & (trajectory == "IFFB"))
        .then(pl.lit("IFFB"))
        .when(clean_bip & (trajectory == "OFFB") & direction.is_not_null())
        .then(pl.concat_str([direction.str.to_uppercase(), pl.lit("OFFB")], separator="_"))
        .when(clean_bip & (trajectory == "LD") & direction.is_not_null())
        .then(pl.concat_str([direction.str.to_uppercase(), pl.lit("LD")], separator="_"))
        .when(clean_bip & (trajectory == "GB") & direction.is_not_null())
        .then(pl.concat_str([direction.str.to_uppercase(), pl.lit("GB")], separator="_"))
        .otherwise(pl.lit(None, dtype=pl.String))
    )

    result = (
        working.with_columns(
            performance_family.alias("performance_family"),
            is_bip_expected.alias("is_bip_expected"),
            evidence_status.alias("evidence_status"),
            core_bin.alias("fabio_core_bin_pre_foul_screen"),
        )
        .with_columns(
            pl.col("fabio_core_bin_pre_foul_screen")
            .is_not_null()
            .alias("core_profile_eligible_pre_foul_screen")
        )
        .select(list(PERFORMANCE_EVENT_SCHEMA))
        .cast(PERFORMANCE_EVENT_SCHEMA, strict=True)
        .sort(["game_pk", "at_bat_index"])
    )

    if result.height != pa.height:
        raise ValueError("Performance mapper did not preserve one row per official true PA")
    duplicates = (
        result.group_by(["game_pk", "at_bat_index"])
        .len()
        .filter(pl.col("len") > 1)
    )
    if not duplicates.is_empty():
        raise ValueError("Performance mapper produced duplicate PA keys")
    return result
