#!/usr/bin/env python3
"""Run chronology-safe six-year prospect comparable folds."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

try:
    from scripts.audit_prospect_comparable_chronology import (
        _cohort_features,
        _deduplicate,
        _sources,
    )
    from scripts.materialize_prospect_hitter_comparables import (
        _outcomes as hitter_outcomes,
        _validation_summary,
    )
    from scripts.materialize_prospect_pitcher_comparables import (
        _outcomes as pitcher_outcomes,
    )
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from audit_prospect_comparable_chronology import (
        _cohort_features,
        _deduplicate,
        _sources,
    )
    from materialize_prospect_hitter_comparables import (
        _outcomes as hitter_outcomes,
        _validation_summary,
    )
    from materialize_prospect_pitcher_comparables import (
        _outcomes as pitcher_outcomes,
    )
from universal_baseball.prospect_historical_comparables import (
    DEFAULT_COMPARABLES,
    score_hitter_comparables,
    score_pitcher_comparables,
)


HORIZON = 6
REFERENCE_ORIGINS = (2003, 2008, 2013, 2016, 2018)
TARGET_ORIGINS = (2013, 2016, 2018, 2019)
BIAS_MARGIN_WAR = 0.01


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--skill-2019-root",
        type=Path,
        default=Path("reports/generated/affiliated-skill-source-2019/tables"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/prospect-six-year-strict-result.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/prospect-six-year-strict-result.md"),
    )
    return parser.parse_args()


def _cohort(
    snapshots: pl.DataFrame,
    skill: pl.DataFrame,
    outcomes: pl.DataFrame,
    debut: pl.DataFrame,
    *,
    origin: int,
    player_type: str,
    runs_per_win: float,
) -> pl.DataFrame:
    features = _cohort_features(
        snapshots, skill, debut, origin=origin, player_type=player_type
    )
    builder = hitter_outcomes if player_type == "hitter" else pitcher_outcomes
    return (
        features.join(
            builder(
                features,
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


def _passes(summary: dict[str, object]) -> bool:
    candidate = summary["historical_comparables"]
    baseline = summary["population_baseline"]
    arrival = summary["arrival_historical_comparables"]
    arrival_baseline = summary["arrival_population_baseline"]
    conditional = summary["conditional_support_sensitivity"]["10"]
    return bool(
        candidate["rmse"] < baseline["rmse"]
        and abs(candidate["bias"]) <= abs(baseline["bias"]) + BIAS_MARGIN_WAR
        and arrival["brier"] < arrival_baseline["brier"]
        and arrival["log_loss"] < arrival_baseline["log_loss"]
        and conditional["arrivals"] >= 20
        and conditional["historical_comparables_rmse"]
        < conditional["population_baseline_rmse"]
    )


def _markdown(report: dict[str, object]) -> str:
    lines = [
        "# Strict six-year prospect comparable result",
        "",
        f"**Decision:** `{report['decision']}`",
        "",
        "Every reference outcome ends before its target snapshot, and target players are removed from their own reference pool.",
        "",
        "| Type | Target | References | WAR RMSE vs baseline | Arrival Brier vs baseline | Conditional RMSE vs baseline | Pass |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for player_type, player_result in report["player_types"].items():
        for origin, fold in player_result["folds"].items():
            summary = fold["scores"]
            total = summary["historical_comparables"]
            total_base = summary["population_baseline"]
            arrival = summary["arrival_historical_comparables"]
            arrival_base = summary["arrival_population_baseline"]
            conditional = summary["conditional_support_sensitivity"]["10"]
            lines.append(
                f"| {player_type} | {origin} | {','.join(map(str, fold['reference_origins']))} | "
                f"{total['rmse']:.3f} vs {total_base['rmse']:.3f} | "
                f"{arrival['brier']:.3f} vs {arrival_base['brier']:.3f} | "
                f"{conditional['historical_comparables_rmse']:.3f} vs {conditional['population_baseline_rmse']:.3f} | {fold['passed']} |"
            )
    lines += [
        "",
        "MAE remains reported in the JSON but does not veto a mean expected-WAR forecast. This is still partial WAR, not full controlled value or FV.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = _args()
    root = Path("reports/generated")
    runs_per_win = float(
        json.loads(Path("docs/prospect-component-uncertainty-result.json").read_text())[
            "runs_per_win"
        ]
    )
    results: dict[str, object] = {}
    for player_type in ("hitter", "pitcher"):
        snapshots, skill, outcomes, debut = _sources(root, player_type)
        extra_name = (
            "affiliated_hitting_components.parquet"
            if player_type == "hitter"
            else "affiliated_pitching_components.parquet"
        )
        skill = (
            pl.concat(
                [skill, pl.read_parquet(args.skill_2019_root / extra_name)],
                how="vertical_relaxed",
            )
            .sort(["season", "player_id", "sport_id", "team_id"])
            .unique(
                ["season", "player_id", "sport_id", "team_id"],
                keep="last",
                maintain_order=True,
            )
        )
        origins = sorted(set(REFERENCE_ORIGINS) | set(TARGET_ORIGINS))
        cohorts = {
            origin: _cohort(
                snapshots,
                skill,
                outcomes,
                debut,
                origin=origin,
                player_type=player_type,
                runs_per_win=runs_per_win,
            )
            for origin in origins
        }
        scorer = (
            score_hitter_comparables
            if player_type == "hitter"
            else score_pitcher_comparables
        )
        rate_basis = 600.0 if player_type == "hitter" else 800.0
        folds = {}
        for target_origin in TARGET_ORIGINS:
            reference_origins = tuple(
                origin
                for origin in REFERENCE_ORIGINS
                if origin + HORIZON < target_origin
            )
            target = cohorts[target_origin]
            reference = _deduplicate(
                [cohorts[origin] for origin in reference_origins]
            ).join(target.select("player_id"), on="player_id", how="anti")
            scored = scorer(
                reference, target, comparable_count=DEFAULT_COMPARABLES
            ).join(
                target.select(
                    "player_id", "later_component_war", "later_mlb_workload"
                ),
                on="player_id",
                validate="1:1",
            )
            summary = _validation_summary(
                scored, reference, rate_basis=rate_basis
            )
            folds[str(target_origin)] = {
                "reference_origins": list(reference_origins),
                "reference_players": reference.height,
                "target_players": target.height,
                "self_comparisons_removed": True,
                "scores": summary,
                "passed": _passes(summary),
            }
        results[player_type] = {
            "folds": folds,
            "all_folds_passed": all(fold["passed"] for fold in folds.values()),
        }
    passed = all(result["all_folds_passed"] for result in results.values())
    report = {
        "status": "prospect_six_year_strict_audited",
        "as_of_date": args.as_of_date.isoformat(),
        "contract": "docs/prospect-six-year-strict-confirmation-contract.md",
        "horizon_calendar_years": HORIZON,
        "decision": "promote_six_year_partial_outcomes" if passed else "withhold_six_year_partial_outcomes",
        "outside_fv_used": False,
        "player_types": results,
    }
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
