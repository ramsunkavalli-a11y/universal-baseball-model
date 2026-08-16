#!/usr/bin/env python
"""Audit full-season MiLB player-game outcomes against season-player aggregates.

This intentionally runs before historical PBP materialization. The two armstjc
release families are independently downloaded and compared at player × actual-
league × season grain for PA, BB, HBP, and strikeouts. Team rows are summed
within actual league. Discrepancies are persisted without synthetic repair.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import polars as pl
import requests

from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.current_talent_era import current_talent_level_spec
from universal_baseball.current_talent_milb_evidence import (
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


GAME_TYPE = "R"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--level", choices=("aaa", "aa", "a+", "a", "rk"), required=True)
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("data/quarantine/current-talent-historical-outcome-backbone"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/current-talent-historical-outcome-backbone"),
    )
    return parser.parse_args()


def _github_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-historical-outcome-audit/0.1"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def main() -> int:
    args = parse_args()
    spec = current_talent_level_spec(args.season, args.level)
    work_dir = args.work_root / str(args.season) / args.level
    report_dir = args.report_root / str(args.season) / args.level
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    session = _github_session()
    try:
        game_assets = [
            asset
            for asset in fetch_player_game_asset_inventory(session=session)
            if asset.year == args.season and asset.filename_level == args.level
        ]
        if not game_assets:
            raise RuntimeError(f"no {args.season} {args.level} player-game assets found")

        outcome_frames: list[pl.DataFrame] = []
        game_dir = work_dir / "player-game"
        game_dir.mkdir(parents=True, exist_ok=True)
        for asset in game_assets:
            path = game_dir / asset.name
            if not path.exists() or path.stat().st_size <= 0:
                download_file(asset.browser_download_url, path, timeout_seconds=240)
            raw = read_quarantined_csv(path)
            outcome_frames.append(
                project_milb_player_game_outcomes(
                    raw,
                    source_asset=asset.name,
                    season=args.season,
                    game_type=GAME_TYPE,
                )
            )

        outcome_observations = pl.concat(outcome_frames, how="vertical_relaxed")
        resolved, resolution_metrics = resolve_milb_player_game_outcomes(outcome_observations)
        if resolution_metrics["unresolved_player_game_count"]:
            unresolved = resolved.filter(pl.col("outcome_resolution").str.starts_with("unresolved"))
            unresolved.write_csv(report_dir / "unresolved_player_games.csv")
            raise RuntimeError(
                f"{args.season} {args.level} has unresolved player-game outcomes: "
                f"{resolution_metrics['unresolved_player_game_count']}"
            )

        batting_inventory = fetch_season_stat_asset_inventory("batting", session=session)
        season_asset = select_season_stat_asset(
            batting_inventory,
            year=args.season,
            filename_level=args.level,
            kind="batting",
            require_nonempty=True,
        )
        season_path = work_dir / season_asset.name
        if not season_path.exists() or season_path.stat().st_size <= 0:
            download_file(season_asset.browser_download_url, season_path, timeout_seconds=240)
        season_raw = read_quarantined_csv(season_path)
        season_standardized, season_schema_metrics = standardize_armstjc_season_stats(
            season_raw, "batting"
        )
    finally:
        session.close()

    comparison, reconciliation = reconcile_resolved_outcomes_to_season_aggregates(
        resolved,
        season_standardized,
        season=args.season,
        expected_league_ids=spec.league_ids,
        require_exact=False,
    )
    mismatch = comparison.filter(pl.col("has_any_mismatch"))
    if not mismatch.is_empty():
        mismatch.write_csv(report_dir / "outcome_mismatches.csv")
        mismatch.sort(
            "plate_appearances_difference",
            descending=True,
        ).head(100).write_csv(report_dir / "top_outcome_mismatches.csv")

    report = {
        "report_schema_version": 1,
        "season": args.season,
        "filename_level": args.level,
        "level_group": spec.level_group,
        "actual_league_ids": sorted(spec.league_ids),
        "player_game_assets": [asset.name for asset in game_assets],
        "player_game_asset_count": len(game_assets),
        "season_asset": season_asset.as_record(),
        "season_schema": season_schema_metrics,
        "outcome_resolution": resolution_metrics,
        "season_reconciliation": reconciliation,
        "accepted_for_contact_materialization": bool(
            resolution_metrics["unresolved_player_game_count"] == 0
            and reconciliation["exact_reconciliation"]
        ),
        "interpretation": (
            "Independent outcome-backbone admission gate only. No mismatches are repaired and no "
            "contact/profile evidence or Current Talent estimate is created here."
        ),
    }
    (report_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    pa = reconciliation["fields"]["plate_appearances"]
    walks = reconciliation["fields"]["walks"]
    hbp = reconciliation["fields"]["hit_by_pitch"]
    strikeouts = reconciliation["fields"]["strikeouts"]
    text = "\n".join(
        [
            f"# Historical outcome backbone — {args.season} {spec.display_name}",
            "",
            f"- Player-game assets: {len(game_assets)}",
            f"- Season aggregate asset: {season_asset.name} ({season_asset.size_bytes:,} bytes)",
            f"- Resolved player-games: {resolution_metrics['resolved_player_game_count']:,}",
            f"- Unresolved player-games: {resolution_metrics['unresolved_player_game_count']:,}",
            f"- Player-league mismatches: {reconciliation['mismatch_player_league_count']:,}",
            f"- PA: game={pa['game_total']:,}, season={pa['season_total']:,}, diff={pa['signed_difference']:+,}",
            f"- BB: game={walks['game_total']:,}, season={walks['season_total']:,}, diff={walks['signed_difference']:+,}",
            f"- HBP: game={hbp['game_total']:,}, season={hbp['season_total']:,}, diff={hbp['signed_difference']:+,}",
            f"- K: game={strikeouts['game_total']:,}, season={strikeouts['season_total']:,}, diff={strikeouts['signed_difference']:+,}",
            f"- Exact reconciliation: {reconciliation['exact_reconciliation']}",
            f"- Accepted for contact materialization: {report['accepted_for_contact_materialization']}",
        ]
    )
    (report_dir / "report.md").write_text(text, encoding="utf-8")
    print(text)

    # A non-exact reconciliation is a *diagnostic result*, not a crashed audit.
    # Structural/schema failures still raise before this point. Persist the
    # mismatch evidence and let the next review decide whether a source defect or
    # semantic rule explains it.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
