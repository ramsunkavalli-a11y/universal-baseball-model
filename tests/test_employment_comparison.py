import polars as pl
import pytest
from universal_baseball.employment_comparison import FLAGS, corrected_frame, support


def sample():
    return pl.DataFrame([dict(origin_year=2021, player_id=553988, ctx_information_date='2022-03-18',
        on_40man=0., last_first_team_work=.898333, signed_first_team_work=.898333,
        status_major_link=0., status_agreement_unspecified=1.,
        **{n: 0. for n in FLAGS if n not in {'status_major_link', 'status_agreement_unspecified'}},
        work_0=0., next_pa=17.)])


def indicators():
    return pl.DataFrame([dict(origin_year=2021, player_id=553988, information_date='2022-03-18',
        **{n: n == 'status_minor_agreement' for n in FLAGS})])


def test_actual_work_kept_when_false_signing_removed():
    f=sample(); n=corrected_frame(f, indicators())
    assert n['signed_first_team_work'][0] == 0 and n['status_minor_agreement'][0] == 1
    assert n['next_pa'].equals(f['next_pa']) and n['last_first_team_work'].equals(f['last_first_team_work'])


def test_missing_source_is_not_zero():
    with pytest.raises(ValueError, match='Missing'):
        corrected_frame(sample(), indicators().filter(pl.col('player_id') != 553988))


def test_future_or_mismatched_date_rejected():
    with pytest.raises(ValueError, match='mismatched'):
        corrected_frame(sample(), indicators().with_columns(pl.lit('2022-03-19').alias('information_date')))


def test_future_outcome_changes_cannot_change_origin_features():
    a=corrected_frame(sample(), indicators())
    b=corrected_frame(sample().with_columns(pl.lit(700.).alias('next_pa')), indicators())
    assert a.drop('next_pa').equals(b.drop('next_pa'))


def test_repeated_seasons_do_not_inflate_people_support():
    r=dict(row_id=1, player_id=1, prior_debut=0, stage='Upper minors', age=23., pa_0=0.,
        evidence_foreign_source_present=0., last_first_team_known=0., status_hard_unavailable=0.,
        status_unresolved_nonmedical=0., status_finite_nonmedical=0., **{n: 0. for n in FLAGS})
    a=pl.DataFrame([r, dict(r,row_id=2)]); b=pl.DataFrame([dict(r,row_id=3,player_id=2)])
    assert support(a,b)['profile_people'][0] == 1
