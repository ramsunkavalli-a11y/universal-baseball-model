"""Training-response and prediction composition plumbing for Projection v1.

This module implements the pre-registered bridge between frozen Current Talent
B2 and the ridge age/development model. Future outcomes are translated back to
the same latent MLB scale using only the translation fitted at the pre-target
snapshot. No candidate selection or proper-score comparison occurs here.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import exp, log
from typing import Any

import polars as pl

from universal_baseball.current_talent_translation import DEFAULT_CLR_PSEUDOCOUNT
from universal_baseball.current_talent_validation_dataset import TARGET_ENVIRONMENT_KEY
from universal_baseball.performance_season import ALL_CORE_BINS
from universal_baseball.projection_composition import (
    PROJECTION_ILR_COORDINATE_COUNT,
    projection_ilr_to_profile,
    projection_profile_to_ilr,
)
from universal_baseball.projection_validation import ProjectionFold, require_development_fold


PROJECTION_DELTA_COLUMNS = tuple(
    f"delta_ilr_{index:02d}" for index in range(PROJECTION_ILR_COORDINATE_COUNT)
)
PREDICTED_PROJECTION_DELTA_COLUMNS = tuple(
    f"predicted_{column}" for column in PROJECTION_DELTA_COLUMNS
)
PROJECTION_TRAINING_RESPONSE_METHOD = "translated_future_profile_ilr_delta_v1"


@dataclass(frozen=True, slots=True)
class ProjectionTrainingResponse:
    responses: pl.DataFrame
    latent_target_profile: pl.DataFrame
    metrics: dict[str, Any]


def _require_columns(frame: pl.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing fields: {missing}")


def _translation_lookup(offsets: pl.DataFrame) -> dict[str, dict[str, float]]:
    _require_columns(
        offsets,
        {"level_group", "core_bin", "clr_environment_effect"},
        "Projection translation offsets",
    )
    if offsets.group_by(["level_group", "core_bin"]).len().filter(pl.col("len") != 1).height:
        raise ValueError("Projection translation offsets violate level_group + core_bin grain")
    lookup: dict[str, dict[str, float]] = defaultdict(dict)
    for row in offsets.select("level_group", "core_bin", "clr_environment_effect").iter_rows(named=True):
        lookup[str(row["level_group"])][str(row["core_bin"])] = float(
            row["clr_environment_effect"]
        )
    for level, values in lookup.items():
        if set(values) != set(ALL_CORE_BINS):
            raise ValueError(f"Projection translation level {level} lacks complete core bins")
        if abs(sum(values.values())) > 1e-7:
            raise ValueError(f"Projection translation CLR effects do not sum to zero for {level}")
    if "MLB" not in lookup:
        raise ValueError("Projection translation offsets require MLB anchor")
    return dict(lookup)


def _softmax(values: list[float]) -> list[float]:
    maximum = max(values)
    numerators = [exp(value - maximum) for value in values]
    denominator = sum(numerators)
    if denominator <= 0.0:
        raise ValueError("Projection target softmax denominator must be positive")
    return [value / denominator for value in numerators]


def _snapshot_profiles(snapshot_profile: pl.DataFrame) -> dict[int, dict[str, float]]:
    _require_columns(
        snapshot_profile,
        {"player_id", "core_bin", "baseline2_latent_probability"},
        "Projection B2 snapshot profile",
    )
    if snapshot_profile.group_by(["player_id", "core_bin"]).len().filter(pl.col("len") != 1).height:
        raise ValueError("Projection B2 snapshot profile violates player_id + core_bin grain")
    output: dict[int, dict[str, float]] = defaultdict(dict)
    for row in snapshot_profile.select(
        "player_id", "core_bin", "baseline2_latent_probability"
    ).iter_rows(named=True):
        output[int(row["player_id"])][str(row["core_bin"])] = float(
            row["baseline2_latent_probability"]
        )
    for player_id, values in output.items():
        if set(values) != set(ALL_CORE_BINS):
            raise ValueError(f"Projection B2 snapshot incomplete for player {player_id}")
        if any(value <= 0.0 for value in values.values()):
            raise ValueError("Projection B2 snapshot probabilities must be positive")
    return dict(output)


def build_projection_training_response(
    snapshot_profile: pl.DataFrame,
    target_summary: pl.DataFrame,
    target_profile: pl.DataFrame,
    translation_offsets: pl.DataFrame,
    *,
    fold: ProjectionFold,
    pseudocount: float = DEFAULT_CLR_PSEUDOCOUNT,
) -> ProjectionTrainingResponse:
    """Build one player-level latent future-profile ILR delta response surface."""

    require_development_fold(fold)
    if pseudocount <= 0.0:
        raise ValueError("Projection target pseudocount must be positive")
    _require_columns(
        target_summary,
        {*TARGET_ENVIRONMENT_KEY, "future_core_events"},
        "Projection target summary",
    )
    _require_columns(
        target_profile,
        {*TARGET_ENVIRONMENT_KEY, "core_bin", "future_occurrence_count"},
        "Projection target profile",
    )
    if target_summary.group_by(list(TARGET_ENVIRONMENT_KEY)).len().filter(pl.col("len") != 1).height:
        raise ValueError("Projection target summary violates target-environment grain")
    if target_profile.group_by([*TARGET_ENVIRONMENT_KEY, "core_bin"]).len().filter(pl.col("len") != 1).height:
        raise ValueError("Projection target profile violates target-environment + core-bin grain")

    snapshot = _snapshot_profiles(snapshot_profile)
    translation = _translation_lookup(translation_offsets)
    target_counts = {
        tuple(row[key] for key in TARGET_ENVIRONMENT_KEY): {
            str(bin_row["core_bin"]): int(bin_row["future_occurrence_count"])
            for bin_row in target_profile.filter(
                pl.all_horizontal(
                    [pl.col(key) == row[key] for key in TARGET_ENVIRONMENT_KEY]
                )
            ).iter_rows(named=True)
        }
        for row in target_summary.iter_rows(named=True)
        if int(row["future_core_events"]) > 0
    }

    pooled_counts: dict[int, dict[str, float]] = defaultdict(
        lambda: {core_bin: 0.0 for core_bin in ALL_CORE_BINS}
    )
    pooled_weights: dict[int, int] = defaultdict(int)
    environment_counts: dict[int, int] = defaultdict(int)
    target_players: set[int] = set()

    for target in target_summary.filter(pl.col("future_core_events") > 0).iter_rows(named=True):
        player_id = int(target["player_id"])
        target_players.add(player_id)
        if player_id not in snapshot:
            continue
        level = str(target["target_level_group"])
        if level not in translation:
            raise ValueError(f"no pre-snapshot translation offset for future level {level}")
        n = int(target["future_core_events"])
        key = tuple(target[column] for column in TARGET_ENVIRONMENT_KEY)
        counts_by_bin = target_counts.get(key, {})
        counts = [int(counts_by_bin.get(core_bin, 0)) for core_bin in ALL_CORE_BINS]
        if sum(counts) != n:
            raise ValueError("Projection future occurrence counts do not reconcile to future_core_events")

        denominator = float(n) + pseudocount * len(ALL_CORE_BINS)
        observed_probabilities = [
            (float(count) + pseudocount) / denominator for count in counts
        ]
        logs = [log(value) for value in observed_probabilities]
        mean_log = sum(logs) / len(logs)
        observed_clr = [value - mean_log for value in logs]
        latent_clr = [
            observed_clr[index] - translation[level][core_bin]
            for index, core_bin in enumerate(ALL_CORE_BINS)
        ]
        latent_probability = _softmax(latent_clr)
        for core_bin, probability in zip(ALL_CORE_BINS, latent_probability, strict=True):
            pooled_counts[player_id][core_bin] += probability * float(n)
        pooled_weights[player_id] += n
        environment_counts[player_id] += 1

    latent_rows: list[dict[str, object]] = []
    response_rows: list[dict[str, object]] = []
    for player_id in sorted(pooled_weights):
        total = pooled_weights[player_id]
        if total <= 0:
            continue
        latent_profile = {
            core_bin: pooled_counts[player_id][core_bin] / float(total)
            for core_bin in ALL_CORE_BINS
        }
        if abs(sum(latent_profile.values()) - 1.0) > 1e-9:
            raise ValueError("Projection pooled latent target profile does not sum to one")
        target_ilr = projection_profile_to_ilr(latent_profile)
        snapshot_ilr = projection_profile_to_ilr(snapshot[player_id])
        delta = [target - current for target, current in zip(target_ilr, snapshot_ilr, strict=True)]
        row: dict[str, object] = {
            "player_id": player_id,
            "projection_fold": fold.label,
            "as_of_date": fold.snapshot_date,
            "future_core_events": int(total),
            "future_target_environment_count": int(environment_counts[player_id]),
            "response_method": PROJECTION_TRAINING_RESPONSE_METHOD,
        }
        row.update({column: value for column, value in zip(PROJECTION_DELTA_COLUMNS, delta, strict=True)})
        response_rows.append(row)
        for core_bin in ALL_CORE_BINS:
            latent_rows.append(
                {
                    "player_id": player_id,
                    "projection_fold": fold.label,
                    "as_of_date": fold.snapshot_date,
                    "core_bin": core_bin,
                    "latent_target_probability": latent_profile[core_bin],
                    "future_core_events": int(total),
                }
            )

    responses = pl.DataFrame(response_rows).sort("player_id") if response_rows else pl.DataFrame()
    latent_target = (
        pl.DataFrame(latent_rows).sort(["player_id", "core_bin"])
        if latent_rows
        else pl.DataFrame()
    )
    snapshot_players = set(snapshot)
    scored_players = set(pooled_weights)
    metrics: dict[str, Any] = {
        "response_method": PROJECTION_TRAINING_RESPONSE_METHOD,
        "fold": fold.label,
        "as_of_date": fold.snapshot_date.isoformat(),
        "snapshot_player_count": len(snapshot_players),
        "future_core_target_player_count": len(target_players),
        "response_player_count": len(scored_players),
        "snapshot_without_future_core_target_count": len(snapshot_players - target_players),
        "future_core_target_without_snapshot_count": len(target_players - snapshot_players),
        "future_core_events_in_responses": int(sum(pooled_weights.values())),
        "pseudocount": float(pseudocount),
        "future_level_used_as_predictor": False,
        "future_level_used_only_for_target_translation": True,
        "zero_future_opportunity_imputed": False,
        "candidate_fit": False,
        "candidate_selected": False,
        "2025_accessed": False,
    }
    return ProjectionTrainingResponse(
        responses=responses,
        latent_target_profile=latent_target,
        metrics=metrics,
    )


def apply_projection_ilr_delta(
    snapshot_profile: pl.DataFrame,
    predicted_delta: pl.DataFrame,
) -> pl.DataFrame:
    """Add predicted ILR deltas to frozen B2 and return candidate latent profiles."""

    snapshot = _snapshot_profiles(snapshot_profile)
    _require_columns(
        predicted_delta,
        {"player_id", *PREDICTED_PROJECTION_DELTA_COLUMNS},
        "Projection predicted delta",
    )
    if predicted_delta.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("Projection predicted delta violates player_id grain")

    rows: list[dict[str, object]] = []
    for row in predicted_delta.iter_rows(named=True):
        player_id = int(row["player_id"])
        if player_id not in snapshot:
            raise ValueError(f"Projection prediction lacks frozen B2 snapshot for player {player_id}")
        base = projection_profile_to_ilr(snapshot[player_id])
        delta = [float(row[column]) for column in PREDICTED_PROJECTION_DELTA_COLUMNS]
        profile = projection_ilr_to_profile(
            [current + adjustment for current, adjustment in zip(base, delta, strict=True)]
        )
        for core_bin in ALL_CORE_BINS:
            rows.append(
                {
                    "player_id": player_id,
                    "core_bin": core_bin,
                    "projection_probability": profile[core_bin],
                }
            )
    return pl.DataFrame(rows).sort(["player_id", "core_bin"])


def build_projection_scoring_pair(
    snapshot_profile: pl.DataFrame,
    candidate_profile: pl.DataFrame,
) -> pl.DataFrame:
    """Pair carry-forward B2 and one candidate for the existing proper-score engine."""

    _require_columns(
        candidate_profile,
        {"player_id", "core_bin", "projection_probability"},
        "Projection candidate profile",
    )
    baseline = snapshot_profile.select(
        "player_id",
        "core_bin",
        pl.col("baseline2_latent_probability").alias("baseline0_latent_probability"),
    )
    candidate = candidate_profile.select(
        "player_id",
        "core_bin",
        pl.col("projection_probability").alias("baseline1_latent_probability"),
    )
    paired = baseline.join(candidate, on=["player_id", "core_bin"], how="inner")
    candidate_players = set(int(value) for value in candidate.get_column("player_id").unique().to_list())
    paired_players = set(int(value) for value in paired.get_column("player_id").unique().to_list())
    if candidate_players != paired_players or paired.height != candidate.height:
        raise ValueError("Projection carry-forward/candidate scoring coverage differs")
    return paired.sort(["player_id", "core_bin"])
