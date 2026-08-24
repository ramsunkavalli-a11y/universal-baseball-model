#!/usr/bin/env python3
"""Capture official 2021-2023 venue metadata for chronology-safe C1 history."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import polars as pl
import requests

from universal_baseball.hitter_v2_park import (
    project_schedule_venues,
    resolve_schedule_venue_duplicates,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
SPORT_IDS = (1, 11, 12, 13, 14, 16)
SEASONS = (2021, 2022, 2023)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--history-player-game",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage1-universal/tables/"
            "hitter_v2_player_game_outcomes_2021_2023.parquet"
        ),
    )
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=Path("data/quarantine/hitter-v2-stage2-park/schedules"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-park-context"),
    )
    parser.add_argument("--reuse-captured", action="store_true")
    return parser.parse_args()


def _capture(
    session: requests.Session,
    *,
    season: int,
    sport_id: int,
    raw_root: Path,
    reuse_captured: bool,
) -> tuple[pl.DataFrame, dict[str, object]]:
    raw_root.mkdir(parents=True, exist_ok=True)
    path = raw_root / f"schedule_{season}_sport_{sport_id}_regular.json"
    if reuse_captured:
        if not path.is_file():
            raise RuntimeError(f"captured schedule is missing: {path}")
        content = path.read_bytes()
        payload: dict[str, Any] = json.loads(content)
        request_url = (
            f"{SCHEDULE_URL}?sportId={sport_id}&season={season}"
            "&gameType=R&hydrate=venue%2Cteam"
        )
        retrieval_mode = "offline_replay"
    else:
        response = session.get(
            SCHEDULE_URL,
            params={
                "sportId": sport_id,
                "season": season,
                "gameType": "R",
                "hydrate": "venue,team",
            },
            timeout=120,
        )
        response.raise_for_status()
        content = response.content
        payload = response.json()
        path.write_bytes(content)
        request_url = response.url
        retrieval_mode = "official_api_capture"
    projected = project_schedule_venues(
        payload,
        season=season,
        sport_id=sport_id,
    )
    return projected, {
        "season": season,
        "sport_id": sport_id,
        "request_url": request_url,
        "retrieval_mode": retrieval_mode,
        "raw_path": path.as_posix(),
        "response_sha256": sha256(content).hexdigest(),
        "response_size_bytes": len(content),
        "regular_season_rows": projected.height,
    }


def main() -> int:
    args = _parse_args()
    session = requests.Session()
    session.headers.update(
        {"User-Agent": "universal-baseball-model-hitter-v2-source-audit/0.1"}
    )
    captures = []
    frames = []
    for season in SEASONS:
        for sport_id in SPORT_IDS:
            frame, record = _capture(
                session,
                season=season,
                sport_id=sport_id,
                raw_root=args.raw_root,
                reuse_captured=args.reuse_captured,
            )
            frames.append(frame)
            captures.append(record)
            print(json.dumps(record, sort_keys=True), flush=True)
    venues = resolve_schedule_venue_duplicates(
        pl.concat(frames, how="vertical_relaxed")
    )
    canonical = pl.read_parquet(args.history_player_game).filter(
        pl.col("modeling_eligible")
    )
    joined = canonical.join(
        venues,
        on=["season", "game_id"],
        how="left",
        validate="m:1",
    ).with_columns(
        pl.col("venue_context_eligible").fill_null(False),
        pl.col("venue_source_status")
        .fill_null("failed_closed_game_absent_from_official_schedule"),
    )
    ready = joined.filter(pl.col("venue_context_eligible"))
    if ready.is_empty():
        raise RuntimeError("official schedule venue source matched no canonical rows")
    output = joined.select(
        "season",
        "game_date",
        "game_id",
        "league_id",
        "level_group",
        "team_id",
        "player_id",
        "accepted_terminal_pa",
        "sport_id",
        "venue_id",
        "venue_name",
        "away_team_id",
        "home_team_id",
        "venue_context_eligible",
        "venue_source_status",
        "source_capability_tier",
    ).sort(["season", "league_id", "game_id", "player_id"])
    status_counts = {
        row["venue_source_status"]: row["len"]
        for row in output.group_by("venue_source_status").len().to_dicts()
    }
    game_artifact = write_canonical_parquet(
        venues,
        args.report_root / "tables" / "hitter_v2_game_venues_2021_2023.parquet",
        table_name="hitter_v2_game_venues",
    ).as_record()
    player_game_artifact = write_canonical_parquet(
        output,
        args.report_root / "tables" / "hitter_v2_player_game_park_context_2021_2023.parquet",
        table_name="hitter_v2_player_game_park_context",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": 2,
        "status": "historical_park_context_source_ready",
        "candidate_fit": False,
        "candidate_scored": False,
        "protected_2026_opened": False,
        "seasons": list(SEASONS),
        "target_season_metadata_opened": False,
        "captures": captures,
        "totals": {
            "canonical_model_ready_player_games": output.height,
            "park_ready_player_games": ready.height,
            "player_game_coverage": ready.height / output.height,
            "canonical_model_ready_pa": int(output["accepted_terminal_pa"].sum()),
            "park_ready_pa": int(ready["accepted_terminal_pa"].sum()),
            "pa_coverage": (
                int(ready["accepted_terminal_pa"].sum())
                / int(output["accepted_terminal_pa"].sum())
            ),
            "canonical_games": output["game_id"].n_unique(),
            "park_ready_games": ready["game_id"].n_unique(),
            "venues": ready["venue_id"].n_unique(),
        },
        "status_counts": status_counts,
        "storage": {
            "game_venues": game_artifact,
            "player_game_park_context": player_game_artifact,
        },
        "input_sha256": {
            "history_player_game": sha256_file(args.history_player_game),
            "capture_manifest": sha256(
                json.dumps(captures, separators=(",", ":"), sort_keys=True).encode()
            ).hexdigest(),
        },
    }
    args.report_root.mkdir(parents=True, exist_ok=True)
    (args.report_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["totals"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
