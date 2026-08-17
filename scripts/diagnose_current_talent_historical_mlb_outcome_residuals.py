#!/usr/bin/env python3
"""Capture official gameLog evidence for historical MLB outcome residuals.

This is a diagnostic-only companion to the historical MLB Current Talent season
materializer. It runs only after the independent season backbone has identified a
player × actual-league residual. It does not alter source evidence or acceptance.

The purpose is to turn a season-level discrepancy into inspectable official game
rows without hard-coding player IDs or guessing which game should change. If the
upstream materializer failed before it produced a reconciliation mismatch table
(for example a transient source transport failure), this diagnostic exits cleanly
because there is no outcome residual to adjudicate yet.
"""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path
from typing import Any

import polars as pl
import requests

from universal_baseball.current_talent_official_outcomes import (
    official_game_log_endpoint,
    project_official_hitting_game_log,
)


STATS_API_ROOT = "https://statsapi.mlb.com/api/v1"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, required=True)
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


def _sum_outcome_vector(frame: pl.DataFrame) -> dict[str, int]:
    fields = (
        "batting_PA",
        "batting_AB",
        "batting_BB",
        "batting_HBP",
        "batting_SO",
        "batting_SF",
        "batting_SH",
        "batting_CI",
    )
    return {
        field: int(frame.get_column(field).fill_null(0).sum() or 0)
        for field in fields
    }


def main() -> int:
    args = _parse_args()
    season = int(args.season)
    report_dir = args.report_root / str(season)
    raw_dir = args.work_root / str(season) / "raw" / "official" / "residual-game-log"
    diagnostic_dir = report_dir / "residual-game-log"
    mismatch_path = report_dir / "official_season_reconciliation_mismatches.csv"

    if not mismatch_path.exists():
        print(
            "No historical MLB reconciliation mismatch table exists; "
            "upstream failure occurred before outcome residual adjudication."
        )
        return 0
    mismatch = pl.read_csv(mismatch_path)
    if mismatch.is_empty():
        print("No historical MLB outcome residuals to diagnose.")
        return 0

    required = {"league_id", "player_id"}
    missing = sorted(required - set(mismatch.columns))
    if missing:
        raise ValueError(f"historical MLB mismatch CSV missing residual identity fields: {missing}")

    keys = (
        mismatch.select(
            pl.col("league_id").cast(pl.Int64),
            pl.col("player_id").cast(pl.Int64),
        )
        .unique()
        .sort(["league_id", "player_id"])
    )
    raw_dir.mkdir(parents=True, exist_ok=True)
    diagnostic_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers["User-Agent"] = (
        "universal-baseball-model-historical-mlb-residual-diagnostic/0.1"
    )
    captures: list[dict[str, Any]] = []
    try:
        for row in keys.to_dicts():
            league_id = int(row["league_id"])
            player_id = int(row["player_id"])
            endpoint = official_game_log_endpoint(
                player_id=player_id,
                sport_id=1,
                season=season,
            )
            url = f"{STATS_API_ROOT}/{endpoint}"
            response = session.get(url, timeout=120)
            response.raise_for_status()
            content = response.content

            raw_path = raw_dir / f"player_{player_id}_sport_1_gamelog.json"
            raw_path.write_bytes(content)
            payload = response.json()
            if not isinstance(payload, dict):
                raise RuntimeError(
                    f"official MLB gameLog for player={player_id} is not a JSON object"
                )
            projected = project_official_hitting_game_log(
                payload,
                player_id=player_id,
                sport_id=1,
            )
            target = projected.filter(
                (pl.col("league_id") == league_id)
                & (pl.col("game_type") == "R")
                & pl.col("batting_PA").is_not_null()
                & (pl.col("batting_PA") > 0)
            ).sort(["game_date", "game_id"])
            projected_path = diagnostic_dir / (
                f"player_{player_id}_league_{league_id}_official_gamelog.csv"
            )
            target.write_csv(projected_path)
            captures.append(
                {
                    "season": season,
                    "league_id": league_id,
                    "player_id": player_id,
                    "endpoint": endpoint,
                    "url": response.url,
                    "status_code": int(response.status_code),
                    "content_sha256": sha256(content).hexdigest(),
                    "response_byte_count": len(content),
                    "raw_path": str(raw_path),
                    "projected_path": str(projected_path),
                    "projected_positive_pa_game_count": int(target.height),
                    "projected_positive_pa_totals": _sum_outcome_vector(target),
                }
            )
    finally:
        session.close()

    manifest = {
        "report_schema_version": "0.1",
        "season": season,
        "purpose": "diagnostic_only_no_evidence_mutation",
        "residual_player_league_count": int(keys.height),
        "captures": captures,
    }
    manifest_path = diagnostic_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
