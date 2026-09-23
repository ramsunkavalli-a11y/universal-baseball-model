"""Historical usage features and bounded, probability-weighted workload states."""
from __future__ import annotations

import numpy as np
import polars as pl

from universal_baseball.hitter_model_tournament import make_engine_models

POSITIONS = ("C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH")
ROLE_NAMES = ("history_available", "starts", "pa_per_start", "positions", "C", "DH", "IF", "OF")
ROLE_COLUMNS = [f"role_{name}_{lag}" for lag in (0, 1) for name in ROLE_NAMES]


def projection_vintage_audit(tables):
    """Cross-year invariance is a veto, never proof of vintage certification."""
    checks = []
    years = sorted(tables)
    for i, year in enumerate(years):
        for later in years[i+1:]:
            joined = tables[year].join(tables[later], on="player_id", suffix="_later", validate="1:1")
            for column in ("projected_pa", "projected_ip"):
                common = joined.filter(pl.col(column).is_not_null() & pl.col(column+"_later").is_not_null())
                same = common.filter(pl.col(column) == pl.col(column+"_later")).height
                checks.append({"earlier": year, "later": later, "field": column,
                               "common_nonnull": common.height, "exactly_equal": same})
    suspicious = any(c["common_nonnull"] >= 100 and c["common_nonnull"] == c["exactly_equal"] for c in checks)
    return {"status": "quarantined_cross_year_invariance" if suspicious else "vintage_still_unverified",
            "historical_workload_eligible": False, "checks": checks}


def role_features(panel, fielding, fractions):
    """Only completed origin-year or earlier usage; MLB starts are not health."""
    if panel["origin_year"].max() > 2025 or fielding["season"].max() > 2025:
        raise ValueError("Protected season")
    keys = ["season", "player_id", "team_id", "position_abbreviation"]
    if fielding.unique(keys).height != fielding.height:
        raise ValueError("Duplicate positional starts")
    f = fielding.filter(pl.col("position_abbreviation").is_in(POSITIONS))
    if f["games_started"].null_count() or (f["games_started"] < 0).any():
        raise ValueError("Invalid starts")
    years = sorted(f["season"].unique().to_list())
    lookup = {}
    for row in f.group_by("season", "player_id", "position_abbreviation").agg(
        pl.col("games_started").sum()).iter_rows(named=True):
        lookup.setdefault((row["season"], row["player_id"]), {})[
            row["position_abbreviation"]] = row["games_started"]
    maximum = max(sum(v.values()) for v in lookup.values())
    if maximum > 170:
        raise ValueError("Impossible summed non-pitcher starts")
    rows = []
    for r in panel.select("origin_year", "player_id", "mlb_pa_lag0", "mlb_pa_lag1").iter_rows(named=True):
        out = {k: r[k] for k in ("origin_year", "player_id")}
        for lag in (0, 1):
            year = r["origin_year"] - lag
            available = year in years and year in fractions
            counts = lookup.get((year, r["player_id"]), {})
            total = sum(counts.values())
            pa = r[f"mlb_pa_lag{lag}"] or 0
            # +5 pseudo-starts at 4 PA/start stabilizes small exposure. Not a
            # literal game rate: pinch-hit PA can occur without a start.
            values = [float(available), total / fractions[year] if available else 0.,
                      (pa + 20.) / (total + 5.) if available else 0.,
                      float(sum(v > 0 for v in counts.values()))]
            for positions in (("C",), ("DH",), ("1B", "2B", "3B", "SS"), ("LF", "CF", "RF")):
                values.append(sum(counts.get(p, 0) for p in positions) / max(total, 1))
            out.update({f"role_{name}_{lag}": value for name, value in zip(ROLE_NAMES, values, strict=True)})
        rows.append(out)
    return pl.DataFrame(rows), {"source_years": years, "max_summed_starts": maximum,
        "rows": len(rows), "features": ROLE_COLUMNS, "minor_usage_measured": False}


def mature_mask(panel, cutoff, horizon):
    if horizon not in (1, 2) or cutoff > 2024:
        raise ValueError("Unsupported development cutoff")
    origins = panel["origin_year"].to_numpy()
    return ((origins + horizon <= cutoff) & (origins < cutoff)
            & ~((origins < 2020) & (origins + horizon >= 2020))
            & panel[f"pa_h{horizon}"].is_not_null().to_numpy())


def workload_states(pa):
    values = np.asarray(pa)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Invalid workload labels")
    return np.where(values == 0, 0, np.where(values < 200, 1, np.where(values < 450, 2, 3)))


def state_mean(probabilities, means):
    p, q = np.asarray(probabilities), np.asarray(means)
    if p.shape != q.shape or p.ndim != 2 or p.shape[1] != 4:
        raise ValueError("Four states required")
    if not np.isfinite(p).all() or not np.isfinite(q).all() or (p < 0).any():
        raise ValueError("Invalid state predictions")
    if not np.allclose(p.sum(axis=1), 1) or (q[:, 0] != 0).any():
        raise ValueError("Invalid probability simplex or zero state")
    for j, (lo, hi) in enumerate(((1, 199), (200, 449), (450, 750)), 1):
        if ((q[:, j] < lo) | (q[:, j] > hi)).any():
            raise ValueError("Mean outside state support")
    return (p * q).sum(axis=1)


def models():
    pair = make_engine_models("lightgbm", 417)
    pair.classifier.set_params(n_jobs=4)
    pair.regressor.set_params(n_jobs=4)
    return pair


def fit_hurdle(x, y, tx):
    pair = models()
    pair.classifier.fit(x, y > 0)
    probability = pair.classifier.predict_proba(tx)[:, 1]
    pair.regressor.fit(x[y > 0], y[y > 0])
    conditional = np.clip(pair.regressor.predict(tx), 1, 750)
    return probability * conditional, probability


def fit_mixture(x, y, tx):
    labels = workload_states(y)
    if set(labels) != {0, 1, 2, 3}:
        raise ValueError("Insufficient state support")
    pair = models()
    pair.classifier.set_params(objective="multiclass", num_class=4)
    pair.classifier.fit(x, labels)
    probabilities = pair.classifier.predict_proba(tx)
    np.testing.assert_array_equal(pair.classifier.classes_, np.arange(4))
    means = np.zeros_like(probabilities)
    for j, (lo, hi) in enumerate(((1, 199), (200, 449), (450, 750)), 1):
        model = models().regressor
        model.fit(x[labels == j], y[labels == j])
        means[:, j] = np.clip(model.predict(tx), lo, hi)
    return state_mean(probabilities, means), probabilities, means
