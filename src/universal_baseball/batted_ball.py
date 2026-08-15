"""Batted-ball evidence certification for the reusable MiLB pitch source.

The first gate is deliberately conservative: verify that fields already copied
from MLB ``hitData`` remain faithful to the current official feed before deriving
spray sectors or FaBIO-style categories from them. No narrative parsing, spray
angle formula, or source repair happens here.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from math import isclose
from typing import Any

import polars as pl


PITCH_KEY = ("game_pk", "at_bat_number", "pitch_number")

SOURCE_TO_OFFICIAL_FIELDS: dict[str, str] = {
    "stand": "batter_side",
    "bb_type": "hit_trajectory",
    "hit_location": "hit_location",
    "hc_x": "hit_coord_x",
    "hc_y": "hit_coord_y",
    "hit_distance_sc": "hit_total_distance",
    "launch_speed": "hit_launch_speed",
    "launch_angle": "hit_launch_angle",
}

NUMERIC_SOURCE_FIELDS = frozenset(
    {"hc_x", "hc_y", "hit_distance_sc", "launch_speed", "launch_angle"}
)


def _key(row: dict[str, Any]) -> tuple[str, str, str]:
    return tuple(str(row[column]) for column in PITCH_KEY)  # type: ignore[return-value]


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _number(value: Any) -> float | None:
    text = _text(value)
    if text is None:
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _normalized(value: Any, *, numeric: bool) -> str | float | None:
    return _number(value) if numeric else _text(value)


def _equal(left: Any, right: Any, *, numeric: bool) -> bool:
    if numeric:
        left_number = _number(left)
        right_number = _number(right)
        if left_number is None or right_number is None:
            return left_number is right_number
        return isclose(left_number, right_number, rel_tol=0.0, abs_tol=1e-6)
    return _text(left) == _text(right)


def compare_source_batted_balls(
    source: pl.DataFrame,
    official_pitch_events: pl.DataFrame,
) -> dict[str, Any]:
    """Compare reusable-source batted-ball fields with current official hitData.

    The official feed defines which current pitch events are in play. Source rows
    are matched only on the natural pitch key. If the source has multiple distinct
    payload observations for a key, each field must agree across those observations
    before a single source value is compared. Conflicting values are reported and
    never silently resolved.
    """

    missing_source_keys = sorted(set(PITCH_KEY) - set(source.columns))
    if missing_source_keys:
        raise ValueError(f"source missing pitch-key columns: {missing_source_keys}")

    required_official = {*PITCH_KEY, "is_in_play"}
    missing_official = sorted(required_official - set(official_pitch_events.columns))
    if missing_official:
        raise ValueError(
            f"official pitch events missing required columns: {missing_official}"
        )

    available_source_fields = {
        source_field: official_field
        for source_field, official_field in SOURCE_TO_OFFICIAL_FIELDS.items()
        if source_field in source.columns and official_field in official_pitch_events.columns
    }

    source_rows_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in source.unique().to_dicts():
        if any(row.get(column) is None for column in PITCH_KEY):
            continue
        source_rows_by_key[_key(row)].append(row)

    official_bip_rows = official_pitch_events.filter(pl.col("is_in_play") == True)  # noqa: E712
    official_rows_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in official_bip_rows.to_dicts():
        if any(row.get(column) is None for column in PITCH_KEY):
            continue
        official_rows_by_key[_key(row)].append(row)

    duplicate_official_keys = {
        key: len(rows)
        for key, rows in official_rows_by_key.items()
        if len(rows) > 1
    }

    field_summaries: dict[str, dict[str, Any]] = {}
    for source_field, official_field in available_source_fields.items():
        field_summaries[source_field] = {
            "official_field": official_field,
            "official_nonblank": 0,
            "source_nonblank": 0,
            "both_nonblank": 0,
            "matches_when_both_nonblank": 0,
            "mismatches_when_both_nonblank": 0,
            "source_missing_when_official_present": 0,
            "official_missing_when_source_present": 0,
            "source_conflicting_key_count": 0,
        }

    trajectory_source_counts: Counter[str] = Counter()
    trajectory_official_counts: Counter[str] = Counter()
    location_source_counts: Counter[str] = Counter()
    location_official_counts: Counter[str] = Counter()
    mismatch_examples: list[dict[str, Any]] = []
    source_conflict_examples: list[dict[str, Any]] = []
    shared_key_count = 0
    source_missing_keys: list[dict[str, str]] = []

    for key, official_rows in sorted(official_rows_by_key.items()):
        # A duplicate official natural key is itself evidence that needs review.
        # Compare against the first row only for field diagnostics; certification
        # reports the duplicate key separately and must not consider it clean.
        official_row = official_rows[0]
        source_rows = source_rows_by_key.get(key)
        if not source_rows:
            source_missing_keys.append(
                {
                    "game_pk": key[0],
                    "at_bat_number": key[1],
                    "pitch_number": key[2],
                }
            )
            continue

        shared_key_count += 1

        source_field_values: dict[str, Any] = {}
        source_field_conflicts: dict[str, list[Any]] = {}
        for source_field in available_source_fields:
            numeric = source_field in NUMERIC_SOURCE_FIELDS
            values: list[Any] = []
            for source_row in source_rows:
                value = _normalized(source_row.get(source_field), numeric=numeric)
                if value is not None and value not in values:
                    values.append(value)
            if len(values) == 1:
                source_field_values[source_field] = values[0]
            elif len(values) > 1:
                source_field_conflicts[source_field] = values
                field_summaries[source_field]["source_conflicting_key_count"] += 1

        if source_field_conflicts and len(source_conflict_examples) < 25:
            source_conflict_examples.append(
                {
                    "game_pk": key[0],
                    "at_bat_number": key[1],
                    "pitch_number": key[2],
                    "conflicts": source_field_conflicts,
                }
            )

        source_trajectory = _text(source_field_values.get("bb_type"))
        official_trajectory = _text(official_row.get("hit_trajectory"))
        if source_trajectory is not None:
            trajectory_source_counts[source_trajectory] += 1
        if official_trajectory is not None:
            trajectory_official_counts[official_trajectory] += 1

        source_location = _text(source_field_values.get("hit_location"))
        official_location = _text(official_row.get("hit_location"))
        if source_location is not None:
            location_source_counts[source_location] += 1
        if official_location is not None:
            location_official_counts[official_location] += 1

        for source_field, official_field in available_source_fields.items():
            summary = field_summaries[source_field]
            numeric = source_field in NUMERIC_SOURCE_FIELDS
            if source_field in source_field_conflicts:
                continue

            source_value = source_field_values.get(source_field)
            official_value = _normalized(official_row.get(official_field), numeric=numeric)
            source_present = source_value is not None
            official_present = official_value is not None

            if source_present:
                summary["source_nonblank"] += 1
            if official_present:
                summary["official_nonblank"] += 1
            if source_present and official_present:
                summary["both_nonblank"] += 1
                if _equal(source_value, official_value, numeric=numeric):
                    summary["matches_when_both_nonblank"] += 1
                else:
                    summary["mismatches_when_both_nonblank"] += 1
                    if len(mismatch_examples) < 50:
                        mismatch_examples.append(
                            {
                                "game_pk": key[0],
                                "at_bat_number": key[1],
                                "pitch_number": key[2],
                                "field": source_field,
                                "source_value": source_value,
                                "official_value": official_value,
                            }
                        )
            elif official_present:
                summary["source_missing_when_official_present"] += 1
            elif source_present:
                summary["official_missing_when_source_present"] += 1

    source_rows_with_metadata = 0
    metadata_fields = [
        field
        for field in (
            "bb_type",
            "hit_location",
            "hc_x",
            "hc_y",
            "hit_distance_sc",
            "launch_speed",
            "launch_angle",
        )
        if field in source.columns
    ]
    if metadata_fields:
        for row in source.unique(subset=list(PITCH_KEY)).to_dicts():
            if any(_text(row.get(field)) is not None for field in metadata_fields):
                source_rows_with_metadata += 1

    for summary in field_summaries.values():
        both = int(summary["both_nonblank"])
        matches = int(summary["matches_when_both_nonblank"])
        summary["agreement_rate_when_both_nonblank"] = (
            matches / both if both else None
        )
        summary["source_coverage_of_official_bip"] = (
            int(summary["source_nonblank"]) / len(official_rows_by_key)
            if official_rows_by_key
            else None
        )
        summary["official_coverage_of_official_bip"] = (
            int(summary["official_nonblank"]) / len(official_rows_by_key)
            if official_rows_by_key
            else None
        )

    total_field_mismatches = sum(
        int(summary["mismatches_when_both_nonblank"])
        for summary in field_summaries.values()
    )
    total_source_field_conflicts = sum(
        int(summary["source_conflicting_key_count"])
        for summary in field_summaries.values()
    )

    return {
        "official_in_play_pitch_count": len(official_rows_by_key),
        "official_duplicate_in_play_pitch_key_count": len(duplicate_official_keys),
        "official_duplicate_in_play_pitch_keys": [
            {
                "game_pk": key[0],
                "at_bat_number": key[1],
                "pitch_number": key[2],
                "row_count": row_count,
            }
            for key, row_count in list(duplicate_official_keys.items())[:25]
        ],
        "shared_in_play_pitch_key_count": shared_key_count,
        "source_missing_in_play_pitch_key_count": len(source_missing_keys),
        "source_missing_in_play_pitch_key_examples": source_missing_keys[:25],
        "source_rows_with_any_batted_ball_metadata": source_rows_with_metadata,
        "source_fields_tested": available_source_fields,
        "field_summaries": field_summaries,
        "total_field_mismatch_count": total_field_mismatches,
        "total_source_field_conflict_count": total_source_field_conflicts,
        "source_field_conflict_examples": source_conflict_examples,
        "mismatch_examples": mismatch_examples,
        "trajectory_source_counts_on_shared_official_bip": dict(
            sorted(trajectory_source_counts.items())
        ),
        "trajectory_official_counts_on_shared_official_bip": dict(
            sorted(trajectory_official_counts.items())
        ),
        "location_source_counts_on_shared_official_bip": dict(
            sorted(location_source_counts.items())
        ),
        "location_official_counts_on_shared_official_bip": dict(
            sorted(location_official_counts.items())
        ),
        "certification_clean": (
            not duplicate_official_keys
            and not source_missing_keys
            and total_source_field_conflicts == 0
            and total_field_mismatches == 0
        ),
    }
