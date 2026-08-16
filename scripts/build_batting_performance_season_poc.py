#!/usr/bin/env python
"""First end-to-end production batting Performance player-season POC.

Scope is deliberately one completed environment family: 2024 AAA. The script
uses production transformation modules for the source-heavy player-season path
and reuses the already-certified 45-game official calibration sampler only to
produce league-season contextual RE24 evidence.

Pipeline:

1. all 2024 AAA reusable PBP snapshots -> deterministic physical contact consensus;
2. all 2024 AAA reusable player-game snapshots -> broad contact controls;
3. player-game residuals -> targeted official participant overlay only;
4. reusable contact geometry/narrative -> final screened contact bins;
5. completed 2024 AAA season batting aggregates -> PA / BB-HBP / K backbone;
6. pre-certified 45-game PCL/IL official sample -> direct bin RE24 means;
7. frozen AAA lambda=25 peer policy -> league-season bin values;
8. production player-season batting Performance summary and long-form profile;
9. Parquet + DuckDB round-trip / uniqueness validation.

No Current Talent, projection, playing-time, defense, WAR, or overall ranking is
computed here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb
import polars as pl

import audit_screened_bin_value_confirmation as screened
from universal_baseball.armstjc_assets import fetch_pbp_asset_inventory
from universal_baseball.armstjc_contacts import (
    contact_resolution_metrics,
    project_armstjc_contact_observations,
    resolve_armstjc_contact_observations,
)
from universal_baseball.bin_value_calibration import (
    bin_calibration_coverage,
    summarize_direct_bin_values,
)
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.contact_identity_overlay import (
    apply_contact_identity_authority,
    contact_identity_residuals,
    exception_games_from_residuals,
    project_official_contact_authority,
)
from universal_baseball.contact_profile import classify_contact_profile_events
from universal_baseball.official import fetch_official_game_evidence
from universal_baseball.performance_season import (
    build_batting_performance_season,
    estimate_certified_bin_values,
)
from universal_baseball.player_game_stats import (
    fetch_player_game_asset_inventory,
    project_player_game_batting,
    resolve_player_game_batting,
)
from universal_baseball.run_expectancy import attach_re24, estimate_run_expectancy
from universal_baseball.season_stats import standardize_armstjc_season_stats
from universal_baseball.storage import write_canonical_parquet


SEASON = 2024
LEVEL = "aaa"
GAME_TYPE = "R"
AAA_LEAGUE_IDS = {112, 117}
CALIBRATION_ASSET = "2024_6_aaa_pbp.csv"
SEASON_BATTING_ASSET = "2024_aaa_season_batting_stats.csv"
SEASON_BATTING_URL = (
    "https://github.com/armstjc/milb-data-repository/releases/download/"
    f"season_player_batting/{SEASON_BATTING_ASSET}"
)
WORK_DIR = Path("data/quarantine/batting-performance-season-poc")
REPORT_DIR = Path("reports/generated/batting-performance-season-poc")
OUTPUT_DIR = REPORT_DIR / "tables"


def _load_reusable_contacts() -> tuple[pl.DataFrame, dict[str, Any]]:
    pbp_dir = WORK_DIR / "pbp"
    assets = [
        asset
        for asset in fetch_pbp_asset_inventory()
        if asset.year == SEASON and asset.filename_level == LEVEL
    ]
    if not assets:
        raise RuntimeError("no reusable 2024 AAA PBP assets found")

    frames: list[pl.DataFrame] = []
    for asset in assets:
        path = pbp_dir / asset.name
        if not path.exists() or path.stat().st_size <= 0:
            download_file(asset.browser_download_url, path, timeout_seconds=300)
        raw = read_quarantined_csv(path)
        frames.append(
            project_armstjc_contact_observations(
                raw,
                source_asset=asset.name,
                season=SEASON,
                game_type=GAME_TYPE,
            )
        )
        del raw

    observations = pl.concat(frames, how="vertical_relaxed")
    all_resolved = resolve_armstjc_contact_observations(
        observations,
        contacts_only=False,
    )
    metrics = contact_resolution_metrics(observations, all_resolved)
    contacts = all_resolved.filter(pl.col("source_is_in_play") == True)  # noqa: E712

    if metrics["contact_status_conflict_key_count"]:
        raise RuntimeError("contact-status conflicts block production POC")
    if contacts.filter(pl.col("source_batter_id").is_null()).height:
        raise RuntimeError("unresolved contact batter blocks participant-control stage")
    return contacts, {
        "asset_count": len(assets),
        "asset_names": [asset.name for asset in assets],
        **metrics,
    }


def _load_player_game_controls() -> tuple[pl.DataFrame, dict[str, Any]]:
    player_game_dir = WORK_DIR / "player-game"
    assets = [
        asset
        for asset in fetch_player_game_asset_inventory()
        if asset.year == SEASON and asset.filename_level == LEVEL
    ]
    if not assets:
        raise RuntimeError("no reusable 2024 AAA player-game assets found")

    frames: list[pl.DataFrame] = []
    for asset in assets:
        path = player_game_dir / asset.name
        if not path.exists() or path.stat().st_size <= 0:
            download_file(asset.browser_download_url, path, timeout_seconds=240)
        raw = read_quarantined_csv(path)
        frames.append(
            project_player_game_batting(
                raw,
                source_asset=asset.name,
                season=SEASON,
                game_type=GAME_TYPE,
            )
        )
        del raw
    observations = pl.concat(frames, how="vertical_relaxed")
    resolved, metrics = resolve_player_game_batting(observations)
    if metrics["unresolved_expected_contact_player_game_count"]:
        raise RuntimeError("unresolved player-game contact controls block production POC")
    return resolved, {
        "asset_count": len(assets),
        "asset_names": [asset.name for asset in assets],
        **metrics,
    }


def _apply_participant_authority(
    contacts: pl.DataFrame,
    player_games: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    residuals = contact_identity_residuals(contacts, player_games)
    exception_games = exception_games_from_residuals(residuals)
    if exception_games:
        pa, pitch = fetch_official_game_evidence(exception_games)
        official_contacts = project_official_contact_authority(pa, pitch)
    else:
        official_contacts = pl.DataFrame(
            schema={
                "game_pk": pl.Int64,
                "at_bat_index": pl.Int64,
                "pitch_number": pl.Int64,
                "official_batter_id": pl.Int64,
            }
        )
    resolved, metrics = apply_contact_identity_authority(
        contacts, player_games, official_contacts
    )
    return resolved, metrics


def _classify_contacts(authorized: pl.DataFrame) -> pl.DataFrame:
    input_frame = authorized.with_columns(
        pl.col("game_date").str.slice(0, 4).cast(pl.Int64, strict=False).alias("season"),
        pl.lit("source_certified_mirror").alias("result_description_authority"),
    ).select(
        "season",
        "league_id",
        "game_pk",
        "at_bat_index",
        "pitch_number",
        "batter_mlbam_id",
        "participant_authority",
        "result_description_authority",
        "batter_side",
        "bb_type",
        "hc_x",
        "hc_y",
        "result_description",
    )
    result = classify_contact_profile_events(input_frame)
    if result.height != authorized.height:
        raise RuntimeError(
            f"contact classification lost rows: {result.height:,} vs {authorized.height:,}"
        )
    return result


def _load_season_batting() -> tuple[pl.DataFrame, dict[str, Any]]:
    path = WORK_DIR / "season" / SEASON_BATTING_ASSET
    if not path.exists() or path.stat().st_size <= 0:
        download_file(SEASON_BATTING_URL, path, timeout_seconds=240)
    raw = read_quarantined_csv(path)
    standardized, metadata = standardize_armstjc_season_stats(raw, "batting")
    standardized = standardized.filter(
        (pl.col("season").cast(pl.Int64, strict=False) == SEASON)
        & pl.col("league_id").cast(pl.Int64, strict=False).is_in(sorted(AAA_LEAGUE_IDS))
    )
    if standardized.is_empty():
        raise RuntimeError("2024 AAA standardized season batting source is empty")
    return standardized, metadata


def _calibrate_bin_values() -> tuple[pl.DataFrame, dict[str, Any]]:
    calibration_dir = WORK_DIR / "calibration"
    frames, environment_meta = screened._load_environment_frames(
        assets=(CALIBRATION_ASSET,),
        work_dir=calibration_dir,
        allowed_leagues=set(AAA_LEAGUE_IDS),
    )
    calibration_events: list[pl.DataFrame] = []
    environment_diagnostics: list[dict[str, Any]] = []

    for environment_id in sorted(frames):
        items = frames[environment_id]
        performance = pl.concat([item[1] for item in items], how="vertical_relaxed")
        transitions = pl.concat([item[2] for item in items], how="vertical_relaxed")
        matrix = estimate_run_expectancy(transitions)
        valued = attach_re24(transitions, matrix)
        terminal = valued.filter(
            pl.col("is_plate_appearance_result") & pl.col("re24_available")
        ).select("game_pk", "at_bat_index", "re24")
        core = performance.filter(pl.col("fabio_core_bin").is_not_null()).select(
            pl.col("season").cast(pl.Int64),
            pl.col("league_id").cast(pl.Int64),
            "game_pk",
            "at_bat_index",
            pl.col("fabio_core_bin").alias("core_bin"),
        )
        joined = core.join(terminal, on=["game_pk", "at_bat_index"], how="left")
        coverage = bin_calibration_coverage(joined)
        missing_re24 = int(coverage.get_column("missing_re24_count").sum() or 0)
        if missing_re24:
            raise RuntimeError(
                f"screened bin calibration missing RE24 in {environment_id}: {missing_re24}"
            )
        calibration_events.append(joined)
        environment_diagnostics.append(
            {
                **environment_meta[environment_id],
                "screened_core_occurrence_count": joined.height,
                "observed_state_count": matrix.height,
                "minimum_state_sample_size": int(
                    matrix.get_column("state_sample_size").min() or 0
                ),
            }
        )

    events = pl.concat(calibration_events, how="vertical_relaxed")
    direct = summarize_direct_bin_values(events)
    estimated = estimate_certified_bin_values(direct)
    if estimated.filter(~pl.col("estimator_certified")).height:
        raise RuntimeError("2024 AAA calibration contains uncertified bin estimates")
    return estimated, {
        "asset": CALIBRATION_ASSET,
        "environment_count": len(environment_diagnostics),
        "environment_diagnostics": environment_diagnostics,
        "calibration_event_count": events.height,
        "direct_bin_row_count": direct.height,
        "estimated_bin_row_count": estimated.height,
    }


def _duckdb_validate(summary_path: Path, profile_path: Path) -> dict[str, int]:
    connection = duckdb.connect()
    try:
        summary_rows = int(
            connection.execute(
                "SELECT count(*) FROM read_parquet(?)", [str(summary_path)]
            ).fetchone()[0]
        )
        unique_summary_keys = int(
            connection.execute(
                "SELECT count(*) FROM (SELECT DISTINCT season, league_id, player_id "
                "FROM read_parquet(?))",
                [str(summary_path)],
            ).fetchone()[0]
        )
        profile_rows = int(
            connection.execute(
                "SELECT count(*) FROM read_parquet(?)", [str(profile_path)]
            ).fetchone()[0]
        )
    finally:
        connection.close()
    if summary_rows != unique_summary_keys:
        raise RuntimeError("player-season Performance output is not unique at canonical grain")
    return {
        "summary_rows": summary_rows,
        "unique_summary_keys": unique_summary_keys,
        "profile_rows": profile_rows,
    }


def main() -> int:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    contacts, contact_source_metrics = _load_reusable_contacts()
    player_games, player_game_metrics = _load_player_game_controls()
    authorized_contacts, authority_metrics = _apply_participant_authority(
        contacts, player_games
    )
    classified_contacts = _classify_contacts(authorized_contacts)
    season_batting, season_metadata = _load_season_batting()
    bin_values, calibration_metrics = _calibrate_bin_values()

    summary, profile = build_batting_performance_season(
        season_batting,
        classified_contacts,
        bin_values,
    )

    duplicate_summary = (
        summary.group_by(["season", "league_id", "player_id"])
        .len()
        .filter(pl.col("len") > 1)
    )
    if not duplicate_summary.is_empty():
        raise RuntimeError("duplicate player-league-season Performance rows")
    if summary.filter(pl.col("core_profile_count_exceeds_pa")).height:
        raise RuntimeError("core Performance event count exceeds PA for at least one player")
    if summary.filter(pl.col("unvalued_core_event_count") > 0).height:
        raise RuntimeError("core Performance events exist without a calibrated bin value")
    if summary.filter(pl.col("has_uncertified_or_missing_bin_value")).height:
        raise RuntimeError("uncertified bin estimator reached production player-season output")

    summary_path = OUTPUT_DIR / "batting_performance_summary_2024_aaa.parquet"
    profile_path = OUTPUT_DIR / "batting_performance_bins_2024_aaa.parquet"
    values_path = OUTPUT_DIR / "league_bin_values_2024_aaa.parquet"
    summary_artifact = write_canonical_parquet(
        summary, summary_path, table_name="batting_performance_summary"
    )
    profile_artifact = write_canonical_parquet(
        profile, profile_path, table_name="batting_performance_bins"
    )
    values_artifact = write_canonical_parquet(
        bin_values, values_path, table_name="league_performance_bin_values"
    )
    duckdb_metrics = _duckdb_validate(summary_path, profile_path)

    total_pa = int(summary.get_column("batting_plate_appearances").sum() or 0)
    total_contact_residual = int(
        summary.get_column("contact_count_residual_vs_aggregate").sum() or 0
    )
    core_events = int(summary.get_column("core_profile_event_count").sum() or 0)
    unknown_contacts = int(summary.get_column("unknown_contact_count").sum() or 0)
    foul_air = int(summary.get_column("foul_air_excluded_count").sum() or 0)
    bunts = int(summary.get_column("bunt_contact_count").sum() or 0)
    overlay_contacts = int(summary.get_column("official_overlay_contact_count").sum() or 0)

    report = {
        "report_schema_version": 1,
        "scope": {"season": SEASON, "level": LEVEL, "league_ids": sorted(AAA_LEAGUE_IDS)},
        "source_contacts": contact_source_metrics,
        "player_game_controls": player_game_metrics,
        "participant_authority": authority_metrics,
        "season_aggregate_schema": season_metadata,
        "calibration": calibration_metrics,
        "player_season_output": {
            "summary_row_count": summary.height,
            "profile_row_count": profile.height,
            "total_plate_appearances": total_pa,
            "total_classified_contact_count": classified_contacts.height,
            "total_contact_residual_vs_aggregate": total_contact_residual,
            "total_core_profile_event_count": core_events,
            "core_profile_coverage_rate": core_events / total_pa if total_pa else None,
            "bunt_contact_count": bunts,
            "foul_air_excluded_count": foul_air,
            "unknown_contact_count": unknown_contacts,
            "official_overlay_contact_count": overlay_contacts,
            "players_with_contact_residual": summary.filter(
                pl.col("contact_count_residual_vs_aggregate") != 0
            ).height,
            "players_with_unknown_contact_evidence": summary.filter(
                pl.col("unknown_contact_count") > 0
            ).height,
        },
        "storage": {
            "summary": summary_artifact.as_record(),
            "profile": profile_artifact.as_record(),
            "bin_values": values_artifact.as_record(),
            "duckdb": duckdb_metrics,
        },
        "interpretation": (
            "This is a Performance-layer expected contextual run-value profile, not a "
            "Current Talent estimate, projection, WAR value, or overall player ranking."
        ),
    }
    (REPORT_DIR / "batting_performance_season_poc.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# Batting Performance player-season POC — 2024 AAA",
        "",
        f"- Player × league × season rows: {summary.height:,}",
        f"- Total PA: {total_pa:,}",
        f"- Resolved reusable contacts: {contacts.height:,}",
        f"- Participant exception games: {authority_metrics['exception_game_count']:,}",
        f"- Contacts under official participant overlay: {overlay_contacts:,}",
        f"- Batter IDs changed by overlay: {authority_metrics['changed_batter_contact_count']:,}",
        f"- Final classified contacts: {classified_contacts.height:,}",
        f"- Contact count residual vs season aggregate: {total_contact_residual:+,}",
        f"- Core Performance events: {core_events:,} ({core_events / total_pa:.2%} of PA)",
        f"- Non-core contacts — bunt / foul-air / unknown: {bunts:,} / {foul_air:,} / {unknown_contacts:,}",
        f"- Calibrated league-bin rows: {bin_values.height:,}",
        f"- Unvalued core event rows: {summary.filter(pl.col('unvalued_core_event_count') > 0).height:,}",
        f"- DuckDB summary uniqueness: {duckdb_metrics['unique_summary_keys']:,}/{duckdb_metrics['summary_rows']:,}",
        "",
        "This is the first production Performance-layer player-season artifact. It is not a talent estimate or projection.",
    ]
    text = "\n".join(lines)
    (REPORT_DIR / "batting_performance_season_poc.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
