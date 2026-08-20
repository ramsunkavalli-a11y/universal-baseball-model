#!/usr/bin/env python
"""Materialize the frozen 2024 player-aware PythagenPat sensitivity."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import polars as pl

from universal_baseball.player_value_positional_adjustment import DEFENSIVE_POSITIONS
from universal_baseball.player_value_pythagenpat_sensitivity import (
    PYTHAGENPAT_EXPONENT_POWER,
    PYTHAGENPAT_SENSITIVITY_ID,
    calculate_position_player_pythagenpat_sensitivity,
)


ZERO_EXPOSURE_PLAYER_IDS = {543518, 593934, 622491, 656555, 666158, 808982}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _distribution(series: pl.Series) -> dict[str, float]:
    return {
        "minimum": float(series.min()),
        "p05": float(series.quantile(0.05, interpolation="linear")),
        "median": float(series.median()),
        "mean": float(series.mean()),
        "p95": float(series.quantile(0.95, interpolation="linear")),
        "maximum": float(series.max()),
        "mean_absolute": float(series.abs().mean()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--centering-components", type=Path, required=True)
    parser.add_argument("--position-allocation", type=Path, required=True)
    parser.add_argument(
        "--run-environment",
        type=Path,
        default=Path("docs/player-value-v1-mlb-run-environment-2024.json"),
    )
    parser.add_argument(
        "--replacement",
        type=Path,
        default=Path("docs/player-value-v1-replacement-level-2024.json"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/player-value-v1-runs-per-win-pythagenpat-sensitivity-2024.json"),
    )
    parser.add_argument(
        "--output-table",
        type=Path,
        default=Path("reports/generated/player-value-v1-runs-per-win-pythagenpat-sensitivity-2024.parquet"),
    )
    args = parser.parse_args()

    components = pl.read_parquet(args.centering_components).sort("player_id")
    if components.height != 651 or components.get_column("player_id").n_unique() != 651:
        raise ValueError("centering component artifact must contain 651 unique players")

    position = pl.read_parquet(args.position_allocation).filter(
        (pl.col("current_season") == 2023) & (pl.col("next_season") == 2024)
    )
    if position.height != 3046 or position.get_column("player_id").n_unique() != 3046:
        raise ValueError("frozen 2024 position allocation must contain 3,046 unique players")
    position_outs = {
        int(row["player_id"]): sum(
            float(row[f"S0_predicted_outs_{position_name}"])
            for position_name in DEFENSIVE_POSITIONS
        )
        for row in position.iter_rows(named=True)
    }

    environment = json.loads(args.run_environment.read_text(encoding="utf-8"))
    replacement = json.loads(args.replacement.read_text(encoding="utf-8"))
    if int(environment["season"]) != 2024:
        raise ValueError("run environment must be the frozen 2024 reference")
    if int(environment["regular_season_games"]) != 2429:
        raise ValueError("2024 run environment game anchor changed")
    if int(environment["batting_runs_scored"]) != 21343:
        raise ValueError("2024 run environment runs anchor changed")
    league_team_rpg = float(environment["batting_runs_scored"]) / (
        2.0 * float(environment["regular_season_games"])
    )
    binding_rpw = float(environment["runs_per_win"])
    replacement_rate = float(replacement["binding"]["replacement_runs_per_pa"])

    rows: list[dict[str, float | int]] = []
    missing_position_ids: list[int] = []
    for row in components.iter_rows(named=True):
        player_id = int(row["player_id"])
        pa = float(row["projected_expected_mlb_pa"])
        if player_id in position_outs:
            defensive_outs = position_outs[player_id]
        elif pa == 0 and player_id in ZERO_EXPOSURE_PLAYER_IDS:
            defensive_outs = 0.0
            missing_position_ids.append(player_id)
        else:
            raise ValueError(f"missing frozen position allocation for player {player_id}")
        sensitivity = calculate_position_player_pythagenpat_sensitivity(
            projected_pa=pa,
            projected_defensive_outs=defensive_outs,
            batting_runs=row["batting_runs"],
            baserunning_runs=row["baserunning_runs"],
            defense_runs=row["defense_runs"],
            positional_runs=row["positional_runs"],
            centering_runs=row["centering_runs"],
            replacement_runs_per_pa=replacement_rate,
            league_team_runs_per_game=league_team_rpg,
        )
        centered_raa = float(row["raw_above_average_runs"]) + float(row["centering_runs"])
        binding_war = (centered_raa + sensitivity.replacement_runs) / binding_rpw
        rows.append(
            {
                "player_id": player_id,
                "projected_expected_mlb_pa": pa,
                "projected_defensive_outs": defensive_outs,
                "estimated_games": sensitivity.estimated_games,
                "centered_runs_above_average": centered_raa,
                "replacement_runs": sensitivity.replacement_runs,
                "binding_common_divisor_war": binding_war,
                "pythagenpat_wins_above_average": sensitivity.wins_above_average,
                "pythagenpat_replacement_wins": sensitivity.replacement_wins,
                "pythagenpat_war": sensitivity.war,
                "pythagenpat_minus_binding_war": sensitivity.war - binding_war,
            }
        )

    result = pl.DataFrame(rows).sort("player_id")
    zero_rows = result.filter(pl.col("projected_expected_mlb_pa") == 0)
    if set(zero_rows.get_column("player_id").to_list()) != ZERO_EXPOSURE_PLAYER_IDS:
        raise ValueError("the exact six required zero-exposure rows were not preserved")
    for column in (
        "binding_common_divisor_war",
        "pythagenpat_wins_above_average",
        "pythagenpat_replacement_wins",
        "pythagenpat_war",
        "pythagenpat_minus_binding_war",
    ):
        if zero_rows.get_column(column).abs().max() != 0:
            raise ValueError(f"zero-exposure rows must have zero {column}")

    differences = result.get_column("pythagenpat_minus_binding_war")
    largest = (
        result.with_columns(differences.abs().alias("absolute_difference"))
        .sort("absolute_difference", descending=True)
        .head(10)
        .drop("absolute_difference")
        .to_dicts()
    )
    payload = {
        "schema_version": "0.1",
        "status": "player_value_v1_runs_per_win_pythagenpat_sensitivity_2024_frozen_verified",
        "contract": "docs/player-value-v1-runs-per-win-pythagenpat-sensitivity-contract.md",
        "reference_season": 2024,
        "source_commit": str(os.environ.get("GITHUB_SHA") or "").strip() or None,
        "actions_run_id": int(os.environ["GITHUB_RUN_ID"]) if os.environ.get("GITHUB_RUN_ID") else None,
        "method": {
            "sensitivity_id": PYTHAGENPAT_SENSITIVITY_ID,
            "exponent_power": PYTHAGENPAT_EXPONENT_POWER,
            "estimated_innings": "max(2.1 * projected_PA, projected_defensive_outs / 3)",
            "offensive_side": "Rbat + Rbr + Rpos + Rlg",
            "runs_allowed_side": "league_team_runs_per_game - Rdef / estimated_games",
            "replacement_evaluated_separately": True,
        },
        "inputs": {
            "centering_components": {
                "run_id": 32384563289,
                "artifact_id": 9412396481,
                "sha256": _sha256(args.centering_components),
            },
            "position_allocation": {
                "run_id": 32266007594,
                "artifact_id": 9370211679,
                "sha256": _sha256(args.position_allocation),
            },
            "run_environment": str(args.run_environment),
            "replacement": str(args.replacement),
        },
        "reference": {
            "player_count": result.height,
            "positive_exposure_player_count": result.filter(
                pl.col("projected_expected_mlb_pa") > 0
            ).height,
            "zero_exposure_player_ids": sorted(ZERO_EXPOSURE_PLAYER_IDS),
            "zero_exposure_missing_position_ids": sorted(missing_position_ids),
            "projected_mlb_pa": float(result.get_column("projected_expected_mlb_pa").sum()),
            "league_team_runs_per_game": league_team_rpg,
            "binding_runs_per_win": binding_rpw,
            "replacement_runs_per_pa": replacement_rate,
        },
        "aggregate": {
            "centered_runs_above_average": float(
                result.get_column("centered_runs_above_average").sum()
            ),
            "replacement_runs": float(result.get_column("replacement_runs").sum()),
            "binding_common_divisor_war": float(
                result.get_column("binding_common_divisor_war").sum()
            ),
            "pythagenpat_wins_above_average": float(
                result.get_column("pythagenpat_wins_above_average").sum()
            ),
            "pythagenpat_replacement_wins": float(
                result.get_column("pythagenpat_replacement_wins").sum()
            ),
            "pythagenpat_war": float(result.get_column("pythagenpat_war").sum()),
            "pythagenpat_minus_binding_war": float(differences.sum()),
        },
        "player_difference_distribution_war": _distribution(differences),
        "largest_absolute_player_differences": largest,
        "boundary": {
            "binding_runs_per_win_changed": False,
            "component_refit": False,
            "replacement_refit": False,
            "zero_exposure_rows_preserved": True,
            "war_ranking_selected": False,
        },
    }
    args.output_table.parent.mkdir(parents=True, exist_ok=True)
    result.write_parquet(args.output_table)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload["aggregate"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
