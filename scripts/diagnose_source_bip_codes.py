#!/usr/bin/env python
"""Profile armstjc pitch `type` codes on rows carrying batted-ball evidence."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

import polars as pl

from universal_baseball.certification import read_quarantined_csv


SAMPLES = {
    "2025_4_aaa_pbp.csv": [779882, 780248, 781453],
    "2024_6_rk_pbp.csv": [772320, 773530, 771821],
}


def _nonblank(column: str) -> pl.Expr:
    return pl.col(column).cast(pl.String, strict=False).fill_null("").str.strip_chars() != ""


def main() -> int:
    work_dir = Path("data/quarantine/missing-batted-ball-diagnostic")
    report_dir = Path("reports/generated/missing-batted-ball-diagnostic")
    report_dir.mkdir(parents=True, exist_ok=True)

    code_rows: list[dict[str, object]] = []
    sequence_rows: list[dict[str, object]] = []

    for asset, game_ids in SAMPLES.items():
        path = work_dir / asset
        if not path.exists():
            raise FileNotFoundError(
                f"{path} is missing; run diagnose_missing_batted_ball_events.py first"
            )
        frame = read_quarantined_csv(path).filter(
            pl.col("game_pk").cast(pl.Int64, strict=False).is_in(game_ids)
        )
        if "bb_type" not in frame.columns or "type" not in frame.columns:
            raise ValueError(f"{asset} lacks type/bb_type columns")

        batted_rows = frame.filter(_nonblank("bb_type")).unique()
        for row in batted_rows.select(
            ["game_pk", "at_bat_number", "pitch_number", "type", "bb_type"]
        ).to_dicts():
            code_rows.append(
                {
                    "asset": asset,
                    "game_pk": int(float(str(row["game_pk"]))),
                    "at_bat_index": int(float(str(row["at_bat_number"]))),
                    "pitch_number": int(float(str(row["pitch_number"]))),
                    "type": None if row["type"] is None else str(row["type"]).strip(),
                    "bb_type": str(row["bb_type"]).strip(),
                }
            )

        grouped = (
            batted_rows.group_by(["game_pk", "at_bat_number"])
            .agg(
                pl.len().alias("bb_type_row_count"),
                pl.col("type").cast(pl.String, strict=False).drop_nulls().unique().sort().alias("type_values"),
                pl.col("bb_type").cast(pl.String, strict=False).drop_nulls().unique().sort().alias("bb_type_values"),
            )
        )
        for row in grouped.to_dicts():
            type_values = [str(value) for value in (row["type_values"] or []) if str(value).strip()]
            sequence_rows.append(
                {
                    "asset": asset,
                    "game_pk": int(float(str(row["game_pk"]))),
                    "at_bat_index": int(float(str(row["at_bat_number"]))),
                    "bb_type_row_count": int(row["bb_type_row_count"]),
                    "type_values": type_values,
                    "bb_type_values": [str(value) for value in (row["bb_type_values"] or [])],
                    "has_type_x": "X" in type_values,
                }
            )

    row_code_counts = Counter(str(row["type"]) for row in code_rows)
    row_bb_type_counts = Counter(str(row["bb_type"]) for row in code_rows)
    no_x_sequences = [row for row in sequence_rows if not row["has_type_x"]]
    no_x_code_sets = Counter(
        ",".join(row["type_values"]) if row["type_values"] else "<blank>"
        for row in no_x_sequences
    )
    no_x_bb_types = Counter(
        bb_type
        for row in no_x_sequences
        for bb_type in row["bb_type_values"]
    )

    payload = {
        "report_schema_version": 1,
        "batted_ball_source_row_count": len(code_rows),
        "batted_ball_sequence_count": len(sequence_rows),
        "batted_ball_sequence_with_type_x_count": sum(row["has_type_x"] for row in sequence_rows),
        "batted_ball_sequence_without_type_x_count": len(no_x_sequences),
        "batted_ball_sequence_without_type_x_rate": (
            len(no_x_sequences) / len(sequence_rows) if sequence_rows else None
        ),
        "type_code_counts_on_batted_ball_rows": dict(sorted(row_code_counts.items())),
        "bb_type_counts": dict(sorted(row_bb_type_counts.items())),
        "type_code_sets_on_batted_ball_sequences_without_x": dict(sorted(no_x_code_sets.items())),
        "bb_types_on_sequences_without_x": dict(sorted(no_x_bb_types.items())),
        "without_x_examples": no_x_sequences[:40],
        "parser_semantics_note": (
            "armstjc get_milb_pbp.py populates bb_type only inside its upstream "
            "details.isInPlay == True branch, while exported type is details.code. "
            "Therefore nonblank bb_type is direct preserved in-play evidence even "
            "when details.code is not literal X."
        ),
    }
    (report_dir / "source_bip_code_semantics.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# Reusable-source BIP code semantics",
        "",
        f"- Batted-ball source rows: {len(code_rows):,}",
        f"- Batted-ball sequences: {len(sequence_rows):,}",
        f"- Sequences with literal `type == X`: {sum(row['has_type_x'] for row in sequence_rows):,}",
        f"- Sequences with batted-ball evidence but no literal X: {len(no_x_sequences):,} "
        f"({len(no_x_sequences) / len(sequence_rows):.2%})",
        f"- `type` codes on batted-ball rows: `{dict(sorted(row_code_counts.items()))}`",
        f"- `bb_type` counts: `{dict(sorted(row_bb_type_counts.items()))}`",
        f"- Non-X code sets: `{dict(sorted(no_x_code_sets.items()))}`",
        "",
        "The upstream parser sets `bb_type` only when MLB's structured `details.isInPlay` is true. The exported `type` field is `details.code`, so a literal `X` must not be treated as the universal in-play truth flag unless independently certified.",
        "",
    ]
    summary = "\n".join(lines)
    (report_dir / "source_bip_code_semantics.md").write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
