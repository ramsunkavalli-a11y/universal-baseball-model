#!/usr/bin/env python3
"""Audit an explainable weak/older/low-level hitter negative control.

This is a model guardrail, not a player-value model.  It keeps every player in the
origin cohort, including players who never reach MLB, and asks how much later MLB
batting production followed a plainly weak age/level/performance profile.
"""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.historical_hitter_performance import (
    build_historical_hitter_performance_paths,
)
from universal_baseball.prospect_arrival import build_arrival_cohort


ORIGINS = (2018, 2021)
HORIZON = 4
MINIMUM_PA = 100.0
MINIMUM_AGE = 23.0
MAXIMUM_XBH_RATE = 0.06


def _history_stats(root: Path) -> pl.DataFrame:
    return pl.concat(
        [pl.read_parquet(path) for path in sorted(root.glob("*/affiliated_season_stats.parquet"))],
        how="vertical_relaxed",
    )


def _outcomes(
    cohort: pl.DataFrame,
    hitting: pl.DataFrame,
    *,
    origin: int,
    runs_per_win: float,
) -> pl.DataFrame:
    annual = (
        pl.DataFrame(
            [
                {
                    "path_player_id": int(player_id),
                    "player_type": "hitter",
                    "outcome_tier_v2": "unknown",
                    "career_role": "hitter",
                    "path_year": season - origin,
                    "source_season": season,
                    "adjusted_workload": 0.0,
                    "annual_role": "inactive",
                }
                for player_id in cohort["player_id"].to_list()
                for season in range(origin + 1, origin + HORIZON + 1)
            ]
        )
        .join(
            hitting.select(
                pl.col("player_id").alias("path_player_id"),
                pl.col("season").alias("source_season"),
                pl.col("batting_plate_appearances").cast(pl.Float64).alias("raw_pa"),
            ),
            on=["path_player_id", "source_season"],
            how="left",
            validate="m:1",
        )
        .with_columns(
            pl.when(pl.col("source_season") == 2020)
            .then(pl.col("raw_pa").fill_null(0.0) * 2.7)
            .otherwise(pl.col("raw_pa").fill_null(0.0))
            .alias("adjusted_workload"),
            pl.when(pl.col("raw_pa").fill_null(0.0) > 0)
            .then(pl.lit("hitter"))
            .otherwise(pl.lit("inactive"))
            .alias("annual_role"),
        )
        .drop("raw_pa")
    )
    return (
        build_historical_hitter_performance_paths(
            annual,
            hitting,
            runs_per_win=runs_per_win,
            shortened_2020_scale=2.7,
        )
        .group_by("path_player_id")
        .agg(
            pl.col("observed_component_war").sum().alias("later_component_war"),
            pl.col("adjusted_workload").sum().alias("later_mlb_pa"),
        )
        .rename({"path_player_id": "player_id"})
    )


def _metrics(frame: pl.DataFrame) -> dict[str, float | int]:
    positive = frame["later_component_war"].clip(0.0, None)
    return {
        "players": frame.height,
        "arrivals": int((frame["later_mlb_pa"] > 0).sum()),
        "arrival_rate": float((frame["later_mlb_pa"] > 0).mean()),
        "mean_later_component_war": float(frame["later_component_war"].mean()),
        "mean_positive_later_component_war": float(positive.mean()),
        "impact_rate_one_war": float((frame["later_component_war"] >= 1.0).mean()),
    }


def main() -> int:
    generated = Path("reports/generated")
    history_root = generated / "opportunity-history-sources-v2/tables"
    stats = _history_stats(history_root)
    membership = pl.read_parquet(
        generated / "opportunity-40man-history/tables/historical_40man_membership.parquet"
    )
    skill = pl.read_parquet(
        generated / "phase2-arrival-skill-source/tables/affiliated_hitting_components.parquet"
    )
    demographics = pl.read_parquet(
        generated / "player-demographics/tables/player-demographics.parquet"
    )
    debut = pl.read_parquet(
        generated / "career-mlb-outcome-inventory-2009-2025/tables/people-debut-dates.parquet"
    )
    hitting = pl.read_parquet(
        generated / "career-mlb-outcome-inventory-2009-2025/tables/mlb_hitting_components_2009_2025.parquet"
    )
    runs_per_win = float(
        json.loads(Path("docs/prospect-component-uncertainty-result.json").read_text())[
            "runs_per_win"
        ]
    )
    results: dict[str, object] = {}
    for origin in ORIGINS:
        cohort = build_arrival_cohort(
            pl.read_parquet(history_root / "hitter_snapshots.parquet"),
            stats,
            membership,
            skill,
            debut,
            snapshot_year=origin,
            horizon=HORIZON,
            player_type="hitter",
            demographics=demographics,
        )
        scored = (
            cohort.join(
                _outcomes(cohort, hitting, origin=origin, runs_per_win=runs_per_win),
                on="player_id",
                how="left",
                validate="1:1",
            )
            .with_columns(
                pl.col("later_component_war").fill_null(0.0),
                pl.col("later_mlb_pa").fill_null(0.0),
            )
        )
        negative = scored.filter(
            (pl.col("primary_level_tier") == "A_OR_BELOW")
            & (pl.col("age_years") >= MINIMUM_AGE)
            & (pl.col("current_milb_workload") >= MINIMUM_PA)
            & (pl.col("production_rate_4") <= MAXIMUM_XBH_RATE)
        )
        results[str(origin)] = {
            "all": _metrics(scored),
            "negative_control": _metrics(negative),
        }

    report = {
        "as_of_date": date.today().isoformat(),
        "status": "negative_control_evidence_not_value_model",
        "definition": {
            "primary_level": "A_OR_BELOW",
            "minimum_age": MINIMUM_AGE,
            "minimum_current_pa": MINIMUM_PA,
            "maximum_xbh_per_pa": MAXIMUM_XBH_RATE,
        },
        "horizon_years": HORIZON,
        "all_origin_players_retained": True,
        "nonarrivals_scored_zero": True,
        "results": results,
    }
    output = Path("docs/weak-low-level-hitter-negative-control-result.json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
