#!/usr/bin/env python
"""Reconcile full-season reusable PBP contact attribution to season aggregates.

Discovery gate: completed 2024 Triple-A only. Every available 2024 AAA PBP
snapshot is inventoried dynamically, regular-season 2024 rows are projected to a
small natural-key/contact view, and overlapping snapshots are resolved by
non-null field consensus without using filename period as chronology.

The independent target is the certified armstjc 2024 AAA season-player batting
aggregate `ballsInPlay` field. ADR 018 established that this is a broad contact
count (approximately AB-SO+SF+SH), which aligns with structured in-play contact
better than the usual BABIP denominator.

This audit does not repair any player. It asks whether the known pinch-runner ID
mutation is sparse enough that official PBP can be exception-only.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.armstjc_assets import fetch_pbp_asset_inventory
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.season_stats import standardize_armstjc_season_stats


SEASON = 2024
LEVEL = "aaa"
BASE_RELEASE_URL = "https://github.com/armstjc/milb-data-repository/releases/download"
SEASON_ASSET = "2024_aaa_season_batting_stats.csv"
SEASON_TAG = "season_player_batting"
IN_PLAY_CODES = ("D", "E", "X")
KEY = ["game_pk", "at_bat_index", "pitch_number"]


def _int_expr(column: str, alias: str | None = None) -> pl.Expr:
    numeric = pl.col(column).cast(pl.Float64, strict=False)
    return (
        pl.when(numeric.is_not_null() & (numeric == numeric.floor()))
        .then(numeric.cast(pl.Int64, strict=False))
        .otherwise(None)
        .alias(alias or column)
    )


def _nonblank(column: str) -> pl.Expr:
    return pl.col(column).is_not_null() & (pl.col(column).cast(pl.String).str.strip_chars() != "")


def _project_asset(frame: pl.DataFrame, asset_name: str) -> pl.DataFrame:
    required = {
        "game_pk", "at_bat_number", "pitch_number", "batter", "league_id",
        "game_date", "game_type", "type", "bb_type", "hit_location", "hc_x", "hc_y",
        "hit_distance_sc", "launch_speed", "launch_angle",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{asset_name} missing contact reconciliation fields: {missing}")

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
    projected = frame.select(
        _int_expr("game_pk"),
        _int_expr("at_bat_number", "at_bat_index"),
        _int_expr("pitch_number"),
        _int_expr("batter", "source_batter_id"),
        _int_expr("league_id"),
        pl.col("game_date").cast(pl.String),
        pl.col("game_type").cast(pl.String),
        contact_evidence.alias("source_is_in_play"),
        pl.lit(asset_name).alias("source_asset"),
    ).drop_nulls(KEY)

    return projected.filter(
        (pl.col("game_type") == "R")
        & pl.col("game_date").str.starts_with(f"{SEASON}-")
    )


def _resolve_pitch_keys(observations: pl.DataFrame) -> pl.DataFrame:
    if observations.is_empty():
        raise RuntimeError("no regular-season source observations after projection")

    # Consensus deliberately ignores filename order. A field resolves only when
    # all non-null observations across all snapshots agree.
    return (
        observations.group_by(KEY)
        .agg(
            pl.col("source_asset").n_unique().alias("source_snapshot_count"),
            pl.col("source_asset").unique().sort().alias("source_assets"),
            pl.col("league_id").drop_nulls().n_unique().alias("league_value_count"),
            pl.when(pl.col("league_id").drop_nulls().n_unique() <= 1)
            .then(pl.col("league_id").drop_nulls().first())
            .otherwise(None)
            .alias("league_id"),
            pl.col("source_batter_id").drop_nulls().n_unique().alias("batter_value_count"),
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
        .sort(KEY)
    )


def _aggregate_target(frame: pl.DataFrame) -> pl.DataFrame:
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
        .agg(pl.col("batting_balls_in_play").sum().alias("aggregate_bip"))
    )


def _league_summary(
    league_id: int,
    contacts: pl.DataFrame,
    target: pl.DataFrame,
    comparison: pl.DataFrame,
) -> dict[str, Any]:
    league_contacts = contacts.filter(pl.col("league_id") == league_id)
    league_target = target.filter(pl.col("league_id") == league_id)
    league_comp = comparison.filter(pl.col("league_id") == league_id)

    source_total = int(league_contacts.height)
    assigned_total = int(
        league_contacts.filter(pl.col("source_batter_id").is_not_null()).height
    )
    unresolved_batter = source_total - assigned_total
    aggregate_total = int(league_target.get_column("aggregate_bip").sum() or 0)

    positive = int(
        league_comp.select(
            pl.when(pl.col("difference") > 0).then(pl.col("difference")).otherwise(0).sum()
        ).item()
        or 0
    )
    negative = int(
        league_comp.select(
            pl.when(pl.col("difference") < 0).then(-pl.col("difference")).otherwise(0).sum()
        ).item()
        or 0
    )
    nonzero = league_comp.filter(pl.col("difference") != 0)
    active = league_comp.filter(
        (pl.col("source_contact_count") > 0) | (pl.col("aggregate_bip") > 0)
    )
    abs_error = int(active.select(pl.col("difference").abs().sum()).item() or 0)

    return {
        "league_id": league_id,
        "source_contact_key_count": source_total,
        "source_assigned_contact_count": assigned_total,
        "source_unresolved_batter_contact_count": unresolved_batter,
        "aggregate_bip_count": aggregate_total,
        "source_minus_aggregate_total": source_total - aggregate_total,
        "assigned_source_minus_aggregate_total": assigned_total - aggregate_total,
        "active_player_count": active.height,
        "exact_active_player_count": active.filter(pl.col("difference") == 0).height,
        "nonzero_player_count": nonzero.height,
        "player_exact_rate": (
            active.filter(pl.col("difference") == 0).height / active.height if active.height else None
        ),
        "positive_source_residual_mass": positive,
        "negative_source_residual_mass": negative,
        "residual_mass_imbalance": positive - negative,
        "player_absolute_discrepancy_mass": abs_error,
        "player_absolute_discrepancy_rate_vs_aggregate_bip": (
            abs_error / aggregate_total if aggregate_total else None
        ),
    }


def main() -> int:
    work_dir = Path("data/quarantine/full-season-contact-identity-reconciliation")
    report_dir = Path("reports/generated/full-season-contact-identity-reconciliation")
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    inventory = fetch_pbp_asset_inventory()
    assets = [
        asset for asset in inventory
        if asset.year == SEASON and asset.filename_level == LEVEL
    ]
    if not assets:
        raise RuntimeError(f"no {SEASON} {LEVEL} PBP assets in release inventory")

    projections: list[pl.DataFrame] = []
    asset_records: list[dict[str, Any]] = []
    for asset in assets:
        path = work_dir / asset.name
        metadata = download_file(asset.browser_download_url, path, timeout_seconds=300)
        frame = read_quarantined_csv(path)
        projection = _project_asset(frame, asset.name)
        projections.append(projection)
        asset_records.append(
            {
                "asset": asset.name,
                "filename_period": asset.filename_period,
                "size_bytes": asset.size_bytes,
                "sha256": metadata["sha256"],
                "regular_season_2024_source_rows": projection.height,
                "regular_season_2024_game_count": projection.get_column("game_pk").n_unique(),
            }
        )
        # Release the full-width CSV before reading the next asset.
        del frame

    observations = pl.concat(projections, how="vertical_relaxed")
    resolved = _resolve_pitch_keys(observations)
    contact_status_conflicts = resolved.filter(pl.col("in_play_value_count") > 1)
    contacts = resolved.filter(pl.col("source_is_in_play") == True)  # noqa: E712

    season_path = work_dir / SEASON_ASSET
    season_meta = download_file(
        f"{BASE_RELEASE_URL}/{SEASON_TAG}/{SEASON_ASSET}",
        season_path,
        timeout_seconds=240,
    )
    season_raw = read_quarantined_csv(season_path)
    target = _aggregate_target(season_raw)

    source_by_player = (
        contacts.filter(
            pl.col("league_id").is_not_null() & pl.col("source_batter_id").is_not_null()
        )
        .group_by(["league_id", "source_batter_id"])
        .len(name="source_contact_count")
        .rename({"source_batter_id": "player_id"})
    )
    comparison = (
        source_by_player.join(target, on=["league_id", "player_id"], how="full", coalesce=True)
        .with_columns(
            pl.col("source_contact_count").fill_null(0),
            pl.col("aggregate_bip").fill_null(0),
        )
        .with_columns(
            (pl.col("source_contact_count") - pl.col("aggregate_bip")).alias("difference")
        )
        .sort(["league_id", "difference", "player_id"], descending=[False, True, False])
    )

    league_ids = sorted(
        set(int(value) for value in target.get_column("league_id").drop_nulls().unique())
        | set(int(value) for value in contacts.get_column("league_id").drop_nulls().unique())
    )
    league_summaries = [
        _league_summary(league_id, contacts, target, comparison)
        for league_id in league_ids
    ]

    total_contact_keys = contacts.height
    total_aggregate = int(target.get_column("aggregate_bip").sum() or 0)
    unresolved_batter_contacts = contacts.filter(pl.col("source_batter_id").is_null()).height
    unresolved_league_contacts = contacts.filter(pl.col("league_id").is_null()).height
    active = comparison.filter(
        (pl.col("source_contact_count") > 0) | (pl.col("aggregate_bip") > 0)
    )
    nonzero = active.filter(pl.col("difference") != 0)
    positive_mass = int(
        active.select(
            pl.when(pl.col("difference") > 0).then(pl.col("difference")).otherwise(0).sum()
        ).item()
        or 0
    )
    negative_mass = int(
        active.select(
            pl.when(pl.col("difference") < 0).then(-pl.col("difference")).otherwise(0).sum()
        ).item()
        or 0
    )
    abs_mass = positive_mass + negative_mass

    discrepancy_distribution = Counter(int(value) for value in nonzero.get_column("difference").to_list())
    top_discrepancies = (
        nonzero.with_columns(pl.col("difference").abs().alias("absolute_difference"))
        .sort(["absolute_difference", "league_id", "player_id"], descending=[True, False, False])
        .head(100)
        .drop("absolute_difference")
        .to_dicts()
    )

    payload = {
        "report_schema_version": 1,
        "status": "full_season_contact_identity_reconciliation_discovery",
        "season": SEASON,
        "level": LEVEL,
        "game_type": "R",
        "natural_pitch_key": KEY,
        "resolution_policy": "non_null_field_consensus_without_snapshot_precedence",
        "assets": asset_records,
        "season_aggregate": {"asset": SEASON_ASSET, "sha256": season_meta["sha256"]},
        "raw_projected_observation_count": observations.height,
        "resolved_pitch_key_count": resolved.height,
        "contact_status_conflict_key_count": contact_status_conflicts.height,
        "resolved_contact_key_count": total_contact_keys,
        "unresolved_contact_batter_count": unresolved_batter_contacts,
        "unresolved_contact_league_count": unresolved_league_contacts,
        "aggregate_bip_count": total_aggregate,
        "source_contact_minus_aggregate_bip": total_contact_keys - total_aggregate,
        "active_player_league_count": active.height,
        "exact_active_player_league_count": active.filter(pl.col("difference") == 0).height,
        "nonzero_player_league_count": nonzero.height,
        "player_exact_rate": (
            active.filter(pl.col("difference") == 0).height / active.height if active.height else None
        ),
        "positive_source_residual_mass": positive_mass,
        "negative_source_residual_mass": negative_mass,
        "residual_mass_imbalance": positive_mass - negative_mass,
        "player_absolute_discrepancy_mass": abs_mass,
        "player_absolute_discrepancy_rate_vs_aggregate_bip": (
            abs_mass / total_aggregate if total_aggregate else None
        ),
        "discrepancy_distribution": dict(sorted(discrepancy_distribution.items())),
        "league_summaries": league_summaries,
        "top_discrepancies": top_discrepancies,
        "interpretation_guardrail": (
            "This is a discovery gate, not an automatic repair. Exact/near-exact league contact "
            "totals plus sparse balanced player residuals would support targeted official identity "
            "resolution. Broad league-total gaps would instead indicate source coverage/semantic "
            "problems and would block an exception-only participant strategy."
        ),
    }
    (report_dir / "full_season_contact_identity_reconciliation.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    lines = [
        "# Full-season source contact identity reconciliation — 2024 AAA",
        "",
        f"- PBP snapshot assets: {len(assets)}",
        f"- Raw projected source observations: {observations.height:,}",
        f"- Resolved natural pitch keys: {resolved.height:,}",
        f"- Contact-status conflict keys: {contact_status_conflicts.height:,}",
        f"- Resolved source contact keys: {total_contact_keys:,}",
        f"- Certified aggregate ballsInPlay: {total_aggregate:,}",
        f"- Source contact minus aggregate BIP: {total_contact_keys - total_aggregate:+,}",
        f"- Contacts with unresolved batter consensus: {unresolved_batter_contacts:,}",
        f"- Active player-league rows: {active.height:,}",
        f"- Exact player-league rows: {active.filter(pl.col('difference') == 0).height:,} ({payload['player_exact_rate']:.2%})",
        f"- Nonzero player-league rows: {nonzero.height:,}",
        f"- Positive source residual mass: {positive_mass:,}",
        f"- Negative source residual mass: {negative_mass:,}",
        f"- Residual mass imbalance: {positive_mass - negative_mass:+,}",
        f"- Absolute player discrepancy mass / aggregate BIP: {abs_mass:,} / {total_aggregate:,} ({payload['player_absolute_discrepancy_rate_vs_aggregate_bip']:.3%})",
        "",
        "## By actual AAA league",
        "",
    ]
    for row in league_summaries:
        lines.append(
            f"- league {row['league_id']}: source={row['source_contact_key_count']:,}, "
            f"aggregate={row['aggregate_bip_count']:,}, total_delta={row['source_minus_aggregate_total']:+,}, "
            f"exact_players={row['exact_active_player_count']}/{row['active_player_count']}, "
            f"+mass={row['positive_source_residual_mass']}, -mass={row['negative_source_residual_mass']}"
        )
    lines.extend(
        [
            "",
            f"Discrepancy distribution (source - aggregate): `{dict(sorted(discrepancy_distribution.items()))}`",
            "",
        ]
    )
    summary = "\n".join(lines)
    (report_dir / "full_season_contact_identity_reconciliation.md").write_text(
        summary, encoding="utf-8"
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
