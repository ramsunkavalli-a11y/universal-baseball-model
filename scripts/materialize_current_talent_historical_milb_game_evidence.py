#!/usr/bin/env python
"""Materialize historical MiLB Current Talent game evidence for one level/season.

This is the reusable post-reorganization historical path. It keeps outcome and
contact evidence separate until both have passed their own source controls:

- player-game batting supplies chronological outcome vectors and contact controls;
- certified exception-only participant corrections are applied after player-game
  snapshot resolution and before outcome/contact reconciliation;
- season-player batting independently triggers sparse outcome review;
- current official gameLog adjudicates only residual player × league outcome rows;
- reusable PBP supplies physical contact geometry/profile evidence;
- missing historical PBP league identity is enriched only from a unique same-game
  player-game league map (ADR 026);
- current official allPlays supplies participant identity only for contact-residual
  games at play-sequence grain;
- the shared Current Talent game-evidence contract combines the adjudicated
  outcome vectors and classified contacts.

No environment translation, talent shrinkage, age adjustment, projection,
playing-time model, WAR, or ranking is fitted here. Official corrections create
retrospective corrected-event history, not vintage information-set history.
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
from universal_baseball.current_talent_identity_corrections import (
    apply_historical_player_game_identity_corrections,
)
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
from universal_baseball.current_talent_official_outcomes import (
    apply_official_game_log_outcome_authority,
    official_game_log_endpoint,
    project_official_hitting_game_log,
)
from universal_baseball.current_talent_season_reconciliation import (
    reconcile_resolved_outcomes_to_season_aggregates,
)
from universal_baseball.official import fetch_official_game_evidence
from universal_baseball.official_capture import capture_official_json, new_official_session
from universal_baseball.player_game_controls import resolve_player_game_contact_controls
from universal_baseball.player_game_stats import (
    fetch_player_game_asset_inventory,
    project_player_game_batting,
)
from universal_baseball.season_stat_assets import (
    fetch_season_stat_asset_inventory,
    select_season_stat_asset,
)
from universal_baseball.season_stats import standardize_armstjc_season_stats
from universal_baseball.storage import write_canonical_parquet


GAME_TYPE = "R"
LEVELS = ("aaa", "aa", "a+", "a", "rk")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--level", choices=LEVELS, required=True)
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("data/quarantine/current-talent-historical-milb-game-evidence"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/current-talent-historical-milb-game-evidence"),
    )
    return parser.parse_args()


def _github_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-historical-game-evidence/0.1"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def _key_set(frame: pl.DataFrame) -> set[tuple[int, int]]:
    if frame.is_empty():
        return set()
    return {
        (int(row["league_id"]), int(row["player_id"]))
        for row in frame.select("league_id", "player_id").unique().to_dicts()
    }


def _load_player_game_sources(
    *,
    season: int,
    level: str,
    league_ids: frozenset[int],
    work_dir: Path,
    session: requests.Session,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    assets = [
        asset
        for asset in fetch_player_game_asset_inventory(session=session)
        if asset.year == season and asset.filename_level == level
    ]
    if not assets:
        raise RuntimeError(f"no reusable {season} {level} player-game assets found")

    raw_dir = work_dir / "player-game"
    raw_dir.mkdir(parents=True, exist_ok=True)
    map_frames: list[pl.DataFrame] = []
    control_frames: list[pl.DataFrame] = []
    outcome_frames: list[pl.DataFrame] = []
    for asset in assets:
        path = raw_dir / asset.name
        if not path.exists() or path.stat().st_size <= 0:
            download_file(asset.browser_download_url, path, timeout_seconds=240)
        raw = read_quarantined_csv(path)
        required_map = {"game_id", "league_id", "game_type"}
        missing = sorted(required_map - set(raw.columns))
        if missing:
            raise RuntimeError(f"{asset.name} missing game-league-map fields: {missing}")
        map_frames.append(raw.select("game_id", "league_id", "game_type"))
        control_frames.append(
            project_player_game_batting(
                raw,
                source_asset=asset.name,
                season=season,
                game_type=GAME_TYPE,
            )
        )
        outcome_frames.append(
            project_milb_player_game_outcomes(
                raw,
                source_asset=asset.name,
                season=season,
                game_type=GAME_TYPE,
            )
        )

    game_league_map, league_map_metrics = derive_player_game_league_map(
        pl.concat(map_frames, how="vertical_relaxed"),
        game_type=GAME_TYPE,
    )
    controls, control_metrics = resolve_player_game_contact_controls(
        pl.concat(control_frames, how="vertical_relaxed")
    )
    if control_metrics["unresolved_contact_control_count"]:
        raise RuntimeError(
            f"{season} {level} has unresolved player-game contact controls: "
            f"{control_metrics['unresolved_contact_control_count']}"
        )

    outcomes, outcome_metrics = resolve_milb_player_game_outcomes(
        pl.concat(outcome_frames, how="vertical_relaxed")
    )
    if outcome_metrics["unresolved_player_game_count"]:
        raise RuntimeError(
            f"{season} {level} has unresolved player-game outcomes: "
            f"{outcome_metrics['unresolved_player_game_count']}"
        )

    outcomes, controls, identity_evidence, identity_metrics = (
        apply_historical_player_game_identity_corrections(
            outcomes,
            controls,
            season=season,
        )
    )

    expected_controls = controls.filter(pl.col("expected_contact_count").is_not_null())
    control_coverage = validate_expected_actual_leagues(
        expected_controls,
        league_column="league_id",
        expected_league_ids=league_ids,
        label=f"{season} {level} player-game contact controls",
    )
    positive_pa = outcomes.filter(
        (pl.col("game_type") == GAME_TYPE)
        & pl.col("batting_PA").is_not_null()
        & (pl.col("batting_PA") > 0)
    )
    outcome_coverage = validate_expected_actual_leagues(
        positive_pa,
        league_column="league_id",
        expected_league_ids=league_ids,
        label=f"{season} {level} player-game outcomes",
    )
    return game_league_map, controls, outcomes, {
        "asset_count": len(assets),
        "asset_names": [asset.name for asset in assets],
        "game_league_map": league_map_metrics,
        "contact_controls": {**control_metrics, "league_coverage": control_coverage},
        "outcomes": {**outcome_metrics, "league_coverage": outcome_coverage},
        "identity_corrections": {
            **identity_metrics,
            "evidence": identity_evidence.to_dicts(),
        },
    }


def _load_season_batting(
    *,
    season: int,
    level: str,
    work_dir: Path,
    session: requests.Session,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    inventory = fetch_season_stat_asset_inventory("batting", session=session)
    asset = select_season_stat_asset(
        inventory,
        year=season,
        filename_level=level,
        kind="batting",
        require_nonempty=True,
    )
    season_dir = work_dir / "season"
    season_dir.mkdir(parents=True, exist_ok=True)
    path = season_dir / asset.name
    if not path.exists() or path.stat().st_size <= 0:
        download_file(asset.browser_download_url, path, timeout_seconds=240)
    raw = read_quarantined_csv(path)
    standardized, schema_metrics = standardize_armstjc_season_stats(raw, "batting")
    return standardized, {
        "asset": asset.as_record(),
        "schema": schema_metrics,
    }


def _adjudicate_outcomes(
    *,
    outcomes: pl.DataFrame,
    season_stats: pl.DataFrame,
    season: int,
    level: str,
    league_ids: frozenset[int],
    sport_id: int,
    raw_official_dir: Path,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    pre_comparison, pre_metrics = reconcile_resolved_outcomes_to_season_aggregates(
        outcomes,
        season_stats,
        season=season,
        expected_league_ids=league_ids,
        require_exact=False,
    )
    pre_mismatch = pre_comparison.filter(pl.col("has_any_mismatch"))
    pre_keys = _key_set(pre_mismatch)
    corrected = outcomes.with_columns(pl.lit("player_game_source").alias("outcome_authority"))

    evidence_frames: list[pl.DataFrame] = []
    adjudications: list[dict[str, Any]] = []
    snapshots: list[dict[str, Any]] = []
    raw_official_dir.mkdir(parents=True, exist_ok=True)
    official_session = new_official_session()
    try:
        for league_id, player_id in sorted(pre_keys):
            endpoint = official_game_log_endpoint(
                player_id=player_id,
                sport_id=sport_id,
                season=season,
            )
            capture = capture_official_json(endpoint, session=official_session)
            raw_path = raw_official_dir / f"player_{player_id}_sport_{sport_id}_gamelog.json"
            capture.write_raw(raw_path)
            if not isinstance(capture.data, dict):
                raise RuntimeError(f"official gameLog for player {player_id} is not an object")
            official = project_official_hitting_game_log(
                capture.data,
                player_id=player_id,
                sport_id=sport_id,
            )
            corrected, evidence, metrics = apply_official_game_log_outcome_authority(
                corrected,
                official,
                player_id=player_id,
                league_id=league_id,
            )
            if not evidence.is_empty():
                evidence_frames.append(evidence)
            adjudications.append(metrics)
            snapshots.append(
                {
                    "league_id": league_id,
                    "player_id": player_id,
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
        season=season,
        expected_league_ids=league_ids,
        require_exact=False,
    )
    post_mismatch = post_comparison.filter(pl.col("has_any_mismatch"))
    post_keys = _key_set(post_mismatch)
    if not post_keys.issubset(pre_keys):
        raise RuntimeError(
            f"{season} {level} official outcome adjudication introduced new season residuals: "
            f"{sorted(post_keys - pre_keys)}"
        )
    if len(adjudications) != len(pre_keys):
        raise RuntimeError(
            f"{season} {level} did not adjudicate every pre-existing outcome residual"
        )

    if evidence_frames:
        evidence = pl.concat(evidence_frames, how="vertical_relaxed").sort(
            ["league_id", "player_id", "game_id", "field"]
        )
    else:
        evidence = pl.DataFrame(
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

    classifications: dict[str, int] = {}
    for row in adjudications:
        key = str(row["classification"])
        classifications[key] = classifications.get(key, 0) + 1
    return corrected, evidence, {
        "pre_reconciliation": pre_metrics,
        "pre_residual_player_league_count": len(pre_keys),
        "pre_residual_keys": [list(key) for key in sorted(pre_keys)],
        "official_adjudication_count": len(adjudications),
        "classification_counts": classifications,
        "adjudications": adjudications,
        "official_snapshots": snapshots,
        "changed_field_evidence_count": int(evidence.height),
        "post_reconciliation": post_metrics,
        "remaining_season_asset_residual_count": len(post_keys),
        "remaining_season_asset_residual_keys": [list(key) for key in sorted(post_keys)],
        "accepted": True,
        "temporal_semantics": (
            "retrospective_event_cutoff_corrected_history_not_vintage_information_set"
        ),
    }


def _load_contacts(
    *,
    season: int,
    level: str,
    league_ids: frozenset[int],
    game_league_map: pl.DataFrame,
    work_dir: Path,
    session: requests.Session,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    assets = [
        asset
        for asset in fetch_pbp_asset_inventory(session=session)
        if asset.year == season and asset.filename_level == level
    ]
    if not assets:
        raise RuntimeError(f"no reusable {season} {level} PBP assets found")

    raw_dir = work_dir / "pbp"
    raw_dir.mkdir(parents=True, exist_ok=True)
    projected_frames: list[pl.DataFrame] = []
    enrichment_metrics: list[dict[str, Any]] = []
    for asset in assets:
        path = raw_dir / asset.name
        if not path.exists() or path.stat().st_size <= 0:
            download_file(asset.browser_download_url, path, timeout_seconds=300)
        raw = read_quarantined_csv(path)
        enriched, enrichment = enrich_historical_pbp_league_id(
            raw,
            game_league_map,
            source_asset=asset.name,
            game_type=GAME_TYPE,
        )
        enrichment_metrics.append(enrichment)
        projected_frames.append(
            project_armstjc_contact_observations(
                enriched,
                source_asset=asset.name,
                season=season,
                game_type=GAME_TYPE,
            )
        )

    observations = pl.concat(projected_frames, how="vertical_relaxed")
    resolved = resolve_armstjc_contact_observations(observations, contacts_only=False)
    resolution = contact_resolution_metrics(observations, resolved)
    if resolution["contact_status_conflict_key_count"]:
        raise RuntimeError(
            f"{season} {level} has unresolved cross-snapshot contact-status conflicts"
        )
    contacts = resolved.filter(pl.col("source_is_in_play") == True)  # noqa: E712
    if contacts.filter(pl.col("source_batter_id").is_null()).height:
        raise RuntimeError(f"{season} {level} contacts contain unresolved source batter")
    coverage = validate_expected_actual_leagues(
        contacts,
        league_column="league_id",
        expected_league_ids=league_ids,
        label=f"{season} {level} contacts",
    )
    return contacts, {
        "asset_count": len(assets),
        "asset_names": [asset.name for asset in assets],
        "league_id_enrichment": enrichment_metrics,
        "resolution": resolution,
        "league_coverage": coverage,
    }


def _apply_participant_authority(
    contacts: pl.DataFrame,
    controls: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    residuals = contact_identity_residuals(contacts, controls)
    exception_games = exception_games_from_residuals(residuals)
    if exception_games:
        official_pa, _ = fetch_official_game_evidence(exception_games)
        official_sequences = project_official_sequence_authority(official_pa)
    else:
        official_sequences = pl.DataFrame(schema=OFFICIAL_SEQUENCE_AUTHORITY_SCHEMA)
    authorized, metrics = apply_contact_identity_authority_by_sequence(
        contacts,
        controls,
        official_sequences,
    )
    return authorized, {
        **metrics,
        "participant_source": "current_official_matchup_batter_for_residual_games_only",
        "physical_contact_source": "reusable_historical_pbp_preserved",
    }


def main() -> int:
    args = parse_args()
    spec = current_talent_level_spec(args.season, args.level)
    slug = args.level.replace("+", "plus")
    work_dir = args.work_root / str(args.season) / slug
    report_dir = args.report_root / str(args.season) / slug
    table_dir = report_dir / "tables"
    raw_official_dir = report_dir / "official-outcome-raw"
    for path in (work_dir, report_dir, table_dir, raw_official_dir):
        path.mkdir(parents=True, exist_ok=True)

    github_session = _github_session()
    try:
        game_league_map, controls, source_outcomes, player_game_metrics = (
            _load_player_game_sources(
                season=args.season,
                level=args.level,
                league_ids=spec.league_ids,
                work_dir=work_dir,
                session=github_session,
            )
        )
        season_stats, season_metrics = _load_season_batting(
            season=args.season,
            level=args.level,
            work_dir=work_dir,
            session=github_session,
        )
        contacts, contact_metrics = _load_contacts(
            season=args.season,
            level=args.level,
            league_ids=spec.league_ids,
            game_league_map=game_league_map,
            work_dir=work_dir,
            session=github_session,
        )
    finally:
        github_session.close()

    corrected_outcomes, outcome_adjudication, outcome_metrics = _adjudicate_outcomes(
        outcomes=source_outcomes,
        season_stats=season_stats,
        season=args.season,
        level=args.level,
        league_ids=spec.league_ids,
        sport_id=spec.official_sport_id,
        raw_official_dir=raw_official_dir,
    )
    authorized_contacts, participant_metrics = _apply_participant_authority(
        contacts,
        controls,
    )
    classified_contacts = classify_milb_current_talent_contacts(authorized_contacts)

    if set(int(v) for v in classified_contacts.get_column("season").unique().to_list()) != {
        int(args.season)
    }:
        raise RuntimeError(f"{args.season} {args.level} classified contacts span wrong seasons")
    classified_coverage = validate_expected_actual_leagues(
        classified_contacts,
        league_column="league_id",
        expected_league_ids=spec.league_ids,
        label=f"{args.season} {args.level} classified contacts",
    )

    summary, profile, evidence_metrics = build_milb_current_talent_player_game_evidence(
        corrected_outcomes,
        classified_contacts,
    )
    if evidence_metrics["season_count"] != 1:
        raise RuntimeError("historical Current Talent output unexpectedly spans multiple seasons")
    if evidence_metrics["actual_league_count"] != len(spec.league_ids):
        raise RuntimeError("historical Current Talent output lost actual-league coverage")

    outcome_storage = write_canonical_parquet(
        corrected_outcomes,
        table_dir / f"current_talent_outcomes_{args.season}_{slug}_adjudicated.parquet",
        table_name=f"current_talent_outcomes_{args.season}_{slug}_adjudicated",
    ).as_record()
    summary_storage = write_canonical_parquet(
        summary,
        table_dir / f"current_talent_game_summary_{args.season}_{slug}.parquet",
        table_name=f"current_talent_game_summary_{args.season}_{slug}",
    ).as_record()
    profile_storage = write_canonical_parquet(
        profile,
        table_dir / f"current_talent_game_profile_{args.season}_{slug}.parquet",
        table_name=f"current_talent_game_profile_{args.season}_{slug}",
    ).as_record()
    if not outcome_adjudication.is_empty():
        outcome_adjudication.write_csv(report_dir / "official_outcome_adjudication.csv")

    total_pa = int(summary.get_column("batting_plate_appearances").sum() or 0)
    total_contacts = int(summary.get_column("observed_contact_count").sum() or 0)
    total_expected_contacts = int(summary.get_column("expected_contact_count").sum() or 0)
    total_core = int(summary.get_column("core_profile_event_count").sum() or 0)
    total_unknown = int(summary.get_column("unknown_contact_count").sum() or 0)
    total_pa_residual = int(summary.get_column("pa_accounting_residual").sum() or 0)
    contact_residual = int(summary.get_column("contact_count_residual").sum() or 0)

    report = {
        "report_schema_version": 1,
        "season": int(args.season),
        "filename_level": args.level,
        "level_group": spec.level_group,
        "display_name": spec.display_name,
        "official_sport_id": int(spec.official_sport_id),
        "actual_league_ids": sorted(spec.league_ids),
        "player_game_source": player_game_metrics,
        "season_aggregate_source": season_metrics,
        "outcome_adjudication": outcome_metrics,
        "contact_source": contact_metrics,
        "participant_authority": participant_metrics,
        "classified_contact_league_coverage": classified_coverage,
        "evidence_contract": evidence_metrics,
        "output": {
            "player_game_summary_rows": int(summary.height),
            "player_game_profile_rows": int(profile.height),
            "game_count": int(summary.get_column("game_pk").n_unique()),
            "player_count": int(summary.get_column("player_id").n_unique()),
            "plate_appearances": total_pa,
            "expected_contacts": total_expected_contacts,
            "observed_contacts": total_contacts,
            "contact_count_residual": contact_residual,
            "core_profile_events": total_core,
            "core_profile_coverage_rate": total_core / total_pa if total_pa else None,
            "unknown_contacts": total_unknown,
            "pa_accounting_residual": total_pa_residual,
        },
        "storage": {
            "adjudicated_outcomes": outcome_storage,
            "summary": summary_storage,
            "profile": profile_storage,
        },
        "accepted": True,
        "temporal_semantics": (
            "retrospective_event_cutoff_corrected_history_not_vintage_information_set"
        ),
        "interpretation": (
            "Game-grain observed outcome/contact evidence for Current Talent validation only; "
            "no talent estimate or environment translation is produced."
        ),
    }
    (report_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    text = "\n".join(
        [
            f"# Historical Current Talent game evidence — {args.season} {spec.display_name}",
            "",
            f"- Player-games: {summary.height:,}",
            f"- Games: {report['output']['game_count']:,}",
            f"- PA: {total_pa:,}",
            f"- Expected contacts: {total_expected_contacts:,}",
            f"- Observed contacts: {total_contacts:,}",
            f"- Contact residual: {contact_residual:+,}",
            f"- Core profile events: {total_core:,}",
            f"- Unknown contacts: {total_unknown:,}",
            f"- PA accounting residual: {total_pa_residual:+,}",
            f"- Outcome residual players reviewed officially: "
            f"{outcome_metrics['official_adjudication_count']:,}",
            f"- Participant exception games: {participant_metrics['exception_game_count']:,}",
            f"- Official batter attribution changes: "
            f"{participant_metrics['changed_batter_contact_count']:,}",
            "- Accepted: True",
        ]
    )
    (report_dir / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())