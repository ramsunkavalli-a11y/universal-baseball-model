import pytest
from universal_baseball.kbo_english_annual_counts import annual_counts,FIELDS


def html(rows):
    headers=['YEAR','TEAM','AVG',*FIELDS.values()]
    return '<table><thead><tr>'+''.join('<th>'+h+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join(
        '<tr>'+''.join('<td>'+str(v)+'</td>' for v in [2025,team,'.250',*[n]*len(FIELDS)])+'</tr>' for team,n in rows)+'</tbody></table>'


def test_traded_players_sum_counts_not_rates():
    r=annual_counts(html([('LG',2),('KT',3)]),2025)
    assert r['counts']['ab']==5 and r['team_stint_rows']==2
    assert not r['rates_summed_or_averaged']


def test_explicit_total_not_counted_twice():
    r=annual_counts(html([('LG',2),('KT',3),('TOTAL',5)]),2025)
    assert r['counts']['ab']==5 and r['explicit_total_used']


def test_disagreeing_total_rejected():
    with pytest.raises(ValueError):annual_counts(html([('LG',2),('TOTAL',3)]),2025)


def test_other_year_not_invented_zero():
    with pytest.raises(ValueError):annual_counts(html([('LG',2)]),2024)
