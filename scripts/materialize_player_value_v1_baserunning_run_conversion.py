#!/usr/bin/env python
"""Materialize the frozen 2024 Player Value v1 baserunning reference constants."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path

from universal_baseball.player_value_baserunning_runs import (
    build_baserunning_reference,
    project_steal_runs,
)


EXPECTED_ATTEMPT_CANDIDATE = "B2_k5"
EXPECTED_SUCCESS_CANDIDATE = "B2_k45"
EXPECTED_ADVANCEMENT_CANDIDATE = "A2_k25"


def _read_json(path: Path) -> dict:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object in {path}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-environment",
        type=Path,
        default=Path("docs/player-value-v1-mlb-run-environment-2024.json"),
    )
    parser.add_argument(
        "--steal-selection",
        type=Path,
        default=Path("docs/player-value-v1-steal-projection-selection-result.json"),
    )
    parser.add_argument(
        "--advancement-selection",
        type=Path,
        default=Path(
            "docs/player-value-v1-advancement-projection-selection-result.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/player-value-v1-baserunning-run-conversion-2024.json"),
    )
    args = parser.parse_args()

    run_environment = _read_json(args.run_environment)
    steal_selection = _read_json(args.steal_selection)
    advancement_selection = _read_json(args.advancement_selection)

    if int(run_environment.get("season", -1)) != 2024:
        raise ValueError("run environment must be the certified 2024 MLB reference")
    if steal_selection.get("attempt_propensity", {}).get("frozen_candidate_id") != EXPECTED_ATTEMPT_CANDIDATE:
        raise ValueError("unexpected frozen steal attempt candidate")
    if steal_selection.get("success_skill", {}).get("frozen_candidate_id") != EXPECTED_SUCCESS_CANDIDATE:
        raise ValueError("unexpected frozen steal success candidate")
    if advancement_selection.get("frozen_candidate_id") != EXPECTED_ADVANCEMENT_CANDIDATE:
        raise ValueError("unexpected frozen advancement candidate")
    if advancement_selection.get("confirmation_passed") is not True:
        raise ValueError("advancement selection has not passed held-out confirmation")

    steal_reference = steal_selection.get("mlb_2024_full_population_reference") or {}
    advancement_reference = advancement_selection.get("mlb_2024_advancement_reference") or {}

    run_environment_pa = float(run_environment["batting_plate_appearances"])
    steal_reference_pa = float(steal_reference["plate_appearances"])
    if run_environment_pa != steal_reference_pa:
        raise ValueError(
            "2024 MLB PA mismatch between run environment and steal reference: "
            f"{run_environment_pa} != {steal_reference_pa}"
        )

    steal_attempts = float(steal_reference["steal_attempts"])
    stolen_bases = float(steal_reference["stolen_bases"])
    caught_stealing = float(steal_reference["caught_stealing"])
    if abs((steal_attempts - stolen_bases) - caught_stealing) > 1e-9:
        raise ValueError("2024 steal reference violates attempts = SB + CS")

    reference = build_baserunning_reference(
        season=2024,
        plate_appearances=run_environment_pa,
        runs=float(run_environment["batting_runs_scored"]),
        outs=float(run_environment["pitching_outs"]),
        steal_opportunity_proxy=float(steal_reference["opportunity_proxy"]),
        steal_attempts=steal_attempts,
        stolen_bases=stolen_bases,
        advancement_opportunities=float(
            advancement_reference["nonsteal_advancement_opportunities"]
        ),
    )

    neutral_steal_runs_600_pa = project_steal_runs(
        projected_mlb_pa=600.0,
        attempt_multiplier=1.0,
        success_logodds_residual=0.0,
        reference=reference,
    )[-1]
    if abs(neutral_steal_runs_600_pa) > 1e-10:
        raise ValueError(
            "neutral steal run conversion is not centered: "
            f"{neutral_steal_runs_600_pa}"
        )

    payload = {
        "status": "player_value_v1_baserunning_run_conversion_frozen",
        "schema_version": "0.1",
        "season": 2024,
        "verified_source_commit": str(os.environ.get("GITHUB_SHA") or "").strip()
        or None,
        "contract": "docs/player-value-v1-baserunning-run-conversion-contract.md",
        "upstream_artifacts": {
            "mlb_run_environment": str(args.run_environment),
            "steal_selection": str(args.steal_selection),
            "advancement_selection": str(args.advancement_selection),
        },
        "frozen_models": {
            "steal_attempt_propensity": EXPECTED_ATTEMPT_CANDIDATE,
            "steal_success_skill": EXPECTED_SUCCESS_CANDIDATE,
            "nonsteal_advancement": EXPECTED_ADVANCEMENT_CANDIDATE,
            "gidp_residual": "G0_omitted_v1",
        },
        "reference": {
            **asdict(reference),
            "caught_stealing": caught_stealing,
        },
        "gidp_residual_authorized": False,
        "baserunning_formula": "Rbr = Rsteal + Radvance; Rgidp_residual = 0",
        "verification": {
            "mlb_pa_reconciled_across_upstream_artifacts": True,
            "steal_attempts_equal_sb_plus_cs": True,
            "neutral_steal_runs_600_pa": neutral_steal_runs_600_pa,
            "neutral_steal_centered_within_1e-10": True,
            "advancement_confirmation_passed": True,
        },
        "notes": [
            "Steal conversion follows the public FanGraphs wSB opportunity-centering convention with the certified 2024 MLB run environment.",
            "Non-steal advancement uses source-defined Savant run value and a common 2024 MLB advancement-opportunity rate per projected MLB PA.",
            "Raw GIDP is non-additive with the frozen RE24 batting bins; the separate residual is explicitly omitted for v1 after the direct opportunity-source audit failed.",
            "Final MLB-reference centering remains a separate downstream gate.",
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
