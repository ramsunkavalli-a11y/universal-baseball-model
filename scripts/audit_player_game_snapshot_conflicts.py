#!/usr/bin/env python
"""Diagnose conflicting 2024 AAA player-game observations without PBP downloads.

The localization gate found 42 player-games whose current release assets contain
more than one distinct boxscore state.  This script tests a narrow hypothesis:
they are partial/final snapshots of the same game.  A later-complete observation
is only identified when its cumulative batting vector (PA, AB, SO, SF, SH)
component-wise dominates every other non-null observation for that player-game.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.player_game_stats import (
    PLAYER_GAME_KEY,
    fetch_player_game_asset_inventory,
    project_player_game_batting,
)
from universal_baseball.season_stats import standardize_armstjc_season_stats


SEASON = 2024
LEVEL = "aaa"
GAME_TYPE = "R"
CUMULATIVE_FIELDS = ["batting_PA", "batting_AB", "batting_SO", "batting_SF", "batting_SH"]
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


def _dominates(candidate: dict[str, Any], other: dict[str, Any]) -> bool:
    """Return true when candidate is no earlier on every cumulative component."""

    for field in CUMULATIVE_FIELDS:
        left = candidate[field]
        right = other[field]
        if right is None:
            continue
        if left is None or int(left) < int(right):
            return False
    return True


def _select_complete_observations(
    exact: pl.DataFrame,
) -> tuple[pl.DataFrame, list[dict[str, Any]]]:
    selected: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []

    for group in exact.partition_by(PLAYER_GAME_KEY, maintain_order=True):
        rows = group.to_dicts()
        # Collapse observations that differ only in source asset provenance.
        vectors: dict[tuple[Any, ...], dict[str, Any]] = {}
        for row in rows:
            vector = tuple(row[field] for field in CUMULATIVE_FIELDS)
            vectors.setdefault(vector, row)
        distinct = list(vectors.values())
        if len(distinct) == 1:
            selected.append(distinct[0])
            continue

        dominators = [
            row
            for row in distinct
            if all(_dominates(row, other) for other in distinct)
        ]
        resolved = len(dominators) == 1
        if resolved:
            selected.append(dominators[0])

        diagnostics.append(
            {
                "game_id": int(rows[0]["game_id"]),
                "player_id": int(rows[0]["player_id"]),
                "distinct_vector_count": len(distinct),
                "unique_componentwise_dominator": resolved,
                "selected_source_asset": (
                    str(dominators[0]["source_asset"]) if resolved else None
                ),
                "selected_expected_contact_count": (
                    int(dominators[0]["expected_contact_count"])
                    if resolved and dominators[0]["expected_contact_count"] is not None
                    else None
                ),
            }
        )

    selected_frame = pl.DataFrame(selected, schema=exact.schema) if selected else exact.head(0)
    return selected_frame, diagnostics


def _season_target(frame: pl.DataFrame) -> pl.DataFrame:
    standardized, _ = standardize_armstjc_season_stats(frame, "batting")
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


def main() -> int:
    work_dir = Path("data/quarantine/player-game-snapshot-conflicts")
    report_dir = Path("reports/generated/player-game-snapshot-conflicts")
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    assets = [
        asset
        for asset in fetch_player_game_asset_inventory()
        if asset.year == SEASON and asset.filename_level == LEVEL
    ]
    projections: list[pl.DataFrame] = []
    asset_records: list[dict[str, Any]] = []
    for asset in assets:
        path = work_dir / asset.name
        metadata = download_file(asset.browser_download_url, path, timeout_seconds=240)
        raw = read_quarantined_csv(path)
        projection = project_player_game_batting(
            raw, source_asset=asset.name, season=SEASON, game_type=GAME_TYPE
        )
        projections.append(projection)
        asset_records.append(
            {
                "asset": asset.name,
                "sha256": metadata["sha256"],
                "created_at_utc": asset.created_at_utc.isoformat(),
                "updated_at_utc": asset.updated_at_utc.isoformat(),
                "row_count": projection.height,
                "game_count": projection.get_column("game_id").n_unique(),
            }
        )

    observations = pl.concat(projections, how="vertical_relaxed")
    exact = observations.unique(maintain_order=True)

    conflict_keys = (
        exact.group_by(PLAYER_GAME_KEY)
        .agg(
            pl.struct(CUMULATIVE_FIELDS).n_unique().alias("batting_vector_count"),
            pl.col("expected_contact_count")
            .drop_nulls()
            .n_unique()
            .alias("expected_contact_value_count"),
            pl.col("source_asset").n_unique().alias("source_asset_count"),
        )
        .filter(pl.col("batting_vector_count") > 1)
        .sort(PLAYER_GAME_KEY)
    )
    conflict_observations = (
        exact.join(conflict_keys.select(PLAYER_GAME_KEY), on=PLAYER_GAME_KEY, how="inner")
        .sort(["game_id", "player_id", "source_asset"])
    )
    conflict_observations.write_csv(report_dir / "conflicting_player_game_observations.csv")

    selected, selection_diagnostics = _select_complete_observations(exact)
    diagnostic_frame = pl.DataFrame(selection_diagnostics)
    if diagnostic_frame.height:
        diagnostic_frame.write_csv(report_dir / "conflict_resolution_diagnostics.csv")
    unresolved = [row for row in selection_diagnostics if not row["unique_componentwise_dominator"]]

    season_path = work_dir / SEASON_ASSET
    season_meta = download_file(
        f"{BASE_RELEASE_URL}/{SEASON_TAG}/{SEASON_ASSET}",
        season_path,
        timeout_seconds=240,
    )
    season_raw = read_quarantined_csv(season_path)
    season_target = _season_target(season_raw)

    selected_by_player = (
        selected.filter(
            pl.col("expected_contact_count").is_not_null()
            & pl.col("league_id").is_not_null()
        )
        .group_by(["league_id", "player_id"])
        .agg(pl.col("expected_contact_count").sum().alias("player_game_bip"))
    )
    season_comparison = (
        selected_by_player.join(
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
    season_comparison.filter(pl.col("difference") != 0).write_csv(
        report_dir / "selected_player_game_vs_season_residuals.csv"
    )

    conflict_games = sorted(
        int(value) for value in conflict_keys.get_column("game_id").unique().to_list()
    )
    selected_total = int(selected.get_column("expected_contact_count").drop_nulls().sum() or 0)
    season_total = int(season_target.get_column("season_aggregate_bip").sum() or 0)
    abs_mass = int(season_comparison.select(pl.col("difference").abs().sum()).item() or 0)
    nonzero_season = season_comparison.filter(pl.col("difference") != 0)

    payload = {
        "report_schema_version": 1,
        "season": SEASON,
        "level": LEVEL,
        "game_type": GAME_TYPE,
        "assets": asset_records,
        "raw_observation_count": observations.height,
        "exact_unique_observation_count": exact.height,
        "exact_duplicate_row_count": observations.height - exact.height,
        "conflicting_player_game_count": conflict_keys.height,
        "conflict_game_count": len(conflict_games),
        "conflict_game_ids": conflict_games,
        "unique_componentwise_dominator_count": sum(
            1 for row in selection_diagnostics if row["unique_componentwise_dominator"]
        ),
        "unresolved_componentwise_conflict_count": len(unresolved),
        "selected_player_game_count": selected.height,
        "selected_contact_total": selected_total,
        "season_aggregate_bip_total": season_total,
        "selected_minus_season_total": selected_total - season_total,
        "season_player_league_nonzero_residual_count": nonzero_season.height,
        "season_player_league_absolute_discrepancy_mass": abs_mass,
        "season_aggregate": {"asset": SEASON_ASSET, "sha256": season_meta["sha256"]},
        "interpretation_guardrail": (
            "Componentwise dominance is admissible only for cumulative within-game batting "
            "statistics. If conflicts are not uniquely dominated, no snapshot is selected."
        ),
    }
    (report_dir / "player_game_snapshot_conflicts.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# Player-game snapshot conflict diagnostic — 2024 AAA",
        "",
        f"- Raw observations: {observations.height:,}",
        f"- Exact duplicates removed: {observations.height - exact.height:,}",
        f"- Conflicting player-games: {conflict_keys.height:,}",
        f"- Games containing conflicts: {len(conflict_games):,} — {conflict_games}",
        f"- Conflicts with a unique component-wise complete observation: {payload['unique_componentwise_dominator_count']:,}/{conflict_keys.height:,}",
        f"- Unresolved conflicts under that rule: {len(unresolved):,}",
        f"- Selected player-game contact total: {selected_total:,}",
        f"- Certified season aggregate BIP: {season_total:,}",
        f"- Selected minus season total: {selected_total - season_total:+,}",
        f"- Remaining player-league residual rows: {nonzero_season.height:,}",
        f"- Remaining player-league absolute discrepancy mass: {abs_mass:,}",
    ]
    summary = "\n".join(lines)
    (report_dir / "player_game_snapshot_conflicts.md").write_text(summary, encoding="utf-8")
    print(summary)

    if unresolved:
        raise RuntimeError(
            f"{len(unresolved)} player-game conflicts lack a unique componentwise-complete snapshot"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
