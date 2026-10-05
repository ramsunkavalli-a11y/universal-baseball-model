import pytest

from universal_baseball.international_hitter_snapshot_2026 import npb_links, batting_rows, snapshot_date, controls, subtotal
from universal_baseball.npb_history import HEADERS, COUNTS


def body(year=2026, marker='*'):
    values = dict(games=10, pa=50, ab=40, runs=5, hits=10, doubles=2, triples=1, hr=1, tb=17,
                  rbi=5, sb=1, cs=0, sh=1, sf=1, bb=7, ibb=1, hbp=1, so=12, gdp=0)
    heads = ''.join('<th>' + h + '</th>' for h in HEADERS[1:])
    numbers = ''.join('<td>' + str(values[k]) + '</td>' for k in COUNTS)
    sup = '<sup>' + marker + '</sup>' if marker else ''
    return f'<title>{year}年度 Test 個人打撃成績</title><table class="tablefix2"><tr>{heads}</tr><tr><td>{sup}Name</td>{numbers}<td>.250</td><td>.425</td><td>.367</td></tr></table>'


@pytest.mark.parametrize('marker,bats', [('*', 'L'), ('+', 'S'), ('', 'R')])
def test_snapshot_counts_and_markers(marker, bats):
    team, rows = batting_rows(body(marker=marker))
    assert team == 'Test' and rows[0]['season'] == 2026 and rows[0]['pa'] == 50
    assert rows[0]['bats'] == bats and rows[0]['name_key'] == 'Name'


@pytest.mark.parametrize('html', [body(2025), body(marker='?'), body().replace('<th>打席</th>', '<th>Wrong</th>'),
                                body().replace('<td>17</td>', '<td>18</td>')])
def test_wrong_year_scope_or_counts_rejected(html):
    with pytest.raises(ValueError): batting_rows(html)


def index(host='npb.jp'):
    return '<title>2026年度 公式戦成績</title>' + ''.join(f'<a href="https://{host}/bis/2026/stats/idb1_{c}.html">x</a>' for c in 'abcdefghijkl')


def test_only_correct_complete_first_team_index():
    assert len(npb_links(index())) == 12
    for html in [index('evil.example'), index().replace('2026年度', '2025年度'), index().replace('idb1_l', 'idb2_l')]:
        with pytest.raises(ValueError): npb_links(html)


def test_asof_does_not_certify_final_season():
    assert snapshot_date('<p>2026年10月4日 現在</p>') == '2026-10-04'
    assert snapshot_date('<p>2026 season</p>') is None
    with pytest.raises(ValueError): snapshot_date('<p>2026年10月4日 現在</p><p>2026年10月5日 現在</p>')


def test_controls_are_source_selected_and_unknown_identity_is_not_fuzzy_merged():
    rows = [{'id': 'b', 'pa': 20}, {'id': 'a', 'pa': 20}, {'id': 'c', 'pa': 1}, {'id': 'd', 'pa': 0}]
    assert [r['id'] for _, r in controls(rows, 'id')] == ['a', 'c', 'd']
    r = batting_rows(body())[1][0]
    rows = [dict(r, id='x', season=2025), dict(r, id='x', season=2026)]
    baseline = subtotal(rows, 'id', 'x', 2025)
    rows[1]['pa'] = 99999
    assert subtotal(rows, 'id', 'x', 2025) == baseline
    assert subtotal(rows, 'id', None, 2026)['source_rows'] == 0
