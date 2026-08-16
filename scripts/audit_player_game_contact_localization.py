#!/usr/bin/env python
"""Localize 2024 AAA reusable-PBP contact identity residuals by player-game.

This is the next gate after the full-season contact reconciliation.  It combines
three independently useful reusable layers:

1. armstjc PBP snapshots, collapsed by natural pitch key without filename-order
   precedence;
2. armstjc player-game boxscore snapshots, exact-deduped and resolved by
   player-game consensus; and
3. the already-certified armstjc season-player batting aggregate.

The player-game release is especially useful because its upstream monthly
builder currently appends each successful game twice.  Raw duplication is
therefore measured and removed explicitly, never silently summed.

No broad source repair is assumed.  A source-only batter reassignment is
accepted only under the strict rule implemented in
``identify_unambiguous_contact_reassignments``: exactly one +1 and one -1
player residual in a game, with the +1 player owning exactly one source contact
and zero player-game boxscore contacts.  All other mismatches remain candidates
for a narrow official-PBP exception overlay.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.armstjc_assets import fetch_pbp_asset_inventory
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.player_game_stats import (
    fetch_player_game_asset_inventory,
    identify_unambiguous_contact_reassignments,
    project_player_game_batting,
    resolve_player_game_batting,
)
from universal_baseball.season_stats import standardize_armstjc_season_stats


SEASON = 2024
LEVEL = "aaa"
GAME_TYPE = "R"
IN_PLAY_CODES = ("D", "E", "X")
PITCH_KEY = ["game_pk", "at_bat_index", "pitch_number"]
SEASON_ASSET = "2024_aaa_season_batting_stats.csv"
SEASON_TAG = "season_player_batting"
BASE_RELEASE_URL = "https://github.com/armstjc/milb-data-repository/releases/download"


def _int_expr(column: str, alias: str | None = None) -> pl.Expr:
    numeric = pl.col(column).cast(pl.Float64, strict=False)
    return (
        pl.when(numeric.is_not_null() & (numeric == numeric.floor()))
        .then(numeric.cast(pl.Int64, strict=False))
        .otherwise(None)
        .alias(alias or column)
    )


def _nonblank(column: str) -> pl.Expr:
    return pl.col(column).is_not_null() & (
        pl.col(column).cast(pl.String).str.strip_chars() != ""
    )


def _project_pbp_asset(frame: pl.DataFrame, asset_name: str) -> pl.DataFrame:
    required = {
        "game_pk",
        "at_bat_number",
        "pitch_number",
        "batter",
        "league_id",
        "game_date",
        "game_type",
        "type",
        "bb_type",
        "hit_location",
        "hc_x",
        "hc_y",
        "hit_distance_sc",
        "launch_speed",
        "launch_angle",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{asset_name} missing PBP localization fields: {missing}")

    contact_evidence = (
        pl.col("type").cast(pl.String).str.strip_chars().is_in(IN_PLAY_CODES)
        | _nonblank("bb_type")
        | _nonblank("hit_location")
        | _nonblank("hc_x")
        | _nonblank("hc_y")
        | _nonblank("hit_distance_sc")
        | _nonblank("launch_speed")
        | _nonblank("launch_angle")
    )
    return (
        frame.select(
            _int_expr("game_pk"),
            _int_expr("at_bat_number", "at_bat_index"),
            _int_expr("pitch_number"),
            _int_expr("batter", "source_batter_id"),
            _int_expr("league_id"),
            pl.col("game_date").cast(pl.String),
            pl.col("game_type").cast(pl.String),
            contact_evidence.alias("source_is_in_play"),
            pl.lit(asset_name).alias("source_asset"),
        )
        .drop_nulls(PITCH_KEY)
        .filter(
            (pl.col("game_type") == GAME_TYPE)
            & pl.col("game_date").str.starts_with(f"{SEASON}-")
        )
    )


def _resolve_pbp_pitch_keys(observations: pl.DataFrame) -> pl.DataFrame:
    if observations.is_empty():
        raise RuntimeError("no regular-season PBP observations after projection")
    return (
        observations.group_by(PITCH_KEY)
        .agg(
            pl.col("source_asset").n_unique().alias("source_snapshot_count"),
            pl.col("source_asset").unique().sort().alias("source_assets"),
            pl.col("league_id").drop_nulls().n_unique().alias("league_value_count"),
            pl.when(pl.col("league_id").drop_nulls().n_unique() <= 1)
            .then(pl.col("league_id").drop_nulls().first())
            .otherwise(None)
            .alias("league_id"),
            pl.col("source_batter_id")
            .drop_nulls()
            .n_unique()
            .alias("batter_value_count"),
            pl.when(pl.col("source_batter_id").drop_nulls().n_unique() <= 1)
            .then(pl.col("source_batter_id").drop_nulls().first())
            .otherwise(None)
            .alias("source_batter_id"),
            pl.col("source_is_in_play").n_unique().alias("in_play_value_count"),
            pl.when(pl.col("source_is_in_play").n_unique() <= 1)
            .then(pl.col("source_is_in_play").first())
            .otherwise(None)
            .alias("source_is_in_play"),
            pl.len().alias("raw_observation_count"),
        )
        .sort(PITCH_KEY)
    )


def _season_target(frame: pl.DataFrame) -> pl.DataFrame:
    standardized, _ = standardize_armstjc_season_stats(frame, "batting")
    required = {"season", "league_id", "player_id", "batting_balls_in_play"}
    missing = sorted(required - set(standardized.columns))
    if missing:
        raise ValueError(f"season batting aggregate missing target fields: {missing}")
    return (
        standardized.filter(pl.col("season").cast(pl.Int64, strict=False) == SEASON)
        .with_columns(
            _int_expr("league_id"),
            _int_expr("player_id"),
            _int_expr("batting_balls_in_play"),
        )
        .drop_nulls(["league_id", "player_id", "batting_balls_in_play"])
        .group_by(["league_id", "player_id"])
        .agg(pl.col("batting_balls_in_play").sum().alias("season_aggregate_bip"))
    )


def _outer_contact_comparison(
    source_by_game_player: pl.DataFrame,
    expected_by_game_player: pl.DataFrame,
) -> pl.DataFrame:
    return (
        source_by_game_player.join(
            expected_by_game_player,
            on=["game_id", "player_id"],
            how="full",
            coalesce=True,
        )
        .with_columns(
            pl.col("source_contact_count").fill_null(0).cast(pl.Int64),
            pl.col("expected_contact_count").fill_null(0).cast(pl.Int64),
        )
        .with_columns(
            (
                pl.col("source_contact_count") - pl.col("expected_contact_count")
            ).alias("difference")
        )
        .filter(
            (pl.col("source_contact_count") > 0)
            | (pl.col("expected_contact_count") > 0)
        )
        .sort(["game_id", "difference", "player_id"], descending=[False, True, False])
    )


def _residual_metrics(comparison: pl.DataFrame) -> dict[str, Any]:
    nonzero = comparison.filter(pl.col("difference") != 0)
    positive_mass = int(
        comparison.select(
            pl.when(pl.col("difference") > 0)
            .then(pl.col("difference"))
            .otherwise(0)
            .sum()
        ).item()
        or 0
    )
    negative_mass = int(
        comparison.select(
            pl.when(pl.col("difference") < 0)
            .then(-pl.col("difference"))
            .otherwise(0)
            .sum()
        ).item()
        or 0
    )
    return {
        "active_player_game_count": comparison.height,
        "exact_player_game_count": comparison.filter(pl.col("difference") == 0).height,
        "nonzero_player_game_count": nonzero.height,
        "mismatch_game_count": nonzero.get_column("game_id").n_unique(),
        "positive_residual_mass": positive_mass,
        "negative_residual_mass": negative_mass,
        "absolute_discrepancy_mass": positive_mass + negative_mass,
        "residual_mass_imbalance": positive_mass - negative_mass,
        "difference_distribution": dict(
            sorted(Counter(int(value) for value in nonzero.get_column("difference")).items())
        ),
    }


def _game_residual_summary(comparison: pl.DataFrame) -> pl.DataFrame:
    return (
        comparison.group_by("game_id")
        .agg(
            pl.col("source_contact_count").sum().alias("source_contact_count"),
            pl.col("expected_contact_count").sum().alias("expected_contact_count"),
            pl.col("difference").sum().alias("game_difference"),
            pl.col("difference").abs().sum().alias("player_abs_discrepancy_mass"),
            (pl.col("difference") != 0).sum().alias("nonzero_player_count"),
            pl.when(pl.col("difference") > 0)
            .then(pl.col("difference"))
            .otherwise(0)
            .sum()
            .alias("positive_mass"),
            pl.when(pl.col("difference") < 0)
            .then(-pl.col("difference"))
            .otherwise(0)
            .sum()
            .alias("negative_mass"),
        )
        .sort("game_id")
    )


def _season_reconciliation(
    player_games: pl.DataFrame,
    season_target: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    game_to_season = (
        player_games.filter(
            pl.col("expected_contact_count").is_not_null()
            & pl.col("league_id").is_not_null()
        )
        .group_by(["league_id", "player_id"])
        .agg(pl.col("expected_contact_count").sum().alias("player_game_bip"))
    )
    comparison = (
        game_to_season.join(
            season_target,
            on=["league_id", "player_id"],
            how="full",
            coalesce=True,
        )
        .with_columns(
            pl.col("player_game_bip").fill_null(0),
            pl.col("season_aggregate_bip").fill_null(0),
        )
        .with_columns(
            (pl.col("player_game_bip") - pl.col("season_aggregate_bip")).alias(
                "difference"
            )
        )
        .filter(
            (pl.col("player_game_bip") > 0) | (pl.col("season_aggregate_bip") > 0)
        )
    )
    abs_mass = int(comparison.select(pl.col("difference").abs().sum()).item() or 0)
    season_total = int(season_target.get_column("season_aggregate_bip").sum() or 0)
    metrics = {
        "player_game_contact_total": int(
            comparison.get_column("player_game_bip").sum() or 0
        ),
        "season_aggregate_bip_total": season_total,
        "total_difference": int(comparison.get_column("difference").sum() or 0),
        "active_player_league_count": comparison.height,
        "exact_player_league_count": comparison.filter(pl.col("difference") == 0).height,
        "nonzero_player_league_count": comparison.filter(pl.col("difference") != 0).height,
        "absolute_discrepancy_mass": abs_mass,
        "absolute_discrepancy_rate_vs_season_bip": (
            abs_mass / season_total if season_total else None
        ),
    }
    return comparison, metrics


def main() -> int:
    work_dir = Path("data/quarantine/player-game-contact-localization")
    report_dir = Path("reports/generated/player-game-contact-localization")
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    # --- PBP contact layer -------------------------------------------------
    pbp_assets = [
        asset
        for asset in fetch_pbp_asset_inventory()
        if asset.year == SEASON and asset.filename_level == LEVEL
    ]
    if not pbp_assets:
        raise RuntimeError(f"no {SEASON} {LEVEL} PBP assets")

    pbp_projections: list[pl.DataFrame] = []
    pbp_asset_records: list[dict[str, Any]] = []
    for asset in pbp_assets:
        path = work_dir / asset.name
        metadata = download_file(asset.browser_download_url, path, timeout_seconds=300)
        raw = read_quarantined_csv(path)
        projection = _project_pbp_asset(raw, asset.name)
        pbp_projections.append(projection)
        pbp_asset_records.append(
            {
                "asset": asset.name,
                "filename_period": asset.filename_period,
                "size_bytes": asset.size_bytes,
                "created_at_utc": asset.created_at_utc.isoformat(),
                "updated_at_utc": asset.updated_at_utc.isoformat(),
                "sha256": metadata["sha256"],
                "regular_season_source_rows": projection.height,
                "regular_season_game_count": projection.get_column("game_pk").n_unique(),
            }
        )
        del raw

    pbp_observations = pl.concat(pbp_projections, how="vertical_relaxed")
    resolved_pitches = _resolve_pbp_pitch_keys(pbp_observations)
    contact_status_conflicts = resolved_pitches.filter(pl.col("in_play_value_count") > 1)
    contacts = resolved_pitches.filter(pl.col("source_is_in_play") == True)  # noqa: E712
    unresolved_contact_batters = contacts.filter(pl.col("source_batter_id").is_null())

    source_by_game_player = (
        contacts.filter(pl.col("source_batter_id").is_not_null())
        .select(
            pl.col("game_pk").alias("game_id"),
            pl.col("source_batter_id").alias("player_id"),
        )
        .group_by(["game_id", "player_id"])
        .len(name="source_contact_count")
    )

    # --- Reusable player-game boxscore layer ------------------------------
    player_game_assets = [
        asset
        for asset in fetch_player_game_asset_inventory()
        if asset.year == SEASON and asset.filename_level == LEVEL
    ]
    if not player_game_assets:
        raise RuntimeError(f"no {SEASON} {LEVEL} player-game assets")

    player_game_projections: list[pl.DataFrame] = []
    player_game_asset_records: list[dict[str, Any]] = []
    for asset in player_game_assets:
        path = work_dir / asset.name
        metadata = download_file(asset.browser_download_url, path, timeout_seconds=240)
        raw = read_quarantined_csv(path)
        projection = project_player_game_batting(
            raw,
            source_asset=asset.name,
            season=SEASON,
            game_type=GAME_TYPE,
        )
        player_game_projections.append(projection)
        player_game_asset_records.append(
            {
                "asset": asset.name,
                "filename_period": asset.filename_period,
                "size_bytes": asset.size_bytes,
                "created_at_utc": asset.created_at_utc.isoformat(),
                "updated_at_utc": asset.updated_at_utc.isoformat(),
                "sha256": metadata["sha256"],
                "regular_season_projected_rows": projection.height,
                "regular_season_game_count": projection.get_column("game_id").n_unique(),
            }
        )
        del raw

    player_game_observations = pl.concat(
        player_game_projections, how="vertical_relaxed"
    )
    player_games, player_game_diagnostics = resolve_player_game_batting(
        player_game_observations
    )
    expected_by_game_player = player_games.select(
        "game_id", "player_id", "expected_contact_count"
    ).filter(pl.col("expected_contact_count").is_not_null())

    # --- Independent season aggregate check -------------------------------
    season_path = work_dir / SEASON_ASSET
    season_metadata = download_file(
        f"{BASE_RELEASE_URL}/{SEASON_TAG}/{SEASON_ASSET}",
        season_path,
        timeout_seconds=240,
    )
    season_raw = read_quarantined_csv(season_path)
    season_target = _season_target(season_raw)
    season_comparison, season_metrics = _season_reconciliation(
        player_games, season_target
    )

    # --- Localize and conservatively repair participant residuals ----------
    comparison = _outer_contact_comparison(
        source_by_game_player, expected_by_game_player
    )
    before_metrics = _residual_metrics(comparison)
    game_summary = _game_residual_summary(comparison)
    repairs = identify_unambiguous_contact_reassignments(comparison)

    repair_contact_keys = (
        contacts.select(
            pl.col("game_pk").alias("game_id"),
            "at_bat_index",
            "pitch_number",
            "source_batter_id",
        )
        .join(repairs, on=["game_id", "source_batter_id"], how="inner")
        .sort(["game_id", "at_bat_index", "pitch_number"])
    )
    repair_mapping_is_unique = repair_contact_keys.height == repairs.height

    repaired_contacts = (
        contacts.select(
            pl.col("game_pk").alias("game_id"),
            "at_bat_index",
            "pitch_number",
            "source_batter_id",
        )
        .join(repairs, on=["game_id", "source_batter_id"], how="left")
        .with_columns(
            pl.coalesce(["reassigned_batter_id", "source_batter_id"]).alias(
                "effective_batter_id"
            )
        )
    )
    repaired_source_by_game_player = (
        repaired_contacts.filter(pl.col("effective_batter_id").is_not_null())
        .group_by(["game_id", "effective_batter_id"])
        .len(name="source_contact_count")
        .rename({"effective_batter_id": "player_id"})
    )
    repaired_comparison = _outer_contact_comparison(
        repaired_source_by_game_player, expected_by_game_player
    )
    after_metrics = _residual_metrics(repaired_comparison)
    repaired_game_summary = _game_residual_summary(repaired_comparison)

    # Any game still carrying a player residual is a narrow exception target.
    exception_games = (
        repaired_comparison.filter(pl.col("difference") != 0)
        .select("game_id")
        .unique()
        .sort("game_id")
    )

    # Persist compact diagnostics for exact inspection in the workflow artifact.
    comparison.filter(pl.col("difference") != 0).write_csv(
        report_dir / "player_game_residuals_before_repair.csv"
    )
    repaired_comparison.filter(pl.col("difference") != 0).write_csv(
        report_dir / "player_game_residuals_after_repair.csv"
    )
    game_summary.filter(pl.col("player_abs_discrepancy_mass") > 0).write_csv(
        report_dir / "game_residuals_before_repair.csv"
    )
    repaired_game_summary.filter(pl.col("player_abs_discrepancy_mass") > 0).write_csv(
        report_dir / "game_residuals_after_repair.csv"
    )
    repairs.write_csv(report_dir / "unambiguous_source_only_reassignments.csv")
    repair_contact_keys.write_csv(report_dir / "reassigned_contact_keys.csv")
    season_comparison.filter(pl.col("difference") != 0).write_csv(
        report_dir / "player_game_vs_season_residuals.csv"
    )

    balanced_unit_pair_games = game_summary.filter(
        (pl.col("nonzero_player_count") == 2)
        & (pl.col("positive_mass") == 1)
        & (pl.col("negative_mass") == 1)
        & (pl.col("game_difference") == 0)
    ).height

    source_total = contacts.height
    player_game_total = int(
        expected_by_game_player.get_column("expected_contact_count").sum() or 0
    )
    payload = {
        "report_schema_version": 1,
        "status": "player_game_contact_localization_discovery",
        "season": SEASON,
        "level": LEVEL,
        "game_type": GAME_TYPE,
        "pbp": {
            "assets": pbp_asset_records,
            "asset_count": len(pbp_assets),
            "raw_projected_observation_count": pbp_observations.height,
            "resolved_pitch_key_count": resolved_pitches.height,
            "contact_status_conflict_key_count": contact_status_conflicts.height,
            "resolved_contact_key_count": source_total,
            "unresolved_contact_batter_count": unresolved_contact_batters.height,
        },
        "player_game": {
            "assets": player_game_asset_records,
            "asset_count": len(player_game_assets),
            **player_game_diagnostics,
            "resolved_expected_contact_total": player_game_total,
        },
        "season_aggregate": {
            "asset": SEASON_ASSET,
            "sha256": season_metadata["sha256"],
            **season_metrics,
        },
        "source_vs_player_game": {
            "source_contact_total": source_total,
            "player_game_expected_contact_total": player_game_total,
            "total_difference": source_total - player_game_total,
            "before_repair": before_metrics,
            "balanced_unit_pair_game_count": balanced_unit_pair_games,
            "strict_unambiguous_reassignment_count": repairs.height,
            "strict_reassignment_contact_key_count": repair_contact_keys.height,
            "strict_repair_mapping_is_unique": repair_mapping_is_unique,
            "after_repair": after_metrics,
            "remaining_exception_game_count": exception_games.height,
            "remaining_exception_game_ids": exception_games.get_column("game_id").to_list(),
        },
        "policy_guardrail": (
            "Only the strict source-only +1/-1 mapping is applied in this discovery report. "
            "All remaining games stay unresolved and are candidates for narrow official-PBP "
            "adjudication; no residual is repaired from season totals alone."
        ),
    }
    (report_dir / "player_game_contact_localization.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    duplicate_rate = (
        player_game_diagnostics["exact_duplicate_row_count"]
        / player_game_diagnostics["raw_observation_count"]
        if player_game_diagnostics["raw_observation_count"]
        else 0.0
    )
    lines = [
        "# Player-game contact localization — 2024 AAA",
        "",
        "## Reusable player-game layer",
        "",
        f"- Assets: {len(player_game_assets)}",
        f"- Raw projected rows: {player_game_diagnostics['raw_observation_count']:,}",
        f"- Exact duplicate rows removed: {player_game_diagnostics['exact_duplicate_row_count']:,} ({duplicate_rate:.2%})",
        f"- Resolved player-games: {player_game_diagnostics['resolved_player_game_count']:,}",
        f"- Conflicting player-games: {player_game_diagnostics['conflicting_player_game_count']:,}",
        f"- Unresolved expected-contact player-games: {player_game_diagnostics['unresolved_expected_contact_player_game_count']:,}",
        "",
        "## Independent aggregate check",
        "",
        f"- Player-game contact total: {season_metrics['player_game_contact_total']:,}",
        f"- Certified season aggregate BIP: {season_metrics['season_aggregate_bip_total']:,}",
        f"- Total difference: {season_metrics['total_difference']:+,}",
        f"- Exact player-league rows: {season_metrics['exact_player_league_count']}/{season_metrics['active_player_league_count']}",
        f"- Absolute discrepancy mass: {season_metrics['absolute_discrepancy_mass']:,}",
        "",
        "## PBP attribution localization",
        "",
        f"- Source PBP contacts: {source_total:,}",
        f"- Player-game expected contacts: {player_game_total:,}",
        f"- Total difference: {source_total - player_game_total:+,}",
        f"- Mismatch games before repair: {before_metrics['mismatch_game_count']:,}",
        f"- Player-game absolute discrepancy mass before: {before_metrics['absolute_discrepancy_mass']:,}",
        f"- Balanced one-for-one (+1/-1) games: {balanced_unit_pair_games:,}",
        f"- Strict source-only reassignments: {repairs.height:,}",
        f"- Strict repair mappings resolve to exactly one contact key: {repair_mapping_is_unique}",
        f"- Mismatch games after strict repair: {after_metrics['mismatch_game_count']:,}",
        f"- Player-game absolute discrepancy mass after: {after_metrics['absolute_discrepancy_mass']:,}",
        f"- Remaining official-exception candidate games: {exception_games.height:,}",
        "",
        "The strict repair does not use season residuals to guess a batter. Remaining games are left for targeted official adjudication.",
    ]
    summary = "\n".join(lines)
    (report_dir / "player_game_contact_localization.md").write_text(
        summary, encoding="utf-8"
    )
    print(summary)

    # Structural failures should stop promotion, while ordinary residuals are the
    # subject of the audit and therefore do not fail the job.
    if contact_status_conflicts.height:
        raise RuntimeError("PBP contact-status conflicts block localization")
    if unresolved_contact_batters.height:
        raise RuntimeError("unresolved PBP contact batter consensus blocks localization")
    if player_game_diagnostics["unresolved_expected_contact_player_game_count"]:
        raise RuntimeError("unresolved player-game expected contacts block localization")
    if not repair_mapping_is_unique:
        raise RuntimeError("strict source-only repair did not map one-to-one to contact keys")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
