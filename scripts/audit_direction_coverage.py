#!/usr/bin/env python
"""Measure cross-level direction evidence coverage in reusable MiLB pitch files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.batted_ball_direction import batted_ball_direction_expr
from universal_baseball.certification import download_file, read_quarantined_csv


PITCH_KEY = ("game_pk", "at_bat_number", "pitch_number")
AUDITED_SOURCE_FIELDS = (
    "type",
    "bb_type",
    "hit_location",
    "hc_x",
    "hc_y",
    "stand",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--asset-name", required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    return parser.parse_args()


def _nonblank_expr(column: str) -> pl.Expr:
    return pl.col(column).is_not_null() & (
        pl.col(column).cast(pl.String).str.strip_chars() != ""
    )


def _field_location_direction_expr(
    hit_location: pl.Expr,
    stand: pl.Expr,
) -> pl.Expr:
    """Coarse diagnostic fallback from scorer fielder-location code.

    This is deliberately *not* a promoted feature. Standard positions 5/6/7
    are treated as the left-field third, 1/2/8 as center, and 3/4/9 as the
    right-field third. The audit measures how this crude stringer/fielder signal
    agrees with coordinate-derived direction where both exist.
    """

    location = hit_location.cast(pl.Float64, strict=False).cast(pl.Int64, strict=False)
    left = location.is_in([5, 6, 7])
    center = location.is_in([1, 2, 8])
    right = location.is_in([3, 4, 9])
    valid = stand.is_in(["L", "R"]) & (left | center | right)
    pull = ((stand == "R") & left) | ((stand == "L") & right)

    return (
        pl.when(~valid)
        .then(pl.lit(None, dtype=pl.String))
        .when(center)
        .then(pl.lit("center"))
        .when(pull)
        .then(pl.lit("pull"))
        .otherwise(pl.lit("opposite"))
    )


def _conflict_profile(frame: pl.DataFrame) -> dict[str, Any]:
    fields = [field for field in AUDITED_SOURCE_FIELDS if field in frame.columns]
    if not fields:
        return {"conflicting_pitch_key_count": 0, "field_conflict_counts": {}}

    aggregations = [
        pl.col(field).drop_nulls().n_unique().alias(field) for field in fields
    ]
    grouped = frame.group_by(list(PITCH_KEY)).agg(aggregations)
    field_counts = {
        field: grouped.filter(pl.col(field) > 1).height
        for field in fields
    }
    conflict_filter = pl.any_horizontal([pl.col(field) > 1 for field in fields])
    return {
        "conflicting_pitch_key_count": grouped.filter(conflict_filter).height,
        "field_conflict_counts": field_counts,
    }


def _trajectory_breakdown(frame: pl.DataFrame) -> dict[str, int]:
    if "bb_type" not in frame.columns:
        return {}
    rows = (
        frame.filter(_nonblank_expr("bb_type"))
        .group_by("bb_type")
        .len()
        .sort("len", descending=True)
        .to_dicts()
    )
    return {str(row["bb_type"]): int(row["len"]) for row in rows}


def _direction_counts(frame: pl.DataFrame, column: str) -> dict[str, int]:
    rows = (
        frame.filter(pl.col(column).is_not_null())
        .group_by(column)
        .len()
        .sort(column)
        .to_dicts()
    )
    return {str(row[column]): int(row["len"]) for row in rows}


def build_report(frame: pl.DataFrame) -> dict[str, Any]:
    missing_key = sorted(set(PITCH_KEY) - set(frame.columns))
    if missing_key:
        raise ValueError(f"source missing natural pitch key: {missing_key}")
    if "type" not in frame.columns:
        raise ValueError("source missing pitch result code column 'type'")

    exact_unique = frame.unique()
    conflicts = _conflict_profile(exact_unique)

    # Coverage is measured at physical pitch-key grain. The tested source
    # conflicts have so far been timestamp-only; audited-field conflicts are
    # reported above so choosing the first observation cannot become silent.
    pitches = exact_unique.unique(subset=list(PITCH_KEY), keep="first")
    bip = pitches.filter(pl.col("type").cast(pl.String) == "X")

    required_direction = {"hc_x", "hc_y", "stand"}
    if required_direction <= set(bip.columns):
        bip = bip.with_columns(
            [
                batted_ball_direction_expr(
                    pl.col("hc_x"), pl.col("hc_y"), pl.col("stand")
                ).alias("coordinate_direction"),
                _field_location_direction_expr(
                    pl.col("hit_location"), pl.col("stand")
                ).alias("location_direction")
                if "hit_location" in bip.columns
                else pl.lit(None, dtype=pl.String).alias("location_direction"),
            ]
        )
    else:
        bip = bip.with_columns(
            [
                pl.lit(None, dtype=pl.String).alias("coordinate_direction"),
                pl.lit(None, dtype=pl.String).alias("location_direction"),
            ]
        )

    denominator = bip.height
    coverage_counts: dict[str, int] = {}
    for field in ("bb_type", "hit_location", "stand"):
        coverage_counts[field] = (
            bip.filter(_nonblank_expr(field)).height if field in bip.columns else 0
        )
    coordinate_count = (
        bip.filter(_nonblank_expr("hc_x") & _nonblank_expr("hc_y")).height
        if {"hc_x", "hc_y"} <= set(bip.columns)
        else 0
    )
    coverage_counts["hc_x_and_hc_y"] = coordinate_count
    coverage_counts["coordinate_direction"] = bip.filter(
        pl.col("coordinate_direction").is_not_null()
    ).height
    coverage_counts["location_direction"] = bip.filter(
        pl.col("location_direction").is_not_null()
    ).height

    coverage_rates = {
        field: count / denominator if denominator else None
        for field, count in coverage_counts.items()
    }

    both = bip.filter(
        pl.col("coordinate_direction").is_not_null()
        & pl.col("location_direction").is_not_null()
    )
    agreements = both.filter(
        pl.col("coordinate_direction") == pl.col("location_direction")
    ).height

    agreement_by_trajectory: dict[str, Any] = {}
    if "bb_type" in both.columns:
        for row in (
            both.group_by("bb_type")
            .agg(
                [
                    pl.len().alias("both_count"),
                    (pl.col("coordinate_direction") == pl.col("location_direction"))
                    .sum()
                    .alias("agreement_count"),
                ]
            )
            .sort("both_count", descending=True)
            .to_dicts()
        ):
            count = int(row["both_count"])
            matched = int(row["agreement_count"])
            agreement_by_trajectory[str(row["bb_type"])] = {
                "both_count": count,
                "agreement_count": matched,
                "agreement_rate": matched / count if count else None,
            }

    return {
        "raw_row_count": frame.height,
        "exact_unique_row_count": exact_unique.height,
        "natural_pitch_key_count": pitches.height,
        "in_play_pitch_key_count": denominator,
        "audited_field_conflicts": conflicts,
        "coverage_counts": coverage_counts,
        "coverage_rates": coverage_rates,
        "trajectory_counts": _trajectory_breakdown(bip),
        "coordinate_direction_counts": _direction_counts(bip, "coordinate_direction"),
        "location_direction_counts": _direction_counts(bip, "location_direction"),
        "coordinate_location_both_count": both.height,
        "coordinate_location_agreement_count": agreements,
        "coordinate_location_agreement_rate": (
            agreements / both.height if both.height else None
        ),
        "agreement_by_trajectory": agreement_by_trajectory,
    }


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
            "This report measures evidence coverage before any fallback hierarchy is promoted.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    source_path = args.work_dir / args.asset_name
    metadata = download_file(args.url, source_path)
    frame = read_quarantined_csv(source_path)
    report = build_report(frame)
    payload = {
        "report_schema_version": 1,
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
