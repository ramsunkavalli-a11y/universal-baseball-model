#!/usr/bin/env python3
"""Select on 2024 and confirm league-within-level translations on 2025."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.league_component_translation import (
    build_league_translated_affiliated_profiles,
    fit_same_season_league_translation,
)
from universal_baseball.level_component_translation import (
    build_translated_affiliated_profiles,
    fit_same_season_component_translation,
    score_component_profiles,
)


SOURCE = Path("reports/generated/affiliated-skill-source/tables")
CONTEXT = Path("reports/generated/affiliated-team-context/tables/affiliated-team-context.parquet")
OUTPUT = Path("reports/generated/affiliated-league-translation-audit")
PRIOR_GRID = (50.0, 100.0, 250.0, 500.0, 1000.0, 2500.0)
HITTER_COMPONENTS = ("ubb", "hbp", "single", "double", "triple", "hr", "other")
PITCHER_COMPONENTS = ("so", "ubb", "hbp", "hr", "other")


def _hitter_components(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        (pl.col("hits") - pl.col("doubles") - pl.col("triples") - pl.col("home_runs")).alias(
            "single"
        ),
        pl.col("doubles").alias("double"),
        pl.col("triples").alias("triple"),
        pl.col("home_runs").alias("hr"),
        pl.col("hit_by_pitch").alias("hbp"),
    ).with_columns(
        (pl.col("plate_appearances") - pl.sum_horizontal(*HITTER_COMPONENTS[:-1])).alias(
            "other"
        )
    )


def _pitcher_components(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        pl.col("strike_outs").alias("so"),
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        pl.col("hit_batters").alias("hbp"),
        pl.col("home_runs").alias("hr"),
    ).with_columns(
        (pl.col("batters_faced") - pl.sum_horizontal(*PITCHER_COMPONENTS[:-1])).alias("other")
    )


def _with_context(frame: pl.DataFrame, context: pl.DataFrame) -> pl.DataFrame:
    joined = frame.filter(pl.col("season") <= 2025).join(
        context.select("season", "team_id", "sport_id", "league_id"),
        on=["season", "team_id", "sport_id"],
        how="left",
        validate="m:1",
    )
    if joined.filter(pl.col("league_id").is_null()).height:
        raise ValueError("affiliated league audit has unmatched context rows")
    return joined


def _players_and_target(
    source: pl.DataFrame, *, cutoff: int, target_season: int, exposure: str
) -> tuple[pl.DataFrame, pl.DataFrame]:
    prior = source.filter(pl.col("season") <= cutoff)
    evidence = prior.group_by("player_id").agg(
        pl.col(exposure).sum().alias("all_exposure"),
        pl.col(exposure).filter(pl.col("level_group") == "MLB").sum().alias("mlb_exposure"),
    )
    players = evidence.filter(
        (pl.col("all_exposure") > 0) & (pl.col("mlb_exposure") == 0)
    ).select("player_id")
    target = source.filter(
        (pl.col("season") == target_season) & (pl.col("level_group") == "MLB")
    )
    return players, target


def _fold(
    source: pl.DataFrame,
    *,
    target_season: int,
    exposure: str,
    components: tuple[str, ...],
    regression_exposure: float,
    league_prior_exposure: float,
) -> dict[str, object]:
    cutoff = target_season - 1
    completed = tuple(range(2023, cutoff + 1))
    prior = source.filter(pl.col("season") <= cutoff)
    players, target = _players_and_target(
        source, cutoff=cutoff, target_season=target_season, exposure=exposure
    )
    level_fit = fit_same_season_component_translation(
        prior,
        exposure_column=exposure,
        component_columns=components,
        completed_seasons=completed,
    )
    level_prediction = build_translated_affiliated_profiles(
        players,
        prior,
        level_fit.offsets,
        exposure_column=exposure,
        component_columns=components,
        current_season=cutoff,
        reference_season=cutoff,
        regression_exposure=regression_exposure,
    )
    league_fit = fit_same_season_league_translation(
        prior,
        exposure_column=exposure,
        component_columns=components,
        completed_seasons=completed,
        league_prior_exposure=league_prior_exposure,
    )
    league_prediction = build_league_translated_affiliated_profiles(
        players,
        prior,
        league_fit.offsets,
        exposure_column=exposure,
        component_columns=components,
        current_season=cutoff,
        reference_season=cutoff,
        regression_exposure=regression_exposure,
    )
    level_score = score_component_profiles(
        level_prediction, target, exposure_column=exposure, component_columns=components
    )
    league_score = score_component_profiles(
        league_prediction, target, exposure_column=exposure, component_columns=components
    )
    return {
        "target_season": target_season,
        "league_prior_exposure": league_prior_exposure,
        "forecast_population_players": players.height,
        "scored_players": league_score["players"],
        "fit_metrics": league_fit.metrics,
        "level_score": level_score,
        "league_score": league_score,
        "league_minus_level_log_loss": float(league_score["component_log_loss"])
        - float(level_score["component_log_loss"]),
        "league_minus_level_brier": float(league_score["component_brier_score"])
        - float(level_score["component_brier_score"]),
    }


def _audit_component(
    source: pl.DataFrame,
    *,
    exposure: str,
    components: tuple[str, ...],
    regression_exposure: float,
) -> dict[str, object]:
    development = [
        _fold(
            source,
            target_season=2024,
            exposure=exposure,
            components=components,
            regression_exposure=regression_exposure,
            league_prior_exposure=prior,
        )
        for prior in PRIOR_GRID
    ]
    eligible = [row for row in development if float(row["league_minus_level_brier"]) <= 0]
    selected = min(
        eligible or development,
        key=lambda row: float(row["league_minus_level_log_loss"]),
    )
    confirmation = _fold(
        source,
        target_season=2025,
        exposure=exposure,
        components=components,
        regression_exposure=regression_exposure,
        league_prior_exposure=float(selected["league_prior_exposure"]),
    )
    passed = all(
        float(row[key]) < 0
        for row in (selected, confirmation)
        for key in ("league_minus_level_log_loss", "league_minus_level_brier")
    )
    return {
        "selection_rule": "lowest_2024_log_loss_among_nonworse_2024_brier_candidates",
        "development_grid": development,
        "selected_prior_exposure": selected["league_prior_exposure"],
        "selected_development": selected,
        "untouched_confirmation": confirmation,
        "promotion_gate_passed": passed,
    }


def main() -> int:
    context = pl.read_parquet(CONTEXT)
    hitters = _hitter_components(
        _with_context(pl.read_parquet(SOURCE / "affiliated_hitting_components.parquet"), context)
    )
    pitchers = _pitcher_components(
        _with_context(pl.read_parquet(SOURCE / "affiliated_pitching_components.parquet"), context)
    )
    report = {
        "report_schema_version": "0.1",
        "gate": "partially_pooled_league_within_level_translation",
        "development_target": 2024,
        "confirmation_target": 2025,
        "current_2026_used": False,
        "prior_grid": list(PRIOR_GRID),
        "hitter": _audit_component(
            hitters,
            exposure="plate_appearances",
            components=HITTER_COMPONENTS,
            regression_exposure=1200.0,
        ),
        "pitcher": _audit_component(
            pitchers,
            exposure="batters_faced",
            components=PITCHER_COMPONENTS,
            regression_exposure=800.0,
        ),
        "production_changed": False,
        "park_boundary": (
            "venue identity is complete, but a park effect is not inferred from identity alone; "
            "a home/away or game-context estimator remains required"
        ),
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    compact = {
        component: {
            "selected_prior_exposure": report[component]["selected_prior_exposure"],
            "development_log_loss_delta": report[component]["selected_development"][
                "league_minus_level_log_loss"
            ],
            "confirmation_log_loss_delta": report[component]["untouched_confirmation"][
                "league_minus_level_log_loss"
            ],
            "confirmation_brier_delta": report[component]["untouched_confirmation"][
                "league_minus_level_brier"
            ],
            "passed": report[component]["promotion_gate_passed"],
        }
        for component in ("hitter", "pitcher")
    }
    print(json.dumps(compact, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
