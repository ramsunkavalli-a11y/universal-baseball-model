#!/usr/bin/env python3
"""Fit a non-Statcast 2024 MLB event park model and compare it with FanGraphs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.event_context_park_model import fit_event_context_park_factors
from universal_baseball.hitter_v2_park import (
    project_schedule_venues,
    resolve_schedule_venue_duplicates,
)
from universal_baseball.park_factor_comparison import (
    compare_park_indexes,
    component_probability_indexes,
    unhalve_full_park_index,
)


COMPONENTS = ("ubb", "hbp", "single", "double", "triple", "hr", "other")
COMPONENT_MAP = {"single": "1b", "double": "2b", "triple": "3b", "hr": "hr"}
FG_ABBR = {
    "Angels": "LAA", "Orioles": "BAL", "Red Sox": "BOS",
    "White Sox": "CWS", "Guardians": "CLE", "Tigers": "DET",
    "Royals": "KC", "Twins": "MIN", "Yankees": "NYY",
    "Athletics": "OAK", "Mariners": "SEA", "Rays": "TB",
    "Rangers": "TEX", "Blue Jays": "TOR", "Diamondbacks": "AZ",
    "Braves": "ATL", "Cubs": "CHC", "Reds": "CIN", "Rockies": "COL",
    "Marlins": "MIA", "Astros": "HOU", "Dodgers": "LAD",
    "Brewers": "MIL", "Nationals": "WSH", "Mets": "NYM",
    "Phillies": "PHI", "Pirates": "PIT", "Cardinals": "STL",
    "Padres": "SD", "Giants": "SF",
}


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--savant-root", type=Path, required=True)
    parser.add_argument("--schedule-json", type=Path, required=True)
    parser.add_argument("--fg-csv", type=Path, required=True)
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/park-factor-external-comparison"),
    )
    return parser.parse_args()


def _events(root: Path, schedule_json: Path) -> pl.DataFrame:
    columns = [
        "game_date", "game_type", "game_pk", "at_bat_number", "events",
        "batter", "pitcher", "stand", "p_throws", "home_team",
    ]
    frames = [
        pl.scan_csv(path, infer_schema_length=1000).select(columns).filter(
            (pl.col("game_type") == "R") & pl.col("events").is_not_null()
        ).collect()
        for path in sorted(root.glob("*.csv"))
    ]
    if not frames:
        raise ValueError("no Savant CSV files found")
    events = pl.concat(frames, how="vertical_relaxed").unique(
        ["game_pk", "at_bat_number"], keep="first"
    )
    payload = json.loads(schedule_json.read_text(encoding="utf-8"))
    venues = resolve_schedule_venue_duplicates(
        project_schedule_venues(payload, season=2024, sport_id=1)
    ).filter(pl.col("venue_context_eligible"))
    outcome = (
        pl.when(pl.col("events") == "walk").then(pl.lit("ubb"))
        .when(pl.col("events") == "hit_by_pitch").then(pl.lit("hbp"))
        .when(pl.col("events") == "single").then(pl.lit("single"))
        .when(pl.col("events") == "double").then(pl.lit("double"))
        .when(pl.col("events") == "triple").then(pl.lit("triple"))
        .when(pl.col("events") == "home_run").then(pl.lit("hr"))
        .otherwise(pl.lit("other"))
    )
    return (
        events.join(
            venues.select("game_id", "venue_id", "venue_name"),
            left_on="game_pk", right_on="game_id", how="inner", validate="m:1",
        )
        .with_columns(
            pl.col("game_date").str.to_date(strict=False),
            pl.col("batter").cast(pl.Int64).alias("batter_id"),
            pl.col("pitcher").cast(pl.Int64).alias("pitcher_id"),
            pl.col("stand").alias("batter_side"),
            pl.col("p_throws").alias("pitcher_hand"),
            outcome.alias("outcome"),
        )
        .select(
            "game_date", "game_pk", "at_bat_number", "batter_id", "pitcher_id",
            "batter_side", "pitcher_hand", "venue_id", "venue_name", "home_team",
            "outcome",
        )
        .sort("game_date", "game_pk", "at_bat_number")
    )


def main() -> int:
    args = _arguments()
    events = _events(args.savant_root, args.schedule_json)
    fit = fit_event_context_park_factors(events, regularization_c=0.1)
    counts = events.group_by("outcome").len()
    total = counts["len"].sum()
    reference = {
        component: counts.filter(pl.col("outcome") == component).item(0, "len") / total
        for component in COMPONENTS
    }
    indexes = component_probability_indexes(
        fit.factors, reference_probabilities=reference
    )
    primary = (
        events.group_by("home_team", "venue_id", "venue_name").len()
        .sort("home_team", "len", descending=[False, True])
        .unique("home_team", keep="first")
    )
    ubm = indexes.join(primary, on="venue_id", how="inner", validate="1:1")
    fg = pl.read_csv(args.fg_csv).with_columns(
        pl.col("team").replace_strict(FG_ABBR).alias("home_team")
    )
    overlap = ubm.join(fg, on="home_team", how="inner", validate="1:1")
    for external in ("1b", "2b", "3b", "hr"):
        overlap = overlap.with_columns(
            pl.col(external).cast(pl.Float64).map_elements(
                unhalve_full_park_index, return_dtype=pl.Float64
            ).alias(f"external_{external}_index")
        )
    comparison = {
        component: compare_park_indexes(
            overlap,
            ubm_column=f"ubm_{component}_index",
            external_column=f"external_{external}_index",
        )
        for component, external in COMPONENT_MAP.items()
    }
    result = {
        "status": "mlb_event_park_fangraphs_comparison_complete",
        "season": 2024,
        "protected_2026_used": False,
        "events": events.height,
        "matched_primary_parks": overlap.height,
        "validation": fit.validation,
        "components": comparison,
        "method_difference": (
            "UBM is a one-season batter/pitcher/hand-adjusted multinomial event model; "
            "FanGraphs components are multi-year regressed and published half-season "
            "indexes, which were unhalved for this comparison."
        ),
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "mlb-fangraphs-comparison.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    overlap.write_parquet(args.output_root / "mlb-fangraphs-matched-parks.parquet")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
