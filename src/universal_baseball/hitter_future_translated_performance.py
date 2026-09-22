"""Next-season hitter performance targets translated onto one MLB scale."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import polars as pl

from universal_baseball.hitter_v2_evaluation import NEUTRAL_WOBA_WEIGHTS
from universal_baseball.level_component_translation import (
    LEVEL_ORDER,
    fit_same_season_component_translation,
    translate_component_probabilities_to_mlb,
)


HITTER_COMPONENTS = ("ubb", "hbp", "single", "double", "triple", "hr", "other")
TARGET_PSEUDOCOUNT = 0.5


@dataclass(frozen=True, slots=True)
class FutureTranslatedTargets:
    targets: pl.DataFrame
    translation_offsets: pl.DataFrame
    fold_metrics: tuple[dict[str, object], ...]


def _require(frame: pl.DataFrame, columns: set[str], label: str) -> None:
    if missing := sorted(columns - set(frame.columns)):
        raise ValueError(f"{label} missing fields: {missing}")


def build_hitter_component_counts(stats: pl.DataFrame) -> pl.DataFrame:
    """Convert official batting lines into the coherent seven-part PA profile."""

    _require(
        stats,
        {
            "season",
            "player_id",
            "level_group",
            "plate_appearances",
            "hits",
            "doubles",
            "triples",
            "home_runs",
            "base_on_balls",
            "intentional_walks",
            "hit_by_pitch",
        },
        "affiliated hitter statistics",
    )
    result = stats.with_columns(
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        pl.col("hit_by_pitch").alias("hbp"),
        (
            pl.col("hits") - pl.col("doubles") - pl.col("triples") - pl.col("home_runs")
        ).alias("single"),
        pl.col("doubles").alias("double"),
        pl.col("triples").alias("triple"),
        pl.col("home_runs").alias("hr"),
    ).with_columns(
        (
            pl.col("plate_appearances") - pl.sum_horizontal(*HITTER_COMPONENTS[:-1])
        ).alias("other")
    )
    if result.filter(
        (pl.col("plate_appearances") < 0)
        | pl.any_horizontal(*(pl.col(column) < 0 for column in HITTER_COMPONENTS))
        | (
            (pl.sum_horizontal(*HITTER_COMPONENTS) - pl.col("plate_appearances")).abs()
            > 1e-8
        )
    ).height:
        raise ValueError("hitter components do not reconcile to plate appearances")
    return result


def _translated_woba(probabilities: dict[str, float]) -> float:
    return (
        probabilities["ubb"] * NEUTRAL_WOBA_WEIGHTS["UBB"]
        + probabilities["hbp"] * NEUTRAL_WOBA_WEIGHTS["HBP"]
        + probabilities["single"] * NEUTRAL_WOBA_WEIGHTS["1B"]
        + probabilities["double"] * NEUTRAL_WOBA_WEIGHTS["2B"]
        + probabilities["triple"] * NEUTRAL_WOBA_WEIGHTS["3B"]
        + probabilities["hr"] * NEUTRAL_WOBA_WEIGHTS["HR"]
    )


def build_future_translated_targets(
    components: pl.DataFrame,
    *,
    origins: Iterable[int],
    minimum_translation_pa: int = 30,
    pseudocount: float = TARGET_PSEUDOCOUNT,
) -> FutureTranslatedTargets:
    """Translate each following-season level segment using cutoff-safe offsets.

    The future level is used only to put the observed target on a common scale.  It
    never enters the predictor matrix.
    """

    _require(
        components,
        {"season", "player_id", "level_group", "plate_appearances", *HITTER_COMPONENTS},
        "hitter component counts",
    )
    origins = tuple(sorted({int(value) for value in origins}))
    if not origins or any(origin >= 2025 for origin in origins):
        raise ValueError(
            "translated target origins must precede the protected 2026 season"
        )
    if minimum_translation_pa <= 0 or pseudocount <= 0:
        raise ValueError("translation exposure and pseudocount must be positive")
    unsupported = set(components["level_group"].drop_nulls().unique().to_list()) - set(
        LEVEL_ORDER
    )
    if unsupported:
        raise ValueError(f"unsupported target levels: {sorted(unsupported)}")

    target_frames: list[pl.DataFrame] = []
    offset_frames: list[pl.DataFrame] = []
    fold_metrics: list[dict[str, object]] = []
    available_seasons = sorted(components["season"].unique().to_list())
    for origin in origins:
        completed = tuple(int(year) for year in available_seasons if year <= origin)
        fit = fit_same_season_component_translation(
            components,
            exposure_column="plate_appearances",
            component_columns=HITTER_COMPONENTS,
            completed_seasons=completed,
            minimum_level_exposure=minimum_translation_pa,
            pseudocount=pseudocount,
        )
        offsets = fit.offsets.with_columns(pl.lit(origin).alias("origin_year"))
        offset_frames.append(offsets)
        future = (
            components.filter(pl.col("season") == origin + 1)
            .group_by("player_id", "level_group")
            .agg(
                pl.col("plate_appearances").sum().alias("plate_appearances"),
                *(pl.col(column).sum().alias(column) for column in HITTER_COMPONENTS),
            )
            .filter(pl.col("plate_appearances") > 0)
        )
        player_rows: dict[int, dict[str, object]] = {}
        for row in future.iter_rows(named=True):
            player_id = int(row["player_id"])
            pa = float(row["plate_appearances"])
            smoothed = {
                component: (float(row[component]) + pseudocount)
                / (pa + pseudocount * len(HITTER_COMPONENTS))
                for component in HITTER_COMPONENTS
            }
            translated = translate_component_probabilities_to_mlb(
                smoothed,
                level_group=str(row["level_group"]),
                offsets=fit.offsets,
            )
            destination = player_rows.setdefault(
                player_id,
                {
                    "origin_year": origin,
                    "target_season": origin + 1,
                    "player_id": player_id,
                    "target_affiliated_pa": 0.0,
                    "_level_pa": {},
                    **{
                        f"_translated_{component}": 0.0
                        for component in HITTER_COMPONENTS
                    },
                },
            )
            destination["target_affiliated_pa"] = (
                float(destination["target_affiliated_pa"]) + pa
            )
            level_pa = destination["_level_pa"]
            if not isinstance(level_pa, dict):
                raise TypeError("internal level exposure is not a mapping")
            level = str(row["level_group"])
            level_pa[level] = float(level_pa.get(level, 0.0)) + pa
            for component in HITTER_COMPONENTS:
                key = f"_translated_{component}"
                destination[key] = float(destination[key]) + translated[component] * pa

        output_rows: list[dict[str, object]] = []
        for row in player_rows.values():
            pa = float(row["target_affiliated_pa"])
            probabilities = {
                component: float(row[f"_translated_{component}"]) / pa
                for component in HITTER_COMPONENTS
            }
            level_pa = row["_level_pa"]
            if not isinstance(level_pa, dict):
                raise TypeError("internal level exposure is not a mapping")
            primary_level = max(
                level_pa,
                key=lambda level: (float(level_pa[level]), LEVEL_ORDER[str(level)]),
            )
            output_rows.append(
                {
                    "origin_year": int(row["origin_year"]),
                    "target_season": int(row["target_season"]),
                    "player_id": int(row["player_id"]),
                    "target_affiliated_pa": pa,
                    "target_primary_level_rank": LEVEL_ORDER[str(primary_level)],
                    "target_levels_played": len(level_pa),
                    "target_translated_woba": _translated_woba(probabilities),
                    **{
                        f"target_translated_rate__{component}": probability
                        for component, probability in probabilities.items()
                    },
                }
            )
        target_frames.append(pl.DataFrame(output_rows))
        fold_metrics.append(
            {
                "origin_year": origin,
                "target_season": origin + 1,
                "target_players": len(output_rows),
                "target_pa": int(
                    sum(float(row["target_affiliated_pa"]) for row in output_rows)
                ),
                "translation": fit.metrics,
            }
        )

    return FutureTranslatedTargets(
        targets=pl.concat(target_frames, how="vertical_relaxed").sort(
            ["origin_year", "player_id"]
        ),
        translation_offsets=pl.concat(offset_frames, how="vertical_relaxed").sort(
            ["origin_year", "level_group", "component"]
        ),
        fold_metrics=tuple(fold_metrics),
    )
