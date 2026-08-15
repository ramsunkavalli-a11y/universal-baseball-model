#!/usr/bin/env python
"""Run the first armstjc MiLB PBP release smoke certification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.certification import (
    ReleaseSpec,
    build_release_report,
    download_file,
    markdown_summary,
    read_quarantined_csv,
    sha256_file,
    write_report,
)
from universal_baseball.official import fetch_official_game_evidence
from universal_baseball.source_comparison import (
    compare_pitch_source_to_official_pas,
    select_diverse_game_ids,
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
    parser.add_argument(
        "--official-sample-games",
        type=int,
        default=100,
        help="Number of date-spread games to compare with official PA results.",
    )
    parser.add_argument(
        "--skip-official-sample",
        action="store_true",
        help="Run only the release-integrity smoke test.",
    )
    return parser.parse_args()


def _write_official_comparison(
    comparison: dict,
    game_ids: list[int],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "armstjc_official_pa_sample.json"
    markdown_path = output_dir / "armstjc_official_pa_sample.md"

    payload = {"sample_game_ids": game_ids, **comparison}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# armstjc + official PA hybrid sample",
        "",
        f"- Sample games: {', '.join(str(game_id) for game_id in game_ids)}",
        f"- Raw source rows: {comparison['source_rows_raw']:,}",
        (
            "- Source rows after exact dedup **for comparison only**: "
            f"{comparison['source_rows_after_exact_dedup_for_comparison']:,}"
        ),
        f"- Source PAs: {comparison['source_pa_count']:,}",
        f"- Official PAs: {comparison['official_pa_count']:,}",
        f"- Shared PAs: {comparison['shared_pa_count']:,}",
        f"- Source-only PAs: {comparison['source_only_pa_count']:,}",
        f"- Official-only PAs: {comparison['official_only_pa_count']:,}",
        (
            "- PAs with source-vs-official pitch-count mismatch: "
            f"{comparison['pitch_count_mismatch_pa_count']:,}"
        ),
        (
            "- PAs with source-vs-official description mismatch: "
            f"{comparison['description_mismatch_pa_count']:,}"
        ),
        (
            "- Official PAs with nonblank event_type: "
            f"{comparison['official_event_type_nonblank_pa_count']:,}"
        ),
        (
            "- Source pitch rows with nonblank `events`: "
            f"{comparison['source_events_nonblank_pitch_row_count']}"
        ),
    ]

    diagnosis = comparison.get("pitch_count_mismatch_diagnosis")
    if diagnosis and diagnosis.get("available"):
        lines.extend(["", "## Pitch-count mismatch diagnosis", ""])
        for label, count in diagnosis["mismatch_class_counts"].items():
            lines.append(f"- {label}: {count}")
        lines.append(
            "- Missing official event codes: "
            f"{diagnosis['missing_official_pitch_event_code_counts']}"
        )
        lines.append(
            "- Missing official events with pitch data: "
            f"{diagnosis['missing_official_pitch_event_has_pitch_data_counts']}"
        )

    lines.extend(
        [
            "",
            "This is a viability test for a hybrid source strategy, not certification.",
            "",
        ]
    )
    markdown_path.write_text("\n".join(lines), encoding="utf-8")


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

    if args.skip_official_sample or args.official_sample_games <= 0:
        return 0

    game_ids = select_diverse_game_ids(frame, limit=args.official_sample_games)
    game_id_strings = [str(game_id) for game_id in game_ids]
    sample_source = frame.filter(pl.col("game_pk").is_in(game_id_strings))

    try:
        official_pas, official_pitch_events = fetch_official_game_evidence(game_ids)
        comparison = compare_pitch_source_to_official_pas(
            sample_source,
            official_pas,
            official_pitch_events,
        )
        _write_official_comparison(comparison, game_ids, args.report_dir)
    except Exception as exc:
        error_path = args.report_dir / "armstjc_official_pa_sample_error.json"
        error_path.parent.mkdir(parents=True, exist_ok=True)
        error_path.write_text(
            json.dumps(
                {
                    "sample_game_ids": game_ids,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        raise

    print(
        "\nHybrid sample: "
        f"{comparison['shared_pa_count']}/{comparison['official_pa_count']} official PAs "
        "matched source PA keys; "
        f"{comparison['pitch_count_mismatch_pa_count']} shared PAs had pitch-count "
        "mismatches."
    )
    diagnosis = comparison.get("pitch_count_mismatch_diagnosis")
    if diagnosis and diagnosis.get("available"):
        print(f"Mismatch classes: {diagnosis['mismatch_class_counts']}")
        print(
            "Missing official pitch-event codes: "
            f"{diagnosis['missing_official_pitch_event_code_counts']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
