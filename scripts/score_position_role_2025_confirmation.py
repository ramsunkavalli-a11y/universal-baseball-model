#!/usr/bin/env python3
"""One-shot untouched-2025 confirmation scorer for Position / Role v1.

The scorer reconstructs the frozen candidate from persisted pre-2025 parameters.
It contains no fitting path and does not select thresholds or candidate forms.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from statistics import fmean

import numpy as np
import polars as pl

from universal_baseball.position_role_profile import (
    BATTING_ROLE_POSITIONS,
    build_batting_role_profiles,
)
from universal_baseball.position_role_transition import (
    primary_position,
    summed_squared_error,
    total_variation_distance,
    transition_smoothed_prediction,
    validate_role_vector,
)


CONFIRMATION_PARAMETER_HASH = (
    "sha256:6b6cc7dd5cc7acb7d4396e60dccab12420fdb1828936a318383362d53a9e3def"
)
HISTORICAL_ROLE_PROFILE_SHA256 = (
    "0437003203b349c97ed208f1545cbe6b72970d77837398a4d29e3b7ce8fd3a48"
)
SOURCE_FIELDING_SHA256 = (
    "6a09b5770e2da839e8ef6c8959b7296e334dce4068b21edde2f727cc15f4d4b2"
)
HISTORICAL_RUN_ID = 32149415617
PARAMETER_RUN_ID = 32153160537
SOURCE_RUN_ID = 32153492066


def _find_one(root: Path, filename: str) -> Path:
    matches = sorted(root.rglob(filename))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {filename!r} below {root}, found {len(matches)}")
    return matches[0]


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_2024_profiles(
    historical_root: Path,
) -> tuple[dict[int, np.ndarray], dict[int, dict[str, object]]]:
    profile_path = _find_one(historical_root, "batting_role_profiles_2021_2024.parquet")
    if _file_sha256(profile_path) != HISTORICAL_ROLE_PROFILE_SHA256:
        raise ValueError("historical role-profile parquet hash mismatch")
    summary_path = _find_one(historical_root, "batting_role_player_season_2021_2024.parquet")

    profile_frame = pl.read_parquet(profile_path).filter(pl.col("season") == 2024).select(
        "player_id", "position_abbreviation", "role_probability"
    )
    summary_frame = pl.read_parquet(summary_path).filter(pl.col("season") == 2024).select(
        "player_id", "primary_position", "primary_role_share", "role_evidence_mode"
    )

    profiles: dict[int, np.ndarray] = {}
    for row in profile_frame.iter_rows(named=True):
        player_id = int(row["player_id"])
        position = str(row["position_abbreviation"])
        if position not in BATTING_ROLE_POSITIONS:
            raise ValueError(f"unexpected 2024 role position {position!r}")
        vector = profiles.setdefault(
            player_id, np.zeros(len(BATTING_ROLE_POSITIONS), dtype=float)
        )
        index = BATTING_ROLE_POSITIONS.index(position)
        if vector[index] != 0.0:
            raise ValueError(f"duplicate 2024 player-position row: {player_id} {position}")
        vector[index] = float(row["role_probability"])
    profiles = {player_id: validate_role_vector(vector) for player_id, vector in profiles.items()}

    summaries: dict[int, dict[str, object]] = {}
    for row in summary_frame.iter_rows(named=True):
        player_id = int(row["player_id"])
        if player_id in summaries:
            raise ValueError(f"duplicate 2024 role summary: {player_id}")
        summaries[player_id] = {
            "primary_position": str(row["primary_position"]),
            "primary_role_share": float(row["primary_role_share"]),
            "role_evidence_mode": str(row["role_evidence_mode"]),
        }
    if set(profiles) != set(summaries):
        raise ValueError("2024 profile and summary keys disagree")
    return profiles, summaries


def _load_2025_profiles(
    source_root: Path,
) -> tuple[dict[int, np.ndarray], dict[int, dict[str, object]], dict[str, object]]:
    source_report_path = _find_one(source_root, "report.json")
    source_report = json.loads(source_report_path.read_text())
    if source_report.get("gate") != "position_role_2025_confirmation_source_materialization":
        raise ValueError("unexpected 2025 source report gate")
    if not source_report.get("decision", {}).get("source_materialized"):
        raise ValueError("2025 source report is not accepted")
    if not source_report.get("decision", {}).get("confirmation_scoring_authorized_next"):
        raise ValueError("2025 source report does not authorize confirmation scoring")
    boundary = source_report.get("boundary", {})
    if boundary.get("2025_position_outcomes_scored") is not False:
        raise ValueError("2025 source artifact already claims outcomes were scored")
    if boundary.get("model_parameters_loaded") is not False:
        raise ValueError("2025 source artifact violated parameter/source separation")

    fielding_path = _find_one(source_root, "position_role_2025_fielding_usage.parquet")
    if _file_sha256(fielding_path) != SOURCE_FIELDING_SHA256:
        raise ValueError("2025 source fielding parquet hash mismatch")
    expected_hash = (
        source_report.get("storage", {})
        .get("fielding_usage", {})
        .get("file_sha256")
    )
    if expected_hash != SOURCE_FIELDING_SHA256:
        raise ValueError("2025 source report fielding hash mismatch")

    built = build_batting_role_profiles(pl.read_parquet(fielding_path))
    profile_frame = built.profile.select(
        "player_id", "position_abbreviation", "role_probability"
    )
    summary_frame = built.player_season.select(
        "player_id", "primary_position", "primary_role_share", "role_evidence_mode"
    )

    profiles: dict[int, np.ndarray] = {}
    for row in profile_frame.iter_rows(named=True):
        player_id = int(row["player_id"])
        position = str(row["position_abbreviation"])
        vector = profiles.setdefault(
            player_id, np.zeros(len(BATTING_ROLE_POSITIONS), dtype=float)
        )
        index = BATTING_ROLE_POSITIONS.index(position)
        if vector[index] != 0.0:
            raise ValueError(f"duplicate 2025 player-position row: {player_id} {position}")
        vector[index] = float(row["role_probability"])
    profiles = {player_id: validate_role_vector(vector) for player_id, vector in profiles.items()}

    summaries: dict[int, dict[str, object]] = {}
    for row in summary_frame.iter_rows(named=True):
        player_id = int(row["player_id"])
        summaries[player_id] = {
            "primary_position": str(row["primary_position"]),
            "primary_role_share": float(row["primary_role_share"]),
            "role_evidence_mode": str(row["role_evidence_mode"]),
        }
    if set(profiles) != set(summaries):
        raise ValueError("2025 profile and summary keys disagree")
    return profiles, summaries, source_report


def _load_parameters(parameter_root: Path) -> tuple[float, dict[str, np.ndarray], dict[str, object]]:
    parameter_path = _find_one(parameter_root, "parameters.json")
    report = json.loads(parameter_path.read_text())
    if report.get("gate") != "position_role_2025_confirmation_parameter_freeze":
        raise ValueError("unexpected confirmation parameter gate")
    if report.get("parameter_hash") != CONFIRMATION_PARAMETER_HASH:
        raise ValueError("persisted confirmation parameter hash changed")
    if not report.get("decision", {}).get("confirmation_parameters_frozen"):
        raise ValueError("confirmation parameters are not frozen")
    boundary = report.get("boundary", {})
    if boundary.get("2025_position_source_accessed") is not False:
        raise ValueError("parameter artifact was created after 2025 source access")
    if boundary.get("training_transitions_end_in_2024") is not True:
        raise ValueError("parameter artifact training boundary is not pre-2025")

    parameters = report["parameters"]
    canonical = json.dumps(parameters, sort_keys=True, separators=(",", ":")).encode("utf-8")
    computed_hash = "sha256:" + sha256(canonical).hexdigest()
    if computed_hash != CONFIRMATION_PARAMETER_HASH:
        raise ValueError("confirmation parameter core hash mismatch")
    if parameters.get("position_order") != list(BATTING_ROLE_POSITIONS):
        raise ValueError("confirmation position ordering changed")
    threshold = float(parameters["primary_share_threshold"])
    if threshold != 0.65:
        raise ValueError(f"confirmation threshold changed: {threshold}")

    destination_means: dict[str, np.ndarray] = {}
    raw_means = parameters["destination_means"]
    for position in BATTING_ROLE_POSITIONS:
        if position not in raw_means:
            raise ValueError(f"missing frozen destination mean for {position}")
        probabilities = raw_means[position]["probabilities"]
        vector = np.array(
            [float(probabilities[destination]) for destination in BATTING_ROLE_POSITIONS],
            dtype=float,
        )
        destination_means[position] = validate_role_vector(vector)
    return threshold, destination_means, report


def _share_band(share: float) -> str:
    if share < 0.50:
        return "lt_0.50"
    if share < 0.65:
        return "0.50_to_0.65"
    if share < 0.75:
        return "0.65_to_0.75"
    if share < 0.85:
        return "0.75_to_0.85"
    return "ge_0.85"


def _diagnostics(frame: pl.DataFrame, by: list[str]) -> list[dict[str, object]]:
    return (
        frame.group_by(by)
        .agg(
            pl.len().alias("player_count"),
            pl.col("smoothing_active").mean().alias("smoothing_active_rate"),
            pl.col("baseline_tv").mean().alias("baseline_mean_tv"),
            pl.col("candidate_tv").mean().alias("candidate_mean_tv"),
            pl.col("baseline_sse").mean().alias("baseline_mean_sse"),
            pl.col("candidate_sse").mean().alias("candidate_mean_sse"),
            pl.col("baseline_primary_correct").mean().alias("baseline_primary_match_rate"),
            pl.col("candidate_primary_correct").mean().alias("candidate_primary_match_rate"),
        )
        .sort(by)
        .to_dicts()
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--parameter-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/position-role-2025-confirmation"),
    )
    args = parser.parse_args()

    profiles_2024, summaries_2024 = _load_2024_profiles(args.historical_root)
    threshold, destination_means, parameter_report = _load_parameters(args.parameter_root)
    profiles_2025, summaries_2025, source_report = _load_2025_profiles(args.source_root)

    players = sorted(set(profiles_2024) & set(profiles_2025))
    if not players:
        raise ValueError("2024->2025 confirmation population is empty")

    rows: list[dict[str, object]] = []
    baseline_tv_values: list[float] = []
    candidate_tv_values: list[float] = []
    baseline_sse_values: list[float] = []
    candidate_sse_values: list[float] = []
    smoothing_count = 0
    baseline_primary_correct = 0
    candidate_primary_correct = 0

    for player_id in players:
        current = profiles_2024[player_id]
        observed = profiles_2025[player_id]
        summary_2024 = summaries_2024[player_id]
        current_primary = str(summary_2024["primary_position"])
        share = float(summary_2024["primary_role_share"])
        smoothing_active = share >= threshold
        if smoothing_active:
            candidate = transition_smoothed_prediction(
                current,
                primary_share=share,
                destination_mean=destination_means[current_primary],
            )
            smoothing_count += 1
        else:
            candidate = current.copy()

        baseline = current
        observed_primary = str(summaries_2025[player_id]["primary_position"])
        baseline_primary = current_primary
        candidate_primary = primary_position(candidate)
        baseline_correct = baseline_primary == observed_primary
        candidate_correct = candidate_primary == observed_primary
        baseline_primary_correct += int(baseline_correct)
        candidate_primary_correct += int(candidate_correct)

        baseline_tv = total_variation_distance(baseline, observed)
        candidate_tv = total_variation_distance(candidate, observed)
        baseline_sse = summed_squared_error(baseline, observed)
        candidate_sse = summed_squared_error(candidate, observed)
        baseline_tv_values.append(baseline_tv)
        candidate_tv_values.append(candidate_tv)
        baseline_sse_values.append(baseline_sse)
        candidate_sse_values.append(candidate_sse)

        row: dict[str, object] = {
            "player_id": player_id,
            "current_primary_position": current_primary,
            "current_primary_share": share,
            "primary_share_band": _share_band(share),
            "smoothing_active": smoothing_active,
            "observed_primary_position": observed_primary,
            "baseline_primary_position": baseline_primary,
            "candidate_primary_position": candidate_primary,
            "baseline_primary_correct": baseline_correct,
            "candidate_primary_correct": candidate_correct,
            "baseline_tv": baseline_tv,
            "candidate_tv": candidate_tv,
            "baseline_sse": baseline_sse,
            "candidate_sse": candidate_sse,
        }
        for index, position in enumerate(BATTING_ROLE_POSITIONS):
            row[f"current_{position}"] = float(current[index])
            row[f"observed_{position}"] = float(observed[index])
            row[f"candidate_{position}"] = float(candidate[index])
        rows.append(row)

    baseline_mean_tv = fmean(baseline_tv_values)
    candidate_mean_tv = fmean(candidate_tv_values)
    baseline_mean_sse = fmean(baseline_sse_values)
    candidate_mean_sse = fmean(candidate_sse_values)
    confirmed = candidate_mean_tv < baseline_mean_tv and candidate_mean_sse < baseline_mean_sse

    prediction_frame = pl.DataFrame(rows)
    frozen_model = (
        "primary_share_thresholded_transition_mean_v1"
        if confirmed
        else "raw_role_profile_carry_forward_v1"
    )
    report = {
        "report_schema_version": "0.1",
        "gate": "position_role_2025_untouched_confirmation",
        "contract": "docs/position-role-2025-confirmation-contract.md",
        "population": {
            "rule": "valid 2024 role profile AND valid 2025 role profile",
            "scored_player_count": len(players),
            "smoothing_active_player_count": smoothing_count,
            "smoothing_active_rate": smoothing_count / len(players),
        },
        "inputs": {
            "historical_run_id": HISTORICAL_RUN_ID,
            "historical_role_profile_sha256": HISTORICAL_ROLE_PROFILE_SHA256,
            "parameter_run_id": PARAMETER_RUN_ID,
            "parameter_hash": CONFIRMATION_PARAMETER_HASH,
            "source_run_id": SOURCE_RUN_ID,
            "source_fielding_sha256": SOURCE_FIELDING_SHA256,
            "source_report_run_id": source_report.get("source_run_id"),
            "parameter_report_run_id": parameter_report.get("source_run_id"),
        },
        "candidate": {
            "name": "primary_share_thresholded_transition_mean_v1",
            "primary_share_threshold": threshold,
            "parameters_reconstructed_from_frozen_artifact": True,
        },
        "metrics": {
            "baseline_mean_tv": baseline_mean_tv,
            "candidate_mean_tv": candidate_mean_tv,
            "tv_absolute_improvement": baseline_mean_tv - candidate_mean_tv,
            "tv_relative_improvement": (baseline_mean_tv - candidate_mean_tv) / baseline_mean_tv,
            "baseline_mean_sse": baseline_mean_sse,
            "candidate_mean_sse": candidate_mean_sse,
            "sse_absolute_improvement": baseline_mean_sse - candidate_mean_sse,
            "sse_relative_improvement": (baseline_mean_sse - candidate_mean_sse) / baseline_mean_sse,
            "baseline_primary_match_rate": baseline_primary_correct / len(players),
            "candidate_primary_match_rate": candidate_primary_correct / len(players),
        },
        "diagnostics": {
            "by_2024_primary_position": _diagnostics(
                prediction_frame, ["current_primary_position"]
            ),
            "by_2024_primary_share_band": _diagnostics(
                prediction_frame, ["primary_share_band"]
            ),
        },
        "boundary": {
            "2025_position_source_accessed": True,
            "2025_position_outcomes_scored": True,
            "fitting_function_called": False,
            "parameters_refit": False,
            "threshold_changed": False,
            "candidate_reselected": False,
            "team_allocator_fit": False,
            "defense_model_fit": False,
        },
        "decision": {
            "confirmed": confirmed,
            "position_role_v1_frozen": True,
            "frozen_position_role_v1": frozen_model,
            "additional_2025_tuning_authorized": False,
            "team_allocator_authorized": False,
            "defense_model_authorized": False,
        },
    }

    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    prediction_frame.write_parquet(args.output_root / "confirmation_predictions.parquet")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
