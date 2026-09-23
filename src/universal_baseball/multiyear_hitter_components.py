"""Small, cutoff-safe helpers for the predeclared multi-year component test."""
from __future__ import annotations

import numpy as np
import polars as pl
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

COMPONENTS = ("position", "steals", "advancement", "general", "framing", "throwing", "blocking")
START = dict(position=2009, steals=2009, advancement=2016, general=2016,
             framing=2016, throwing=2016, blocking=2018)


def pandemic(origin, horizon):
    return (origin < 2020) & (origin + horizon >= 2020)


def mature_mask(frame, cutoff, horizon, component):
    if cutoff > 2025 or horizon not in (1, 2, 3):
        raise ValueError("Invalid cutoff/horizon")
    year = frame["origin_year"].to_numpy()
    y = frame[f"{component}_h{horizon}"].to_numpy()
    return ((year + horizon <= cutoff) & (year + horizon >= START[component])
            & ~pandemic(year, horizon) & np.isfinite(y))


def component_ridge():
    return make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True),
                         StandardScaler(), Ridge(alpha=100.0))


def choose_component(history, cutoff, horizon, component):
    """No current-fold outcomes or immature paths can select their own model."""
    fallback = "benchmark" if component in ("position", "steals", "advancement") else "neutral"
    if history.is_empty():
        return fallback, {"reason": "no_mature_oof", "origins": []}
    f = history.filter((pl.col("component") == component) & (pl.col("horizon") == horizon)
        & (pl.col("origin_year") + horizon <= cutoff) & (pl.col("origin_year") < cutoff)
        & ~pl.col("pandemic") & pl.col("actual").is_not_null())
    if "batting" in f.columns:
        # Extra 2023/24 diagnostics use a different PA proxy and cannot select a
        # model for the unchanged delivered-workload integration.
        f = f.filter(pl.col("batting").is_not_null())
    years = sorted(f["origin_year"].unique().to_list())
    if len(years) < 2 or f.height < 100:
        return fallback, {"reason": "insufficient_mature_oof", "origins": years}
    scores = {k: float(f.with_columns(((pl.col(k)-pl.col("actual"))**2).alias("loss"))
                       .group_by("origin_year").agg(pl.col("loss").mean())["loss"].mean())
              for k in ("neutral", "benchmark", "direct")}
    return min(scores, key=scores.get), {"reason": "earlier_oof_mse", "origins": years, "mse": scores}


def historical_rate(runs, pa, available, weights=(1.0, .5, .25)):
    """Runs/600 PA: absent component years do not become zero observations."""
    w = np.asarray(weights) * np.asarray(available, dtype=float)
    return 600 * np.nansum(np.asarray(runs)*w, axis=-1) / (600 + np.nansum(np.asarray(pa)*w, axis=-1))


def attach_labels(panel, annual):
    if annual["season"].max() > 2025 or panel["origin_year"].max() > 2025:
        raise ValueError("Protected season")
    if annual.unique(["season", "player_id"]).height != annual.height:
        raise ValueError("Duplicate annual identity")
    result = panel
    for h in (1, 2, 3):
        result = result.join(annual.select((pl.col("season")-h).alias("origin_year"), "player_id",
            pl.lit(True).alias("label_present"), *[pl.col(c).alias(f"{c}_h{h}") for c in COMPONENTS]),
            on=["origin_year", "player_id"], how="left", validate="1:1", maintain_order="left")
        # Missing player in a complete season is a known nonparticipant; a present
        # row with a missing measurement must stay unknown.
        result = result.with_columns(*[
            pl.when((pl.col("origin_year")+h >= START[c]) & (pl.col("origin_year")+h <= 2025))
            .then(pl.when(pl.col("label_present").is_null()).then(0.0).otherwise(pl.col(f"{c}_h{h}")))
            .otherwise(None).alias(f"{c}_h{h}") for c in COMPONENTS]).drop("label_present")
    return result
