#!/usr/bin/env python
"""Measure cross-level direction evidence coverage in reusable MiLB pitch files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.direction_coverage import build_direction_coverage_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--asset-name", required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    return parser.parse_args()


def _percent(value: float | None) -> str:
    return f"{value:.1%}" if value is not None else "n/a"


def _markdown(asset: str, metadata: dict[str, Any], report: dict[str, Any]) -> str:
    lines = [
        "# Batted-ball direction evidence coverage",
        "",
        f"- Asset: `{asset}`",
        f"- Source SHA-256: `{metadata['sha256']}`",
        f"- Raw rows: {report['raw_row_count']:,}",
        f"- Natural pitch keys: {report['natural_pitch_key_count']:,}",
        f"- In-play pitch keys (`type == X`): {report['in_play_pitch_key_count']:,}",
        f"- Audited-field conflicting pitch keys: "
        f"{report['audited_field_conflicts']['conflicting_pitch_key_count']:,}",
        "",
        "## Coverage among in-play pitch keys",
        "",
        "| Evidence | Count | Coverage |",
        "|---|---:|---:|",
    ]
    for field, count in report["coverage_counts"].items():
        lines.append(
            f"| `{field}` | {count:,} | {_percent(report['coverage_rates'][field])} |"
        )

    lines.extend(
        [
            "",
            "## Direction comparison",
            "",
            f"- Coordinate + coarse location both available: "
            f"{report['coordinate_location_both_count']:,}",
            f"- Agreement: {report['coordinate_location_agreement_count']:,} "
            f"({_percent(report['coordinate_location_agreement_rate'])})",
            f"- Coordinate direction counts: `{report['coordinate_direction_counts']}`",
            f"- Coarse location direction counts: `{report['location_direction_counts']}`",
            f"- Trajectory counts: `{report['trajectory_counts']}`",
            "",
            "### Agreement by batted-ball trajectory",
            "",
            "| Trajectory | Both | Agreement |",
            "|---|---:|---:|",
        ]
    )
    for trajectory, summary in report["agreement_by_trajectory"].items():
        lines.append(
            f"| `{trajectory}` | {summary['both_count']:,} | "
            f"{_percent(summary['agreement_rate'])} |"
        )

    lines.extend(
        [
            "",
            "The `location_direction` mapping is a diagnostic proxy based on the "
            "fielder/location code, not an accepted ground-truth direction label. "
            "Disagreement can reflect defensive positioning as well as source error. "
            "Conflicting source fields are projected as unavailable rather than "
            "resolved by arbitrary row order. This report measures evidence coverage "
            "before any fallback hierarchy is promoted.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    source_path = args.work_dir / args.asset_name
    metadata = download_file(args.url, source_path)
    frame = read_quarantined_csv(source_path)
    report = build_direction_coverage_report(frame)
    payload = {
        "report_schema_version": 2,
        "source_asset": args.asset_name,
        "source_url": args.url,
        "source_metadata": metadata,
        "report": report,
    }

    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / "direction_coverage.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    summary = _markdown(args.asset_name, metadata, report)
    (args.report_dir / "direction_coverage.md").write_text(
        summary, encoding="utf-8"
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
