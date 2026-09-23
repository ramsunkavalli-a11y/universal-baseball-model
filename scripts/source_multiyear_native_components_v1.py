"""Capture explicit completed-season public native-run labels, not tracking features.

No model fitting or scoring. Schema/year validation precedes downstream use.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path

import polars as pl
import requests
from sportsdataverse.mlb.mlb_statcast import parse_mlb_statcast_html_leaderboard

from universal_baseball.player_value_baserunning_sources import savant_baserunning_query_params

OUT = Path("reports/generated/multiyear-hitter-components-v1/native-source")


def capture(kind, year):
    if not 2016 <= year <= 2025:
        raise ValueError("Completed 2016–2025 seasons only")
    if kind == "fielding":
        endpoint, params = "fielding-run-value", {"type": "player", "year": year, "team": "", "min": 0}
    elif kind == "running":
        endpoint, params = "baserunning-run-value", savant_baserunning_query_params(year)
    elif kind == "framing":
        endpoint, params = "catcher-framing", {"type": "catcher", "seasonStart": year,
            "seasonEnd": year, "team": "", "min": 0, "sortColumn": "rv_tot", "sortDirection": "desc", "csv": "true"}
    else:
        raise ValueError(kind)
    rawpath = OUT / f"{kind}-{year}.response"
    if rawpath.exists():
        content = rawpath.read_bytes()
    else:
        r = requests.get(f"https://baseballsavant.mlb.com/leaderboard/{endpoint}", params=params, timeout=60)
        r.raise_for_status()
        content = r.content
        OUT.mkdir(parents=True, exist_ok=True)
        rawpath.write_bytes(content)
    if kind == "fielding":
        frame = parse_mlb_statcast_html_leaderboard(content.decode("utf-8"))
    else:
        if content.lstrip().startswith(b"<"):
            raise ValueError(f"HTML instead of table: {kind} {year}")
        frame = pl.read_csv(io.BytesIO(content), infer_schema_length=None)
    if not isinstance(frame, pl.DataFrame) or frame.is_empty():
        raise ValueError(f"No parsed table: {kind} {year}")
    year_fields = [c for c in ("year", "season", "start_year", "end_year", "season_start", "season_end") if c in frame.columns]
    observed = {c: frame[c].cast(pl.Int64, strict=False).drop_nulls().unique().to_list() for c in year_fields}
    if any(set(values) != {year} for values in observed.values()):
        raise ValueError(f"Wrong embedded year, requested {year}: {observed}")
    frame.write_parquet(OUT / f"{kind}-{year}.parquet")
    note = {"kind": kind, "requested_year": year, "endpoint": endpoint, "params": params,
        "response_sha256": hashlib.sha256(content).hexdigest(), "embedded_year": observed,
        "rows": frame.height, "columns": frame.columns,
        "status": "embedded_year_verified" if observed else "needs_cross_year_fingerprint_and_identity_checks"}
    (OUT / f"{kind}-{year}.json").write_text(json.dumps(note, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(note), flush=True)
    return note


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", nargs="+", type=int, default=list(range(2016,2026)))
    parser.add_argument("--kinds", nargs="+", default=["fielding", "running"])
    args = parser.parse_args()
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda item: capture(*item), [(k,y) for k in args.kinds for y in args.years]))
