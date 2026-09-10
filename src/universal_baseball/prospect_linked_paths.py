"""Whole-tail resampling for annually linked prospect career research."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl

from universal_baseball.prospect_mlb_progression import (
    SIMULATED_STATE_CODES,
    predict_progression_from_coefficients,
)


@dataclass(frozen=True, slots=True)
class LinkedPathDraws:
    adjusted_workload: np.ndarray
    raw_workload: np.ndarray
    states: np.ndarray
    donor_player_ids: np.ndarray
    tail_resamples: int


def simulate_linked_tail_blocks(
    rng: np.random.Generator,
    donor_paths: pl.DataFrame,
    coefficients: pl.DataFrame,
    active_mean_raw_workload: np.ndarray,
    *,
    player_type: str,
    initial_age_years: float,
    direct_established_probability: float,
    draws: int,
) -> LinkedPathDraws:
    """Sample whole paths, replacing only incompatible remaining tail blocks."""

    required = {
        "path_player_id", "player_type", "path_year", "adjusted_workload",
        "raw_workload", "observed_career_state",
    }
    if missing := sorted(required - set(donor_paths.columns)):
        raise ValueError(f"linked donor paths missing fields: {missing}")
    if draws < 1:
        raise ValueError("linked path draws must be positive")
    source = donor_paths.filter(pl.col("player_type") == player_type).sort(
        "path_player_id", "path_year"
    )
    if source.is_empty():
        raise ValueError(f"linked donor pool is empty for {player_type}")
    lengths = source.group_by("path_player_id").agg(
        pl.len().alias("rows"), pl.col("path_year").n_unique().alias("years")
    )
    seasons = int(lengths["years"].max())
    if lengths.filter(
        (pl.col("rows") != seasons) | (pl.col("years") != seasons)
    ).height:
        raise ValueError("linked donor paths must be complete and aligned")
    environment = np.asarray(active_mean_raw_workload, dtype=float)
    if environment.shape != (seasons,) or np.any(
        ~np.isfinite(environment) | (environment <= 0.0)
    ):
        raise ValueError("linked path environment is invalid")

    groups = source.partition_by("path_player_id", maintain_order=True)
    player_ids = np.asarray(
        [int(group.item(0, "path_player_id")) for group in groups], dtype=np.int64
    )
    adjusted_library = np.stack(
        [group["adjusted_workload"].to_numpy().astype(float) for group in groups]
    )
    raw_library = np.stack(
        [group["raw_workload"].to_numpy().astype(float) for group in groups]
    )
    state_library = np.stack(
        [
            np.asarray(
                [SIMULATED_STATE_CODES[str(value)] for value in group["observed_career_state"]],
                dtype=np.int8,
            )
            for group in groups
        ]
    )
    if np.any(~np.isfinite(adjusted_library)) or np.any(adjusted_library < 0.0):
        raise ValueError("linked donor workloads are invalid")

    chosen = rng.integers(0, len(groups), size=draws)
    donor_indices = np.repeat(chosen[:, None], seasons, axis=1)
    adjusted = adjusted_library[chosen].copy()
    raw = raw_library[chosen].copy()
    states = np.zeros((draws, seasons), dtype=np.int8)
    states[:, 0] = state_library[chosen, 0]
    tail_resamples = 0
    for year_index in range(1, seasons):
        starting = states[:, year_index - 1]
        desired = starting.copy()
        scoring = pl.DataFrame(
            {
                "transition_age_years": np.full(
                    draws, initial_age_years + year_index
                ),
                "elapsed_year": np.full(draws, year_index + 1),
                "prior_mlb_active": (raw[:, year_index - 1] > 0.0).astype(np.int8),
                "prior_workload_vs_active_mean": (
                    raw[:, year_index - 1] / environment[year_index - 1]
                ),
            }
        )
        fringe = starting == SIMULATED_STATE_CODES["FRINGE_MLB"]
        if np.any(fringe):
            probability = predict_progression_from_coefficients(
                scoring.filter(pl.Series(fringe)),
                coefficients,
                player_type=player_type,
                origin_state="FRINGE_MLB",
            )
            advanced = np.flatnonzero(fringe)[rng.random(fringe.sum()) < probability]
            direct = rng.random(advanced.size) < direct_established_probability
            desired[advanced] = np.where(
                direct,
                SIMULATED_STATE_CODES["ESTABLISHED_MLB"],
                SIMULATED_STATE_CODES["MEANINGFUL_MLB"],
            )
        meaningful = starting == SIMULATED_STATE_CODES["MEANINGFUL_MLB"]
        if np.any(meaningful):
            probability = predict_progression_from_coefficients(
                scoring.filter(pl.Series(meaningful)),
                coefficients,
                player_type=player_type,
                origin_state="MEANINGFUL_MLB",
            )
            advanced = np.flatnonzero(meaningful)[
                rng.random(meaningful.sum()) < probability
            ]
            desired[advanced] = SIMULATED_STATE_CODES["ESTABLISHED_MLB"]
        no_mlb = starting == SIMULATED_STATE_CODES["NO_MLB"]
        current_donor_state = state_library[donor_indices[:, year_index], year_index]
        desired[no_mlb] = current_donor_state[no_mlb]

        mismatch = current_donor_state != desired
        for state_code in SIMULATED_STATE_CODES.values():
            targets = np.flatnonzero(mismatch & (desired == state_code))
            if not targets.size:
                continue
            candidates = np.flatnonzero(state_library[:, year_index] == state_code)
            if not candidates.size:
                raise ValueError(
                    f"no donor tail for state {state_code} in year {year_index + 1}"
                )
            replacements = rng.choice(candidates, size=targets.size)
            for target, replacement in zip(targets, replacements, strict=True):
                donor_indices[target, year_index:] = replacement
                adjusted[target, year_index:] = adjusted_library[replacement, year_index:]
                raw[target, year_index:] = raw_library[replacement, year_index:]
            tail_resamples += targets.size
        states[:, year_index] = desired
    if np.any(np.diff(states, axis=1) < 0):
        raise RuntimeError("linked state path moved backward")
    return LinkedPathDraws(
        adjusted_workload=adjusted,
        raw_workload=raw,
        states=states,
        donor_player_ids=player_ids[donor_indices],
        tail_resamples=tail_resamples,
    )
