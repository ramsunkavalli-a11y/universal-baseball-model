"""Role inputs cannot silently use defective medical spans as playing-time boosts."""

from copy import deepcopy
from datetime import date

import numpy as np
import polars as pl

from .finite_return_baseline import FEATURES as PREVIOUS_FEATURES

FEATURES = PREVIOUS_FEATURES[:20]
OMITTED_CLINICAL = PREVIOUS_FEATURES[20:]


def matrix(frame, *, reported_ready=False):
    x = frame.select(FEATURES).to_numpy().copy()
    if reported_ready:
        x[:, FEATURES.index("role_gap")] = 0.0
    if not np.isfinite(x).all():
        raise ValueError("Nonfinite role input")
    return x


def coefficients(model, x):
    scale, head = model.steps[0][1], model.steps[1][1]
    effects = np.asarray(head.coef_).reshape(-1) * scale.transform(x)[0]
    intercept = float(np.asarray(head.intercept_).reshape(-1)[0])
    return dict(
        intercept=intercept,
        feature_effects=dict(zip(FEATURES, effects.tolist(), strict=True)),
        linear_prediction=float(intercept + effects.sum()),
    )


def support(train, test):
    def tag(f):
        return f.with_columns(
            (pl.col("age") // 5).cast(pl.Int64).alias("age_band"),
            (pl.col("last_MLB_work") >= 2 / 3).alias("prior_regular"),
            (pl.col("role_gap") > 0).alias("interrupted"),
        )

    keys = ["age_band", "prior_regular", "interrupted", "status_major_link"]
    counts = (
        tag(train)
        .group_by(keys)
        .agg(pl.col("player_id").n_unique().alias("role_profile_people"))
    )
    return (
        tag(test)
        .select("row_id", *keys)
        .join(counts, on=keys, how="left", validate="m:1")
        .with_columns(pl.col("role_profile_people").fill_null(0))
    )


def medical_span_audit(spells, windows, cutoff):
    """Positive period totals can contradict a continuous span, not date recovery.

    Only a fully contained positive window contradicts absence throughout that
    window. Overlapping or annual totals alone do not identify the return date.
    This is an audit, never a clinical-day replacement or forecast feature.
    """
    cutoff = date.fromisoformat(cutoff)
    eligible = []
    for w in windows:
        start, end = date.fromisoformat(w["start"]), date.fromisoformat(w["end"])
        known = date.fromisoformat(w.get("available_date", w["end"]))
        if start > end or known < end or w["pa"] < 0:
            raise ValueError("Invalid appearance window")
        if known <= cutoff and end <= cutoff and w["pa"] > 0:
            eligible.append(w)
    rows = []
    for s in spells:
        start = date.fromisoformat(s["start"])
        if start > cutoff:
            raise ValueError("Future clinical spell")
        end = date.fromisoformat(s["end"]) if s["end"] else cutoff
        if end < start or end > cutoff:
            raise ValueError("Invalid clinical end")
        conflicts = [
            deepcopy(w)
            for w in eligible
            if start <= date.fromisoformat(w["start"])
            and date.fromisoformat(w["end"]) < end
        ]
        rows.append(
            dict(
                source_spell=deepcopy(s),
                continuous_absence_contradicted=bool(conflicts),
                positive_contained_windows=conflicts,
                exact_return_date_known=False,
                medical_recovery_certified=False,
                certified_medical_absence_days=None,
            )
        )
    return rows
