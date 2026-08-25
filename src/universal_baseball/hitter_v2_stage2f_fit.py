"""Chronology-safe source preparation and fit-only Hitter v2 Stage 2f helpers.

The functions in this module accept already-certified historical predictor
tables.  They have no target loader, evaluation scorer, or protected-season
knowledge.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import polars as pl

from universal_baseball.hitter_v2_c1 import (
    aggregate_player_park_exposure,
    attach_relative_ages,
    estimate_player_season_probabilities,
    neutralize_player_season_parks,
)
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_stage2f import (
    AGE_KNOTS,
    CalibrationFit,
    DevelopmentFit,
    H0Projection,
    LEVELS,
    ReferenceTranslationFit,
    apply_h0_neutral_projection,
    fit_forward_development,
    fit_reference_level_translations,
    fit_training_origin_calibration,
    normalize_level,
    probabilities_from_links,
    probability_links,
    translation_age_band,
    wrap_reference_level_probabilities,
)


@dataclass(frozen=True, slots=True)
class H0FitSources:
    """Fit-only player-season and adjacent-season predictor sources."""

    player_seasons: pl.DataFrame
    adjacent_pairs: pl.DataFrame
    translation_pairs: pl.DataFrame
    level_age_references: dict[str, float]


@dataclass(frozen=True, slots=True)
class H0FitSurfaces:
    """One fold's fitted transformations, excluding evaluation metrics."""

    translation: ReferenceTranslationFit | None
    development: DevelopmentFit | None
    calibration: CalibrationFit | None
    development_pairs: pl.DataFrame
    calibration_origins: pl.DataFrame


@dataclass(frozen=True, slots=True)
class CompiledH0Surfaces:
    """Dictionary representation used to avoid repeated table scans."""

    translation: dict[tuple[str, str, str], tuple[float, str, float]]
    development_coefficients: dict[tuple[str, str], float]
    development_transforms: dict[tuple[str, str], tuple[float, float]]
    level_age_references: Mapping[str, float]
    calibration: dict[str, tuple[float, float]]


def _probabilities_from_row(
    row: Mapping[str, object], *, prefix: str
) -> dict[str, float]:
    return {
        outcome: float(row[f"{prefix}{outcome}"]) for outcome in HITTER_TALENT_OUTCOMES
    }


def compile_h0_surfaces(surfaces: H0FitSurfaces) -> CompiledH0Surfaces:
    """Compile immutable fit tables once for linear-time forecast application."""

    translation = (
        {
            (str(row["component"]), str(row["level"]), str(row["age_band"])): (
                float(row["link_offset_to_MLB"]),
                str(row["path_quality"]),
                float(row["translation_uncertainty"]),
            )
            for row in surfaces.translation.offsets.iter_rows(named=True)
        }
        if surfaces.translation is not None
        else {}
    )
    coefficients = (
        {
            (str(row["component"]), str(row["feature"])): float(row["coefficient"])
            for row in surfaces.development.coefficients.iter_rows(named=True)
        }
        if surfaces.development is not None
        else {}
    )
    transforms = (
        {
            (str(row["component"]), str(row["feature"])): (
                float(row["mean"]),
                float(row["scale"]),
            )
            for row in surfaces.development.transforms.iter_rows(named=True)
        }
        if surfaces.development is not None
        else {}
    )
    calibration = (
        {
            str(row["component"]): (
                float(row["intercept"]),
                float(row["slope"]),
            )
            for row in surfaces.calibration.coefficients.iter_rows(named=True)
        }
        if surfaces.calibration is not None
        else {}
    )
    return CompiledH0Surfaces(
        translation=translation,
        development_coefficients=coefficients,
        development_transforms=transforms,
        level_age_references=(
            surfaces.development.level_age_references
            if surfaces.development is not None
            else {}
        ),
        calibration=calibration,
    )


