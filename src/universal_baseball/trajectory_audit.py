"""Empirical diagnostics for the Gameday batted-ball trajectory vocabulary.

This module is intentionally descriptive. It measures how source labels such as
``popup`` and ``bunt_grounder`` behave before the project maps them into a
FaBIO-like Performance/Profile taxonomy. No trajectory label is promoted here.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from universal_baseball.batted_ball_direction import field_spray_angle_expr


PITCH_KEY = ("game_pk", "at_bat_number", "pitch_number")
PROFILE_FIELDS = (
    "type",
    "bb_type",
    "hit_location",
    "description",
    "hc_x",
    "hc_y",
    "stand",
)
AIRBORNE_TYPES = ("popup", "fly_ball")
BUNT_TYPES = ("bunt_grounder", "bunt_popup", "bunt_line_drive")
INFIELD_POSITIONS = (1, 2, 3, 4, 5, 6)
OUTFIELD_POSITIONS = (7, 8, 9)
APPROX_FAIR_LINE_DEGREES = 45.0


def _stable_value(field: str) -> pl.Expr:
    values = pl.col(field).drop_nulls()
    return (
        pl.when(values.n_unique() <= 1)
        .then(values.first())
        .otherwise(pl.lit(None))
        .alias(field)
    )


def _conflict(field: str) -> pl.Expr:
    return (pl.col(field).drop_nulls().n_unique() > 1).alias(f"{field}__conflict")


def collapse_trajectory_evidence(frame: pl.DataFrame) -> pl.DataFrame:
    """Resolve repeated source observations without choosing arbitrary rows."""

    missing_key = sorted(set(PITCH_KEY) - set(frame.columns))
    if missing_key:
        raise ValueError(f"source missing natural pitch key: {missing_key}")
    missing_fields = sorted({"type", "bb_type"} - set(frame.columns))
    if missing_fields:
        raise ValueError(f"source missing trajectory fields: {missing_fields}")

    fields = [field for field in PROFILE_FIELDS if field in frame.columns]
    aggregations: list[pl.Expr] = []
    for field in fields:
        aggregations.extend([_stable_value(field), _conflict(field)])
    return frame.group_by(list(PITCH_KEY)).agg(aggregations).sort(list(PITCH_KEY))


def _position_expr() -> pl.Expr:
    return pl.col("hit_location").cast(pl.Float64, strict=False).cast(pl.Int64, strict=False)


def _contains_foul_expr() -> pl.Expr:
    return (
        pl.col("description")
        .cast(pl.String, strict=False)
        .fill_null("")
        .str.to_lowercase()
        .str.contains("foul")
    )


def _hit_like_description_expr() -> pl.Expr:
    # Diagnostic only. Production outcomes come from official structured PA
    # semantics, never this narrative heuristic.
    text = (
        pl.col("description")
        .cast(pl.String, strict=False)
        .fill_null("")
        .str.to_lowercase()
    )
    return text.str.contains(r"\b(single|doubles?|triples?|home run)\b")


def _counts(frame: pl.DataFrame, column: str) -> dict[str, int]:
    if column not in frame.columns:
        return {}
    rows = (
        frame.filter(pl.col(column).is_not_null())
        .group_by(column)
        .len()
        .sort(["len", column], descending=[True, False])
        .to_dicts()
    )
    return {str(row[column]): int(row["len"]) for row in rows}


def _spray_geometry(rows: pl.DataFrame) -> dict[str, Any]:
    if not {"hc_x", "hc_y"} <= set(rows.columns):
        return {
            "spray_angle_present_count": 0,
            "outside_approx_fair_sector_count": 0,
            "outside_approx_fair_sector_rate": None,
            "foul_text_and_outside_sector_count": 0,
            "foul_text_but_inside_sector_count": 0,
            "outside_sector_without_foul_text_count": 0,
        }

    angled = rows.with_columns(
        field_spray_angle_expr(pl.col("hc_x"), pl.col("hc_y")).alias("spray_angle")
    ).filter(pl.col("spray_angle").is_not_null())
    outside_expr = pl.col("spray_angle").abs() > APPROX_FAIR_LINE_DEGREES
    outside = angled.filter(outside_expr)
    foul_expr = _contains_foul_expr() if "description" in angled.columns else pl.lit(False)
    foul_and_outside = angled.filter(foul_expr & outside_expr).height
    foul_inside = angled.filter(foul_expr & ~outside_expr).height
    outside_not_foul = angled.filter(outside_expr & ~foul_expr).height

    return {
        "spray_angle_present_count": angled.height,
        "outside_approx_fair_sector_count": outside.height,
        "outside_approx_fair_sector_rate": (
            outside.height / angled.height if angled.height else None
        ),
        "foul_text_and_outside_sector_count": foul_and_outside,
        "foul_text_but_inside_sector_count": foul_inside,
        "outside_sector_without_foul_text_count": outside_not_foul,
    }


def _trajectory_detail(bip: pl.DataFrame, trajectory: str) -> dict[str, Any]:
    rows = bip.filter(pl.col("bb_type") == trajectory)
    total = rows.height
    position = _position_expr()
    with_location = rows.filter(position.is_not_null())
    infield_touch = with_location.filter(position.is_in(INFIELD_POSITIONS)).height
    outfield_touch = with_location.filter(position.is_in(OUTFIELD_POSITIONS)).height
    other_location = with_location.height - infield_touch - outfield_touch
    foul_count = (
        rows.filter(_contains_foul_expr()).height
        if "description" in rows.columns
        else 0
    )
    hit_like_count = (
        rows.filter(_hit_like_description_expr()).height
        if "description" in rows.columns
        else 0
    )
    return {
        "count": total,
        "share_of_in_play": total / bip.height if bip.height else None,
        "hit_location_present_count": with_location.height,
        "infield_first_touch_count": infield_touch,
        "outfield_first_touch_count": outfield_touch,
        "other_hit_location_count": other_location,
        "infield_first_touch_rate_when_location_present": (
            infield_touch / with_location.height if with_location.height else None
        ),
        "outfield_first_touch_rate_when_location_present": (
            outfield_touch / with_location.height if with_location.height else None
        ),
        "description_mentions_foul_count": foul_count,
        "description_mentions_foul_rate": foul_count / total if total else None,
        "description_hit_like_count": hit_like_count,
        "description_hit_like_rate": hit_like_count / total if total else None,
        "hit_location_counts": _counts(rows.with_columns(position.alias("position")), "position"),
        "spray_geometry": _spray_geometry(rows),
    }


def build_trajectory_profile(frame: pl.DataFrame) -> dict[str, Any]:
    """Profile trajectory labels at natural physical-pitch grain."""

    exact_unique = frame.unique()
    pitches = collapse_trajectory_evidence(exact_unique)

    conflict_columns = [
        f"{field}__conflict"
        for field in PROFILE_FIELDS
        if f"{field}__conflict" in pitches.columns
    ]
    field_conflicts = {
        field: pitches.filter(pl.col(f"{field}__conflict")).height
        for field in PROFILE_FIELDS
        if f"{field}__conflict" in pitches.columns
    }
    any_conflict = (
        pitches.filter(pl.any_horizontal([pl.col(column) for column in conflict_columns])).height
        if conflict_columns
        else 0
    )

    # Unknown/conflicting pitch-result evidence never enters the BIP denominator.
    bip = pitches.filter(pl.col("type").cast(pl.String, strict=False) == "X")
    trajectory_counts = _counts(bip, "bb_type")
    known_trajectory_count = sum(trajectory_counts.values())
    unknown_trajectory_count = bip.height - known_trajectory_count

    details = {
        trajectory: _trajectory_detail(bip, trajectory)
        for trajectory in sorted(trajectory_counts)
    }
    bunt_count = sum(trajectory_counts.get(value, 0) for value in BUNT_TYPES)
    airborne = bip.filter(pl.col("bb_type").is_in(AIRBORNE_TYPES))
    airborne_foul_count = (
        airborne.filter(_contains_foul_expr()).height
        if "description" in airborne.columns
        else 0
    )

    return {
        "raw_row_count": frame.height,
        "exact_unique_row_count": exact_unique.height,
        "natural_pitch_key_count": pitches.height,
        "in_play_pitch_key_count": bip.height,
        "known_trajectory_count": known_trajectory_count,
        "unknown_trajectory_count": unknown_trajectory_count,
        "known_trajectory_rate": (
            known_trajectory_count / bip.height if bip.height else None
        ),
        "trajectory_counts": trajectory_counts,
        "trajectory_details": details,
        "bunt_in_play_count": bunt_count,
        "bunt_share_of_in_play": bunt_count / bip.height if bip.height else None,
        "airborne_count": airborne.height,
        "airborne_description_mentions_foul_count": airborne_foul_count,
        "airborne_description_mentions_foul_rate": (
            airborne_foul_count / airborne.height if airborne.height else None
        ),
        "airborne_spray_geometry": _spray_geometry(airborne),
        "audited_field_conflicts": {
            "conflicting_pitch_key_count": any_conflict,
            "field_conflict_counts": field_conflicts,
        },
    }
