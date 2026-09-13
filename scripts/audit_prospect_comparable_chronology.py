#!/usr/bin/env python3
"""Audit prospect comparables with nonoverlapping training outcomes and targets."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl

try:
    from scripts.materialize_prospect_hitter_comparables import (
        _outcomes as hitter_outcomes,
        _validation_summary,
    )
    from scripts.materialize_prospect_pitcher_comparables import (
        _outcomes as pitcher_outcomes,
    )
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from materialize_prospect_hitter_comparables import (
        _outcomes as hitter_outcomes,
        _validation_summary,
    )
    from materialize_prospect_pitcher_comparables import _outcomes as pitcher_outcomes
from universal_baseball.hitter_opportunity_paths import hitter_level_tier
from universal_baseball.prospect_historical_comparables import (
    DEFAULT_COMPARABLES,
    primary_exact_level,
    score_hitter_comparables,
    score_pitcher_comparables,
)


HORIZON = 4
REFERENCE_ORIGINS = (2003, 2008, 2013, 2016, 2018, 2021)
VALIDATION_ORIGINS = (2008, 2013, 2018, 2021)
BLEND_SELECTION_ORIGINS = (2008, 2013, 2018)
BLEND_CONFIRMATION_ORIGIN = 2021
BLEND_WEIGHTS = tuple(value / 10.0 for value in range(11))


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/prospect-comparable-chronology-result.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/prospect-comparable-chronology-result.md"),
    )
    return parser.parse_args()


def _read_many(paths: list[Path], *, keys: list[str]) -> pl.DataFrame:
    frame = pl.concat([pl.read_parquet(path) for path in paths], how="vertical_relaxed")
    return frame.sort(keys).unique(keys, keep="last", maintain_order=True)


def _sources(root: Path, player_type: str) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    snapshot_name = f"{player_type}_snapshots.parquet"
    snapshots = _read_many(
        [
            root / "opportunity-history-sources-2003-2007/tables" / snapshot_name,
            root / "opportunity-history-sources-pre2020/tables" / snapshot_name,
            root / "opportunity-history-sources-v2/tables" / snapshot_name,
        ],
        keys=["snapshot_year", "player_id"],
    )
    skill_name = (
        "affiliated_hitting_components.parquet"
        if player_type == "hitter"
        else "affiliated_pitching_components.parquet"
    )
    skill = _read_many(
        [
            root / "affiliated-skill-source-2003-2007/tables" / skill_name,
            root / "affiliated-skill-source-2008-2017/tables" / skill_name,
            root / "phase2-arrival-skill-source/tables" / skill_name,
        ],
        keys=["season", "player_id", "sport_id", "team_id"],
    )
    if player_type == "hitter":
        outcome_names = (
            "mlb_hitting_components_2004_2009.parquet",
            "mlb_hitting_components_2009_2025.parquet",
        )
    else:
        outcome_names = (
            "mlb_pitching_2004_2009.parquet",
            "mlb_pitching_2009_2025.parquet",
        )
    outcomes = _read_many(
        [
            root / "career-mlb-outcome-inventory-2004-2009/tables" / outcome_names[0],
            root / "career-mlb-outcome-inventory-2009-2025/tables" / outcome_names[1],
        ],
        keys=["season", "player_id"],
    )
    debut = _read_many(
        [
            root / "career-mlb-outcome-inventory-2004-2009/tables/people-debut-dates.parquet",
            root / "career-mlb-outcome-inventory-2009-2025/tables/people-debut-dates.parquet",
        ],
        keys=["player_id"],
    )
    return snapshots, skill, outcomes, debut


def _cohort_features(
    snapshots: pl.DataFrame,
    skill: pl.DataFrame,
    debut: pl.DataFrame,
    *,
    origin: int,
    player_type: str,
) -> pl.DataFrame:
    exposure = "plate_appearances" if player_type == "hitter" else "batters_faced"
    current = skill.filter(
        (pl.col("season") == origin)
        & (pl.col("sport_id") != 1)
        & (pl.col(exposure) > 0)
    )
    if player_type == "hitter":
        current = current.group_by("player_id").agg(
            pl.col(exposure).sum().cast(pl.Float64).alias("current_milb_workload"),
            (pl.col("base_on_balls") - pl.col("intentional_walks")).sum().alias("n1"),
            pl.col("strike_outs").sum().alias("n2"),
            pl.col("home_runs").sum().alias("n3"),
            (pl.col("doubles") + pl.col("triples") + pl.col("home_runs")).sum().alias("n4"),
        )
    else:
        current = current.group_by("player_id").agg(
            pl.col(exposure).sum().cast(pl.Float64).alias("current_milb_workload"),
            pl.col("strike_outs").sum().alias("n1"),
            (pl.col("base_on_balls") - pl.col("intentional_walks")).sum().alias("n2"),
            pl.col("hit_batters").sum().alias("n3"),
            pl.col("home_runs").sum().alias("n4"),
        )
    current = current.with_columns(
        *(
            (pl.col(f"n{index}") / pl.col("current_milb_workload"))
            .clip(0.0, 1.0)
            .alias(f"production_rate_{index}")
            for index in range(1, 5)
        )
    )
    level = primary_exact_level(skill, season=origin, exposure=exposure).with_columns(
        pl.col("primary_level_group")
        .map_elements(hitter_level_tier, return_dtype=pl.String)
        .alias("primary_level_tier")
    )
    prior_debut = debut.select(
        "player_id",
        pl.col("mlb_debut_date").dt.year().alias("debut_year"),
    )
    return (
        snapshots.filter(pl.col("snapshot_year") == origin)
        .select("player_id", "age_years")
        .join(current, on="player_id", how="inner", validate="1:1")
        .join(level, on="player_id", how="inner", validate="1:1")
        .join(prior_debut, on="player_id", how="left", validate="1:1")
        .filter(
            (pl.col("debut_year").is_null() | (pl.col("debut_year") > origin))
            & pl.col("age_years").is_between(16.0, 30.0)
        )
        .drop("debut_year")
        .sort("player_id")
    )


def _cohort_with_outcome(
    snapshots: pl.DataFrame,
    skill: pl.DataFrame,
    outcomes: pl.DataFrame,
    debut: pl.DataFrame,
    *,
    origin: int,
    player_type: str,
    runs_per_win: float,
) -> pl.DataFrame:
    cohort = _cohort_features(
        snapshots, skill, debut, origin=origin, player_type=player_type
    )
    builder = hitter_outcomes if player_type == "hitter" else pitcher_outcomes
    return (
        cohort.join(
            builder(
                cohort,
                outcomes,
                origin=origin,
                runs_per_win=runs_per_win,
                horizon=HORIZON,
            ),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .with_columns(
            pl.col("later_component_war").fill_null(0.0),
            pl.col("later_mlb_workload").fill_null(0.0),
            pl.lit(origin).alias("origin_year"),
        )
    )


def _deduplicate(frames: list[pl.DataFrame]) -> pl.DataFrame:
    return (
        pl.concat(frames, how="vertical_relaxed")
        .sort(["player_id", "origin_year"])
        .unique("player_id", keep="last", maintain_order=True)
    )


def _passes(summary: dict[str, object]) -> bool:
    candidate = summary["historical_comparables"]
    baseline = summary["population_baseline"]
    arrival = summary["arrival_historical_comparables"]
    arrival_baseline = summary["arrival_population_baseline"]
    supported = summary["conditional_support_sensitivity"]["10"]
    return bool(
        candidate["mae"] < baseline["mae"]
        and candidate["rmse"] < baseline["rmse"]
        and arrival["brier"] < arrival_baseline["brier"]
        and arrival["log_loss"] < arrival_baseline["log_loss"]
        and supported["arrivals"] >= 20
        and supported["historical_comparables_mae"] < supported["population_baseline_mae"]
        and supported["historical_comparables_rmse"] < supported["population_baseline_rmse"]
    )


def _conditional_rows(
    validation: pl.DataFrame,
    reference: pl.DataFrame,
    *,
    rate_basis: float,
) -> pl.DataFrame:
    arrivals = reference.filter(pl.col("later_mlb_workload") > 0)
    prior = (
        float(arrivals["later_component_war"].sum())
        * rate_basis
        / float(arrivals["later_mlb_workload"].sum())
    )
    return (
        validation.filter(
            (pl.col("historical_conditional_arrival_support") >= 10)
            & (pl.col("later_mlb_workload") > 0)
        )
        .select(
            "player_id",
            (
                (
                    pl.col("later_component_war") * rate_basis
                    + pl.lit(prior) * 200.0
                )
                / (pl.col("later_mlb_workload") + 200.0)
            ).alias("actual"),
            pl.col("historical_conditional_component_war_rate").alias("local"),
            pl.lit(prior).alias("baseline"),
        )
    )


def _errors(frame: pl.DataFrame, weight: float) -> dict[str, float | int]:
    actual = frame["actual"].to_numpy()
    prediction = (
        weight * frame["local"].to_numpy()
        + (1.0 - weight) * frame["baseline"].to_numpy()
    )
    error = prediction - actual
    return {
        "players": frame.height,
        "local_weight": weight,
        "mae": float(np.abs(error).mean()),
        "rmse": float(np.sqrt(np.square(error).mean())),
    }


def _blend_selection(
    rows: dict[int, pl.DataFrame],
) -> dict[str, object]:
    selection = pl.concat([rows[origin] for origin in BLEND_SELECTION_ORIGINS])
    baseline = _errors(selection, 0.0)
    grid = [_errors(selection, weight) for weight in BLEND_WEIGHTS]
    eligible = [
        result
        for result in grid
        if result["local_weight"] > 0
        and result["mae"] < baseline["mae"]
        and result["rmse"] < baseline["rmse"]
    ]
    selected = min(eligible, key=lambda result: (result["rmse"], result["mae"])) if eligible else baseline
    confirmation_baseline = _errors(rows[BLEND_CONFIRMATION_ORIGIN], 0.0)
    confirmation = _errors(
        rows[BLEND_CONFIRMATION_ORIGIN], float(selected["local_weight"])
    )
    passed = bool(
        selected["local_weight"] > 0
        and confirmation["mae"] < confirmation_baseline["mae"]
        and confirmation["rmse"] < confirmation_baseline["rmse"]
    )
    return {
        "selection_origins": list(BLEND_SELECTION_ORIGINS),
        "confirmation_origin": BLEND_CONFIRMATION_ORIGIN,
        "weights_tested": list(BLEND_WEIGHTS),
        "selection_baseline": baseline,
        "selection_selected": selected,
        "confirmation_baseline": confirmation_baseline,
        "confirmation_selected": confirmation,
        "passed": passed,
    }


def _markdown(report: dict[str, object]) -> str:
    lines = [
        "# Prospect comparable chronology audit",
        "",
        f"**Decision:** `{report['decision']}`",
        "",
        "Every reference outcome window ends before its validation snapshot. Non-arrivals are retained as zero.",
        "",
        "| Type | Target | Reference origins | Total MAE vs baseline | Arrival Brier vs baseline | Supported conditional MAE vs baseline | Pass |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for player_type, result in report["player_types"].items():
        for origin, fold in result["folds"].items():
            summary = fold["scores"]
            total = summary["historical_comparables"]
            total_base = summary["population_baseline"]
            arrival = summary["arrival_historical_comparables"]
            arrival_base = summary["arrival_population_baseline"]
            conditional = summary["conditional_support_sensitivity"]["10"]
            lines.append(
                f"| {player_type} | {origin} | {','.join(map(str, fold['reference_origins']))} "
                f"| {total['mae']:.3f} vs {total_base['mae']:.3f} "
                f"| {arrival['brier']:.3f} vs {arrival_base['brier']:.3f} "
                f"| {conditional['historical_comparables_mae']:.3f} vs {conditional['population_baseline_mae']:.3f} "
                f"| {fold['passed']} |"
            )
    lines += [
        "",
        "## Frozen global/local blend",
        "",
        "The local comparable rate was blended toward the historical arrival-population mean. The weight was selected on 2008, 2013 and 2018, then tested unchanged on 2021.",
        "",
        "| Type | Selected local weight | 2021 MAE vs baseline | 2021 RMSE vs baseline | Pass |",
        "|---|---:|---:|---:|---:|",
    ]
    for player_type, result in report["player_types"].items():
        blend = result["conditional_global_local_blend"]
        selected = blend["confirmation_selected"]
        baseline = blend["confirmation_baseline"]
        lines.append(
            f"| {player_type} | {blend['selection_selected']['local_weight']:.1f} "
            f"| {selected['mae']:.3f} vs {baseline['mae']:.3f} "
            f"| {selected['rmse']:.3f} vs {baseline['rmse']:.3f} "
            f"| {blend['passed']} |"
        )
    lines += [
        "",
        "A player type may be displayed as validated conditional talent only if every frozen fold passes. Public FV and rankings are not used.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = _args()
    root = Path("reports/generated")
    runs_per_win = float(
        json.loads(Path("docs/prospect-component-uncertainty-result.json").read_text())["runs_per_win"]
    )
    results: dict[str, object] = {}
    for player_type in ("hitter", "pitcher"):
        snapshots, skill, outcomes, debut = _sources(root, player_type)
        cohorts = {
            origin: _cohort_with_outcome(
                snapshots,
                skill,
                outcomes,
                debut,
                origin=origin,
                player_type=player_type,
                runs_per_win=runs_per_win,
            )
            for origin in REFERENCE_ORIGINS
        }
        scorer = score_hitter_comparables if player_type == "hitter" else score_pitcher_comparables
        rate_basis = 600.0 if player_type == "hitter" else 800.0
        folds = {}
        conditional_rows = {}
        for target_origin in VALIDATION_ORIGINS:
            reference_origins = tuple(
                origin
                for origin in REFERENCE_ORIGINS
                if origin + HORIZON < target_origin
            )
            reference = _deduplicate([cohorts[origin] for origin in reference_origins])
            target = cohorts[target_origin]
            scored = scorer(
                reference,
                target,
                comparable_count=DEFAULT_COMPARABLES,
            ).join(
                target.select("player_id", "later_component_war", "later_mlb_workload"),
                on="player_id",
                validate="1:1",
            )
            summary = _validation_summary(scored, reference, rate_basis=rate_basis)
            conditional_rows[target_origin] = _conditional_rows(
                scored, reference, rate_basis=rate_basis
            )
            folds[str(target_origin)] = {
                "reference_origins": list(reference_origins),
                "reference_players": reference.height,
                "target_players": target.height,
                "chronology_safe": max(reference_origins) + HORIZON < target_origin,
                "scores": summary,
                "passed": _passes(summary),
            }
        results[player_type] = {
            "folds": folds,
            "all_folds_passed": all(fold["passed"] for fold in folds.values()),
            "conditional_global_local_blend": _blend_selection(conditional_rows),
        }
    report = {
        "status": "prospect_comparable_chronology_audited",
        "as_of_date": args.as_of_date.isoformat(),
        "horizon_calendar_years": HORIZON,
        "nonarrivals_scored_zero": True,
        "outside_fv_used": False,
        "decision": (
            "promote_both_player_types"
            if all(result["all_folds_passed"] for result in results.values())
            else "withhold_any_player_type_failing_a_fold"
        ),
        "player_types": results,
    }
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps({
        player_type: result["all_folds_passed"]
        for player_type, result in results.items()
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
