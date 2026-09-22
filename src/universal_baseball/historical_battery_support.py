"""All-level pitcher-catcher battery support from terminal plate appearances.

The public affiliated feed does not identify who selected a pitch or where the
catcher wanted it.  This module therefore estimates a deliberately narrower
quantity: after level-season, handedness, park, batter and pitcher context,
does a catcher's presence leave a repeatable residual in outcomes that are
available at every affiliated level?

The fitted effects are descriptive season estimates.  They become projection
evidence only when a strictly earlier-season effect predicts a later season.
"""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl


_STRIKEOUT = r"\b(?:strikes out|called out on strikes)\b"
_WALK = r"\bwalks\b"
_INTENTIONAL_WALK = r"\b(?:intentionally walks|intentional walk)\b"
_HIT_BY_PITCH = r"\bhit by pitch\b"
_SACRIFICE_BUNT = r"\b(?:sacrifice bunt|out on a sacrifice bunt)\b"


@dataclass(frozen=True)
class BatteryEffectFit:
    catchers: pl.DataFrame
    pitchers: pl.DataFrame
    batters: pl.DataFrame
    pairs: pl.DataFrame
    cells: pl.DataFrame


def classify_battery_plate_appearances(terminal: pl.DataFrame) -> pl.DataFrame:
    """Return completed, non-intentional affiliated PAs with universal targets."""

    required = {
        "season",
        "level",
        "game_pk",
        "at_bat_index",
        "batter",
        "pitcher",
        "fielder_2",
        "stand",
        "p_throws",
        "park_key",
        "bb_type",
        "pa_description",
        "terminal_outcome_group",
        "terminal_outcome_status",
    }
    missing = sorted(required - set(terminal.columns))
    if missing:
        raise ValueError(f"terminal plays missing battery fields: {missing}")

    text = (
        pl.col("pa_description")
        .cast(pl.String, strict=False)
        .fill_null("")
        .str.to_lowercase()
    )
    bb_type = pl.col("bb_type").cast(pl.String, strict=False).fill_null("")
    is_strikeout = text.str.contains(_STRIKEOUT)
    is_walk = text.str.contains(_WALK)
    is_intentional_walk = text.str.contains(_INTENTIONAL_WALK)
    is_hbp = text.str.contains(_HIT_BY_PITCH)
    is_bunt = (pl.col("terminal_outcome_status") == "unsupported_bunt") | (
        text.str.contains(_SACRIFICE_BUNT)
    )
    is_contact = pl.col("terminal_outcome_group").is_not_null()
    is_complete = is_contact | is_strikeout | is_walk | is_hbp | is_bunt
    is_special = pl.col("terminal_outcome_status") == "unsupported_special_result"

    return (
        terminal.filter(
            pl.col("batter").is_not_null()
            & pl.col("pitcher").is_not_null()
            & pl.col("fielder_2").is_not_null()
            & is_complete
            & ~is_special
            & ~is_intentional_walk
        )
        .with_columns(
            pl.col("fielder_2").cast(pl.Int64).alias("catcher_id"),
            pl.col("pitcher").cast(pl.Int64).alias("pitcher_id"),
            pl.col("batter").cast(pl.Int64).alias("batter_id"),
            pl.col("p_throws").fill_null("U").alias("pitcher_hand"),
            pl.col("stand").fill_null("U").alias("batter_side"),
            pl.col("park_key").fill_null("unknown_park").alias("park_context"),
            is_strikeout.cast(pl.Int8).alias("strikeout"),
            (is_walk & ~is_intentional_walk).cast(pl.Int8).alias(
                "unintentional_walk"
            ),
            is_hbp.cast(pl.Int8).alias("hit_by_pitch"),
            (
                (is_walk & ~is_intentional_walk) | is_hbp
            ).cast(pl.Int8).alias("control_failure"),
            (pl.col("terminal_outcome_group") == "HR")
            .fill_null(False)
            .cast(pl.Int8)
            .alias("home_run"),
            pl.when(pl.col("terminal_outcome_group") == "HR")
            .then(1.400)
            .when(is_walk & ~is_intentional_walk)
            .then(0.330)
            .when(is_hbp)
            .then(0.345)
            .when(is_strikeout)
            .then(-0.105)
            .when(bb_type == "line_drive")
            .then(0.380)
            .when(bb_type.is_in(["popup", "pop_up"]))
            .then(-0.096)
            .otherwise(0.050)
            .alias("defense_independent_run_value"),
        )
        .select(
            "season",
            "level",
            "game_pk",
            "at_bat_index",
            "catcher_id",
            "pitcher_id",
            "batter_id",
            "pitcher_hand",
            "batter_side",
            "park_context",
            "bb_type",
            "terminal_outcome_group",
            "terminal_outcome_status",
            "control_failure",
            "unintentional_walk",
            "hit_by_pitch",
            "strikeout",
            "home_run",
            "defense_independent_run_value",
        )
    )


