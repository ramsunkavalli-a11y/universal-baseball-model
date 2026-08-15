"""Certify MLBAM identities carried by reusable pitch-grain source rows."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import polars as pl


SOURCE_ID_COLUMNS = {"batter": "batter_id", "pitcher": "pitcher_id"}
SOURCE_SEQUENCE_KEY = ("game_pk", "at_bat_number")


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return None


def compare_source_mlbam_ids(
    source: pl.DataFrame,
    official_pas: pl.DataFrame,
) -> dict[str, Any]:
    """Compare source batter/pitcher MLBAM IDs with true official PA identities.

    The source is pitch-grain and may contain exact duplicates or multiple source
    snapshots for one pitch key. Identity is therefore first reduced to the
    ``game_pk + at_bat_number`` sequence. Multiple distinct non-null IDs inside
    one source sequence are reported as conflicts and never silently resolved.

    Only sequences that correspond to a true official PA are scored as identity
    matches/mismatches. Source-only pitch-bearing sequences remain diagnostic
    evidence because a pitch table cannot by itself establish PA semantics.
    """

    required_source = {*SOURCE_SEQUENCE_KEY, *SOURCE_ID_COLUMNS}
    required_official = {
        *SOURCE_SEQUENCE_KEY,
        *SOURCE_ID_COLUMNS.values(),
        "event_type",
    }
    missing_source = sorted(required_source - set(source.columns))
    missing_official = sorted(required_official - set(official_pas.columns))
    if missing_source:
        raise ValueError(f"source missing identity columns: {missing_source}")
    if missing_official:
        raise ValueError(f"official PA frame missing identity columns: {missing_official}")

    source_values: dict[tuple[str, str], dict[str, set[int]]] = defaultdict(
        lambda: {"batter": set(), "pitcher": set()}
    )
    for row in source.select(
        ["game_pk", "at_bat_number", "batter", "pitcher"]
    ).unique().to_dicts():
        key = (str(row["game_pk"]), str(row["at_bat_number"]))
        for source_column in SOURCE_ID_COLUMNS:
            value = _int_or_none(row.get(source_column))
            if value is not None:
                source_values[key][source_column].add(value)

    official_map = {
        (str(row["game_pk"]), str(row["at_bat_number"])): row
        for row in official_pas.to_dicts()
    }
    source_keys = set(source_values)
    official_keys = set(official_map)
    shared_keys = source_keys & official_keys

    conflict_examples: list[dict[str, Any]] = []
    mismatch_examples: list[dict[str, Any]] = []
    missing_source_id_examples: list[dict[str, Any]] = []
    role_counts: dict[str, dict[str, int]] = {
        "batter": {"compared": 0, "matched": 0, "mismatched": 0, "missing": 0, "conflict": 0},
        "pitcher": {"compared": 0, "matched": 0, "mismatched": 0, "missing": 0, "conflict": 0},
    }

    for key in sorted(shared_keys):
        official_row = official_map[key]
        source_roles = source_values[key]
        for source_column, official_column in SOURCE_ID_COLUMNS.items():
            values = sorted(source_roles[source_column])
            counts = role_counts[source_column]
            if len(values) > 1:
                counts["conflict"] += 1
                if len(conflict_examples) < 25:
                    conflict_examples.append(
                        {
                            "game_pk": key[0],
                            "at_bat_number": key[1],
                            "role": source_column,
                            "source_ids": values,
                            "official_id": _int_or_none(official_row.get(official_column)),
                            "event_type": official_row.get("event_type"),
                        }
                    )
                continue

            source_id = values[0] if values else None
            official_id = _int_or_none(official_row.get(official_column))
            if source_id is None:
                counts["missing"] += 1
                if len(missing_source_id_examples) < 25:
                    missing_source_id_examples.append(
                        {
                            "game_pk": key[0],
                            "at_bat_number": key[1],
                            "role": source_column,
                            "official_id": official_id,
                            "event_type": official_row.get("event_type"),
                        }
                    )
                continue

            counts["compared"] += 1
            if source_id == official_id:
                counts["matched"] += 1
            else:
                counts["mismatched"] += 1
                if len(mismatch_examples) < 25:
                    mismatch_examples.append(
                        {
                            "game_pk": key[0],
                            "at_bat_number": key[1],
                            "role": source_column,
                            "source_id": source_id,
                            "official_id": official_id,
                            "event_type": official_row.get("event_type"),
                        }
                    )

    source_only_keys = sorted(source_keys - official_keys)
    official_only_keys = sorted(official_keys - source_keys)

    total_compared = sum(role["compared"] for role in role_counts.values())
    total_matched = sum(role["matched"] for role in role_counts.values())
    total_mismatched = sum(role["mismatched"] for role in role_counts.values())
    total_conflicts = sum(role["conflict"] for role in role_counts.values())
    total_missing = sum(role["missing"] for role in role_counts.values())

    return {
        "source_pitch_sequence_count": len(source_keys),
        "official_true_pa_count": len(official_keys),
        "shared_sequence_true_pa_count": len(shared_keys),
        "source_only_pitch_sequence_count": len(source_only_keys),
        "official_only_true_pa_count": len(official_only_keys),
        "source_only_pitch_sequence_examples": [
            {"game_pk": key[0], "at_bat_number": key[1]}
            for key in source_only_keys[:25]
        ],
        "official_only_true_pa_examples": [
            {
                "game_pk": key[0],
                "at_bat_number": key[1],
                "event_type": official_map[key].get("event_type"),
            }
            for key in official_only_keys[:25]
        ],
        "role_counts": role_counts,
        "identity_comparison_count": total_compared,
        "identity_match_count": total_matched,
        "identity_mismatch_count": total_mismatched,
        "source_identity_conflict_count": total_conflicts,
        "source_identity_missing_count": total_missing,
        "identity_match_rate": total_matched / total_compared if total_compared else None,
        "identity_mismatch_examples": mismatch_examples,
        "source_identity_conflict_examples": conflict_examples,
        "source_identity_missing_examples": missing_source_id_examples,
        "certification_clean_on_shared_true_pas": (
            total_mismatched == 0 and total_conflicts == 0 and total_missing == 0
        ),
    }
