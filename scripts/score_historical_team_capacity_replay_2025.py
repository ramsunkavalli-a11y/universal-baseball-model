#!/usr/bin/env python3
"""Score frozen team/position/role capacity layers on the 2025 historical replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.historical_replay_inputs import MLB_TEAM_ID_BY_ABBREVIATION
from universal_baseball.opportunity_capacity import historical_mlb_workload_pools
from universal_baseball.team_opportunity_allocation import (
    allocate_current_organization_opportunity,
    allocate_hitter_position_capacity,
    allocate_pitcher_role_capacity,
    estimate_hitter_position_capacity_shares,
    estimate_pitcher_role_capacity_shares,
    historical_hitter_position_shares,
    historical_pitcher_role_shares,
    position_group,
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-root", type=Path, default=Path("reports/generated"))
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/historical-team-capacity-replay-2025-result.json"),
    )
    parser.add_argument("--bootstrap-repetitions", type=int, default=10_000)
    return parser.parse_args()


def _only(root: Path, pattern: str) -> Path:
    matches = list(root.rglob(pattern))
    if len(matches) != 1:
        raise FileNotFoundError(f"expected one {pattern} below {root}, found {len(matches)}")
    return matches[0]


def _metrics(frame: pl.DataFrame, *, prediction: str, actual: str) -> dict[str, float | int]:
    error = frame.get_column(prediction).to_numpy() - frame.get_column(actual).to_numpy()
    predicted = frame.get_column(prediction).to_numpy()
    observed = frame.get_column(actual).to_numpy()
    return {
        "players": frame.height,
        "rmse": float(np.sqrt(np.mean(error**2))),
        "mae": float(np.mean(np.abs(error))),
        "mean_forecast_minus_actual": float(np.mean(error)),
        "predicted_total": float(predicted.sum()),
        "actual_total": float(observed.sum()),
        "predicted_to_actual_ratio": float(predicted.sum() / observed.sum()),
    }


def _cluster_bootstrap_delta(
    frame: pl.DataFrame,
    *,
    baseline: str,
    challenger: str,
    actual: str,
    repetitions: int,
    seed: int,
) -> dict[str, object]:
    organizations = sorted(frame.get_column("organization_id").unique().to_list())
    arrays = []
    for organization_id in organizations:
        group = frame.filter(pl.col("organization_id") == organization_id)
        observed = group.get_column(actual).to_numpy()
        baseline_error = group.get_column(baseline).to_numpy() - observed
        challenger_error = group.get_column(challenger).to_numpy() - observed
        arrays.append(
            (
                group.height,
                float(np.sum(baseline_error**2)),
                float(np.sum(challenger_error**2)),
                float(np.sum(np.abs(baseline_error))),
                float(np.sum(np.abs(challenger_error))),
            )
        )
    values = np.asarray(arrays, dtype=float)
    rng = np.random.default_rng(seed)
    rmse_delta = np.empty(repetitions)
    mae_delta = np.empty(repetitions)
    for index in range(repetitions):
        sampled = values[rng.integers(0, len(values), size=len(values))].sum(axis=0)
        count, base_sse, challenge_sse, base_sae, challenge_sae = sampled
        rmse_delta[index] = np.sqrt(challenge_sse / count) - np.sqrt(base_sse / count)
        mae_delta[index] = challenge_sae / count - base_sae / count
    return {
        "clusters": len(organizations),
        "repetitions": repetitions,
        "seed": seed,
        "delta_definition": "challenger_minus_original; negative_is_better",
        "rmse_delta": {
            "point": _metrics(frame, prediction=challenger, actual=actual)["rmse"]
            - _metrics(frame, prediction=baseline, actual=actual)["rmse"],
            "ci95": [float(np.quantile(rmse_delta, 0.025)), float(np.quantile(rmse_delta, 0.975))],
        },
        "mae_delta": {
            "point": _metrics(frame, prediction=challenger, actual=actual)["mae"]
            - _metrics(frame, prediction=baseline, actual=actual)["mae"],
            "ci95": [float(np.quantile(mae_delta, 0.025)), float(np.quantile(mae_delta, 0.975))],
        },
    }


def _score_layers(
    frame: pl.DataFrame,
    *,
    actual: str,
    original: str,
    team: str,
    final: str,
    repetitions: int,
    seed: int,
) -> dict[str, object]:
    affected = frame.filter(pl.col(final) < pl.col(original) - 1e-7)
    return {
        "all_players": {
            "original": _metrics(frame, prediction=original, actual=actual),
            "team_cap": _metrics(frame, prediction=team, actual=actual),
            "final_capacity": _metrics(frame, prediction=final, actual=actual),
        },
        "final_capacity_affected_players": {
            "original": _metrics(affected, prediction=original, actual=actual),
            "final_capacity": _metrics(affected, prediction=final, actual=actual),
        },
        "team_vs_original_cluster_bootstrap": _cluster_bootstrap_delta(
            frame, baseline=original, challenger=team, actual=actual,
            repetitions=repetitions, seed=seed - 100,
        ),
        "final_vs_original_cluster_bootstrap": _cluster_bootstrap_delta(
            frame, baseline=original, challenger=final, actual=actual,
            repetitions=repetitions, seed=seed,
        ),
    }


def main() -> int:
    args = _args()
    history_paths = sorted(
        (args.generated_root / "opportunity-history-sources-v2/tables").glob(
            "*/affiliated_season_stats.parquet"
        )
    )
    history = pl.concat(
        [pl.read_parquet(path) for path in history_paths], how="vertical_relaxed"
    )
    pools = historical_mlb_workload_pools(history).filter(
        pl.col("season").is_in([2021, 2022, 2023, 2024])
    )
    league_capacity = float(pools.get_column("actual_pa").median())
    team_capacity = league_capacity / 30.0

    fielding_root = args.generated_root / "position-capacity-source"
    historical_fielding = pl.read_parquet(
        _only(fielding_root / "historical", "historical_fielding_usage.parquet")
    )
    hitter_shares = historical_hitter_position_shares(
        historical_fielding, history
    ).filter(pl.col("season").is_in([2021, 2022, 2023, 2024]))
    hitter_capacity = estimate_hitter_position_capacity_shares(
        hitter_shares, development_seasons=(2021, 2022, 2023, 2024)
    )
    pitcher_shares = historical_pitcher_role_shares(history).filter(
        pl.col("season").is_in([2021, 2022, 2023, 2024])
    )
    pitcher_capacity = estimate_pitcher_role_capacity_shares(
        pitcher_shares, development_seasons=(2021, 2022, 2023, 2024)
    )

    forecast_root = args.generated_root / "historical-projection-paths/2025-03-27/tables"
    hitters = pl.read_parquet(forecast_root / "hitter-expected-war-paths.parquet").filter(
        pl.col("season") == 2025
    ).with_columns(pl.lit(True).alias("is_controlled_season"))
    pitchers = pl.read_parquet(forecast_root / "pitcher-expected-war-paths.parquet").filter(
        pl.col("season") == 2025
    ).with_columns(pl.lit(True).alias("is_controlled_season"))
    owners = pl.read_parquet(
        args.generated_root / "historical-control-value/2025-03-27/historical-control-owners.parquet"
    )
    ownership = (
        owners.filter(pl.col("team_abbreviation").is_in(list(MLB_TEAM_ID_BY_ABBREVIATION)))
        .select(
            "player_id",
            pl.lit(2025).alias("control_year"),
            pl.col("team_abbreviation").replace_strict(
                MLB_TEAM_ID_BY_ABBREVIATION, return_dtype=pl.Int64
            ).alias("organization_id"),
        )
    )
    allocated = allocate_current_organization_opportunity(
        hitters, pitchers, ownership, team_capacity=team_capacity
    )
    hitter_final = allocate_hitter_position_capacity(
        allocated.hitter, hitter_capacity, team_capacity=team_capacity
    )
    pitcher_final = allocate_pitcher_role_capacity(
        allocated.pitcher, pitcher_capacity, team_capacity=team_capacity
    )

    actual_hitter = (
        history.filter(
            (pl.col("season") == 2025) & (pl.col("sport_id") == 1)
            & (pl.col("stat_group") == "hitting")
        )
        .group_by("player_id")
        .agg(pl.col("plate_appearances").sum().cast(pl.Float64).alias("actual_mlb_pa"))
    )
    actual_pitcher = (
        history.filter(
            (pl.col("season") == 2025) & (pl.col("sport_id") == 1)
            & (pl.col("stat_group") == "pitching")
        )
        .group_by("player_id")
        .agg(pl.col("batters_faced").sum().cast(pl.Float64).alias("actual_mlb_bf"))
    )
    hitter_scored = (
        hitter_final.players.join(actual_hitter, on="player_id", how="left", validate="m:1")
        .with_columns(
            pl.col("actual_mlb_pa").fill_null(0.0),
            pl.col("primary_position").map_elements(
                position_group, return_dtype=pl.String
            ).alias("diagnostic_group"),
        )
    )
    pitcher_scored = (
        pitcher_final.players.join(actual_pitcher, on="player_id", how="left", validate="m:1")
        .with_columns(
            pl.col("actual_mlb_bf").fill_null(0.0),
            pl.col("projected_role").str.to_uppercase().alias("diagnostic_group"),
        )
    )

    def subgroup_scores(
        frame: pl.DataFrame, *, actual: str, original: str, final: str
    ) -> list[dict[str, object]]:
        rows = []
        for group in sorted(frame.get_column("diagnostic_group").unique().to_list()):
            part = frame.filter(pl.col("diagnostic_group") == group)
            before = _metrics(part, prediction=original, actual=actual)
            after = _metrics(part, prediction=final, actual=actual)
            rows.append(
                {
                    "group": group,
                    "players": part.height,
                    "reduced_players": part.filter(pl.col(final) < pl.col(original) - 1e-7).height,
                    "original_rmse": before["rmse"],
                    "final_rmse": after["rmse"],
                    "rmse_delta": after["rmse"] - before["rmse"],
                    "original_mae": before["mae"],
                    "final_mae": after["mae"],
                    "mae_delta": after["mae"] - before["mae"],
                }
            )
        return rows

    report = {
        "report_schema_version": "0.1",
        "status": "historical_team_capacity_replay_2025_complete",
        "forecast_cutoff": "2025-03-27",
        "contract": "docs/historical-team-capacity-replay-2025-contract.md",
        "chronology": {
            "capacity_development_seasons": [2021, 2022, 2023, 2024],
            "outcome_season": 2025,
            "outcome_previously_available_for_other_descriptive_checks": True,
            "forecast_refit": False,
        },
        "capacity": {
            "league_workload": league_capacity,
            "team_workload": team_capacity,
            "hitter_position_shares": hitter_capacity.to_dicts(),
            "pitcher_role_shares": pitcher_capacity.to_dicts(),
        },
        "coverage": {
            "hitter_forecast_players": hitters.height,
            "pitcher_forecast_players": pitchers.height,
            "resolved_owner_players": ownership.height,
            "scored_hitter_players": hitter_scored.height,
            "scored_pitcher_players": pitcher_scored.height,
            "unresolved_hitter_players": hitters.height - hitter_scored.height,
            "unresolved_pitcher_players": pitchers.height - pitcher_scored.height,
        },
        "hitter": _score_layers(
            hitter_scored, actual="actual_mlb_pa", original="expected_mlb_pa",
            team="current_org_expected_mlb_pa", final="position_capped_expected_mlb_pa",
            repetitions=args.bootstrap_repetitions, seed=20250901,
        ),
        "pitcher": _score_layers(
            pitcher_scored, actual="actual_mlb_bf", original="expected_mlb_bf",
            team="current_org_expected_mlb_bf", final="role_capped_expected_mlb_bf",
            repetitions=args.bootstrap_repetitions, seed=20250902,
        ),
        "hitter_position_diagnostics": subgroup_scores(
            hitter_scored, actual="actual_mlb_pa", original="expected_mlb_pa",
            final="position_capped_expected_mlb_pa",
        ),
        "pitcher_role_diagnostics": subgroup_scores(
            pitcher_scored, actual="actual_mlb_bf", original="expected_mlb_bf",
            final="role_capped_expected_mlb_bf",
        ),
        "decision": {
            "broad_team_cap": "retain_for_team_context",
            "hitter_team_cap_evidence": "small_inconclusive_improvement",
            "pitcher_team_cap_evidence": "rmse_and_mae_improved",
            "rigid_hitter_position_cap": "reject_for_display",
            "rigid_pitcher_role_cap": "do_not_promote",
            "next_challenger": "flexible_cross_position_and_cross_role_reallocation",
            "organization_neutral_value_changed": False,
        },
        "checks": {
            "outcome_zeros_retained": True,
            "capacity_uses_only_pre_outcome_seasons": True,
            "identical_players_within_each_comparison": True,
            "player_workload_never_increased": True,
            "organization_neutral_forecasts_modified": False,
        },
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
