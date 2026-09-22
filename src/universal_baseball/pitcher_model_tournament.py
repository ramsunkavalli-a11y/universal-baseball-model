"""Adapters for the clean-slate pitcher value model tournament."""

from __future__ import annotations

import polars as pl

from universal_baseball.hitter_model_tournament import run_engine_fold
from universal_baseball.hitter_target_architecture import Fold, feature_columns


PITCHER_TARGET_COLUMNS = {
    "target_mlb_bf",
    "target_mlb_active",
    "target_conditional_component_war_per_800",
    "target_component_war",
    "target_season",
}


def to_generic_two_part_panel(panel: pl.DataFrame) -> pl.DataFrame:
    """Map pitcher target names onto the tested generic two-part architecture."""

    required = {
        "origin_year",
        "target_season",
        "player_id",
        *PITCHER_TARGET_COLUMNS,
    }
    if missing := sorted(required - set(panel.columns)):
        raise ValueError(f"pitcher panel missing fields: {missing}")
    generic = panel.rename(
        {
            "target_mlb_bf": "target_mlb_pa",
            "target_conditional_component_war_per_800": (
                "target_conditional_component_war_per_600"
            ),
        }
    )
    leaked = [
        column for column in feature_columns(generic) if column.startswith("target_")
    ]
    if leaked:
        raise ValueError(f"pitcher target leakage: {leaked}")
    return generic


def run_pitcher_engine_fold(
    panel: pl.DataFrame,
    fold: Fold,
    engine: str,
    *,
    random_state: int = 417,
    variant: str = "balanced",
) -> tuple[pl.DataFrame, dict[str, dict[str, float]]]:
    """Run one pitcher engine using the common two-part value architecture."""

    return run_engine_fold(
        to_generic_two_part_panel(panel),
        fold,
        engine,
        random_state=random_state,
        variant=variant,
    )
