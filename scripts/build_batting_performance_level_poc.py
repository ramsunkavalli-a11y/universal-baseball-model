#!/usr/bin/env python
"""Build one completed-2024 MiLB batting Performance level POC.

This generalizes the accepted 2024 AAA player-season transform to AA, High-A,
Single-A, and Rookie/complex without changing production model semantics.

Each invocation:

1. resolves all reusable 2024 PBP contact snapshots for one filename level;
2. resolves all reusable player-game batting controls for that level;
3. fetches official PBP only for player-game residual exception games and
   requires exact physical contact-key equality before participant overlay;
4. independently samples unflagged games to test the residual trigger for hidden
   batter-attribution false negatives at the new level;
5. classifies final screened contact bins from reusable geometry/narrative;
6. loads the certified 2024 season-player batting outcome backbone;
7. builds a deterministic 45-game-per-actual-league RE24 calibration sample;
8. applies the already-frozen level-specific bin-value policy; and
9. writes unique player × actual-league × season summary/profile Parquet tables.

This is still the Performance layer only. No Current Talent, projection,
playing-time forecast, defense, WAR, or overall ranking is produced.
"""

from __future__ import annotations

import argparse
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
    OFFICIAL_CONTACT_AUTHORITY_SCHEMA,
    apply_contact_identity_authority,
    contact_identity_residuals,
    exception_games_from_residuals,
    project_official_contact_authority,
)
from universal_baseball.contact_profile import classify_contact_profile_events
from universal_baseball.official import fetch_official_game_evidence
from universal_baseball.performance_level_config import performance_level_spec_2024
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
GAME_TYPE = "R"
UNFLAGGED_IDENTITY_SAMPLE_GAMES = 40


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--level",
        required=True,
        choices=("aaa", "aa", "a+", "a", "rk"),
        help="armstjc filename level",
    )
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("data/quarantine/batting-performance-multilevel-poc"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/batting-performance-multilevel-poc"),
    )
    parser.add_argument(
        "--unflagged-sample-games",
        type=int,
        default=UNFLAGGED_IDENTITY_SAMPLE_GAMES,
    )
    return parser.parse_args()


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


