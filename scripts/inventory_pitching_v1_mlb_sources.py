#!/usr/bin/env python
"""Capture the exact pre-2025 official MLB source inventory for Pitching v1."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.mlb_season_stats import fetch_mlb_pitching_backbone
from universal_baseball.pitching_performance import build_pitching_performance
from universal_baseball.pitching_source_inventory import (
    FROZEN_2021_2024_MLB_PITCHING_RESPONSE_SHA256,
    FROZEN_2024_MLB_PITCHING_BF,
    PITCHING_DEVELOPMENT_SEASONS,
    validate_frozen_mlb_pitching_response_sha,
)


REPORT_DIR = Path("reports/generated/pitching-v1-mlb-source-inventory")


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    summaries: list[pl.DataFrame] = []
    profiles: list[pl.DataFrame] = []
    capture_rows: list[dict[str, object]] = []
    seasonal_rows: list[dict[str, object]] = []
    observed_capture_keys: set[tuple[int, int, int]] = set()

    for season in PITCHING_DEVELOPMENT_SEASONS:
        backbone, captures = fetch_mlb_pitching_backbone(season)
        if backbone.is_empty():
            raise RuntimeError(f"official MLB pitching backbone is empty for {season}")

        provenance_rows: list[dict[str, object]] = []
        for capture in captures:
            key = (capture.season, capture.league_id, capture.offset)
            validate_frozen_mlb_pitching_response_sha(
                season=capture.season,
                league_id=capture.league_id,
                offset=capture.offset,
                observed_sha256=capture.response_sha256,
            )
            if key in observed_capture_keys:
                raise RuntimeError(f"duplicate official MLB pitching capture: {key}")
            observed_capture_keys.add(key)
            provenance_rows.append(
                {
                    "season": capture.season,
                    "league_id": capture.league_id,
                    "source_response_sha256": capture.response_sha256,
                }
            )
            capture_rows.append(
                {
                    "season": capture.season,
                    "league_id": capture.league_id,
                    "offset": capture.offset,
                    "requested_limit": capture.requested_limit,
                    "returned_split_count": capture.returned_split_count,
                    "total_splits": capture.total_splits,
                    "response_byte_count": len(capture.response_bytes),
                    "response_sha256": capture.response_sha256,
                }
            )

        provenance = pl.DataFrame(provenance_rows)
        duplicate_provenance = provenance.group_by(["season", "league_id"]).len().filter(
            pl.col("len") != 1
        )
        if not duplicate_provenance.is_empty():
            raise RuntimeError("official MLB pitching league-season used multiple pages")

        performance = build_pitching_performance(backbone)
        summaries.append(
            performance.summary.join(
                provenance,
                on=["season", "league_id"],
                how="left",
                validate="m:1",
            ).with_columns(pl.lit("MLB Stats API").alias("source_family"))
        )
        profiles.append(
            performance.profile.join(
                provenance,
                on=["season", "league_id"],
                how="left",
                validate="m:1",
            ).with_columns(pl.lit("MLB Stats API").alias("source_family"))
        )
        seasonal_rows.append(
            {
                "season": season,
                "summary_row_count": performance.summary.height,
                "profile_row_count": performance.profile.height,
                "distinct_player_count": performance.summary.get_column(
                    "player_id"
                ).n_unique(),
                "total_batters_faced": performance.metrics["total_batters_faced"],
            }
        )

    expected_capture_keys = set(FROZEN_2021_2024_MLB_PITCHING_RESPONSE_SHA256)
    if observed_capture_keys != expected_capture_keys:
        raise RuntimeError(
            "official MLB pitching capture keys did not match the frozen inventory"
        )

    summary = pl.concat(summaries, how="vertical_relaxed").sort(
        ["season", "league_id", "player_id"]
    )
    profile = pl.concat(profiles, how="vertical_relaxed").sort(
        ["season", "league_id", "player_id", "pitching_outcome_bin"]
    )
    duplicate_summary = summary.group_by(["season", "league_id", "player_id"]).len().filter(
        pl.col("len") != 1
    )
    if not duplicate_summary.is_empty():
        raise RuntimeError("combined official MLB pitching summary violates canonical grain")
    duplicate_profile = profile.group_by(
        ["season", "league_id", "player_id", "pitching_outcome_bin"]
    ).len().filter(pl.col("len") != 1)
    if not duplicate_profile.is_empty():
        raise RuntimeError("combined official MLB pitching profile violates canonical grain")

    observed_2024_bf = int(
        summary.filter(pl.col("season") == 2024)
        .get_column("pitching_batters_faced")
        .sum()
    )
    if observed_2024_bf != FROZEN_2024_MLB_PITCHING_BF:
        raise RuntimeError(
            f"official 2024 MLB pitching BF drift: expected "
            f"{FROZEN_2024_MLB_PITCHING_BF}, observed {observed_2024_bf}"
        )

    summary_path = REPORT_DIR / "pitching_v1_mlb_performance_summary_2021_2024.parquet"
    profile_path = REPORT_DIR / "pitching_v1_mlb_performance_profile_2021_2024.parquet"
    summary.write_parquet(summary_path)
    profile.write_parquet(profile_path)

    payload = {
        "report_schema_version": 1,
        "status": "pitching_v1_pre_outcome_mlb_source_inventory",
        "seasons": list(PITCHING_DEVELOPMENT_SEASONS),
        "confirmation_2025_accessed": False,
        "source_family": "official MLB Stats API bulk season pitching",
        "raw_source_storage": "response_bytes_not_persisted_or_uploaded",
        "capture_count": len(capture_rows),
        "captures": capture_rows,
        "seasonal": seasonal_rows,
        "combined": {
            "summary_row_count": summary.height,
            "profile_row_count": profile.height,
            "distinct_player_count": summary.get_column("player_id").n_unique(),
            "distinct_actual_league_count": summary.get_column("league_id").n_unique(),
            "total_batters_faced": int(summary.get_column("pitching_batters_faced").sum()),
            "summary_grain_unique": True,
            "profile_grain_unique": True,
            "all_eight_frozen_response_hashes_reproduced": True,
            "official_2024_bf_anchor_reproduced": observed_2024_bf,
        },
        "outputs": {
            "summary_parquet": summary_path.as_posix(),
            "profile_parquet": profile_path.as_posix(),
        },
    }
    result_path = REPORT_DIR / "pitching-v1-mlb-source-inventory.json"
    result_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "capture_count": payload["capture_count"],
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