def apply_compiled_h0_projection(
    probabilities: Mapping[str, float],
    compiled: CompiledH0Surfaces,
    *,
    observed_level: object,
    age_at_target: float | None,
    include_calibration: bool,
) -> H0Projection:
    """Apply a compiled surface with the same frozen link arithmetic as H0."""

    level = normalize_level(observed_level)
    if (
        not compiled.translation
        and not compiled.development_coefficients
        and (not include_calibration or not compiled.calibration)
    ):
        return apply_h0_neutral_projection(probabilities, observed_level=level)
    band = "ALL" if age_at_target is None else translation_age_band(age_at_target)
    qualities: list[str] = []
    uncertainties: list[float] = []
    development_applied = False
    calibration_applied = False
    adjusted: dict[str, float] = {}
    for component, raw_link in probability_links(probabilities).items():
        value = raw_link
        translation = compiled.translation.get((component, level, band))
        if translation is None and compiled.translation:
            qualities.append("neutral_disconnected_component_fallback")
            uncertainties.append(float("inf"))
        elif translation is not None:
            offset, quality, uncertainty = translation
            value += offset
            qualities.append(quality)
            uncertainties.append(uncertainty)
        if (
            age_at_target is not None
            and (
                component,
                "intercept",
            )
            in compiled.development_coefficients
        ):
            reference_age = float(compiled.level_age_references[level])
            raw_features = {
                "age_relative_to_level": float(age_at_target) - reference_age,
                **{
                    f"age_above_{int(knot)}": max(float(age_at_target) - knot, 0.0)
                    for knot in AGE_KNOTS
                },
            }
            delta = compiled.development_coefficients[(component, "intercept")]
            for feature, raw_feature in raw_features.items():
                mean, scale = compiled.development_transforms[(component, feature)]
                delta += (
                    compiled.development_coefficients[(component, feature)]
                    * (raw_feature - mean)
                    / scale
                )
            value += delta
            development_applied = development_applied or delta != 0.0
        if include_calibration and component in compiled.calibration:
            intercept, slope = compiled.calibration[component]
            value = intercept + slope * value
            calibration_applied = True
        adjusted[component] = value
    projected = probabilities_from_links(adjusted)
    if any(quality.startswith("neutral_disconnected") for quality in qualities):
        path_quality = "neutral_disconnected_component_fallback"
        uncertainty = float("inf")
    elif "global_fallback" in qualities:
        path_quality = "global_fallback"
        uncertainty = max(uncertainties, default=0.0)
    elif "age_band_fallback" in qualities:
        path_quality = "age_band_fallback"
        uncertainty = max(uncertainties, default=0.0)
    elif level == "MLB":
        path_quality = "reference"
        uncertainty = 0.0
    else:
        path_quality = "partially_pooled_mover_path"
        uncertainty = max(uncertainties, default=0.0)
    return H0Projection(
        probabilities=projected,
        reference_level="MLB",
        translation_path_quality=path_quality,
        translation_uncertainty=uncertainty,
        development_applied=development_applied,
        calibration_applied=calibration_applied,
    )


def _empty_adjacent_pairs() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "player_id": pl.Int64,
            "origin_season": pl.Int64,
            "destination_season": pl.Int64,
            "origin_level": pl.String,
            "destination_level": pl.String,
            "origin_age": pl.Float64,
            "destination_age": pl.Float64,
            "mover_pa": pl.Float64,
            **{
                f"origin_link_{component}": pl.Float64
                for component in probability_links(
                    {
                        outcome: 1.0 / len(HITTER_TALENT_OUTCOMES)
                        for outcome in HITTER_TALENT_OUTCOMES
                    }
                )
            },
            **{
                f"destination_link_{component}": pl.Float64
                for component in probability_links(
                    {
                        outcome: 1.0 / len(HITTER_TALENT_OUTCOMES)
                        for outcome in HITTER_TALENT_OUTCOMES
                    }
                )
            },
        }
    )


