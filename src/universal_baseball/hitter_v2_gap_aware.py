"""Gap-aware historical inputs for the Hitter v2 G0 outcome core."""

from __future__ import annotations

import polars as pl

from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES


MODEL_HISTORY_COLUMNS = (
    "season",
    "league_id",
    "player_id",
    "level_group",
    *HITTER_TALENT_OUTCOMES,
    "hitter_talent_pa",
)


def assemble_gap_aware_history(
    base_history: pl.DataFrame,
    milb_2019: pl.DataFrame,
    mlb_2019_2020: pl.DataFrame,
    *,
    predictor_cutoff_season: int,
) -> pl.DataFrame:
    """Append accepted old outcomes without constructing a 2020 MiLB season."""

    frames = []
    for label, source in (
        ("BASE", base_history),
        ("MILB_2019", milb_2019),
        ("MLB_2019_2020", mlb_2019_2020),
    ):
        missing = sorted(set(MODEL_HISTORY_COLUMNS) - set(source.columns))
        if missing:
            raise ValueError(f"{label} history missing model columns: {missing}")
        eligible = source
        if "modeling_eligible" in source.columns:
            eligible = source.filter(pl.col("modeling_eligible"))
        frames.append(
            eligible.select(*MODEL_HISTORY_COLUMNS).with_columns(
                pl.lit(label).alias("history_source")
            )
        )
    combined = pl.concat(frames, how="vertical_relaxed").filter(
        pl.col("season") <= predictor_cutoff_season
    )
    if combined.filter(
        (pl.col("season") == 2020) & (pl.col("level_group") != "MLB")
    ).height:
        raise ValueError("gap-aware history cannot construct 2020 MiLB evidence")
    if combined.filter(pl.col("hitter_talent_pa") < 0).height:
        raise ValueError("gap-aware history contains negative evidence")
    if combined.filter(
        pl.sum_horizontal(*HITTER_TALENT_OUTCOMES)
        != pl.col("hitter_talent_pa")
    ).height:
        raise ValueError("gap-aware history has non-exhaustive talent outcomes")
    return combined.sort(
        "season", "league_id", "player_id", "level_group", "history_source"
    )
