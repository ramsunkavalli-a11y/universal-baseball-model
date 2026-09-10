#!/usr/bin/env python3
"""Select on 2024 and confirm on 2025 partially pooled MiLB park factors."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.affiliated_park_factor import (
    build_venue_season_observations,
    fit_park_factors,
    score_park_factors,
)
from universal_baseball.storage import write_canonical_parquet


PRIORS = (25.0, 50.0, 100.0, 200.0, 400.0)
ROOT = Path("reports/generated/affiliated-game-context")
OUTPUT = Path("reports/generated/affiliated-park-factors")
REPORT_JSON = Path("docs/affiliated-park-factor-result.json")
REPORT_MD = Path("docs/affiliated-park-factor-result.md")


def main() -> int:
    games = pl.read_parquet(ROOT / "tables/affiliated-game-context.parquet")
    observations = build_venue_season_observations(games)
    development = {}
    for prior in PRIORS:
        factors = fit_park_factors(observations, through_season=2023, prior_games=prior)
        development[str(prior)] = score_park_factors(
            observations, factors, season=2024
        )
    passing = [
        prior for prior in PRIORS
        if development[str(prior)]["candidate_rmse"] < development[str(prior)]["baseline_rmse"]
        and development[str(prior)]["candidate_mae"] <= development[str(prior)]["baseline_mae"]
    ]
    selected = min(
        passing,
        key=lambda prior: development[str(prior)]["candidate_rmse"],
        default=None,
    )
    selected_for_scoring = selected if selected is not None else PRIORS[-1]
    final_factors = fit_park_factors(
        observations, through_season=2024, prior_games=selected_for_scoring
    )
    confirmation = score_park_factors(
        observations, final_factors, season=2025
    )
    promoted = bool(
        selected is not None
        and confirmation["candidate_rmse"] < confirmation["baseline_rmse"]
        and confirmation["candidate_mae"] <= confirmation["baseline_mae"]
    )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        final_factors, OUTPUT / "park-factors-through-2024.parquet",
        table_name="affiliated_park_factors_through_2024",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "status": "affiliated_park_factor_outer_test_complete",
        "method": "home game total runs per scheduled nine divided by the same team's road-game rate; venue effects partially pooled to 1.0",
        "development_season": 2024,
        "confirmation_season": 2025,
        "prior_game_candidates": list(PRIORS),
        "development": development,
        "selected_prior_games": selected,
        "confirmation": confirmation,
        "decision": {
            "park_factor_source_promoted": promoted,
            "current_player_rates_changed": False,
        },
        "coverage": {
            "source_games": games.height,
            "venue_season_team_observations": observations.height,
            "final_factor_venues": final_factors.height,
        },
        "storage": storage,
        "boundaries": {
            "team_environment_controlled_by_road_games": True,
            "scheduled_innings_used": True,
            "opponent_strength_modeled": False,
            "weather_or_altitude_feature_used": False,
            "outside_fv_used": False,
        },
    }
    REPORT_JSON.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    d = development[str(selected_for_scoring)]
    REPORT_MD.write_text(
        f"""# Affiliated park-factor result

Status: {'source promoted for player-rate integration research' if promoted else 'candidate rejected; level-only translation retained'}.

The test estimates a venue effect from total runs in a team's home games divided by
total runs in that same team's road games. Venue estimates are shrunk toward neutral.
The shrinkage amount was selected on 2024, then frozen and checked on 2025.

| Period | Baseline MAE | Park MAE | Baseline RMSE | Park RMSE |
|---|---:|---:|---:|---:|
| 2024 development | {d['baseline_mae']:.4f} | {d['candidate_mae']:.4f} | {d['baseline_rmse']:.4f} | {d['candidate_rmse']:.4f} |
| 2025 confirmation | {confirmation['baseline_mae']:.4f} | {confirmation['candidate_mae']:.4f} | {confirmation['baseline_rmse']:.4f} | {confirmation['candidate_rmse']:.4f} |

Selected prior: {selected if selected is not None else 'none'} games. The source covers
{games.height:,} official games and {final_factors.height:,} venues in the final fit.

This validates only persistence of the run environment. It does not yet authorize a
player projection change: the next step must convert the full-game factor to a player
home/road exposure adjustment and show improvement in translated component rates.
Opponent strength, weather, and altitude are not separately modeled.
""",
        encoding="utf-8",
    )
    print(json.dumps({"selected_prior_games": selected, "promoted": promoted, "development": d, "confirmation": confirmation}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
