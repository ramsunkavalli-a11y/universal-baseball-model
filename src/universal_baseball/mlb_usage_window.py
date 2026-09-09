"""Official MLB date-range workload projections."""

from __future__ import annotations

from typing import Any

import polars as pl


MLB_USAGE_WINDOW_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "workload": pl.Float64,
    "games": pl.Int64,
    "starts": pl.Int64,
}


def project_mlb_usage_date_range_payload(
    payload: dict[str, Any], *, group: str
) -> pl.DataFrame:
    """Aggregate one complete StatsAPI byDateRange response to player grain."""

    if group not in {"hitting", "pitching"}:
        raise ValueError("MLB usage group must be hitting or pitching")
    blocks = payload.get("stats")
    if not isinstance(blocks, list) or len(blocks) != 1:
        raise ValueError("official MLB date-range stats require one result block")
    block = blocks[0]
    splits = block.get("splits")
    total = block.get("totalSplits")
    if not isinstance(splits, list) or total is None or int(total) != len(splits):
        raise ValueError("official MLB date-range stats are missing or paginated")
    rows: list[dict[str, object]] = []
    for split in splits:
        if not isinstance(split, dict):
            raise ValueError("official MLB date-range split must be an object")
        player_id = (split.get("player") or {}).get("id")
        stat = split.get("stat") or {}
        if player_id is None:
            raise ValueError("official MLB date-range stat lacks player identity")
        rows.append(
            {
                "player_id": int(player_id),
                "workload": float(
                    stat.get("plateAppearances", 0)
                    if group == "hitting"
                    else stat.get("battersFaced", 0)
                ),
                "games": int(stat.get("gamesPlayed", 0)),
                "starts": (
                    int(stat.get("gamesStarted", 0)) if group == "pitching" else 0
                ),
            }
        )
    frame = (
        pl.DataFrame(rows, schema=MLB_USAGE_WINDOW_SCHEMA)
        if rows
        else pl.DataFrame(schema=MLB_USAGE_WINDOW_SCHEMA)
    )
    result = (
        frame.group_by("player_id")
        .agg(
            pl.col("workload").sum(),
            pl.col("games").sum(),
            pl.col("starts").sum(),
        )
        .cast(MLB_USAGE_WINDOW_SCHEMA, strict=True)
        .sort("player_id")
    )
    if result.filter(
        (pl.col("player_id") <= 0)
        | (pl.col("workload") < 0)
        | (pl.col("games") < 0)
        | (pl.col("starts") < 0)
        | (pl.col("starts") > pl.col("games"))
    ).height:
        raise ValueError("official MLB date-range stats contain invalid usage")
    return result
