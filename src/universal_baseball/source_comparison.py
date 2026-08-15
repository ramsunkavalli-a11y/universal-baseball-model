"""Pure comparison helpers for certification experiments."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

import polars as pl


def select_diverse_game_ids(frame: pl.DataFrame, limit: int = 5) -> list[int]:
    """Select game IDs spread across the observed source date range."""

    if limit <= 0 or "game_pk" not in frame.columns:
        return []

    columns = ["game_pk"]
    if "game_date" in frame.columns:
        columns.append("game_date")

    games = frame.select(columns).unique()
    if "game_date" in games.columns:
        games = games.sort(["game_date", "game_pk"])
    else:
        games = games.sort("game_pk")

    values = games.get_column("game_pk").drop_nulls().to_list()
    if len(values) <= limit:
        return [int(value) for value in values]

    if limit == 1:
        return [int(values[0])]

    indexes = {
        round(i * (len(values) - 1) / (limit - 1)) for i in range(limit)
    }
    return [int(values[index]) for index in sorted(indexes)]


def _text_present(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _normalize_pitch_number(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return None


def _event_public_dict(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_index": row.get("event_index"),
        "pitch_number": _normalize_pitch_number(row.get("pitch_number")),
        "code": row.get("code"),
        "event": row.get("event"),
        "event_type": row.get("event_type"),
        "description": row.get("description"),
        "has_pitch_data": row.get("has_pitch_data"),
        "pitch_type_code": row.get("pitch_type_code"),
    }


def _diagnose_pitch_mismatches(
    source_exact_unique: pl.DataFrame,
    official_pitch_events: pl.DataFrame,
    pitch_mismatches: list[dict[str, Any]],
) -> dict[str, Any]:
    """Explain pitch-count disagreements using official pitch-event metadata."""

    if official_pitch_events.is_empty():
        return {
            "available": False,
            "reason": "official pitch-event frame was empty",
        }

    required = {"game_pk", "at_bat_number", "pitch_number"}
    missing = sorted(required - set(official_pitch_events.columns))
    if missing:
        return {
            "available": False,
            "reason": f"official pitch-event frame missing columns: {missing}",
        }

    source_numbers: dict[tuple[str, str], set[int]] = defaultdict(set)
    for row in source_exact_unique.select(
        ["game_pk", "at_bat_number", "pitch_number"]
    ).to_dicts():
        number = _normalize_pitch_number(row.get("pitch_number"))
        if number is not None:
            source_numbers[(str(row["game_pk"]), str(row["at_bat_number"]))].add(number)

    official_events: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in official_pitch_events.to_dicts():
        key = (str(row["game_pk"]), str(row["at_bat_number"]))
        official_events[key].append(row)

    class_counts: Counter[str] = Counter()
    missing_code_counts: Counter[str] = Counter()
    missing_event_type_counts: Counter[str] = Counter()
    missing_has_pitch_data_counts: Counter[str] = Counter()
    details: list[dict[str, Any]] = []

    for mismatch in pitch_mismatches:
        key = (str(mismatch["game_pk"]), str(mismatch["at_bat_number"]))
        source_set = source_numbers.get(key, set())
        events = official_events.get(key, [])
        official_set = {
            number
            for number in (_normalize_pitch_number(row.get("pitch_number")) for row in events)
            if number is not None
        }
        missing_numbers = sorted(official_set - source_set)
        extra_numbers = sorted(source_set - official_set)
        missing_events = [
            _event_public_dict(row)
            for row in events
            if _normalize_pitch_number(row.get("pitch_number")) in missing_numbers
        ]

        for event in missing_events:
            code = event.get("code")
            event_type = event.get("event_type")
            missing_code_counts[str(code) if code is not None else "<null>"] += 1
            missing_event_type_counts[
                str(event_type) if event_type is not None else "<null>"
            ] += 1
            missing_has_pitch_data_counts[str(bool(event.get("has_pitch_data")))] += 1

        if missing_numbers and not extra_numbers and missing_events:
            if all(event.get("code") == "AC" for event in missing_events):
                classification = "source_skips_automatic_strike"
            elif all(not bool(event.get("has_pitch_data")) for event in missing_events):
                classification = "source_skips_nonphysical_pitch_event"
            else:
                classification = "source_missing_other_official_pitch_event"
        elif extra_numbers and not missing_numbers:
            classification = "source_has_extra_pitch_number"
        elif missing_numbers and extra_numbers:
            classification = "pitch_number_sets_disagree_both_directions"
        else:
            classification = "count_mismatch_without_pitch_number_difference"

        class_counts[classification] += 1
        details.append(
            {
                **mismatch,
                "classification": classification,
                "source_pitch_numbers": sorted(source_set),
                "official_pitch_numbers": sorted(official_set),
                "missing_source_pitch_numbers": missing_numbers,
                "extra_source_pitch_numbers": extra_numbers,
                "official_pitch_event_row_count": len(events),
                "missing_official_pitch_events": missing_events,
            }
        )

    return {
        "available": True,
        "mismatch_class_counts": dict(sorted(class_counts.items())),
        "missing_official_pitch_event_code_counts": dict(
            sorted(missing_code_counts.items())
        ),
        "missing_official_pitch_event_type_counts": dict(
            sorted(missing_event_type_counts.items())
        ),
        "missing_official_pitch_event_has_pitch_data_counts": dict(
            sorted(missing_has_pitch_data_counts.items())
        ),
        "mismatch_details": details,
    }


def compare_pitch_source_to_official_pas(
    source: pl.DataFrame,
    official: pl.DataFrame,
    official_pitch_events: pl.DataFrame | None = None,
) -> dict[str, Any]:
    """Compare deduplicated pitch rows with official PA rows.

    Exact source duplicates are removed *for comparison only*. The raw source is
    never mutated or silently promoted. The goal is to learn whether the unique
    pitch rows underneath an upstream duplication defect still align with the
    official PA structure.
    """

    required_source = {"game_pk", "at_bat_number", "pitch_number"}
    missing_source = sorted(required_source - set(source.columns))
    if missing_source:
        raise ValueError(f"source missing required columns: {missing_source}")

    required_official = {
        "game_pk",
        "at_bat_number",
        "official_pitch_count",
        "event_type",
        "event",
        "description",
    }
    missing_official = sorted(required_official - set(official.columns))
    if missing_official:
        raise ValueError(f"official frame missing required columns: {missing_official}")

    source_exact_unique = source.unique()

    source_pa_rows = (
        source_exact_unique.group_by(["game_pk", "at_bat_number"])
        .agg(
            [
                pl.len().alias("source_pitch_count"),
                pl.col("description").drop_nulls().n_unique().alias("description_variants")
                if "description" in source_exact_unique.columns
                else pl.lit(0).alias("description_variants"),
                pl.col("description").drop_nulls().first().alias("source_description")
                if "description" in source_exact_unique.columns
                else pl.lit(None, dtype=pl.String).alias("source_description"),
            ]
        )
        .to_dicts()
    )

    source_map = {
        (str(row["game_pk"]), str(row["at_bat_number"])): row
        for row in source_pa_rows
    }
    official_map = {
        (str(row["game_pk"]), str(row["at_bat_number"])): row
        for row in official.to_dicts()
    }

    source_keys = set(source_map)
    official_keys = set(official_map)
    shared = source_keys & official_keys

    pitch_mismatches: list[dict[str, Any]] = []
    description_mismatches: list[dict[str, Any]] = []

    for key in sorted(shared):
        source_row = source_map[key]
        official_row = official_map[key]

        source_pitch_count = int(source_row["source_pitch_count"])
        official_pitch_count = int(official_row["official_pitch_count"])
        if source_pitch_count != official_pitch_count:
            pitch_mismatches.append(
                {
                    "game_pk": key[0],
                    "at_bat_number": key[1],
                    "source_pitch_count": source_pitch_count,
                    "official_pitch_count": official_pitch_count,
                }
            )

        source_description = source_row.get("source_description")
        official_description = official_row.get("description")
        if (
            _text_present(source_description)
            and _text_present(official_description)
            and source_description != official_description
        ):
            description_mismatches.append(
                {
                    "game_pk": key[0],
                    "at_bat_number": key[1],
                    "source_description": source_description,
                    "official_description": official_description,
                }
            )

    official_event_type_nonblank = sum(
        1 for row in official_map.values() if _text_present(row.get("event_type"))
    )
    official_event_nonblank = sum(
        1 for row in official_map.values() if _text_present(row.get("event"))
    )

    source_event_nonblank = None
    if "events" in source_exact_unique.columns:
        source_event_nonblank = int(
            source_exact_unique.select(
                (
                    pl.col("events").is_not_null()
                    & (pl.col("events").cast(pl.String).str.strip_chars() != "")
                )
                .sum()
                .alias("nonblank")
            ).item()
        )

    game_ids = sorted({key[0] for key in source_keys | official_keys}, key=int)
    per_game: list[dict[str, Any]] = []
    for game_id in game_ids:
        source_game_keys = {key for key in source_keys if key[0] == game_id}
        official_game_keys = {key for key in official_keys if key[0] == game_id}
        shared_game = source_game_keys & official_game_keys
        game_pitch_mismatches = [
            row for row in pitch_mismatches if row["game_pk"] == game_id
        ]
        per_game.append(
            {
                "game_pk": game_id,
                "source_pa_count": len(source_game_keys),
                "official_pa_count": len(official_game_keys),
                "shared_pa_count": len(shared_game),
                "source_only_pa_count": len(source_game_keys - official_game_keys),
                "official_only_pa_count": len(official_game_keys - source_game_keys),
                "pitch_count_mismatch_pa_count": len(game_pitch_mismatches),
            }
        )

    pitch_mismatch_diagnosis = None
    if official_pitch_events is not None:
        pitch_mismatch_diagnosis = _diagnose_pitch_mismatches(
            source_exact_unique,
            official_pitch_events,
            pitch_mismatches,
        )

    return {
        "source_rows_raw": int(source.height),
        "source_rows_after_exact_dedup_for_comparison": int(source_exact_unique.height),
        "official_pa_rows": int(official.height),
        "source_pa_count": len(source_keys),
        "official_pa_count": len(official_keys),
        "shared_pa_count": len(shared),
        "source_only_pa_count": len(source_keys - official_keys),
        "official_only_pa_count": len(official_keys - source_keys),
        "pitch_count_mismatch_pa_count": len(pitch_mismatches),
        "pitch_count_mismatch_examples": pitch_mismatches[:25],
        "pitch_count_mismatch_diagnosis": pitch_mismatch_diagnosis,
        "description_mismatch_pa_count": len(description_mismatches),
        "description_mismatch_examples": description_mismatches[:10],
        "official_event_type_nonblank_pa_count": official_event_type_nonblank,
        "official_event_nonblank_pa_count": official_event_nonblank,
        "source_events_nonblank_pitch_row_count": source_event_nonblank,
        "per_game": per_game,
    }
