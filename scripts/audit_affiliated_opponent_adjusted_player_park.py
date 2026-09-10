#!/usr/bin/env python3
"""Test opponent-adjusted component parks on future MLB player lines."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from audit_affiliated_component_park_factors import (
    HITTER_COMPONENTS,
    PITCHER_COMPONENTS,
    _hitter_components,
    _pitcher_components,
)
from audit_affiliated_opponent_adjusted_park_factors import (
    _hitter_as_pitcher_opponents,
    _pitcher_as_hitter_outcomes,
)
from audit_affiliated_player_park_adjustment import _fold, _mlb
from universal_baseball.affiliated_component_park_factor import (
    build_component_park_observations,
    build_schedule_opponent_adjustments,
)


ROOT = Path("reports/generated")
SPLITS = ROOT / "affiliated-home-away-components/tables"
SKILL = ROOT / "affiliated-skill-source/tables"
CONTEXT = ROOT / "affiliated-team-context/tables/affiliated-team-context.parquet"
GAMES = ROOT / "affiliated-game-context/tables/affiliated-game-context.parquet"
REPORT_JSON = Path("docs/affiliated-opponent-adjusted-player-park-result.json")
REPORT_MD = Path("docs/affiliated-opponent-adjusted-player-park-result.md")


def _one(
    split_source: pl.DataFrame, opponent: pl.DataFrame, mlb: pl.DataFrame,
    context: pl.DataFrame, games: pl.DataFrame, *, exposure: str,
    opponent_exposure: str, components: tuple[str, ...], regression: float,
) -> dict[str, object]:
    adjustments = build_schedule_opponent_adjustments(
        games, opponent, exposure_column=opponent_exposure,
        component_columns=components,
    )
    observations = build_component_park_observations(
        split_source, context, exposure_column=exposure,
        component_columns=components, opponent_adjustments=adjustments,
    )
    development = _fold(
        split_source, mlb, context, target_season=2024, exposure=exposure,
        components=components, regression_exposure=regression,
        park_prior=5000.0, park_observations=observations,
    )
    confirmation = _fold(
        split_source, mlb, context, target_season=2025, exposure=exposure,
        components=components, regression_exposure=regression,
        park_prior=5000.0, park_observations=observations,
    )
    passed = all(
        row["park_minus_baseline_log_loss"] < 0
        and row["park_minus_baseline_brier"] <= 0
        for row in (development, confirmation)
    )
    return {
        "development": development, "untouched_confirmation": confirmation,
        "promotion_gate_passed": passed,
    }


def main() -> int:
    context = pl.read_parquet(CONTEXT)
    games = pl.read_parquet(GAMES)
    hitter_raw = pl.read_parquet(SPLITS / "affiliated-hitter-home-away.parquet")
    pitcher_raw = pl.read_parquet(SPLITS / "affiliated-pitcher-home-away.parquet")
    hitter = _hitter_components(hitter_raw)
    pitcher = _pitcher_components(pitcher_raw)
    hitter_mlb = _mlb(
        _hitter_components(pl.read_parquet(SKILL / "affiliated_hitting_components.parquet")),
        exposure="plate_appearances", components=HITTER_COMPONENTS,
    )
    pitcher_mlb = _mlb(
        _pitcher_components(pl.read_parquet(SKILL / "affiliated_pitching_components.parquet")),
        exposure="batters_faced", components=PITCHER_COMPONENTS,
    )
    report = {
        "report_schema_version": "0.1",
        "status": "opponent_adjusted_player_park_outer_test_complete",
        "hitter": _one(
            hitter, _pitcher_as_hitter_outcomes(pitcher_raw), hitter_mlb,
            context, games, exposure="plate_appearances",
            opponent_exposure="batters_faced", components=HITTER_COMPONENTS,
            regression=1200.0,
        ),
        "pitcher": _one(
            pitcher, _hitter_as_pitcher_opponents(hitter_raw), pitcher_mlb,
            context, games, exposure="batters_faced",
            opponent_exposure="plate_appearances", components=PITCHER_COMPONENTS,
            regression=800.0,
        ),
        "current_2026_used": False, "production_changed": False,
        "outside_fv_used": False,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    def line(name: str) -> str:
        value = report[name]
        d, c = value["development"], value["untouched_confirmation"]
        return (
            f"| {name.title()} | {d['park_minus_baseline_log_loss']:+.6f} | "
            f"{d['park_minus_baseline_brier']:+.6f} | "
            f"{c['park_minus_baseline_log_loss']:+.6f} | "
            f"{c['park_minus_baseline_brier']:+.6f} | "
            f"{'Pass' if value['promotion_gate_passed'] else 'Reject'} |"
        )
    REPORT_MD.write_text(f"""# Opponent-adjusted player park test

Status: future-player gate complete; no current value changed.

Exact player home exposure is neutralized with component park effects after correcting
each team-season for its actual home and road opponent mix. The full level translation
is refit at each cutoff and scored on next-season MLB player components. Negative
deltas are better.

| Group | 2024 log-loss delta | 2024 Brier delta | 2025 log-loss delta | 2025 Brier delta | Decision |
|---|---:|---:|---:|---:|---|
{line('hitter')}
{line('pitcher')}

Schedule opponents are game-weighted, not exact matchup-PA weighted. Both time-ordered
years and both proper scores must improve before any current player rate can change.
No outside FV enters the test.
""", encoding="utf-8")
    print(json.dumps({name: report[name] for name in ("hitter", "pitcher")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
