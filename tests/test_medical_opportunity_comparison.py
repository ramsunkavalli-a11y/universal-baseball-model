import numpy as np
import polars as pl
import pytest

from universal_baseball.medical_opportunity_comparison import apply, frame, support


def example():
    base = pl.DataFrame(
        dict(
            row_id=[1, 2, 3],
            ctx_information_date=["2023-01-26"] * 3,
            work_0=[0.0, 480.0, 0.0],
            work_1=[540.0, 0.0, 0.0],
            work_2=[0.0, 0.0, 0.0],
            prior_debut=[1, 1, 0],
            obs_status_finite_nonmedical=[1.0, 0.0, 0.0],
            obs_status_unresolved_nonmedical=[0.0] * 3,
            status_hard_unavailable=[0.0] * 3,
            status_retired=[0.0] * 3,
            age=[23.0, 30.0, 18.0],
            pa_0=[0, 480, 0],
            last_MLB_quality=[1.3, 0.2, 0.0],
            player_id=[11, 22, 33],
            next_pa=[635, 500, 0],
        )
    )
    source = pl.DataFrame(
        dict(
            row_id=[1, 2, 3],
            information_date=["2023-01-26"] * 3,
            observation_state=[
                "medical_followup_censored",
                "observed_MLB_use",
                "no_captured_medical_entry",
            ],
            recent_history_coverage_complete=[True, True, False],
            recent_episode_count=[4, 1, None],
            recent_placement_reports=[4, 1, None],
            recent_surgery_report_count=[0, 0, None],
        )
    )
    return base, source


def test_eligibility_preserves_suspension_and_minor_missingness():
    base, source = example()
    f = frame(base, source)
    assert f["med_eligible"].to_list() == [False, True, False]
    assert f.select(base.columns).equals(base)
    assert f["recent_episode_count"].to_list() == [4, 1, None]
    assert f["med_medical_followup_censored"].to_list() == [1.0, 0.0, 0.0]


def test_test_outcomes_cannot_change_eligibility_or_support():
    base, source = example()
    f = frame(base, source)
    changed = frame(base.with_columns(pl.lit(99999).alias("next_pa")), source)
    assert changed["med_eligible"].equals(f["med_eligible"])
    assert support(f, f).equals(support(f, changed))


def test_distinct_people_not_repeated_seasons():
    base, source = example()
    f = frame(base, source).slice(1, 1)
    assert support(pl.concat([f] * 20), f)["medical_profile_people"].item() == 1


def test_no_training_support_and_outside_range():
    base, source = example()
    f = frame(base, source)
    assert support(f.head(0), f)["medical_range_outside"].all()
    assert support(f.slice(1, 1), f)["medical_range_outside"].to_list() == [
        True,
        False,
        True,
    ]


def test_fallback_exact_not_another_medical_deduction():
    p, c = apply([0.95, 0.0], [500.0, 300.0], [0.3, 0.8], [900.0, 600.0], [False, True])
    np.testing.assert_array_equal(p, [0.95, 0.8])
    np.testing.assert_array_equal(c, [500.0, 600.0])


def test_missing_identity_or_cutoff_raises():
    base, source = example()
    with pytest.raises(ValueError):
        frame(base, source.head(1))
    with pytest.raises(ValueError):
        frame(base, source.with_columns(pl.lit("2024-01-26").alias("information_date")))


def test_invalid_prediction_shapes():
    with pytest.raises(ValueError):
        apply([1.0], [500.0], [1.0, 1.0], [500.0, 500.0], [True])
