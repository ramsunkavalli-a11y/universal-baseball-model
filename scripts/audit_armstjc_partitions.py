#!/usr/bin/env python
"""Audit adjacent armstjc release assets before trusting filename partitions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.partition_audit import compare_adjacent_partitions


LEFT_ASSET = "2025_3_aaa_pbp.csv"
RIGHT_ASSET = "2025_4_aaa_pbp.csv"
BASE_URL = "https://github.com/armstjc/milb-data-repository/releases/download/pbp"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--left-asset", default=LEFT_ASSET)
    parser.add_argument("--right-asset", default=RIGHT_ASSET)
    parser.add_argument("--left-url", default=f"{BASE_URL}/{LEFT_ASSET}")
    parser.add_argument("--right-url", default=f"{BASE_URL}/{RIGHT_ASSET}")
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/armstjc/partitions"),
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/armstjc"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.report_dir.mkdir(parents=True, exist_ok=True)

    left_path = args.work_dir / args.left_asset
    right_path = args.work_dir / args.right_asset
    left_meta = download_file(args.left_url, left_path, timeout_seconds=120)
    right_meta = download_file(args.right_url, right_path, timeout_seconds=120)

    left = read_quarantined_csv(left_path)
    right = read_quarantined_csv(right_path)
    comparison = compare_adjacent_partitions(left, right)

    report = {
        "left_asset": args.left_asset,
        "right_asset": args.right_asset,
        "left_retrieval": left_meta,
        "right_retrieval": right_meta,
        **comparison,
    }

    json_path = args.report_dir / "armstjc_adjacent_partition_audit.json"
    md_path = args.report_dir / "armstjc_adjacent_partition_audit.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    overlap = comparison["overlap"]
    left_profile = comparison["left"]
    right_profile = comparison["right"]
    lines = [
        "# armstjc adjacent-partition audit",
        "",
        f"- Left asset: `{args.left_asset}`",
        f"- Right asset: `{args.right_asset}`",
        f"- Left date range: {left_profile['min_game_date']} to {left_profile['max_game_date']}",
        f"- Right date range: {right_profile['min_game_date']} to {right_profile['max_game_date']}",
        f"- Left game_month values: {left_profile['game_month_values']}",
        f"- Right game_month values: {right_profile['game_month_values']}",
        f"- Left exact-duplicate extra rows: {left_profile['exact_duplicate_extra_rows']:,}",
        f"- Right exact-duplicate extra rows: {right_profile['exact_duplicate_extra_rows']:,}",
        f"- Overlapping natural keys: {overlap['natural_key_count']:,}",
        f"- Overlap with identical full rows: {overlap['identical_full_row_key_count']:,}",
        f"- Overlap with changed full rows: {overlap['changed_full_row_key_count']:,}",
        f"- Left-only natural keys: {overlap['left_only_natural_key_count']:,}",
        f"- Right-only natural keys: {overlap['right_only_natural_key_count']:,}",
        "",
        "## Overlapping keys by game date",
        "",
    ]
    for row in overlap["natural_keys_by_game_date"]:
        lines.append(f"- {row['game_date']}: {row['len']:,}")

    lines.extend(
        [
            "",
            "No rows are repaired or removed by this audit. Exact deduplication is applied only in-memory to understand partition behavior.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
