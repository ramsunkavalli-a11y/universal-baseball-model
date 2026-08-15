#!/usr/bin/env python
"""Inventory armstjc PBP assets and audit cross-asset ordering metadata."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any

from universal_baseball.armstjc_assets import fetch_pbp_asset_inventory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/armstjc-asset-inventory"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    assets = fetch_pbp_asset_inventory()
    by_year = Counter(asset.year for asset in assets)
    by_level = Counter(asset.filename_level for asset in assets)
    periods_by_year_level: dict[str, list[int]] = defaultdict(list)
    for asset in assets:
        periods_by_year_level[f"{asset.year}:{asset.filename_level}"].append(
            asset.filename_period
        )

    lookup = {asset.name: asset for asset in assets}
    overlap_pair_names = [
        ("2025_3_aaa_pbp.csv", "2025_4_aaa_pbp.csv"),
        ("2023_7_rk_pbp.csv", "2023_8_rk_pbp.csv"),
    ]
    overlap_order: list[dict[str, Any]] = []
    for earlier_name, later_name in overlap_pair_names:
        if earlier_name not in lookup or later_name not in lookup:
            continue
        earlier = lookup[earlier_name]
        later = lookup[later_name]
        overlap_order.append(
            {
                "earlier_asset": earlier_name,
                "earlier_asset_id": earlier.asset_id,
                "earlier_created_at_utc": earlier.created_at_utc.isoformat(),
                "earlier_updated_at_utc": earlier.updated_at_utc.isoformat(),
                "later_asset": later_name,
                "later_asset_id": later.asset_id,
                "later_created_at_utc": later.created_at_utc.isoformat(),
                "later_updated_at_utc": later.updated_at_utc.isoformat(),
                "creation_order_matches_filename_period": (
                    later.created_at_utc > earlier.created_at_utc
                ),
            }
        )

    # Do not assume every year/level has twelve calendar periods. The source has
    # historical schedule/collection differences. We report observed periods and
    # only flag exact duplicate filenames/IDs in the underlying validator.
    payload = {
        "report_schema_version": 1,
        "asset_count": len(assets),
        "min_year": min(by_year),
        "max_year": max(by_year),
        "asset_count_by_year": dict(sorted(by_year.items())),
        "asset_count_by_level": dict(sorted(by_level.items())),
        "observed_filename_periods_by_year_level": {
            key: sorted(set(values))
            for key, values in sorted(periods_by_year_level.items())
        },
        "known_overlap_pair_ordering": overlap_order,
        "assets": [
            {
                **asset.as_record(),
                "created_at_utc": asset.created_at_utc.isoformat(),
                "updated_at_utc": asset.updated_at_utc.isoformat(),
            }
            for asset in assets
        ],
    }

    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / "asset_inventory.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    lines = [
        "# armstjc PBP release asset inventory",
        "",
        f"- Recognized PBP assets: {len(assets)}",
        f"- Observed years: {payload['min_year']}–{payload['max_year']}",
        f"- Asset counts by level: `{payload['asset_count_by_level']}`",
        "",
        "## Known overlapping-pair ordering",
        "",
    ]
    for row in overlap_order:
        lines.append(
            f"- `{row['earlier_asset']}` created {row['earlier_created_at_utc']}; "
            f"`{row['later_asset']}` created {row['later_created_at_utc']}; "
            f"filename-period order matches asset creation order: "
            f"**{row['creation_order_matches_filename_period']}**"
        )
    lines.extend(
        [
            "",
            "GitHub asset creation/update timestamps are provenance metadata, not "
            "baseball event dates. This audit is used to decide whether they can "
            "support source-specific current-snapshot ordering; it does not make "
            "that policy decision by itself.",
            "",
        ]
    )
    summary = "\n".join(lines)
    (args.report_dir / "asset_inventory.md").write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
