"""Partially pooled league-within-level component translation candidates."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np
import polars as pl

from universal_baseball.level_component_translation import (
    DEFAULT_LEVEL_EVIDENCE_MULTIPLIER,
    LEVEL_ORDER,
    _clr,
    fit_same_season_component_translation,
)


TRANSLATION_METHOD = "same_player_same_season_league_residual_ridge_v1"


@dataclass(frozen=True, slots=True)
class LeagueTranslationFit:
    offsets: pl.DataFrame
    metrics: dict[str, object]


def fit_same_season_league_translation(
    frame: pl.DataFrame,
    *,
    exposure_column: str,
    component_columns: tuple[str, ...],
    completed_seasons: tuple[int, ...],
    minimum_environment_exposure: int = 30,
    league_prior_exposure: float = 500.0,
    pseudocount: float = 0.5,
) -> LeagueTranslationFit:
    """Fit league residuals around the existing MLB-anchored level effects.

    MLB American/National League residuals are fixed at zero, so every output is
    expressed against the pooled MLB environment. Non-MLB league residuals are
    ridge-shrunk toward their parent level effect.
    """

    required = {
        "season",
        "player_id",
        "level_group",
        "league_id",
        exposure_column,
        *component_columns,
    }
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"league translation source missing columns: {missing}")
    if minimum_environment_exposure <= 0 or league_prior_exposure <= 0:
        raise ValueError("environment threshold and league prior exposure must be positive")
    level_fit = fit_same_season_component_translation(
        frame,
        exposure_column=exposure_column,
        component_columns=component_columns,
        completed_seasons=completed_seasons,
        minimum_level_exposure=minimum_environment_exposure,
        pseudocount=pseudocount,
    )
    level_effect = {
        (str(row["level_group"]), str(row["component"])): float(
            row["clr_environment_effect"]
        )
        for row in level_fit.offsets.iter_rows(named=True)
    }
    source = (
        frame.filter(pl.col("season").is_in(completed_seasons))
        .group_by("season", "player_id", "level_group", "league_id")
        .agg(
            pl.col(exposure_column).sum().alias(exposure_column),
            *(pl.col(column).sum().alias(column) for column in component_columns),
        )
        .filter(pl.col(exposure_column) >= minimum_environment_exposure)
    )
    if source.filter(pl.col("league_id").is_null()).height:
        raise ValueError("league translation source contains missing league identity")
    league_levels = source.select("league_id", "level_group").unique()
    if league_levels.group_by("league_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("league identity maps to more than one level")
    league_to_level = {
        int(row["league_id"]): str(row["level_group"])
        for row in league_levels.iter_rows(named=True)
    }
    non_mlb_leagues = sorted(
        league for league, level in league_to_level.items() if level != "MLB"
    )
    league_index = {league: index for index, league in enumerate(non_mlb_leagues)}

    pair_rows: list[dict[str, object]] = []
    deltas: list[np.ndarray] = []
    for group in source.partition_by(["season", "player_id"], maintain_order=False):
        rows = sorted(
            group.iter_rows(named=True),
            key=lambda row: (LEVEL_ORDER[str(row["level_group"])], int(row["league_id"])),
        )
        for left, right in combinations(rows, 2):
            left_league = int(left["league_id"])
            right_league = int(right["league_id"])
            if left_league == right_league:
                continue
            left_exposure = float(left[exposure_column])
            right_exposure = float(right[exposure_column])
            pair_rows.append(
                {
                    "from_league_id": left_league,
                    "to_league_id": right_league,
                    "from_level_group": str(left["level_group"]),
                    "to_level_group": str(right["level_group"]),
                    "precision_weight": 2.0 / (1.0 / left_exposure + 1.0 / right_exposure),
                }
            )
            deltas.append(
                _clr([float(right[column]) for column in component_columns], pseudocount)
                - _clr([float(left[column]) for column in component_columns], pseudocount)
            )
    if not pair_rows:
        raise ValueError("league translation source has no eligible environment pairs")

    design = np.zeros((len(pair_rows), len(non_mlb_leagues)), dtype=float)
    weights = np.asarray([float(row["precision_weight"]) for row in pair_rows])
    for row_index, pair in enumerate(pair_rows):
        left = int(pair["from_league_id"])
        right = int(pair["to_league_id"])
        if left in league_index:
            design[row_index, league_index[left]] -= 1.0
        if right in league_index:
            design[row_index, league_index[right]] += 1.0
    delta_matrix = np.vstack(deltas)
    residual_effects = np.zeros((len(non_mlb_leagues), len(component_columns)))
    weighted_cross = design.T @ (weights[:, None] * design)
    penalized_cross = weighted_cross + league_prior_exposure * np.eye(len(non_mlb_leagues))
    for component_index, component in enumerate(component_columns):
        baseline_delta = np.asarray(
            [
                level_effect[(str(pair["to_level_group"]), component)]
                - level_effect[(str(pair["from_level_group"]), component)]
                for pair in pair_rows
            ]
        )
        residual_target = delta_matrix[:, component_index] - baseline_delta
        residual_effects[:, component_index] = np.linalg.solve(
            penalized_cross,
            design.T @ (weights * residual_target),
        )

    rows = []
    for league_id, level_group in sorted(
        league_to_level.items(), key=lambda item: (LEVEL_ORDER[item[1]], item[0])
    ):
        for component_index, component in enumerate(component_columns):
            residual = (
                0.0
                if level_group == "MLB"
                else float(residual_effects[league_index[league_id], component_index])
            )
            rows.append(
                {
                    "league_id": league_id,
                    "level_group": level_group,
                    "component": component,
                    "level_clr_effect": level_effect[(level_group, component)],
                    "league_residual_clr_effect": residual,
                    "clr_environment_effect": level_effect[(level_group, component)] + residual,
                    "translation_method": TRANSLATION_METHOD,
                }
            )
    offsets = pl.DataFrame(rows).sort("level_group", "league_id", "component")
    centered = offsets.group_by("league_id").agg(
        pl.col("clr_environment_effect").sum().abs().alias("absolute_clr_sum")
    )
    if centered.filter(pl.col("absolute_clr_sum") > 1e-7).height:
        raise ValueError("league translation CLR profiles are not centered")
    return LeagueTranslationFit(
        offsets=offsets,
        metrics={
            "eligible_pairs": len(pair_rows),
            "distinct_leagues": len(league_to_level),
            "non_mlb_leagues": len(non_mlb_leagues),
            "league_prior_exposure": league_prior_exposure,
            "minimum_environment_exposure": minimum_environment_exposure,
            "completed_seasons": list(completed_seasons),
            "parent_level_method": level_fit.metrics,
            "partial_pooling_target": "parent_level_clr_effect",
            "mlb_league_residuals_fixed_zero": True,
        },
    )


def _translate(
    probabilities: dict[str, float],
    *,
    league_id: int,
    offsets: pl.DataFrame,
) -> dict[str, float]:
    components = tuple(sorted(probabilities))
    values = np.asarray([float(probabilities[component]) for component in components])
    if np.any(~np.isfinite(values)) or np.any(values <= 0):
        raise ValueError("translation probabilities must be finite and positive")
    relevant = offsets.filter(pl.col("league_id") == league_id)
    lookup = {
        str(row["component"]): float(row["clr_environment_effect"])
        for row in relevant.iter_rows(named=True)
    }
    if set(lookup) != set(components):
        raise ValueError(f"missing league translation offsets for {league_id}")
    clr = np.log(values) - np.log(values).mean()
    latent = clr - np.asarray([lookup[component] for component in components])
    exponentials = np.exp(latent - latent.max())
    translated = exponentials / exponentials.sum()
    return {component: float(translated[index]) for index, component in enumerate(components)}


def build_league_translated_affiliated_profiles(
    players: pl.DataFrame,
    history: pl.DataFrame,
    offsets: pl.DataFrame,
    *,
    exposure_column: str,
    component_columns: tuple[str, ...],
    current_season: int,
    reference_season: int,
    regression_exposure: float,
    pseudocount: float = 0.5,
) -> pl.DataFrame:
    """Build MLB-scale profiles using partially pooled league context."""

    if set(players.columns) != {"player_id"} or regression_exposure <= 0:
        raise ValueError("players must be player IDs and regression exposure must be positive")
    required = {
        "season",
        "player_id",
        "level_group",
        "league_id",
        exposure_column,
        *component_columns,
    }
    if missing := sorted(required - set(history.columns)):
        raise ValueError(f"league translated history missing columns: {missing}")
    source = (
        history.filter(pl.col("season").is_between(current_season - 2, current_season))
        .group_by("season", "player_id", "level_group", "league_id")
        .agg(
            pl.col(exposure_column).sum().alias(exposure_column),
            *(pl.col(column).sum().alias(column) for column in component_columns),
        )
        .filter(pl.col(exposure_column) > 0)
    )
    reference = source.filter(
        (pl.col("season") == reference_season) & (pl.col("level_group") == "MLB")
    )
    reference_total = float(reference.get_column(exposure_column).sum())
    if reference_total <= 0:
        raise ValueError("league translated profile requires an MLB reference")
    prior = {
        component: float(reference.get_column(component).sum()) / reference_total
        for component in component_columns
    }
    translated_rows = []
    for row in source.iter_rows(named=True):
        exposure = float(row[exposure_column])
        probabilities = {
            component: (float(row[component]) + pseudocount)
            / (exposure + pseudocount * len(component_columns))
            for component in component_columns
        }
        translated = _translate(
            probabilities,
            league_id=int(row["league_id"]),
            offsets=offsets,
        )
        recency_weight = {0: 3.0, 1: 2.0, 2: 1.0}[current_season - int(row["season"])]
        weight = recency_weight * DEFAULT_LEVEL_EVIDENCE_MULTIPLIER[str(row["level_group"])]
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
    output = []
    for row in players.join(weighted, on="player_id", how="left").iter_rows(named=True):
        evidence = float(row.get("weighted_exposure") or 0.0)
        raw = {
            component: (
                float(row.get(f"weighted_{component}") or 0.0)
                + regression_exposure * prior[component]
            )
            / (evidence + regression_exposure)
            for component in component_columns
        }
        total = sum(raw.values())
        output.append(
            {
                "player_id": int(row["player_id"]),
                "weighted_affiliated_exposure": evidence,
                "affiliated_reliability": evidence / (evidence + regression_exposure),
                **{f"p_{component}": raw[component] / total for component in component_columns},
            }
        )
    return pl.DataFrame(output).sort("player_id")
