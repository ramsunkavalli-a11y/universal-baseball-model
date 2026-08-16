"""Narrow official participant authority for residual-triggered contact games.

Contact participant adjudication needs only the top-level Stats API
``allPlays.matchup.batter`` identity at ``game + atBatIndex`` grain. It does not
need pitch-event parsing, pitch type codes, batted-ball data, or even true-PA
classification. Keeping this projector narrow has two advantages:

- irregular historical MiLB pitch-event fields cannot break participant repair;
- pitch-bearing play sequences that are not true PAs can still receive the
  official matchup batter, consistent with the project's canonical
  ``play_sequence -> 0..N pitches`` grain.

Exact HTTP bytes are captured by the caller through ``official_capture``. This
module performs only the deterministic payload projection.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import polars as pl

from universal_baseball.contact_identity_overlay import OFFICIAL_SEQUENCE_AUTHORITY_SCHEMA


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return int(numeric) if numeric.is_integer() else None


def project_official_allplays_participant_authority(
    game_pk: int,
    payload: Mapping[str, Any],
) -> pl.DataFrame:
    """Project unique top-level matchup batter identity for every allPlays row.

    Rows lacking ``atBatIndex`` or batter ID are not useful authority and are
    excluded. Duplicate sequence keys must agree on batter identity or the game
    fails closed rather than selecting one observation arbitrarily.
    """

    rows: list[dict[str, int]] = []
    all_plays = payload.get("allPlays") or []
    if not isinstance(all_plays, list):
        all_plays = []
    for raw_play in all_plays:
        play = _mapping(raw_play)
        matchup = _mapping(play.get("matchup"))
        batter = _mapping(matchup.get("batter"))
        at_bat_index = _int(play.get("atBatIndex"))
        batter_id = _int(batter.get("id"))
        if at_bat_index is None or batter_id is None:
            continue
        rows.append(
            {
                "source_game_pk": int(game_pk),
                "source_at_bat_index": at_bat_index,
                "official_batter_id": batter_id,
            }
        )

    if not rows:
        return pl.DataFrame(schema=OFFICIAL_SEQUENCE_AUTHORITY_SCHEMA)
    frame = pl.DataFrame(rows, schema=OFFICIAL_SEQUENCE_AUTHORITY_SCHEMA, strict=False)
    conflicts = (
        frame.group_by(["source_game_pk", "source_at_bat_index"])
        .agg(pl.col("official_batter_id").n_unique().alias("batter_id_count"))
        .filter(pl.col("batter_id_count") > 1)
    )
    if not conflicts.is_empty():
        raise ValueError(
            f"official allPlays contains conflicting matchup batters for game_pk={game_pk}"
        )
    return frame.unique(
        subset=["source_game_pk", "source_at_bat_index"],
        maintain_order=False,
    ).sort(["source_game_pk", "source_at_bat_index"])
