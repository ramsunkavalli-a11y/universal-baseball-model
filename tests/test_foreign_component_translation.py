import numpy as np
import pytest

from universal_baseball.foreign_component_translation import References, clr, events, fit, probability, profile, training_pairs
from universal_baseball.post_arrival_history import player_fold


def row(pid=1, year=2013, league='NPB', pa=100):
    return dict(player_id=pid, season=year, league=league, pa=pa, hits=20, doubles=3,
                triples=1, hr=2, bb=10, ibb=1, hbp=2, so=20)


def pair(pid=1, year=2013):
    return dict(player_id=pid, fold=player_fold(pid), a='NPB', b='MLB', from_year=year,
                through_year=year+1, from_pa=100, to_pa=100, minimum_pa=30,
                mechanism='consecutive_season', domestic_2020_exception=False,
                role_evidence={'supported_hitter': True}, from_counts=row(pid,year),
                to_counts=dict(row(pid,year+1,'MLB'),so=25,hr=1))


def test_events_preserve_ibb_and_all_pa():
    x=events(row()); assert x.sum()==100 and x[2]==9 and x[4]==14
    assert np.isclose(probability(x).sum(),1)
    with pytest.raises(ValueError): events(dict(row(),hits=0))


def test_full_reference_retains_unmapped_and_excludes_known_fold():
    r=References([row(),row(None),dict(row(2),so=10)])
    expected=events(row())+events(row(None))+events(dict(row(2),so=10))
    assert np.array_equal(r.counts('NPB',2013,[]),expected)
    excluded={player_fold(1)}
    keep=[x for x in [row(),row(None),dict(row(2),so=10)] if x['player_id'] is None or player_fold(x['player_id']) not in excluded]
    assert np.array_equal(r.counts('NPB',2013,excluded),sum((events(x) for x in keep),np.zeros(8)))


def test_forward_only_mature_whole_player_fit():
    p=pair(); future=pair(2,2015)
    backwards=dict(pair(3),a='MLB',b='NPB')
    assert training_pairs([p,future,backwards],2014,[])==[p]
    assert training_pairs([p],2014,[p['fold']])==[]
    with pytest.raises(ValueError): training_pairs([p,p],2014,[])


def test_future_reference_mutation_and_fit_optimum():
    refs=[row(None),row(None,2014,'MLB'),row(None,2014,'NPB')]
    m=fit([pair()],References(refs),2014,[])
    altered=fit([pair(),pair(5,2019)],References(refs+[row(None,2099)]),2014,[])
    assert m==altered
    c=np.array(m['coefficients']); assert np.isfinite(c).all() and (c[:,2]>=0).all() and (c[:,2]<=2).all()


def input_row():
    return dict(candidate_key='x',player_id=1,origin_year=2014,original_source_origin=True,
                recent_foreign_pa=100,foreign_history_counts={f'{l}_{k}':dict(season=2014-k,
                player_identity_and_stat_observed=(l=='NPB' and k==0), counts=row(1,2014-k,l) if l=='NPB' and k==0 else dict(row(1,2014-k,l),pa=0))
                for l in ['NPB','KBO'] for k in range(3)})


def test_missing_support_is_not_average_talent_or_forecast():
    r=References([row(None,2014,'MLB'),row(None,2014,'NPB')])
    out=profile(input_row(),fit([],r,2014,[]),r)
    assert out['missing_translation'] and out['translated_probability'] is None
    assert out['raw_recent_foreign_pa']==100 and out['new_workload_forecast'] is None


def test_positive_coherent_prediction_and_cutoff_guard():
    r=References([row(None),row(None,2014,'MLB'),row(None,2014,'NPB')])
    out=profile(input_row(),fit([pair()],r,2014,[]),r)
    assert not out['missing_translation']
    assert np.isclose(sum(out['translated_probability']),1)
    assert (np.array(out['translated_probability'])>0).all()
    with pytest.raises(ValueError): profile(input_row(),fit([],r,2013,[]),r)


def test_clr_scale_and_zero_guard():
    assert abs(clr(probability(events(row()))).sum())<1e-12
    with pytest.raises(ValueError): clr(np.zeros(8))
