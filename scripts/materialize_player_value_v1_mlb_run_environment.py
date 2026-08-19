from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from universal_baseball.player_value_mlb_run_environment import fetch_mlb_run_environment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    env = fetch_mlb_run_environment(args.season)
    rpw = env.runs_per_win
    if not (3.0 < rpw.mlb_runs_per_9_innings < 6.5):
        raise RuntimeError(f"implausible MLB runs/9: {rpw.mlb_runs_per_9_innings}")
    if not (7.5 < rpw.runs_per_win < 13.0):
        raise RuntimeError(f"implausible MLB runs per win: {rpw.runs_per_win}")

    payload = {
        "schema_version": "0.1",
        "status": "player_value_v1_mlb_run_environment_materialized",
        "season": env.season,
        "batting_runs_scored": env.batting_runs_scored,
        "pitching_runs_allowed": env.pitching_runs_allowed,
        "pitching_outs": env.pitching_outs,
        "innings_pitched": env.innings_pitched,
        "mlb_runs_per_9_innings": rpw.mlb_runs_per_9_innings,
        "runs_per_win": rpw.runs_per_win,
        "runs_per_win_convention_id": rpw.convention_id,
        "reconciliation": {
            "batting_runs_equal_pitching_runs": env.batting_runs_scored == env.pitching_runs_allowed,
        },
        "captures": [asdict(capture) for capture in env.captures],
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
