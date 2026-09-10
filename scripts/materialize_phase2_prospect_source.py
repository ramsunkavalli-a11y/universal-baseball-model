#!/usr/bin/env python3
"""Capture and normalize the current public FanGraphs Top 100."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import requests
import polars as pl

from universal_baseball.prospect_value import (
    FANGRAPHS_2026_PROSPECT_VALUE_URL,
    FANGRAPHS_2026_TOP100_URL,
    attach_mlbam_ids,
    parse_fangraphs_top100_html,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--html-capture", type=Path)
    parser.add_argument(
        "--control-root", type=Path, default=Path("reports/generated/league-control")
    )
    parser.add_argument(
        "--output-root", type=Path, default=Path("reports/generated/phase2-prospect-source")
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    output = args.output_root / args.as_of_date.isoformat()
    capture = args.html_capture or output / "captures/fangraphs-top-100.html"
    if args.html_capture is None:
        response = requests.get(FANGRAPHS_2026_TOP100_URL, timeout=60)
        response.raise_for_status()
        capture.parent.mkdir(parents=True, exist_ok=True)
        capture.write_bytes(response.content)
    rankings = parse_fangraphs_top100_html(capture.read_text(encoding="utf-8"))
    control_path = (
        args.control_root / args.as_of_date.isoformat() / "league-control-snapshot.parquet"
    )
    matched = attach_mlbam_ids(rankings, pl.read_parquet(control_path))
    output.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        matched,
        output / "fangraphs-top-100.parquet",
        table_name="phase2_fangraphs_top_100",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "gate": "phase2_current_prospect_source",
        "as_of_date": args.as_of_date.isoformat(),
        "ranking_url": FANGRAPHS_2026_TOP100_URL,
        "valuation_url": FANGRAPHS_2026_PROSPECT_VALUE_URL,
        "ranked_players": matched.height,
        "matched_mlbam": matched.filter(pl.col("player_id").is_not_null()).height,
        "unmatched_mlbam": matched.filter(pl.col("player_id").is_null()).height,
        "identity_policy": (
            "exact normalized player name plus organization; exact unique normalized "
            "name fallback when dated source organization no longer matches; ambiguous "
            "names remain unmatched"
        ),
        "capture_sha256": sha256_file(capture),
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
