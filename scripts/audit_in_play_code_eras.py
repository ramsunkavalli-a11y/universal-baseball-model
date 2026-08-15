#!/usr/bin/env python
"""Check armstjc in-play code semantics in older AAA release assets."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

import polars as pl

from universal_baseball.canonical_adapters import ARMSTJC_IN_PLAY_CODES
from universal_baseball.certification import download_file, read_quarantined_csv


BASE_URL = "https://github.com/armstjc/milb-data-repository/releases/download/pbp"
ASSETS = ("2005_9_aaa_pbp.csv", "2015_9_aaa_pbp.csv")


def _nonblank(column: str) -> pl.Expr:
    return pl.col(column).cast(pl.String, strict=False).fill_null("").str.strip_chars() != ""


def main() -> int:
    work_dir = Path("data/quarantine/in-play-code-era-audit")
    report_dir = Path("reports/generated/in-play-code-era-audit")
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    reports: list[dict[str, object]] = []
    for asset in ASSETS:
        path = work_dir / asset
        metadata = download_file(f"{BASE_URL}/{asset}", path, timeout_seconds=180)
        frame = read_quarantined_csv(path).unique()
        required = {"type", "bb_type", "hc_x", "hc_y"}
        missing = sorted(required - set(frame.columns))
        if missing:
            raise ValueError(f"{asset} missing required columns: {missing}")

        batted = frame.filter(_nonblank("bb_type"))
        code_counts = Counter(
            str(value).strip()
            for value in batted.get_column("type").to_list()
            if value is not None and str(value).strip()
        )
        unexpected_batted_codes = {
            code: count
            for code, count in code_counts.items()
            if code not in ARMSTJC_IN_PLAY_CODES
        }
        in_play_code_rows = frame.filter(
            pl.col("type").cast(pl.String, strict=False).is_in(sorted(ARMSTJC_IN_PLAY_CODES))
        )
        in_play_code_without_trajectory = in_play_code_rows.filter(~_nonblank("bb_type"))
        coordinate_complete = batted.filter(
            pl.col("hc_x").cast(pl.Float64, strict=False).is_not_null()
            & pl.col("hc_y").cast(pl.Float64, strict=False).is_not_null()
        )
        reports.append(
            {
                "asset": asset,
                "source_sha256": metadata["sha256"],
                "exact_unique_row_count": frame.height,
                "batted_ball_row_count": batted.height,
                "batted_ball_type_code_counts": dict(sorted(code_counts.items())),
                "unexpected_batted_ball_type_code_counts": dict(sorted(unexpected_batted_codes.items())),
                "in_play_code_row_count": in_play_code_rows.height,
                "in_play_code_without_bb_type_count": in_play_code_without_trajectory.height,
                "batted_ball_coordinate_complete_count": coordinate_complete.height,
                "batted_ball_coordinate_complete_rate": (
                    coordinate_complete.height / batted.height if batted.height else None
                ),
            }
        )

    payload = {
        "report_schema_version": 1,
        "accepted_in_play_codes": sorted(ARMSTJC_IN_PLAY_CODES),
        "assets": reports,
    }
    (report_dir / "in_play_code_eras.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# Historical in-play code era audit",
        "",
        f"Accepted positive codes: `{sorted(ARMSTJC_IN_PLAY_CODES)}`",
        "",
    ]
    for report in reports:
        lines.extend(
            [
                f"## `{report['asset']}`",
                "",
                f"- Exact-unique source rows: {report['exact_unique_row_count']:,}",
                f"- Rows with batted-ball trajectory: {report['batted_ball_row_count']:,}",
                f"- Codes on those rows: `{report['batted_ball_type_code_counts']}`",
                f"- Unexpected codes on batted-ball rows: `{report['unexpected_batted_ball_type_code_counts']}`",
                f"- D/E/X rows without trajectory: {report['in_play_code_without_bb_type_count']:,}",
                f"- Coordinate completeness on trajectory rows: {report['batted_ball_coordinate_complete_rate']:.2%}",
                "",
            ]
        )

    if any(report["unexpected_batted_ball_type_code_counts"] for report in reports):
        raise RuntimeError("historical batted-ball rows contain unreviewed source type codes")

    summary = "\n".join(lines)
    (report_dir / "in_play_code_eras.md").write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
