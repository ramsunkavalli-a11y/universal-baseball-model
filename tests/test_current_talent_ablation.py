from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.current_talent_ablation import (
    ZERO_TRANSLATION_METHOD,
    zero_translation_offsets,
)
from universal_baseball.performance_season import ALL_CORE_BINS


def _fitted_offsets() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for level, scale in (("MLB", 0.0), ("AAA", 0.2)):
        for index, core_bin in enumerate(ALL_CORE_BINS):
            # Sum to zero within AAA while retaining nonzero fitted effects.
            effect = 0.0
            if level == "AAA":
                effect = scale if index == 0 else -scale if index == 1 else 0.0
            rows.append(
                {
                    "level_group": level,
                    "core_bin": core_bin,
                    "clr_environment_effect": effect,
                    "anchor_level_group": "MLB",
                    "matched_pair_count": 10,
                    "matched_pair_weight": 50.0,
                    "graph_distance_to_anchor": 0 if level == "MLB" else 1,
                    "weighted_fit_residual_rmse": 0.4,
                    "estimator_method": "matched_adjacent_stint_clr_wls_v1",
                }
            )
    return pl.DataFrame(rows)


def test_zero_translation_ablation_only_zeros_applied_effect() -> None:
    fitted = _fitted_offsets()
    zero = zero_translation_offsets(fitted)

    assert zero.height == fitted.height
    assert zero.get_column("clr_environment_effect").abs().sum() == pytest.approx(0.0)
    assert zero.get_column("fitted_clr_environment_effect").to_list() == pytest.approx(
        fitted.get_column("clr_environment_effect").to_list()
    )
    assert zero.get_column("matched_pair_count").to_list() == fitted.get_column(
        "matched_pair_count"
    ).to_list()
    assert zero.get_column("ablation_method").unique().to_list() == [
        ZERO_TRANSLATION_METHOD
    ]


def test_zero_translation_ablation_requires_complete_core_profile() -> None:
    fitted = _fitted_offsets().filter(pl.col("core_bin") != ALL_CORE_BINS[-1])
    with pytest.raises(ValueError, match="complete core profile"):
        zero_translation_offsets(fitted)


def test_zero_translation_ablation_requires_mlb_anchor() -> None:
    fitted = _fitted_offsets().with_columns(
        pl.lit("AAA").alias("anchor_level_group")
    )
    with pytest.raises(ValueError, match="MLB reporting anchor"):
        zero_translation_offsets(fitted)
