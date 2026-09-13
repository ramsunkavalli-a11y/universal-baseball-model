#!/usr/bin/env python3
"""Audit frozen portable steal skill inside historical prospect value."""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict
from datetime import date
import json
from pathlib import Path

import polars as pl

try:
    from scripts.audit_prospect_comparable_chronology import (
        HORIZON,
        REFERENCE_ORIGINS,
        VALIDATION_ORIGINS,
        _cohort_features,
        _deduplicate,
        _sources,
    )
    from scripts.audit_prospect_position_adjusted_outcomes import (
        _metrics,
        _score_outcome,
    )
    from scripts.materialize_prospect_hitter_comparables import _outcomes
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from audit_prospect_comparable_chronology import (
        HORIZON,
        REFERENCE_ORIGINS,
        VALIDATION_ORIGINS,
        _cohort_features,
        _deduplicate,
        _sources,
    )
    from audit_prospect_position_adjusted_outcomes import _metrics, _score_outcome
    from materialize_prospect_hitter_comparables import _outcomes
from universal_baseball.current_baserunning import (
    ATTEMPT_CANDIDATE,
    SUCCESS_CANDIDATE,
    build_steal_history,
)
from universal_baseball.historical_hitter_baserunning import (
    steal_war_by_player_origin,
)
from universal_baseball.player_value_baserunning_runs import (
    build_baserunning_reference,
    project_steal_runs,
)
from universal_baseball.player_value_steal_projection import (
    PlayerSeasonStealSummary,
    attempt_multiplier,
    success_log_odds_residual,
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--target-skill-path",
        type=Path,
        default=Path(
            "reports/generated/affiliated-skill-source-2019/tables/"
            "affiliated_hitting_components.parquet"
        ),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/prospect-steal-value-result.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/prospect-steal-value-result.md"),
    )
    return parser.parse_args()


def _reference():
    source = json.loads(
        Path("docs/player-value-v1-baserunning-run-conversion-2024.json").read_text()
    )["reference"]
    return build_baserunning_reference(
        season=int(source["season"]),
        plate_appearances=float(source["plate_appearances"]),
        runs=float(source["runs"]),
        outs=float(source["outs"]),
        steal_opportunity_proxy=float(source["steal_opportunity_proxy"]),
        steal_attempts=float(source["steal_attempts"]),
        stolen_bases=float(source["stolen_bases"]),
        advancement_opportunities=float(source["advancement_opportunities"]),
    )


def _cohort(
    snapshots: pl.DataFrame,
    skill: pl.DataFrame,
    hitting: pl.DataFrame,
    debut: pl.DataFrame,
    *,
    origin: int,
    runs_per_win: float,
    reference,
) -> pl.DataFrame:
    players = _cohort_features(
        snapshots, skill, debut, origin=origin, player_type="hitter"
    )
    batting = _outcomes(
        players,
        hitting,
        origin=origin,
        runs_per_win=runs_per_win,
        horizon=HORIZON,
    )
    steals = steal_war_by_player_origin(
        hitting,
        origin=origin,
        horizon=HORIZON,
        runs_per_win=runs_per_win,
        reference=reference,
    )
    return (
        players.join(batting, on="player_id", how="left", validate="1:1")
        .join(steals, on="player_id", how="left", validate="1:1")
        .with_columns(
            pl.col("later_component_war").fill_null(0.0),
            pl.col("later_mlb_workload").fill_null(0.0),
            pl.col("later_steal_runs").fill_null(0.0),
            pl.col("later_steal_war").fill_null(0.0),
            pl.lit(origin).alias("origin_year"),
        )
        .with_columns(
            (pl.col("later_component_war") + pl.col("later_steal_war")).alias(
                "later_batting_steal_war"
            )
        )
    )


def _steal_predictions(
    target: pl.DataFrame,
    expected_workload: pl.DataFrame,
    history_by_player: dict[int, list[PlayerSeasonStealSummary]],
    *,
    origin: int,
    runs_per_win: float,
    reference,
) -> pl.DataFrame:
    workload = {
        int(row["player_id"]): float(row["expected_mlb_pa"])
        for row in expected_workload.iter_rows(named=True)
    }
    rows = []
    for player_id in target["player_id"].to_list():
        pid = int(player_id)
        evidence = history_by_player.get(pid, [])
        forecast = PlayerSeasonStealSummary(
            player_id=pid,
            season=origin + 1,
            tier="MLB",
            opportunity_proxy=0.0,
            attempts=0.0,
            successes=0.0,
            expected_attempts=0.0,
            expected_successes=0.0,
        )
        projection = project_steal_runs(
            projected_mlb_pa=workload[pid],
            attempt_multiplier=attempt_multiplier(
                forecast, evidence, ATTEMPT_CANDIDATE
            ),
            success_logodds_residual=success_log_odds_residual(
                forecast, evidence, SUCCESS_CANDIDATE
            ),
            reference=reference,
        )
        rows.append(
            {
                "player_id": pid,
                "predicted_steal_war": projection[4] / runs_per_win,
                "has_recent_steal_evidence": any(
                    1 <= forecast.season - row.season <= 3 for row in evidence
                ),
            }
        )
    return pl.DataFrame(rows).sort("player_id")


