"""Chronology-safe park features for future player models.

Park effects are offered to a forecast as explanatory features.  They do not
automatically alter a player's talent estimate: the future-player model must
learn whether, and how much, the context improves held-out projections.
"""

from __future__ import annotations

import math

import polars as pl


def build_park_factor_vintage(
    factors: pl.DataFrame,
    *,
    through_season: int,
    components: tuple[str, ...],
    prior_exposure: float,
) -> pl.DataFrame:
    """Make one auditable, wide park-feature row per venue.

    ``factors`` is the long output of ``fit_component_park_factors``.  The
    vintage records what was knowable when the effects were fit and exposes a
    reliability feature rather than hiding shrinkage from the gradient model.
    """

    required = {
        "venue_id",
        "component",
        "training_precision",
        "training_seasons",
        "park_clr_effect",
    }
    if missing := sorted(required - set(factors.columns)):
        raise ValueError(f"park factors missing fields: {missing}")
    if not components or len(set(components)) != len(components):
        raise ValueError("components must be nonempty and unique")
    if not math.isfinite(prior_exposure) or prior_exposure < 0:
        raise ValueError("prior exposure must be finite and nonnegative")
    if factors.group_by(["venue_id", "component"]).len().filter(
        pl.col("len") != 1
    ).height:
        raise ValueError("park factors violate venue/component grain")
    observed_components = set(factors["component"].unique().to_list())
    if observed_components != set(components):
        raise ValueError("park factor components do not match requested components")
    if factors.filter(
        pl.col("training_precision").is_null()
        | pl.col("training_seasons").is_null()
        | pl.col("park_clr_effect").is_null()
        | ~pl.col("training_precision").is_finite()
        | ~pl.col("park_clr_effect").is_finite()
        | (pl.col("training_precision") < 0)
        | (pl.col("training_seasons") < 1)
    ).height:
        raise ValueError("park factors contain invalid estimates or training support")

    support = factors.group_by("venue_id").agg(
        pl.col("training_precision").n_unique().alias("precision_values"),
        pl.col("training_seasons").n_unique().alias("season_values"),
        pl.col("training_precision").first().alias("park_training_precision"),
        pl.col("training_seasons").first().alias("park_training_seasons"),
    )
    if support.filter(
        (pl.col("precision_values") != 1) | (pl.col("season_values") != 1)
    ).height:
        raise ValueError("park support must be identical across components")

    wide = factors.select("venue_id", "component", "park_clr_effect").pivot(
        on="component", index="venue_id", values="park_clr_effect"
    ).rename({value: f"park_effect_{value}" for value in components})
    return (
        support.drop("precision_values", "season_values")
        .join(wide, on="venue_id", how="inner", validate="1:1")
        .with_columns(
            pl.lit(int(through_season)).alias("park_factor_through_season"),
            (
                pl.col("park_training_precision")
                / (pl.col("park_training_precision") + float(prior_exposure))
            )
            .fill_nan(0.0)
            .alias("park_factor_reliability"),
            pl.lit(True).alias("park_factor_known"),
        )
        .select(
            "venue_id",
            "park_factor_through_season",
            "park_factor_known",
            "park_training_precision",
            "park_training_seasons",
            "park_factor_reliability",
            *(f"park_effect_{value}" for value in components),
        )
        .sort("venue_id")
    )


def attach_prior_park_features(
    rows: pl.DataFrame,
    vintage: pl.DataFrame,
    *,
    components: tuple[str, ...],
) -> pl.DataFrame:
    """Attach only a strictly earlier park vintage, with neutral fallbacks.

    Missing/new venues remain in the data with zero effects and zero
    reliability.  This is both a safe fallback and a signal the gradient model
    can use to avoid treating an unknown park as a precise neutral estimate.
    """

    if missing := sorted({"season", "venue_id"} - set(rows.columns)):
        raise ValueError(f"park feature rows missing fields: {missing}")
    required = {
        "venue_id",
        "park_factor_through_season",
        "park_factor_known",
        "park_training_precision",
        "park_training_seasons",
        "park_factor_reliability",
        *(f"park_effect_{value}" for value in components),
    }
    if missing := sorted(required - set(vintage.columns)):
        raise ValueError(f"park factor vintage missing fields: {missing}")
    if vintage["park_factor_through_season"].n_unique() != 1:
        raise ValueError("park factor vintage must have one through-season")
    through_season = int(vintage.item(0, "park_factor_through_season"))
    if rows.filter(pl.col("season") <= through_season).height:
        raise ValueError("park factors must be fit strictly before every feature row")

    effect_columns = [f"park_effect_{value}" for value in components]
    return rows.join(vintage, on="venue_id", how="left", validate="m:1").with_columns(
        pl.col("park_factor_through_season").fill_null(through_season),
        pl.col("park_factor_known").fill_null(False),
        pl.col("park_training_precision").fill_null(0.0),
        pl.col("park_training_seasons").fill_null(0),
        pl.col("park_factor_reliability").fill_null(0.0),
        *(pl.col(value).fill_null(0.0) for value in effect_columns),
    )
