#!/usr/bin/env python3
"""Stream public MiLB PBP assets into a compact pitcher contact panel."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl
import requests

from universal_baseball.armstjc_assets import fetch_pbp_asset_inventory
from universal_baseball.armstjc_contacts import (
    CERTIFIED_FALSE_POSITIVE_CONTACTS,
    project_armstjc_contact_observations,
    resolve_armstjc_contact_observations,
)
from universal_baseball.certification import (
    download_file,
    read_quarantined_csv,
    sha256_file,
)
from universal_baseball.pitcher_contact_features import build_pitcher_contact_panel


LEVEL_CODES = {"aaa": -1, "aa": -2, "a+": -3, "a": -4, "rk": -5}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", nargs="+", type=int, required=True)
    parser.add_argument(
        "--work-dir", type=Path,
        default=Path("data/quarantine/pitcher-contact-stream"),
    )
    parser.add_argument(
        "--report-dir", type=Path,
        default=Path("reports/generated/pitcher-contact-panel"),
    )
    parser.add_argument("--keep-raw", action="store_true")
    args = parser.parse_args()
    years = sorted(set(args.years))
    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)

    with requests.Session() as session:
        inventory = fetch_pbp_asset_inventory(session=session)
    assets = [asset for asset in inventory if asset.year in years]
    if not assets:
        raise ValueError(f"no recognized PBP assets for years={years}")

    observations: list[pl.DataFrame] = []
    manifest: list[dict[str, object]] = []
    for number, asset in enumerate(assets, start=1):
        raw_path = args.work_dir / asset.name
        if raw_path.exists() and raw_path.stat().st_size == asset.size_bytes:
            metadata = {
                "file_size_bytes": raw_path.stat().st_size,
                "sha256": sha256_file(raw_path),
            }
        else:
            metadata = download_file(
                asset.browser_download_url, raw_path, timeout_seconds=300
            )
        if int(metadata["file_size_bytes"]) != asset.size_bytes:
            raise RuntimeError(f"download size differs from GitHub metadata: {asset.name}")
        raw = read_quarantined_csv(raw_path)
        # Older PBP snapshots omit exact league ID. The filename level is a
        # certified scope field and is sufficient for this level-adjusted test.
        if "league_id" not in raw.columns:
            raw = raw.with_columns(
                pl.lit(str(LEVEL_CODES[asset.filename_level])).alias("league_id")
            )
            for correction in CERTIFIED_FALSE_POSITIVE_CONTACTS:
                if correction.source_asset != asset.name:
                    continue
                raw = raw.with_columns(
                    pl.when(
                        (pl.col("game_pk") == str(correction.game_pk))
                        & (pl.col("at_bat_number") == str(correction.at_bat_index))
                        & (pl.col("pitch_number") == str(correction.pitch_number))
                    )
                    .then(pl.lit(str(correction.league_id)))
                    .otherwise(pl.col("league_id"))
                    .alias("league_id")
                )
        projected = project_armstjc_contact_observations(
            raw, source_asset=asset.name, season=asset.year, game_type="R"
        ).with_columns(
            pl.lit(LEVEL_CODES[asset.filename_level]).alias("league_id")
        )
        # Retain only positive contact evidence. Prior source certification found
        # exact terminal reconciliation; the manifest records this compact-build
        # boundary instead of pretending the full raw archive remains present.
        positive = projected.filter(pl.col("source_is_in_play") == True)  # noqa: E712
        observations.append(positive)
        manifest.append(
            {
                "asset_id": asset.asset_id,
                "asset_name": asset.name,
                "year": asset.year,
                "level": asset.filename_level,
                "github_size_bytes": asset.size_bytes,
                "downloaded_size_bytes": metadata["file_size_bytes"],
                "sha256": metadata["sha256"],
                "raw_rows": raw.height,
                "positive_contact_observations": positive.height,
            }
        )
        if not args.keep_raw:
            raw_path.unlink()
        print(f"[{number}/{len(assets)}] {asset.name}: {positive.height:,} contacts")

    combined = pl.concat(observations, how="vertical_relaxed")
    resolved = resolve_armstjc_contact_observations(combined, contacts_only=True)
    level_by_code = {code: level for level, code in LEVEL_CODES.items()}
    resolved = resolved.with_columns(
        pl.col("league_id").replace_strict(level_by_code).alias("source_level")
    )
    panel = build_pitcher_contact_panel(resolved)
    table_dir = args.report_dir / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    panel_path = table_dir / "pitcher_contact_panel.parquet"
    panel.write_parquet(panel_path)
    payload = {
        "report_schema_version": 1,
        "status": "research_source_ready_not_model_promoted",
        "years": years,
        "source_family": "armstjc/milb-data-repository PBP release",
        "source_license": "MIT",
        "build_policy": "stream_each_asset_hash_then_delete_raw_unless_keep_raw",
        "resolution_policy": "positive_contact_non_null_field_consensus",
        "asset_count": len(assets),
        "assets": manifest,
        "raw_download_bytes": sum(int(row["downloaded_size_bytes"]) for row in manifest),
        "positive_contact_observations": combined.height,
        "resolved_contacts": resolved.height,
        "panel_rows": panel.height,
        "distinct_pitchers": panel.get_column("player_id").n_unique(),
        "output": panel_path.as_posix(),
        "model_effect": "none",
    }
    (args.report_dir / "report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: payload[key] for key in (
        "asset_count", "raw_download_bytes", "resolved_contacts", "panel_rows",
        "distinct_pitchers", "output")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
