import pytest
from universal_baseball.npb_hitter_2026_identity import listings, names


def body(title='Test 2026年度 選手一覧'):
    return f'<title>{title}</title><table><tr class="rosterPlayer"><td>1</td><td><a href="/bis/players/123.html">Name</a></td><td>2000.01.02</td><td>2027 major league star</td></tr></table>'


def test_static_keys_only_and_wrong_vintage_rejected():
    found, dates = names(body(), 'Test')
    assert found == {'Name': {'123'}} and dates == {'123': '2000-01-02'}
    for html in [body('Other 2026年度 選手一覧'), body('Test 2025年度 選手一覧'),
                 body().replace('/123.html', '/x.html'), body().replace('2000.01.02', '2000.02.31')]:
        with pytest.raises(ValueError): names(html, 'Test')


def test_complete_current_index_and_host_guard():
    html = ''.join(f'<a href="rst_{c}.html">{c}</a>' for c in 'abcdefghijkl')
    assert len(listings(html)) == 12
    with pytest.raises(ValueError): listings(html.replace('rst_l', 'rst2_l'))
    with pytest.raises(ValueError): listings(html.replace('rst_a.html', 'https://wrong.example/bis/teams/rst_a.html'))


def test_only_explicit_staff_section_is_removed():
    from universal_baseball.npb_hitter_2026_identity_v2 import names as current_names
    html = body().replace('<tr class="rosterPlayer">', '<tr class="rosterMainHead"><th class="rosterPos">投手</th></tr><tr class="rosterPlayer">')
    staff = '<tr class="rosterMainHead"><th class="rosterPos">監督</th></tr><tr class="rosterPlayer"><td>1</td><td>Manager</td><td>1980.01.01</td></tr>'
    html = html.replace('<table>', '<table>' + staff)
    assert current_names(html, 'Test')[0] == {'Name': {'123'}}
    with pytest.raises(ValueError): current_names(html.replace('投手', 'Unknown'), 'Test')
