"""Frozen training-origin selection helpers for Hitter v2 Stage 2f H0."""

from __future__ import annotations

from typing import Mapping

import numpy as np
import polars as pl

from universal_baseball.hitter_v2_evaluation import NESTED_COMPONENT_CHILD_LEAVES
from universal_baseball.hitter_v2_model import NESTED_NODES
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_stage2f import (
    ReferenceTranslationFit,
    normalize_level,
    probabilities_from_links,
    probability_links,
)
from universal_baseball.hitter_v2_stage2f_fit import (
    H0FitSurfaces,
    apply_compiled_h0_projection,
    compile_h0_surfaces,
)


SELECTION_TOLERANCE = 1e-8


def aggregate_training_origin_target(
    outer_training: pl.DataFrame,
    *,
    origin_season: int,
    eligible_player_ids: set[int],
) -> pl.DataFrame:
    """Build an earlier-origin response only from the outer predictor history."""

    if outer_training.filter(pl.col("season") > origin_season).height:
        raise ValueError("origin target input contains later outer-history seasons")
    season = outer_training.filter(
        (pl.col("season") == origin_season)
        & pl.col("player_id").is_in(sorted(eligible_player_ids))
        & pl.col("modeling_eligible")
        & (pl.col("hitter_talent_pa") > 0)
    )
    if season.is_empty():
        raise ValueError("training origin has no eligible response rows")
    primary = (
        season.group_by("player_id", "level_group")
        .agg(pl.col("hitter_talent_pa").sum().alias("level_pa"))
        .sort(
            ["player_id", "level_pa", "level_group"],
            descending=[False, True, False],
        )
        .unique("player_id", keep="first", maintain_order=True)
    )
    target = season.group_by("player_id").agg(
        pl.col("hitter_talent_pa").sum().alias("hitter_talent_pa"),
        *[pl.col(outcome).sum().alias(outcome) for outcome in HITTER_TALENT_OUTCOMES],
    )
    return target.join(
        primary.select("player_id", "level_group"),
        on="player_id",
        how="left",
        validate="1:1",
    ).sort("player_id")


