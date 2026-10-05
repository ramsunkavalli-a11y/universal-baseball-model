"""Transparent established-role reference and a dated finite-return evidence gate."""

from datetime import date

import numpy as np
import polars as pl

FEATURES = [
    "role_age",
    "role_age_squared",
    "role_career",
    "last_MLB_work",
    "last_MLB_quality",
    "role_active_mean",
    "pooled_mlb_quality",
    "role_gap",
    "position_2",
    "position_3",
    "position_6",
    "position_10",
    "status_major_link",
    "status_minor_agreement",
    "status_agreement_unspecified",
    "status_released",
    "status_employment_unknown",
    "status_employment_conflict",
    "employment_evidence_unknown",
    "employment_evidence_age_years",
    "availability_annual_coverage",
    "status_medical_evidence_open",
    "status_medical_scope_interrupted",
    "medical_recent_days",
    "medical_recent_spells",
    "role_surgery",
]


def readiness(reports, pid, target, cutoff):
    cutoff = date.fromisoformat(cutoff)
    rows = [
        r
        for r in reports
        if r["player_id"] == pid
        and r["target_year"] == target
        and date.fromisoformat(r["known_date"]) <= cutoff
    ]
    if not rows:
        return None
    if any(not r.get("source_url") for r in rows):
        raise ValueError("Missing medical report provenance")
    latest = max(r["known_date"] for r in rows)
    rows = [r for r in rows if r["known_date"] == latest]
    if (
        len({(r["expected_ready_before_season"], r["surgery_reported"]) for r in rows})
        != 1
    ):
        raise ValueError("Conflicting medical readiness reports")
    return rows[0]


def frame(original, reports):
    w = original.select("work_0", "work_1", "work_2").to_numpy()
    active_mean = w.sum(axis=1) / np.maximum((w > 0).sum(axis=1), 1)
    if not np.isfinite(w).all() or (w < 0).any():
        raise ValueError("Invalid historical workloads")
    selected = [
        readiness(reports, r["player_id"], r["target_year"], r["ctx_information_date"])
        for r in original.select(
            "player_id", "target_year", "ctx_information_date"
        ).to_dicts()
    ]
    surgery = np.maximum(
        original["medical_recent_surgery"].to_numpy(),
        [float(bool(r and r["surgery_reported"])) for r in selected],
    )
    return original.with_columns(
        ((pl.col("age") - 27) / 10).alias("role_age"),
        (((pl.col("age") - 27) / 10) ** 2).alias("role_age_squared"),
        (pl.col("career_mlb_observed_pa") + 1).log().alias("role_career"),
        pl.Series("role_active_mean", active_mean / 600),
        (pl.col("last_MLB_lag") * 3).alias("role_gap"),
        pl.Series("role_surgery", surgery),
        pl.Series(
            "anticipated_preseason_readiness",
            [bool(r and r["expected_ready_before_season"]) for r in selected],
        ),
        (
            (pl.col("prior_debut") > 0)
            & (pl.col("last_MLB_known") > 0)
            & (pl.col("last_MLB_work") >= 0.5)
        ).alias("role_eligible"),
    )


def unrestricted(frame):
    return frame.filter(
        pl.col("role_eligible")
        & (pl.col("obs_status_finite_nonmedical") == 0)
        & (pl.col("obs_status_unresolved_nonmedical") == 0)
        & (pl.col("status_hard_unavailable") == 0)
        & (pl.col("status_retired") == 0)
    )


def transfer_allowed(row, evidence):
    return (
        row["role_eligible"]
        and row["anticipated_preseason_readiness"]
        and row["status_major_link"] > 0
        and row["status_employment_conflict"] == 0
        and row["status_retired"] == 0
        and row["status_hard_unavailable"] == 0
        and evidence["state"] == "reported_finite_season_budget"
    )


def matrix(frame, *, remove_explained_gap=False):
    x = frame.select(FEATURES).to_numpy().copy()
    if remove_explained_gap:
        x[:, FEATURES.index("role_gap")] = 0.0
    if not np.isfinite(x).all():
        raise ValueError("Nonfinite role input")
    return x


def support(train, test):
    def tag(f):
        return f.with_columns(
            (pl.col("age") // 5).cast(pl.Int64).alias("role_age_band"),
            (pl.col("last_MLB_work") >= 2 / 3).alias("role_400"),
            (pl.col("role_gap") > 0).alias("role_interrupted"),
        )

    keys = [
        "role_age_band",
        "role_400",
        "role_interrupted",
        "status_major_link",
        "availability_annual_coverage",
    ]
    a, b = tag(train), tag(test)
    counts = a.group_by(keys).agg(
        pl.col("player_id").n_unique().alias("role_profile_people")
    )
    return (
        b.select("row_id", *keys)
        .join(counts, on=keys, how="left", validate="m:1")
        .with_columns(pl.col("role_profile_people").fill_null(0))
    )


def coefficients(model, x):
    """Exact standardized linear predictor; classifier output remains log odds."""
    scale, head = model.steps[0][1], model.steps[1][1]
    z = scale.transform(x)[0]
    effects = np.asarray(head.coef_).reshape(-1) * z
    return dict(
        intercept=float(np.asarray(head.intercept_).reshape(-1)[0]),
        feature_effects=dict(zip(FEATURES, effects.tolist(), strict=True)),
        linear_prediction=float(
            np.asarray(head.intercept_).reshape(-1)[0] + effects.sum()
        ),
    )
