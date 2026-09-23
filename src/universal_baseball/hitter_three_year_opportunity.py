"""Cutoff-safe three-year workload confirmation and prospect/value diagnostics."""
from __future__ import annotations

import numpy as np
import polars as pl

from universal_baseball.hitter_horizon_consistency import fixed_groups
from universal_baseball.hitter_model_tournament import make_engine_models

ORIGINS = (2016, 2017, 2018, 2019, 2021, 2022)


def training_rows(panel, cutoff, horizon, excluded_ids=()):
    if horizon not in (1, 2, 3) or cutoff > 2024:
        raise ValueError("Unsupported development cutoff")
    o = panel["origin_year"].to_numpy()
    mask = ((o+horizon <= cutoff) & ~((o < 2020) & (o+horizon >= 2020))
            & panel[f"pa_h{horizon}"].is_not_null().to_numpy())
    if len(excluded_ids):
        mask &= ~np.isin(panel["player_id"].to_numpy(), excluded_ids)
    return panel.filter(mask)


def attach_cohorts(panel, debuts, targets):
    if debuts["mlb_debut_date"].max().year > 2025 or targets["season"].max() > 2025:
        raise ValueError("Protected source")
    if debuts.unique("player_id").height != debuts.height:
        raise ValueError("Duplicate debut identity")
    known = debuts.select("player_id", pl.col("mlb_debut_date").dt.year().alias("debut_year"))
    f = panel.join(known, on="player_id", how="left", validate="m:1", maintain_order="left")
    first_pa = targets.filter(pl.col("mlb_pa") > 0).group_by("player_id").agg(pl.col("season").min().alias("first_observed_pa"))
    f = f.join(first_pa, on="player_id", how="left", validate="m:1", maintain_order="left")
    invalid = f.filter((pl.col("first_observed_pa") <= pl.col("origin_year")) &
        (pl.col("debut_year").is_null() | (pl.col("debut_year") > pl.col("origin_year"))))
    if invalid.height:
        raise ValueError("Observed MLB PA contradicts debut evidence")
    f = f.with_columns((pl.col("debut_year") <= pl.col("origin_year")).fill_null(False).alias("prior_debut"))
    return f.with_columns(
        (pl.col("stage").is_in(["Upper minors", "Lower minors"]) & ~pl.col("prior_debut")).alias("prospect"),
        (pl.col("stage").is_in(["Upper minors", "Lower minors"]) & pl.col("prior_debut")).alias("minor_returner"),
        ((pl.col("debut_year") >= pl.col("origin_year")-1) & pl.col("prior_debut")).fill_null(False).alias("recent_debut"),
    ).drop("debut_year", "first_observed_pa")


def cohorts(frame):
    groups = {"overall": np.ones(frame.height, bool), **fixed_groups(frame)}
    prospect = frame["prospect"].to_numpy()
    age, stage = frame["age"].to_numpy(), frame["stage"].to_numpy()
    groups.update({"Never-debuted minors": prospect,
        "Minor-league MLB returners": frame["minor_returner"].to_numpy(),
        "Recent debut": frame["recent_debut"].to_numpy()})
    for level in ("Upper minors", "Lower minors"):
        for name, mask in (("under23", age < 23), ("23plus", age >= 23)):
            groups[f"Prospects {level} {name}"] = prospect & (stage == level) & mask
    return groups


def fit_benchmark(x, y, tx):
    """Old selected five-member architecture, harmonized input rows/features."""
    predictions, probabilities = {}, {}
    for engine in ("lightgbm", "xgboost", "ebm", "ridge"):
        pair = make_engine_models(engine, 417)
        for model in (pair.classifier, pair.regressor):
            if "n_jobs" in model.get_params():
                model.set_params(n_jobs=4)
        pair.classifier.fit(x, y > 0)
        prob = np.clip(pair.classifier.predict_proba(tx)[:, 1], 0, 1)
        pair.regressor.fit(x[y > 0], y[y > 0])
        raw = pair.regressor.predict(tx)
        predictions[engine] = prob*np.clip(raw, 0, 750)
        probabilities[engine] = prob
        if engine == "lightgbm":
            # Candidate differs from the old member only in lower PA clipping.
            candidate = prob*np.clip(raw, 1, 750)
    direct = make_engine_models("lightgbm", 427).regressor.set_params(n_jobs=4)
    direct.fit(x, y)
    predictions["direct"] = np.clip(direct.predict(tx), 0, 750)
    return {"candidate": candidate, "candidate_p": probabilities["lightgbm"],
            "ensemble": np.mean(list(predictions.values()), axis=0),
            "ensemble_p": np.mean(list(probabilities.values()), axis=0),
            **{"member_"+k: v for k, v in predictions.items()}}


def arrival_probability(x, labels, tx):
    model = make_engine_models("lightgbm", 417).classifier.set_params(n_jobs=4)
    model.fit(x, labels)
    return model.predict_proba(tx)[:, 1]


def monotone_arrival(raw):
    p = np.asarray(raw)
    if p.ndim != 2 or p.shape[1] != 3 or not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("Expected three valid horizon probabilities")
    return np.maximum.accumulate(p, axis=1)


def reconciliation_beta(prior, cutoff, horizon):
    eligible = prior.filter((pl.col("origin_year")+horizon <= cutoff)
        & (pl.col("origin_year") < cutoff) & ~pl.col("pandemic"))
    years = sorted(eligible["origin_year"].unique().to_list())
    note = {"cutoff": cutoff, "horizon": horizon, "origins": years, "rows": eligible.height,
            "latest_target": max(years)+horizon if years else None, "beta": 0., "fallback": True}
    if len(years) < 2 or eligible.height < 300:
        return note
    xx, xy = [], []
    for f in eligible.partition_by("origin_year"):
        x = (f["candidate"]-f["accepted"]).to_numpy()*f["performance_anchor"].to_numpy()/600
        residual = (f["actual_value"]-f["delivered"]).to_numpy()
        xx.append(float(np.mean(x*x)))
        xy.append(float(np.mean(x*residual)))
    slope = float(np.mean(xy)/np.mean(xx)) if np.mean(xx) > 0 else 0.
    beta = float(np.clip(slope*eligible.height/(eligible.height+100), 0, 1))
    return {**note, "beta": beta, "fallback": False, "unconstrained_slope": slope}


def value_versions(frame, beta):
    """Never derive a hitting rate from the delivered value divided by PA."""
    return frame.with_columns(
        (pl.col("candidate")*pl.col("performance_anchor")/600).alias("replacement"),
        (pl.col("accepted")*pl.col("performance_anchor")/600).alias("product_control"),
        (pl.col("ensemble")*pl.col("performance_anchor")/600).alias("ensemble_product"),
        (pl.col("delivered")+beta*(pl.col("candidate")-pl.col("accepted"))*pl.col("performance_anchor")/600).alias("reconciled"),
        pl.lit(beta).alias("beta"))
