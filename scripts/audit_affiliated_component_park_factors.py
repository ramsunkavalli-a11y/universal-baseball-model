#!/usr/bin/env python3
"""Select on 2024 and confirm 2025 component-specific MiLB park effects."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.affiliated_component_park_factor import (
    build_component_park_observations,
    fit_component_park_factors,
    score_component_park_factors,
)
from universal_baseball.storage import write_canonical_parquet


ROOT = Path("reports/generated")
SOURCE = ROOT / "affiliated-home-away-components/tables"
CONTEXT = ROOT / "affiliated-team-context/tables/affiliated-team-context.parquet"
OUTPUT = ROOT / "affiliated-component-park-factors"
REPORT_JSON = Path("docs/affiliated-component-park-factor-result.json")
REPORT_MD = Path("docs/affiliated-component-park-factor-result.md")
PRIORS = (100.0, 250.0, 500.0, 1000.0, 2500.0, 5000.0)
HITTER_COMPONENTS = ("ubb", "hbp", "single", "double", "triple", "hr", "other")
PITCHER_COMPONENTS = ("so", "ubb", "hbp", "hr", "other")


def _hitter_components(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        (pl.col("hits") - pl.col("doubles") - pl.col("triples") - pl.col("home_runs")).alias("single"),
        pl.col("doubles").alias("double"), pl.col("triples").alias("triple"),
        pl.col("home_runs").alias("hr"), pl.col("hit_by_pitch").alias("hbp"),
    ).with_columns(
        (pl.col("plate_appearances") - pl.sum_horizontal(*HITTER_COMPONENTS[:-1])).alias("other")
    )


def _pitcher_components(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        pl.col("strike_outs").alias("so"),
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        pl.col("hit_batters").alias("hbp"), pl.col("home_runs").alias("hr"),
    ).with_columns(
        (pl.col("batters_faced") - pl.sum_horizontal(*PITCHER_COMPONENTS[:-1])).alias("other")
    )


def _one(
    frame: pl.DataFrame, context: pl.DataFrame, *, exposure: str,
    components: tuple[str, ...],
) -> dict[str, object]:
    observations = build_component_park_observations(
        frame, context, exposure_column=exposure, component_columns=components
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
        "observations": observations.height,
        "selected_prior_exposure": selected,
        "development_grid": development,
        "selected_development": chosen,
        "untouched_confirmation": confirmation,
        "promotion_gate_passed": passed,
        "final_factors": factors,
    }


def main() -> int:
    context = pl.read_parquet(CONTEXT)
    hitter = _one(
        _hitter_components(pl.read_parquet(SOURCE / "affiliated-hitter-home-away.parquet")),
        context, exposure="plate_appearances", components=HITTER_COMPONENTS,
    )
    pitcher = _one(
        _pitcher_components(pl.read_parquet(SOURCE / "affiliated-pitcher-home-away.parquet")),
        context, exposure="batters_faced", components=PITCHER_COMPONENTS,
    )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    storage = {}
    for name, value in (("hitter", hitter), ("pitcher", pitcher)):
        storage[name] = write_canonical_parquet(
            value.pop("final_factors"), OUTPUT / f"{name}-factors-through-2024.parquet",
            table_name=f"affiliated_{name}_component_park_factors_through_2024",
        ).as_record()
    report = {
        "report_schema_version": "0.1",
        "status": "component_park_outer_test_complete",
        "selection_rule": "lowest_2024_log_loss_among_nonworse_2024_brier_candidates",
        "development_season": 2024, "confirmation_season": 2025,
        "current_2026_used": False, "prior_exposure_candidates": list(PRIORS),
        "hitter": hitter, "pitcher": pitcher, "storage": storage,
        "decision": {
            "source_promoted": bool(hitter["promotion_gate_passed"] or pitcher["promotion_gate_passed"]),
            "current_player_rates_changed": False,
        },
        "boundaries": {
            "league_season_centered": True,
            "same_team_away_profile_baseline": True,
            "exact_player_home_away_source_available": True,
            "opponent_strength_explicitly_modeled": False,
            "outside_fv_used": False,
        },
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    def line(name: str) -> str:
        value = report[name]
        dev = value["selected_development"]
        con = value["untouched_confirmation"]
        return (
            f"| {name.title()} | {value['selected_prior_exposure']:.0f} | "
            f"{dev['candidate_log_loss']-dev['baseline_log_loss']:+.6f} | "
            f"{dev['candidate_brier']-dev['baseline_brier']:+.6f} | "
            f"{con['candidate_log_loss']-con['baseline_log_loss']:+.6f} | "
            f"{con['candidate_brier']-con['baseline_brier']:+.6f} | "
            f"{'Pass' if value['promotion_gate_passed'] else 'Reject'} |"
        )
    REPORT_MD.write_text(f"""# Affiliated component park-factor result

Status: outer source test complete; no player value changed.

Home and away player splits are aggregated to team-season components. Each park
effect is a home-minus-away centered log-ratio, centered again within league-season
and partially pooled toward neutral. The prior was selected on 2024; 2025 remained
untouched. Negative score deltas are better.

| Group | Prior | 2024 log-loss delta | 2024 Brier delta | 2025 log-loss delta | 2025 Brier delta | Decision |
|---|---:|---:|---:|---:|---:|---|
{line('hitter')}
{line('pitcher')}

This is stricter than applying one runs factor to every event. It uses the same
component families as the player model and preserves exact player home/away splits
for the next test. Opponent strength is only controlled by comparing each team with
itself; it is not yet an explicit schedule model. A current player adjustment still
requires improvement in future MLB player forecasts.
""", encoding="utf-8")
    print(json.dumps({name: {
        "prior": report[name]["selected_prior_exposure"],
        "development": report[name]["selected_development"],
        "confirmation": report[name]["untouched_confirmation"],
        "passed": report[name]["promotion_gate_passed"],
    } for name in ("hitter", "pitcher")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
