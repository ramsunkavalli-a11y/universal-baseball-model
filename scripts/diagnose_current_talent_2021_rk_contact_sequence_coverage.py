#!/usr/bin/env python
"""Diagnose 2021 Rookie contact participant-authority sequence coverage.

This diagnostic reproduces only the player-game contact controls and reusable
physical-contact path needed by Current Talent participant authority. It applies
certified player-game identity corrections, identifies residual-triggered games,
fetches current official allPlays evidence for those games, and writes the exact
source ``game_pk + at_bat_index`` sequences that official authority does or does
not cover.

No outcome season reconciliation, participant overlay, or source mutation occurs.
"""

from __future__ import annotations

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
    SEQUENCE_KEY,
    contact_identity_residuals,
    exception_games_from_residuals,
    project_official_sequence_authority,
)
from universal_baseball.current_talent_era import current_talent_level_spec
from universal_baseball.current_talent_identity_corrections import (
    apply_historical_player_game_identity_corrections,
)
from universal_baseball.current_talent_milb_evidence import (
    project_milb_player_game_outcomes,
    resolve_milb_player_game_outcomes,
)
from universal_baseball.current_talent_milb_source import (
    derive_player_game_league_map,
    enrich_historical_pbp_league_id,
)
from universal_baseball.official import fetch_official_game_evidence
from universal_baseball.player_game_controls import resolve_player_game_contact_controls
from universal_baseball.player_game_stats import (
    fetch_player_game_asset_inventory,
    project_player_game_batting,
)


SEASON = 2021
LEVEL = "rk"
GAME_TYPE = "R"


def _github_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-2021-rk-contact-sequence/0.1"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def _load_player_game(
    *,
    work_dir: Path,
    session: requests.Session,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    assets = [
        asset
        for asset in fetch_player_game_asset_inventory(session=session)
        if asset.year == SEASON and asset.filename_level == LEVEL
    ]
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
        map_frames.append(raw.select("game_id", "league_id", "game_type"))
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

    game_league_map, league_map_metrics = derive_player_game_league_map(
        pl.concat(map_frames, how="vertical_relaxed"),
        game_type=GAME_TYPE,
    )
    controls, control_metrics = resolve_player_game_contact_controls(
        pl.concat(control_frames, how="vertical_relaxed")
    )
    outcomes, outcome_metrics = resolve_milb_player_game_outcomes(
        pl.concat(outcome_frames, how="vertical_relaxed")
    )
    outcomes, controls, correction_evidence, correction_metrics = (
        apply_historical_player_game_identity_corrections(
            outcomes,
            controls,
            season=SEASON,
        )
    )
    return game_league_map, controls, outcomes, {
        "asset_names": [asset.name for asset in assets],
        "league_map": league_map_metrics,
        "control_resolution": control_metrics,
        "outcome_resolution": outcome_metrics,
        "identity_corrections": {
            **correction_metrics,
            "evidence": correction_evidence.to_dicts(),
        },
    }


