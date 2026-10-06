"""Past-only training-era weights; no changes to a player's performance history."""
import numpy as np
import polars as pl

from .hitter_arrival_cohort_review import profiles

HALF_LIFE = 4.0
TOP15_SCORE = 1 - np.log(15) / np.log(2000)
MINOR_BUCKETS = ["AAA", "AA", "Aplus", "A", "Aminus", "DSL", "RK120", "RK121", "RK124", "RK128", "RK134", "RKother"]
PROFILE_KEYS = ["prior_debut", "upper_exposure", "age_band", "protected_listing",
                "fresh_rank_positive", "draft_time", "thin_advanced_top_pick"]


def weights(f, *, recent=False):
    years = f["origin_year"].to_numpy()
    if not len(years):
        raise ValueError("Empty training head")
    unique, counts = np.unique(years, return_counts=True)
    lookup = dict(zip(unique, counts, strict=True))
    w = np.array([len(f) / (len(unique) * lookup[y]) for y in years])
    if recent:
        w *= 2.0 ** ((years - years.max()) / HALF_LIFE)
        w *= len(f) / w.sum()
    assert np.isfinite(w).all() and (w > 0).all()
    return w


def profile(f):
    minor = pl.sum_horizontal([pl.col(b + "_" + str(k) + "_pa")
                               for b in MINOR_BUCKETS for k in range(3)])
    return profiles(f).with_columns(
        minor.alias("observed_minor_pa"),
        pl.when(pl.col("draft_known") == 0).then(pl.lit("unknown"))
        .when(pl.col("draft_elapsed") == 0).then(pl.lit("draft_year"))
        .when(pl.col("draft_elapsed") <= .2).then(pl.lit("one_two_years"))
        .otherwise(pl.lit("older_draft")).alias("draft_time"),
        ((pl.col("draft_known") > 0) & (pl.col("draft_elapsed") == 0)
         & (pl.col("draft_rank") >= TOP15_SCORE - 1e-12) & (pl.col("age") >= 20)
         & (minor <= 250)).alias("thin_advanced_top_pick"))


def support(train, query):
    tr = profile(train).with_columns(pl.Series("weight", weights(train, recent=True)))
    te = profile(query)
    person = tr.group_by(*PROFILE_KEYS, "player_id").agg(pl.col("weight").sum().alias("person_weight"))
    counts = person.group_by(PROFILE_KEYS).agg(pl.len().alias("profile_people"),
        (pl.col("person_weight").sum() ** 2 / (pl.col("person_weight") ** 2).sum()).alias("weighted_person_effective_count"))
    masses = tr.group_by(PROFILE_KEYS).agg(pl.col("weight").sum().alias("profile_weight"),
        pl.col("weight").filter(pl.col("origin_year") >= 2022).sum().alias("post2021_weight"))
    out = te.select("row_id", *PROFILE_KEYS).join(counts, on=PROFILE_KEYS, how="left", validate="m:1").join(
        masses, on=PROFILE_KEYS, how="left", validate="m:1")
    return out.with_columns(pl.col("profile_people", "weighted_person_effective_count", "profile_weight", "post2021_weight").fill_null(0)).with_columns(
        (pl.col("profile_people") == 0).alias("profile_absent"),
        (pl.col("profile_people") < 20).alias("profile_under20_warning"))
