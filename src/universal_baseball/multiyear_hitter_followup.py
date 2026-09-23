"""Cutoff-safe opportunity and rolling interval helpers for the frozen v2 test."""
from __future__ import annotations

import numpy as np
import polars as pl

from universal_baseball.multiyear_hitter_value import training_mask


def opportunity_mask(panel, cutoff, horizon):
    origin = panel["origin_year"].to_numpy()
    return (training_mask(panel, cutoff, horizon)
            & panel["established"].to_numpy()
            & ~((origin < 2020) & (origin + horizon >= 2020)))


def upper_quantile(values, coverage=.8):
    """Finite-sample empirical correction; no exchangeability guarantee claimed."""
    values = np.sort(np.asarray(values, dtype=float))
    if not len(values) or not np.isfinite(values).all():
        raise ValueError("Correction needs finite calibration errors")
    rank = min(len(values), int(np.ceil((len(values) + 1) * coverage)))
    return float(values[rank - 1])


def interval_score(y, lo, hi):
    y, lo, hi = (np.asarray(a, dtype=float) for a in (y, lo, hi))
    if np.any(lo > hi):
        raise ValueError("Crossed interval")
    return hi - lo + 10 * (np.maximum(lo - y, 0) + np.maximum(y - hi, 0))


def calibrate(history, current, cutoff, horizon, minimum=100):
    """Calibrate raw OOF endpoints using only fully mature earlier origins.

    Latest five origins are selected before stage slicing. Q0 is the original
    stage-residual recipe (all mature origins, >=200 rows); Q2 is the frozen
    rolling quantile correction. Missing support remains null, never zero.
    """
    mature = history.filter((pl.col("origin_year") < cutoff)
                            & (pl.col("origin_year") + horizon <= cutoff)
                            & pl.col("actual").is_not_null())
    years = sorted(mature["origin_year"].unique().to_list())[-5:]
    pool = mature.filter(pl.col("origin_year").is_in(years))
    output = []
    for stage in sorted(current["stage"].unique()):
        sub = current.filter(pl.col("stage") == stage)
        prior = pool.filter(pl.col("stage") == stage)
        baseline = mature.filter(pl.col("stage") == stage)
        threshold = float(np.quantile(prior["mean"], .8)) if prior.height else None
        top = float(np.quantile(sub["mean"], .8))
        q0 = [None, None]
        if baseline.height >= 200 and baseline["origin_year"].n_unique() >= 2:
            q0 = np.quantile((baseline["actual"] - baseline["mean"]).to_numpy(), [.1, .9]).tolist()
        for high in (False, True):
            if threshold is None:
                group = sub if not high else sub.head(0)
            else:
                group = sub.filter((pl.col("mean") >= threshold) == high)
            if group.is_empty():
                continue
            bucket = prior.filter((pl.col("mean") >= threshold) == high) if threshold is not None else prior
            fallback = bucket.height < minimum or bucket["origin_year"].n_unique() < 2
            if fallback:
                bucket = prior
            correction = None
            if bucket.height >= minimum and bucket["origin_year"].n_unique() >= 2:
                correction = upper_quantile(np.maximum.reduce([
                    (bucket["raw_lo"] - bucket["actual"]).to_numpy(),
                    (bucket["actual"] - bucket["raw_hi"]).to_numpy(), np.zeros(bucket.height)]))
            output.append(group.with_columns(
                (pl.col("mean") + pl.lit(q0[0], dtype=pl.Float64)).alias("q0_lo"),
                (pl.col("mean") + pl.lit(q0[1], dtype=pl.Float64)).alias("q0_hi"),
                (pl.col("raw_lo") - pl.lit(correction, dtype=pl.Float64)).alias("q2_lo"),
                (pl.col("raw_hi") + pl.lit(correction, dtype=pl.Float64)).alias("q2_hi"),
                pl.lit(correction, dtype=pl.Float64).alias("correction"),
                pl.lit(threshold, dtype=pl.Float64).alias("prior_threshold"),
                pl.lit(high).alias("high_prior"), (pl.col("mean") >= top).alias("high_current"),
                pl.lit(fallback).alias("stage_fallback"), pl.lit(bucket.height).alias("calibration_rows"),
                pl.lit(bucket["origin_year"].n_unique()).alias("calibration_origins"),
                pl.lit(max(years) if years else None, dtype=pl.Int64).alias("latest_calibration_origin")))
    return pl.concat(output).sort("player_id")


def compare_losses(frame, candidate, baseline, draws=1000):
    """Equal-origin loss difference, resampling whole player histories."""
    ids, inverse = np.unique(frame["player_id"].to_numpy(), return_inverse=True)
    origins = sorted(frame["origin_year"].unique())
    delta = np.zeros((len(ids), len(origins)))
    count = np.zeros_like(delta)
    a, b = frame[candidate].to_numpy(), frame[baseline].to_numpy()
    folds = []
    for j, year in enumerate(origins):
        use = frame["origin_year"].to_numpy() == year
        np.add.at(delta[:, j], inverse[use], a[use] - b[use])
        np.add.at(count[:, j], inverse[use], 1)
        folds.append({"origin": int(year), "candidate": float(a[use].mean()),
                      "baseline": float(b[use].mean()), "delta": float((a[use]-b[use]).mean())})
    rng = np.random.default_rng(417)
    boot = []
    for _ in range(draws):
        ix = rng.integers(0, len(ids), len(ids))
        n = count[ix].sum(axis=0)
        if np.all(n > 0):
            boot.append(float(np.mean(delta[ix].sum(axis=0) / n)))
    return {"candidate": float(np.mean([r["candidate"] for r in folds])),
            "baseline": float(np.mean([r["baseline"] for r in folds])),
            "delta": float(np.mean([r["delta"] for r in folds])),
            "interval95": np.quantile(boot, [.025, .975]).tolist(), "folds": folds,
            "improving_origins": sum(r["delta"] < 0 for r in folds)}
