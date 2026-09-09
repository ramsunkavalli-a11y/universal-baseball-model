#!/usr/bin/env python3
"""Report the disclosed 2025 check for the Phase 2 workload anchor."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-root", type=Path,
        default=Path("reports/generated/historical-projection-score/2025-03-27"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("reports/generated/phase2-workload-evaluation/2025/report.json"),
    )
    return parser.parse_args()


def _metrics(
    frame: pl.DataFrame, *, predicted: str, observed: str,
    reliability: float, strength: float, cap: float,
) -> dict[str, float | int]:
    scored = (
        frame.with_columns(
            (pl.col(predicted) / pl.col("mlb_active_probability").clip(1e-8, 1.0))
            .alias("conditional")
        )
        .with_columns(
            (
                pl.col("mlb_active_probability")
                * (
                    pl.col("conditional")
                    + pl.lit(strength)
                    * pl.col("prior_mlb_workload")
                    / (pl.col("prior_mlb_workload") + pl.lit(reliability))
                    * (
                        pl.col("prior_mlb_workload").clip(0.0, cap)
                        - pl.col("conditional")
                    )
                )
            ).alias("phase2_prediction")
        )
    )
    tail = scored.filter(pl.col("prior_mlb_workload") >= 500)
    return {
        "players": scored.height,
        "phase1_mae": float((scored[predicted] - scored[observed]).abs().mean()),
        "phase2_mae": float(
            (scored["phase2_prediction"] - scored[observed]).abs().mean()
        ),
        "established_players": tail.height,
        "phase1_established_bias": float((tail[predicted] - tail[observed]).mean()),
        "phase2_established_bias": float(
            (tail["phase2_prediction"] - tail[observed]).mean()
        ),
        "phase1_established_mae": float(
            (tail[predicted] - tail[observed]).abs().mean()
        ),
        "phase2_established_mae": float(
            (tail["phase2_prediction"] - tail[observed]).abs().mean()
        ),
    }


def main() -> int:
    args = _args()
    report = {
        "report_schema_version": "0.1",
        "gate": "phase2_workload_anchor_disclosed_2025_check",
        "hitter": _metrics(
            pl.read_parquet(args.source_root / "hitter-opportunity-scores.parquet"),
            predicted="expected_mlb_pa", observed="observed_mlb_pa",
            reliability=300.0, strength=0.75, cap=700.0,
        ),
        "pitcher": _metrics(
            pl.read_parquet(args.source_root / "pitcher-opportunity-scores.parquet"),
            predicted="expected_mlb_bf", observed="observed_mlb_bf",
            reliability=250.0, strength=0.25, cap=900.0,
        ),
        "boundary": (
            "2025 was already disclosed and is a diagnostic, not pristine confirmation. "
            "The correction may proceed as a Phase 2 preview, not a frozen production model."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
