"""Origin-only medical observations and outcome-blind matched fallback gates."""

import numpy as np
import polars as pl

OLD = [
    "availability_annual_coverage",
    "status_medical_evidence_open",
    "status_medical_scope_interrupted",
    "medical_recent_spells",
    "medical_recent_days",
    "medical_recent_surgery",
]
STATES = [
    "no_captured_medical_entry",
    "observed_MLB_use",
    "reported_IL_activation",
    "unqualified_roster_return",
    "captured_IL_unresolved",
    "medical_followup_censored",
]
COUNTS = [
    "recent_episode_count",
    "recent_placement_reports",
    "recent_surgery_report_count",
]
NEW = ["med_" + s for s in STATES] + ["med_" + s for s in COUNTS]
KEYS = [
    "observation_state",
    "med_age_band",
    "med_current",
    "med_recent_regular",
    "med_quality_band",
]
RANGE = ["age", "med_best_recent_work", "last_MLB_quality"] + [
    "med_" + s for s in COUNTS
]


def frame(original, observations):
    source = observations.select(
        "row_id",
        "information_date",
        "observation_state",
        "recent_history_coverage_complete",
        *COUNTS,
    )
    if any(c in original.columns for c in source.columns if c != "row_id"):
        raise ValueError("Medical source collision")
    j = original.join(source, on="row_id", how="left", validate="1:1")
    if j.height != original.height or j["information_date"].null_count():
        raise ValueError("Missing source identity")
    if not j["information_date"].eq(j["ctx_information_date"]).all():
        raise ValueError("Medical cutoff mismatch")
    if set(j["observation_state"]) - set(STATES):
        raise ValueError("Unrecognized observation state")
    if (
        j.filter(pl.col("recent_history_coverage_complete"))
        .select(
            pl.any_horizontal(
                [pl.col(c).is_null() | (pl.col(c) < 0) for c in COUNTS]
            ).any()
        )
        .item()
    ):
        raise ValueError("Missing covered observation counts")
    j = j.with_columns(
        (pl.max_horizontal("work_0", "work_1", "work_2") / 600).alias(
            "med_best_recent_work"
        ),
        *[
            (pl.col("observation_state") == s).cast(pl.Float64).alias("med_" + s)
            for s in STATES
        ],
        *[
            (pl.col(c).fill_null(0).cast(pl.Float64) / 2).alias("med_" + c)
            for c in COUNTS
        ],
    )
    j = j.with_columns(
        (
            pl.col("recent_history_coverage_complete")
            & (pl.col("prior_debut") > 0)
            & (pl.col("med_best_recent_work") >= 0.5)
            & (pl.col("obs_status_finite_nonmedical") == 0)
            & (pl.col("obs_status_unresolved_nonmedical") == 0)
            & (pl.col("status_hard_unavailable") == 0)
            & (pl.col("status_retired") == 0)
        ).alias("med_eligible"),
        pl.when(pl.col("age") <= 25)
        .then(0)
        .when(pl.col("age") <= 32)
        .then(1)
        .otherwise(2)
        .alias("med_age_band"),
        (pl.col("pa_0") > 0).alias("med_current"),
        (pl.col("med_best_recent_work") >= 2 / 3).alias("med_recent_regular"),
        pl.when(pl.col("last_MLB_quality") < -1)
        .then(0)
        .when(pl.col("last_MLB_quality") <= 1)
        .then(1)
        .otherwise(2)
        .alias("med_quality_band"),
    )
    if not j.select(original.columns).equals(original):
        raise ValueError("Original feature/label evidence changed")
    return j


def support(train, test):
    counts = train.group_by(KEYS).agg(
        pl.col("player_id").n_unique().alias("medical_profile_people")
    )
    result = (
        test.select("row_id", *KEYS)
        .join(counts, on=KEYS, how="left", validate="m:1")
        .with_columns(pl.col("medical_profile_people").fill_null(0))
    )
    if train.is_empty():
        outside = np.ones(test.height, dtype=bool)
    else:
        x, t = train.select(RANGE).to_numpy(), test.select(RANGE).to_numpy()
        if not np.isfinite(x).all() or not np.isfinite(t).all():
            raise ValueError("Nonfinite medical support evidence")
        outside = ((t < x.min(axis=0)) | (t > x.max(axis=0))).any(axis=1)
    return result.with_columns(pl.Series("medical_range_outside", outside))


def apply(anchor_p, anchor_c, raw_p, raw_c, allowed):
    arrays = [np.asarray(v) for v in [anchor_p, anchor_c, raw_p, raw_c, allowed]]
    if len({a.shape for a in arrays}) != 1:
        raise ValueError("Prediction identity mismatch")
    p, c, rp, rc, gate = arrays
    if not np.isfinite(np.column_stack([p, c, rp, rc])).all():
        raise ValueError("Nonfinite forecast")
    if ((rp < 0) | (rp > 1)).any() or ((p < 0) | (p > 1)).any():
        raise ValueError("Invalid participation probability")
    return np.where(gate, rp, p), np.where(gate, np.clip(rc, 1, 800), c)