def _center_effects(
    effects: pl.DataFrame, *, effect_column: str, opportunity_column: str
) -> pl.DataFrame:
    centers = effects.group_by("season").agg(
        (
            (pl.col(effect_column) * pl.col(opportunity_column)).sum()
            / pl.col(opportunity_column).sum()
        ).alias("season_effect_center")
    )
    return (
        effects.join(centers, on="season", validate="m:1")
        .with_columns(
            (pl.col(effect_column) - pl.col("season_effect_center")).alias(
                effect_column
            )
        )
        .drop("season_effect_center")
    )


def _update_effect(
    cells: pl.DataFrame,
    effects: dict[str, pl.DataFrame],
    *,
    entity: str,
    prior: float,
) -> pl.DataFrame:
    id_column = f"{entity}_id" if entity != "pair" else "pair_id"
    effect_column = f"{entity}_effect"
    opportunity_column = f"{entity}_opportunities"

    joined = cells
    other_effect_columns: list[str] = []
    for other, frame in effects.items():
        if other == entity:
            continue
        other_id = f"{other}_id" if other != "pair" else "pair_id"
        other_effect = f"{other}_effect"
        joined = joined.join(
            frame.select("season", other_id, other_effect),
            on=["season", other_id],
            how="left",
            validate="m:1",
        )
        other_effect_columns.append(other_effect)

    fitted_other = pl.lit(0.0)
    for column in other_effect_columns:
        fitted_other = fitted_other + pl.col(column).fill_null(0.0)

    updated = (
        joined.group_by("season", id_column)
        .agg(
            pl.col("opportunities").sum().alias(opportunity_column),
            (
                pl.col("outcome_sum")
                - pl.col("baseline_sum")
                - pl.col("opportunities") * fitted_other
            )
            .sum()
            .alias("effect_numerator"),
        )
        .with_columns(
            (
                pl.col("effect_numerator")
                / (pl.col(opportunity_column) + float(prior))
            ).alias(effect_column)
        )
        .drop("effect_numerator")
    )
    return _center_effects(
        updated,
        effect_column=effect_column,
        opportunity_column=opportunity_column,
    )


