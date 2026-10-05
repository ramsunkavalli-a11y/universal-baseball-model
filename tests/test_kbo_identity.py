import pytest
from universal_baseball.kbo_identity import match_identity, name_key, profile_identity


def html(name='KIM Hye Seong', born='27/01/1999', code='67304'):
    return f'<a href="/Teams/PlayerInfoHitter/Summary.aspx?pcode={code}">Profile</a><ul><li>Name : {name}</li><li>Born : {born}</li><li>Salary : Future salary</li></ul>'


def test_static_whitelist_and_navigation():
    a = profile_identity(html(), '67304')
    assert a['birth_date'] == '1999-01-27' and 'salary' not in a
    assert profile_identity(html().replace('Future salary', '999999'), '67304') == a
    with pytest.raises(ValueError, match='navigation'):
        profile_identity(html(code='00000'), '67304')


def test_missing_identity_is_not_a_guess():
    p = profile_identity(html(name=''), '67304')
    assert not p['identity_available']
    assert match_identity(p, {})['player_id'] is None
    assert not profile_identity(html(born=''), '67304')['identity_available']


def test_normalization_does_not_guess_romanization():
    assert name_key('KIM Hye-Seong') == name_key('kim hye seong')
    assert name_key('José Fernández') == name_key('Jose Fernandez')
    assert name_key('LEE Jung Hoo') != name_key('LEE Jung Ho')


def test_birth_name_and_unique_person_all_required():
    p = profile_identity(html(), '67304')
    key = (p['birth_date'], name_key(p['english_name']))
    person = dict(key_uuid='x', player_id=808975, register_name='Hyeseong Kim')
    assert match_identity(p, {key: {'x': person}})['player_id'] == 808975
    assert match_identity(p, {(p['birth_date'], 'another'): {'x': person}})['player_id'] is None
    assert match_identity(p, {('1998-01-27', key[1]): {'x': person}})['player_id'] is None
    assert match_identity(p, {key: {'x': person, 'y': dict(person, player_id=1)}})['match_status'].startswith('ambiguous')


def test_no_MLB_key_still_retains_register_person():
    p = profile_identity(html(), '67304')
    key = (p['birth_date'], name_key(p['english_name']))
    r = match_identity(p, {key: {'x': dict(key_uuid='x', player_id=None, register_name='Hye Seong Kim')}})
    assert r['key_uuid'] == 'x' and r['player_id'] is None
