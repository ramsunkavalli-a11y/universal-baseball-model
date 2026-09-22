"""Reuse frozen hitter context estimators at later forecast cutoffs.

The Stage 2d implementation is hash-bound by an older scientific contract and
must remain byte-for-byte unchanged.  These adapters translate the season axis
before calling that implementation, then restore the real seasons.  Shifting
every season by the same amount preserves ordering, gaps, and recency weights.
"""

from __future__ import annotations

import polars as pl

from universal_baseball.hitter_v2_stage2d import (
    build_prior_pitcher_binary_feature,
    build_prior_pitcher_hit_composition_features,
)


FROZEN_PROTECTED_SEASON = 2025


def _rebase(
    frame: pl.DataFrame, *, protected_season: int
) -> tuple[pl.DataFrame, int]:
    if protected_season < FROZEN_PROTECTED_SEASON:
        raise ValueError("protected season cannot precede the frozen boundary")
    if frame.filter(pl.col("season") >= protected_season).height:
        raise ValueError(f"context input contains protected season {protected_season}")
    offset = protected_season - FROZEN_PROTECTED_SEASON
    return frame.with_columns((pl.col("season") - offset).alias("season")), offset


def build_postfreeze_prior_pitcher_binary_feature(
    frame: pl.DataFrame,
    node_name: str,
    *,
    protected_season: int,
) -> pl.DataFrame:
    """Apply the frozen binary estimator without editing its locked source."""

    rebased, offset = _rebase(frame, protected_season=protected_season)
    result = build_prior_pitcher_binary_feature(rebased, node_name)
    return result.with_columns((pl.col("season") + offset).alias("season"))


def build_postfreeze_prior_pitcher_hit_composition_features(
    frame: pl.DataFrame,
    *,
    protected_season: int,
) -> pl.DataFrame:
    """Apply the frozen hit-composition estimator at a later cutoff."""

    rebased, offset = _rebase(frame, protected_season=protected_season)
    result = build_prior_pitcher_hit_composition_features(rebased)
    return result.with_columns((pl.col("season") + offset).alias("season"))
