from pathlib import Path
import importlib

from bs4 import BeautifulSoup
import pytest

from universal_baseball.kbo_history import FIELDS1,FIELDS2


@pytest.fixture
def review(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/'scripts'))
    return importlib.import_module('review_kbo_hitting_source')


def source_html(year=2023,future_hits=999):
    headers=['YEAR','TEAM','AVG','G','AB','R','H','2B','3B','HR','TB','RBI','SB','CS','BB','HBP','SO','GIDP','E']
    values=['TEST','0.500',1,4,0,2,0,0,1,5,1,0,0,1,0,1,0,0]
    row='<tr><th scope="row">'+str(year)+'</th>'+''.join('<td>'+str(v)+'</td>' for v in values)+'</tr>'
    future='<tr><th scope="row">2099</th>'+''.join('<td>'+str(future_hits)+'</td>' for _ in values)+'</tr>'
    return BeautifulSoup('<ul><li>Name : TEST Player</li><li>Born : 20/08/1998</li>'
                         '<li>Salary : future salary must not be used</li></ul>'
                         '<a href="/Teams/PlayerInfoHitter/Summary.aspx?pcode=00001">Summary</a>'
                         '<table><thead><tr>'+''.join('<th>'+h+'</th>' for h in headers)+
                         '</tr></thead><tbody>'+row+future+'</tbody></table>','html.parser')


def source_row():
    row={k:0 for k in FIELDS1+FIELDS2}
    row.update(kbo_id='00001',season=2023,games=1,pa=5,ab=4,hits=2,hr=1,tb=5,rbi=1,bb=1,so=1)
    return row


def test_year_row_heading_is_counted_and_future_line_does_not_change_check(review,monkeypatch):
    monkeypatch.setattr(review.probe,'request',lambda *a:(source_html(),{'url':'synthetic'}))
    first=review.english_case(None,source_row(),None)
    assert first['english_origin_count_fields_checked']==13
    assert first['birth_date']=='1998-08-20'
    assert not first['historical_salary_position_status_used']
    monkeypatch.setattr(review.probe,'request',lambda *a:(source_html(future_hits=2),{'url':'synthetic'}))
    assert review.english_case(None,source_row(),None)==first


def test_missing_origin_is_not_empty_performance(review,monkeypatch):
    monkeypatch.setattr(review.probe,'request',lambda *a:(source_html(year=2022),{'url':'synthetic'}))
    with pytest.raises(AssertionError):
        review.english_case(None,source_row(),None)


def test_count_disagreement_fails(review,monkeypatch):
    monkeypatch.setattr(review.probe,'request',lambda *a:(source_html(),{'url':'synthetic'}))
    row=source_row(); row['hits']=1
    with pytest.raises(AssertionError):
        review.english_case(None,row,None)