def materialize_h0_fit_sources(
    training: pl.DataFrame,
    player_games: pl.DataFrame,
    park_context: pl.DataFrame,
    park_offsets: pl.DataFrame,
    historical_ages: pl.DataFrame,
    *,
    predictor_cutoff_season: int,
    component_prior_pa: float,
) -> H0FitSources:
    """Materialize park-neutral, one-row-per-player-season H0 fit sources."""

    for label, frame in (
        ("training", training),
        ("player_games", player_games),
        ("park_context", park_context),
        ("park_offsets", park_offsets),
        ("historical_ages", historical_ages),
    ):
        if "season" not in frame.columns:
            raise ValueError(f"{label} source is missing season")
        if frame.filter(pl.col("season") > predictor_cutoff_season).height:
            raise ValueError(f"{label} source crosses the predictor cutoff")

    priors = {
        name: float(component_prior_pa)
        for name in (
            "plate_appearance",
            "non_k",
            "non_k_non_ubb",
            "contact",
            "non_hr_contact",
            "reach",
            "hit_in_play",
            "non_hit_reach",
            "non_reach",
        )
    }
    player_seasons = estimate_player_season_probabilities(
        training,
        predictor_cutoff_season=predictor_cutoff_season,
        component_prior_pa=priors,
    )
    exposure = aggregate_player_park_exposure(
        player_games,
        park_context,
        park_offsets,
        predictor_cutoff_season=predictor_cutoff_season,
        by_season=True,
    )
    neutral = neutralize_player_season_parks(player_seasons, exposure)
    aged = attach_relative_ages(neutral, historical_ages).sort("player_id", "season")
    if aged.is_duplicated().any():
        raise ValueError("H0 player-season source contains duplicate rows")
    key_duplicates = (
        aged.group_by("player_id", "season").len().filter(pl.col("len") != 1)
    )
    if key_duplicates.height:
        raise ValueError("H0 player-season source is not unique by player and season")

    lookup = {
        (int(row["player_id"]), int(row["season"])): row
        for row in aged.iter_rows(named=True)
    }
    pair_rows: list[dict[str, object]] = []
    for (player_id, season), origin in sorted(lookup.items()):
        destination = lookup.get((player_id, season + 1))
        if destination is None:
            continue
        origin_links = probability_links(
            _probabilities_from_row(origin, prefix="neutral_p_")
        )
        destination_links = probability_links(
            _probabilities_from_row(destination, prefix="neutral_p_")
        )
        pair_rows.append(
            {
                "player_id": player_id,
                "origin_season": season,
                "destination_season": season + 1,
                "origin_level": normalize_level(origin["level_group"]),
                "destination_level": normalize_level(destination["level_group"]),
                "origin_age": origin["age_years"],
                "destination_age": destination["age_years"],
                "mover_pa": min(
                    float(origin["hitter_talent_pa"]),
                    float(destination["hitter_talent_pa"]),
                ),
                **{
                    f"origin_link_{component}": value
                    for component, value in origin_links.items()
                },
                **{
                    f"destination_link_{component}": value
                    for component, value in destination_links.items()
                },
            }
        )
    adjacent = pl.DataFrame(pair_rows) if pair_rows else _empty_adjacent_pairs()
    link_components = probability_links(
        {
            outcome: 1.0 / len(HITTER_TALENT_OUTCOMES)
            for outcome in HITTER_TALENT_OUTCOMES
        }
    )
    translation_rows: list[dict[str, object]] = []
    for row in adjacent.iter_rows(named=True):
        if row["origin_level"] == row["destination_level"]:
            continue
        if row["destination_age"] is None:
            continue
        for component in link_components:
            translation_rows.append(
                {
                    "component": component,
                    "origin_level": row["origin_level"],
                    "destination_level": row["destination_level"],
                    "age": float(row["destination_age"]),
                    "link_delta": float(row[f"destination_link_{component}"])
                    - float(row[f"origin_link_{component}"]),
                    "mover_pa": float(row["mover_pa"]),
                    "origin_season": int(row["origin_season"]),
                    "destination_season": int(row["destination_season"]),
                }
            )
    translation_pairs = (
        pl.DataFrame(translation_rows)
        if translation_rows
        else pl.DataFrame(
            schema={
                "component": pl.String,
                "origin_level": pl.String,
                "destination_level": pl.String,
                "age": pl.Float64,
                "link_delta": pl.Float64,
                "mover_pa": pl.Float64,
                "origin_season": pl.Int64,
                "destination_season": pl.Int64,
            }
        )
    )
    medians = (
        aged.filter(pl.col("age_years").is_not_null())
        .with_columns(
            pl.col("level_group")
            .map_elements(normalize_level, return_dtype=pl.String)
            .alias("normalized_level")
        )
        .group_by("normalized_level")
        .agg(pl.col("age_years").median().alias("median_age"))
    )
    median_map = {
        str(row["normalized_level"]): float(row["median_age"])
        for row in medians.iter_rows(named=True)
    }
    missing_levels = sorted(set(LEVELS) - set(median_map))
    if missing_levels:
        raise ValueError(
            f"H0 age references missing affiliated levels: {missing_levels}"
        )
    return H0FitSources(
        player_seasons=aged,
        adjacent_pairs=adjacent,
        translation_pairs=translation_pairs,
        level_age_references=median_map,
    )