def translate_training_origin_target(
    target: pl.DataFrame,
    translation: ReferenceTranslationFit | None,
) -> pl.DataFrame:
    """Put earlier-origin response mass on the training-frozen reference level."""

    if translation is None:
        return target
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
    for row in target.iter_rows(named=True):
        evidence = float(row["hitter_talent_pa"])
        probabilities = {
            outcome: float(row[outcome]) / evidence
            for outcome in HITTER_TALENT_OUTCOMES
        }
        projected = apply_compiled_h0_projection(
            probabilities,
            compiled,
            observed_level=normalize_level(row["level_group"]),
            age_at_target=None,
            include_calibration=False,
        )
        rows.append(
            {
                "player_id": int(row["player_id"]),
                "hitter_talent_pa": evidence,
                "level_group": normalize_level(row["level_group"]),
                **{
                    outcome: projected.probabilities[outcome] * evidence
                    for outcome in HITTER_TALENT_OUTCOMES
                },
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None).sort("player_id")


def backtranslate_predictions_to_scoring_level(
    reference_predictions: pl.DataFrame,
    raw_target: pl.DataFrame,
    translation: ReferenceTranslationFit | None,
) -> pl.DataFrame:
    """Map reference forecasts to fixed observed levels for proper event scoring."""

    if translation is None:
        return reference_predictions
    offsets = {
        (str(row["component"]), str(row["level"])): float(row["link_offset_to_MLB"])
        for row in translation.offsets.filter(pl.col("age_band") == "ALL").iter_rows(
            named=True
        )
    }
    joined = reference_predictions.join(
        raw_target.select("player_id", "level_group"),
        on="player_id",
        how="inner",
        validate="1:1",
    )
    rows: list[dict[str, object]] = []
    for row in joined.iter_rows(named=True):
        level = normalize_level(row["level_group"])
        links = probability_links(
            {outcome: float(row[f"p_{outcome}"]) for outcome in HITTER_TALENT_OUTCOMES}
        )
        scoring_links = {
            component: value - offsets.get((component, level), 0.0)
            for component, value in links.items()
        }
        probabilities = probabilities_from_links(scoring_links)
        rows.append(
            {
                "player_id": int(row["player_id"]),
                **{
                    f"p_{outcome}": probabilities[outcome]
                    for outcome in HITTER_TALENT_OUTCOMES
                },
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None).sort("player_id")


def nested_selection_scores(
    predictions: pl.DataFrame,
    target: pl.DataFrame,
) -> tuple[list[dict[str, float | int | str]], float, int]:
    """Return frozen component scores and their event-weighted aggregate."""

    probability_columns = [f"p_{outcome}" for outcome in HITTER_TALENT_OUTCOMES]
    joined = target.join(
        predictions.select("player_id", *probability_columns),
        on="player_id",
        how="inner",
        validate="1:1",
    )
    rows: list[dict[str, float | int | str]] = []
    for node in NESTED_NODES:
        children = NESTED_COMPONENT_CHILD_LEAVES[node.name]
        child_counts = np.column_stack(
            [
                sum(
                    (joined[outcome].to_numpy().astype(float) for outcome in leaves),
                    start=np.zeros(joined.height),
                )
                for leaves in children
            ]
        )
        child_mass = np.column_stack(
            [
                sum(
                    (
                        joined[f"p_{outcome}"].to_numpy().astype(float)
                        for outcome in leaves
                    ),
                    start=np.zeros(joined.height),
                )
                for leaves in children
            ]
        )
        parent_events = child_counts.sum(axis=1)
        eligible = parent_events > 0.0
        events = float(parent_events[eligible].sum())
        if events <= 0.0:
            raise ValueError(f"component {node.name} has no target events")
        conditional = child_mass[eligible] / child_mass[eligible].sum(
            axis=1, keepdims=True
        )
        loss = -float(
            np.sum(child_counts[eligible] * np.log(np.maximum(conditional, 1e-15)))
        )
        rows.append(
            {
                "component": node.name,
                "events": int(events),
                "event_log_loss": loss / events,
            }
        )
    total_events = sum(int(row["events"]) for row in rows)
    aggregate = (
        sum(float(row["event_log_loss"]) * int(row["events"]) for row in rows)
        / total_events
    )
    return rows, aggregate, total_events


def build_reference_calibration_rows(
    predictions: pl.DataFrame,
    reference_target: pl.DataFrame,
    *,
    target_season: int,
) -> pl.DataFrame:
    """Build link calibration evidence from an already translated prior origin."""

    joined = reference_target.join(
        predictions.select(
            "player_id",
            *[f"p_{outcome}" for outcome in HITTER_TALENT_OUTCOMES],
        ),
        on="player_id",
        how="inner",
        validate="1:1",
    )
    rows: list[dict[str, object]] = []
    for row in joined.iter_rows(named=True):
        evidence = float(row["hitter_talent_pa"])
        predicted = probability_links(
            {outcome: float(row[f"p_{outcome}"]) for outcome in HITTER_TALENT_OUTCOMES}
        )
        observed = probability_links(
            {
                outcome: float(row[outcome]) / evidence
                for outcome in HITTER_TALENT_OUTCOMES
            }
        )
        for component in predicted:
            rows.append(
                {
                    "component": component,
                    "predicted_link": predicted[component],
                    "observed_link": observed[component],
                    "evidence": evidence,
                    "target_season": int(target_season),
                }
            )
    return pl.DataFrame(rows)


def select_surface_configuration(scores: pl.DataFrame) -> dict[str, float]:
    """Apply the frozen aggregate score and larger-shrinkage tie rule."""

    required = {
        "translation_prior_mover_pa",
        "development_prior_sd",
        "calibration_prior_sd",
        "event_log_loss",
    }
    if missing := sorted(required - set(scores.columns)):
        raise ValueError(f"surface selection scores missing columns: {missing}")
    minimum = float(scores["event_log_loss"].min())
    tied = scores.filter(
        pl.col("event_log_loss") <= minimum + SELECTION_TOLERANCE
    ).sort(
        [
            "translation_prior_mover_pa",
            "development_prior_sd",
            "calibration_prior_sd",
        ],
        descending=[True, False, False],
    )
    winner = tied.row(0, named=True)
    return {
        "translation_prior_mover_pa": float(winner["translation_prior_mover_pa"]),
        "development_prior_sd": float(winner["development_prior_sd"]),
        "calibration_prior_sd": float(winner["calibration_prior_sd"]),
        "event_log_loss": float(winner["event_log_loss"]),
    }


def selected_component_maps(
    selected: Mapping[str, Mapping[str, float | None]],
) -> tuple[dict[str, float], dict[str, float]]:
    """Extract complete half-life and prior maps from the frozen selection."""

    expected = {node.name for node in NESTED_NODES}
    if set(selected) != expected:
        raise ValueError("selected component configuration is incomplete")
    half_lives = {
        component: float(values["half_life_seasons"])
        for component, values in selected.items()
    }
    priors = {
        component: float(values["component_prior_pa"])
        for component, values in selected.items()
    }
    return half_lives, priors
