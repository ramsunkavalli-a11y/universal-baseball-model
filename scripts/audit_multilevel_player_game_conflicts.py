#!/usr/bin/env python
"""Diagnose unresolved 2024 player-game batting snapshots below AAA.

The generic Performance POC deliberately failed rather than using unresolved
player-game controls. This cheap audit isolates those conflicts without
re-downloading season PBP or calling the official API.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.performance_level_config import performance_level_spec_2024
from universal_baseball.player_game_stats import (
    fetch_player_game_asset_inventory,
    project_player_game_batting,
    resolve_player_game_batting,
)


SEASON = 2024
LEVELS = ("aa", "a+", "a", "rk")
WORK_DIR = Path("data/quarantine/multilevel-player-game-conflicts")
REPORT_DIR = Path("reports/generated/multilevel-player-game-conflicts")


def main() -> int:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inventory = fetch_player_game_asset_inventory()

    reports: list[dict[str, object]] = []
    unresolved_frames: list[pl.DataFrame] = []
    observation_frames: list[pl.DataFrame] = []

    for level in LEVELS:
        spec = performance_level_spec_2024(level)
        assets = [
            asset
            for asset in inventory
            if asset.year == SEASON and asset.filename_level == level
        ]
        if not assets:
            raise RuntimeError(f"no player-game assets for {SEASON} {level}")

        projected_frames: list[pl.DataFrame] = []
        for asset in assets:
            path = WORK_DIR / level.replace("+", "plus") / asset.name
            if not path.exists() or path.stat().st_size <= 0:
                download_file(asset.browser_download_url, path, timeout_seconds=240)
            raw = read_quarantined_csv(path)
            projected_frames.append(
                project_player_game_batting(
                    raw,
                    source_asset=asset.name,
                    season=SEASON,
                    game_type="R",
                )
            )
        observations = pl.concat(projected_frames, how="vertical_relaxed")
        resolved, diagnostics = resolve_player_game_batting(observations)
        unresolved = resolved.filter(
            pl.col("expected_contact_count").is_null()
        ).with_columns(
            pl.lit(level).alias("filename_level"),
            pl.lit(spec.level_group).alias("level_group"),
        )
        if not unresolved.is_empty():
            unresolved_frames.append(unresolved)
            keys = unresolved.select("game_id", "player_id")
            raw_conflicts = (
                observations.join(keys, on=["game_id", "player_id"], how="inner")
                .with_columns(
                    pl.lit(level).alias("filename_level"),
                    pl.lit(spec.level_group).alias("level_group"),
                )
                .sort(["game_id", "player_id", "source_asset"])
            )
            observation_frames.append(raw_conflicts)

        resolution_counts = {
            str(row["player_game_resolution"]): int(row["len"])
            for row in resolved.group_by("player_game_resolution")
            .len()
            .sort("player_game_resolution")
            .to_dicts()
        }
        unresolved_games = int(unresolved.get_column("game_id").n_unique()) if unresolved.height else 0
        unresolved_by_league = (
            {
                str(int(row["league_id"])): int(row["len"])
                for row in unresolved.drop_nulls("league_id")
                .group_by("league_id")
                .len()
                .sort("league_id")
                .to_dicts()
            }
            if unresolved.height
            else {}
        )
        reports.append(
            {
                "filename_level": level,
                "level_group": spec.level_group,
                "league_ids": sorted(spec.league_ids),
                "asset_count": len(assets),
                "asset_names": [asset.name for asset in assets],
                "diagnostics": diagnostics,
                "resolution_counts": resolution_counts,
                "unresolved_game_count": unresolved_games,
                "unresolved_by_league": unresolved_by_league,
            }
        )

    unresolved_all = (
        pl.concat(unresolved_frames, how="diagonal_relaxed")
        if unresolved_frames
        else pl.DataFrame()
    )
    observations_all = (
        pl.concat(observation_frames, how="diagonal_relaxed")
        if observation_frames
        else pl.DataFrame()
    )
    if not unresolved_all.is_empty():
        unresolved_all.write_csv(REPORT_DIR / "unresolved_player_games.csv")
    if not observations_all.is_empty():
        # source_assets is not present here; every row carries scalar source_asset.
        observations_all.write_csv(REPORT_DIR / "unresolved_source_observations.csv")

    payload = {
        "report_schema_version": 1,
        "season": SEASON,
        "levels": reports,
        "total_unresolved_player_games": unresolved_all.height,
        "total_unresolved_games": (
            unresolved_all.select("filename_level", "game_id").unique().height
            if unresolved_all.height
            else 0
        ),
        "interpretation": (
            "These are controls intentionally left unresolved by the reusable-data "
            "component-wise dominance rule. No filename/upload chronology is used to "
            "pick a winner. The next decision should be driven by conflict structure "
            "or a targeted official boxscore authority overlay."
        ),
    }
    (REPORT_DIR / "multilevel_player_game_conflicts.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = ["# 2024 multilevel player-game conflict audit", ""]
    for report in reports:
        diagnostics = report["diagnostics"]
        lines.extend(
            [
                f"## {report['level_group']}",
                "",
                f"- Player-games: {diagnostics['resolved_player_game_count']:,}",
                f"- Batting-vector conflicts: {diagnostics['conflicting_player_game_count']:,}",
                f"- Resolved by component-wise dominance: {diagnostics['resolved_by_componentwise_dominance_count']:,}",
                f"- Unresolved conflict player-games: {diagnostics['unresolved_conflicting_player_game_count']:,}",
                f"- Metadata conflict player-games: {diagnostics['metadata_conflict_player_game_count']:,}",
                f"- Unresolved expected-contact player-games: {diagnostics['unresolved_expected_contact_player_game_count']:,}",
                f"- Unresolved games: {report['unresolved_game_count']:,}",
                f"- By actual league: {report['unresolved_by_league']}",
                "",
            ]
        )
    summary = "\n".join(lines)
    (REPORT_DIR / "multilevel_player_game_conflicts.md").write_text(
        summary, encoding="utf-8"
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
