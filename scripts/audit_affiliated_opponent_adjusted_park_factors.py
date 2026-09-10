#!/usr/bin/env python3
"""Test component park effects after controlling actual opponent mix."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from audit_affiliated_component_park_factors import (
    HITTER_COMPONENTS,
    PITCHER_COMPONENTS,
    PRIORS,
    _hitter_components,
    _pitcher_components,
)
from universal_baseball.affiliated_component_park_factor import (
    build_component_park_observations,
    build_schedule_opponent_adjustments,
    fit_component_park_factors,
    score_component_park_factors,
)
from universal_baseball.storage import write_canonical_parquet


ROOT = Path("reports/generated")
SPLITS = ROOT / "affiliated-home-away-components/tables"
CONTEXT = ROOT / "affiliated-team-context/tables/affiliated-team-context.parquet"
GAMES = ROOT / "affiliated-game-context/tables/affiliated-game-context.parquet"
OUTPUT = ROOT / "affiliated-opponent-adjusted-park-factors"
REPORT_JSON = Path("docs/affiliated-opponent-adjusted-park-factor-result.json")
REPORT_MD = Path("docs/affiliated-opponent-adjusted-park-factor-result.md")


def _pitcher_as_hitter_outcomes(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        pl.col("hit_batters").alias("hbp"),
        (pl.col("hits") - pl.col("doubles") - pl.col("triples") - pl.col("home_runs")).alias("single"),
        pl.col("doubles").alias("double"), pl.col("triples").alias("triple"),
        pl.col("home_runs").alias("hr"),
    ).with_columns(
        (pl.col("batters_faced") - pl.sum_horizontal(*HITTER_COMPONENTS[:-1])).alias("other")
    )


def _hitter_as_pitcher_opponents(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        pl.col("strike_outs").alias("so"),
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        pl.col("hit_by_pitch").alias("hbp"), pl.col("home_runs").alias("hr"),
    ).with_columns(
        (pl.col("plate_appearances") - pl.sum_horizontal(*PITCHER_COMPONENTS[:-1])).alias("other")
    )


def _one(
    observed: pl.DataFrame, opponent: pl.DataFrame, context: pl.DataFrame,
    games: pl.DataFrame, *, exposure: str, opponent_exposure: str,
    components: tuple[str, ...],
) -> dict[str, object]:
    adjustment = build_schedule_opponent_adjustments(
        games, opponent, exposure_column=opponent_exposure,
        component_columns=components,
    )
    observations = build_component_park_observations(
        observed, context, exposure_column=exposure,
        component_columns=components, opponent_adjustments=adjustment,
    )
    development = {}
    for prior in PRIORS:
        factors = fit_component_park_factors(
            observations, through_season=2023,
            component_columns=components, prior_exposure=prior,
        )
        development[str(prior)] = score_component_park_factors(
            observations, factors, season=2024, component_columns=components
        )
    eligible = [
        prior for prior in PRIORS
        if development[str(prior)]["candidate_brier"]
        <= development[str(prior)]["baseline_brier"]
    ]
    selected = min(
        eligible or PRIORS,
        key=lambda prior: development[str(prior)]["candidate_log_loss"],
    )
    factors = fit_component_park_factors(
        observations, through_season=2024,
        component_columns=components, prior_exposure=selected,
    )
    confirmation = score_component_park_factors(
        observations, factors, season=2025, component_columns=components
    )
    chosen = development[str(selected)]
    passed = all(
        row["candidate_log_loss"] < row["baseline_log_loss"]
        and row["candidate_brier"] <= row["baseline_brier"]
        for row in (chosen, confirmation)
    )
    return {
        "opponent_adjustment_team_seasons": adjustment.height,
        "park_observations": observations.height,
        "selected_prior_exposure": selected,
        "development_grid": development,
        "selected_development": chosen,
        "untouched_confirmation": confirmation,
        "outer_gate_passed": passed,
        "final_factors": factors,
    }


def main() -> int:
    context = pl.read_parquet(CONTEXT)
    games = pl.read_parquet(GAMES)
    hitter_raw = pl.read_parquet(SPLITS / "affiliated-hitter-home-away.parquet")
    pitcher_raw = pl.read_parquet(SPLITS / "affiliated-pitcher-home-away.parquet")
    hitter = _one(
        _hitter_components(hitter_raw), _pitcher_as_hitter_outcomes(pitcher_raw),
        context, games, exposure="plate_appearances",
        opponent_exposure="batters_faced", components=HITTER_COMPONENTS,
    )
    pitcher = _one(
        _pitcher_components(pitcher_raw), _hitter_as_pitcher_opponents(hitter_raw),
        context, games, exposure="batters_faced",
        opponent_exposure="plate_appearances", components=PITCHER_COMPONENTS,
    )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    storage = {}
    for name, value in (("hitter", hitter), ("pitcher", pitcher)):
        storage[name] = write_canonical_parquet(
            value.pop("final_factors"), OUTPUT / f"{name}-factors-through-2024.parquet",
            table_name=f"opponent_adjusted_{name}_park_factors_through_2024",
        ).as_record()
    report = {
        "report_schema_version": "0.1",
        "status": "opponent_adjusted_component_park_outer_test_complete",
        "development_season": 2024, "confirmation_season": 2025,
        "current_2026_used": False, "hitter": hitter, "pitcher": pitcher,
        "storage": storage,
        "decision": {"player_test_authorized": bool(
            hitter["outer_gate_passed"] or pitcher["outer_gate_passed"]
        ), "production_changed": False},
        "boundary": (
            "Opponent component quality is schedule-weighted by games, not exact "
            "matchup PA/BF; league-season centering and venue pooling remain active."
        ),
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    def line(name: str) -> str:
        value = report[name]
        d, c = value["selected_development"], value["untouched_confirmation"]
        return (
            f"| {name.title()} | {value['selected_prior_exposure']:.0f} | "
            f"{d['candidate_log_loss']-d['baseline_log_loss']:+.6f} | "
            f"{d['candidate_brier']-d['baseline_brier']:+.6f} | "
            f"{c['candidate_log_loss']-c['baseline_log_loss']:+.6f} | "
            f"{c['candidate_brier']-c['baseline_brier']:+.6f} | "
            f"{'Pass' if value['outer_gate_passed'] else 'Reject'} |"
        )
    REPORT_MD.write_text(f"""# Opponent-adjusted affiliated component parks

Status: outer environment test complete; no player value changed.

Each team's home-minus-away component line is corrected for the component quality of
the actual opponents on its home and road schedules. Effects remain centered within
league-season and pooled toward neutral. Prior strength is selected on 2024 and
checked unchanged on 2025. Negative deltas are better.

| Group | Prior | 2024 log-loss delta | 2024 Brier delta | 2025 log-loss delta | 2025 Brier delta | Decision |
|---|---:|---:|---:|---:|---:|---|
{line('hitter')}
{line('pitcher')}

Opponent profiles are weighted by games because exact matchup PA/BF is not present in
the season split source. This is more defensible than ignoring opponent mix, but a
passing environment test only authorizes the separate future-player gate.
""", encoding="utf-8")
    print(json.dumps({name: report[name] for name in ("hitter", "pitcher")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
