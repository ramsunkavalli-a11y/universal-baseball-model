import polars as pl

from universal_baseball.hitter_arrival_cohort_review import profiles, support, probability_bands


def sample(**extra):
    row = dict(row_id=1, player_id=1, prior_debut=0, age=24., AAA_0_pa=120., AA_0_pa=220.,
               on_40man=1, scout_rank_score_0=0., milb_canceled_0=0,
               milb_canceled_1=0, milb_canceled_2=0, observation_p=.3, next_pa=0)
    row.update(extra)
    return pl.DataFrame([row])


def test_outcomes_do_not_define_profiles():
    a = sample()
    b = a.with_columns(pl.lit(600).alias("next_pa"))
    assert profiles(a).drop("next_pa").equals(profiles(b).drop("next_pa"))
    assert profiles(a)["upper_exposure"].item() == "200plus"


def test_mature_generic_peers_cannot_certify_unseen_calendar_context():
    train = pl.concat([sample(row_id=k, player_id=k, milb_canceled_0=1) for k in range(30)])
    query = sample(row_id=100, player_id=100, milb_canceled_1=1)
    s = support(train, query)
    assert s["readiness_people"].item() == 30
    assert s["calendar_readiness_people"].item() == 0
    assert s["calendar_context_absent"].item()
    assert s.height == query.height


def test_count_distinct_players_not_repeated_years():
    tr = pl.concat([sample(row_id=k) for k in range(30)])
    s = support(tr, sample(row_id=100, player_id=100))
    assert s["calendar_readiness_people"].item() == 1
    assert s["calendar_context_under20_warning"].item()


def test_probability_band_boundaries_and_mexico_not_upper():
    q = pl.concat([sample(row_id=k, observation_p=p, AAA_0_pa=0., AA_0_pa=0.)
                   for k, p in enumerate([0., .01, .1, .3, .7, 1.])])
    assert probability_bands(q)["probability_band"].to_list() == ["0_to_.01", ".01_to_.1", ".1_to_.3", ".3_to_.7", ".7_to_1", ".7_to_1"]
    assert not profiles(q)["upper_now"].any()
