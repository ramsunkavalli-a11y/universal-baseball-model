#!/usr/bin/env python3
"""Materialize one historical MLB season on the Current Talent game contract.

This intentionally reuses the already-certified MLB source adapters rather than
rebuilding the 2024 contextual Performance/value pipeline. Historical Current
Talent needs chronology-safe player-game outcomes/profile evidence; bulk official
season totals provide the independent accounting gate.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import date, timedelta
from hashlib import sha256
from pathlib import Path
import time
from typing import Any

import polars as pl
import requests

from universal_baseball.current_talent_mlb_evidence import (
    build_mlb_current_talent_player_game_evidence,
)
from universal_baseball.current_talent_mlb_history import (
    reconcile_mlb_game_evidence_to_official_backbone,
)
from universal_baseball.mlb_performance import assign_savant_actual_league
from universal_baseball.mlb_season_stats import (
    MlbBulkStatsCapture,
    fetch_mlb_hitting_backbone,
    fetch_mlb_team_leagues,
)
from universal_baseball.savant import (
    SavantCsvCapture,
    fetch_savant_csv,
    project_savant_performance_rows,
    read_savant_csv_bytes,
)
from universal_baseball.storage import write_canonical_parquet


SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
SAVANT_CHUNK_DAYS = 4
SAVANT_FETCH_ATTEMPTS = 5
SAVANT_RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--chunk-days", type=int, default=SAVANT_CHUNK_DAYS)
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("data/quarantine/current-talent-historical-mlb-game-evidence"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/current-talent-historical-mlb-game-evidence"),
    )
    return parser.parse_args()


def _date_chunks(start: date, end: date, days: int) -> list[tuple[date, date]]:
    if days <= 0:
        raise ValueError("chunk-days must be positive")
    chunks: list[tuple[date, date]] = []
    current = start
    while current <= end:
        chunk_end = min(current + timedelta(days=days - 1), end)
        chunks.append((current, chunk_end))
        current = chunk_end + timedelta(days=1)
    return chunks


def _fetch_savant_chunk_with_retry(
    chunk_start: date,
    chunk_end: date,
    *,
    session: requests.Session,
    timeout_seconds: int = 180,
    attempts: int = SAVANT_FETCH_ATTEMPTS,
) -> tuple[SavantCsvCapture, int]:
    """Retry only transient Savant transport failures; never semantic failures."""

    if attempts <= 0:
        raise ValueError("Savant fetch attempts must be positive")
    for attempt in range(1, attempts + 1):
        try:
            return (
                fetch_savant_csv(
                    chunk_start,
                    chunk_end,
                    session=session,
                    timeout_seconds=timeout_seconds,
                ),
                attempt,
            )
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status not in SAVANT_RETRYABLE_STATUS_CODES or attempt >= attempts:
                raise
        except (requests.ConnectionError, requests.Timeout):
            if attempt >= attempts:
                raise
        # Long historical runs should survive isolated upstream 5xx responses but
        # remain bounded. The first retry waits 2s, then 4/8/16s.
        time.sleep(min(2 ** attempt, 30))
    raise AssertionError("unreachable Savant retry loop")


def _fetch_regular_season_bounds(
    season: int,
    *,
    session: requests.Session,
    raw_dir: Path,
) -> tuple[date, date, dict[str, Any]]:
    response = session.get(
        SCHEDULE_URL,
        params={"sportId": 1, "season": int(season), "gameType": "R"},
        timeout=120,
    )
    response.raise_for_status()
    content = response.content
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"schedule_{season}_regular.json"
    path.write_bytes(content)
    payload = response.json()

    game_dates: list[date] = []
    game_pks: set[int] = set()
    for day in payload.get("dates") or []:
        for game in day.get("games") or []:
            game_type = str(game.get("gameType") or "")
            if game_type != "R":
                continue
            official_date = str(game.get("officialDate") or day.get("date") or "")
            if not official_date:
                raise RuntimeError("MLB regular-season schedule game missing official date")
            game_dates.append(date.fromisoformat(official_date))
            game_pk = game.get("gamePk")
            if game_pk is not None:
                game_pks.add(int(game_pk))
    if not game_dates:
        raise RuntimeError(f"official MLB schedule returned no regular-season games for {season}")
    return min(game_dates), max(game_dates), {
        "request_url": response.url,
        "response_sha256": sha256(content).hexdigest(),
        "response_byte_count": len(content),
        "raw_path": str(path),
        "regular_season_game_count": len(game_pks),
        "regular_season_first_date": min(game_dates).isoformat(),
        "regular_season_last_date": max(game_dates).isoformat(),
    }


def _load_savant_season(
    season: int,
    *,
    start_date: date,
    end_date: date,
    chunk_days: int,
    session: requests.Session,
    raw_dir: Path,
) -> tuple[pl.DataFrame, list[dict[str, Any]]]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    frames: list[pl.DataFrame] = []
    captures: list[dict[str, Any]] = []
    for chunk_start, chunk_end in _date_chunks(start_date, end_date, chunk_days):
        path = raw_dir / f"savant_{chunk_start}_{chunk_end}.csv"
        if path.exists() and path.stat().st_size > 0:
            content = path.read_bytes()
            request_path = None
            retrieved_url = "quarantine-cache"
            status_code = None
            fetch_attempt_count = 0
        else:
            capture, fetch_attempt_count = _fetch_savant_chunk_with_retry(
                chunk_start,
                chunk_end,
                session=session,
                timeout_seconds=180,
            )
            content = capture.response_bytes
            path.write_bytes(content)
            request_path = capture.request_path
            retrieved_url = capture.retrieved_url
            status_code = capture.status_code
        raw = read_savant_csv_bytes(content)
        projected = project_savant_performance_rows(raw, regular_season_only=True)
        frames.append(projected)
        captures.append(
            {
                "start_date": chunk_start.isoformat(),
                "end_date": chunk_end.isoformat(),
                "response_sha256": sha256(content).hexdigest(),
                "response_byte_count": len(content),
                "raw_row_count": int(raw.height),
                "projected_row_count": int(projected.height),
                "request_path": request_path,
                "retrieved_url": retrieved_url,
                "status_code": status_code,
                "fetch_attempt_count": fetch_attempt_count,
                "raw_path": str(path),
            }
        )

    nonempty = [frame for frame in frames if not frame.is_empty()]
    if not nonempty:
        raise RuntimeError(f"Baseball Savant returned no regular-season MLB rows for {season}")
    combined = pl.concat(nonempty, how="vertical_relaxed").sort(
        ["game_date", "game_pk", "at_bat_index", "pitch_number"]
    )
    observed_years = sorted(
        int(value) for value in combined.get_column("game_year").drop_nulls().unique().to_list()
    )
    if observed_years != [int(season)]:
        raise RuntimeError(
            f"historical MLB Savant season coverage mismatch: observed={observed_years}, expected={[season]}"
        )
    duplicate = combined.group_by(["game_pk", "at_bat_index", "pitch_number"]).len().filter(
        pl.col("len") > 1
    )
    if not duplicate.is_empty():
        raise RuntimeError(
            "historical MLB Savant source contains duplicate canonical pitch keys: "
            f"{duplicate.height}"
        )
    return combined, captures


def _persist_bulk_captures(
    captures: list[MlbBulkStatsCapture],
    *,
    raw_dir: Path,
) -> list[dict[str, Any]]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    for capture in captures:
        path = raw_dir / (
            f"stats_{capture.season}_league_{capture.league_id}_offset_{capture.offset}.json"
        )
        path.write_bytes(capture.response_bytes)
        record = asdict(capture)
        record.pop("response_bytes")
        record["response_byte_count"] = len(capture.response_bytes)
        record["raw_path"] = str(path)
        records.append(record)
    return records


def main() -> int:
    args = _parse_args()
    season = int(args.season)
    if season < 2021:
        raise ValueError("initial historical MLB Current Talent gate is post-reorganization, season >= 2021")

    work_dir = args.work_root / str(season)
    report_dir = args.report_root / str(season)
    raw_dir = work_dir / "raw"
    table_dir = report_dir / "tables"
    raw_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-historical-mlb-current-talent/0.1"
    try:
        start_date, end_date, schedule_meta = _fetch_regular_season_bounds(
            season,
            session=session,
            raw_dir=raw_dir / "schedule",
        )
        savant, savant_captures = _load_savant_season(
            season,
            start_date=start_date,
            end_date=end_date,
            chunk_days=int(args.chunk_days),
            session=session,
            raw_dir=raw_dir / "savant",
        )
        teams, team_response = fetch_mlb_team_leagues(season, session=session)
        team_path = raw_dir / "official" / f"teams_{season}.json"
        team_path.parent.mkdir(parents=True, exist_ok=True)
        team_path.write_bytes(team_response)
        assigned = assign_savant_actual_league(savant, teams)
        summary, profile, evidence_metrics = build_mlb_current_talent_player_game_evidence(
            assigned
        )
        backbone, backbone_captures = fetch_mlb_hitting_backbone(season, session=session)
    finally:
        session.close()

    official_capture_records = _persist_bulk_captures(
        backbone_captures,
        raw_dir=raw_dir / "official" / "season-stats",
    )
    comparison, reconciliation_metrics = reconcile_mlb_game_evidence_to_official_backbone(
        summary,
        profile,
        backbone,
        require_exact=False,
    )
    mismatch = comparison.filter(pl.col("has_exact_outcome_mismatch"))
    comparison.write_csv(report_dir / "official_season_reconciliation.csv")
    mismatch.write_csv(report_dir / "official_season_reconciliation_mismatches.csv")

    summary_path = table_dir / f"current_talent_game_summary_{season}_mlb.parquet"
    profile_path = table_dir / f"current_talent_game_profile_{season}_mlb.parquet"
    summary_artifact = write_canonical_parquet(
        summary,
        summary_path,
        table_name="current_talent_game_summary_mlb",
    ).as_record()
    profile_artifact = write_canonical_parquet(
        profile,
        profile_path,
        table_name="current_talent_game_profile_mlb",
    ).as_record()

    observed_game_pks = set(summary.get_column("game_pk").unique().to_list())
    report = {
        "report_schema_version": "0.2",
        "accepted": bool(reconciliation_metrics["exact_outcome_reconciliation"]),
        "scope": {
            "season": season,
            "level_group": "MLB",
            "actual_league_ids": sorted(
                int(value) for value in summary.get_column("league_id").unique().to_list()
            ),
            "purpose": "historical chronology-safe Current Talent player-game evidence",
        },
        "temporal_semantics": "retrospective_event_cutoff_corrected_history_not_vintage_information_set",
        "schedule": {
            **schedule_meta,
            "observed_game_count_in_player_game_evidence": len(observed_game_pks),
        },
        "source": {
            "savant_chunk_count": len(savant_captures),
            "savant_captures": savant_captures,
            "savant_retry_policy": {
                "attempts": SAVANT_FETCH_ATTEMPTS,
                "retryable_status_codes": sorted(SAVANT_RETRYABLE_STATUS_CODES),
                "backoff_seconds": [2, 4, 8, 16],
            },
            "team_authority": {
                "response_sha256": sha256(team_response).hexdigest(),
                "response_byte_count": len(team_response),
                "raw_path": str(team_path),
                "team_count": len(teams),
            },
            "official_season_stats_captures": official_capture_records,
        },
        "evidence": evidence_metrics,
        "reconciliation": reconciliation_metrics,
        "storage": {
            "summary": summary_artifact,
            "profile": profile_artifact,
            "comparison_csv": str(report_dir / "official_season_reconciliation.csv"),
            "mismatch_csv": str(report_dir / "official_season_reconciliation_mismatches.csv"),
        },
        "interpretation": (
            "MLB game-grain observed outcome/profile evidence only. Exact season outcome "
            "accounting is certified independently against bulk MLB Stats API. Physical-contact "
            "residuals remain diagnostics. No Current Talent estimate, translation, projection, "
            "playing time, WAR, or ranking is produced here."
        ),
    }
    report_path = report_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))

    if not report["accepted"]:
        raise RuntimeError(
            "historical MLB Current Talent season failed official outcome reconciliation: "
            f"{mismatch.height} player-league-season rows; see {report_dir / 'official_season_reconciliation_mismatches.csv'}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
