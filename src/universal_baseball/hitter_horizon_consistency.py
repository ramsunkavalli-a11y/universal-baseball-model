"""Cutoff-safe target adaptation for the fixed hitter horizon comparison."""
import numpy as np
import polars as pl

from universal_baseball.hitter_target_architecture import TARGET_COLUMNS


def horizon_training(rich, panel, cutoff, horizon):
    if horizon not in (1,2,3) or cutoff>2025:
        raise ValueError("Unsupported horizon or protected cutoff")
    # Discard every old target, not just WAR: activity and PA must belong to
    # the same future calendar year as the new value label.
    inputs = rich.drop([c for c in rich.columns if c in TARGET_COLUMNS])
    inputs = inputs.filter(pl.col("origin_year")+horizon<=cutoff)
    labels = panel.filter((pl.col("origin_year")+horizon<=cutoff)
        & pl.col(f"war_h{horizon}").is_not_null() & pl.col(f"pa_h{horizon}").is_not_null()).select(
            "origin_year","player_id",pl.col(f"war_h{horizon}").alias("target_component_war"),
            pl.col(f"pa_h{horizon}").alias("target_mlb_pa"))
    result = inputs.join(labels,on=["origin_year","player_id"],how="inner",validate="1:1",maintain_order="left")
    return result.with_columns((pl.col("origin_year")+horizon).alias("target_season"),
        (pl.col("target_mlb_pa")>0).cast(pl.Int8).alias("target_mlb_active"),
        pl.when(pl.col("target_mlb_pa")>0).then(pl.col("target_component_war")*600/pl.col("target_mlb_pa"))
          .otherwise(0.).alias("target_conditional_component_war_per_600"))


def fixed_groups(frame):
    """Membership depends only on baseline forecasts and cutoff features."""
    stage, age = frame["stage"].to_numpy(),frame["age"].to_numpy()
    groups = {s: stage==s for s in sorted(frame["stage"].unique())}
    groups.update({"MLB under26":(stage=="Current MLB")&(age<26),
                   "MLB 26to29":(stage=="Current MLB")&(age>=26)&(age<30),
                   "MLB 30plus":(stage=="Current MLB")&(age>=30)})
    top = np.zeros(frame.height,dtype=bool)
    for year in frame["origin_year"].unique():
        ix = np.flatnonzero(frame["origin_year"].to_numpy()==year)
        order = np.lexsort((frame["player_id"].to_numpy()[ix],-frame["reference_h1"].to_numpy()[ix]))
        top[ix[order[:50]]] = True
    groups["Top50"] = top
    groups["Top50 under26"] = top&(age<26)
    return groups
