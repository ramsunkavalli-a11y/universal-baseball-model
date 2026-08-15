"""Narrow authority-aware adjudication of unresolved source conflicts.

Source consensus and official authority are separate operations. The source-only
resolver must never silently prefer one upstream snapshot. This module can then
compare a small unresolved field set with structured official evidence while
preserving every candidate value and an explicit adjudication status.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import polars as pl


SEQUENCE_KEY = ("game_pk", "at_bat_index")
SUPPORTED_OFFICIAL_PA_FIELDS = frozenset({"batter_side", "pitcher_hand"})


def _normalise_official_pas(official_pas: pl.DataFrame) -> pl.DataFrame:
    required = {"game_pk", "at_bat_number", *SUPPORTED_OFFICIAL_PA_FIELDS}
    missing = sorted(required - set(official_pas.columns))
    if missing:
        raise ValueError(f"official PA evidence missing columns: {missing}")

    return official_pas.select(
        pl.col("game_pk").cast(pl.Int64, strict=True),
        pl.col("at_bat_number").cast(pl.Int64, strict=True).alias("at_bat_index"),
        *[pl.col(field).cast(pl.String) for field in sorted(SUPPORTED_OFFICIAL_PA_FIELDS)],
    )


def adjudicate_pitch_conflicts_with_official_pas(
    observations: pl.DataFrame,
    resolved_conflicts: pl.DataFrame,
    official_pas: pl.DataFrame,
    *,
    fields: Iterable[str] = ("batter_side", "pitcher_hand"),
) -> pl.DataFrame:
    """Compare unresolved pitch fields with official sequence-level matchup data.

    Results are emitted once per ``game_pk + at_bat_index + field`` rather than
    once per pitch so a five-pitch plate appearance cannot look like five pieces
    of independent adjudication evidence.

    Status values:
    - ``official_unavailable``: no true-PA official row or official field is null;
    - ``source_candidate_ambiguous``: at least one source snapshot itself has
      multiple non-null candidates for the field;
    - ``official_matches_one_source_snapshot``;
    - ``official_matches_multiple_source_snapshots``;
    - ``official_matches_all_source_snapshots``;
    - ``official_matches_no_source_snapshot``.

    This function reports evidence only. It never mutates the source-only
    consensus view or silently fills a conflict.
    """

    requested_fields = tuple(dict.fromkeys(str(field) for field in fields))
    unsupported = sorted(set(requested_fields) - SUPPORTED_OFFICIAL_PA_FIELDS)
    if unsupported:
        raise ValueError(f"unsupported official PA adjudication fields: {unsupported}")

    observation_required = {
        "source_snapshot_id",
        "game_pk",
        "at_bat_index",
        *requested_fields,
    }
    missing_observation = sorted(observation_required - set(observations.columns))
    if missing_observation:
        raise ValueError(
            f"pitch observations missing adjudication columns: {missing_observation}"
        )
    conflict_required = {"game_pk", "at_bat_index", "conflict_fields"}
    missing_conflict = sorted(conflict_required - set(resolved_conflicts.columns))
    if missing_conflict:
        raise ValueError(
            f"resolved conflicts missing adjudication columns: {missing_conflict}"
        )

    official = _normalise_official_pas(official_pas)
    official_duplicates = (
        official.group_by(list(SEQUENCE_KEY)).len().filter(pl.col("len") > 1)
    )
    if not official_duplicates.is_empty():
        raise ValueError("official PA evidence contains duplicate sequence keys")
    official_map = {
        (int(row["game_pk"]), int(row["at_bat_index"])): row
        for row in official.to_dicts()
    }

    target_pairs: set[tuple[int, int, str]] = set()
    for row in resolved_conflicts.select(
        ["game_pk", "at_bat_index", "conflict_fields"]
    ).to_dicts():
        for field in row.get("conflict_fields") or []:
            if field in requested_fields:
                target_pairs.add(
                    (int(row["game_pk"]), int(row["at_bat_index"]), str(field))
                )

    rows: list[dict[str, Any]] = []
    observation_rows = observations.to_dicts()
    for game_pk, at_bat_index, field in sorted(target_pairs):
        candidates_by_snapshot: dict[str, list[str]] = {}
        for observation in observation_rows:
            if (
                int(observation["game_pk"]) != game_pk
                or int(observation["at_bat_index"]) != at_bat_index
            ):
                continue
            value = observation.get(field)
            if value is None:
                continue
            snapshot_id = str(observation["source_snapshot_id"])
            values = candidates_by_snapshot.setdefault(snapshot_id, [])
            text = str(value)
            if text not in values:
                values.append(text)

        for values in candidates_by_snapshot.values():
            values.sort()
        candidates_by_snapshot = dict(sorted(candidates_by_snapshot.items()))

        official_row = official_map.get((game_pk, at_bat_index))
        official_value = None if official_row is None else official_row.get(field)
        ambiguous_snapshots = sorted(
            snapshot_id
            for snapshot_id, values in candidates_by_snapshot.items()
            if len(values) > 1
        )
        matching_snapshots: list[str] = []
        if official_value is not None and not ambiguous_snapshots:
            official_text = str(official_value)
            matching_snapshots = sorted(
                snapshot_id
                for snapshot_id, values in candidates_by_snapshot.items()
                if values == [official_text]
            )

        if official_value is None:
            status = "official_unavailable"
        elif ambiguous_snapshots:
            status = "source_candidate_ambiguous"
        elif not matching_snapshots:
            status = "official_matches_no_source_snapshot"
        elif len(matching_snapshots) == len(candidates_by_snapshot):
            status = "official_matches_all_source_snapshots"
        elif len(matching_snapshots) == 1:
            status = "official_matches_one_source_snapshot"
        else:
            status = "official_matches_multiple_source_snapshots"

        rows.append(
            {
                "game_pk": game_pk,
                "at_bat_index": at_bat_index,
                "field": field,
                "official_value": None if official_value is None else str(official_value),
                "official_sequence_available": official_row is not None,
                "source_snapshot_count_with_non_null_candidate": len(
                    candidates_by_snapshot
                ),
                "source_candidates_by_snapshot": candidates_by_snapshot,
                "ambiguous_source_snapshot_ids": ambiguous_snapshots,
                "matching_source_snapshot_ids": matching_snapshots,
                "status": status,
            }
        )

    if not rows:
        return pl.DataFrame(
            schema={
                "game_pk": pl.Int64,
                "at_bat_index": pl.Int64,
                "field": pl.String,
                "official_value": pl.String,
                "official_sequence_available": pl.Boolean,
                "source_snapshot_count_with_non_null_candidate": pl.Int64,
                "source_candidates_by_snapshot": pl.Object,
                "ambiguous_source_snapshot_ids": pl.List(pl.String),
                "matching_source_snapshot_ids": pl.List(pl.String),
                "status": pl.String,
            }
        )
    return pl.DataFrame(rows).sort(["game_pk", "at_bat_index", "field"])
