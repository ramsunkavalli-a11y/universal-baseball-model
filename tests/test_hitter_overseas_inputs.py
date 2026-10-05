from copy import deepcopy
import pytest
from universal_baseball.hitter_overseas_inputs import foreign_features, status_features
from universal_baseball.mlb_event_logit import EVENTS


def source():
    return dict(candidate_key='2017:1', origin_year=2017, recent_foreign_pa=100,
        foreign_history_counts={f'{l}_{k}': dict(season=2017-k, counts={'pa':100 if l=='NPB' else 0},
            player_identity_and_stat_observed=l=='NPB', absent_group_is_not_certified_zero=l=='KBO')
            for l in ['NPB','KBO'] for k in range(3)})


def profile():
    return dict(candidate_key='2017:1', origin_year=2017, outer_fold=2, excluded_folds=[2,3],
        missing_translation=True, supported_fraction=0., leagues=[], translated_probability=None)


def test_unknown_overseas_is_not_zero_observed_talent():
    f=foreign_features(source(),profile(),origin=2017,outer_fold=2,own_fold=3)
    assert f['foreign_KBO_0_unknown']==1 and f['foreign_KBO_0_observed']==0
    assert f['foreign_translation_missing']==1 and f['foreign_profile_present']==1
    assert len([k for k in f if k.startswith('foreign_translated_')])==len(EVENTS)


def test_nested_own_player_fold_is_required():
    p=profile();p['excluded_folds']=[2]
    with pytest.raises(ValueError,match='contamination'):
        foreign_features(source(),p,origin=2017,outer_fold=2,own_fold=3)


def test_future_counts_cannot_enter():
    s=source();s['foreign_history_counts']['NPB_0']['season']=2018
    with pytest.raises(ValueError,match='Future'):
        foreign_features(s,profile(),origin=2017,outer_fold=2,own_fold=3)


def test_absent_profile_and_nonforeign_are_distinct():
    assert not any(foreign_features(None,None,origin=2017,outer_fold=2,own_fold=3).values())
    with pytest.raises(ValueError,match='Missing'):
        foreign_features(source(),None,origin=2017,outer_fold=2,own_fold=3)
