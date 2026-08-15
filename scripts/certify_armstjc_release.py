#!/usr/bin/env python
"""Run armstjc MiLB PBP release certification against official true PAs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

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
from universal_baseball.source_sequence_comparison import (
    compare_pitch_source_to_official_true_pas,
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
        default=5,
        help=(
            "Number of date-spread games to compare with official true plate "
            "appearances and pitch events. Use a large value for an explicit "
            "full-release audit."
        ),
    )
    parser.add_argument(
        "--skip-official-sample",
        action="store_true",
        help="Run only the release-integrity smoke test.",
    )
    return parser.parse_args()


def _fetch_official_per_game(
    game_ids: list[int],
) -> tuple[pl.DataFrame, pl.DataFrame, list[dict[str, Any]], list[int]]:
    """Fetch official true-PA and pitch evidence while recording failures."""

    pa_frames: list[pl.DataFrame] = []
    pitch_frames: list[pl.DataFrame] = []
    failures: list[dict[str, Any]] = []
    successes: list[int] = []

    for game_id in game_ids:
        try:
            pa_frame, pitch_frame = fetch_official_game_evidence([game_id])
        except Exception as exc:
            failures.append(
                {
                    "game_pk": int(game_id),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
            continue

        pa_frames.append(pa_frame)
        pitch_frames.append(pitch_frame)
        successes.append(int(game_id))

    official_true_pas = (
        pl.concat(pa_frames, how="vertical_relaxed") if pa_frames else pl.DataFrame()
    )
    official_pitch_events = (
        pl.concat(pitch_frames, how="vertical_relaxed")
        if pitch_frames
        else pl.DataFrame()
    )
    return official_true_pas, official_pitch_events, failures, successes


def _write_official_comparison(
    comparison: dict[str, Any],
    game_ids: list[int],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "armstjc_official_sequence_sample.json"
    markdown_path = output_dir / "armstjc_official_sequence_sample.md"

    payload = {
        "report_schema_version": 3,
        "sample_game_ids": game_ids,
        **comparison,
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# armstjc pitch-sequence + official true-PA sample",
        "",
        f"- Requested games: {len(game_ids)}",
        f"- Official-adapter successful games: {comparison['successful_official_game_count']}",
        f"- Official-adapter failed games: {len(comparison['official_fetch_failures'])}",
        f"- Raw source rows: {comparison['source_rows_raw']:,}",
        (
            "- Source rows after exact dedup **for comparison only**: "
            f"{comparison['source_rows_after_exact_dedup_for_comparison']:,}"
        ),
        (
            "- Distinct natural pitch keys **for comparison only**: "
            f"{comparison['source_rows_after_natural_key_collapse_for_comparison']:,}"
        ),
        f"- Source pitch-bearing sequences: {comparison['source_pitch_sequence_count']:,}",
        f"- Official true PAs: {comparison['official_true_pa_count']:,}",
        (
            "- Shared source-sequence / true-PA keys: "
            f"{comparison['shared_sequence_true_pa_count']:,}"
        ),
        f"- Source-only pitch-bearing sequences: {comparison['source_only_pitch_sequence_count']:,}",
        f"- Official-only true PAs: {comparison['official_only_true_pa_count']:,}",
        (
            "- Official-only zero-pitch true PAs (structural pitch-table gap): "
            f"{comparison['official_only_zero_pitch_true_pa_count']:,}"
        ),
        (
            "- Official-only positive-pitch true PAs (unexplained gap): "
            f"{comparison['official_only_positive_pitch_true_pa_count']:,}"
        ),
        (
            "- Shared sequences with source-vs-official pitch-count mismatch: "
            f"{comparison['pitch_count_mismatch_sequence_count']:,}"
        ),
        (
            "- Shared sequences with source-vs-official description mismatch: "
            f"{comparison['description_mismatch_sequence_count']:,}"
        ),
        (
            "- Official true PAs with nonblank event_type: "
            f"{comparison['official_event_type_nonblank_true_pa_count']:,}"
        ),
        (
            "- Source pitch rows with nonblank `events`: "
            f"{comparison['source_events_nonblank_pitch_row_count']}"
        ),
    ]

    zero_pitch_examples = (
        comparison.get("official_only_zero_pitch_true_pa_examples") or []
    )
    if zero_pitch_examples:
        lines.extend(["", "## Structural zero-pitch true-PA gaps", ""])
        for row in zero_pitch_examples:
            lines.append(
                f"- game {row['game_pk']} sequence {row['at_bat_number']}: "
                f"{row.get('event_type')} — {row.get('description')}"
            )

    source_only_examples = comparison.get("source_only_pitch_sequence_examples") or []
    if source_only_examples:
        lines.extend(["", "## Source-only pitch-bearing sequence examples", ""])
        for row in source_only_examples[:10]:
            lines.append(
                f"- game {row['game_pk']} sequence {row['at_bat_number']}"
            )

    if comparison["official_fetch_failures"]:
        lines.extend(["", "## Official-adapter failures", ""])
        for failure in comparison["official_fetch_failures"]:
            first_line = failure["error"].splitlines()[0]
            lines.append(
                f"- game {failure['game_pk']}: {failure['error_type']}: {first_line}"
            )

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
            "A source `game_pk + atBatIndex` group is a **pitch-bearing sequence**, "
            "not automatically a plate appearance. Official true-PA membership is "
            "defined independently by versioned MLB event semantics.",
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
    official_true_pas, official_pitch_events, failures, successful_game_ids = (
        _fetch_official_per_game(game_ids)
    )

    if not successful_game_ids:
        error_path = args.report_dir / "armstjc_official_sequence_sample_error.json"
        error_path.parent.mkdir(parents=True, exist_ok=True)
        error_path.write_text(
            json.dumps(
                {
                    "sample_game_ids": game_ids,
                    "official_fetch_failures": failures,
                    "error": "official adapter failed for every requested game",
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        raise RuntimeError("official adapter failed for every requested game")

    successful_strings = [str(game_id) for game_id in successful_game_ids]
    sample_source = frame.filter(pl.col("game_pk").is_in(successful_strings))
    comparison = compare_pitch_source_to_official_true_pas(
        sample_source,
        official_true_pas,
        official_pitch_events,
    )
    comparison["requested_game_count"] = len(game_ids)
    comparison["successful_official_game_count"] = len(successful_game_ids)
    comparison["official_fetch_failures"] = failures
    _write_official_comparison(comparison, game_ids, args.report_dir)

    print(
        "\nHybrid sample: "
        f"{comparison['shared_sequence_true_pa_count']}/"
        f"{comparison['official_true_pa_count']} official true PAs shared a source "
        "pitch-sequence key; "
        f"{comparison['pitch_count_mismatch_sequence_count']} shared sequences had "
        "pitch-count mismatches."
    )
    print(
        "True-PA gaps from the pitch table: "
        f"{comparison['official_only_zero_pitch_true_pa_count']} structural zero-pitch; "
        f"{comparison['official_only_positive_pitch_true_pa_count']} unexplained positive-pitch."
    )
    print(
        "Source-only pitch-bearing sequences: "
        f"{comparison['source_only_pitch_sequence_count']}"
    )
    print(
        "Official-adapter coverage: "
        f"{len(successful_game_ids)}/{len(game_ids)} games; "
        f"failed game IDs: {[failure['game_pk'] for failure in failures]}"
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
