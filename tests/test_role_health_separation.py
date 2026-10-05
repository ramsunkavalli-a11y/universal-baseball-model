from copy import deepcopy

import numpy as np
import polars as pl
import pytest

from universal_baseball.role_health_separation import (
    FEATURES,
    OMITTED_CLINICAL,
    matrix,
    medical_span_audit,
    support,
)


def test_medical_inputs_cannot_grant_workload_or_change_readiness_matrix():
    f = pl.DataFrame({n: [0.3] for n in FEATURES + OMITTED_CLINICAL})
    other = f.with_columns([pl.lit(999.0).alias(n) for n in OMITTED_CLINICAL])
    assert np.array_equal(matrix(f), matrix(other))
    x = matrix(f, reported_ready=True)
    assert x[0, FEATURES.index("role_gap")] == 0
    assert np.array_equal(
        np.delete(x, FEATURES.index("role_gap"), axis=1),
        np.delete(matrix(f), FEATURES.index("role_gap"), axis=1),
    )


def test_nonfinite_used_input_rejected_but_missing_medical_not_healthy():
    f = pl.DataFrame({n: [0.0] for n in FEATURES})
    assert matrix(f).shape == (1, 20)
    with pytest.raises(ValueError):
        matrix(f.with_columns(pl.lit(float("nan")).alias("role_gap")))


def test_support_counts_people_and_keeps_missing_profiles():
    tr = pl.DataFrame(
        dict(
            player_id=[1, 1, 2],
            age=[22, 22, 22],
            last_MLB_work=[0.8] * 3,
            role_gap=[0.0] * 3,
            status_major_link=[1.0] * 3,
        )
    )
    te = pl.DataFrame(
        dict(
            row_id=[5, 6],
            age=[22, 40],
            last_MLB_work=[0.8] * 2,
            role_gap=[0.0] * 2,
            status_major_link=[1.0] * 2,
        )
    )
    assert support(tr, te)["role_profile_people"].to_list() == [2, 0]


def test_positive_window_marks_contradiction_not_recovery_or_exact_days():
    spells = [
        dict(
            start="2016-03-25", end="2016-09-01", closure_kind="observation_scope_exit"
        )
    ]
    windows = [dict(start="2016-06-01", end="2016-08-31", pa=200)]
    original = deepcopy(spells)
    a = medical_span_audit(spells, windows, "2017-01-26")[0]
    assert a["continuous_absence_contradicted"]
    assert a["certified_medical_absence_days"] is None
    assert not a["medical_recovery_certified"]
    assert not a["exact_return_date_known"]
    assert spells == original


@pytest.mark.parametrize(
    "window",
    [
        dict(start="2016-01-01", end="2016-12-31", pa=432),
        dict(start="2016-06-01", end="2016-08-31", pa=0),
        dict(start="2016-06-01", end="2016-08-31", pa=200, available_date="2017-02-01"),
    ],
)
def test_annual_or_future_or_zero_total_does_not_certify_contradiction(window):
    s = [dict(start="2016-03-25", end="2016-09-01")]
    assert not medical_span_audit(s, [window], "2017-01-26")[0][
        "continuous_absence_contradicted"
    ]
