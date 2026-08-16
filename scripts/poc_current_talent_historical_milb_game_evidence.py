#!/usr/bin/env python
"""Scoped historical MiLB Current Talent player-game evidence POC.

This gate samples an earlier post-reorganization season before any full history
backfill. It reuses the certified physical-contact, player-game, participant-
authority, and profile taxonomy layers without importing 2024 run values or
season-end Performance tables into historical predictors.

Some older PBP schemas omit ``league_id``.  The POC may enrich that field only
from a unique structured ``game_id -> league_id`` map derived from the same
season's player-game source.  Filename level is never substituted for actual
league identity.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import polars as pl
import requests

from universal_baseball.armstjc_assets import fetch_pbp_asset_inventory
from universal_baseball.armstjc_contacts import (
    contact_resolution_metrics,
    project_armstjc_contact_observations,
    resolve_armstjc_contact_observations,
)
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.contact_identity_overlay import (
    OFFICIAL_SEQUENCE_AUTHORITY_SCHEMA,
    apply_contact_identity_authority_by_sequence,
    contact_identity_residuals,
    exception_games_from_residuals,
    project_official_sequence_authority,
)
from universal_baseball.current_talent_era import current_talent_level_spec
from universal_baseball.current_talent_milb_evidence import (
    build_milb_current_talent_player_game_evidence,
    project_milb_player_game_outcomes,
    resolve_milb_player_game_outcomes,
)
from universal_baseball.current_talent_milb_source import (
    classify_milb_current_talent_contacts,
    derive_player_game_league_map,
    enrich_historical_pbp_league_id,
    validate_expected_actual_leagues,
)
from universal_baseball.official import fetch_official_game_evidence
from universal_baseball.player_game_controls import resolve_player_game_contact_controls
from universal_baseball.player_game_stats import (
    fetch_player_game_asset_inventory,
    project_player_game_batting,
)
from universal_baseball.storage import write_canonical_parquet


GAME_TYPE = "R"
PBP_ASSETS_PER_LEVEL = 2
DEFAULT_GAMES_PER_ACTUAL_LEAGUE = 8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2022)
    parser.add_argument("--level", choices=("aaa", "aa", "a+", "a", "rk"), required=True)
    parser.add_argument("--games-per-league", type=int, default=DEFAULT_GAMES_PER_ACTUAL_LEAGUE)
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("data/quarantine/current-talent-historical-milb-poc"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/current-talent-historical-milb-poc"),
    )
    return parser.parse_args()


def _github_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-historical-milb-poc/0.2"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def _evenly_spaced(values: list[int], limit: int) -> list[int]:
    ordered = sorted(set(int(value) for value in values))
    if limit <= 0 or not ordered:
        return []
    if len(ordered) <= limit:
        return ordered
    if limit == 1:
        return [ordered[len(ordered) // 2]]
    indices = [round(i * (len(ordered) - 1) / (limit - 1)) for i in range(limit)]
    return [ordered[index] for index in indices]


def _sample_games(
    contacts: pl.DataFrame,
    *,
    league_ids: frozenset[int],
    games_per_league: int,
) -> tuple[list[int], dict[str, list[int]]]:
    selected: list[int] = []
    by_league: dict[str, list[int]] = {}
    for league_id in sorted(league_ids):
        games = (
            contacts.filter(pl.col("league_id") == league_id)
            .get_column("game_pk")
            .drop_nulls()
            .unique()
            .sort()
            .to_list()
        )
        chosen = _evenly_spaced([int(value) for value in games], games_per_league)
        if not chosen:
            raise RuntimeError(f"league_id={league_id} has no reusable contact games")
        by_league[str(league_id)] = chosen
        selected.extend(chosen)
    return sorted(set(selected)), by_league


def _player_game_assets(
    *,
    season: int,
    level: str,
    session: requests.Session,
) -> list[Any]:
    assets = [
        asset
        for asset in fetch_player_game_asset_inventory(session=session)
        if asset.year == season and asset.filename_level == level
    ]
    if not assets:
        raise RuntimeError(f"no reusable {season} {level} player-game assets found")
    return assets


def _load_game_league_map(
    *,
    assets: list[Any],
    work_dir: Path,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    raw_dir = work_dir / "player-game"
    raw_dir.mkdir(parents=True, exist_ok=True)
    frames: list[pl.DataFrame] = []
    for asset in assets:
        path = raw_dir / asset.name
        if not path.exists() or path.stat().st_size <= 0:
            download_file(asset.browser_download_url, path, timeout_seconds=240)
        raw = read_quarantined_csv(path)
        required = {"game_id", "league_id", "game_type"}
        missing = sorted(required - set(raw.columns))
        if missing:
            raise RuntimeError(f"{asset.name} missing game-league-map fields: {missing}")
        frames.append(raw.select("game_id", "league_id", "game_type"))
    mapping, metrics = derive_player_game_league_map(
        pl.concat(frames, how="vertical_relaxed"),
        game_type=GAME_TYPE,
    )
    return mapping, {
        **metrics,
        "player_game_asset_count": len(assets),
        "player_game_assets": [asset.name for asset in assets],
    }


def _load_contacts(
    *,
    season: int,
    level: str,
    league_ids: frozenset[int],
    game_league_map: pl.DataFrame,
    work_dir: Path,
    session: requests.Session,
    games_per_league: int,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    candidates = [
        asset
        for asset in fetch_pbp_asset_inventory(session=session)
        if asset.year == season and asset.filename_level == level
    ]
    if not candidates:
        raise RuntimeError(f"no reusable {season} {level} PBP assets found")
    chosen = sorted(
        candidates,
        key=lambda asset: (asset.size_bytes, asset.filename_period, asset.asset_id),
        reverse=True,
    )[:PBP_ASSETS_PER_LEVEL]

    pbp_dir = work_dir / "pbp"
    pbp_dir.mkdir(parents=True, exist_ok=True)
    frames: list[pl.DataFrame] = []
    enrichment: list[dict[str, Any]] = []
    for asset in sorted(chosen, key=lambda row: (row.filename_period, row.asset_id)):
        path = pbp_dir / asset.name
        if not path.exists() or path.stat().st_size <= 0:
            download_file(asset.browser_download_url, path, timeout_seconds=300)
        raw = read_quarantined_csv(path)
        enriched, metrics = enrich_historical_pbp_league_id(
            raw,
            game_league_map,
            source_asset=asset.name,
            game_type=GAME_TYPE,
        )
        enrichment.append(metrics)
        frames.append(
            project_armstjc_contact_observations(
                enriched,
                source_asset=asset.name,
                season=season,
                game_type=GAME_TYPE,
            )
        )

    observations = pl.concat(frames, how="vertical_relaxed")
    resolved = resolve_armstjc_contact_observations(observations, contacts_only=False)
    resolution = contact_resolution_metrics(observations, resolved)
    if resolution["contact_status_conflict_key_count"]:
        raise RuntimeError("historical POC has contact-status conflicts")
    contacts = resolved.filter(pl.col("source_is_in_play") == True)  # noqa: E712
    if contacts.filter(pl.col("source_batter_id").is_null()).height:
        raise RuntimeError("historical POC contacts contain unresolved source batter identity")
    all_coverage = validate_expected_actual_leagues(
        contacts,
        league_column="league_id",
        expected_league_ids=league_ids,
        label=f"{season} {level} resolved contacts",
    )
    game_ids, games_by_league = _sample_games(
        contacts,
        league_ids=league_ids,
        games_per_league=games_per_league,
    )
    sample = contacts.filter(pl.col("game_pk").is_in(game_ids))
    sample_coverage = validate_expected_actual_leagues(
        sample,
        league_column="league_id",
        expected_league_ids=league_ids,
        label=f"{season} {level} sampled contacts",
    )
    return sample, {
        "selected_pbp_assets": [asset.name for asset in chosen],
        "league_id_enrichment": enrichment,
        "sample_games_by_league": games_by_league,
        "sample_game_count": len(game_ids),
        "sample_contact_count": sample.height,
        "selected_snapshot_contact_count": contacts.height,
        "all_league_coverage": all_coverage,
        "sample_league_coverage": sample_coverage,
        "resolution": resolution,
    }


def _load_player_games(
    *,
    assets: list[Any],
    season: int,
    level: str,
    sample_games: list[int],
    league_ids: frozenset[int],
    work_dir: Path,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    raw_dir = work_dir / "player-game"
    control_frames: list[pl.DataFrame] = []
    outcome_frames: list[pl.DataFrame] = []
    for asset in assets:
        path = raw_dir / asset.name
        raw = read_quarantined_csv(path)
        control = project_player_game_batting(
            raw, source_asset=asset.name, season=season, game_type=GAME_TYPE
        ).filter(pl.col("game_id").is_in(sample_games))
        outcome = project_milb_player_game_outcomes(
            raw, source_asset=asset.name, season=season, game_type=GAME_TYPE
        ).filter(pl.col("game_id").is_in(sample_games))
        if not control.is_empty():
            control_frames.append(control)
        if not outcome.is_empty():
            outcome_frames.append(outcome)

    if not control_frames or not outcome_frames:
        raise RuntimeError("sample games have no player-game evidence")
    controls, control_metrics = resolve_player_game_contact_controls(
        pl.concat(control_frames, how="vertical_relaxed")
    )
    outcomes, outcome_metrics = resolve_milb_player_game_outcomes(
        pl.concat(outcome_frames, how="vertical_relaxed")
    )
    if control_metrics["unresolved_contact_control_count"]:
        raise RuntimeError("sample contains unresolved contact-control snapshots")
    if outcome_metrics["unresolved_player_game_count"]:
        raise RuntimeError("sample contains unresolved player-game outcome snapshots")

    positive_pa = outcomes.filter(pl.col("batting_PA").is_not_null() & (pl.col("batting_PA") > 0))
    coverage = validate_expected_actual_leagues(
        positive_pa,
        league_column="league_id",
        expected_league_ids=league_ids,
        label=f"{season} {level} sampled player-game outcomes",
    )
    observed_games = set(int(v) for v in positive_pa.get_column("game_id").unique().to_list())
    missing_games = sorted(set(sample_games) - observed_games)
    if missing_games:
        raise RuntimeError(f"sample contact games missing positive-PA boxscores: {missing_games}")
    return controls, outcomes, {
        "contact_controls": control_metrics,
        "outcomes": outcome_metrics,
        "league_coverage": coverage,
    }


def _apply_participant_authority(
    contacts: pl.DataFrame,
    controls: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    residuals = contact_identity_residuals(contacts, controls)
    exception_games = exception_games_from_residuals(residuals)
    if exception_games:
        official_sequences, _ = fetch_official_game_evidence(exception_games)
        authority = project_official_sequence_authority(official_sequences)
    else:
        authority = pl.DataFrame(schema=OFFICIAL_SEQUENCE_AUTHORITY_SCHEMA)
    authorized, metrics = apply_contact_identity_authority_by_sequence(
        contacts, controls, authority
    )
    nonzero = residuals.filter(pl.col("contact_count_difference") != 0)
    return authorized, {
        **metrics,
        "nonzero_player_game_residual_count": nonzero.height,
        "absolute_player_game_residual_mass": int(
            nonzero.select(pl.col("contact_count_difference").abs().sum()).item() or 0
        ),
    }


def main() -> int:
    args = parse_args()
    spec = current_talent_level_spec(args.season, args.level)
    work_dir = args.work_root / str(args.season) / args.level
    report_dir = args.report_root / str(args.season) / args.level
    table_dir = report_dir / "tables"
    for path in (work_dir, table_dir):
        path.mkdir(parents=True, exist_ok=True)

    session = _github_session()
    try:
        player_game_assets = _player_game_assets(
            season=args.season,
            level=args.level,
            session=session,
        )
        game_league_map, league_map_metrics = _load_game_league_map(
            assets=player_game_assets,
            work_dir=work_dir,
        )
        contacts, contact_metrics = _load_contacts(
            season=args.season,
            level=args.level,
            league_ids=spec.league_ids,
            game_league_map=game_league_map,
            work_dir=work_dir,
            session=session,
            games_per_league=args.games_per_league,
        )
        sample_games = sorted(int(v) for v in contacts.get_column("game_pk").unique().to_list())
        controls, outcomes, player_game_metrics = _load_player_games(
            assets=player_game_assets,
            season=args.season,
            level=args.level,
            sample_games=sample_games,
            league_ids=spec.league_ids,
            work_dir=work_dir,
        )
    finally:
        session.close()

    authorized, authority_metrics = _apply_participant_authority(contacts, controls)
    classified = classify_milb_current_talent_contacts(authorized)
    if set(int(v) for v in classified.get_column("season").unique().to_list()) != {args.season}:
        raise RuntimeError("classified historical contacts contain wrong event season")

    summary, profile, evidence_metrics = build_milb_current_talent_player_game_evidence(
        outcomes, classified
    )
    summary = summary.filter(pl.col("game_pk").is_in(sample_games))
    profile = profile.filter(pl.col("game_pk").is_in(sample_games))
    summary_games = int(summary.get_column("game_pk").n_unique())
    if summary_games != len(sample_games):
        raise RuntimeError(
            f"Current Talent evidence lost sample games: {summary_games} vs {len(sample_games)}"
        )
    if evidence_metrics["season_count"] != 1:
        raise RuntimeError("historical game evidence unexpectedly spans multiple seasons")
    if evidence_metrics["actual_league_count"] != len(spec.league_ids):
        raise RuntimeError("historical game evidence lost actual-league coverage")

    summary_storage = write_canonical_parquet(
        summary,
        table_dir / f"current_talent_game_summary_{args.season}_{args.level}_poc.parquet",
        table_name=f"current_talent_game_summary_{args.season}_{args.level}_poc",
    ).as_record()
    profile_storage = write_canonical_parquet(
        profile,
        table_dir / f"current_talent_game_profile_{args.season}_{args.level}_poc.parquet",
        table_name=f"current_talent_game_profile_{args.season}_{args.level}_poc",
    ).as_record()

    output = {
        "player_game_summary_rows": summary.height,
        "player_game_profile_rows": profile.height,
        "game_count": summary_games,
        "plate_appearances": int(summary.get_column("batting_plate_appearances").sum() or 0),
        "core_profile_events": int(summary.get_column("core_profile_event_count").sum() or 0),
        "observed_contacts": int(summary.get_column("observed_contact_count").sum() or 0),
        "contact_residual": int(summary.get_column("contact_count_residual").sum() or 0),
    }
    report = {
        "report_schema_version": 3,
        "season": args.season,
        "filename_level": args.level,
        "level_group": spec.level_group,
        "actual_league_ids": sorted(spec.league_ids),
        "game_league_map": league_map_metrics,
        "contacts": contact_metrics,
        "player_game": player_game_metrics,
        "participant_authority": authority_metrics,
        "evidence": evidence_metrics,
        "output": output,
        "storage": {"summary": summary_storage, "profile": profile_storage},
        "accepted": True,
        "interpretation": (
            "Scoped historical observed game evidence only; no environment translation, talent "
            "estimate, age adjustment, projection, playing time, WAR, or ranking."
        ),
    }
    (report_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    text = "\n".join(
        [
            f"# Historical Current Talent MiLB game evidence — {args.season} {spec.display_name}",
            "",
            f"- Actual leagues: {sorted(spec.league_ids)}",
            f"- Sample games: {len(sample_games):,}",
            f"- Player-games: {summary.height:,}",
            f"- PA: {output['plate_appearances']:,}",
            f"- Observed contacts: {output['observed_contacts']:,}",
            f"- Contact residual: {output['contact_residual']:+,}",
            f"- Official participant exception games: {authority_metrics['exception_game_count']:,}",
            f"- Official batter changes: {authority_metrics['changed_batter_contact_count']:,}",
            "- Accepted: True",
        ]
    )
    (report_dir / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
