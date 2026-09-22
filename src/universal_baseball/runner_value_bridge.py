"""Chronology-safe candidates joining MiLB RE24 and MLB runner evidence."""

from __future__ import annotations

from collections.abc import Sequence

import polars as pl


BLEND_WEIGHTS = (0.25, 0.50, 0.75, 1.00)


def candidate_columns() -> tuple[str, ...]:
    return (
        "prediction_advancement_war",
        *(f"prediction_advancement_blend_all_{int(weight * 100)}" for weight in BLEND_WEIGHTS),
        *(f"prediction_advancement_fallback_{int(weight * 100)}" for weight in BLEND_WEIGHTS),
    )


def build_runner_bridge_candidates(
    base: pl.DataFrame,
    milb_projection: pl.DataFrame,
    *,
    advancement_opportunities_per_pa: float,
    runs_per_win: float,
) -> pl.DataFrame:
    """Create conservative blends of existing MLB and prior MiLB runner forecasts."""

    required = {
        "target_season",
        "player_id",
        "prediction_candidate_expected_pa",
        "prediction_advancement_war",
        "baserunning_evidence_tier",
    }
    if missing := sorted(required - set(base.columns)):
        raise ValueError(f"hitter value rows missing runner bridge fields: {missing}")
    if advancement_opportunities_per_pa <= 0 or runs_per_win <= 0:
        raise ValueError("runner bridge scales must be positive")
    required_milb = {"target_season", "player_id", "projected_effect"}
    if missing := sorted(required_milb - set(milb_projection.columns)):
        raise ValueError(f"MiLB runner projection missing fields: {missing}")
    joined = base.join(
        milb_projection.select(*required_milb).rename(
            {"projected_effect": "milb_projected_advancement_runs_per_opportunity"}
        ),
        on=["target_season", "player_id"],
        how="left",
        validate="1:1",
    ).with_columns(
        (
            pl.col("prediction_candidate_expected_pa")
            * advancement_opportunities_per_pa
            * pl.col("milb_projected_advancement_runs_per_opportunity")
            / runs_per_win
        ).alias("prediction_milb_advancement_war"),
        pl.col("baserunning_evidence_tier")
        .is_in(["steal_and_advancement", "advancement_only"])
        .alias("has_mlb_advancement_evidence"),
    )
    expressions: list[pl.Expr] = []
    for weight in BLEND_WEIGHTS:
        suffix = int(weight * 100)
        blended = (
            pl.col("prediction_advancement_war")
            + weight
            * (
                pl.col("prediction_milb_advancement_war")
                - pl.col("prediction_advancement_war")
            )
        )
        expressions.extend(
            [
                pl.when(pl.col("prediction_milb_advancement_war").is_not_null())
                .then(blended)
                .otherwise(pl.col("prediction_advancement_war"))
                .alias(f"prediction_advancement_blend_all_{suffix}"),
                pl.when(
                    pl.col("prediction_milb_advancement_war").is_not_null()
                    & ~pl.col("has_mlb_advancement_evidence")
                )
                .then(blended)
                .otherwise(pl.col("prediction_advancement_war"))
                .alias(f"prediction_advancement_fallback_{suffix}"),
            ]
        )
    return joined.with_columns(*expressions)


def select_from_prior_targets(
    frame: pl.DataFrame,
    *,
    target_season: int,
    candidates: Sequence[str] | None = None,
) -> tuple[str, int, float | None]:
    """Select advancement candidate using only earlier MLB target seasons."""

    choices = tuple(candidates or candidate_columns())
    required = {"target_season", "later_advancement_war", *choices}
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"runner bridge selection missing fields: {missing}")
    history = frame.filter(pl.col("target_season") < target_season)
    if history.is_empty():
        return "prediction_advancement_war", 0, None
    scored = [
        (
            float(
                (
                    history[column] - history["later_advancement_war"]
                ).pow(2).sum()
            ),
            index,
            column,
        )
        for index, column in enumerate(choices)
    ]
    sse, _, selected = min(scored)
    return selected, history.height, sse
