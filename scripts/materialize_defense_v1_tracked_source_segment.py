#!/usr/bin/env python3
"""Materialize one frozen Defense-v1 historical tracking source segment.

Execution-only split of the already-frozen source contract. The query windows,
SportsDataverse version, OAA/framing functions, and MiLB classification semantics
are unchanged from materialize_defense_v1_tracked_source.py.
"""

from __future__ import annotations

import argparse
from importlib.metadata import version
import json
from pathlib import Path

import polars as pl

from materialize_defense_v1_tracked_source import (
    PACKAGE_VERSION,
    MLB_WINDOWS,
    MILB_2023_WINDOW,
    _aaa_abbreviations,
    _derive_level,
    _file_sha,
)
from sportsdataverse.mlb.mlb_statcast_extra import mlb_statcast_search, mlb_statcast_search_minors


SEGMENTS = ("mlb-2021", "mlb-2022", "mlb-2023", "milb-2023")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segment", choices=SEGMENTS, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/defense-v1-tracked-source-segments"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    installed = version("sportsdataverse")
    if installed != PACKAGE_VERSION:
        raise RuntimeError(f"expected sportsdataverse {PACKAGE_VERSION}, observed {installed}")

    root = args.output_root / args.segment
    table_root = root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)
    range_frames: list[pl.DataFrame] = []
    framing_frames: list[pl.DataFrame] = []
    diagnostics: list[dict[str, object]] = []
    queries: list[dict[str, object]] = []

    if args.segment.startswith("mlb-"):
        season = int(args.segment.split("-", 1)[1])
        start, end = MLB_WINDOWS[season]
        print(f"Fetching MLB Statcast {season}: {start}..{end}", flush=True)
        pitches = mlb_statcast_search(start, end, season=season, game_type="R", chunk_days=7)
        print(f"Fetched MLB {season}: {pitches.height:,} pitch rows", flush=True)
        range_rows, framing_rows, diag = _derive_level(
            pitches, season=season, level_group="MLB"
        )
        range_frames.append(range_rows)
        framing_frames.append(framing_rows)
        diagnostics.append(diag)
        queries.append(
            {
                "source": "Baseball Savant MLB Statcast CSV via SportsDataverse",
                "season": season,
                "level_group": "MLB",
                "start": start,
                "end": end,
                "game_type": "R",
                "chunk_days": 7,
            }
        )
    else:
        start, end = MILB_2023_WINDOW
        print(f"Fetching tracked MiLB Statcast 2023: {start}..{end}", flush=True)
        milb = mlb_statcast_search_minors(
            start,
            end,
            season=2023,
            game_type="R",
            minors="true",
            chunk_days=7,
        )
        print(f"Fetched MiLB 2023: {milb.height:,} pitch rows", flush=True)
        if milb.is_empty() or "home_team" not in milb.columns:
            raise RuntimeError("tracked MiLB 2023 source empty or missing home_team")
        aaa_abbr = _aaa_abbreviations()
        milb = milb.with_columns(pl.col("home_team").cast(pl.Utf8).str.strip_chars())
        aaa = milb.filter(pl.col("home_team").is_in(sorted(aaa_abbr)))
        non_aaa = milb.filter(~pl.col("home_team").is_in(sorted(aaa_abbr)))
        for level_group, frame in (("AAA", aaa), ("TRACKED_NON_AAA", non_aaa)):
            range_rows, framing_rows, diag = _derive_level(
                frame, season=2023, level_group=level_group
            )
            range_frames.append(range_rows)
            framing_frames.append(framing_rows)
            diagnostics.append(diag)
            queries.append(
                {
                    "source": "Baseball Savant MiLB Statcast CSV via SportsDataverse",
                    "season": 2023,
                    "level_group": level_group,
                    "start": start,
                    "end": end,
                    "game_type": "R",
                    "minors": "true",
                    "server_level_filter": False,
                    "client_level_classification": "official 2023 AAA home-team abbreviation membership",
                    "chunk_days": 7,
                }
            )

    range_all = pl.concat(range_frames, how="vertical_relaxed").sort(
        ["season", "level_group", "player_id", "position"]
    )
    framing_all = pl.concat(framing_frames, how="vertical_relaxed").sort(
        ["season", "level_group", "player_id"]
    )
    range_path = table_root / "tracked_range_proxy.parquet"
    framing_path = table_root / "tracked_framing_proxy.parquet"
    range_all.write_parquet(range_path, compression="zstd")
    framing_all.write_parquet(framing_path, compression="zstd")
    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_tracked_source_segment",
        "contract": "docs/defense-v1-tracked-challenger-contract.md",
        "segment": args.segment,
        "sportsdataverse_version": installed,
        "queries": queries,
        "diagnostics": diagnostics,
        "storage": {
            "range": {
                "path": str(range_path),
                "row_count": range_all.height,
                "sha256": _file_sha(range_path),
            },
            "framing": {
                "path": str(framing_path),
                "row_count": framing_all.height,
                "sha256": _file_sha(framing_path),
            },
        },
        "boundary": {"2025_source_accessed": False, "model_fit": False},
    }
    (root / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        f"Completed {args.segment}: range={range_all.height:,}, framing={framing_all.height:,}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
