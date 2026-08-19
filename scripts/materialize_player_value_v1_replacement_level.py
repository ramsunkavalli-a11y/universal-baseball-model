from __future__ import annotations

import argparse
import json
from pathlib import Path

from universal_baseball.player_value_replacement_level import (
    BREF_POSITION_PLAYER_WAR_ALLOCATION_SENSITIVITY,
    LEGACY_REPLACEMENT_RUNS_PER_600_PA,
    REPLACEMENT_LEVEL_CONVENTION_ID,
    build_replacement_reference,
    build_v1_replacement_reference,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-environment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    environment = json.loads(args.reference_environment.read_text())
    required = {
        "season",
        "regular_season_games",
        "batting_plate_appearances",
        "runs_per_win",
        "runs_per_win_convention_id",
    }
    missing = sorted(required - set(environment))
    if missing:
        raise RuntimeError(f"reference environment missing fields: {missing}")
    if environment["runs_per_win_convention_id"] != "fangraphs_tango_league_rpw_v1":
        raise RuntimeError("replacement materializer requires the frozen FanGraphs/Tango RPW")

    season = int(environment["season"])
    games = environment["regular_season_games"]
    pa = environment["batting_plate_appearances"]
    rpw = environment["runs_per_win"]

    binding = build_v1_replacement_reference(
        games,
        pa,
        rpw,
        reference_season=season,
    )
    bref = build_replacement_reference(
        games,
        pa,
        rpw,
        reference_season=season,
        position_player_war_allocation=BREF_POSITION_PLAYER_WAR_ALLOCATION_SENSITIVITY,
        convention_id="baseball_reference_590_war_pool_sensitivity",
    )

    if not (15.0 < binding.replacement_runs_per_600_pa < 22.0):
        raise RuntimeError(
            f"implausible binding replacement runs/600: {binding.replacement_runs_per_600_pa}"
        )
    if bref.replacement_runs_per_600_pa <= binding.replacement_runs_per_600_pa:
        raise RuntimeError("590-WAR sensitivity must exceed 570-WAR binding replacement rate")

    payload = {
        "schema_version": "0.2",
        "status": "player_value_v1_replacement_level_materialized",
        "convention_id": REPLACEMENT_LEVEL_CONVENTION_ID,
        "reference_season": binding.reference_season,
        "reference_environment": {
            "mlb_regular_season_games": binding.mlb_regular_season_games,
            "mlb_plate_appearances": binding.mlb_plate_appearances,
            "runs_per_win": binding.runs_per_win,
            "source_artifact": str(args.reference_environment),
        },
        "binding": {
            "position_player_war_allocation": binding.position_player_war_allocation,
            "replacement_war_pool": binding.replacement_war_pool,
            "replacement_runs_per_pa": binding.replacement_runs_per_pa,
            "replacement_runs_per_600_pa": binding.replacement_runs_per_600_pa,
        },
        "sensitivities": {
            "baseball_reference_590_war_pool": {
                "position_player_war_allocation": bref.position_player_war_allocation,
                "replacement_war_pool": bref.replacement_war_pool,
                "replacement_runs_per_pa": bref.replacement_runs_per_pa,
                "replacement_runs_per_600_pa": bref.replacement_runs_per_600_pa,
            },
            "legacy_fixed_20_5_runs_per_600_pa": {
                "replacement_runs_per_600_pa": LEGACY_REPLACEMENT_RUNS_PER_600_PA,
            },
        },
        "boundary": {
            "baserunning_frozen": False,
            "mlb_reference_centering_frozen": False,
            "park_neutrality_audited": False,
            "war_value_calculated": False,
        },
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
