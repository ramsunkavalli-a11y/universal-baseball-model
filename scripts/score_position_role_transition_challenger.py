#!/usr/bin/env python3
"""Score the frozen chronology-safe batting position-role challenger."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import fmean

import numpy as np
import polars as pl

from universal_baseball.position_role_profile import BATTING_ROLE_POSITIONS
from universal_baseball.position_role_transition import (
    fit_primary_destination_means,
    primary_position,
    summed_squared_error,
    total_variation_distance,
    transition_smoothed_prediction,
    validate_role_vector,
)


SOURCE_RUN_ID = 32149415617
SOURCE_ARTIFACT = "position-role-batting-profile-stability-2021-2024"
SOURCE_ARTIFACT_DIGEST = "sha256:a2c5aa7cbc5f9bfaadcab9597a9b228c8f32463c09c88097052bcfec78cdeb26"
EVAL_FOLDS = (
    (2022, 2023, ((2021, 2022),)),
    (2023, 2024, ((2021, 2022), (2022, 2023))),
)


def _find_one(root: Path, filename: str) -> Path:
    matches = sorted(root.rglob(filename))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {filename!r} below {root}, found {len(matches)}")
    return matches[0]


def _load_profiles(source_root: Path) -> tuple[dict[tuple[int, int], np.ndarray], dict[tuple[int, int], dict[str, object]]]:
    profile_path = _find_one(source_root, "batting_role_profiles_2021_2024.parquet")
    summary_path = _find_one(source_root, "batting_role_player_season_2021_2024.parquet")

    profile_frame = pl.read_parquet(profile_path).select(
        "season", "player_id", "position_abbreviation", "role_probability"
    )
    summary_frame = pl.read_parquet(summary_path).select(
        "season", "player_id", "primary_position", "primary_role_share", "role_evidence_mode"
    )

    vectors: dict[tuple[int, int], np.ndarray] = {}
    for row in profile_frame.iter_rows(named=True):
        season = int(row["season"])
        player_id = int(row["player_id"])
        position = str(row["position_abbreviation"])
        if position not in BATTING_ROLE_POSITIONS:
            raise ValueError(f"unexpected batting role position {position!r}")
        key = (season, player_id)
        vector = vectors.setdefault(key, np.zeros(len(BATTING_ROLE_POSITIONS), dtype=float))
        index = BATTING_ROLE_POSITIONS.index(position)
        if vector[index] != 0.0:
            raise ValueError(f"duplicate player-season-position role row: {key} {position}")
        vector[index] = float(row["role_probability"])

    for key, vector in vectors.items():
        vectors[key] = validate_role_vector(vector)

    summaries: dict[tuple[int, int], dict[str, object]] = {}
    for row in summary_frame.iter_rows(named=True):
        key = (int(row["season"]), int(row["player_id"]))
        if key in summaries:
            raise ValueError(f"duplicate player-season summary row: {key}")
        primary = str(row["primary_position"])
        if primary not in BATTING_ROLE_POSITIONS:
            raise ValueError(f"unexpected player-season primary position {primary!r}")
        summaries[key] = {
            "primary_position": primary,
            "primary_role_share": float(row["primary_role_share"]),
            "role_evidence_mode": str(row["role_evidence_mode"]),
        }

    missing_summary = sorted(set(vectors) - set(summaries))
    missing_profile = sorted(set(summaries) - set(vectors))
    if missing_summary or missing_profile:
        raise ValueError(
            "role profile / player-season summary keys disagree: "
            f"missing_summary={missing_summary[:5]}, missing_profile={missing_profile[:5]}"
        )
    return vectors, summaries


def _paired_players(
    vectors: dict[tuple[int, int], np.ndarray],
    current_season: int,
    next_season: int,
) -> list[int]:
    current = {player_id for season, player_id in vectors if season == current_season}
    future = {player_id for season, player_id in vectors if season == next_season}
    return sorted(current & future)


def _fit_means(
    vectors: dict[tuple[int, int], np.ndarray],
    summaries: dict[tuple[int, int], dict[str, object]],
    training_pairs: tuple[tuple[int, int], ...],
) -> tuple[dict[str, np.ndarray], dict[str, int]]:
    samples: dict[str, list[np.ndarray]] = {position: [] for position in BATTING_ROLE_POSITIONS}
    for current_season, next_season in training_pairs:
        for player_id in _paired_players(vectors, current_season, next_season):
            current_key = (current_season, player_id)
            next_key = (next_season, player_id)
            position = str(summaries[current_key]["primary_position"])
            samples[position].append(vectors[next_key])
    return fit_primary_destination_means(samples)


def _score_fold(
    vectors: dict[tuple[int, int], np.ndarray],
    summaries: dict[tuple[int, int], dict[str, object]],
    *,
    current_season: int,
    next_season: int,
    training_pairs: tuple[tuple[int, int], ...],
) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    means, counts = _fit_means(vectors, summaries, training_pairs)
    players = _paired_players(vectors, current_season, next_season)
    if not players:
        raise ValueError(f"no paired players for {current_season}->{next_season}")

    prediction_rows: list[dict[str, object]] = []
    baseline_tv: list[float] = []
    candidate_tv: list[float] = []
    baseline_sse: list[float] = []
    candidate_sse: list[float] = []
    baseline_primary_correct = 0
    candidate_primary_correct = 0
    primary_shares: list[float] = []

    for player_id in players:
        current_key = (current_season, player_id)
        next_key = (next_season, player_id)
        current = vectors[current_key]
        observed = vectors[next_key]
        summary = summaries[current_key]
        current_primary = str(summary["primary_position"])
        share = float(summary["primary_role_share"])
        primary_shares.append(share)

        baseline = current
        candidate = transition_smoothed_prediction(
            current,
            primary_share=share,
            destination_mean=means[current_primary],
        )
        observed_primary = str(summaries[next_key]["primary_position"])
        baseline_primary = primary_position(baseline)
        candidate_primary = primary_position(candidate)

        b_tv = total_variation_distance(baseline, observed)
        c_tv = total_variation_distance(candidate, observed)
        b_sse = summed_squared_error(baseline, observed)
        c_sse = summed_squared_error(candidate, observed)
        baseline_tv.append(b_tv)
        candidate_tv.append(c_tv)
        baseline_sse.append(b_sse)
        candidate_sse.append(c_sse)
        baseline_primary_correct += int(baseline_primary == observed_primary)
        candidate_primary_correct += int(candidate_primary == observed_primary)

        row: dict[str, object] = {
            "current_season": current_season,
            "next_season": next_season,
            "player_id": player_id,
            "current_primary_position": current_primary,
            "current_primary_share": share,
            "observed_primary_position": observed_primary,
            "baseline_primary_position": baseline_primary,
            "candidate_primary_position": candidate_primary,
            "baseline_tv": b_tv,
            "candidate_tv": c_tv,
            "baseline_sse": b_sse,
            "candidate_sse": c_sse,
        }
        for index, position in enumerate(BATTING_ROLE_POSITIONS):
            row[f"current_{position}"] = float(current[index])
            row[f"observed_{position}"] = float(observed[index])
            row[f"candidate_{position}"] = float(candidate[index])
        prediction_rows.append(row)

    baseline_mean_tv = fmean(baseline_tv)
    candidate_mean_tv = fmean(candidate_tv)
    baseline_mean_sse = fmean(baseline_sse)
    candidate_mean_sse = fmean(candidate_sse)
    fold_pass = (
        candidate_mean_tv < baseline_mean_tv
        and candidate_mean_sse < baseline_mean_sse
    )

    fold = {
        "current_season": current_season,
        "next_season": next_season,
        "training_transitions": [list(pair) for pair in training_pairs],
        "scored_player_count": len(players),
        "mean_current_primary_share": fmean(primary_shares),
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
        "passed": fold_pass,
    }
    mean_rows = []
    for position in BATTING_ROLE_POSITIONS:
        row = {
            "evaluation_current_season": current_season,
            "evaluation_next_season": next_season,
            "current_primary_position": position,
            "training_transition_count": counts[position],
        }
        for index, destination in enumerate(BATTING_ROLE_POSITIONS):
            row[f"mean_next_{destination}"] = float(means[position][index])
        mean_rows.append(row)
    return fold, prediction_rows, mean_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/position-role-transition-challenger"),
    )
    args = parser.parse_args()

    vectors, summaries = _load_profiles(args.source_root)
    folds: list[dict[str, object]] = []
    all_predictions: list[dict[str, object]] = []
    all_means: list[dict[str, object]] = []
    for current_season, next_season, training_pairs in EVAL_FOLDS:
        fold, predictions, means = _score_fold(
            vectors,
            summaries,
            current_season=current_season,
            next_season=next_season,
            training_pairs=training_pairs,
        )
        folds.append(fold)
        all_predictions.extend(predictions)
        all_means.extend(means)

    candidate_passed = all(bool(fold["passed"]) for fold in folds)
    report = {
        "report_schema_version": "0.1",
        "gate": "position_role_transition_smoothing_development",
        "contract": "docs/position-role-transition-challenger-contract.md",
        "source": {
            "run_id": SOURCE_RUN_ID,
            "artifact_name": SOURCE_ARTIFACT,
            "artifact_digest": SOURCE_ARTIFACT_DIGEST,
            "seasons": [2021, 2022, 2023, 2024],
        },
        "positions": list(BATTING_ROLE_POSITIONS),
        "candidate": {
            "name": "primary_share_weighted_transition_mean_v1",
            "formula": "s * current_profile + (1 - s) * prior_history_mean_next_profile_by_current_primary_position",
            "hyperparameters": [],
        },
        "boundary": {
            "2025_position_source_accessed": False,
            "2025_position_outcomes_scored": False,
            "hyperparameter_search": False,
            "training_uses_only_prior_transitions": True,
            "playing_time_v1_modified": False,
            "batting_projection_v1_modified": False,
            "team_allocator_fit": False,
            "defense_model_fit": False,
        },
        "folds": folds,
        "decision": {
            "candidate_passed_development": candidate_passed,
            "2025_position_role_confirmation_authorized": candidate_passed,
            "team_allocator_authorized": False,
            "defense_model_authorized": False,
        },
    }

    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    pl.DataFrame(all_predictions).write_parquet(args.output_root / "predictions.parquet")
    pl.DataFrame(all_means).write_parquet(args.output_root / "transition_means.parquet")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
