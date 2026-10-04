import pytest

from universal_baseball.npb_history import (
    COUNTS, HEADERS, attach_npb_ids, batting_rows, history_at, name_key,
    roster_names, season_links, validate_counts,
)


def fixture_html(values=None, season=2017):
    values = values or [10, 40, 30, 3, 10, 2, 0, 1, 15, 4, 1, 0, 1, 1, 6, 1, 2, 5, 0]
    heads = ''.join(f'<th>{h}</th>' for h in HEADERS)
    cells = ['*', '架空　選手'] + list(map(str, values)) + ['.333', '.500', '.462']
    body = ''.join(f'<td>{x}</td>' for x in cells)
    return f'<title>{season}年度 架空球団 個人打撃成績（パシフィック・リーグ）</title><table><tr>{heads}</tr><tr class="ststats">{body}</tr></table>'


def test_complete_counts_and_rates():
    team, rows = batting_rows(fixture_html(), 2017)
    assert team == '架空球団'
    row = rows[0]
    assert row['pa'] == 40 and row['unenumerated_pa'] == 0
    assert row['avg'] == 10/30 and row['obp'] == 18/39
    assert row['bats'] == 'L'


def test_zero_pa_is_undefined_not_zero_talent():
    html = fixture_html([0]*len(COUNTS)).replace('.333', '.000').replace('.500', '.000').replace('.462', '.000')
    row = batting_rows(html, 2017)[1][0]
    assert row['avg'] is None and row['slg'] is None and row['obp'] is None


def test_wrong_year_and_farm_fail():
    with pytest.raises(ValueError, match='Wrong season'):
        batting_rows(fixture_html(), 2018)
    with pytest.raises(ValueError, match='first-team'):
        batting_rows(fixture_html().replace('個人打撃成績', 'ファーム個人打撃成績'), 2017)


def test_column_order_and_total_bases_fail_closed():
    with pytest.raises(ValueError, match='headers'):
        batting_rows(fixture_html().replace('<th>二塁打</th>', '<th>三塁打</th>'), 2017)
    values = [10, 40, 30, 3, 10, 2, 0, 1, 16, 4, 1, 0, 1, 1, 6, 1, 2, 5, 0]
    with pytest.raises(ValueError, match='Total bases'):
        batting_rows(fixture_html(values), 2017)


def test_pa_residual_visible_and_negative_invalid():
    row = dict(zip(COUNTS, [10, 41, 30, 3, 10, 2, 0, 1, 15, 4, 1, 0, 1, 1, 6, 1, 2, 5, 0], strict=True))
    assert validate_counts(row) == 1
    row['pa'] = 39
    with pytest.raises(ValueError, match='Negative'):
        validate_counts(row)


def test_identity_no_fuzzy_merge_and_ambiguity_retained():
    rows = batting_rows(fixture_html(), 2017)[1]
    assert name_key('架空　選手') == name_key('架空 選手')
    assert attach_npb_ids(rows, {'架空選手': {'001'}})[0]['npb_id'] == '001'
    assert attach_npb_ids(rows, {'架空選手': {'001', '002'}})[0]['npb_identity_status'] == 'ambiguous'
    assert attach_npb_ids(rows, {'架空選手改名': {'001'}})[0]['npb_id'] is None


def test_roster_year_scope_and_structured_id():
    html = '<title>架空球団(2017) | 全ての選手</title><a class="player_unit_1 old_player" href="/bis/players/001.html"><dd class="name">架空　選手</dd><dd class="note">Later note</dd></a>'
    assert roster_names(html, 2017, '架空球団') == {'架空選手': {'001'}}
    with pytest.raises(ValueError, match='Wrong team/year'):
        roster_names(html, 2018, '架空球団')


def test_future_results_cannot_change_cutoff_history():
    row = attach_npb_ids(batting_rows(fixture_html(), 2017)[1], {'架空選手': {'001'}})[0]
    future = dict(row, season=2018, pa=900, hr=100)
    before = history_at([row], '001', 2017)
    assert before == history_at([row, future], '001', 2017)
    assert before['ubb_rate'] == 5/40
    assert before['mlb_translation_fitted'] is False


def test_full_season_enumeration_not_qualified_leaders():
    html = '<title>2017年度 公式戦成績</title>' + ''.join(
        f'<a href="/bis/2017/stats/idb1_{chr(97+i)}.html">team</a>' for i in range(12))
    assert len(season_links(html, 2017)) == 12
    relative = html.replace('/bis/2017/stats/', '')
    assert season_links(relative+html, 2017) == season_links(html, 2017)
    with pytest.raises(ValueError, match='twelve'):
        season_links(html.replace('idb1_a', 'idb2_a'), 2017)
    with pytest.raises(ValueError, match='scope'):
        season_links(html, 2026)
