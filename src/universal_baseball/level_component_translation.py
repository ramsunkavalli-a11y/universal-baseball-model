"""Matched-player level translation for simple affiliated component profiles."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from itertools import combinations
import math
from typing import Sequence

import numpy as np
import polars as pl


LEVEL_ORDER = {
    "ROOKIE_COMPLEX": 0,
    "SINGLE_A": 1,
    "HIGH_A": 2,
    "AA": 3,
    "AAA": 4,
    "MLB": 5,
}
TRANSLATION_METHOD = "same_player_same_season_clr_graph_v1"
DEFAULT_LEVEL_EVIDENCE_MULTIPLIER = {
    "MLB": 1.0,
    "AAA": 0.50,
    "AA": 0.30,
    "HIGH_A": 0.20,
    "SINGLE_A": 0.10,
    "ROOKIE_COMPLEX": 0.05,
}


@dataclass(frozen=True, slots=True)
class ComponentTranslationFit:
    offsets: pl.DataFrame
    metrics: dict[str, object]


def _clr(counts: Sequence[float], pseudocount: float) -> np.ndarray:
    values = np.asarray(counts, dtype=float) + pseudocount
    probabilities = values / values.sum()
    logged = np.log(probabilities)
    return logged - logged.mean()


def _connected_levels(pairs: list[dict[str, object]], anchor: str) -> set[str]:
    graph: dict[str, set[str]] = defaultdict(set)
    for pair in pairs:
        left = str(pair["from_level_group"])
        right = str(pair["to_level_group"])
        graph[left].add(right)
        graph[right].add(left)
    reached = {anchor}
    queue = deque([anchor])
    while queue:
        level = queue.popleft()
        for neighbor in graph[level]:
            if neighbor not in reached:
                reached.add(neighbor)
                queue.append(neighbor)
    return reached


def fit_same_season_component_translation(
    frame: pl.DataFrame,
    *,
    exposure_column: str,
    component_columns: tuple[str, ...],
    completed_seasons: tuple[int, ...],
    minimum_level_exposure: int = 30,
    pseudocount: float = 0.5,
    anchor_level: str = "MLB",
) -> ComponentTranslationFit:
    """Fit level CLR effects from players observed at multiple levels in one year."""

    required = {"season", "player_id", "level_group", exposure_column, *component_columns}
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"translation source missing columns: {missing}")
    if not component_columns or minimum_level_exposure <= 0 or pseudocount <= 0:
        raise ValueError("translation components, exposure threshold, and pseudocount must be positive")
    if anchor_level not in LEVEL_ORDER:
        raise ValueError("unsupported translation anchor")
    source = frame.filter(pl.col("season").is_in(completed_seasons)).group_by(
        "season", "player_id", "level_group"
    ).agg(
        pl.col(exposure_column).sum().alias(exposure_column),
        *(pl.col(column).sum().alias(column) for column in component_columns),
    ).filter(pl.col(exposure_column) >= minimum_level_exposure)
    if source.filter(~pl.col("level_group").is_in(list(LEVEL_ORDER))).height:
        raise ValueError("translation source contains unsupported levels")
    if source.filter(
        pl.any_horizontal(*(pl.col(column) < 0 for column in component_columns))
        | ((pl.sum_horizontal(*component_columns) - pl.col(exposure_column)).abs() > 1e-8)
    ).height:
        raise ValueError("translation components must be nonnegative and sum to exposure")

    pairs: list[dict[str, object]] = []
    deltas: list[np.ndarray] = []
    for group in source.partition_by(["season", "player_id"], maintain_order=False):
        rows = sorted(group.iter_rows(named=True), key=lambda row: LEVEL_ORDER[str(row["level_group"])])
        for left, right in combinations(rows, 2):
            left_level = str(left["level_group"])
            right_level = str(right["level_group"])
            left_exposure = float(left[exposure_column])
            right_exposure = float(right[exposure_column])
            precision = 2.0 / (1.0 / left_exposure + 1.0 / right_exposure)
            pairs.append(
                {
                    "season": int(left["season"]),
                    "player_id": int(left["player_id"]),
                    "from_level_group": left_level,
                    "to_level_group": right_level,
                    "precision_weight": precision,
                }
            )
            deltas.append(
                _clr([float(right[column]) for column in component_columns], pseudocount)
                - _clr([float(left[column]) for column in component_columns], pseudocount)
            )
    if not pairs:
        raise ValueError("translation source has no eligible same-season level pairs")
    connected = _connected_levels(pairs, anchor_level)
    observed = set(source.get_column("level_group").to_list())
    disconnected = sorted(observed - connected, key=LEVEL_ORDER.__getitem__)
    if disconnected:
        raise ValueError(f"translation levels are disconnected from MLB: {disconnected}")

    unknown = sorted(connected - {anchor_level}, key=LEVEL_ORDER.__getitem__)
    index = {level: offset for offset, level in enumerate(unknown)}
    design = np.zeros((len(pairs), len(unknown)), dtype=float)
    weights = np.asarray([float(pair["precision_weight"]) for pair in pairs])
    for row_index, pair in enumerate(pairs):
        left = str(pair["from_level_group"])
        right = str(pair["to_level_group"])
        if left != anchor_level:
            design[row_index, index[left]] -= 1.0
        if right != anchor_level:
            design[row_index, index[right]] += 1.0
    root_weight = np.sqrt(weights)
    weighted_design = design * root_weight[:, None]
    delta_matrix = np.vstack(deltas)
    effects: dict[str, np.ndarray] = {anchor_level: np.zeros(len(component_columns))}
    residual_rmse: dict[str, float] = {}
    for component_index, component in enumerate(component_columns):
        target = delta_matrix[:, component_index] * root_weight
        solution = np.linalg.lstsq(weighted_design, target, rcond=None)[0]
        for level, level_index in index.items():
            effects.setdefault(level, np.zeros(len(component_columns)))[component_index] = solution[level_index]
        residual = delta_matrix[:, component_index] - design @ solution
        residual_rmse[component] = math.sqrt(float(np.average(residual**2, weights=weights)))
    for level in effects:
        effects[level] = effects[level] - effects[level].mean()
    rows = [
        {
            "level_group": level,
            "component": component,
            "clr_environment_effect": float(effects[level][component_index]),
            "translation_method": TRANSLATION_METHOD,
        }
        for level in sorted(effects, key=LEVEL_ORDER.__getitem__)
        for component_index, component in enumerate(component_columns)
    ]
    return ComponentTranslationFit(
        offsets=pl.DataFrame(rows).sort(["level_group", "component"]),
        metrics={
            "eligible_pairs": len(pairs),
            "distinct_players": len({int(pair["player_id"]) for pair in pairs}),
            "completed_seasons": list(completed_seasons),
            "minimum_level_exposure": minimum_level_exposure,
            "pseudocount": pseudocount,
            "connected_levels": sorted(connected, key=LEVEL_ORDER.__getitem__),
            "residual_clr_rmse": residual_rmse,
            "pair_weighting": "harmonic_mean_exposure",
            "same_player_same_season_only": True,
        },
    )


def translate_component_probabilities_to_mlb(
    probabilities: dict[str, float],
    *,
    level_group: str,
    offsets: pl.DataFrame,
) -> dict[str, float]:
    """Remove fitted level environment effects and return a coherent MLB profile."""

    components = tuple(sorted(probabilities))
    values = np.asarray([float(probabilities[component]) for component in components])
    if np.any(~np.isfinite(values)) or np.any(values <= 0) or not math.isclose(float(values.sum()), 1.0, abs_tol=1e-9):
        raise ValueError("translation probabilities must be positive and sum to one")
    relevant = offsets.filter(pl.col("level_group") == level_group)
    lookup = {
        str(row["component"]): float(row["clr_environment_effect"])
        for row in relevant.iter_rows(named=True)
    }
    if set(lookup) != set(components):
        raise ValueError(f"missing translation offsets for {level_group}")
    clr = np.log(values) - np.log(values).mean()
    latent = clr - np.asarray([lookup[component] for component in components])
    exponentials = np.exp(latent - latent.max())
    translated = exponentials / exponentials.sum()
    return {component: float(translated[index]) for index, component in enumerate(components)}


def translate_component_probabilities_from_mlb(
    probabilities: dict[str, float],
    *,
    level_group: str,
    offsets: pl.DataFrame,
) -> dict[str, float]:
    """Apply a fitted level environment to an MLB-scale component profile."""

    components = tuple(sorted(probabilities))
    values = np.asarray([float(probabilities[component]) for component in components])
    if np.any(~np.isfinite(values)) or np.any(values <= 0) or not math.isclose(
        float(values.sum()), 1.0, abs_tol=1e-9
    ):
        raise ValueError("translation probabilities must be positive and sum to one")
    relevant = offsets.filter(pl.col("level_group") == level_group)
    lookup = {
        str(row["component"]): float(row["clr_environment_effect"])
        for row in relevant.iter_rows(named=True)
    }
    if set(lookup) != set(components):
        raise ValueError(f"missing translation offsets for {level_group}")
    clr = np.log(values) - np.log(values).mean()
    observed = clr + np.asarray([lookup[component] for component in components])
    exponentials = np.exp(observed - observed.max())
    translated = exponentials / exponentials.sum()
    return {
        component: float(translated[index])
        for index, component in enumerate(components)
    }


def build_translated_affiliated_profiles(
    players: pl.DataFrame,
    history: pl.DataFrame,
    offsets: pl.DataFrame,
    *,
    exposure_column: str,
    component_columns: tuple[str, ...],
    current_season: int,
    reference_season: int,
    regression_exposure: float | dict[str, float],
    pseudocount: float = 0.5,
    level_evidence_multiplier: dict[str, float] | None = None,
) -> pl.DataFrame:
    """Build recency-weighted, regressed MLB-scale profiles for all players."""

    if set(players.columns) != {"player_id"}:
        raise ValueError("translated profile denominator must contain only player_id")
    component_specific_regression = isinstance(regression_exposure, dict)
    if component_specific_regression:
        if set(regression_exposure) != set(component_columns):
            raise ValueError("component regression exposure must cover every component")
        regression_by_component = {
            component: float(regression_exposure[component])
            for component in component_columns
        }
    else:
        regression_by_component = {
            component: float(regression_exposure) for component in component_columns
        }
    if (
        any(not math.isfinite(value) or value <= 0 for value in regression_by_component.values())
        or pseudocount <= 0
    ):
        raise ValueError("regression exposure and pseudocount must be positive")
    multipliers = level_evidence_multiplier or DEFAULT_LEVEL_EVIDENCE_MULTIPLIER
    if set(multipliers) != set(LEVEL_ORDER) or any(
        not math.isfinite(float(value)) or not 0 < float(value) <= 1
        for value in multipliers.values()
    ):
        raise ValueError("level evidence multipliers must cover every level in (0, 1]")
    required = {"season", "player_id", "level_group", exposure_column, *component_columns}
    if missing := sorted(required - set(history.columns)):
        raise ValueError(f"translated profile history missing columns: {missing}")
    source = history.filter(
        pl.col("season").is_between(current_season - 2, current_season)
    ).group_by("season", "player_id", "level_group").agg(
        pl.col(exposure_column).sum().alias(exposure_column),
        *(pl.col(column).sum().alias(column) for column in component_columns),
    ).filter(pl.col(exposure_column) > 0)
    if source.filter(
        ((pl.sum_horizontal(*component_columns) - pl.col(exposure_column)).abs() > 1e-8)
        | pl.any_horizontal(*(pl.col(column) < 0 for column in component_columns))
    ).height:
        raise ValueError("translated profile components do not reconcile to exposure")
    reference = source.filter(
        (pl.col("season") == reference_season) & (pl.col("level_group") == "MLB")
    )
    reference_total = float(reference.get_column(exposure_column).sum())
    if reference_total <= 0:
        raise ValueError("translated profile requires positive MLB reference exposure")
    prior = {
        component: float(reference.get_column(component).sum()) / reference_total
        for component in component_columns
    }
    translated_rows: list[dict[str, object]] = []
    for row in source.iter_rows(named=True):
        exposure = float(row[exposure_column])
        probabilities = {
            component: (float(row[component]) + pseudocount)
            / (exposure + pseudocount * len(component_columns))
            for component in component_columns
        }
        translated = translate_component_probabilities_to_mlb(
            probabilities, level_group=str(row["level_group"]), offsets=offsets
        )
        recency_weight = {0: 3.0, 1: 2.0, 2: 1.0}[
            current_season - int(row["season"])
        ]
        weight = recency_weight * float(multipliers[str(row["level_group"])])
        translated_rows.append(
            {
                "player_id": int(row["player_id"]),
                "weighted_exposure": exposure * weight,
                **{
                    f"weighted_{component}": translated[component] * exposure * weight
                    for component in component_columns
                },
            }
        )
    translated_frame = pl.DataFrame(translated_rows)
    weighted = translated_frame.group_by("player_id").agg(
        pl.col("weighted_exposure").sum(),
        *(pl.col(f"weighted_{component}").sum() for component in component_columns),
    )
    joined = players.join(weighted, on="player_id", how="left")
    output = []
    for row in joined.iter_rows(named=True):
        evidence = float(row.get("weighted_exposure") or 0.0)
        raw_probabilities = {
            component: (
                float(row.get(f"weighted_{component}") or 0.0)
                + regression_by_component[component] * prior[component]
            )
            / (evidence + regression_by_component[component])
            for component in component_columns
        }
        probability_total = sum(raw_probabilities.values())
        probabilities = {
            component: raw_probabilities[component] / probability_total
            for component in component_columns
        }
        effective_regression = sum(
            prior[component] * regression_by_component[component]
            for component in component_columns
        )
        result = {
            "player_id": int(row["player_id"]),
            "weighted_affiliated_exposure": evidence,
            "affiliated_reliability": evidence / (evidence + effective_regression),
            **{f"p_{component}": probabilities[component] for component in component_columns},
        }
        if component_specific_regression:
            result.update({
                f"affiliated_reliability_{component}": evidence
                / (evidence + regression_by_component[component])
                for component in component_columns
            })
        output.append(result)
    return pl.DataFrame(output).sort("player_id")


def score_component_profiles(
    predictions: pl.DataFrame,
    targets: pl.DataFrame,
    *,
    exposure_column: str,
    component_columns: tuple[str, ...],
) -> dict[str, object]:
    """Score future component distributions on positive target exposure."""

    prediction_required = {"player_id", *(f"p_{value}" for value in component_columns)}
    target_required = {"player_id", exposure_column, *component_columns}
    if missing := sorted(prediction_required - set(predictions.columns)):
        raise ValueError(f"component predictions missing fields: {missing}")
    if missing := sorted(target_required - set(targets.columns)):
        raise ValueError(f"component targets missing fields: {missing}")
    if predictions.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("component predictions violate player grain")
    target = targets.group_by("player_id").agg(
        pl.col(exposure_column).sum().alias(exposure_column),
        *(pl.col(column).sum().alias(column) for column in component_columns),
    ).filter(pl.col(exposure_column) > 0)
    if target.filter(
        ((pl.sum_horizontal(*component_columns) - pl.col(exposure_column)).abs() > 1e-8)
        | pl.any_horizontal(*(pl.col(column) < 0 for column in component_columns))
    ).height:
        raise ValueError("component targets do not reconcile to exposure")
    joined = target.join(
        predictions.select(*prediction_required), on="player_id", how="inner", validate="1:1"
    )
    if joined.is_empty():
        raise ValueError("component predictions and targets do not overlap")
    total_exposure = float(joined.get_column(exposure_column).sum())
    negative_log_likelihood = 0.0
    brier_total = 0.0
    calibration: dict[str, dict[str, float]] = {}
    for component in component_columns:
        probability_column = f"p_{component}"
        if joined.filter(
            ~pl.col(probability_column).is_finite()
            | (pl.col(probability_column) <= 0)
            | (pl.col(probability_column) >= 1)
        ).height:
            raise ValueError("component predictions contain invalid probability")
        observed = float(joined.get_column(component).sum())
        predicted = float(
            joined.select(
                (pl.col(probability_column) * pl.col(exposure_column)).sum()
            ).item()
        )
        calibration[component] = {
            "observed_rate": observed / total_exposure,
            "predicted_rate": predicted / total_exposure,
            "rate_bias": (predicted - observed) / total_exposure,
        }
        negative_log_likelihood -= float(
            joined.select(
                (pl.col(component) * pl.col(probability_column).log()).sum()
            ).item()
        )
    probability_square = pl.sum_horizontal(
        *(pl.col(f"p_{component}") ** 2 for component in component_columns)
    )
    observed_probability = pl.sum_horizontal(
        *(
            pl.col(component) * pl.col(f"p_{component}")
            for component in component_columns
        )
    )
    brier_total = float(
        joined.select(
            (
                pl.col(exposure_column) * (1.0 + probability_square)
                - 2.0 * observed_probability
            ).sum()
        ).item()
    )
    probability_sum = pl.sum_horizontal(
        *(pl.col(f"p_{component}") for component in component_columns)
    )
    if joined.filter((probability_sum - 1.0).abs() > 1e-9).height:
        raise ValueError("component predictions do not sum to one")
    return {
        "players": joined.height,
        "target_exposure": int(total_exposure),
        "component_log_loss": negative_log_likelihood / total_exposure,
        "component_brier_score": brier_total / total_exposure,
        "calibration": calibration,
    }
