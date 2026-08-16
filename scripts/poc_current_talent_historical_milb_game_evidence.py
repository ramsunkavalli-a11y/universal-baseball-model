#!/usr/bin/env python
"""Scoped historical MiLB Current Talent player-game evidence POC.

The first historical gate intentionally samples games rather than backfilling a
whole season. It verifies that the already-certified 2024 source architecture
survives an earlier post-reorganization season without importing 2024 run values
or season-end Performance tables into the predictor surface.

For one explicit season + filename level the POC:

1. selects two large reusable PBP snapshots and resolves physical contact evidence;
2. samples regular-season games across every era-certified actual league;
3. resolves player-game contact controls and outcome evidence only for those games;
4. triggers official top-level matchup-batter authority only for residual games;
5. classifies the preserved historical contacts into the frozen 12-bin profile;
6. builds the canonical Current Talent player-game evidence contract; and
7. persists only observed game-grain evidence plus diagnostics.

No environment translation, run-value calibration, age prior, talent estimate,
projection, playing time, WAR, or ranking is fitted here.
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
GAMES_PER_ACTUAL_LEAGUE = 8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2022)
    parser.add_argument("--level", choices=("aaa", "aa", "a+", "a", "rk"), required=True)
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
    parser.add_argument("--games-per-league", type=int, default=GAMES_PER_ACTUAL_LEAGUE)
    return parser.parse_args()


def _github_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-historical-milb-poc/0.1"
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


def _select_sample_games(
    contacts: pl.DataFrame,
    *,
    league_ids: frozenset[int],
    games_per_league: int,
) -> tuple[list[int], dict[str, list[int]]]:
    selected: list[int] = []
    by_league: dict[str, list[int]] = {}
    for league_id in sorted(league_ids):
        games = (
            contacts.filter(pl.col("league_id") == int(league_id))
            .get_column("game_pk")
            .drop_nulls()
            .unique()
            .sort()
            .to_list()
        )
        chosen = _evenly_spaced([int(value) for value in games], games_per_league)
        if not chosen:
            raise RuntimeError(f"league_id={league_id} has no reusable contact games in POC source")
        by_league[str(int(league_id))] = chosen
        selected.extend(chosen)
    return sorted(set(selected)), by_league


def _load_contact_sample(
    *,
    season: int,
    level: str,
    league_ids: frozenset[int],
    work_dir: Path,
    github_session: requests.Session,
    games_per_league: int,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    inventory = [
        asset
        for asset in fetch_pbp_asset_inventory(session=github_session)
        if asset.year == season and asset.filename_level == level
    ]
    if not inventory:
        raise RuntimeError(f"no reusable {season} {level} PBP assets found")
    chosen_assets = sorted(
        inventory,
        key=lambda asset: (asset.size_bytes, asset.filename_period, asset.asset_id),
        reverse=True,
    )[:PBP_ASSETS_PER_LEVEL]

    pbp_dir = work_dir / "pbp"
    pbp_dir.mkdir(parents=True, exist_ok=True)
    frames: list[pl.DataFrame] = []
    for asset in sorted(chosen_assets, key=lambda row: (row.filename_period, row.asset_id)):
        path = pbp_dir / asset.name
        if not path.exists() or path.stat().st_size <= 0:
            download_file(asset.browser_download_url, path, timeout_seconds=300)
        raw = read_quarantined_csv(path)
        frames.append(
            project_armstjc_contact_observations(
                raw,
                source_asset=asset.name,
                season=season,
                game_type=GAME_TYPE,
            )
        )
        del raw

    observations = pl.concat(frames, how="vertical_relaxed")
    resolved_all = resolve_armstjc_contact_observations(observations, contacts_only=False)
    resolution = contact_resolution_metrics(observations, resolved_all)
    if resolution["contact_status_conflict_key_count"]:
        raise RuntimeError(
            f"{season} {level} has contact-status conflicts in selected historical snapshots"
        )
    contacts = resolved_all.filter(pl.col("source_is_in_play") == True)  # noqa: E712
    if contacts.filter(pl.col("source_batter_id").is_null()).height:
        raise RuntimeError(f"{season} {level} historical contacts contain unresolved source batter")
    coverage = validate_expected_actual_leagues(
        contacts,
        league_column="league_id",
        expected_league_ids=league_ids,
        label=f"{season} {level} resolved contacts",
    )
    sample_games, sample_by_league = _select_sample_games(
        contacts,
        league_ids=league_ids,
        games_per_league=games_per_league,
    )
    sample = contacts.filter(pl.col("game_pk").is_in(sample_games))
    sample_coverage = validate_expected_actual_leagues(
        sample,
        league_column="league_id",
        expected_league_ids=league_ids,
        label=f"{season} {level} sampled contacts",
    )
    return sample, {
        "selected_pbp_assets": [asset.name for asset in chosen_assets],
        "selected_pbp_asset_count": len(chosen_assets),
        "sample_game_count": len(sample_games),
        "sample_games_by_league": sample_by_league,
        "sample_contact_count": sample.height,
        "all_selected_snapshot_contact_count": contacts.height,
        "league_coverage": coverage,
        "sample_league_coverage": sample_coverage,
        "resolution": resolution,
    }


def _load_player_game_sample(
    *,
    season: int,
    level: str,
    sample_games: list[int],
    league_ids: frozenset[int],
    work_dir: Path,
    github_session: requests.Session,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    inventory = [
        asset
        for asset in fetch_player_game_asset_inventory(session=github_session)
        if asset.year == season and asset.filename_level == level
    ]
    if not inventory:
        raise RuntimeError(f"no reusable {season} {level} player-game assets found")

    raw_dir = work_dir / "player-game"
    raw_dir.mkdir(parents=True, exist_ok=True)
    control_frames: list[pl.DataFrame] = []
    outcome_frames: list[pl.DataFrame] = []
    for asset in inventory:
        path = raw_dir / asset.name
        if not path.exists() or path.stat().st_size <= 0:
            download_file(asset.browser_download_url, path, timeout_seconds=240)
        raw = read_quarantined_csv(path)
        controls = project_player_game_batting(
            raw,
            source_asset=asset.name,
            season=season,
            game_type=GAME_TYPE,
        ).filter(pl.col("game_id").is_in(sample_games))
        outcomes = project_milb_player_game_outcomes(
            raw,
            source_asset=asset.name,
            season=season,
            game_type=GAME_TYPE,
        ).filter(pl.col("game_id").is_in(sample_games))
        if not controls.is_empty():
            control_frames.append(controls)
        if not outcomes.is_empty():
            outcome_frames.append(outcomes)
        del raw

    if not control_frames or not outcome_frames:
        raise RuntimeError(f"{season} {level} sample has no player-game observations")

    control_observations = pl.concat(control_frames, how="vertical_relaxed")
    outcome_observations = pl.concat(outcome_frames, how="vertical_relaxed")
    controls, control_metrics = resolve_player_game_contact_controls(control_observations)
    outcomes, outcome_metrics = resolve_milb_player_game_outcomes(outcome_observations)

    if control_metrics["unresolved_contact_control_count"]:
        raise RuntimeError(
            f"{season} {level} sample has unresolved player-game contact controls: "
            f"{control_metrics['unresolved_contact_control_count']}"
        )
    if outcome_metrics["unresolved_player_game_count"]:
        raise RuntimeError(
            f"{season} {level} sample has unresolved player-game outcomes: "
            f"{outcome_metrics['unresolved_player_game_count']}"
        )

    positive_pa = outcomes.filter(pl.col("batting_PA").is_not_null() & (pl.col("batting_PA") > 0))
    outcome_coverage = validate_expected_actual_leagues(
        positive_pa,
        league_column="league_id",
        expected_league_ids=league_ids,
        label=f"{season} {level} sampled player-game outcomes",
    )
    observed_games = {
        int(value) for value in positive_pa.get_column("game_id").drop_nulls().unique().to_list()
    }
    missing_games = sorted(set(sample_games) - observed_games)
    if missing_games:
        raise RuntimeError(
            f"{season} {level} sample contact games lack positive-PA player-game evidence: {missing_games}"
        )

    return controls, outcomes, {
        "player_game_asset_count": len(inventory),
        "player_game_assets": [asset.name for asset in inventory],
        "contact_controls": control_metrics,
        "outcomes": outcome_metrics,
        "outcome_league_coverage": outcome_coverage,
        "sample_games_with_positive_pa": len(observed_games),
    }


def _authorize_participants(
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
        contacts,
        controls,
        authority,
    )
    nonzero_residuals = residuals.filter(pl.col("contact_count_difference") != 0)
    return authorized, {
        **metrics,
        "exception_game_count": len(exception_games),
        "exception_game_ids": exception_games,
        "nonzero_player_game_residual_count": nonzero_residuals.height,
        "absolute_player_game_residual_mass": int(
            nonzero_residuals.select(pl.col("contact_count_difference").abs().sum()).item() or 0
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

    github_session = _github_session()
    try:
        contacts, contact_metrics = _load_contact_sample(
            season=args.season,
            level=args.level,
            league_ids=spec.league_ids,
            work_dir=work_dir,
            github_session=github_session,
            games_per_league=args.games_per_league,
        )
        sample_games = sorted(
            int(value) for value in contacts.get_column("game_pk").unique().to_list()
        )
        controls, outcomes, player_game_metrics = _load_player_game_sample(
            season=args.season,
            level=args.level,
            sample_games=sample_games,
            league_ids=spec.league_ids,
            work_dir=work_dir,
            github_session=github_session,
        )
    finally:
        github_session.close()

    authorized, authority_metrics = _authorize_participants(contacts, controls)
    classified = classify_milb_current_talent_contacts(authorized)
    if set(classified.get_column("season").unique().to_list()) != {int(args.season)}:
        raise RuntimeError("historical contact classification contains wrong season")

    summary, profile, evidence_metrics = build_milb_current_talent_player_game_evidence(
        outcomes,
        classified,
    )
    summary = summary.filter(pl.col("game_pk").is_in(sample_games))
    profile = profile.filter(pl.col("game_pk").is_in(sample_games))

    summary_artifact = write_canonical_parquet(
        summary,
        table_dir / f"current_talent_game_summary_{args.season}_{args.level}_poc.parquet",
        table_name=f"current_talent_game_summary_{args.season}_{args.level}_poc",
    ).as_record()
    profile_artifact = write_canonical_parquet(
        profile,
        table_dir / f"current_talent_game_profile_{args.season}_{args.level}_poc.parquet",
        table_name=f"current_talent_game_profile_{args.season}_{args.level}_poc",
    ).as_record()

    summary_games = int(summary.get_column("game_pk").n_unique())
    accepted = bool(
        summary_games == len(sample_games)
        and evidence_metrics["profile_matches_summary_core_counts"]
        and evidence_metrics["profile_has_no_orphans"]
    )
    report = {
        "report_schema_version": 1,
        "season": int(args.season),
        "filename_level": args.level,
        "level_group": spec.level_group,
        "actual_league_ids": sorted(spec.league_ids),
        "scope": {
            "pbp_assets_per_level": PBP_ASSETS_PER_LEVEL,
            "games_per_actual_league": int(args.games_per_league),
            "sample_game_count": len(sample_games),
        },
        "contacts": contact_metrics,
        "player_game": player_game_metrics,
        "participant_authority": authority_metrics,
        "evidence": evidence_metrics,
        "output": {
            "player_game_summary_rows": summary.height,
            "player_game_profile_rows": profile.height,
            "game_count": summary_games,
            "plate_appearances": int(summary.get_column("batting_plate_appearances").sum() or 0),
            "core_profile_events": int(summary.get_column("core_profile_event_count").sum() or 0),
            "observed_contacts": int(summary.get_column("observed_contact_count").sum() or 0),
            "contact_residual": int(summary.get_column("contact_count_residual").sum() or 0),
        },
        "storage": {"summary": summary_artifact, "profile": profile_artifact},
        "accepted": accepted,
        "interpretation": (
            "Scoped historical observed game evidence only. No Current Talent estimate, "
            "environment translation, run-value fitting, projection, playing time, WAR, or ranking."
        ),
    }
    (report_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    lines = [
        f"# Historical Current Talent MiLB game-evidence POC — {args.season} {spec.display_name}",
        "",
        f"- Actual leagues: {sorted(spec.league_ids)}",
        f"- Sample games: {len(sample_games):,}",
        f"- Player-games: {summary.height:,}",
        f"- PA: {report['output']['plate_appearances']:,}",
        f"- Observed contacts: {report['output']['observed_contacts']:,}",
        f"- Contact residual: {report['output']['contact_residual']:+,}",
        f"- Official participant exception games: {authority_metrics['exception_game_count']:,}",
        f"- Official batter changes: {authority_metrics['changed_batter_count']:,}",
        f"- Accepted: {accepted}",
    ]
    text = "\n".join(lines)
    (report_dir / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
