#!/usr/bin/env python3
"""Compare a matched-window UBM park fit with public FG and BA factors."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import polars as pl

from audit_affiliated_component_park_factors import HITTER_COMPONENTS, _hitter_components
from audit_affiliated_opponent_adjusted_park_factors import _pitcher_as_hitter_outcomes
from universal_baseball.affiliated_component_park_factor import (
    build_component_park_observations,
    build_schedule_opponent_adjustments,
    fit_component_park_factors,
)
from universal_baseball.park_factor_comparison import (
    compare_park_indexes,
    component_probability_indexes,
    unhalve_full_park_index,
)


W_OBA_WEIGHTS_2023 = {
    "ubb": 0.696,
    "hbp": 0.726,
    "single": 0.883,
    "double": 1.244,
    "triple": 1.569,
    "hr": 2.004,
    "other": 0.0,
}
BA_LEVEL_SPORT = {"AAA": 11, "AA": 12, "A+": 13, "A": 14}
COMPONENT_MAP = {
    "single": "1b",
    "double": "2b",
    "triple": "3b",
    "hr": "hr",
}
BA_ALIASES = {
    "okla city": "oklahoma city",
    "nw arkansas": "northwest arkansas",
    "r cucamonga": "rancho cucamonga",
    "w michigan": "west michigan",
}


def _name_key(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    return BA_ALIASES.get(cleaned, cleaned)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--ba-csv", type=Path, required=True)
    parser.add_argument("--fg-csv", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/park-factor-external-comparison"),
    )
    return parser.parse_args()


def _matched_window_fit(source_root: Path) -> tuple[pl.DataFrame, pl.DataFrame]:
    tables = source_root / "reports/generated"
    split_root = tables / "affiliated-home-away-components/tables"
    context = pl.read_parquet(
        tables / "affiliated-team-context/tables/affiliated-team-context.parquet"
    )
    games = pl.read_parquet(
        tables / "affiliated-game-context/tables/affiliated-game-context.parquet"
    )
    hitter_raw = pl.read_parquet(split_root / "affiliated-hitter-home-away.parquet")
    pitcher_raw = pl.read_parquet(split_root / "affiliated-pitcher-home-away.parquet")
    hitter = _hitter_components(hitter_raw)
    opponent = _pitcher_as_hitter_outcomes(pitcher_raw)
    adjustment = build_schedule_opponent_adjustments(
        games,
        opponent,
        exposure_column="batters_faced",
        component_columns=HITTER_COMPONENTS,
    )
    observations = build_component_park_observations(
        hitter,
        context,
        exposure_column="plate_appearances",
        component_columns=HITTER_COMPONENTS,
        opponent_adjustments=adjustment,
    ).filter(pl.col("season").is_between(2022, 2023))
    factors = fit_component_park_factors(
        observations,
        through_season=2023,
        component_columns=HITTER_COMPONENTS,
        prior_exposure=5000.0,
    )
    totals = (
        hitter.filter(pl.col("season").is_between(2022, 2023))
        .select(*HITTER_COMPONENTS)
        .sum()
        .to_dicts()[0]
    )
    denominator = sum(float(totals[value]) for value in HITTER_COMPONENTS)
    reference = {
        value: float(totals[value]) / denominator for value in HITTER_COMPONENTS
    }
    indexes = component_probability_indexes(
        factors,
        reference_probabilities=reference,
        outcome_weights=W_OBA_WEIGHTS_2023,
    )
    names = (
        context.filter(
            (pl.col("season") == 2023)
            & pl.col("sport_id").is_in([1, 11, 12, 13, 14])
        )
        .select(
            "venue_id", "sport_id", "team_name", "venue_name", "league_name"
        )
        .unique("venue_id")
    )
    return indexes.join(names, on="venue_id", how="inner", validate="1:1"), observations


def _attach_ba(ubm: pl.DataFrame, path: Path) -> pl.DataFrame:
    ba = pl.read_csv(path).with_columns(
        pl.col("level").replace_strict(BA_LEVEL_SPORT).cast(pl.Int64).alias("sport_id")
    )
    ubm_rows = ubm.filter(pl.col("sport_id").is_in(list(BA_LEVEL_SPORT.values())))
    candidates: list[dict[str, object]] = []
    for external in ba.iter_rows(named=True):
        key = _name_key(str(external["team"]))
        matches = [
            row
            for row in ubm_rows.filter(pl.col("sport_id") == external["sport_id"])
            .iter_rows(named=True)
            if _name_key(str(row["team_name"])).startswith(key)
        ]
        if len(matches) != 1:
            continue
        row = {**matches[0], "external_team": external["team"], "source": "BA"}
        for column in ("woba", "1b", "2b", "3b", "hr"):
            row[f"external_{column}_index"] = float(external[column])
        candidates.append(row)
    return pl.DataFrame(candidates)


def _attach_fg(ubm: pl.DataFrame, path: Path) -> pl.DataFrame:
    fg = pl.read_csv(path)
    mlb = ubm.filter(pl.col("sport_id") == 1)
    rows: list[dict[str, object]] = []
    for external in fg.iter_rows(named=True):
        key = _name_key(str(external["team"]))
        matches = [
            row
            for row in mlb.iter_rows(named=True)
            if _name_key(str(row["team_name"])).endswith(key)
        ]
        if len(matches) != 1:
            continue
        row = {**matches[0], "external_team": external["team"], "source": "FG"}
        for column in ("1b", "2b", "3b", "hr"):
            row[f"external_{column}_index"] = unhalve_full_park_index(
                float(external[column])
            )
        rows.append(row)
    return pl.DataFrame(rows)


def _summaries(source: str, overlap: pl.DataFrame) -> dict[str, object]:
    result: dict[str, object] = {"matched_parks": overlap.height, "components": {}}
    for ubm_component, external_component in COMPONENT_MAP.items():
        result["components"][ubm_component] = compare_park_indexes(
            overlap,
            ubm_column=f"ubm_{ubm_component}_index",
            external_column=f"external_{external_component}_index",
        )
    if source == "BA":
        result["components"]["weighted_offense"] = compare_park_indexes(
            overlap,
            ubm_column="ubm_weighted_index",
            external_column="external_woba_index",
        )
    return result


def _largest_gaps(overlap: pl.DataFrame, source: str) -> list[dict[str, object]]:
    long_rows: list[dict[str, object]] = []
    components = dict(COMPONENT_MAP)
    if source == "BA":
        components["weighted"] = "woba"
    for row in overlap.iter_rows(named=True):
        for component, external in components.items():
            ubm_column = (
                "ubm_weighted_index" if component == "weighted"
                else f"ubm_{component}_index"
            )
            external_column = f"external_{external}_index"
            ubm_value = float(row[ubm_column])
            external_value = float(row[external_column])
            long_rows.append(
                {
                    "source": source,
                    "team": row["external_team"],
                    "venue": row["venue_name"],
                    "component": component,
                    "ubm_index": ubm_value,
                    "external_index": external_value,
                    "absolute_gap": abs(ubm_value - external_value),
                }
            )
    return sorted(long_rows, key=lambda row: float(row["absolute_gap"]), reverse=True)[:15]


def main() -> int:
    args = _arguments()
    ubm, observations = _matched_window_fit(args.source_root)
    ba = _attach_ba(ubm, args.ba_csv)
    fg = _attach_fg(ubm, args.fg_csv)
    fg_summary: dict[str, object]
    if fg.is_empty():
        fg_summary = {
            "matched_parks": 0,
            "status": "aggregate_affiliated_source_has_no_MLB_rows",
            "comparison_path": "use_event-level MLB adapter",
        }
        fg_gaps: list[dict[str, object]] = []
    else:
        fg_summary = _summaries("FG", fg)
        fg_gaps = _largest_gaps(fg, "FG")
    summary = {
        "status": "park_factor_external_comparison_complete",
        "ubm_window": [2022, 2023],
        "protected_2026_used": False,
        "ubm_observation_cells": observations.height,
        "ubm_method": (
            "league-season-centered opponent-adjusted component CLR; "
            "5000-exposure shrinkage; full in-park indexes"
        ),
        "BA": _summaries("BA", ba),
        "FG": fg_summary,
        "largest_differences": _largest_gaps(ba, "BA") + fg_gaps,
        "interpretation": {
            "agreement_standard": "direction and rank, not identical index",
            "BA_expected_scale_difference": (
                "BA is raw home/road; UBM adjusts opponent mix and strongly shrinks"
            ),
            "FG_expected_scale_difference": (
                "FG is five-year regressed and published halved; comparison unhalves FG"
            ),
            "UBM_distinctive_scope": (
                "component probabilities are exhaustive and normalized jointly within "
                "league-season"
            ),
        },
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "comparison.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    pl.concat([ba, fg], how="diagonal_relaxed").write_parquet(
        args.output_root / "matched-parks.parquet"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
