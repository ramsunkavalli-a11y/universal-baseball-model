#!/usr/bin/env python3
"""Diagnose the two historical 40-man duplicate-player source cases.

Compares query-parameter and path-segment rosterType endpoint forms for team 121
on the exact failing 2022/2023 snapshots. Persists raw duplicate rows and set
comparisons. Source diagnostic only; no deduplication or model feature creation.
"""

from __future__ import annotations

from collections import Counter
from datetime import date
import json
from pathlib import Path
from typing import Any

import requests


CASES = ((121, date(2022, 10, 15)), (121, date(2023, 10, 15)))
BASE = "https://statsapi.mlb.com/api/v1"
REPORT_ROOT = Path("reports/generated/playing-time-roster-duplicate-diagnostic")


def _fetch(session: requests.Session, url: str, params: dict[str, Any]) -> dict[str, Any]:
    response = session.get(url, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict) or not isinstance(payload.get("roster"), list):
        raise RuntimeError("unexpected roster response schema")
    return {
        "requested_url": response.url,
        "status_code": response.status_code,
        "payload": payload,
    }


def _summarize(capture: dict[str, Any]) -> dict[str, Any]:
    roster = capture["payload"]["roster"]
    ids = [int(row["person"]["id"]) for row in roster]
    counts = Counter(ids)
    duplicate_ids = sorted(player_id for player_id, count in counts.items() if count > 1)
    duplicates: list[dict[str, Any]] = []
    for player_id in duplicate_ids:
        rows = [row for row in roster if int(row["person"]["id"]) == player_id]
        normalized = [json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows]
        duplicates.append(
            {
                "player_id": player_id,
                "row_count": len(rows),
                "rows_exactly_identical": len(set(normalized)) == 1,
                "rows": rows,
            }
        )
    return {
        "requested_url": capture["requested_url"],
        "row_count": len(roster),
        "unique_player_count": len(set(ids)),
        "duplicate_player_ids": duplicate_ids,
        "duplicates": duplicates,
        "unique_player_ids": sorted(set(ids)),
    }


def main() -> int:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-roster-duplicate-diagnostic/0.1"
    cases: list[dict[str, Any]] = []
    try:
        for team_id, snapshot in CASES:
            common = {"season": snapshot.year, "date": snapshot.isoformat()}
            query_capture = _fetch(
                session,
                f"{BASE}/teams/{team_id}/roster",
                {**common, "rosterType": "40Man"},
            )
            path_capture = _fetch(
                session,
                f"{BASE}/teams/{team_id}/roster/40Man",
                common,
            )
            query = _summarize(query_capture)
            path = _summarize(path_capture)
            query_set = set(query["unique_player_ids"])
            path_set = set(path["unique_player_ids"])
            cases.append(
                {
                    "team_id": team_id,
                    "snapshot_date": snapshot.isoformat(),
                    "query_form": query,
                    "path_form": path,
                    "unique_player_sets_equal": query_set == path_set,
                    "query_only_player_ids": sorted(query_set - path_set),
                    "path_only_player_ids": sorted(path_set - query_set),
                }
            )
    finally:
        session.close()

    all_duplicate_rows_identical = all(
        duplicate["rows_exactly_identical"]
        for case in cases
        for form in (case["query_form"], case["path_form"])
        for duplicate in form["duplicates"]
    )
    path_form_removes_duplicates = all(
        not case["path_form"]["duplicate_player_ids"] for case in cases
    )
    report = {
        "report_schema_version": "0.1",
        "gate": "playing_time_historical_roster_duplicate_diagnostic",
        "queried_2025": False,
        "cases": cases,
        "summary": {
            "all_duplicate_rows_exactly_identical": all_duplicate_rows_identical,
            "path_form_removes_duplicates": path_form_removes_duplicates,
            "all_query_and_path_unique_player_sets_equal": all(
                case["unique_player_sets_equal"] for case in cases
            ),
        },
        "interpretation": (
            "Diagnostic only. Do not authorize deduplication unless the exact duplicate "
            "semantics are proven harmless and encoded in a fail-closed source rule."
        ),
    }
    (REPORT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
