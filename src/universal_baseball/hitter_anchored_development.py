"""Conditional performance anchors and strictly vintage-matched later labels."""
import numpy as np
import polars as pl


EXTRA_FEATURES = ["performance_anchor","anchor_age","anchor_mlb_workload","age_mlb_workload"]


def normalized_pa_weights(pa):
    pa=np.asarray(pa,dtype=float)
    if not len(pa) or not np.isfinite(pa).all() or np.any(pa<=0):
        raise ValueError("Rate fitting requires positive, finite PA")
    return pa/pa.mean()


def active_rate_rows(panel,cutoff,horizon):
    if cutoff>2025 or horizon not in (1,2):
        raise ValueError("Unsupported cutoff/horizon")
    return panel.filter((pl.col("origin_year")+horizon<=cutoff)
        & (pl.col(f"pa_h{horizon}")>0) & pl.col(f"war_h{horizon}").is_not_null()).with_columns(
            (pl.col(f"war_h{horizon}")*600/pl.col(f"pa_h{horizon}")).alias("actual_rate"))


def attach_anchors(panel,anchors):
    if anchors.filter(pl.col("anchor_cutoff")!=pl.col("origin_year")).height:
        raise ValueError("Anchor was not produced at its own origin")
    if anchors.filter(pl.col("latest_anchor_target")>pl.col("anchor_cutoff")).height:
        raise ValueError("Anchor uses future outcomes")
    result=panel.join(anchors,on=["origin_year","player_id"],how="inner",validate="1:1",maintain_order="left")
    if result["performance_anchor"].null_count():
        raise ValueError("Missing anchor")
    return result.with_columns(
        (pl.col("performance_anchor")*pl.col("age_centered")).alias("anchor_age"),
        (pl.col("performance_anchor")*pl.col("log_mlb_pa_lag0")).alias("anchor_mlb_workload"),
        (pl.col("age_centered")*pl.col("log_mlb_pa_lag0")).alias("age_mlb_workload"))


def later_training(panel,cutoff):
    if cutoff>2025:raise ValueError("Protected cutoff")
    return panel.filter((pl.col("origin_year")>=2012)&(pl.col("origin_year")+2<=cutoff)
        & pl.col("war_h2").is_not_null() & pl.col("pa_h2").is_not_null())


def weighted_rate_mse(pa,actual,predicted):
    weights=normalized_pa_weights(pa)
    return float(np.average((np.asarray(predicted)-np.asarray(actual))**2,weights=weights))
