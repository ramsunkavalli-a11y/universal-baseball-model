"""Pair frozen Baseline 2 and the richer EV/LA challenger for existing scoring.

The Current Talent scoring engine intentionally stays generic and pair-oriented:
it expects temporary ``baseline0`` / ``baseline1`` latent probability columns.
This adapter maps frozen B2 -> temporary baseline0 and B2+richer -> temporary
baseline1 without changing the scorer itself.

Primary richer development scoring is restricted to players for whom the richer
adjustment was actually applied. B2 fallback players remain part of the universal
production surface but are not allowed to dilute or inflate the paired incremental
value test.
"""

from __future__ import annotations

import polars as pl

from universal_baseball.performance_season import ALL_CORE_BINS


SCORING_COMPARATOR_LABEL = "baseline2"
SCORING_CHALLENGER_LABEL = "batted_ball_richer"


def build_baseline2_vs_richer_scoring_pair(
    richer_profile: pl.DataFrame,
    *,
    richer_eligible_only: bool = True,
    probability_tolerance: float = 1e-12,
) -> pl.DataFrame:
    """Return the temporary two-model latent surface required by the scorer.

    Input must be the deterministic output of
    ``apply_batted_ball_quality_residual``. When ``richer_eligible_only`` is true,
    only players with the richer adjustment applied on their entire 12-bin profile
    are retained. Mixed per-player application flags fail closed.
    """

    if probability_tolerance < 0:
        raise ValueError("probability tolerance must be nonnegative")
    required = {
        "player_id",
        "core_bin",
        "baseline2_latent_probability",
        "richer_latent_probability",
        "richer_adjustment_applied",
    }
    missing = sorted(required - set(richer_profile.columns))
    if missing:
        raise ValueError(f"richer Current Talent profile missing fields: {missing}")

    duplicate = richer_profile.group_by(["player_id", "core_bin"]).len().filter(
        pl.col("len") != 1
    )
    if not duplicate.is_empty():
        raise ValueError("richer Current Talent profile violates player_id + core_bin grain")

    player_flags = richer_profile.group_by("player_id").agg(
        pl.col("richer_adjustment_applied").n_unique().alias("_flag_count"),
        pl.col("richer_adjustment_applied").first().alias("_applied"),
        pl.col("core_bin").n_unique().alias("_bin_count"),
    )
    if player_flags.filter(pl.col("_flag_count") != 1).height:
        raise ValueError("richer adjustment application is inconsistent within a player profile")
    if player_flags.filter(pl.col("_bin_count") != len(ALL_CORE_BINS)).height:
        raise ValueError("richer Current Talent player profile does not contain all core bins")

    working = richer_profile
    if richer_eligible_only:
        eligible_ids = player_flags.filter(pl.col("_applied")).select("player_id")
        working = working.join(eligible_ids, on="player_id", how="inner")
    if working.is_empty():
        return pl.DataFrame(
            schema={
                "player_id": pl.Int64,
                "core_bin": pl.String,
                "baseline0_latent_probability": pl.Float64,
                "baseline1_latent_probability": pl.Float64,
            }
        )

    observed_bins = set(str(value) for value in working.get_column("core_bin").unique().to_list())
    if observed_bins != set(ALL_CORE_BINS):
        raise ValueError("paired richer scoring surface does not contain the frozen 12-bin vocabulary")

    result = (
        working.select(
            pl.col("player_id").cast(pl.Int64),
            pl.col("core_bin").cast(pl.String),
            pl.col("baseline2_latent_probability")
            .cast(pl.Float64)
            .alias("baseline0_latent_probability"),
            pl.col("richer_latent_probability")
            .cast(pl.Float64)
            .alias("baseline1_latent_probability"),
        )
        .sort(["player_id", "core_bin"])
    )

    sums = result.group_by("player_id").agg(
        pl.col("baseline0_latent_probability").sum().alias("_b2_sum"),
        pl.col("baseline1_latent_probability").sum().alias("_richer_sum"),
        pl.col("core_bin").n_unique().alias("_bin_count"),
    )
    if sums.filter(
        (pl.col("_bin_count") != len(ALL_CORE_BINS))
        | ((pl.col("_b2_sum") - 1.0).abs() > probability_tolerance)
        | ((pl.col("_richer_sum") - 1.0).abs() > probability_tolerance)
    ).height:
        raise ValueError("paired B2/richer latent profiles are incomplete or not normalized")
    return result


def relabel_richer_pair_model(model: str) -> str:
    """Map scorer pair labels to stable B2/richer comparison names idempotently."""

    mapping = {
        "baseline0": SCORING_COMPARATOR_LABEL,
        "baseline1": SCORING_CHALLENGER_LABEL,
        SCORING_COMPARATOR_LABEL: SCORING_COMPARATOR_LABEL,
        SCORING_CHALLENGER_LABEL: SCORING_CHALLENGER_LABEL,
    }
    try:
        return mapping[str(model)]
    except KeyError as exc:
        raise ValueError(f"unsupported B2/richer scoring label: {model}") from exc
