#!/usr/bin/env python3
"""Inventory supported four-year prospect career-state transitions."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_arrival import build_arrival_cohort
from universal_baseball.prospect_career_state import build_career_transition_rows


ROOT = Path("reports/generated")
SNAPSHOTS = (2018, 2019, 2021)
HORIZONS = (1, 2, 3, 4)
OUTPUT_JSON = Path("docs/prospect-career-transition-support-result.json")
OUTPUT_MD = Path("docs/prospect-career-transition-support-result.md")


def _history_stats() -> pl.DataFrame:
    paths = sorted((ROOT / "opportunity-history-sources-v2/tables").glob(
        "*/affiliated_season_stats.parquet"
    ))
    return pl.concat([pl.read_parquet(path) for path in paths], how="vertical_relaxed")


def _one(player_type: str) -> dict[str, object]:
    history = ROOT / "opportunity-history-sources-v2/tables"
    snapshots = pl.read_parquet(history / f"{player_type}_snapshots.parquet")
    stats = _history_stats()
    membership = pl.read_parquet(
        ROOT / "opportunity-40man-history/tables/historical_40man_membership.parquet"
    )
    demographics = pl.read_parquet(
        ROOT / "player-demographics/tables/player-demographics.parquet"
    )
    skill = pl.read_parquet(
        ROOT / "phase2-arrival-skill-source/tables"
        / f"affiliated_{'hitting' if player_type == 'hitter' else 'pitching'}_components.parquet"
    )
    debut = pl.read_parquet(
        ROOT / "career-mlb-outcome-inventory-2009-2025/tables/people-debut-dates.parquet"
    )
    all_rows = []
    cohort_sizes = {}
    for year in SNAPSHOTS:
        cohorts = {
            horizon: build_arrival_cohort(
                snapshots, stats, membership, skill, debut,
                snapshot_year=year, horizon=horizon, player_type=player_type,
                demographics=demographics,
            )
            for horizon in HORIZONS
        }
        cohort_sizes[str(year)] = cohorts[1].height
        all_rows.append(build_career_transition_rows(cohorts, snapshot_year=year))
    rows = pl.concat(all_rows, how="vertical")
    counts = rows.group_by("from_state", "to_state").agg(
        pl.len().alias("transitions"),
        pl.col("player_id").n_unique().alias("distinct_players"),
    ).sort("from_state", "to_state").to_dicts()
    support = rows.group_by("from_state").agg(
        pl.len().alias("risk_rows"),
        pl.col("player_id").n_unique().alias("distinct_players"),
        (pl.col("to_state") != pl.col("from_state")).sum().alias("advancements"),
    ).sort("from_state").to_dicts()
    return {
        "snapshot_cohort_sizes": cohort_sizes,
        "transition_rows": rows.height,
        "distinct_players": rows.get_column("player_id").n_unique(),
        "by_transition": counts,
        "origin_state_support": support,
    }


def main() -> int:
    report = {
        "report_schema_version": "0.1",
        "status": "career_transition_support_inventory_complete",
        "snapshots": list(SNAPSHOTS), "horizons": list(HORIZONS),
        "outcome_years": [2019, 2020, 2021, 2022, 2023, 2024, 2025],
        "current_2026_used": False,
        "hitter": _one("hitter"), "pitcher": _one("pitcher"),
        "production_changed": False,
    }
    OUTPUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    def support_rows(name: str) -> str:
        return "\n".join(
            f"| {name.title()} | {row['from_state']} | {row['risk_rows']:,} | "
            f"{row['distinct_players']:,} | {row['advancements']:,} |"
            for row in report[name]["origin_state_support"]
        )
    OUTPUT_MD.write_text(f"""# Prospect career-transition support

Status: four-year transition training inventory complete.

The 2018, 2019 and 2021 pre-MLB cohorts are followed one season at a time for four
years. Career milestones are monotone: no MLB, fringe MLB, meaningful MLB and
established MLB. A row cannot move backward, and players who do not advance remain
in the risk set.

| Group | Origin state | Risk rows | Distinct players | Advancements |
|---|---|---:|---:|---:|
{support_rows('hitter')}
{support_rows('pitcher')}

These counts decide how much pooling later hazards require. They do not fit a model
or change a player value. The shortened 2020 outcome remains scaled under the
existing workload rule; the 2020 snapshot itself is not used.
""", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
