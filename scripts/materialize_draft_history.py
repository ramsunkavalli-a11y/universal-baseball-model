#!/usr/bin/env python3
"""Capture official Rule 4 draft history for chronology-safe model research."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl
import requests

from universal_baseball.draft_source import fetch_draft_year
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=2006)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/draft-history"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    if args.start_year > args.end_year:
        raise ValueError("start year must not exceed end year")
    captures = args.output_root / "captures"
    captures.mkdir(parents=True, exist_ok=True)
    frames = []
    requested_urls = []
    with requests.Session() as session:
        for year in range(args.start_year, args.end_year + 1):
            frame, payload, url = fetch_draft_year(year, session=session)
            frames.append(frame)
            requested_urls.append(url)
            (captures / f"draft-{year}.json").write_text(
                json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8"
            )
    history = pl.concat(frames, how="vertical_relaxed").sort(
        ["draft_year", "pick_number"]
    )
    storage = write_canonical_parquet(
        history,
        args.output_root / "draft-history.parquet",
        table_name="official_statsapi_rule4_draft_history",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "status": "source_evidence_not_model_selection",
        "source": "official_mlb_statsapi_rule4_draft",
        "years": [args.start_year, args.end_year],
        "picks": history.height,
        "players": history.get_column("player_id").n_unique(),
        "signing_bonus_coverage": float(
            history.get_column("signing_bonus_dollars").is_not_null().mean()
        ),
        "narrative_scouting_text_retained_as_feature": False,
        "requested_urls": requested_urls,
        "storage": storage,
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
