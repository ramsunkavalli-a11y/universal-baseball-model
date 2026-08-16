#!/usr/bin/env python
"""Certify the MLB Stats API bulk season-hitting endpoint as outcome backbone.

The affiliated MiLB Performance layer uses certified season-player aggregates
for PA/BB/HBP/K rather than reconstructing standard totals from pitch rows. MLB
should follow the same architecture. The Stats API ``/stats`` endpoint supports
``playerPool=ALL`` plus pagination, allowing one/few bulk requests instead of a
per-player loop.

This audit checks completed 2024 regular-season hitting data for:

- complete pagination;
- one aggregate split per MLBAM player-season;
- presence and integer-like typing of the standard outcome/count fields needed
  by the Performance layer;
- basic PA accounting residuals retained explicitly rather than assumed zero;
- a deterministic sample reconciled to Savant terminal-event counts on the
  already-certified source dates.
"""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

import polars as pl
import requests

from universal_baseball.savant import (
    fetch_savant_csv,
    project_savant_performance_rows,
    read_savant_csv_bytes,
)


REPORT_DIR = Path("reports/generated/mlb-bulk-season-stats")
STATS_URL = "https://statsapi.mlb.com/api/v1/stats"
SEASON = 2024
PAGE_LIMIT = 500
AUDIT_DATES = (date(2024, 4, 15), date(2024, 6, 15), date(2024, 9, 15))

REQUIRED_STAT_FIELDS = (
    "plateAppearances",
    "atBats",
    "baseOnBalls",
    "intentionalWalks",
    "hitByPitch",
    "strikeOuts",
    "sacBunts",
    "sacFlies",
)


def _int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    numeric = float(str(value))
    if not numeric.is_integer():
        raise ValueError(f"expected integer-like count, got {value!r}")
    return int(numeric)


def _fetch_pages() -> tuple[list[Mapping[str, Any]], list[dict[str, Any]]]:
    rows: list[Mapping[str, Any]] = []
    captures: list[dict[str, Any]] = []
    offset = 0
    session = requests.Session()
    try:
        while True:
            params = {
                "stats": "season",
                "group": "hitting",
                "season": SEASON,
                "sportIds": 1,
                "playerPool": "ALL",
                "gameType": "R",
                "limit": PAGE_LIMIT,
                "offset": offset,
            }
            response = session.get(STATS_URL, params=params, timeout=120)
            response.raise_for_status()
            content = response.content
            payload = response.json()
            stats_groups = payload.get("stats") or []
            if len(stats_groups) != 1:
                raise RuntimeError(
                    f"expected one stats group, found {len(stats_groups)} at offset {offset}"
                )
            group = stats_groups[0]
            splits = group.get("splits") or []
            rows.extend(splits)
            captures.append(
                {
                    "offset": offset,
                    "requested_limit": PAGE_LIMIT,
                    "returned_split_count": len(splits),
                    "response_sha256": sha256(content).hexdigest(),
                    "response_byte_count": len(content),
                    "total_splits": group.get("totalSplits"),
                }
            )
            total = group.get("totalSplits")
            if total is not None:
                total = int(total)
                if len(rows) >= total:
                    break
            if len(splits) < PAGE_LIMIT:
                break
            if not splits:
                break
            offset += len(splits)
            if offset > 5000:
                raise RuntimeError("bulk stats pagination exceeded safety bound")
    finally:
        session.close()
    return rows, captures


def _project(rows: list[Mapping[str, Any]]) -> pl.DataFrame:
    projected: list[dict[str, Any]] = []
    missing_required_fields: dict[int, list[str]] = {}
    for split in rows:
        person = split.get("player") or split.get("person") or {}
        stat = split.get("stat") or {}
        player_id = _int(person.get("id"))
        if player_id is None:
            raise RuntimeError("bulk season split lacks MLBAM player ID")
        missing = [field for field in REQUIRED_STAT_FIELDS if field not in stat]
        if missing:
            missing_required_fields[player_id] = missing
        values = {field: _int(stat.get(field)) for field in REQUIRED_STAT_FIELDS}
        projected.append(
            {
                "season": SEASON,
                "player_id": player_id,
                "player_name": str(person.get("fullName") or ""),
                **values,
            }
        )
    if missing_required_fields:
        examples = list(missing_required_fields.items())[:10]
        raise RuntimeError(f"bulk season stats missing required fields: {examples}")
    return pl.DataFrame(projected).with_columns(
        *[
            pl.col(field).cast(pl.Int64, strict=True)
            for field in REQUIRED_STAT_FIELDS
        ],
        pl.col("season").cast(pl.Int64),
        pl.col("player_id").cast(pl.Int64),
    )


