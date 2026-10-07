"""Fixed-position MLB range quality, not opportunity or total defensive value."""
from collections import defaultdict
from datetime import date
import math

import numpy as np

LEVELS = ("rk", "a-", "a", "a+", "aa", "aaa")
BASE_FEATURES = ("age_c", "age_sq", "age_missing", "pos_4", "pos_5", "log_gb",
                 "current_fielding", "source_history_left_truncated", "prior_mlb_defense",
                 "prior_rate", "log_prior_outs", "prior_quality_missing", "current_mlb_position",
                 *[f"share_{v}" for v in LEVELS], "dsl_share")


def origin_context(row, minor, biography, native, official):
    out = dict(row)
    year, pid, pos = row["origin_year"], row["player_id"], row["position"]
    bio = biography.get(pid, {})
    dob = date.fromisoformat(bio["birth_date"]) if bio.get("birth_date") else None
    cutoff = date(year, 7, 1)
    age = year - dob.year - ((cutoff.month, cutoff.day) < (dob.month, dob.day)) if dob else row["age"]
    out.update(original_age=row["age"], original_level=row["level"], original_name=row["player_name"],
               age=float(age) if age is not None else None, player_name=bio.get("captured_name") or row["player_name"],
               age_basis="identity_birthdate_july_1" if dob else "original_reported_age")
    pool = [r for r in minor.get((pid, pos), []) if year - 2 <= r["season"] <= year]
    current = [r for r in pool if r["season"] == year]
    counts = {level: sum(r["ground_balls"] * .5 ** (year - r["season"]) for r in pool if r["level"] == level) for level in LEVELS}
    assert math.isclose(sum(counts.values()), row["ground_balls"], abs_tol=1e-8)
    out.update({f"share_{level}": n / row["ground_balls"] for level, n in counts.items()})
    current_level = max((r["level"] for r in current), key=LEVELS.index, default=None)
    out.update(fielding_level=current_level or "NO_CURRENT_MINOR_FIELDING", current_fielding=bool(current),
               latest_minor_fielding_season=max((r["season"] for r in pool), default=None),
               dsl_share=row["dsl_ground_balls"] / row["ground_balls"],
               current_mlb_position=official.get((year, pid, pos), 0) > 0,
               prior_quality_missing=True, prior_rate=0., log_prior_outs=0.)
    past = [r for r in native.get((pid, pos), {}).values() if year - 2 <= r["season"] <= year and r["measurement_valid"]]
    n = sum(r["native_outs"] * .5 ** (year - r["season"]) for r in past)
    runs = sum(r["range_runs"] * .5 ** (year - r["season"]) for r in past)
    out.update(prior_native_outs=n, prior_range_runs=runs, prior_measured_seasons=len(past),
               prior_rate=1500 * runs / (n + 1500), log_prior_outs=math.log1p(n), prior_quality_missing=not past,
               age_c=((age if age is not None else 23) - 23) / 10,
               age_sq=(((age if age is not None else 23) - 23) / 10) ** 2,
               age_missing=age is None, pos_4=pos == 4, pos_5=pos == 5,
               log_gb=math.log1p(row["ground_balls"]), raw_share=row["credits"] / row["ground_balls"])
    return out


def label(row, horizon, native, official):
    year, pid, pos = row["origin_year"], row["player_id"], row["position"]
    paths = []
    for season in range(year + 1, min(year + horizon, 2025) + 1):
        r = native.get((pid, pos), {}).get(season)
        official_n = official.get((season, pid, pos), 0)
        paths.append(dict(season=season, official_outs=official_n,
                          native_outs=r["native_outs"] if r else None,
                          range_runs=r["range_runs"] if r else None,
                          measurement_valid=bool(r and r["measurement_valid"])))
    measured = [r for r in paths if r["measurement_valid"]]
    n = sum(r["native_outs"] for r in measured)
    runs = sum(r["range_runs"] for r in measured)
    mature = year + horizon <= 2025
    quality = 1500 * runs / n if mature and n >= 1500 and len(measured) >= 2 else None
    missing = sum(r["official_outs"] for r in paths if r["official_outs"] > 0 and not r["measurement_valid"])
    out = {**row, "horizon": horizon, "window_end": year + horizon, "window_mature": mature,
           "quality_rate": quality, "same_position_outs": n, "same_position_range_runs": runs,
           "same_position_seasons": len(measured), "unmeasured_official_outs": missing,
           "future_position_official_outs": sum(r["official_outs"] for r in paths),
           "quality_status": "window_incomplete" if not mature else "measured_quality" if quality is not None else "insufficient_or_absent_quality",
           "measurement_mean_elapsed": sum((r["season"] - year) * r["native_outs"] for r in measured) / n if n else None}
    return out, paths


def profile(row):
    age = row["age"]
    band = "unknown" if age is None else "<=20" if age <= 20 else "21-24" if age <= 24 else "25-29" if age <= 29 else "30+"
    return row["fielding_level"], band, row["position"], row["prior_mlb_defense"]


def preflight(train, test, origin, fold, horizon):
    assert all(r["window_end"] <= origin and r["origin_year"] < origin and r["horizon"] == horizon and r["quality_rate"] is not None for r in train)
    assert all(r["player_id"] % 5 != fold for r in train)
    assert all(r["origin_year"] == origin and r["player_id"] % 5 == fold and r["horizon"] == horizon for r in test)
    assert {r["player_id"] for r in train}.isdisjoint(r["player_id"] for r in test)
    keys = lambda rows: [(r["origin_year"], r["player_id"], r["position"]) for r in rows]
    assert len(set(keys(train))) == len(train) and len(set(keys(test))) == len(test)
    counts = defaultdict(set)
    for r in train:
        counts[profile(r)].add(r["player_id"])
    support = [len(counts[profile(r)]) for r in test]
    people = len({r["player_id"] for r in train})
    origins = sorted({r["origin_year"] for r in train})
    features = (*BASE_FEATURES, "complete_rate", "raw_share")
    assert np.isfinite(matrix(train, features)).all() and np.isfinite(matrix(test, features)).all()
    return dict(origin=origin, fold=fold, horizon=horizon, training_rows=len(train), training_people=people,
                training_origins=origins, test_rows=len(test), test_people=len({r["player_id"] for r in test}),
                measured_test_rows=sum(r["quality_rate"] is not None for r in test),
                measured_test_sparse_profiles=sum(n < 20 and r["quality_rate"] is not None for n, r in zip(support, test)),
                fit_allowed=people >= 30 and len(origins) >= 2), support


def matrix(rows, features):
    return np.array([[float(r[c]) for c in features] for r in rows], dtype=float).reshape(len(rows), len(features))


def person_weights(rows):
    counts = defaultdict(int)
    for r in rows:
        counts[r["player_id"]] += 1
    return np.array([1 / counts[r["player_id"]] for r in rows])