def fit_crossed_battery_effects(
    plate_appearances: pl.DataFrame,
    *,
    outcome_column: str,
    pitcher_prior: float = 400.0,
    batter_prior: float = 400.0,
    catcher_prior: float = 2_000.0,
    pair_prior: float = 1_000.0,
    context_prior: float = 500.0,
    park_prior: float = 1_000.0,
    iterations: int = 8,
) -> BatteryEffectFit:
    """Fit shrunken season effects for pitcher, batter, catcher and battery pair.

    Pair effects are estimated after the three main participant effects.  They
    are intentionally not fed back into the catcher estimate: a recurring pair
    can be useful chemistry without being evidence that the catcher improves
    every pitcher.
    """

    required = {
        "season",
        "level",
        "catcher_id",
        "pitcher_id",
        "batter_id",
        "pitcher_hand",
        "batter_side",
        "park_context",
        outcome_column,
    }
    missing = sorted(required - set(plate_appearances.columns))
    if missing:
        raise ValueError(f"battery plate appearances missing fields: {missing}")
    if min(
        pitcher_prior,
        batter_prior,
        catcher_prior,
        pair_prior,
        context_prior,
        park_prior,
    ) < 0:
        raise ValueError("battery shrinkage priors must be nonnegative")
    if iterations < 1:
        raise ValueError("iterations must be positive")

    work = plate_appearances.select(
        "season",
        "level",
        "catcher_id",
        "pitcher_id",
        "batter_id",
        "pitcher_hand",
        "batter_side",
        "park_context",
        pl.col(outcome_column).cast(pl.Float64).alias("outcome"),
    ).drop_nulls(["outcome"])
    if work.is_empty():
        raise ValueError("no eligible battery plate appearances")

    broad_keys = ["season", "level"]
    matchup_keys = [*broad_keys, "pitcher_hand", "batter_side"]
    park_keys = [*matchup_keys, "park_context"]
    broad = work.group_by(broad_keys).agg(
        pl.col("outcome").sum().alias("broad_sum"),
        pl.len().alias("broad_n"),
    ).with_columns((pl.col("broad_sum") / pl.col("broad_n")).alias("broad_mean"))
    matchup = work.group_by(matchup_keys).agg(
        pl.col("outcome").sum().alias("matchup_sum"),
        pl.len().alias("matchup_n"),
    )
    park = work.group_by(park_keys).agg(
        pl.col("outcome").sum().alias("park_sum"),
        pl.len().alias("park_n"),
    )
    scored = (
        work.join(broad, on=broad_keys, validate="m:1")
        .join(matchup, on=matchup_keys, validate="m:1")
        .join(park, on=park_keys, validate="m:1")
        .with_columns(
            (
                (pl.col("matchup_sum") + context_prior * pl.col("broad_mean"))
                / (pl.col("matchup_n") + context_prior)
            ).alias("matchup_expected")
        )
        .with_columns(
            (
                (pl.col("park_sum") + park_prior * pl.col("matchup_expected"))
                / (pl.col("park_n") + park_prior)
            ).alias("baseline_expected")
        )
        .with_columns(
            pl.concat_str(
                [pl.col("pitcher_id"), pl.col("catcher_id")], separator=":"
            ).alias("pair_id")
        )
    )
    cells = scored.group_by(
        "season", "catcher_id", "pitcher_id", "batter_id", "pair_id"
    ).agg(
        pl.len().alias("opportunities"),
        pl.col("outcome").sum().alias("outcome_sum"),
        pl.col("baseline_expected").sum().alias("baseline_sum"),
    )

    effects: dict[str, pl.DataFrame] = {}
    for entity in ("pitcher", "batter", "catcher"):
        id_column = f"{entity}_id"
        effects[entity] = (
            cells.group_by("season", id_column)
            .agg(pl.col("opportunities").sum().alias(f"{entity}_opportunities"))
            .with_columns(pl.lit(0.0).alias(f"{entity}_effect"))
        )

    priors = {
        "pitcher": float(pitcher_prior),
        "batter": float(batter_prior),
        "catcher": float(catcher_prior),
    }
    for _ in range(iterations):
        for entity in ("pitcher", "batter", "catcher"):
            effects[entity] = _update_effect(
                cells, effects, entity=entity, prior=priors[entity]
            )

    fitted = cells
    for entity in ("pitcher", "batter", "catcher"):
        fitted = fitted.join(
            effects[entity],
            on=["season", f"{entity}_id"],
            validate="m:1",
        )
    fitted = fitted.with_columns(
        (
            pl.col("baseline_sum")
            + pl.col("opportunities")
            * (
                pl.col("pitcher_effect")
                + pl.col("batter_effect")
                + pl.col("catcher_effect")
            )
        ).alias("main_effect_prediction_sum")
    )
    pairs = (
        fitted.group_by("season", "pair_id", "pitcher_id", "catcher_id")
        .agg(
            pl.col("opportunities").sum().alias("pair_opportunities"),
            (
                pl.col("outcome_sum") - pl.col("main_effect_prediction_sum")
            ).sum().alias("pair_numerator"),
        )
        .with_columns(
            (
                pl.col("pair_numerator")
                / (pl.col("pair_opportunities") + float(pair_prior))
            ).alias("pair_effect")
        )
        .drop("pair_numerator")
    )

    catchers = effects["catcher"].select(
        "season",
        pl.col("catcher_id").alias("player_id"),
        pl.col("catcher_opportunities").alias("opportunities"),
        pl.col("catcher_effect").alias("effect"),
    )
    pitchers = effects["pitcher"].select(
        "season",
        pl.col("pitcher_id").alias("player_id"),
        pl.col("pitcher_opportunities").alias("opportunities"),
        pl.col("pitcher_effect").alias("effect"),
    )
    batters = effects["batter"].select(
        "season",
        pl.col("batter_id").alias("player_id"),
        pl.col("batter_opportunities").alias("opportunities"),
        pl.col("batter_effect").alias("effect"),
    )
    return BatteryEffectFit(
        catchers=catchers.sort("season", "player_id"),
        pitchers=pitchers.sort("season", "player_id"),
        batters=batters.sort("season", "player_id"),
        pairs=pairs.sort("season", "pair_id"),
        cells=fitted,
    )
