#!/usr/bin/env python
"""Profile Gameday trajectory labels before mapping them into model taxonomy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.trajectory_audit import build_trajectory_profile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--asset-name", required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    return parser.parse_args()


def _pct(value: float | None) -> str:
    return f"{value:.2%}" if value is not None else "n/a"


def _markdown(asset: str, metadata: dict[str, Any], report: dict[str, Any]) -> str:
    lines = [
        "# Gameday batted-ball trajectory taxonomy audit",
        "",
        f"- Asset: `{asset}`",
        f"- Source SHA-256: `{metadata['sha256']}`",
        f"- Natural pitch keys: {report['natural_pitch_key_count']:,}",
        f"- In-play pitch keys: {report['in_play_pitch_key_count']:,}",
        f"- Known trajectory labels: {report['known_trajectory_count']:,} "
        f"({_pct(report['known_trajectory_rate'])})",
        f"- Unknown trajectory labels: {report['unknown_trajectory_count']:,}",
        f"- Bunt trajectories: {report['bunt_in_play_count']:,} "
        f"({_pct(report['bunt_share_of_in_play'])} of in-play)",
        f"- `popup` + `fly_ball` descriptions mentioning foul: "
        f"{report['airborne_description_mentions_foul_count']:,} / "
        f"{report['airborne_count']:,} "
        f"({_pct(report['airborne_description_mentions_foul_rate'])})",
        f"- Audited-field conflicting pitch keys: "
        f"{report['audited_field_conflicts']['conflicting_pitch_key_count']:,}",
        "",
        "## Trajectory vocabulary",
        "",
        "| `bb_type` | Count | Share BIP | IF first touch | OF first touch | Foul text | Hit-like text |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for trajectory, count in report["trajectory_counts"].items():
        detail = report["trajectory_details"][trajectory]
        lines.append(
            f"| `{trajectory}` | {count:,} | {_pct(detail['share_of_in_play'])} | "
            f"{detail['infield_first_touch_count']:,} "
            f"({_pct(detail['infield_first_touch_rate_when_location_present'])}) | "
            f"{detail['outfield_first_touch_count']:,} "
            f"({_pct(detail['outfield_first_touch_rate_when_location_present'])}) | "
            f"{detail['description_mentions_foul_count']:,} "
            f"({_pct(detail['description_mentions_foul_rate'])}) | "
            f"{detail['description_hit_like_count']:,} "
            f"({_pct(detail['description_hit_like_rate'])}) |"
        )

    lines.extend(
        [
            "",
            "`hit_location` is the first fielder to touch the ball, so IF/OF touch is "
            "diagnostic rather than a definition of IFFB/OFFB. Narrative foul/hit "
            "flags are also diagnostic only; production PA outcomes come from the "
            "official structured play-sequence layer.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    source_path = args.work_dir / args.asset_name
    metadata = download_file(args.url, source_path)
    frame = read_quarantined_csv(source_path)
    report = build_trajectory_profile(frame)
    payload = {
        "report_schema_version": 1,
        "source_asset": args.asset_name,
        "source_url": args.url,
        "source_metadata": metadata,
        "report": report,
    }

    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / "trajectory_taxonomy.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    summary = _markdown(args.asset_name, metadata, report)
    (args.report_dir / "trajectory_taxonomy.md").write_text(
        summary, encoding="utf-8"
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
