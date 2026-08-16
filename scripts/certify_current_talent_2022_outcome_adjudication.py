#!/usr/bin/env python
"""Certify residual-triggered official game-log adjudication on full 2022 MiLB.

The season-player aggregate is used only to identify player × actual-league
residuals.  Each residual is then adjudicated at game grain with current official
Stats API gameLog evidence. Exact official bytes are persisted. The resulting
corrected player-game table is retrospective corrected-event history and is not a
vintage information-set reconstruction.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import polars as pl
import requests

from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.current_talent_era import current_talent_level_spec
from universal_baseball.current_talent_milb_evidence import (
    project_milb_player_game_outcomes,
    resolve_milb_player_game_outcomes,
)
from universal_baseball.current_talent_official_outcomes import (
    apply_official_game_log_outcome_authority,
    official_game_log_endpoint,
    project_official_hitting_game_log,
)
from universal_baseball.current_talent_season_reconciliation import (
    reconcile_resolved_outcomes_to_season_aggregates,
)
from universal_baseball.official_capture import capture_official_json, new_official_session
from universal_baseball.player_game_stats import fetch_player_game_asset_inventory
from universal_baseball.season_stat_assets import (
    fetch_season_stat_asset_inventory,
    select_season_stat_asset,
)
from universal_baseball.season_stats import standardize_armstjc_season_stats
from universal_baseball.storage import write_canonical_parquet


SEASON = 2022
GAME_TYPE = "R"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", choices=("aaa", "aa", "a+", "a", "rk"), required=True)
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("data/quarantine/current-talent-2022-outcome-adjudication"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/current-talent-2022-outcome-adjudication"),
    )
    return parser.parse_args()


def _github_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-2022-outcome-adjudication/0.1"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def _load_sources(level: str, work_dir: Path) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    session = _github_session()
    try:
        game_assets = [
            asset
            for asset in fetch_player_game_asset_inventory(session=session)
            if asset.year == SEASON and asset.filename_level == level
        ]
        if not game_assets:
            raise RuntimeError(f"no {SEASON} {level} player-game assets found")
        game_dir = work_dir / "player-game"
        game_dir.mkdir(parents=True, exist_ok=True)
        frames: list[pl.DataFrame] = []
        for asset in game_assets:
            path = game_dir / asset.name
            if not path.exists() or path.stat().st_size <= 0:
                download_file(asset.browser_download_url, path, timeout_seconds=240)
            raw = read_quarantined_csv(path)
            frames.append(
                project_milb_player_game_outcomes(
                    raw,
                    source_asset=asset.name,
                    season=SEASON,
                    game_type=GAME_TYPE,
                )
            )
        resolved, resolution = resolve_milb_player_game_outcomes(
            pl.concat(frames, how="vertical_relaxed")
        )
        if resolution["unresolved_player_game_count"]:
            raise RuntimeError(f"{level} has unresolved source player-game outcomes")

        batting_inventory = fetch_season_stat_asset_inventory("batting", session=session)
        season_asset = select_season_stat_asset(
            batting_inventory,
            year=SEASON,
            filename_level=level,
            kind="batting",
            require_nonempty=True,
        )
        season_path = work_dir / season_asset.name
        if not season_path.exists() or season_path.stat().st_size <= 0:
            download_file(season_asset.browser_download_url, season_path, timeout_seconds=240)
        season_raw = read_quarantined_csv(season_path)
        standardized, season_schema = standardize_armstjc_season_stats(season_raw, "batting")
    finally:
        session.close()
    return resolved, standardized, {
        "player_game_assets": [asset.name for asset in game_assets],
        "player_game_resolution": resolution,
        "season_asset": season_asset.as_record(),
        "season_schema": season_schema,
    }


def _key_set(frame: pl.DataFrame) -> set[tuple[int, int]]:
    if frame.is_empty():
        return set()
    return {
        (int(row["league_id"]), int(row["player_id"]))
        for row in frame.select("league_id", "player_id").to_dicts()
    }


def main() -> int:
    args = parse_args()
    spec = current_talent_level_spec(SEASON, args.level)
    work_dir = args.work_root / args.level
    report_dir = args.report_root / args.level
    raw_official_dir = report_dir / "official-raw"
    table_dir = report_dir / "tables"
    for path in (work_dir, raw_official_dir, table_dir):
        path.mkdir(parents=True, exist_ok=True)

    resolved, season_stats, source_metrics = _load_sources(args.level, work_dir)
    pre_comparison, pre_metrics = reconcile_resolved_outcomes_to_season_aggregates(
        resolved,
        season_stats,
        season=SEASON,
        expected_league_ids=spec.league_ids,
        require_exact=False,
    )
    pre_mismatch = pre_comparison.filter(pl.col("has_any_mismatch"))
    corrected = resolved.with_columns(pl.lit("player_game_source").alias("outcome_authority"))
    adjudication_tables: list[pl.DataFrame] = []
    adjudication_metrics: list[dict[str, Any]] = []
    official_snapshots: list[dict[str, Any]] = []

    official_session = new_official_session()
    try:
        for row in pre_mismatch.select("league_id", "player_id").unique().sort(
            ["league_id", "player_id"]
        ).to_dicts():
            league_id = int(row["league_id"])
            player_id = int(row["player_id"])
            endpoint = official_game_log_endpoint(
                player_id=player_id,
                sport_id=spec.official_sport_id,
                season=SEASON,
            )
            capture = capture_official_json(endpoint, session=official_session)
            raw_path = raw_official_dir / f"player_{player_id}_sport_{spec.official_sport_id}_gamelog.json"
            capture.write_raw(raw_path)
            if not isinstance(capture.data, dict):
                raise RuntimeError(f"official gameLog for player {player_id} is not an object")
            official = project_official_hitting_game_log(
                capture.data,
                player_id=player_id,
                sport_id=spec.official_sport_id,
            )
            corrected, evidence, metrics = apply_official_game_log_outcome_authority(
                corrected,
                official,
                player_id=player_id,
                league_id=league_id,
            )
            if not evidence.is_empty():
                adjudication_tables.append(evidence)
            adjudication_metrics.append(metrics)
            official_snapshots.append(
                {
                    "player_id": player_id,
                    "league_id": league_id,
                    "endpoint": capture.endpoint,
                    "url": capture.url,
                    "retrieved_at_utc": capture.retrieved_at_utc.isoformat(),
                    "content_sha256": capture.content_sha256,
                    "raw_path": str(raw_path),
                }
            )
    finally:
        official_session.close()

    post_comparison, post_metrics = reconcile_resolved_outcomes_to_season_aggregates(
        corrected,
        season_stats,
        season=SEASON,
        expected_league_ids=spec.league_ids,
        require_exact=False,
    )
    post_mismatch = post_comparison.filter(pl.col("has_any_mismatch"))
    pre_keys = _key_set(pre_mismatch)
    post_keys = _key_set(post_mismatch)
    if not post_keys.issubset(pre_keys):
        raise RuntimeError(f"official adjudication introduced new season residual keys: {post_keys - pre_keys}")
    if len(adjudication_metrics) != len(pre_keys):
        raise RuntimeError("not every pre-adjudication residual player/league received official review")

    evidence = (
        pl.concat(adjudication_tables, how="vertical_relaxed")
        if adjudication_tables
        else pl.DataFrame(
            schema={
                "player_id": pl.Int64,
                "league_id": pl.Int64,
                "game_id": pl.Int64,
                "field": pl.String,
                "source_value": pl.Int64,
                "official_value": pl.Int64,
                "action": pl.String,
                "source_game_date": pl.Date,
                "official_game_date": pl.Date,
                "retained_game_date": pl.Date,
                "game_date_authority": pl.String,
            }
        )
    )
    if not evidence.is_empty():
        evidence.write_csv(report_dir / "official_game_log_adjudication.csv")
    if not post_mismatch.is_empty():
        post_mismatch.write_csv(report_dir / "remaining_season_asset_residuals.csv")

    corrected_storage = write_canonical_parquet(
        corrected,
        table_dir / f"current_talent_outcomes_{SEASON}_{args.level}_adjudicated.parquet",
        table_name=f"current_talent_outcomes_{SEASON}_{args.level}_adjudicated",
    ).as_record()
    classification_counts: dict[str, int] = {}
    for metrics in adjudication_metrics:
        key = str(metrics["classification"])
        classification_counts[key] = classification_counts.get(key, 0) + 1

    accepted = bool(
        source_metrics["player_game_resolution"]["unresolved_player_game_count"] == 0
        and len(adjudication_metrics) == len(pre_keys)
        and post_keys.issubset(pre_keys)
    )
    report = {
        "report_schema_version": 1,
        "season": SEASON,
        "filename_level": args.level,
        "level_group": spec.level_group,
        "official_sport_id": spec.official_sport_id,
        "actual_league_ids": sorted(spec.league_ids),
        "source": source_metrics,
        "pre_adjudication_season_reconciliation": pre_metrics,
        "pre_adjudication_residual_player_league_count": len(pre_keys),
        "official_adjudication_count": len(adjudication_metrics),
        "official_adjudication_classification_counts": classification_counts,
        "official_adjudications": adjudication_metrics,
        "official_snapshots": official_snapshots,
        "changed_field_evidence_count": int(evidence.height),
        "post_adjudication_season_reconciliation": post_metrics,
        "remaining_season_asset_residual_player_league_count": len(post_keys),
        "remaining_season_asset_residual_keys": sorted([list(key) for key in post_keys]),
        "corrected_storage": corrected_storage,
        "accepted_for_historical_contact_materialization": accepted,
        "temporal_semantics": "retrospective_event_cutoff_corrected_history_not_vintage_information_set",
        "interpretation": (
            "Season aggregates trigger review but never locate corrections. Current official gameLog "
            "evidence supplies game-grain field authority for residual player/league rows."
        ),
    }
    (report_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    text = "\n".join(
        [
            f"# 2022 outcome adjudication — {spec.display_name}",
            "",
            f"- Pre-adjudication residual player-league rows: {len(pre_keys):,}",
            f"- Official gameLog adjudications: {len(adjudication_metrics):,}",
            f"- Classification counts: {classification_counts}",
            f"- Changed/inserted field evidence rows: {evidence.height:,}",
            f"- Remaining season-asset residual rows: {len(post_keys):,}",
            f"- Accepted for historical contact materialization: {accepted}",
        ]
    )
    (report_dir / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