def _fold(
    reference_cohort: pl.DataFrame,
    target: pl.DataFrame,
    history_by_player: dict[int, list[PlayerSeasonStealSummary]],
    *,
    origin: int,
    runs_per_win: float,
    reference,
) -> dict[str, object]:
    batting = _score_outcome(
        reference_cohort, target, "later_component_war"
    ).select(
        "player_id",
        pl.col("historical_component_war_4y").alias("predicted_batting_war"),
    )
    workload = _score_outcome(
        reference_cohort, target, "later_mlb_workload"
    ).select(
        "player_id",
        pl.col("historical_component_war_4y").alias("expected_mlb_pa"),
    )
    predictions = _steal_predictions(
        target,
        workload,
        history_by_player,
        origin=origin,
        runs_per_win=runs_per_win,
        reference=reference,
    )
    scored = (
        target.select(
            "player_id", "later_steal_war", "later_batting_steal_war"
        )
        .join(batting, on="player_id", validate="1:1")
        .join(predictions, on="player_id", validate="1:1")
        .with_columns(
            (pl.col("predicted_batting_war") + pl.col("predicted_steal_war")).alias(
                "predicted_combined_war"
            )
        )
    )
    zeros = [0.0] * scored.height
    steal_baseline = _metrics(scored["later_steal_war"].to_numpy(), zeros)
    steal_candidate = _metrics(
        scored["later_steal_war"].to_numpy(), scored["predicted_steal_war"].to_numpy()
    )
    combined_baseline = _metrics(
        scored["later_batting_steal_war"].to_numpy(),
        scored["predicted_batting_war"].to_numpy(),
    )
    combined_candidate = _metrics(
        scored["later_batting_steal_war"].to_numpy(),
        scored["predicted_combined_war"].to_numpy(),
    )
    passed = bool(
        steal_candidate["rmse"] < steal_baseline["rmse"]
        and combined_candidate["rmse"] < combined_baseline["rmse"]
        and abs(steal_candidate["bias"]) <= abs(steal_baseline["bias"])
        and abs(combined_candidate["bias"]) <= abs(combined_baseline["bias"])
    )
    return {
        "target_players": target.height,
        "players_with_recent_steal_evidence": scored.filter(
            pl.col("has_recent_steal_evidence")
        ).height,
        "steal_war": {"neutral_baseline": steal_baseline, "candidate": steal_candidate},
        "batting_plus_steal_war": {
            "batting_only_baseline": combined_baseline,
            "candidate": combined_candidate,
        },
        "passed": passed,
    }


def _markdown(report: dict[str, object]) -> str:
    lines = [
        "# Prospect stolen-base value audit",
        "",
        f"**Decision:** `{report['decision']}`",
        "",
        "The already-frozen portable steal model is applied to old prospect cohorts. Expected future MLB PA comes from chronology-safe comparables; actual future steal value is centered within each MLB season and translated with one fixed run environment.",
        "",
        "| Target | Evidence | Steal RMSE vs neutral | Combined RMSE vs batting only | Pass |",
        "|---:|---:|---:|---:|---:|",
    ]
    for origin, fold in report["folds"].items():
        steal = fold["steal_war"]
        combined = fold["batting_plus_steal_war"]
        lines.append(
            f"| {origin} | {fold['players_with_recent_steal_evidence']}/{fold['target_players']} | "
            f"{steal['candidate']['rmse']:.4f} vs {steal['neutral_baseline']['rmse']:.4f} | "
            f"{combined['candidate']['rmse']:.4f} vs {combined['batting_only_baseline']['rmse']:.4f} | {fold['passed']} |"
        )
    lines += [
        "",
        "This covers stolen-base value only. Non-steal advancement remains unavailable in the broad history and is not inferred. MAE is reported but does not veto an expected-mean forecast.",
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
    snapshots, skill, hitting, debut = _sources(root, "hitter")
    skill = (
        pl.concat([skill, pl.read_parquet(args.target_skill_path)], how="vertical_relaxed")
        .sort(["season", "player_id", "sport_id", "team_id"])
        .unique(
            ["season", "player_id", "sport_id", "team_id"],
            keep="last",
            maintain_order=True,
        )
    )
    reference = _reference()
    steal_history, environment_audit = build_steal_history(skill)
    history_by_player: dict[int, list[PlayerSeasonStealSummary]] = defaultdict(list)
    for row in steal_history:
        history_by_player[row.player_id].append(row)
    cohorts = {
        origin: _cohort(
            snapshots,
            skill,
            hitting,
            debut,
            origin=origin,
            runs_per_win=runs_per_win,
            reference=reference,
        )
        for origin in REFERENCE_ORIGINS
    }
    folds = {}
    for target_origin in VALIDATION_ORIGINS:
        reference_origins = tuple(
            origin
            for origin in REFERENCE_ORIGINS
            if origin + HORIZON < target_origin
        )
        reference_cohort = _deduplicate(
            [cohorts[origin] for origin in reference_origins]
        )
        folds[str(target_origin)] = {
            "reference_origins": list(reference_origins),
            **_fold(
                reference_cohort,
                cohorts[target_origin],
                history_by_player,
                origin=target_origin,
                runs_per_win=runs_per_win,
                reference=reference,
            ),
        }
    passed = all(bool(fold["passed"]) for fold in folds.values())
    report = {
        "status": "prospect_steal_value_audited",
        "as_of_date": args.as_of_date.isoformat(),
        "model": {
            "attempt": ATTEMPT_CANDIDATE.candidate_id,
            "success": SUCCESS_CANDIDATE.candidate_id,
        },
        "decision": "promote_steal_value" if passed else "withhold_steal_value",
        "outside_fv_used": False,
        "environment_audit": asdict(environment_audit),
        "folds": folds,
    }
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
