#!/usr/bin/env python3
"""Diagnose historical season filtering on Savant catcher leaderboards.

Diagnostic only. Compare stale/generated query shapes with the query shape used
by the current Savant leaderboard UI. No model fitting or scoring.
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
TARGET_MIN = {"catcher-throwing": 10, "catcher-blocking": 500}


def _ui_params(endpoint: str, year: int, n: object) -> dict[str, object]:
    params: dict[str, object] = {
        "game_type": "Regular",
        "n": n,
        "season_start": year,
        "season_end": year,
        "split": "no",
        "team": "",
        "type": "Cat",
        "with_team_only": 1,
        "csv": "true",
    }
    if endpoint == "catcher-throwing":
        params["target_base"] = "All"
    return params


def _params(style: str, endpoint: str, year: int) -> dict[str, object]:
    if style == "year_only":
        return {"year": year, "csv": "true"}
    if style == "year_min0":
        return {"year": year, "min": 0, "csv": "true"}
    if style == "year_minq":
        return {"year": year, "min": "q", "csv": "true"}
    if style == "camel_range_min0":
        return {"seasonStart": year, "seasonEnd": year, "min": 0, "csv": "true"}
    if style == "camel_range_minq":
        return {"seasonStart": year, "seasonEnd": year, "min": "q", "csv": "true"}
    if style == "ui_snake_all":
        return _ui_params(endpoint, year, 0)
    if style == "ui_snake_qualified":
        return _ui_params(endpoint, year, "q")
    if style == "ui_snake_target_min":
        return _ui_params(endpoint, year, TARGET_MIN[endpoint])
    raise ValueError(style)


STYLES = (
    "year_only",
    "year_min0",
    "year_minq",
    "camel_range_min0",
    "camel_range_minq",
    "ui_snake_all",
    "ui_snake_qualified",
    "ui_snake_target_min",
)


def fingerprint(text: str) -> dict:
    raw_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    stripped = text.strip()
    if not stripped or stripped.startswith("<!"):
        return {"sha256": raw_sha, "row_count": 0, "columns": [], "body_kind": "empty_or_html"}
    try:
        reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
        rows = list(reader)
    except Exception as exc:
        return {"sha256": raw_sha, "row_count": None, "columns": [], "body_kind": f"parse_error:{type(exc).__name__}"}
    columns = list(rows[0].keys()) if rows else []
    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    sample = []
    for row in rows[:5]:
        sample.append(
            {
                key: row.get(key)
                for key in ("player_id", "player_name", "start_year", "end_year", "sb_attempts", "pitches")
                if key in row
            }
        )
    observed_start_years = sorted({str(r.get("start_year")) for r in rows if r.get("start_year") not in (None, "")})
    observed_end_years = sorted({str(r.get("end_year")) for r in rows if r.get("end_year") not in (None, "")})
    return {
        "sha256": raw_sha,
        "canonical_rows_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "row_count": len(rows),
        "columns": columns,
        "sample": sample,
        "observed_start_years": observed_start_years,
        "observed_end_years": observed_end_years,
        "body_kind": "csv",
    }


def _year_specific(results: dict, endpoint: str, style: str) -> bool:
    item = results[endpoint][style]
    if item["distinct_year_payload_count"] != len(YEARS):
        return False
    return all(
        str(year) in item["years"][str(year)]["observed_start_years"]
        and (
            not item["years"][str(year)]["observed_end_years"]
            or str(year) in item["years"][str(year)]["observed_end_years"]
        )
        for year in YEARS
    )


def main() -> int:
    out = Path("reports/generated/savant-catcher-year-filter-diagnostic.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "universal-baseball-model-source-diagnostic/0.3"})
    results = {}
    for endpoint in ENDPOINTS:
        url = f"https://baseballsavant.mlb.com/leaderboard/{endpoint}"
        endpoint_results = {}
        for style in STYLES:
            style_results = {}
            for year in YEARS:
                params = _params(style, endpoint, year)
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

    target_min_clean = all(_year_specific(results, endpoint, "ui_snake_target_min") for endpoint in ENDPOINTS)
    qualified_clean = all(_year_specific(results, endpoint, "ui_snake_qualified") for endpoint in ENDPOINTS)
    report = {
        "report_schema_version": "0.3",
        "gate": "savant_catcher_year_filter_diagnostic",
        "status": "target_min_query_certified" if target_min_clean else "diagnostic_complete_query_not_certified",
        "years": list(YEARS),
        "target_minimums": TARGET_MIN,
        "results": results,
        "decision": {
            "legacy_year_query_is_year_specific": all(results[e]["year_min0"]["distinct_year_payload_count"] == len(YEARS) for e in ENDPOINTS),
            "ui_snake_qualified_query_is_year_specific": qualified_clean,
            "ui_snake_target_min_query_is_year_specific": target_min_clean,
            "catcher_source_repair_authorized": target_min_clean,
        },
        "boundary": {"model_fit": False, "model_scoring": False, "war_calculated": False},
    }
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for endpoint in ENDPOINTS:
        print(endpoint)
        for style in STYLES:
            item = results[endpoint][style]
            counts = [item["years"][str(y)]["row_count"] for y in YEARS]
            print(f"  {style}: distinct={item['distinct_year_payload_count']} rows={counts}")
    print(f"target-min query certified={target_min_clean}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
