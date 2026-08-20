#!/usr/bin/env python3
"""Freeze pre-2025 Position / Role v1 confirmation parameters."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.position_role_profile import BATTING_ROLE_POSITIONS
from universal_baseball.position_role_transition import (
    fit_primary_destination_means,
    validate_role_vector,
)


THRESHOLD = 0.65
TRAINING_TRANSITIONS = ((2021, 2022), (2022, 2023), (2023, 2024))
SOURCE_RUN_ID = 32149415617
SOURCE_ARTIFACT = "position-role-batting-profile-stability-2021-2024"
SOURCE_ARTIFACT_DIGEST = "sha256:a2c5aa7cbc5f9bfaadcab9597a9b228c8f32463c09c88097052bcfec78cdeb26"


def _find_one(root: Path, filename: str) -> Path:
    matches = sorted(root.rglob(filename))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {filename!r} below {root}, found {len(matches)}")
    return matches[0]


def _load_profiles(source_root: Path) -> tuple[
    dict[tuple[int, int], np.ndarray],
    dict[tuple[int, int], tuple[str, float]],
]:
    profile_frame = pl.read_parquet(
        _find_one(source_root, "batting_role_profiles_2021_2024.parquet")
    ).select("season", "player_id", "position_abbreviation", "role_probability")
    summary_frame = pl.read_parquet(
        _find_one(source_root, "batting_role_player_season_2021_2024.parquet")
    ).select("season", "player_id", "primary_position", "primary_role_share")

    profiles: dict[tuple[int, int], np.ndarray] = {}
    for row in profile_frame.iter_rows(named=True):
        key = (int(row["season"]), int(row["player_id"]))
        position = str(row["position_abbreviation"])
        if position not in BATTING_ROLE_POSITIONS:
            raise ValueError(f"unexpected role position {position!r}")
        vector = profiles.setdefault(key, np.zeros(len(BATTING_ROLE_POSITIONS), dtype=float))
        index = BATTING_ROLE_POSITIONS.index(position)
        if vector[index] != 0.0:
            raise ValueError(f"duplicate role position row for {key}: {position}")
        vector[index] = float(row["role_probability"])
    profiles = {key: validate_role_vector(value) for key, value in profiles.items()}

    summaries: dict[tuple[int, int], tuple[str, float]] = {}
    for row in summary_frame.iter_rows(named=True):
        key = (int(row["season"]), int(row["player_id"]))
        if key in summaries:
            raise ValueError(f"duplicate player-season summary row: {key}")
        position = str(row["primary_position"])
        share = float(row["primary_role_share"])
        if position not in BATTING_ROLE_POSITIONS:
            raise ValueError(f"unexpected primary position {position!r}")
        if not 0.0 <= share <= 1.0:
            raise ValueError(f"invalid primary share {share} for {key}")
        summaries[key] = (position, share)

    if set(profiles) != set(summaries):
        raise ValueError("profile and summary player-season keys disagree")
    return profiles, summaries


def _paired_players(
    profiles: dict[tuple[int, int], np.ndarray], current_season: int, next_season: int
) -> list[int]:
    current = {player_id for season, player_id in profiles if season == current_season}
    future = {player_id for season, player_id in profiles if season == next_season}
    return sorted(current & future)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/position-role-confirmation-parameters"),
    )
    args = parser.parse_args()

    profiles, summaries = _load_profiles(args.source_root)
    samples: dict[str, list[np.ndarray]] = {position: [] for position in BATTING_ROLE_POSITIONS}
    transition_counts: list[dict[str, int]] = []
    for current_season, next_season in TRAINING_TRANSITIONS:
        players = _paired_players(profiles, current_season, next_season)
        transition_counts.append(
            {
                "current_season": current_season,
                "next_season": next_season,
                "paired_player_count": len(players),
            }
        )
        for player_id in players:
            current_key = (current_season, player_id)
            next_key = (next_season, player_id)
            primary_position, _ = summaries[current_key]
            samples[primary_position].append(profiles[next_key])

    means, counts = fit_primary_destination_means(samples)
    destination_means = {
        position: {
            "training_transition_count": counts[position],
            "probabilities": {
                destination: float(means[position][index])
                for index, destination in enumerate(BATTING_ROLE_POSITIONS)
            },
        }
        for position in BATTING_ROLE_POSITIONS
    }

    parameter_core = {
        "model_name": "primary_share_thresholded_transition_mean_v1",
        "position_order": list(BATTING_ROLE_POSITIONS),
        "primary_share_threshold": THRESHOLD,
        "formula": "carry_forward if s < 0.65 else s * current_profile + (1 - s) * frozen_mean_next_profile_by_current_primary_position",
        "training_transitions": [list(pair) for pair in TRAINING_TRANSITIONS],
        "training_transition_counts": transition_counts,
        "destination_means": destination_means,
        "source": {
            "run_id": SOURCE_RUN_ID,
            "artifact_name": SOURCE_ARTIFACT,
            "artifact_digest": SOURCE_ARTIFACT_DIGEST,
        },
    }
    canonical = json.dumps(parameter_core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    parameter_hash = "sha256:" + sha256(canonical).hexdigest()

    report = {
        "report_schema_version": "0.1",
        "gate": "position_role_2025_confirmation_parameter_freeze",
        "contract": "docs/position-role-2025-confirmation-contract.md",
        "parameters": parameter_core,
        "parameter_hash": parameter_hash,
        "boundary": {
            "2025_position_source_accessed": False,
            "2025_position_outcomes_scored": False,
            "training_transitions_end_in_2024": True,
            "hyperparameter_search": False,
            "team_allocator_fit": False,
            "defense_model_fit": False,
        },
        "decision": {
            "confirmation_parameters_frozen": True,
            "2025_position_source_materialization_authorized": True,
            "confirmation_scoring_authorized": False,
        },
    }

    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "parameters.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    mean_rows = []
    for position in BATTING_ROLE_POSITIONS:
        row: dict[str, object] = {
            "current_primary_position": position,
            "training_transition_count": counts[position],
        }
        for index, destination in enumerate(BATTING_ROLE_POSITIONS):
            row[f"mean_next_{destination}"] = float(means[position][index])
        mean_rows.append(row)
    pl.DataFrame(mean_rows).write_parquet(args.output_root / "transition_means.parquet")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