def _translation_offset(
    fit: ReferenceTranslationFit,
    component: str,
    level: str,
    age: float | None,
) -> float:
    band = "ALL" if age is None else translation_age_band(age)
    row = fit.offsets.filter(
        (pl.col("component") == component)
        & (pl.col("level") == normalize_level(level))
        & (pl.col("age_band") == band)
    )
    if row.is_empty():
        return 0.0
    return float(row["link_offset_to_MLB"].item())


def materialize_development_pairs(
    adjacent_pairs: pl.DataFrame,
    translation: ReferenceTranslationFit,
) -> pl.DataFrame:
    """Translate both sides of prior adjacent pairs before development fitting."""

    components = [
        column.removeprefix("origin_link_")
        for column in adjacent_pairs.columns
        if column.startswith("origin_link_")
    ]
    rows: list[dict[str, object]] = []
    for row in adjacent_pairs.iter_rows(named=True):
        if row["destination_age"] is None:
            continue
        for component in components:
            origin = float(row[f"origin_link_{component}"]) + _translation_offset(
                translation,
                component,
                str(row["origin_level"]),
                None if row["origin_age"] is None else float(row["origin_age"]),
            )
            destination = float(
                row[f"destination_link_{component}"]
            ) + _translation_offset(
                translation,
                component,
                str(row["destination_level"]),
                float(row["destination_age"]),
            )
            rows.append(
                {
                    "component": component,
                    "level": str(row["destination_level"]),
                    "age": float(row["destination_age"]),
                    "reference_link_delta": destination - origin,
                    "mover_pa": float(row["mover_pa"]),
                    "origin_season": int(row["origin_season"]),
                    "destination_season": int(row["destination_season"]),
                }
            )
    return pl.DataFrame(rows)


def fit_h0_surfaces(
    sources: H0FitSources,
    *,
    predictor_cutoff_season: int,
    translation_prior_mover_pa: float,
    development_prior_sd: float,
    calibration_prior_sd: float,
    calibration_origins: pl.DataFrame | None = None,
) -> H0FitSurfaces:
    """Fit one fold's real-data surfaces without evaluating forecast outcomes."""

    if sources.translation_pairs.is_empty():
        return H0FitSurfaces(
            translation=None,
            development=None,
            calibration=None,
            development_pairs=pl.DataFrame(),
            calibration_origins=pl.DataFrame(),
        )
    translation = fit_reference_level_translations(
        sources.translation_pairs,
        predictor_cutoff_season=predictor_cutoff_season,
        prior_mover_pa=translation_prior_mover_pa,
    )
    development_pairs = materialize_development_pairs(
        sources.adjacent_pairs, translation
    )
    development = fit_forward_development(
        development_pairs,
        predictor_cutoff_season=predictor_cutoff_season,
        prior_sd=development_prior_sd,
        level_age_references=sources.level_age_references,
    )
    origins = calibration_origins if calibration_origins is not None else pl.DataFrame()
    calibration = (
        fit_training_origin_calibration(
            origins,
            predictor_cutoff_season=predictor_cutoff_season,
            prior_sd=calibration_prior_sd,
        )
        if not origins.is_empty()
        else None
    )
    return H0FitSurfaces(
        translation=translation,
        development=development,
        calibration=calibration,
        development_pairs=development_pairs,
        calibration_origins=origins,
    )


def latest_player_context(player_seasons: pl.DataFrame) -> pl.DataFrame:
    """Return the chronology-safe latest observed level for every player."""

    return (
        player_seasons.sort(
            ["player_id", "season", "hitter_talent_pa", "league_id"],
            descending=[False, True, True, False],
        )
        .unique("player_id", keep="first", maintain_order=True)
        .select("player_id", "season", "level_group")
    )


