#!/usr/bin/env python3
"""Materialize the all-player denominator for joint aging/opportunity scoring."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.next_season_transitions import build_next_season_transitions
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-root", type=Path,
        default=Path("reports/generated/career-mlb-outcome-inventory-2009-2025/tables"),
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/next-season-transition-scoreboard"),
    )
    return parser.parse_args()


def _summary(frame: pl.DataFrame, column: str) -> list[dict[str, object]]:
    return frame.group_by(column).agg(
        pl.len().alias("source_player_seasons"),
        pl.col("returned_any").sum().alias("returned_player_seasons"),
        pl.col("returned_any").mean().alias("return_rate"),
        pl.col("target_batting_pa").mean().alias("mean_next_batting_pa_all"),
        pl.col("target_pitching_bf").mean().alias("mean_next_pitching_bf_all"),
    ).sort(column).to_dicts()


def _workload_error(frame: pl.DataFrame, source: str, target: str) -> dict[str, float | int]:
    eligible = frame.filter(pl.col(source) > 0)
    returners = eligible.filter(pl.col(target) > 0)
    return {
        "source_player_seasons": eligible.height,
        "returners": returners.height,
        "return_rate": returners.height / eligible.height,
        "carry_forward_mae_all": float(
            eligible.select((pl.col(source) - pl.col(target)).abs().mean()).item()
        ),
        "carry_forward_mae_returners_only": float(
            returners.select((pl.col(source) - pl.col(target)).abs().mean()).item()
        ),
        "observed_mean_all": float(eligible.get_column(target).mean()),
        "observed_mean_returners_only": float(returners.get_column(target).mean()),
    }


def main() -> int:
    args = _args()
    hitting_path = args.source_root / "mlb_hitting_components_2009_2025.parquet"
    pitching_path = args.source_root / "mlb_pitching_2009_2025.parquet"
    hitting = pl.read_parquet(hitting_path).select(
        "season", "player_id", pl.col("batting_plate_appearances").alias("batting_pa")
    )
    pitching = pl.read_parquet(pitching_path).select(
        "season", "player_id", "pitching_bf"
    )
    seasons = sorted(
        set(hitting.get_column("season").to_list())
        | set(pitching.get_column("season").to_list())
    )
    transitions = build_next_season_transitions(
        hitting, pitching, complete_seasons=seasons, source_seasons=seasons
    )
    observed = transitions.filter(~pl.col("is_right_censored"))
    args.output_root.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        transitions, args.output_root / "next-season-transitions.parquet",
        table_name="complete_next_season_mlb_transitions",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "status": "denominator_ready_no_production_change",
        "source_seasons": [seasons[0], seasons[-1]],
        "observed_transition_seasons": [seasons[0], seasons[-1] - 1],
        "source_player_seasons": transitions.height,
        "observed_player_seasons": observed.height,
        "right_censored_player_seasons": transitions.height - observed.height,
        "observed_inactive_player_seasons": observed.filter(
            pl.col("target_state") == "inactive"
        ).height,
        "overall_return_rate": float(observed.get_column("returned_any").mean()),
        "by_source_state": _summary(observed, "source_state"),
        "by_target_season": _summary(observed, "target_season"),
        "carry_forward_workload_diagnostic": {
            "hitting": _workload_error(
                observed, "source_batting_pa", "target_batting_pa"
            ),
            "pitching": _workload_error(
                observed, "source_pitching_bf", "target_pitching_bf"
            ),
        },
        "estimand_boundary": {
            "conditional_skill": "score component rates only when the player returns in that role",
            "joint_production": "score return probability x workload x conditional skill on every observed source player-season",
            "inactivity": "observed zero production, not a zero component-rate target",
            "right_censoring": "null and excluded from score",
        },
        "production_changed": False,
        "storage": storage,
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Complete next-season MLB transition denominator",
        "",
        "Status: denominator ready; no production model changed.",
        "",
        f"The retained 2009-2025 MLB history produces **{report['observed_player_seasons']:,}** "
        f"observed source player-seasons. **{report['observed_inactive_player_seasons']:,}** "
        "do not appear in MLB the next year. Those rows were absent from adjacent-season "
        "aging fits but are now retained for the joint production score.",
        "",
        f"Overall next-season MLB return rate is **{report['overall_return_rate']:.1%}**. "
        "The 2025-to-2026 rows remain right censored and cannot be scored.",
        "",
        "## Why this matters",
        "",
        "Conditional aging is still estimated only among players with a valid next-season "
        "rate. The final score, however, must multiply that skill estimate by separately "
        "predicted return and workload and compare with every observed player, including "
        "zero-production non-returners. This prevents the aging test from silently assuming "
        "that every source-season player survives.",
        "",
        "## Next gate",
        "",
        "Attach cutoff-safe age and incumbent opportunity forecasts, then compare no-aging, "
        "Tango aging and fitted component aging on identical rows using both conditional "
        "component loss and unconditional next-season production error. No playable value "
        "changes until both sides pass.",
        "",
    ]
    (args.output_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "observed_player_seasons": report["observed_player_seasons"],
        "inactive": report["observed_inactive_player_seasons"],
        "return_rate": report["overall_return_rate"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
