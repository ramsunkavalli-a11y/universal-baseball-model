"""Support rules and sealed experiment output invariants, not new model tuning."""
import polars as pl
import pytest
from universal_baseball.minor_infield_play_share import check_support


def rows():
    train=pl.DataFrame([dict(player_id=i,origin_year=y,target_year=y+1,age=20.,level='AA',prior_mlb_defense=0.,gb_4=0.,gb_5=0.,gb_6=100.,x=1.) for i in range(1,32) for y in [2016,2017]])
    test=pl.DataFrame([dict(player_id=101,origin_year=2018,target_year=2019,age=19.,level='AA',prior_mlb_defense=0.,gb_4=0.,gb_5=0.,gb_6=100.,x=1.)])
    return train,test


def test_distinct_people_and_profile_warning():
    train,test=rows()
    check,support=check_support(train,test,['x'],2018,1)
    assert check['training_rows']==62 and check['training_people']==31
    assert support==[31] and check['fit_allowed']
    test=test.with_columns(pl.lit('RK').alias('level'))
    check,support=check_support(train,test,['x'],2018,1)
    assert support==[0] and check['zero_profile']==1 and check['test_rows']==1


def test_support_does_not_use_future_values():
    train,test=rows()
    changed=test.with_columns(pl.lit(99.).alias('quality'),pl.lit(0.).alias('delivered'))
    assert check_support(train,test,['x'],2018,1)==check_support(train,changed,['x'],2018,1)


def test_player_overlap_and_future_training_rejected():
    train,test=rows()
    with pytest.raises(AssertionError):
        check_support(train,test.with_columns(pl.lit(1).alias('player_id')),['x'],2018,1)
    with pytest.raises(AssertionError):
        check_support(train.with_columns(pl.lit(2019).alias('target_year')),test,['x'],2018,1)


def test_many_repeated_rows_do_not_create_people_or_target_year_support():
    train,test=rows()
    small=train.filter(pl.col('player_id')<=10)
    check,_=check_support(small,test,['x'],2018,1)
    assert not check['fit_allowed']
    single=train.filter(pl.col('origin_year')==2016)
    check,_=check_support(single,test,['x'],2018,1)
    assert not check['fit_allowed']
