"""Pure comparison helpers for certification experiments."""

from __future__ import annotations

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


def compare_pitch_source_to_official_pas(
    source: pl.DataFrame,
    official: pl.DataFrame,
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
        "description_mismatch_pa_count": len(description_mismatches),
        "description_mismatch_examples": description_mismatches[:10],
        "official_event_type_nonblank_pa_count": official_event_type_nonblank,
        "official_event_nonblank_pa_count": official_event_nonblank,
        "source_events_nonblank_pitch_row_count": source_event_nonblank,
        "per_game": per_game,
    }
