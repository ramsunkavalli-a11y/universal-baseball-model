"""Empirical workload-only uncertainty for nested pre-MLB career paths."""

from __future__ import annotations

from typing import Any

import numpy as np
import polars as pl


UNCERTAINTY_MODEL_ID = "nested_empirical_workload_only_v1"


def _weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    order = np.argsort(values, kind="stable")
    ordered_values = values[order]
    cumulative = np.cumsum(weights[order])
    return float(ordered_values[np.searchsorted(cumulative, q, side="left")])


def _samples(
    paths: pl.DataFrame,
    *,
    player_type: str,
    tier: str,
    role: str,
    minimum_role_players: int,
) -> tuple[np.ndarray, str]:
    pooled = paths.filter(
        (pl.col("player_type") == player_type)
        & (pl.col("outcome_tier_v2") == tier)
    )
    cell = pooled.filter(pl.col("career_role") == role)
    selected = cell if cell.height >= minimum_role_players else pooled
    if selected.is_empty():
        raise ValueError(f"missing workload samples: {player_type}/{tier}/{role}")
    return selected.get_column("adjusted_total_workload").to_numpy(), (
        "role" if selected is cell else "pooled"
    )


def build_nested_workload_uncertainty(
    nested: pl.DataFrame,
    workload_paths: pl.DataFrame,
    *,
    minimum_role_players: int = 30,
    star_war_threshold: float = 18.0,
) -> pl.DataFrame:
    """Return exact weighted workload quantiles while holding WAR rate fixed."""

    required = {
        "player_id", "model_player_type", "primary_position",
        "ordered_arrival_probability", "fringe_probability",
        "meaningful_only_probability", "established_probability",
        "starter_probability", "reliever_probability",
        "hitter_six_control_year_war_if_arrived",
        "pitcher_six_control_year_war_if_arrived",
        "three_tier_expected_six_year_war",
    }
    if missing := sorted(required - set(nested.columns)):
        raise ValueError(f"nested values missing fields: {missing}")
    if minimum_role_players < 1:
        raise ValueError("minimum_role_players must be positive")
    rows: list[dict[str, Any]] = []
    applicable = nested.filter(pl.col("ordered_arrival_probability").is_not_null())
    for row in applicable.iter_rows(named=True):
        player_type = str(row["model_player_type"])
        tier_probabilities = {
            "fringe": float(row["fringe_probability"]),
            "meaningful_only": float(row["meaningful_only_probability"]),
            "established": float(row["established_probability"]),
        }
        if player_type == "hitter":
            roles = {"hitter": 1.0}
            assumed_workload = 6.0 * (
                450.0 if str(row["primary_position"] or "") == "C" else 550.0
            )
            full_war = float(row["hitter_six_control_year_war_if_arrived"] or 0.0)
        else:
            starter = min(1.0, max(0.0, float(row["starter_probability"] or 0.0)))
            reliever = min(1.0, max(0.0, float(row["reliever_probability"] or 0.0)))
            swingman = max(0.0, 1.0 - starter - reliever)
            total = starter + reliever + swingman
            roles = {
                "starter": starter / total,
                "swingman": swingman / total,
                "reliever": reliever / total,
            }
            assumed_workload = 6.0 * (
                800.0 * roles["starter"]
                + 450.0 * roles["swingman"]
                + 250.0 * roles["reliever"]
            )
            full_war = float(row["pitcher_six_control_year_war_if_arrived"] or 0.0)
        rate = full_war / assumed_workload if assumed_workload > 0 else 0.0
        values = [0.0]
        weights = [max(0.0, 1.0 - float(row["ordered_arrival_probability"]))]
        sources: set[str] = set()
        for tier, tier_probability in tier_probabilities.items():
            for role, role_probability in roles.items():
                probability = tier_probability * role_probability
                if probability <= 0:
                    continue
                samples, source = _samples(
                    workload_paths,
                    player_type=player_type,
                    tier=tier,
                    role=role,
                    minimum_role_players=minimum_role_players,
                )
                values.extend((samples * rate).tolist())
                weights.extend([probability / len(samples)] * len(samples))
                sources.add(f"{tier}_{role}_{source}")
        value_array = np.asarray(values, dtype=float)
        weight_array = np.asarray(weights, dtype=float)
        weight_array /= weight_array.sum()
        mean = float(np.sum(value_array * weight_array))
        point = float(row["three_tier_expected_six_year_war"])
        if abs(mean - point) > 1e-8:
            raise ValueError(
                f"workload distribution mean differs from point for {row['player_id']}: "
                f"{mean} vs {point}"
            )
        rows.append(
            {
                "player_id": int(row["player_id"]),
                "workload_war_mean": mean,
                "workload_war_p10": _weighted_quantile(value_array, weight_array, 0.10),
                "workload_war_p50": _weighted_quantile(value_array, weight_array, 0.50),
                "workload_war_p90": _weighted_quantile(value_array, weight_array, 0.90),
                "workload_only_star_probability": float(
                    weight_array[value_array >= star_war_threshold].sum()
                ),
                "conditional_war_per_workload": rate,
                "sample_source": ":".join(sorted(sources)),
                "uncertainty_model_id": UNCERTAINTY_MODEL_ID,
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None).sort("player_id")
