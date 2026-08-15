"""Known, tested schema aliases for the reusable armstjc MiLB source.

Raw source files are never rewritten. These helpers create a standardized view
for downstream certification and, later, normalization. Aliases are deliberately
small and explicit so upstream drift becomes visible instead of being hidden by
fuzzy column matching.
"""

from __future__ import annotations

from typing import Any

import polars as pl


KNOWN_COLUMN_ALIASES: dict[str, str] = {
    # Older armstjc releases use the upstream misspelling. Recent releases use
    # the corrected spellings.
    "leauge_id": "league_id",
    "leauge_name": "league_name",
}


def normalize_known_schema_aliases(
    frame: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Apply only explicitly certified source-column aliases.

    If an old and new spelling coexist, their overlapping nonblank values must
    agree. The standardized view then prefers the canonical column and fills its
    blanks from the alias before dropping the alias. A disagreement is a hard
    error because silently choosing one would hide source drift.
    """

    result = frame
    actions: list[dict[str, Any]] = []

    for alias, canonical in KNOWN_COLUMN_ALIASES.items():
        if alias not in result.columns:
            continue

        if canonical not in result.columns:
            result = result.rename({alias: canonical})
            actions.append(
                {
                    "alias": alias,
                    "canonical": canonical,
                    "action": "renamed",
                    "overlap_conflict_count": 0,
                }
            )
            continue

        alias_text = pl.col(alias).cast(pl.String).str.strip_chars()
        canonical_text = pl.col(canonical).cast(pl.String).str.strip_chars()
        both_present = (
            alias_text.is_not_null()
            & (alias_text != "")
            & canonical_text.is_not_null()
            & (canonical_text != "")
        )
        conflict_count = int(
            result.select(
                (both_present & (alias_text != canonical_text))
                .sum()
                .alias("conflicts")
            ).item()
        )
        if conflict_count:
            raise ValueError(
                f"source columns {alias!r} and {canonical!r} disagree in "
                f"{conflict_count} overlapping nonblank rows"
            )

        result = result.with_columns(
            pl.when(
                pl.col(canonical).is_null()
                | (pl.col(canonical).cast(pl.String).str.strip_chars() == "")
            )
            .then(pl.col(alias))
            .otherwise(pl.col(canonical))
            .alias(canonical)
        ).drop(alias)
        actions.append(
            {
                "alias": alias,
                "canonical": canonical,
                "action": "coalesced_and_dropped_alias",
                "overlap_conflict_count": 0,
            }
        )

    return result, {
        "known_aliases": KNOWN_COLUMN_ALIASES,
        "actions": actions,
        "action_count": len(actions),
    }
