#!/usr/bin/env python3
"""Diagnose historical season filtering on Savant catcher leaderboards.

Diagnostic only: compare several documented/observed query shapes for 2022-2025.
No model fitting or scoring.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import requests

YEARS = (2022, 2023, 2024, 2025)
ENDPOINTS = ("catcher-throwing", "catcher-blocking")
STYLES = {
    "year_only": lambda y: {"year": y, "csv": "true"},
    "year_min0": lambda y: {"year": y, "min": 0, "csv": "true"},
    "year_minq": lambda y: {"year": y, "min": "q", "csv": "true"},
    "season_range_min0": lambda y: {"seasonStart": y, "seasonEnd": y, "min": 0, "csv": "true"},
    "season_range_minq": lambda y: {"seasonStart": y, "seasonEnd": y, "min": "q", "csv": "true"},
}


def fingerprint(text: str) -> dict:
    raw_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    stripped = text.strip()
    if not stripped or stripped.startswith("<!"):
        return {"sha256": raw_sha, "row_count": 0, "columns": [], "player_ids_head": [], "body_kind": "empty_or_html"}
    try:
        rows = list(csv.DictReader(io.StringIO(text)))
    except Exception as exc:
        return {"sha256": raw_sha, "row_count": None, "columns": [], "player_ids_head": [], "body_kind": f"parse_error:{type(exc).__name__}"}
    columns = list(rows[0].keys()) if rows else []
    player_key = next((key for key in ("player_id", "playerid", "id") if key in columns), None)
    ids = [str(row.get(player_key) or "") for row in rows[:10]] if player_key else []
    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {
        "sha256": raw_sha,
        "canonical_rows_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "row_count": len(rows),
        "columns": columns,
        "player_ids_head": ids,
        "body_kind": "csv",
    }


def main() -> int:
    out = Path("reports/generated/savant-catcher-year-filter-diagnostic.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "universal-baseball-model-source-diagnostic/0.1"})
    results = {}
    for endpoint in ENDPOINTS:
        url = f"https://baseballsavant.mlb.com/leaderboard/{endpoint}"
        endpoint_results = {}
        for style, make_params in STYLES.items():
            style_results = {}
            for year in YEARS:
                params = make_params(year)
                response = session.get(url, params=params, timeout=60)
                response.raise_for_status()
                style_results[str(year)] = {
                    "requested_params": params,
                    "response_url": response.url,
                    "content_type": response.headers.get("content-type"),
                    **fingerprint(response.text),
                }
            hashes = [style_results[str(y)].get("canonical_rows_sha256") for y in YEARS]
            endpoint_results[style] = {
                "years": style_results,
                "distinct_year_payload_count": len(set(hashes)),
                "all_year_payloads_identical": len(set(hashes)) == 1,
            }
        results[endpoint] = endpoint_results
    report = {
        "report_schema_version": "0.1",
        "gate": "savant_catcher_year_filter_diagnostic",
        "status": "diagnostic_complete",
        "years": list(YEARS),
        "results": results,
        "boundary": {"model_fit": False, "model_scoring": False, "war_calculated": False},
    }
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for endpoint in ENDPOINTS:
        print(endpoint)
        for style in STYLES:
            item = results[endpoint][style]
            counts = [item["years"][str(y)]["row_count"] for y in YEARS]
            print(f"  {style}: distinct={item['distinct_year_payload_count']} rows={counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
