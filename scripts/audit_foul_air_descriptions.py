#!/usr/bin/env python
"""Audit reusable Gameday narrative vocabulary for foul-air outs.

This is a descriptive certification tool, not a production classifier. It asks
whether a narrow, explicit narrative allowlist can identify airborne balls
caught in foul territory without treating every occurrence of the word
``foul`` as equivalent evidence.

The source rows are first collapsed at natural physical-pitch grain using the
same non-null field-consensus logic as the trajectory taxonomy audit. We then
inspect ``popup``, ``fly_ball``, and ``line_drive`` trajectories and partition
descriptions into explicit foul-territory phrases versus other/ambiguous uses
of ``foul``. Spray angle is retained only as a diagnostic; it is never used to
classify fair/foul status.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from typing import Any

import polars as pl

from universal_baseball.batted_ball_direction import field_spray_angle_expr
from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.trajectory_audit import collapse_trajectory_evidence


FOUL_SCREEN_BB_TYPES = frozenset({"popup", "fly_ball", "line_drive"})
EXPLICIT_FOUL_TERRITORY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("foul_territory", re.compile(r"\bfoul\s+territory\b", re.IGNORECASE)),
    ("foul_ground", re.compile(r"\bfoul\s+ground\b", re.IGNORECASE)),
)
BROAD_FOUL_PATTERN = re.compile(r"\bfoul\b", re.IGNORECASE)
FOUL_LINE_PATTERN = re.compile(r"\bfoul\s+line\b", re.IGNORECASE)
FOUL_POLE_PATTERN = re.compile(r"\bfoul\s+pole\b", re.IGNORECASE)
FOUL_BALL_PATTERN = re.compile(r"\bfoul\s+ball\b", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--asset-name", required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--example-limit", type=int, default=50)
    return parser.parse_args()


def _clean_text(value: Any) -> str:
    return "" if value is None else " ".join(str(value).split())


def classify_description(text: str) -> dict[str, Any]:
    """Return mutually useful narrative diagnostics without promoting a rule."""

    explicit_matches = [
        name for name, pattern in EXPLICIT_FOUL_TERRITORY_PATTERNS if pattern.search(text)
    ]
    broad_foul = bool(BROAD_FOUL_PATTERN.search(text))
    return {
        "broad_foul": broad_foul,
        "explicit_foul_territory": bool(explicit_matches),
        "explicit_pattern_names": explicit_matches,
        "mentions_foul_line": bool(FOUL_LINE_PATTERN.search(text)),
        "mentions_foul_pole": bool(FOUL_POLE_PATTERN.search(text)),
        "mentions_foul_ball": bool(FOUL_BALL_PATTERN.search(text)),
        "broad_foul_without_explicit_territory": broad_foul and not explicit_matches,
    }


def _example(row: dict[str, Any], classification: dict[str, Any]) -> dict[str, Any]:
    return {
        "game_pk": row.get("game_pk"),
        "at_bat_number": row.get("at_bat_number"),
        "pitch_number": row.get("pitch_number"),
        "bb_type": row.get("bb_type"),
        "hit_location": row.get("hit_location"),
        "description": _clean_text(row.get("description")),
        "spray_angle": row.get("spray_angle"),
        **classification,
    }


def build_report(frame: pl.DataFrame, *, example_limit: int) -> dict[str, Any]:
    if example_limit < 1:
        raise ValueError("example_limit must be at least 1")

    collapsed = collapse_trajectory_evidence(frame.unique())
    required = {"bb_type", "description"}
    missing = sorted(required - set(collapsed.columns))
    if missing:
        raise ValueError(f"collapsed source missing foul-air fields: {missing}")

    airborne = collapsed.filter(pl.col("bb_type").is_in(sorted(FOUL_SCREEN_BB_TYPES)))
    if {"hc_x", "hc_y"} <= set(airborne.columns):
        airborne = airborne.with_columns(
            field_spray_angle_expr(pl.col("hc_x"), pl.col("hc_y")).alias("spray_angle")
        )
    else:
        airborne = airborne.with_columns(pl.lit(None, dtype=pl.Float64).alias("spray_angle"))

    description_conflict_count = (
        airborne.filter(pl.col("description__conflict")).height
        if "description__conflict" in airborne.columns
        else 0
    )
    with_description = airborne.filter(pl.col("description").is_not_null())

    counters = Counter()
    pattern_counts = Counter()
    category_examples: dict[str, list[dict[str, Any]]] = {
        "explicit_foul_territory": [],
        "broad_foul_without_explicit_territory": [],
        "mentions_foul_line": [],
        "mentions_foul_pole": [],
        "mentions_foul_ball": [],
    }
    broad_foul_text_counts = Counter()
    explicit_text_counts = Counter()
    ambiguous_text_counts = Counter()

    for row in with_description.to_dicts():
        text = _clean_text(row.get("description"))
        classification = classify_description(text)
        counters["description_count"] += 1
        for key in (
            "broad_foul",
            "explicit_foul_territory",
            "broad_foul_without_explicit_territory",
            "mentions_foul_line",
            "mentions_foul_pole",
            "mentions_foul_ball",
        ):
            if classification[key]:
                counters[key] += 1
        for name in classification["explicit_pattern_names"]:
            pattern_counts[name] += 1
        if classification["broad_foul"]:
            broad_foul_text_counts[text] += 1
        if classification["explicit_foul_territory"]:
            explicit_text_counts[text] += 1
        if classification["broad_foul_without_explicit_territory"]:
            ambiguous_text_counts[text] += 1
        for category in category_examples:
            if classification[category] and len(category_examples[category]) < example_limit:
                category_examples[category].append(_example(row, classification))

    trajectory_counts = {
        str(row["bb_type"]): int(row["len"])
        for row in airborne.group_by("bb_type").len().sort("bb_type").to_dicts()
    }

    broad_foul = counters["broad_foul"]
    explicit = counters["explicit_foul_territory"]
    return {
        "natural_pitch_key_count": collapsed.height,
        "foul_screen_bb_types": sorted(FOUL_SCREEN_BB_TYPES),
        "airborne_pitch_count": airborne.height,
        "airborne_trajectory_counts": trajectory_counts,
        "airborne_description_present_count": with_description.height,
        "airborne_description_missing_count": airborne.height - with_description.height,
        "airborne_description_conflict_count": description_conflict_count,
        "broad_foul_count": broad_foul,
        "explicit_foul_territory_count": explicit,
        "broad_foul_without_explicit_territory_count": counters[
            "broad_foul_without_explicit_territory"
        ],
        "explicit_share_of_broad_foul": explicit / broad_foul if broad_foul else None,
        "mentions_foul_line_count": counters["mentions_foul_line"],
        "mentions_foul_pole_count": counters["mentions_foul_pole"],
        "mentions_foul_ball_count": counters["mentions_foul_ball"],
        "explicit_pattern_counts": dict(sorted(pattern_counts.items())),
        "broad_foul_description_counts": dict(
            broad_foul_text_counts.most_common(example_limit)
        ),
        "explicit_foul_territory_description_counts": dict(
            explicit_text_counts.most_common(example_limit)
        ),
        "broad_foul_without_explicit_territory_description_counts": dict(
            ambiguous_text_counts.most_common(example_limit)
        ),
        "examples": category_examples,
    }


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2%}"


def _markdown(asset: str, metadata: dict[str, Any], report: dict[str, Any]) -> str:
    lines = [
        "# Foul-air description vocabulary audit",
        "",
        "**Diagnostic only. This report does not promote a production foul-air rule.**",
        "",
        f"- Asset: `{asset}`",
        f"- Source SHA-256: `{metadata['sha256']}`",
        f"- Candidate `popup` + `fly_ball` + `line_drive` pitch keys: {report['airborne_pitch_count']:,}",
        f"- Description present: {report['airborne_description_present_count']:,}",
        f"- Description missing: {report['airborne_description_missing_count']:,}",
        f"- Description conflicts at natural pitch grain: {report['airborne_description_conflict_count']:,}",
        f"- Broad word-boundary `foul`: {report['broad_foul_count']:,}",
        f"- Explicit `foul territory` / `foul ground`: {report['explicit_foul_territory_count']:,}",
        f"- Explicit share of broad foul: {_pct(report['explicit_share_of_broad_foul'])}",
        f"- Broad foul without explicit territory/ground: {report['broad_foul_without_explicit_territory_count']:,}",
        f"- Mentions `foul line`: {report['mentions_foul_line_count']:,}",
        f"- Mentions `foul pole`: {report['mentions_foul_pole_count']:,}",
        f"- Mentions `foul ball`: {report['mentions_foul_ball_count']:,}",
        "",
        "## Explicit phrase counts",
        "",
    ]
    if report["explicit_pattern_counts"]:
        for name, count in report["explicit_pattern_counts"].items():
            lines.append(f"- `{name}`: {count:,}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Broad foul descriptions without explicit territory/ground",
            "",
        ]
    )
    ambiguous = report["broad_foul_without_explicit_territory_description_counts"]
    if ambiguous:
        for text, count in ambiguous.items():
            lines.append(f"- {count}× `{text}`")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "Spray angle is retained in JSON examples only as a diagnostic. It is not used in the narrative categories above.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)

    source_path = args.work_dir / args.asset_name
    metadata = download_file(args.url, source_path, timeout_seconds=240)
    frame = read_quarantined_csv(source_path)
    if frame.is_empty():
        raise RuntimeError(f"foul-air source asset is empty: {args.asset_name}")
    report = build_report(frame, example_limit=args.example_limit)
    payload = {
        "report_schema_version": 2,
        "status": "description_vocabulary_diagnostic_not_production_rule",
        "source_asset": args.asset_name,
        "source_url": args.url,
        "source_metadata": metadata,
        "patterns": {
            "explicit_foul_territory": [
                {"name": name, "regex": pattern.pattern}
                for name, pattern in EXPLICIT_FOUL_TERRITORY_PATTERNS
            ],
            "broad_foul": BROAD_FOUL_PATTERN.pattern,
            "foul_line": FOUL_LINE_PATTERN.pattern,
            "foul_pole": FOUL_POLE_PATTERN.pattern,
            "foul_ball": FOUL_BALL_PATTERN.pattern,
        },
        "report": report,
    }
    (args.report_dir / "foul_air_descriptions.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    summary = _markdown(args.asset_name, metadata, report)
    (args.report_dir / "foul_air_descriptions.md").write_text(
        summary, encoding="utf-8"
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
