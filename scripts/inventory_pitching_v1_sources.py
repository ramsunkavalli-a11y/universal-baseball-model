#!/usr/bin/env python
"""Capture the exact pre-2025 MiLB source inventory for Pitching v1.

Raw third-party CSV files remain in the ignored quarantine directory.  The
workflow artifact contains only a provenance manifest and derived canonical BF
Performance tables.
"""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

import polars as pl
import requests

from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.pitching_performance import build_pitching_performance
from universal_baseball.pitching_source_inventory import (
    PITCHING_DEVELOPMENT_SEASONS,
    expected_pitching_source_specs,
    validate_frozen_pitching_sha,
)
from universal_baseball.season_stat_assets import (
    fetch_season_stat_asset_inventory,
    select_season_stat_asset,
)
from universal_baseball.season_stats import standardize_armstjc_season_stats


RAW_DIR = Path("data/quarantine/pitching-v1-source-inventory")
REPORT_DIR = Path("reports/generated/pitching-v1-source-inventory")


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    try:
        inventory = fetch_season_stat_asset_inventory("pitching", session=session)
    finally:
        session.close()

    manifest_rows: list[dict[str, object]] = []
    summaries: list[pl.DataFrame] = []
    profiles: list[pl.DataFrame] = []
    for spec in expected_pitching_source_specs():
        asset = select_season_stat_asset(
            inventory,
            year=spec.season,
            filename_level=spec.filename_level,
            kind="pitching",
            require_nonempty=True,
        )
        if asset.name != spec.asset_name:
            raise RuntimeError(
                f"selected pitching source name mismatch: expected {spec.asset_name}, "
                f"observed {asset.name}"
            )

        raw_path = RAW_DIR / asset.name
        downloaded = download_file(
            asset.browser_download_url,
            raw_path,
            timeout_seconds=180,
        )
        observed_sha = str(downloaded["sha256"])
        validate_frozen_pitching_sha(asset.name, observed_sha)

        raw = read_quarantined_csv(raw_path)
        if raw.is_empty():
            raise RuntimeError(f"pitching source asset is empty: {asset.name}")
        standardized, normalization = standardize_armstjc_season_stats(raw, "pitching")
        performance = build_pitching_performance(standardized)

        summaries.append(
            performance.summary.with_columns(
                pl.lit(asset.name).alias("source_asset_name"),
                pl.lit(observed_sha).alias("source_sha256"),
                pl.lit(asset.asset_id).cast(pl.Int64).alias("source_asset_id"),
                pl.lit(spec.filename_level).alias("source_filename_level"),
            )
        )
        profiles.append(
            performance.profile.with_columns(
                pl.lit(asset.name).alias("source_asset_name"),
                pl.lit(observed_sha).alias("source_sha256"),
                pl.lit(asset.asset_id).cast(pl.Int64).alias("source_asset_id"),
                pl.lit(spec.filename_level).alias("source_filename_level"),
            )
        )
        manifest_rows.append(
            {
                "spec": asdict(spec),
                "asset_id": asset.asset_id,
                "asset_name": asset.name,
                "asset_size_bytes": asset.size_bytes,
                "asset_created_at_utc": asset.created_at_utc.isoformat(),
                "asset_updated_at_utc": asset.updated_at_utc.isoformat(),
                "browser_download_url": asset.browser_download_url,
                "retrieved_at_utc": downloaded["retrieved_at_utc"],
                "resolved_url": downloaded["resolved_url"],
                "downloaded_size_bytes": downloaded["file_size_bytes"],
                "source_sha256": observed_sha,
                "raw_row_count": raw.height,
                "raw_column_count": raw.width,
                "raw_columns": raw.columns,
                "normalization": normalization,
                "performance_metrics": performance.metrics,
                "frozen_2024_hash_reproduced": spec.season == 2024,
            }
        )

    summary = pl.concat(summaries, how="diagonal_relaxed").sort(
        ["season", "league_id", "player_id", "source_asset_name"]
    )
    profile = pl.concat(profiles, how="diagonal_relaxed").sort(
        ["season", "league_id", "player_id", "pitching_outcome_bin"]
    )

    duplicate_summary = summary.group_by(
        ["season", "league_id", "player_id"]
    ).len().filter(pl.col("len") != 1)
    if not duplicate_summary.is_empty():
        raise RuntimeError(
            "combined pitching source inventory overlaps player/league/season grain"
        )
    duplicate_profile = profile.group_by(
        ["season", "league_id", "player_id", "pitching_outcome_bin"]
    ).len().filter(pl.col("len") != 1)
    if not duplicate_profile.is_empty():
        raise RuntimeError("combined pitching source profile violates canonical grain")

    summary_path = REPORT_DIR / "pitching_v1_milb_performance_summary_2021_2024.parquet"
    profile_path = REPORT_DIR / "pitching_v1_milb_performance_profile_2021_2024.parquet"
    summary.write_parquet(summary_path)
    profile.write_parquet(profile_path)

    payload = {
        "report_schema_version": 1,
        "status": "pitching_v1_pre_outcome_milb_source_inventory",
        "seasons": list(PITCHING_DEVELOPMENT_SEASONS),
        "confirmation_2025_accessed": False,
        "source_family": "armstjc/milb-data-repository season_player_pitching",
        "source_license": "MIT",
        "raw_source_storage": "private_ignored_quarantine_not_uploaded",
        "asset_count": len(manifest_rows),
        "assets": manifest_rows,
        "combined": {
            "summary_row_count": summary.height,
            "profile_row_count": profile.height,
            "distinct_player_count": summary.get_column("player_id").n_unique(),
            "distinct_actual_league_count": summary.get_column("league_id").n_unique(),
            "total_batters_faced": int(summary.get_column("pitching_batters_faced").sum()),
            "summary_grain_unique": True,
            "profile_grain_unique": True,
            "all_twenty_frozen_source_hashes_reproduced": True,
            "all_five_frozen_2024_hashes_reproduced": True,
        },
        "outputs": {
            "summary_parquet": summary_path.as_posix(),
            "profile_parquet": profile_path.as_posix(),
        },
        "interpretation": (
            "The 2021-2023 assets are frozen here as retrospective event-cutoff "
            "source snapshots. They are not claimed to be historical vintages. "
            "The 2024 assets must reproduce the earlier independently certified bytes."
        ),
    }
    result_path = REPORT_DIR / "pitching-v1-source-inventory.json"
    result_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "asset_count": payload["asset_count"],
                "combined": payload["combined"],
                "result": result_path.as_posix(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
