#!/usr/bin/env python
"""Run the first armstjc MiLB PBP release smoke certification."""

from __future__ import annotations

import argparse
from pathlib import Path

from universal_baseball.certification import (
    ReleaseSpec,
    build_release_report,
    download_file,
    markdown_summary,
    read_quarantined_csv,
    sha256_file,
    write_report,
)


DEFAULT_ASSET = "2025_3_aaa_pbp.csv"
DEFAULT_URL = (
    "https://github.com/armstjc/milb-data-repository/releases/download/pbp/"
    f"{DEFAULT_ASSET}"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--asset-name", default=DEFAULT_ASSET)
    parser.add_argument("--expected-year", type=int, default=2025)
    parser.add_argument("--expected-month", type=int, default=3)
    parser.add_argument("--expected-level", default="aaa")
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/armstjc"),
        help="Temporary source-data directory; must remain outside git.",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/generated/armstjc"),
    )
    parser.add_argument(
        "--input-file",
        type=Path,
        default=None,
        help="Profile an already-downloaded file instead of fetching the release.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    spec = ReleaseSpec(
        source_name="armstjc/milb-data-repository",
        asset_name=args.asset_name,
        url=args.url,
        expected_year=args.expected_year,
        expected_month=args.expected_month,
        expected_level=args.expected_level,
    )

    if args.input_file is not None:
        source_path = args.input_file
        file_metadata = {
            "retrieved_at_utc": None,
            "resolved_url": None,
            "file_size_bytes": source_path.stat().st_size,
            "sha256": sha256_file(source_path),
            "provided_locally": True,
        }
    else:
        source_path = args.work_dir / args.asset_name
        file_metadata = download_file(args.url, source_path)
        file_metadata["provided_locally"] = False

    frame = read_quarantined_csv(source_path)
    report = build_release_report(frame, spec, file_metadata)
    write_report(report, args.report_dir)
    print(markdown_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