def _savant_sample_counts() -> pl.DataFrame:
    frames: list[pl.DataFrame] = []
    for audit_date in AUDIT_DATES:
        capture = fetch_savant_csv(audit_date, audit_date)
        projected = project_savant_performance_rows(
            read_savant_csv_bytes(capture.response_bytes),
            regular_season_only=True,
        )
        frames.append(projected)
    savant = pl.concat(frames, how="vertical_relaxed")
    terminal = savant.filter(pl.col("is_plate_appearance_terminal"))
    return (
        terminal.group_by("batter_mlbam_id")
        .agg(
            pl.len().alias("sample_pa"),
            pl.col("events")
            .is_in(["walk", "intent_walk"])
            .cast(pl.Int64)
            .sum()
            .alias("sample_bb"),
            (pl.col("events") == "hit_by_pitch")
            .cast(pl.Int64)
            .sum()
            .alias("sample_hbp"),
            pl.col("events")
            .is_in(["strikeout", "strikeout_double_play"])
            .cast(pl.Int64)
            .sum()
            .alias("sample_so"),
        )
        .rename({"batter_mlbam_id": "player_id"})
    )


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    rows, captures = _fetch_pages()
    frame = _project(rows)

    duplicates = frame.group_by(["season", "player_id"]).len().filter(pl.col("len") > 1)
    null_counts = frame.select(
        *[pl.col(field).is_null().sum().alias(field) for field in REQUIRED_STAT_FIELDS]
    ).to_dicts()[0]
    negative_counts = {
        field: frame.filter(pl.col(field) < 0).height for field in REQUIRED_STAT_FIELDS
    }

    accounting = frame.with_columns(
        (
            pl.col("atBats")
            + pl.col("baseOnBalls")
            + pl.col("hitByPitch")
            + pl.col("sacBunts")
            + pl.col("sacFlies")
            - pl.col("plateAppearances")
        ).alias("standard_pa_accounting_residual")
    )
    residual_distribution = (
        accounting.group_by("standard_pa_accounting_residual")
        .len()
        .sort("standard_pa_accounting_residual")
        .to_dicts()
    )

    # The three-date Savant sample is not expected to equal season totals. This
    # join is an identity/monotonic sanity check: every sampled batter should
    # exist in the bulk backbone and sample counts cannot exceed completed-season
    # totals.
    sample = _savant_sample_counts()
    sample_join = sample.join(frame, on="player_id", how="left")
    missing_sample_players = sample_join.filter(pl.col("plateAppearances").is_null())
    impossible_sample_counts = sample_join.filter(
        (pl.col("sample_pa") > pl.col("plateAppearances"))
        | (pl.col("sample_bb") > pl.col("baseOnBalls"))
        | (pl.col("sample_hbp") > pl.col("hitByPitch"))
        | (pl.col("sample_so") > pl.col("strikeOuts"))
    )

    accounting.filter(pl.col("standard_pa_accounting_residual") != 0).write_csv(
        REPORT_DIR / "pa_accounting_residuals.csv"
    )
    sample_join.write_csv(REPORT_DIR / "savant_sample_vs_bulk_season.csv")

    payload = {
        "report_schema_version": 1,
        "season": SEASON,
        "endpoint": STATS_URL,
        "request_parameters": {
            "stats": "season",
            "group": "hitting",
            "sportIds": 1,
            "playerPool": "ALL",
            "gameType": "R",
        },
        "pagination": {
            "page_count": len(captures),
            "captures": captures,
            "raw_split_count": len(rows),
        },
        "projection": {
            "player_season_row_count": frame.height,
            "unique_player_count": frame.get_column("player_id").n_unique(),
            "duplicate_player_season_key_count": duplicates.height,
            "null_required_field_counts": null_counts,
            "negative_required_field_counts": negative_counts,
            "pa_accounting_residual_distribution": residual_distribution,
            "nonzero_pa_accounting_residual_player_count": accounting.filter(
                pl.col("standard_pa_accounting_residual") != 0
            ).height,
        },
        "savant_identity_sanity": {
            "sample_player_count": sample.height,
            "sample_player_missing_from_bulk_count": missing_sample_players.height,
            "sample_player_with_count_exceeding_season_total_count": impossible_sample_counts.height,
        },
        "interpretation": (
            "A successful audit certifies the bulk Stats API season endpoint as the MLB "
            "standard outcome-count backbone. Nonzero PA accounting residuals are preserved "
            "because catcher interference and other official PA events are not represented "
            "by the simple AB+BB+HBP+SH+SF identity."
        ),
    }
    (REPORT_DIR / "mlb_bulk_season_stats.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# MLB bulk season-stat source audit — 2024",
        "",
        f"- API pages / raw splits: {len(captures):,} / {len(rows):,}",
        f"- Player-season rows / unique players: {frame.height:,} / {frame.get_column('player_id').n_unique():,}",
        f"- Duplicate player-season keys: {duplicates.height:,}",
        f"- Players with nonzero simple PA-accounting residual: {accounting.filter(pl.col('standard_pa_accounting_residual') != 0).height:,}",
        f"- Savant sample players missing from bulk backbone: {missing_sample_players.height:,}",
        f"- Savant sample players with a sampled count above season total: {impossible_sample_counts.height:,}",
    ]
    summary = "\n".join(lines)
    (REPORT_DIR / "mlb_bulk_season_stats.md").write_text(summary, encoding="utf-8")
    print(summary)

    if duplicates.height:
        raise RuntimeError("bulk season endpoint contains duplicate player-season keys")
    if any(int(value) for value in null_counts.values()):
        raise RuntimeError("bulk season endpoint has null required counts")
    if any(int(value) for value in negative_counts.values()):
        raise RuntimeError("bulk season endpoint has negative required counts")
    if missing_sample_players.height or impossible_sample_counts.height:
        raise RuntimeError("bulk season outcome backbone fails Savant identity/count sanity")
    if frame.height < 500:
        raise RuntimeError("bulk season endpoint returned implausibly few MLB hitters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
