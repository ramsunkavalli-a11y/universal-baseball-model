import numpy as np
import polars as pl
import pytest

from universal_baseball.hitter_recent_promotion import MINOR_BUCKETS, profile, support, weights


def sample(**change):
    r = dict(row_id=1, player_id=1, origin_year=2016, prior_debut=0, age=21.,
        on_40man=0, scout_rank_score_0=.9, milb_canceled_0=0, milb_canceled_1=0,
        milb_canceled_2=0, draft_known=1, draft_elapsed=0., draft_rank=.82, next_pa=0.)
    r.update({b + "_" + str(k) + "_pa": 0. for b in MINOR_BUCKETS for k in range(3)})
    r.update(change)
    return pl.DataFrame([r])


def test_reference_origin_mass_equal():
    f = pl.concat([sample(row_id=1), sample(row_id=2), sample(row_id=3, origin_year=2020)])
    w = weights(f)
    assert w[:2].sum() == w[2]


def test_recent_four_year_ratio_preserves_mass_and_old_rows():
    f = pl.concat([sample(), sample(row_id=2, origin_year=2020)])
    w = weights(f, recent=True)
    assert w.sum() == pytest.approx(2.) and w[1] / w[0] == pytest.approx(2.)
    assert (w > 0).all()


def test_weights_outcome_invariant():
    f = pl.concat([sample(), sample(origin_year=2024)])
    assert np.array_equal(weights(f, recent=True), weights(f.with_columns(pl.lit(600.).alias("next_pa")), recent=True))


def test_profile_unknown_draft_not_fresh_and_missing_school_not_used():
    assert not profile(sample(draft_known=0))["thin_advanced_top_pick"].item()
    assert profile(sample(draft_known=0))["draft_time"].item() == "unknown"
    assert profile(sample(AA_0_pa=15., A_0_pa=35.))["thin_advanced_top_pick"].item()
    assert not profile(sample(AA_0_pa=251.))["thin_advanced_top_pick"].item()


def test_distinct_person_support_and_concentration_not_repeated_rows():
    f = pl.concat([sample(row_id=k, origin_year=2016+k) for k in range(3)])
    s = support(f, sample(row_id=50, origin_year=2024))
    assert s["profile_people"].item() == 1
    assert s["weighted_person_effective_count"].item() == pytest.approx(1.)


def test_unknown_profile_stays_scored():
    s = support(sample(), sample(row_id=50, draft_known=0))
    assert s.height == 1 and s["profile_absent"].item()