def _load_reusable_contacts(
    level: str,
    league_ids: frozenset[int],
    work_dir: Path,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    pbp_dir = work_dir / "pbp"
    assets = [
        asset
        for asset in fetch_pbp_asset_inventory()
        if asset.year == SEASON and asset.filename_level == level
    ]
    if not assets:
        raise RuntimeError(f"no reusable {SEASON} {level} PBP assets found")

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
    unexpected = contacts.filter(~pl.col("league_id").is_in(sorted(league_ids)))

    if metrics["contact_status_conflict_key_count"]:
        raise RuntimeError(
            f"{level} contact-status conflicts block multi-level Performance POC"
        )
    if contacts.filter(pl.col("source_batter_id").is_null()).height:
        raise RuntimeError(f"{level} unresolved contact batter blocks identity control")
    if not unexpected.is_empty():
        unexpected_ids = sorted(
            int(value)
            for value in unexpected.get_column("league_id").drop_nulls().unique().to_list()
        )
        raise RuntimeError(
            f"{level} contact source contains unexpected actual league IDs: {unexpected_ids}"
        )

    observed_leagues = set(
        int(value) for value in contacts.get_column("league_id").unique().to_list()
    )
    if observed_leagues != set(league_ids):
        raise RuntimeError(
            f"{level} source actual-league coverage mismatch: "
            f"observed={sorted(observed_leagues)}, expected={sorted(league_ids)}"
        )
    return contacts, {
        "asset_count": len(assets),
        "asset_names": [asset.name for asset in assets],
        "observed_league_ids": sorted(observed_leagues),
        **metrics,
    }


def _load_player_game_controls(
    level: str,
    league_ids: frozenset[int],
    work_dir: Path,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    player_game_dir = work_dir / "player-game"
    assets = [
        asset
        for asset in fetch_player_game_asset_inventory()
        if asset.year == SEASON and asset.filename_level == level
    ]
    if not assets:
        raise RuntimeError(f"no reusable {SEASON} {level} player-game assets found")

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
    expected = resolved.filter(pl.col("expected_contact_count").is_not_null())
    unexpected = expected.filter(~pl.col("league_id").is_in(sorted(league_ids)))
    if metrics["unresolved_expected_contact_player_game_count"]:
        raise RuntimeError(
            f"{level} unresolved player-game contact controls block production POC"
        )
    if not unexpected.is_empty():
        raise RuntimeError(f"{level} player-game controls contain unexpected league IDs")
    observed_leagues = set(
        int(value)
        for value in expected.get_column("league_id").drop_nulls().unique().to_list()
    )
    if observed_leagues != set(league_ids):
        raise RuntimeError(
            f"{level} player-game league coverage mismatch: "
            f"observed={sorted(observed_leagues)}, expected={sorted(league_ids)}"
        )
    return resolved, {
        "asset_count": len(assets),
        "asset_names": [asset.name for asset in assets],
        "observed_league_ids": sorted(observed_leagues),
        **metrics,
    }


def _compare_source_official_contacts(
    source_contacts: pl.DataFrame,
    official_contacts: pl.DataFrame,
) -> dict[str, int]:
    key = ["game_pk", "at_bat_index", "pitch_number"]
    source = source_contacts.select(
        *[pl.col(column).cast(pl.Int64) for column in key],
        pl.col("source_batter_id").cast(pl.Int64),
    )
    official = official_contacts.select(
        *[pl.col(column).cast(pl.Int64) for column in key],
        pl.col("official_batter_id").cast(pl.Int64),
    )
    source_only = source.join(official.select(key), on=key, how="anti")
    official_only = official.join(source.select(key), on=key, how="anti")
    both = source.join(official, on=key, how="inner")
    batter_mismatch = both.filter(
        pl.col("source_batter_id") != pl.col("official_batter_id")
    )
    return {
        "source_contact_count": source.height,
        "official_contact_count": official.height,
        "matched_physical_key_count": both.height,
        "source_only_physical_key_count": source_only.height,
        "official_only_physical_key_count": official_only.height,
        "batter_mismatch_count": batter_mismatch.height,
        "batter_mismatch_game_count": batter_mismatch.get_column("game_pk").n_unique(),
    }


def _participant_authority_and_false_negative_gate(
    contacts: pl.DataFrame,
    player_games: pl.DataFrame,
    *,
    unflagged_sample_games: int,
) -> tuple[pl.DataFrame, dict[str, Any], dict[str, Any]]:
    residuals = contact_identity_residuals(contacts, player_games)
    exception_games = exception_games_from_residuals(residuals)
    if exception_games:
        pa, pitch = fetch_official_game_evidence(exception_games)
        official_contacts = project_official_contact_authority(pa, pitch)
    else:
        official_contacts = pl.DataFrame(schema=OFFICIAL_CONTACT_AUTHORITY_SCHEMA)
    authorized, authority_metrics = apply_contact_identity_authority(
        contacts, player_games, official_contacts
    )

    all_games = sorted(
        int(value) for value in contacts.get_column("game_pk").unique().to_list()
    )
    exception_set = set(exception_games)
    unflagged = [game for game in all_games if game not in exception_set]
    sample = _evenly_spaced(unflagged, unflagged_sample_games)
    if sample:
        sample_pa, sample_pitch = fetch_official_game_evidence(sample)
        sample_official = project_official_contact_authority(sample_pa, sample_pitch)
        sample_source = contacts.filter(pl.col("game_pk").is_in(sample))
        comparison = _compare_source_official_contacts(sample_source, sample_official)
        if comparison["source_only_physical_key_count"]:
            raise RuntimeError("unflagged identity sample has source-only physical contacts")
        if comparison["official_only_physical_key_count"]:
            raise RuntimeError("unflagged identity sample has official-only physical contacts")
        if comparison["batter_mismatch_count"]:
            raise RuntimeError(
                "unflagged identity sample found hidden source batter attribution errors"
            )
    else:
        comparison = {
            "source_contact_count": 0,
            "official_contact_count": 0,
            "matched_physical_key_count": 0,
            "source_only_physical_key_count": 0,
            "official_only_physical_key_count": 0,
            "batter_mismatch_count": 0,
            "batter_mismatch_game_count": 0,
        }

    false_negative = {
        "design": "deterministic evenly spaced unflagged contact games",
        "unflagged_game_count": len(unflagged),
        "sample_game_count": len(sample),
        "sample_game_ids": sample,
        **comparison,
    }
    return authorized, authority_metrics, false_negative


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


def _load_season_batting(
    asset: str,
    url: str,
    league_ids: frozenset[int],
    work_dir: Path,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    path = work_dir / "season" / asset
    if not path.exists() or path.stat().st_size <= 0:
        download_file(url, path, timeout_seconds=240)
    raw = read_quarantined_csv(path)
    standardized, metadata = standardize_armstjc_season_stats(raw, "batting")
    standardized = standardized.filter(
        (pl.col("season").cast(pl.Int64, strict=False) == SEASON)
        & pl.col("league_id").cast(pl.Int64, strict=False).is_in(sorted(league_ids))
    )
    observed = set(
        int(value)
        for value in standardized.get_column("league_id").cast(pl.Int64).unique().to_list()
    )
    if standardized.is_empty() or observed != set(league_ids):
        raise RuntimeError(
            f"season batting actual-league coverage mismatch: "
            f"observed={sorted(observed)}, expected={sorted(league_ids)}"
        )
    return standardized, metadata


def _calibrate_bin_values(
    *,
    calibration_asset: str,
    league_ids: frozenset[int],
    level_group: str,
    work_dir: Path,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    calibration_dir = work_dir / "calibration"
    original_pool_map = screened.POOL_GROUP_BY_LEAGUE
    screened.POOL_GROUP_BY_LEAGUE = {
        int(league_id): str(level_group) for league_id in league_ids
    }
    try:
        frames, environment_meta = screened._load_environment_frames(
            assets=(calibration_asset,),
            work_dir=calibration_dir,
            allowed_leagues=set(league_ids),
        )
    finally:
        screened.POOL_GROUP_BY_LEAGUE = original_pool_map

    observed = {
        int(metadata["league_id"]) for metadata in environment_meta.values()
    }
    if observed != set(league_ids):
        raise RuntimeError(
            f"calibration actual-league coverage mismatch: "
            f"observed={sorted(observed)}, expected={sorted(league_ids)}"
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
        if matrix.height != 24:
            raise RuntimeError(
                f"calibration environment {environment_id} observed {matrix.height}/24 states"
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
    uncertified = estimated.filter(~pl.col("estimator_certified"))
    if not uncertified.is_empty():
        raise RuntimeError(
            f"calibration contains {uncertified.height} uncertified bin estimates"
        )
    return estimated, {
        "asset": calibration_asset,
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
    args = parse_args()
    spec = performance_level_spec_2024(args.level)
    slug_for_path = spec.filename_level.replace("+", "plus")
    work_dir = args.work_root / slug_for_path
    report_dir = args.report_root / slug_for_path
    output_dir = report_dir / "tables"
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    contacts, contact_source_metrics = _load_reusable_contacts(
        spec.filename_level, spec.league_ids, work_dir
    )
    player_games, player_game_metrics = _load_player_game_controls(
        spec.filename_level, spec.league_ids, work_dir
    )
    authorized, authority_metrics, false_negative_metrics = (
        _participant_authority_and_false_negative_gate(
            contacts,
            player_games,
            unflagged_sample_games=args.unflagged_sample_games,
        )
    )
    classified = _classify_contacts(authorized)
    season_batting, season_metadata = _load_season_batting(
        spec.season_batting_asset,
        spec.season_batting_url,
        spec.league_ids,
        work_dir,
    )
    bin_values, calibration_metrics = _calibrate_bin_values(
        calibration_asset=spec.calibration_asset,
        league_ids=spec.league_ids,
        level_group=spec.level_group,
        work_dir=work_dir,
    )
    summary, profile = build_batting_performance_season(
        season_batting, classified, bin_values
    )

    if summary.group_by(["season", "league_id", "player_id"]).len().filter(
        pl.col("len") > 1
    ).height:
        raise RuntimeError("duplicate player-league-season Performance rows")
    if summary.filter(pl.col("core_profile_count_exceeds_pa")).height:
        raise RuntimeError("core Performance event count exceeds PA")
    if summary.filter(pl.col("unvalued_core_event_count") > 0).height:
        raise RuntimeError("core Performance events exist without calibrated bin value")
    if summary.filter(pl.col("has_uncertified_or_missing_bin_value")).height:
        raise RuntimeError("uncertified bin estimator reached player-season output")

    summary_path = output_dir / f"batting_performance_summary_{SEASON}_{slug_for_path}.parquet"
    profile_path = output_dir / f"batting_performance_bins_{SEASON}_{slug_for_path}.parquet"
    values_path = output_dir / f"league_bin_values_{SEASON}_{slug_for_path}.parquet"
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
    core_events = int(summary.get_column("core_profile_event_count").sum() or 0)
    contact_residual = int(
        summary.get_column("contact_count_residual_vs_aggregate").sum() or 0
    )
    bunts = int(summary.get_column("bunt_contact_count").sum() or 0)
    foul_air = int(summary.get_column("foul_air_excluded_count").sum() or 0)
    unknown = int(summary.get_column("unknown_contact_count").sum() or 0)
    overlay = int(summary.get_column("official_overlay_contact_count").sum() or 0)

    report = {
        "report_schema_version": 1,
        "scope": {
            "season": SEASON,
            "filename_level": spec.filename_level,
            "level_group": spec.level_group,
            "display_name": spec.display_name,
            "league_ids": sorted(spec.league_ids),
        },
        "source_contacts": contact_source_metrics,
        "player_game_controls": player_game_metrics,
        "participant_authority": authority_metrics,
        "unflagged_identity_false_negative_gate": false_negative_metrics,
        "season_aggregate_schema": season_metadata,
        "calibration": calibration_metrics,
        "player_season_output": {
            "summary_row_count": summary.height,
            "profile_row_count": profile.height,
            "total_plate_appearances": total_pa,
            "total_classified_contact_count": classified.height,
            "total_contact_residual_vs_aggregate": contact_residual,
            "total_core_profile_event_count": core_events,
            "core_profile_coverage_rate": core_events / total_pa if total_pa else None,
            "bunt_contact_count": bunts,
            "foul_air_excluded_count": foul_air,
            "unknown_contact_count": unknown,
            "official_overlay_contact_count": overlay,
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
            "Performance-layer contextual profile only; not Current Talent, projection, "
            "WAR, or overall ranking. Pitch-process capability restrictions are separate "
            "and do not remove PA/BIP Performance evidence."
        ),
    }
    (report_dir / "batting_performance_level_poc.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        f"# Batting Performance player-season POC — {SEASON} {spec.display_name}",
        "",
        f"- Actual leagues: {sorted(spec.league_ids)}",
        f"- Player × league × season rows: {summary.height:,}",
        f"- Total PA: {total_pa:,}",
        f"- Resolved reusable contacts: {contacts.height:,}",
        f"- Participant exception games: {authority_metrics['exception_game_count']:,}",
        f"- Contacts under official participant overlay: {overlay:,}",
        f"- Batter IDs changed by overlay: {authority_metrics['changed_batter_contact_count']:,}",
        f"- Unflagged identity sample: {false_negative_metrics['sample_game_count']:,} games / "
        f"{false_negative_metrics['matched_physical_key_count']:,} matched contacts / "
        f"{false_negative_metrics['batter_mismatch_count']:,} batter mismatches",
        f"- Final classified contacts: {classified.height:,}",
        f"- Contact count residual vs season aggregate: {contact_residual:+,}",
        f"- Core Performance events: {core_events:,} ({core_events / total_pa:.2%} of PA)",
        f"- Non-core contacts — bunt / foul-air / unknown: {bunts:,} / {foul_air:,} / {unknown:,}",
        f"- Calibrated league-bin rows: {bin_values.height:,}",
        f"- Unvalued core event rows: {summary.filter(pl.col('unvalued_core_event_count') > 0).height:,}",
        f"- DuckDB summary uniqueness: {duckdb_metrics['unique_summary_keys']:,}/{duckdb_metrics['summary_rows']:,}",
    ]
    text = "\n".join(lines)
    (report_dir / "batting_performance_level_poc.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
