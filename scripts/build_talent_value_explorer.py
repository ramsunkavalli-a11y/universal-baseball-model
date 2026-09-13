#!/usr/bin/env python3
"""Build the safe prospect-talent foundation explorer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_foundation import (
    build_prospect_foundation_payload,
    write_prospect_foundation_explorer,
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", default="2026-09-08")
    parser.add_argument(
        "--output", type=Path,
        default=Path("reports/generated/talent-value-explorer/index.html"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    dated = args.as_of_date
    generated = Path("reports/generated")
    peak = generated / "current-peak-talent" / dated / "tables"
    future = generated / "current-future-talent" / dated / "tables"
    arrival = generated / "phase2-prospect-arrival" / dated
    control = generated / "league-control" / dated / "league-control-snapshot.parquet"
    raw = generated / "affiliated-skill-source" / "tables"
    negative_control = Path(
        "docs/weak-low-level-hitter-negative-control-result.json"
    )
    required = (
        peak / "current_peak_hitters.parquet",
        peak / "current_peak_pitchers.parquet",
        future / "current_future_hitters.parquet",
        future / "current_future_pitchers.parquet",
        arrival / "hitter-arrival-probabilities.parquet",
        arrival / "pitcher-arrival-probabilities.parquet",
        control,
        raw / "affiliated_hitting_components.parquet",
        raw / "affiliated_pitching_components.parquet",
        negative_control,
    )
    if missing := [path for path in required if not path.exists()]:
        raise FileNotFoundError(
            "Missing foundation inputs:\n" + "\n".join(map(str, missing))
        )
    payload = build_prospect_foundation_payload(
        pl.read_parquet(required[0]),
        pl.read_parquet(required[1]),
        pl.read_parquet(required[2]),
        pl.read_parquet(required[3]),
        pl.read_parquet(required[4]),
        pl.read_parquet(required[5]),
        pl.read_parquet(required[6]),
        pl.read_parquet(required[7]),
        pl.read_parquet(required[8]),
        season=int(dated[:4]),
        negative_control_evidence=json.loads(negative_control.read_text(encoding="utf-8")),
    )
    write_prospect_foundation_explorer(
        payload,
        Path("src/universal_baseball/talent_value_explorer.html"),
        args.output,
    )
    print(f"Prospect foundation explorer created: {args.output.resolve()}")
    print(f"Player/type rows: {payload['meta']['player_count']:,} | FV withdrawn")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