def _load_contacts(
    *,
    game_league_map: pl.DataFrame,
    work_dir: Path,
    session: requests.Session,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    assets = [
        asset
        for asset in fetch_pbp_asset_inventory(session=session)
        if asset.year == SEASON and asset.filename_level == LEVEL
    ]
    raw_dir = work_dir / "pbp"
    raw_dir.mkdir(parents=True, exist_ok=True)
    projected_frames: list[pl.DataFrame] = []
    enrichments: list[dict[str, Any]] = []
    for asset in assets:
        path = raw_dir / asset.name
        if not path.exists() or path.stat().st_size <= 0:
            download_file(asset.browser_download_url, path, timeout_seconds=300)
        raw = read_quarantined_csv(path)
        enriched, metrics = enrich_historical_pbp_league_id(
            raw,
            game_league_map,
            source_asset=asset.name,
            game_type=GAME_TYPE,
        )
        enrichments.append(metrics)
        projected_frames.append(
            project_armstjc_contact_observations(
                enriched,
                source_asset=asset.name,
                season=SEASON,
                game_type=GAME_TYPE,
            )
        )
    observations = pl.concat(projected_frames, how="vertical_relaxed")
    resolved = resolve_armstjc_contact_observations(observations, contacts_only=False)
    contacts = resolved.filter(pl.col("source_is_in_play") == True)  # noqa: E712
    return contacts, {
        "asset_names": [asset.name for asset in assets],
        "enrichment": enrichments,
        "resolution": contact_resolution_metrics(observations, resolved),
    }


def main() -> int:
    spec = current_talent_level_spec(SEASON, LEVEL)
    work_dir = Path("data/quarantine/current-talent-2021-rk-contact-sequence-diagnostic")
    report_dir = Path("reports/generated/current-talent-2021-rk-contact-sequence-diagnostic")
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    session = _github_session()
    try:
        game_league_map, controls, outcomes, player_game_metrics = _load_player_game(
            work_dir=work_dir,
            session=session,
        )
        contacts, contact_metrics = _load_contacts(
            game_league_map=game_league_map,
            work_dir=work_dir,
            session=session,
        )
    finally:
        session.close()

    residuals = contact_identity_residuals(contacts, controls)
    residual_rows = residuals.filter(pl.col("contact_count_difference") != 0)
    exception_games = exception_games_from_residuals(residuals)
    residual_rows.write_csv(report_dir / "contact_identity_residuals.csv")

    official_pa, _ = fetch_official_game_evidence(exception_games)
    official_sequences = project_official_sequence_authority(official_pa)
    official_sequences.write_csv(report_dir / "official_sequence_authority.csv")

    source_sequences = (
        contacts.filter(pl.col("game_pk").is_in(exception_games))
        .select(list(SEQUENCE_KEY))
        .unique()
        .sort(list(SEQUENCE_KEY))
    )
    official_keys = official_sequences.select(list(SEQUENCE_KEY)).unique().sort(list(SEQUENCE_KEY))
    source_only = source_sequences.join(official_keys, on=list(SEQUENCE_KEY), how="anti")
    official_only = official_keys.join(source_sequences, on=list(SEQUENCE_KEY), how="anti")
    covered = source_sequences.join(official_keys, on=list(SEQUENCE_KEY), how="inner")
    source_only.write_csv(report_dir / "source_sequences_missing_official_authority.csv")
    official_only.write_csv(report_dir / "official_sequences_without_source_contact.csv")

    source_contact_detail = contacts.join(
        source_only,
        on=list(SEQUENCE_KEY),
        how="inner",
    ).sort(["game_pk", "at_bat_index", "pitch_number"])
    source_contact_detail.write_csv(report_dir / "missing_sequence_source_contacts.csv")

    by_game = (
        source_sequences.group_by("game_pk")
        .agg(pl.len().alias("source_sequence_count"))
        .join(
            covered.group_by("game_pk").agg(pl.len().alias("covered_sequence_count")),
            on="game_pk",
            how="left",
        )
        .join(
            source_only.group_by("game_pk").agg(pl.len().alias("missing_sequence_count")),
            on="game_pk",
            how="left",
        )
        .with_columns(
            pl.col("covered_sequence_count").fill_null(0),
            pl.col("missing_sequence_count").fill_null(0),
        )
        .sort("game_pk")
    )
    by_game.write_csv(report_dir / "sequence_coverage_by_game.csv")

    missing_indices = source_only.select(
        pl.col("game_pk"),
        pl.col("at_bat_index"),
    )
    report = {
        "report_schema_version": 1,
        "season": SEASON,
        "level": LEVEL,
        "official_sport_id": int(spec.official_sport_id),
        "exception_game_count": len(exception_games),
        "exception_game_ids": exception_games,
        "residual_player_game_row_count": int(residual_rows.height),
        "source_exception_sequence_count": int(source_sequences.height),
        "covered_source_exception_sequence_count": int(covered.height),
        "missing_source_exception_sequence_count": int(source_only.height),
        "official_only_sequence_count": int(official_only.height),
        "missing_sequences": missing_indices.to_dicts(),
        "coverage_by_game": by_game.to_dicts(),
        "player_game_source": player_game_metrics,
        "contact_source": contact_metrics,
        "outcome_rows_loaded_for_identity_guard": int(outcomes.height),
        "accepted": False,
        "interpretation": (
            "Diagnostic only. Missing official sequence keys must be explained before participant "
            "authority can be relaxed or changed. Reusable physical contacts remain unmodified."
        ),
    }
    (report_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    text = "\n".join(
        [
            "# 2021 Rookie contact sequence coverage diagnostic",
            "",
            f"- Exception games: {len(exception_games)}",
            f"- Residual player-game rows: {residual_rows.height}",
            f"- Source exception sequences: {source_sequences.height}",
            f"- Covered sequences: {covered.height}",
            f"- Missing source sequences: {source_only.height}",
            f"- Official-only sequences: {official_only.height}",
            f"- Missing keys: {missing_indices.to_dicts()}",
        ]
    )
    (report_dir / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