def apply_surfaces_to_predictions(
    base_predictions: pl.DataFrame,
    player_context: pl.DataFrame,
    forecast_ages: pl.DataFrame,
    surfaces: H0FitSurfaces,
    *,
    include_calibration: bool,
    model_id: str,
) -> pl.DataFrame:
    """Apply fitted H0 surfaces to an unscored full-population forecast."""

    joined = base_predictions.join(
        player_context,
        on="player_id",
        how="left",
        validate="1:1",
    ).join(
        forecast_ages.select("player_id", "age_years"),
        on="player_id",
        how="left",
        validate="1:1",
    )
    if joined.filter(pl.col("level_group").is_null()).height:
        raise ValueError("H0 prediction is missing prior observed level")
    compiled = compile_h0_surfaces(surfaces)
    rows: list[dict[str, object]] = []
    for row in joined.iter_rows(named=True):
        base = _probabilities_from_row(row, prefix="p_")
        projection = apply_compiled_h0_projection(
            base,
            compiled,
            observed_level=row["level_group"],
            include_calibration=include_calibration,
            age_at_target=(
                None if row["age_years"] is None else float(row["age_years"])
            ),
        )
        rows.append(
            {
                "player_id": int(row["player_id"]),
                "model_id": model_id,
                "prior_level": normalize_level(row["level_group"]),
                "prior_level_season": int(row["season"]),
                "age_at_target": row["age_years"],
                "translation_path_quality": projection.translation_path_quality,
                "translation_uncertainty": projection.translation_uncertainty,
                "development_applied": projection.development_applied,
                "calibration_applied": projection.calibration_applied,
                **{
                    f"p_{outcome}": projection.probabilities[outcome]
                    for outcome in HITTER_TALENT_OUTCOMES
                },
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None).sort("player_id")


def wrap_baseline_predictions(
    base_predictions: pl.DataFrame,
    player_context: pl.DataFrame,
    translation: ReferenceTranslationFit | None,
    *,
    model_id: str,
) -> pl.DataFrame:
    """Put one permanent baseline on the common reference level without scoring."""

    joined = base_predictions.join(
        player_context, on="player_id", how="left", validate="1:1"
    )
    compiled = compile_h0_surfaces(
        H0FitSurfaces(
            translation=translation,
            development=None,
            calibration=None,
            development_pairs=pl.DataFrame(),
            calibration_origins=pl.DataFrame(),
        )
    )
    rows: list[dict[str, object]] = []
    for row in joined.iter_rows(named=True):
        probabilities = _probabilities_from_row(row, prefix="p_")
        projection = apply_compiled_h0_projection(
            probabilities,
            compiled,
            observed_level=row["level_group"],
            age_at_target=None,
            include_calibration=False,
        )
        rows.append(
            {
                "player_id": int(row["player_id"]),
                "model_id": model_id,
                "translation_path_quality": projection.translation_path_quality,
                **{
                    f"p_{outcome}": projection.probabilities[outcome]
                    for outcome in HITTER_TALENT_OUTCOMES
                },
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None).sort("player_id")


def build_calibration_origins(
    prior_precal_predictions: pl.DataFrame,
    observed_player_seasons: pl.DataFrame,
    prior_translation: ReferenceTranslationFit,
    *,
    target_season: int,
) -> pl.DataFrame:
    """Build earlier-origin calibration rows using its own frozen translation."""

    observed = observed_player_seasons.filter(pl.col("season") == target_season)
    joined = prior_precal_predictions.join(
        observed.select(
            "player_id",
            "level_group",
            "age_years",
            "hitter_talent_pa",
            *[f"neutral_p_{outcome}" for outcome in HITTER_TALENT_OUTCOMES],
        ),
        on="player_id",
        how="inner",
        validate="1:1",
    )
    rows: list[dict[str, object]] = []
    for row in joined.iter_rows(named=True):
        predicted_links = probability_links(_probabilities_from_row(row, prefix="p_"))
        observed_projection = wrap_reference_level_probabilities(
            _probabilities_from_row(row, prefix="neutral_p_"),
            observed_level=row["level_group"],
            translation=prior_translation,
        )
        observed_links = probability_links(observed_projection.probabilities)
        for component in predicted_links:
            rows.append(
                {
                    "component": component,
                    "predicted_link": predicted_links[component],
                    "observed_link": observed_links[component],
                    "evidence": float(row["hitter_talent_pa"]),
                    "target_season": int(target_season),
                }
            )
    return pl.DataFrame(rows)
