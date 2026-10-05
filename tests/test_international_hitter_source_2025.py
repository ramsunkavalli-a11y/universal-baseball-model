import pytest
from universal_baseball.international_hitter_source_2025 import npb_2025_links,recent_counts


def html(year=2025,host='https://npb.jp',count=12):
    return f'<title>{year}年度</title>'+''.join(
        f'<a href="{host}/bis/2025/stats/idb1_{chr(97+i)}.html">x</a>' for i in range(count))


def test_explicit_2025_first_team_links():
    assert len(npb_2025_links(html()))==12


@pytest.mark.parametrize('body',[html(2024),html(host='https://example.com'),html(count=11)])
def test_wrong_source_cannot_pass(body):
    with pytest.raises(ValueError):
        npb_2025_links(body)


def test_farm_does_not_fill_missing_first_team():
    with pytest.raises(ValueError):
        npb_2025_links(html(count=11)+'<a href="/bis/2025/stats/idb2_a.html">farm</a>')


def row(year=2025,pa=100):
    return dict(season=year,player_id=1,pa=pa,ab=80,hits=20,doubles=3,triples=1,
                hr=2,bb=15,ibb=2,hbp=1,so=20,sh=1,sf=2)


def test_mutated_future_history_ignored():
    a=recent_counts([row()],1,2025)
    assert a==recent_counts([row(),row(2026,10000)],1,2025)
    assert sum(a['events'].values())==100
    assert a['events']['1B']==14 and a['events']['UBB']==13


def test_empty_rate_unobserved_not_zero():
    a=recent_counts([],1,2025)
    assert all(v is None for v in a['event_rates'].values())


def test_invalid_counts_rejected():
    with pytest.raises(ValueError):
        recent_counts([row(pa=5)],1,2025)
