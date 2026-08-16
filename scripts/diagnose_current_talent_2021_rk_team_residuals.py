#!/usr/bin/env python
"""Localize 2021 Rookie Current Talent season residuals by team.

This diagnostic tests whether the sparse player × league residuals between the
reusable player-game history and the independent season batting release are
actually concentrated in one team/stint. Ambiguous raw game/player team keys
are preserved as diagnostics and excluded from team attribution rather than
silently resolved. The script does not mutate either source and does not relax
the Current Talent admission gate.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import polars as pl
import requests

from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.current_talent_milb_evidence import (
    OUTCOME_FIELDS,
    project_milb_player_game_outcomes,
    resolve_milb_player_game_outcomes,
)
from universal_baseball.current_talent_season_reconciliation import (
    reconcile_resolved_outcomes_to_season_aggregates,
)
from universal_baseball.player_game_stats import fetch_player_game_asset_inventory
from universal_baseball.season_stat_assets import (
    fetch_season_stat_asset_inventory,
    select_season_stat_asset,
)
from universal_baseball.season_stats import standardize_armstjc_season_stats


SEASON = 2021
LEVEL = "rk"
LEAGUE_ID = 130
GAME_TYPE = "R"


def _github_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-2021-rk-team-residuals/0.1"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def main() -> int:
    work_root = Path("data/quarantine/current-talent-2021-rk-team-residuals")
    report_root = Path("reports/generated/current-talent-outcome-residual-case")
    player_game_dir = work_root / "player-game"
    season_dir = work_root / "season"
    for path in (work_root, report_root, player_game_dir, season_dir):
        path.mkdir(parents=True, exist_ok=True)

    session = _github_session()
    try:
        assets = [
            asset
            for asset in fetch_player_game_asset_inventory(session=session)
            if asset.year == SEASON and asset.filename_level == LEVEL
        ]
        if not assets:
            raise RuntimeError("no reusable 2021 Rookie player-game assets found")

        outcome_frames: list[pl.DataFrame] = []
        team_map_frames: list[pl.DataFrame] = []
        for asset in assets:
            path = player_game_dir / asset.name
            if not path.exists() or path.stat().st_size <= 0:
                download_file(asset.browser_download_url, path, timeout_seconds=240)
            raw = read_quarantined_csv(path)
            required = {"game_id", "game_type", "league_id", "player_id", "team_id", "team_name"}
            missing = sorted(required - set(raw.columns))
            if missing:
                raise RuntimeError(f"{asset.name} missing team-diagnostic fields: {missing}")
            team_map_frames.append(
                raw.select(
                    pl.col("game_id").cast(pl.Int64, strict=False),
                    pl.col("game_type").cast(pl.String),
                    pl.col("league_id").cast(pl.Int64, strict=False),
                    pl.col("player_id").cast(pl.Int64, strict=False),
                    pl.col("team_id").cast(pl.Int64, strict=False),
                    pl.col("team_name").cast(pl.String),
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

        resolved, resolution_metrics = resolve_milb_player_game_outcomes(
            pl.concat(outcome_frames, how="vertical_relaxed")
        )
        if resolution_metrics["unresolved_player_game_count"]:
            raise RuntimeError("2021 Rookie has unresolved player-game outcomes")

        raw_team_map = (
            pl.concat(team_map_frames, how="vertical_relaxed")
            .filter(
                (pl.col("game_type") == GAME_TYPE)
                & (pl.col("league_id") == LEAGUE_ID)
                & pl.col("game_id").is_not_null()
                & pl.col("player_id").is_not_null()
                & pl.col("team_id").is_not_null()
            )
            .select("game_id", "player_id", "team_id", "team_name")
            .unique()
        )
        team_key_counts = raw_team_map.group_by(["game_id", "player_id"]).agg(
            pl.col("team_id").n_unique().alias("team_count")
        )
        team_conflicts = team_key_counts.filter(pl.col("team_count") != 1)
        conflict_detail = raw_team_map.join(
            team_conflicts.select("game_id", "player_id"),
            on=["game_id", "player_id"],
            how="inner",
        ).sort(["game_id", "player_id", "team_id"])
        if not conflict_detail.is_empty():
            conflict_detail.write_csv(report_root / "raw_team_conflicts.csv")
        valid_team_keys = team_key_counts.filter(pl.col("team_count") == 1).select(
            "game_id", "player_id"
        )
        team_map = (
            raw_team_map.join(
                valid_team_keys,
                on=["game_id", "player_id"],
                how="inner",
            )
            .unique(["game_id", "player_id"], keep="first")
        )

        season_inventory = fetch_season_stat_asset_inventory("batting", session=session)
        season_asset = select_season_stat_asset(
            season_inventory,
            year=SEASON,
            filename_level=LEVEL,
            kind="batting",
            require_nonempty=True,
        )
        season_path = season_dir / season_asset.name
        if not season_path.exists() or season_path.stat().st_size <= 0:
            download_file(season_asset.browser_download_url, season_path, timeout_seconds=240)
        season_raw = read_quarantined_csv(season_path)
        season_stats, season_schema_metrics = standardize_armstjc_season_stats(
            season_raw, "batting"
        )
    finally:
        session.close()

    comparison, reconciliation_metrics = reconcile_resolved_outcomes_to_season_aggregates(
        resolved,
        season_stats,
        season=SEASON,
        require_exact=False,
    )
    residuals = comparison.filter(
        (pl.col("league_id") == LEAGUE_ID) & pl.col("has_any_mismatch")
    )
    if residuals.is_empty():
        raise RuntimeError("expected 2021 DSL residuals but found none")
    residual_player_ids = residuals.get_column("player_id").unique().to_list()

    source_games_all = (
        resolved.filter(
            (pl.col("league_id") == LEAGUE_ID)
            & (pl.col("game_type") == GAME_TYPE)
            & pl.col("player_id").is_in(residual_player_ids)
            & pl.col("batting_PA").is_not_null()
            & (pl.col("batting_PA") > 0)
        )
        .join(team_map, on=["game_id", "player_id"], how="left")
    )
    missing_team = source_games_all.filter(pl.col("team_id").is_null()).sort(
        ["player_id", "game_id"]
    )
    if not missing_team.is_empty():
        missing_team.write_csv(report_root / "residual_source_games_without_unique_team.csv")
    source_games = source_games_all.filter(pl.col("team_id").is_not_null())
    if source_games.is_empty():
        raise RuntimeError("no residual-player games have unambiguous raw team attribution")

    source_by_player_team = (
        source_games.group_by(["player_id", "team_id", "team_name"])
        .agg(
            pl.col("game_id").n_unique().alias("game_count"),
            *[
                pl.col(field).sum().cast(pl.Int64).alias(field)
                for field in OUTCOME_FIELDS
            ],
        )
        .sort(["team_id", "player_id"])
    )
    source_by_player_team.write_csv(report_root / "residual_source_by_player_team.csv")

    season_target = season_stats.filter(
        (pl.col("season").cast(pl.Int64, strict=False) == SEASON)
        & (pl.col("league_id").cast(pl.Int64, strict=False) == LEAGUE_ID)
        & pl.col("player_id").cast(pl.Int64, strict=False).is_in(residual_player_ids)
        & pl.col("batting_plate_appearances").cast(pl.Int64, strict=False).is_not_null()
        & (pl.col("batting_plate_appearances").cast(pl.Int64, strict=False) > 0)
    )
    season_by_player_team = (
        season_target.select(
            pl.col("player_id").cast(pl.Int64, strict=False),
            pl.col("team_id").cast(pl.Int64, strict=False),
            pl.col("team_name").cast(pl.String),
            pl.col("batting_plate_appearances").cast(pl.Int64, strict=False).alias("batting_PA"),
            pl.col("batting_base_on_balls").cast(pl.Int64, strict=False).alias("batting_BB"),
            pl.col("batting_hit_by_pitch").cast(pl.Int64, strict=False).alias("batting_HBP"),
            pl.col("batting_strike_outs").cast(pl.Int64, strict=False).alias("batting_SO"),
        )
        .sort(["team_id", "player_id"])
    )
    season_by_player_team.write_csv(report_root / "residual_season_by_player_team.csv")

    source_team_summary = (
        source_by_player_team.group_by(["team_id", "team_name"])
        .agg(
            pl.col("player_id").n_unique().alias("residual_player_count"),
            pl.col("game_count").sum().alias("player_game_count"),
            pl.col("batting_PA").sum().alias("batting_PA"),
            pl.col("batting_BB").sum().alias("batting_BB"),
            pl.col("batting_HBP").sum().alias("batting_HBP"),
            pl.col("batting_SO").sum().alias("batting_SO"),
        )
        .sort("team_id")
    )
    season_team_summary = (
        season_by_player_team.group_by(["team_id", "team_name"])
        .agg(
            pl.col("player_id").n_unique().alias("residual_player_count"),
            pl.col("batting_PA").sum().alias("batting_PA"),
            pl.col("batting_BB").sum().alias("batting_BB"),
            pl.col("batting_HBP").sum().alias("batting_HBP"),
            pl.col("batting_SO").sum().alias("batting_SO"),
        )
        .sort("team_id")
    )
    source_team_summary.write_csv(report_root / "residual_source_team_summary.csv")
    season_team_summary.write_csv(report_root / "residual_season_team_summary.csv")

    source_team_611 = source_team_summary.filter(pl.col("team_id") == 611).to_dicts()
    season_team_611 = season_team_summary.filter(pl.col("team_id") == 611).to_dicts()
    report = {
        "report_schema_version": 2,
        "season": SEASON,
        "level": LEVEL,
        "league_id": LEAGUE_ID,
        "residual_player_league_count": int(residuals.height),
        "residual_player_ids": [int(value) for value in sorted(residual_player_ids)],
        "raw_team_conflict_key_count": int(team_conflicts.height),
        "raw_team_conflict_row_count": int(conflict_detail.height),
        "residual_source_game_count": int(source_games_all.height),
        "residual_source_game_without_unique_team_count": int(missing_team.height),
        "residual_source_game_with_unique_team_count": int(source_games.height),
        "source_team_summary": source_team_summary.to_dicts(),
        "season_team_summary": season_team_summary.to_dicts(),
        "source_team_611": source_team_611,
        "season_team_611": season_team_611,
        "player_game_resolution": resolution_metrics,
        "reconciliation": reconciliation_metrics,
        "season_asset": season_asset.as_record(),
        "season_schema": season_schema_metrics,
        "accepted": False,
        "interpretation": (
            "Diagnostic only. Concentration of unambiguously attributed residual-player PA in a "
            "source team that is absent or incomplete in the season release is evidence of season-"
            "aggregate coverage drift. Ambiguous team keys remain explicitly unassigned and are not "
            "used to justify chronology or identity repair."
        ),
    }
    (report_root / "team_residual_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    text = "\n".join(
        [
            "# 2021 Rookie Current Talent residuals by team",
            "",
            f"- DSL residual player-league rows: {residuals.height}",
            f"- Raw team-conflict game/player keys: {team_conflicts.height}",
            f"- Residual-player games without unique team: {missing_team.height}/{source_games_all.height}",
            f"- Source teams represented (unambiguous only): {source_team_summary.height}",
            f"- Season teams represented for those players: {season_team_summary.height}",
            f"- Source team 611 rows: {source_team_611}",
            f"- Season team 611 rows: {season_team_611}",
        ]
    )
    (report_root / "team_residual_report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
