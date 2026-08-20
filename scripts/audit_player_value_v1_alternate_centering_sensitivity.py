#!/usr/bin/env python
"""Audit whether a complete alternate recent centering surface is frozen."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from universal_baseball.player_value_centering_sensitivity_feasibility import (
    evaluate_centering_sensitivity_feasibility,
)


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _inventory_has_path(inventory: dict[str, Any], suffix: str) -> bool:
    return any(str(row.get("path", "")).endswith(suffix) for row in inventory["files"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/player-value-v1-alternate-centering-sensitivity-feasibility.json"),
    )
    args = parser.parse_args()

    inventory = _json(Path("docs/player-value-v1-mlb-centering-source-inventory.json"))
    playing_time = _json(Path("docs/playing-time-v1-validation-2023-result.json"))
    position = _json(Path("docs/player-value-v1-defensive-position-allocation-result.json"))
    dh = _json(Path("docs/player-value-v1-dh-positional-exposure-selection-result.json"))
    catcher = _json(Path("docs/player-value-v1-catcher-native-opportunity-selection-result.json"))
    steals = _json(Path("docs/player-value-v1-steal-projection-selection-result.json"))
    advancement = _json(Path("docs/player-value-v1-advancement-projection-selection-result.json"))

    b2_available = _inventory_has_path(
        inventory, "batting-b2/tables/projection_2022_to_2023/frozen_b2_profile.parquet"
    )
    projected_pa_available = playing_time.get("status") == "scored" and (
        playing_time.get("validation_fold") == "projection_2022_to_2023"
    )
    position_available = (
        position.get("status") == "binding_v1_position_allocation_selection_complete"
        and "allocation_2022_to_2023" in position.get("fold_coverage", {})
    )
    dh_available = (
        dh.get("status") == "player_value_v1_dh_positional_exposure_frozen"
        and "2022_to_2023" in dh.get("folds", {})
    )
    catcher_available = (
        catcher.get("status") == "player_value_v1_catcher_native_opportunity_forecasts_frozen"
        and "2022_to_2023" in json.dumps(catcher, sort_keys=True)
    )
    baserunning_available = (
        steals.get("status") == "player_value_v1_steal_projection_selection_completed"
        and advancement.get("status") == "player_value_v1_advancement_projection_selection_completed"
        and 2023 in steals.get("source_seasons", [])
    )
    defense_available = (
        _inventory_has_path(
            inventory, "defense-tracked/tables/tracked_range_proxy_2021_2023.parquet"
        )
        and _inventory_has_path(
            inventory, "defense-tracked/tables/tracked_framing_proxy_2021_2023.parquet"
        )
        and catcher_available
    )

    membership_path = Path("docs/player-value-v1-mlb-centering-2023-membership.json")
    batting_reference_paths = (
        Path("docs/player-value-v1-mlb-batting-reference-2023.json"),
        Path("reports/generated/batting_performance_summary_2023_mlb.parquet"),
        Path("reports/generated/batting_performance_bins_2023_mlb.parquet"),
        Path("reports/generated/league_bin_values_2023_mlb.parquet"),
    )
    availability = {
        "official_positive_pa_membership": membership_path.exists(),
        "projected_pa_with_outside_snapshot_fallback": projected_pa_available
        and membership_path.exists(),
        "batting_profile": b2_available,
        "mlb_batting_run_reference": all(path.exists() for path in batting_reference_paths),
        "baserunning_projection": baserunning_available,
        "defense_projection": defense_available,
        "position_and_dh_projection": position_available and dh_available,
    }
    result = evaluate_centering_sensitivity_feasibility(availability)
    if result.complete:
        raise RuntimeError(
            "a complete alternate surface exists; materialize the sensitivity instead of closing it"
        )

    evidence = {
        "official_positive_pa_membership": {
            "available": availability["official_positive_pa_membership"],
            "required_path": membership_path.as_posix(),
            "reason": "no certified 2023 cohort includes an audited outside-snapshot fallback",
        },
        "projected_pa_with_outside_snapshot_fallback": {
            "available": availability["projected_pa_with_outside_snapshot_fallback"],
            "playing_time_run_id": 32141934868,
            "playing_time_artifact_id": 9326237253,
            "playing_time_artifact_digest": "sha256:738c631f5b4fbaa7875219ee452996e487799c4a323b0cafa57a7500583c5b39",
            "reason": "snapshot-player projections exist, but cannot define exposure for uncatalogued official members without the missing membership audit",
        },
        "batting_profile": {
            "available": b2_available,
            "run_id": 32099733186,
            "artifact_id": 9311172007,
            "artifact_digest": "sha256:40430b67a492aec81e570cd67e74ae3ca7b809cb3ce538082237be244c450d44",
        },
        "mlb_batting_run_reference": {
            "available": availability["mlb_batting_run_reference"],
            "required_paths": [path.as_posix() for path in batting_reference_paths],
            "reason": "the frozen centering inventory contains only the certified 2024 MLB batting conversion tables",
        },
        "baserunning_projection": {"available": baserunning_available},
        "defense_projection": {"available": defense_available},
        "position_and_dh_projection": {
            "available": position_available and dh_available,
            "position_run_id": 32266007594,
            "position_artifact_id": 9370211679,
            "dh_run_id": 32270141291,
            "dh_artifact_id": 9371840453,
        },
    }
    payload = {
        "schema_version": "0.1",
        "status": "player_value_v1_alternate_centering_sensitivity_unavailable_verified",
        "contract": "docs/player-value-v1-mlb-centering-contract.md",
        "candidate_reference_season": 2023,
        "scope": "artifacts frozen in the numerical-centering source inventory and committed repository records",
        "source_commit": str(os.environ.get("GITHUB_SHA") or "").strip() or None,
        "actions_run_id": int(os.environ["GITHUB_RUN_ID"]) if os.environ.get("GITHUB_RUN_ID") else None,
        "complete_comparable_surface": result.complete,
        "available_surface_keys": list(result.available_keys),
        "missing_surface_keys": list(result.missing_keys),
        "evidence": evidence,
        "decision": {
            "alternate_centering_constant_materialized": False,
            "partial_season_manufactured": False,
            "sensitivity_obligation_closed_as_unavailable": True,
            "new_source_certification_required_to_reopen": True,
        },
        "boundary": {
            "binding_2024_centering_changed": False,
            "model_refit": False,
            "realized_outcomes_used_as_projection": False,
            "war_calculated": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"complete": result.complete, "missing": result.missing_keys}, indent=2))


if __name__ == "__main__":
    main()
