import pytest

from universal_baseball.kbo_history import player_id,join_groups,validate,FIELDS1,FIELDS2


def row(**changes):
    result=dict(kbo_id='00123',player_name_ko='테스트',displayed_team='NC',
                **{k:0 for k in FIELDS1+FIELDS2},raw_avg='0.000',raw_slg='0.000',raw_obp='0.000')
    result.update(changes)
    return result


def test_old_and_new_paths_preserve_leading_zero_without_status():
    assert player_id('/Record/Retire/Hitter.aspx?playerId=00123')=='00123'
    assert player_id('/Record/Player/HitterDetail/Basic.aspx?playerId=00123')=='00123'
    with pytest.raises(ValueError):
        player_id('/Record/Other.aspx?playerId=00123')


def test_undefined_rates_are_not_zero_talent():
    r=validate(row())
    assert r['avg'] is None and r['slg'] is None and r['obp'] is None


def test_residual_and_rounded_rates():
    r=validate(row(pa=12,ab=8,hits=3,doubles=1,hr=1,tb=7,bb=2,ibb=1,hbp=1,
                   raw_avg='0.375',raw_slg='0.875',raw_obp='0.545'))
    assert r['unenumerated_pa']==1


def test_negative_residual_and_bad_bases_fail():
    with pytest.raises(AssertionError):
        validate(row(pa=1,ab=2))
    with pytest.raises(AssertionError):
        validate(row(pa=1,ab=1,hits=1,tb=2,raw_avg='1.000',raw_slg='2.000',raw_obp='1.000'))


def test_coverage_mismatch_does_not_drop_players():
    with pytest.raises(AssertionError,match='coverage differs'):
        join_groups([row()],[row(kbo_id='002')],2015)


def test_join_duplicate_and_mismatched_identity_fail():
    with pytest.raises(AssertionError):
        join_groups([row(),row()],[row()],2015)
    with pytest.raises(AssertionError,match='identity mismatch'):
        join_groups([row()],[row(player_name_ko='다른이름')],2015)


def test_join_retains_unknown_mlb_id_and_full_season_key():
    r=join_groups([row()],[row()],2015)[0]
    assert r['season']==2015 and r['kbo_id']=='00123'
    assert 'player_id' not in r and not r['mlb_translation_fitted']
