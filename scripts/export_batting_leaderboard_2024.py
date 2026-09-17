#!/usr/bin/env python
"""Export the frozen 2024 pure-batting leaderboard.

Ranks hitters only by the frozen B2 batting profile, converted with the binding
Player Value v1 2024 pooled-MLB RE24 reference. Every hitter is evaluated at a
constant 600 PA, so Playing Time, defense, baserunning, position, and WAR do not
enter the ordering.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import polars as pl
import requests

from universal_baseball.player_value_batting_runs import (
    build_v1_mlb_batting_reference,
    calculate_v1_projected_batting_runs,
)

REFERENCE_SEASON = 2024
RATE_PA = 600.0


def _resolve_names(player_ids: Iterable[int]) -> dict[int, str]:
    """Resolve display names from MLB's public people endpoint; IDs remain canonical."""
    ids = sorted(set(int(value) for value in player_ids))
    names: dict[int, str] = {}
    for start in range(0, len(ids), 100):
        batch = ids[start : start + 100]
        try:
            response = requests.get(
                "https://statsapi.mlb.com/api/v1/people",
                params={"personIds": ",".join(str(value) for value in batch)},
                timeout=30,
            )
            response.raise_for_status()
            for person in response.json().get("people", []):
                if person.get("id") is not None and person.get("fullName"):
                    names[int(person["id"])] = str(person["fullName"])
        except requests.RequestException:
            # Names are presentation metadata only; never block the frozen model export.
            continue
    return names


def build_leaderboard(*, b2_profile: Path, performance_root: Path) -> pl.DataFrame:
    reference = build_v1_mlb_batting_reference(
        pl.read_parquet(performance_root / "tables/batting_performance_summary_2024_mlb.parquet"),
        pl.read_parquet(performance_root / "tables/batting_performance_bins_2024_mlb.parquet"),
        pl.read_parquet(performance_root / "tables/league_bin_values_2024_mlb.parquet"),
        season=REFERENCE_SEASON,
    )
    profile = pl.read_parquet(b2_profile)
    required = {"player_id", "core_bin", "baseline2_latent_probability"}
    missing = sorted(required - set(profile.columns))
    if missing:
        raise ValueError(f"frozen B2 profile missing required columns: {missing}")

    rows: list[dict[str, object]] = []
    for player_key, group in profile.group_by("player_id"):
        player_id = int(player_key[0])
        probabilities = {
            str(row["core_bin"]): float(row["baseline2_latent_probability"])
            for row in group.iter_rows(named=True)
        }
        projection = calculate_v1_projected_batting_runs(
            probabilities,
            projected_expected_mlb_pa=RATE_PA,
            reference=reference,
        )
        rows.append(
            {
                "player_id": player_id,
                "runs_above_mlb_per_600_pa": projection.projected_batting_runs_above_mlb_reference,
                "projected_core_run_value_per_event": projection.projected_core_run_value_per_event,
                "mlb_reference_core_run_value_per_event": projection.mlb_reference_core_run_value_per_event,
                "mlb_reference_core_event_rate_per_pa": projection.mlb_reference_core_event_rate_per_pa,
                "batting_run_conversion_id": projection.batting_run_conversion_id,
            }
        )

    leaderboard = pl.DataFrame(rows).sort(
        ["runs_above_mlb_per_600_pa", "player_id"], descending=[True, False]
    )
    leaderboard = leaderboard.with_row_index("rank", offset=1)
    names = _resolve_names(leaderboard.get_column("player_id").to_list())
    leaderboard = leaderboard.with_columns(
        pl.col("player_id")
        .map_elements(lambda value: names.get(int(value), ""), return_dtype=pl.String)
        .alias("player_name")
    ).select(
        "rank",
        "player_id",
        "player_name",
        "runs_above_mlb_per_600_pa",
        "projected_core_run_value_per_event",
        "mlb_reference_core_run_value_per_event",
        "mlb_reference_core_event_rate_per_pa",
        "batting_run_conversion_id",
    )
    return leaderboard


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--b2-profile", type=Path, required=True)
    parser.add_argument("--performance-root", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()

    leaderboard = build_leaderboard(
        b2_profile=args.b2_profile,
        performance_root=args.performance_root,
    )
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    leaderboard.write_csv(args.output_csv, float_precision=6)
    payload = {
        "projection_target_season": 2024,
        "rate_basis_pa": int(RATE_PA),
        "ranking_metric": "runs_above_mlb_per_600_pa",
        "player_count": leaderboard.height,
        "note": "Pure batting only: frozen B2 profile converted with the binding 2024 pooled-MLB RE24 reference; no Playing Time, defense, baserunning, position, or WAR inputs.",
        "players": leaderboard.to_dicts(),
    }
    args.output_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
