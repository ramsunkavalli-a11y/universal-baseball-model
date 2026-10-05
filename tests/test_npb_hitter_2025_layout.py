import pytest
from universal_baseball.npb_history import HEADERS,COUNTS
from universal_baseball.npb_hitter_2025_layout import batting_2025_rows


def body(year=2025,marker='*'):
    values=dict(games=10,pa=50,ab=40,runs=5,hits=10,doubles=2,triples=1,hr=1,tb=17,
                rbi=5,sb=1,cs=0,sh=1,sf=1,bb=7,ibb=1,hbp=1,so=12,gdp=0)
    headers=''.join('<th>'+h+'</th>' for h in HEADERS[1:])
    counts=''.join('<td>'+str(values[k])+'</td>' for k in COUNTS)
    rates='<td>.250</td><td>.425</td><td>.367</td>'
    superscript='<sup>'+marker+'</sup>' if marker else ''
    return f'<title>{year}年度 Test 個人打撃成績</title><table class="tablefix2"><tr>{headers}</tr><tr><td>{superscript}Name</td>{counts}{rates}</tr></table>'


@pytest.mark.parametrize('marker,bats',[('*','L'),('+','S'),('','R')])
def test_structured_marker_not_part_of_name(marker,bats):
    team,rows=batting_2025_rows(body(marker=marker))
    assert team=='Test' and rows[0]['name_key']=='Name' and rows[0]['bats']==bats
    assert rows[0]['pa']==50 and rows[0]['so']==12


@pytest.mark.parametrize('html',[body(2024),body(marker='?'),body().replace('<th>打席</th>','<th>Wrong</th>'),
                               body().replace('<td>17</td>','<td>18</td>')])
def test_changed_source_fails_closed(html):
    with pytest.raises(ValueError):batting_2025_rows(html)
