#!/usr/bin/env python
"""Profile distinct armstjc payloads that share the same pitch key."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from universal_baseball.certification import read_quarantined_csv
from universal_baseball.source_conflicts import profile_natural_key_conflicts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    return parser.parse_args()


def markdown_summary(report: dict) -> str:
    lines = [
        "# armstjc natural-key conflict profile",
        "",
        f"- Raw rows: {report.get('raw_rows')}",
        f"- Exact-unique rows: {report.get('exact_unique_rows')}",
        f"- Natural-key unique rows: {report.get('natural_key_unique_rows')}",
        f"- Conflicting pitch-key groups: {report.get('conflicting_key_group_count')}",
        f"- Conflicting pitch-key extra rows: {report.get('conflicting_key_extra_rows')}",
        "",
        "## Variant-count distribution",
        "",
    ]

    distribution = report.get("variant_count_distribution") or {}
    if distribution:
        for variants, count in distribution.items():
            lines.append(f"- {variants} distinct payloads: {count} pitch keys")
    else:
        lines.append("No conflicting pitch keys.")

    lines.extend(["", "## Most common changed payload columns", ""])
    top_columns = report.get("top_changed_columns") or []
    if top_columns:
        for row in top_columns:
            lines.append(
                f"- `{row['column']}`: {row['conflicting_key_groups']} pitch keys"
            )
    else:
        lines.append("No payload-column conflicts.")

    lines.extend(
        [
            "",
            "This report is diagnostic only. It does not select a winning row or "
            "repair the source.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    frame = read_quarantined_csv(args.input_file)
    report = profile_natural_key_conflicts(frame)

    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / "armstjc_key_conflicts.json").write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (args.report_dir / "armstjc_key_conflicts.md").write_text(
        markdown_summary(report),
        encoding="utf-8",
    )
    print(markdown_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
