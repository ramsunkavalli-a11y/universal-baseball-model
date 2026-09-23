"""Bounded cutoff-safe league PA allocation, not a delivered model."""
from __future__ import annotations

import numpy as np
import polars as pl

KEYS = ["origin_year", "player_id"]


def ordinary_origin(year):
    return not (year <= 2020 <= year + 2)


def grouped(frame):
    pa = frame["pa_00"].to_numpy()
    if not np.isfinite(pa).all() or np.any(pa < 0):
        raise ValueError("Invalid baseline PA")
    band = np.searchsorted([50, 200, 400], pa, side="right")
    return frame.with_columns(pl.Series("allocation_group", [
        f"{stage}|{int(b)}" for stage, b in zip(frame["stage"], band, strict=True)]))


def calibration(history, cutoff):
    prior = history.filter(pl.col("origin_year") + 2 <= cutoff)
    prior = prior.filter(pl.col("origin_year").is_in([
        y for y in prior["origin_year"].unique() if ordinary_origin(y)]))
    prior = grouped(prior).sort(KEYS)
    records = []
    for name in sorted(prior["allocation_group"].unique()):
        f = prior.filter(pl.col("allocation_group") == name)
        predicted, actual = float(f["pa_00"].sum()), float(f["pa_h2"].sum())
        pseudo = 100 * predicted / f.height
        raw = (actual + pseudo) / (predicted + pseudo) if predicted > 0 else 1.
        records.append({"allocation_group": name, "rows": f.height,
            "origins": sorted(f["origin_year"].unique().to_list()),
            "predicted_pa": predicted, "actual_pa": actual,
            "multiplier": float(np.clip(raw, .5, 2.))})
    return records


def budget_at_cutoff(panel, targets, schedules, cutoff):
    if cutoff > 2025:
        raise ValueError("Protected cutoff")
    # Slice before every aggregation: future actuals cannot enter pool or reserve.
    known = targets.filter(pl.col("season") <= cutoff)
    annual = known.group_by("season").agg(pl.col("mlb_pa").sum()).sort("season")
    years = [y for y in annual["season"] if y != 2020][-3:]
    if len(years) != 3:
        raise ValueError("Insufficient known league pool")
    schedule = {r["season"]: 2*r["completed_games"]/(162*r["teams"])
                for r in schedules.filter(pl.col("season").is_in(years)).iter_rows(named=True)}
    totals = dict(zip(annual["season"], annual["mlb_pa"], strict=True))
    pool = float(np.median([totals[y]/schedule[y] for y in years]))
    origins = sorted(y for y in panel["origin_year"].unique()
                     if y+2 <= cutoff and y+2 in totals and ordinary_origin(y))[-5:]
    if not origins:
        raise ValueError("No mature outsider reserve cohorts")
    reserve_rows = []
    for y in origins:
        cohort = panel.filter(pl.col("origin_year") == y).select("player_id")
        if cohort.unique().height != cohort.height:
            raise ValueError("Duplicate cohort player")
        outsiders = known.filter(pl.col("season") == y+2).join(cohort, on="player_id", how="anti")
        pa = float(outsiders["mlb_pa"].sum())
        reserve_rows.append({"origin": y, "target": y+2, "outside_pa": pa,
                             "fraction": pa/totals[y+2]})
    fraction = float(np.median([r["fraction"] for r in reserve_rows]))
    return {"pool_years": years, "pool": pool, "reserve_fraction": fraction,
            "reserve_pa": pool*fraction, "named_budget": pool*(1-fraction),
            "reserve_support": reserve_rows}


def capped_allocation(weights, probability, budget):
    weights, probability = np.asarray(weights, float), np.asarray(probability, float)
    if (weights.shape != probability.shape or weights.ndim != 1
            or not np.isfinite(weights).all() or not np.isfinite(probability).all()
            or np.any(weights < 0) or np.any((probability < 0) | (probability > 1))
            or not np.isfinite(budget) or budget < 0):
        raise ValueError("Invalid allocation inputs")
    cap = probability * 800
    out = np.zeros_like(weights)
    remaining = (weights > 0) & (cap > 0)
    while remaining.any():
        available = max(0., budget-float(out.sum()))
        indices = np.flatnonzero(remaining)
        proposed = weights[indices]/weights[indices].sum()*available
        hit = proposed >= cap[indices]
        if not hit.any():
            out[indices] = proposed
            break
        out[indices[hit]] = cap[indices[hit]]
        remaining[indices[hit]] = False
    return out


def allocate(test, records, budget):
    f = grouped(test).sort(KEYS)
    mapping = {r["allocation_group"]: r["multiplier"] for r in records}
    multipliers = np.array([mapping.get(g, 1.) for g in f["allocation_group"]])
    baseline = f["pa_00"].to_numpy()
    candidate = capped_allocation(baseline*multipliers, f["old_p"], budget)
    uniform = capped_allocation(baseline, f["old_p"], budget)
    return f.with_columns(pl.Series("allocation_multiplier", multipliers),
        pl.Series("candidate_pa", candidate), pl.Series("uniform_pa", uniform),
        pl.col("pa_00").alias("baseline_pa"))


def losses(frame):
    out = frame
    for form in ("baseline", "uniform", "candidate"):
        out = out.with_columns(
            (pl.col(form+"_pa") - pl.col("pa_h2")).alias(form+"_error"),
            (pl.col(form+"_pa") * pl.col("performance_anchor")/600).alias(form+"_value"))
        out = out.with_columns(pl.col(form+"_error").pow(2).alias(form+"_pa_loss"),
            pl.col(form+"_error").abs().alias(form+"_pa_mae"),
            (pl.col(form+"_value")-pl.col("war_h2")).pow(2).alias(form+"_value_loss"))
    return out.with_columns((pl.col("reference_h2")-pl.col("war_h2")).pow(2).alias("direct_value_loss"))
