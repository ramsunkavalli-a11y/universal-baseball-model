"""Reconcile official play-by-play outcomes to official boxscore totals.

The first purpose of this module is not to create a clever batting metric. It is
to prove that the narrow PA projection preserves ordinary baseball accounting
before any modeling depends on it.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import polars as pl

from universal_baseball.event_types import (
    HIT_EVENT_TYPES_FROM_MLB,
    KNOWN_EVENT_TYPES,
    PLATE_APPEARANCE_EVENT_TYPES,
)


HIT_EVENT_TYPES = HIT_EVENT_TYPES_FROM_MLB
WALK_EVENT_TYPES = frozenset({"walk", "intent_walk"})
STRIKEOUT_EVENT_TYPES = frozenset(
    {
        "strikeout",
        "strike_out",
        "strikeout_double_play",
        "strikeout_triple_play",
    }
)
SAC_BUNT_EVENT_TYPES = frozenset({"sac_bunt", "sac_bunt_double_play"})
SAC_FLY_EVENT_TYPES = frozenset({"sac_fly", "sac_fly_double_play"})
CATCHER_INTERFERENCE_EVENT_TYPES = frozenset({"catcher_interf"})

RECONCILIATION_STATS = (
    "plate_appearances",
    "at_bats",
    "hits",
    "doubles",
    "triples",
    "home_runs",
    "base_on_balls",
    "intentional_walks",
    "hit_by_pitch",
    "strikeouts",
    "sac_bunts",
    "sac_flies",
    "catchers_interference",
)

DIAGNOSTIC_COLUMNS = (
    "null_event_type_count",
    "unknown_event_type_count",
    "known_non_pa_result_count",
    "non_at_bat_result_count",
)


def _membership_sum(column: str, values: frozenset[str], alias: str) -> pl.Expr:
    return pl.col(column).is_in(list(values)).fill_null(False).sum().alias(alias)


def aggregate_pa_batting(pa_frame: pl.DataFrame) -> pl.DataFrame:
    """Aggregate play records into home/away batting lines.

    The Stats API's ``allPlays`` can contain a play whose *result* is a runner or
    advisory event (for example a pickoff or caught stealing). We therefore do
    not equate one ``allPlays`` row with one PA. Plate appearances are selected
    using the versioned MLB ``eventTypes`` PA flags in :mod:`event_types`.

    At-bats are reconstructed from the standard accounting identity
    ``PA - BB - HBP - SH - SF - CI``. The component counts and excluded/unknown
    result counts remain visible so a mismatch can be diagnosed rather than
    hidden inside the derived AB value.
    """

    required = {"game_pk", "batting_side", "event_type"}
    missing = sorted(required - set(pa_frame.columns))
    if missing:
        raise ValueError(f"PA frame missing required columns: {missing}")

    if pa_frame.is_empty():
        return pl.DataFrame(
            schema={
                "game_pk": pl.String,
                "batting_side": pl.String,
                **{stat: pl.Int64 for stat in RECONCILIATION_STATS},
                **{column: pl.Int64 for column in DIAGNOSTIC_COLUMNS},
            }
        )

    working = pa_frame.filter(pl.col("batting_side").is_in(["away", "home"]))
    if working.is_empty():
        return aggregate_pa_batting(pa_frame.head(0))

    is_nonblank = (
        pl.col("event_type").is_not_null()
        & (pl.col("event_type").cast(pl.String).str.strip_chars() != "")
    )
    is_known = pl.col("event_type").is_in(list(KNOWN_EVENT_TYPES)).fill_null(False)
    is_pa = pl.col("event_type").is_in(list(PLATE_APPEARANCE_EVENT_TYPES)).fill_null(False)

    aggregations: list[pl.Expr] = [
        is_pa.sum().alias("plate_appearances"),
        _membership_sum("event_type", HIT_EVENT_TYPES, "hits"),
        _membership_sum("event_type", frozenset({"double"}), "doubles"),
        _membership_sum("event_type", frozenset({"triple"}), "triples"),
        _membership_sum("event_type", frozenset({"home_run"}), "home_runs"),
        _membership_sum("event_type", WALK_EVENT_TYPES, "base_on_balls"),
        _membership_sum(
            "event_type", frozenset({"intent_walk"}), "intentional_walks"
        ),
        _membership_sum("event_type", frozenset({"hit_by_pitch"}), "hit_by_pitch"),
        _membership_sum("event_type", STRIKEOUT_EVENT_TYPES, "strikeouts"),
        _membership_sum("event_type", SAC_BUNT_EVENT_TYPES, "sac_bunts"),
        _membership_sum("event_type", SAC_FLY_EVENT_TYPES, "sac_flies"),
        _membership_sum(
            "event_type",
            CATCHER_INTERFERENCE_EVENT_TYPES,
            "catchers_interference",
        ),
        (~is_nonblank).sum().alias("null_event_type_count"),
        (is_nonblank & ~is_known).sum().alias("unknown_event_type_count"),
        (is_known & ~is_pa).sum().alias("known_non_pa_result_count"),
    ]

    if "result_type" in working.columns:
        aggregations.append(
            (pl.col("result_type").fill_null("") != "atBat")
            .sum()
            .alias("non_at_bat_result_count")
        )
    else:
        aggregations.append(pl.lit(0).sum().alias("non_at_bat_result_count"))

    result = working.group_by(["game_pk", "batting_side"]).agg(aggregations)
    result = result.with_columns(
        (
            pl.col("plate_appearances")
            - pl.col("base_on_balls")
            - pl.col("hit_by_pitch")
            - pl.col("sac_bunts")
            - pl.col("sac_flies")
            - pl.col("catchers_interference")
        ).alias("at_bats")
    )

    return result.select(
        [
            "game_pk",
            "batting_side",
            *RECONCILIATION_STATS,
            *DIAGNOSTIC_COLUMNS,
        ]
    ).sort(["game_pk", "batting_side"])


def profile_pa_event_types(pa_frame: pl.DataFrame) -> dict[str, Any]:
    """Return observed structured result vocabulary and official PA semantics."""

    if "event_type" not in pa_frame.columns:
        return {"available": False, "reason": "event_type column missing"}

    counts: Counter[str] = Counter()
    pa_counts: Counter[str] = Counter()
    known_non_pa_counts: Counter[str] = Counter()
    unknown_counts: Counter[str] = Counter()
    null_count = 0

    for value in pa_frame.get_column("event_type").to_list():
        if value is None or str(value).strip() == "":
            null_count += 1
            continue
        code = str(value)
        counts[code] += 1
        if code in PLATE_APPEARANCE_EVENT_TYPES:
            pa_counts[code] += 1
        elif code in KNOWN_EVENT_TYPES:
            known_non_pa_counts[code] += 1
        else:
            unknown_counts[code] += 1

    return {
        "available": True,
        "event_type_snapshot": "MLB /eventTypes retrieved 2026-08-15",
        "null_or_blank_count": null_count,
        "unknown_counts": dict(sorted(unknown_counts.items())),
        "known_non_pa_counts": dict(sorted(known_non_pa_counts.items())),
        "plate_appearance_counts": dict(sorted(pa_counts.items())),
        "counts": dict(sorted(counts.items())),
    }


def compare_batting_lines(
    derived: pl.DataFrame,
    official: pl.DataFrame,
) -> dict[str, Any]:
    """Compare derived PA batting lines with official team boxscore totals."""

    required = {"game_pk", "batting_side", *RECONCILIATION_STATS}
    missing_derived = sorted(required - set(derived.columns))
    missing_official = sorted(required - set(official.columns))
    if missing_derived:
        raise ValueError(f"derived frame missing columns: {missing_derived}")
    if missing_official:
        raise ValueError(f"official frame missing columns: {missing_official}")

    derived_map = {
        (str(row["game_pk"]), str(row["batting_side"])): row
        for row in derived.to_dicts()
    }
    official_map = {
        (str(row["game_pk"]), str(row["batting_side"])): row
        for row in official.to_dicts()
    }

    keys = sorted(
        set(derived_map) | set(official_map),
        key=lambda item: (int(item[0]), item[1]),
    )
    rows: list[dict[str, Any]] = []
    stat_mismatch_counts: Counter[str] = Counter()
    missing_derived_keys: list[dict[str, str]] = []
    missing_official_keys: list[dict[str, str]] = []

    for key in keys:
        derived_row = derived_map.get(key)
        official_row = official_map.get(key)
        if derived_row is None:
            missing_derived_keys.append({"game_pk": key[0], "batting_side": key[1]})
            continue
        if official_row is None:
            missing_official_keys.append({"game_pk": key[0], "batting_side": key[1]})
            continue

        differences: dict[str, int | None] = {}
        mismatched_stats: list[str] = []
        for stat in RECONCILIATION_STATS:
            derived_value = derived_row.get(stat)
            official_value = official_row.get(stat)
            if derived_value is None or official_value is None:
                difference = None
                is_mismatch = derived_value != official_value
            else:
                difference = int(derived_value) - int(official_value)
                is_mismatch = difference != 0

            if is_mismatch:
                stat_mismatch_counts[stat] += 1
                mismatched_stats.append(stat)
            differences[stat] = difference

        rows.append(
            {
                "game_pk": key[0],
                "batting_side": key[1],
                "mismatched_stats": mismatched_stats,
                "differences_derived_minus_official": differences,
                "derived": {
                    stat: derived_row.get(stat) for stat in RECONCILIATION_STATS
                },
                "official": {
                    stat: official_row.get(stat) for stat in RECONCILIATION_STATS
                },
                **{
                    column: derived_row.get(column)
                    for column in DIAGNOSTIC_COLUMNS
                },
            }
        )

    mismatch_rows = [row for row in rows if row["mismatched_stats"]]
    unknown_event_rows = [
        row for row in rows if int(row.get("unknown_event_type_count") or 0) > 0
    ]
    null_event_rows = [
        row for row in rows if int(row.get("null_event_type_count") or 0) > 0
    ]

    return {
        "derived_line_count": len(derived_map),
        "official_line_count": len(official_map),
        "shared_line_count": len(rows),
        "exact_match_line_count": len(rows) - len(mismatch_rows),
        "mismatch_line_count": len(mismatch_rows),
        "missing_derived_lines": missing_derived_keys,
        "missing_official_lines": missing_official_keys,
        "stat_mismatch_counts": dict(sorted(stat_mismatch_counts.items())),
        "mismatch_rows": mismatch_rows,
        "unknown_event_type_line_count": len(unknown_event_rows),
        "null_event_type_line_count": len(null_event_rows),
        "all_rows": rows,
        "all_reconciled": (
            not mismatch_rows
            and not missing_derived_keys
            and not missing_official_keys
        ),
        "certification_clean": (
            not mismatch_rows
            and not missing_derived_keys
            and not missing_official_keys
            and not unknown_event_rows
            and not null_event_rows
        ),
    }
