#!/usr/bin/env python3
"""Freeze Player Value v1 Defense run-conversion parameters from the completed pre-2025 audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CONTRACT_SHA256 = "577dabe03ab669036132cafa141a54e41b912af00269d8377cad08764d72006a"
CALIBRATION_CONTRACT_SHA256 = "276481bc343245ce0b8ea82373286faa347a17d8d0bda13915865d743f72ad0b"
CALIBRATION_RUN_ID = 32267920355
CALIBRATION_SOURCE_SHA = "f2bddb23e38b5a42a413cc20fc1f6feb5fbeaa0f"
CALIBRATION_ARTIFACT = "player-value-v1-defense-native-run-rate-calibration"
CALIBRATION_ARTIFACT_DIGEST = "sha256:d78d857ebe608d5fe86e29cc57db66bb2d1e68fd0636683148ff97e0f4ffb934"
GENERAL_POSITIONS = ("1B", "2B", "3B", "SS", "LF", "CF", "RF")
GROUP_BY_POSITION = {
    "1B": "IF",
    "2B": "IF",
    "3B": "IF",
    "SS": "IF",
    "LF": "OF",
    "CF": "OF",
    "RF": "OF",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--contract-path",
        type=Path,
        default=Path("docs/player-value-v1-defense-native-run-conversion-selection-contract.md"),
    )
    parser.add_argument(
        "--calibration-result",
        type=Path,
        default=Path("docs/player-value-v1-defense-native-run-rate-calibration-result.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/generated/player-value-v1-defense-native-run-conversion/parameters.json"),
    )
    return parser.parse_args()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable(metrics: dict[str, Any], *, cv_limit: float, ratio_limit: float) -> bool:
    cv = metrics.get("coefficient_of_variation")
    ratio = metrics.get("max_to_min_ratio")
    return bool(
        metrics.get("all_positive") is True
        and cv is not None
        and float(cv) <= cv_limit
        and ratio is not None
        and float(ratio) <= ratio_limit
    )


def _gate_snapshot(metrics: dict[str, Any], *, cv_limit: float, ratio_limit: float) -> dict[str, Any]:
    return {
        "all_positive": bool(metrics.get("all_positive")),
        "coefficient_of_variation": metrics.get("coefficient_of_variation"),
        "cv_limit": cv_limit,
        "cv_pass": metrics.get("coefficient_of_variation") is not None
        and float(metrics["coefficient_of_variation"]) <= cv_limit,
        "max_to_min_ratio": metrics.get("max_to_min_ratio"),
        "ratio_limit": ratio_limit,
        "ratio_pass": metrics.get("max_to_min_ratio") is not None
        and float(metrics["max_to_min_ratio"]) <= ratio_limit,
        "passes": _stable(metrics, cv_limit=cv_limit, ratio_limit=ratio_limit),
    }


def main() -> int:
    args = _parse_args()
    observed_contract = _sha256(args.contract_path)
    if observed_contract != CONTRACT_SHA256:
        raise RuntimeError(
            f"selection contract mismatch: expected {CONTRACT_SHA256}, observed {observed_contract}"
        )

    calibration = json.loads(args.calibration_result.read_text())
    if calibration.get("contract_sha256") != CALIBRATION_CONTRACT_SHA256:
        raise RuntimeError("unexpected calibration contract hash")
    if int(calibration.get("source_run_id", -1)) != CALIBRATION_RUN_ID:
        raise RuntimeError("unexpected calibration run id")
    if calibration.get("source_sha") != CALIBRATION_SOURCE_SHA:
        raise RuntimeError("unexpected calibration source sha")
    boundary = calibration.get("boundary") or {}
    if boundary.get("2025_data_accessed") is not False:
        raise RuntimeError("calibration boundary does not prove 2025 stayed closed")
    if boundary.get("defense_refit") is not False:
        raise RuntimeError("calibration boundary indicates Defense refit")

    general = calibration["general_range"]
    position_stability = general["stability_by_position"]
    group_stability = general["stability_by_group"]
    general_parameters: dict[str, Any] = {}
    unresolved: list[str] = []

    for position in GENERAL_POSITIONS:
        own = position_stability[position]
        group = GROUP_BY_POSITION[position]
        group_metrics = group_stability[group]
        own_gate = _gate_snapshot(own, cv_limit=0.15, ratio_limit=1.50)
        group_gate = _gate_snapshot(group_metrics, cv_limit=0.15, ratio_limit=1.50)
        if own_gate["passes"]:
            selected_scale = float(own["median_slope"])
            source = f"position_{position}_median_2022_2024"
            used_group_fallback = False
        elif group_gate["passes"]:
            selected_scale = float(group_metrics["median_slope"])
            source = f"group_{group}_median_2022_2024"
            used_group_fallback = True
        else:
            unresolved.append(f"general_range:{position}")
            selected_scale = None
            source = None
            used_group_fallback = True
        general_parameters[position] = {
            "run_rate_per_z_opportunity": selected_scale,
            "native_opportunity": "projected_mlb_defensive_outs_at_position",
            "calibration_source": source,
            "used_group_fallback": used_group_fallback,
            "position_gate": own_gate,
            "group": group,
            "group_gate": group_gate,
        }

    throwing_stability = calibration["catcher_throwing"]["stability"]
    throwing_gate = _gate_snapshot(throwing_stability, cv_limit=0.10, ratio_limit=1.25)
    if not throwing_gate["passes"]:
        unresolved.append("catcher_throwing")

    blocking = calibration["catcher_blocking"]
    blocking_stability = blocking["stability_by_opportunity"]["pitches"]
    blocking_gate = _gate_snapshot(blocking_stability, cv_limit=0.10, ratio_limit=1.25)
    rmse_year_checks: dict[str, bool] = {}
    for year in ("2022", "2023", "2024"):
        calibrations = blocking["by_year"][year]["calibrations"]
        pitch_rmse = float(calibrations["pitches"]["run_rmse"])
        n_pbwp_rmse = float(calibrations["n_pbwp"]["run_rmse"])
        rmse_year_checks[year] = pitch_rmse < n_pbwp_rmse
    blocking_rmse_gate = all(rmse_year_checks.values())
    if not (blocking_gate["passes"] and blocking_rmse_gate):
        unresolved.append("catcher_blocking")

    framing_stability = calibration["catcher_framing"]["stability"]
    framing_gate = _gate_snapshot(framing_stability, cv_limit=0.10, ratio_limit=1.25)
    if not framing_gate["passes"]:
        unresolved.append("catcher_framing")

    if unresolved:
        raise RuntimeError(f"run conversion unresolved under frozen gates: {unresolved}")

    parameters = {
        "schema_version": "0.1",
        "status": "player_value_v1_defense_native_run_conversion_frozen",
        "contract": "docs/player-value-v1-defense-native-run-conversion-selection-contract.md",
        "contract_sha256": observed_contract,
        "calibration_provenance": {
            "result": "docs/player-value-v1-defense-native-run-rate-calibration-result.json",
            "contract_sha256": CALIBRATION_CONTRACT_SHA256,
            "source_run_id": CALIBRATION_RUN_ID,
            "source_sha": CALIBRATION_SOURCE_SHA,
            "artifact_name": CALIBRATION_ARTIFACT,
            "artifact_digest": CALIBRATION_ARTIFACT_DIGEST,
            "target_years": [2022, 2023, 2024],
        },
        "formula": "component_runs = frozen_skill_z * projected_native_opportunities * run_rate_per_z_opportunity",
        "intercept": 0.0,
        "neutral_skill_maps_to_zero_runs": True,
        "general_range": {
            "parameters_by_position": general_parameters,
            "multi_position_rule": "calculate by projected position outs and sum",
            "T1_U1_share_same_conversion_rule": True,
        },
        "catcher_throwing": {
            "run_rate_per_z_opportunity": float(throwing_stability["median_slope"]),
            "native_opportunity": "projected_sb_attempts",
            "calibration_source": "median_2022_2024_through_origin_slope",
            "gate": throwing_gate,
            "source_identity": "caught_stealing_above_average = cs_aa_per_throw * sb_attempts",
            "public_run_identity": "catcher_stealing_runs = 0.65 * caught_stealing_above_average",
        },
        "catcher_blocking": {
            "run_rate_per_z_opportunity": float(blocking_stability["median_slope"]),
            "native_opportunity": "projected_blocking_pitches",
            "calibration_source": "median_2022_2024_pitches_through_origin_slope",
            "gate": blocking_gate,
            "pitches_rmse_lower_than_n_pbwp_every_year": blocking_rmse_gate,
            "rmse_year_checks": rmse_year_checks,
            "n_pbwp_rejected_as_native_opportunity": True,
            "public_methodology": "40 blocking chances per game; 0.25 runs per block saved",
        },
        "catcher_framing": {
            "run_rate_per_z_opportunity": float(framing_stability["median_slope"]),
            "native_opportunity": "projected_framing_pitches",
            "calibration_source": "median_2022_2024_through_origin_slope",
            "gate": framing_gate,
            "native_source_identity": "target_raw = 1000 * rv_tot / pitches; rv_tot is seasonal runs",
        },
        "unresolved_components": [],
        "catcher_opportunity_forecasting_frozen": False,
        "positional_adjustment_frozen": False,
        "replacement_level_frozen": False,
        "runs_per_win_frozen": False,
        "war_value_authorized": False,
        "boundary": {
            "2025_data_accessed": False,
            "2025_confirmation_residuals_used": False,
            "defense_refit": False,
            "defense_rescored": False,
            "playing_time_refit": False,
            "position_role_refit": False,
            "general_defensive_exposure_changed": False,
            "catcher_opportunity_forecast_selected": False,
            "positional_adjustment_calculated": False,
            "war_value_calculated": False,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(parameters, indent=2, sort_keys=True) + "\n")
    print(json.dumps(parameters, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
