#!/usr/bin/env python3
"""Test exact-exposure park neutralization on future MLB player components."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.affiliated_component_park_factor import (
    build_component_park_observations,
    build_park_neutral_player_rows,
    fit_component_park_factors,
)
from universal_baseball.level_component_translation import (
    build_translated_affiliated_profiles,
    fit_same_season_component_translation,
    score_component_profiles,
)
from universal_baseball.opportunity_history_source import SPORT_LEVEL


ROOT = Path("reports/generated")
SPLITS = ROOT / "affiliated-home-away-components/tables"
SKILL = ROOT / "affiliated-skill-source/tables"
CONTEXT = ROOT / "affiliated-team-context/tables/affiliated-team-context.parquet"
REPORT_JSON = Path("docs/affiliated-player-park-adjustment-result.json")
REPORT_MD = Path("docs/affiliated-player-park-adjustment-result.md")
HITTER_COMPONENTS = ("ubb", "hbp", "single", "double", "triple", "hr", "other")
PITCHER_COMPONENTS = ("so", "ubb", "hbp", "hr", "other")


def _hitter(frame: pl.DataFrame, exposure: str = "plate_appearances") -> pl.DataFrame:
    return frame.with_columns(
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        (pl.col("hits") - pl.col("doubles") - pl.col("triples") - pl.col("home_runs")).alias("single"),
        pl.col("doubles").alias("double"), pl.col("triples").alias("triple"),
        pl.col("home_runs").alias("hr"), pl.col("hit_by_pitch").alias("hbp"),
    ).with_columns(
        (pl.col(exposure) - pl.sum_horizontal(*HITTER_COMPONENTS[:-1])).alias("other")
    )


def _pitcher(frame: pl.DataFrame, exposure: str = "batters_faced") -> pl.DataFrame:
    return frame.with_columns(
        pl.col("strike_outs").alias("so"),
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        pl.col("hit_batters").alias("hbp"), pl.col("home_runs").alias("hr"),
    ).with_columns(
        (pl.col(exposure) - pl.sum_horizontal(*PITCHER_COMPONENTS[:-1])).alias("other")
    )


def _minor_baseline(
    splits: pl.DataFrame, *, exposure: str, components: tuple[str, ...]
) -> pl.DataFrame:
    return splits.with_columns(
        pl.col("sport_id").replace_strict(SPORT_LEVEL).alias("level_group")
    ).group_by("season", "player_id", "level_group").agg(
        pl.col(exposure).sum().cast(pl.Float64).alias(exposure),
        *(pl.col(value).sum().cast(pl.Float64).alias(value) for value in components),
    )


def _mlb(
    source: pl.DataFrame, *, exposure: str, components: tuple[str, ...]
) -> pl.DataFrame:
    return source.filter(pl.col("level_group") == "MLB").group_by(
        "season", "player_id", "level_group"
    ).agg(
        pl.col(exposure).sum().cast(pl.Float64).alias(exposure),
        *(pl.col(value).sum().cast(pl.Float64).alias(value) for value in components),
    )


def _players_and_target(
    history: pl.DataFrame, *, cutoff: int, target_season: int, exposure: str
) -> tuple[pl.DataFrame, pl.DataFrame]:
    evidence = history.filter(pl.col("season") <= cutoff).group_by("player_id").agg(
        pl.col(exposure).sum().alias("all_exposure"),
        pl.col(exposure).filter(pl.col("level_group") == "MLB").sum().alias("mlb_exposure"),
    )
    players = evidence.filter(
        (pl.col("all_exposure") > 0) & (pl.col("mlb_exposure") == 0)
    ).select("player_id")
    target = history.filter(
        (pl.col("season") == target_season) & (pl.col("level_group") == "MLB")
    )
    return players, target


def _fold(
    split_source: pl.DataFrame, mlb_source: pl.DataFrame, context: pl.DataFrame,
    *, target_season: int, exposure: str, components: tuple[str, ...],
    regression_exposure: float, park_prior: float,
    park_observations: pl.DataFrame | None = None,
) -> dict[str, object]:
    cutoff = target_season - 1
    observations = park_observations
    if observations is None:
        observations = build_component_park_observations(
            split_source, context, exposure_column=exposure,
            component_columns=components,
        )
    factors = fit_component_park_factors(
        observations, through_season=cutoff,
        component_columns=components, prior_exposure=park_prior,
    )
    baseline_minor = _minor_baseline(
        split_source, exposure=exposure, components=components
    )
    candidate_minor = build_park_neutral_player_rows(
        split_source, context, factors, exposure_column=exposure,
        component_columns=components, level_by_sport=SPORT_LEVEL,
    )
    history_baseline = pl.concat([baseline_minor, mlb_source], how="vertical")
    history_candidate = pl.concat([candidate_minor, mlb_source], how="vertical")
    players, target = _players_and_target(
        history_baseline, cutoff=cutoff, target_season=target_season, exposure=exposure
    )
    completed = tuple(range(2023, cutoff + 1))
    predictions = {}
    scores = {}
    for name, history in (("baseline", history_baseline), ("park", history_candidate)):
        fit = fit_same_season_component_translation(
            history.filter(pl.col("season") <= cutoff),
            exposure_column=exposure, component_columns=components,
            completed_seasons=completed,
        )
        predictions[name] = build_translated_affiliated_profiles(
            players, history.filter(pl.col("season") <= cutoff), fit.offsets,
            exposure_column=exposure, component_columns=components,
            current_season=cutoff, reference_season=cutoff,
            regression_exposure=regression_exposure,
        )
        scores[name] = score_component_profiles(
            predictions[name], target,
            exposure_column=exposure, component_columns=components,
        )
    return {
        "target_season": target_season,
        "forecast_population_players": players.height,
        "scored_players": scores["park"]["players"],
        "baseline_score": scores["baseline"], "park_score": scores["park"],
        "park_minus_baseline_log_loss": (
            scores["park"]["component_log_loss"] - scores["baseline"]["component_log_loss"]
        ),
        "park_minus_baseline_brier": (
            scores["park"]["component_brier_score"] - scores["baseline"]["component_brier_score"]
        ),
    }


def _one(
    split_source: pl.DataFrame, mlb_source: pl.DataFrame, context: pl.DataFrame,
    *, exposure: str, components: tuple[str, ...], regression_exposure: float,
) -> dict[str, object]:
    development = _fold(
        split_source, mlb_source, context, target_season=2024,
        exposure=exposure, components=components,
        regression_exposure=regression_exposure, park_prior=5000.0,
    )
    confirmation = _fold(
        split_source, mlb_source, context, target_season=2025,
        exposure=exposure, components=components,
        regression_exposure=regression_exposure, park_prior=5000.0,
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
    hitter_splits = _hitter(pl.read_parquet(SPLITS / "affiliated-hitter-home-away.parquet"))
    pitcher_splits = _pitcher(pl.read_parquet(SPLITS / "affiliated-pitcher-home-away.parquet"))
    hitter_mlb = _mlb(
        _hitter(pl.read_parquet(SKILL / "affiliated_hitting_components.parquet")),
        exposure="plate_appearances", components=HITTER_COMPONENTS,
    )
    pitcher_mlb = _mlb(
        _pitcher(pl.read_parquet(SKILL / "affiliated_pitching_components.parquet")),
        exposure="batters_faced", components=PITCHER_COMPONENTS,
    )
    report = {
        "report_schema_version": "0.1",
        "status": "player_park_adjustment_outer_test_complete",
        "park_prior_exposure": 5000.0,
        "development_target": 2024, "confirmation_target": 2025,
        "current_2026_used": False,
        "hitter": _one(
            hitter_splits, hitter_mlb, context,
            exposure="plate_appearances", components=HITTER_COMPONENTS,
            regression_exposure=1200.0,
        ),
        "pitcher": _one(
            pitcher_splits, pitcher_mlb, context,
            exposure="batters_faced", components=PITCHER_COMPONENTS,
            regression_exposure=800.0,
        ),
        "production_changed": False,
        "outside_fv_used": False,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    def line(name: str) -> str:
        value = report[name]
        dev = value["development"]
        con = value["untouched_confirmation"]
        return (
            f"| {name.title()} | {dev['scored_players']} | "
            f"{dev['park_minus_baseline_log_loss']:+.6f} | "
            f"{dev['park_minus_baseline_brier']:+.6f} | {con['scored_players']} | "
            f"{con['park_minus_baseline_log_loss']:+.6f} | "
            f"{con['park_minus_baseline_brier']:+.6f} | "
            f"{'Pass' if value['promotion_gate_passed'] else 'Reject'} |"
        )
    REPORT_MD.write_text(f"""# Player-level affiliated park adjustment

Status: tested with no current player-value change.

Each player's exact home split is neutralized with the previously selected,
league-season-centered component park effect. His away split is retained. The level
translation is then refit using only data available at the forecast cutoff and scored
on next-season MLB components. Negative score deltas are better.

| Group | 2024 players | 2024 log-loss delta | 2024 Brier delta | 2025 players | 2025 log-loss delta | 2025 Brier delta | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
{line('hitter')}
{line('pitcher')}

The test uses no outside FV opinion and does not assume a 50/50 schedule. The park
factor is learned before each target year and applied only to observed home exposure.
Opponent mix is not yet modeled explicitly; failure of either time-ordered fold keeps
the current level-only player model unchanged.
""", encoding="utf-8")
    print(json.dumps({name: report[name] for name in ("hitter", "pitcher")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
