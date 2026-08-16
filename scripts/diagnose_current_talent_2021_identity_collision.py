#!/usr/bin/env python
"""Preserve the resolved rows around the 2021 DSL identity-correction collision.

Diagnostic only: loads the same reusable Rookie player-game assets used by the
historical Current Talent materializer, resolves snapshots, and writes the
outcome/contact-control rows for game 660171 and players 703595/682770. Nothing
is corrected or mutated.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import polars as pl
import requests

from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.current_talent_milb_evidence import (
    project_milb_player_game_outcomes,
    resolve_milb_player_game_outcomes,
)
from universal_baseball.player_game_controls import resolve_player_game_contact_controls
from universal_baseball.player_game_stats import (
    fetch_player_game_asset_inventory,
    project_player_game_batting,
)


SEASON = 2021
LEVEL = "rk"
GAME_ID = 660171
PLAYER_IDS = (703595, 682770)
GAME_TYPE = "R"


def _session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-identity-collision/0.1"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def main() -> int:
    work_dir = Path("data/quarantine/current-talent-2021-identity-collision")
    report_dir = Path(
        "reports/generated/current-talent-historical-milb-game-evidence/2021/rk"
    )
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    session = _session()
    try:
        assets = [
            asset
            for asset in fetch_player_game_asset_inventory(session=session)
            if asset.year == SEASON and asset.filename_level == LEVEL
        ]
        control_frames: list[pl.DataFrame] = []
        outcome_frames: list[pl.DataFrame] = []
        raw_rows: list[pl.DataFrame] = []
        for asset in assets:
            path = work_dir / asset.name
            if not path.exists() or path.stat().st_size <= 0:
                download_file(asset.browser_download_url, path, timeout_seconds=240)
            raw = read_quarantined_csv(path)
            if {"game_id", "player_id"}.issubset(raw.columns):
                target = raw.filter(
                    (pl.col("game_id").cast(pl.Int64, strict=False) == GAME_ID)
                    & pl.col("player_id").cast(pl.Int64, strict=False).is_in(PLAYER_IDS)
                )
                if not target.is_empty():
                    raw_rows.append(
                        target.with_columns(pl.lit(asset.name).alias("diagnostic_source_asset"))
                    )
            control_frames.append(
                project_player_game_batting(
                    raw,
                    source_asset=asset.name,
                    season=SEASON,
                    game_type=GAME_TYPE,
                )
            )
            outcome_frames.append(
                project_milb_player_game_outcomes(
                    raw,
                    source_asset=asset.name,
                    season=SEASON,
                    game_type=GAME_TYPE,
                )
            )
    finally:
        session.close()

    controls, control_metrics = resolve_player_game_contact_controls(
        pl.concat(control_frames, how="vertical_relaxed")
    )
    outcomes, outcome_metrics = resolve_milb_player_game_outcomes(
        pl.concat(outcome_frames, how="vertical_relaxed")
    )
    target_controls = controls.filter(
        (pl.col("game_id") == GAME_ID) & pl.col("player_id").is_in(PLAYER_IDS)
    ).sort("player_id")
    target_outcomes = outcomes.filter(
        (pl.col("game_id") == GAME_ID) & pl.col("player_id").is_in(PLAYER_IDS)
    ).sort("player_id")

    target_controls.write_csv(report_dir / "identity_collision_controls.csv")
    target_outcomes.write_csv(report_dir / "identity_collision_outcomes.csv")
    if raw_rows:
        pl.concat(raw_rows, how="diagonal_relaxed").write_csv(
            report_dir / "identity_collision_raw_rows.csv"
        )

    report = {
        "season": SEASON,
        "level": LEVEL,
        "game_id": GAME_ID,
        "player_ids": list(PLAYER_IDS),
        "resolved_outcomes": target_outcomes.to_dicts(),
        "resolved_controls": target_controls.to_dicts(),
        "outcome_resolution_metrics": outcome_metrics,
        "control_resolution_metrics": control_metrics,
        "raw_row_count": int(sum(frame.height for frame in raw_rows)),
        "interpretation": (
            "Diagnostic only. A target-row collision may be merged only if the existing corrected-player "
            "row contains no competing positive-PA/contact evidence; otherwise identity repair remains blocked."
        ),
    }
    (report_dir / "identity_collision_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
