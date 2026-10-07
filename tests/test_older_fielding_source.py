import json
import pytest
from universal_baseball.older_fielding_source import decode,normalize,outs_from_baseball_innings


@pytest.mark.parametrize('value,want', [('884.1',2653),('1099.2',3299),('0.0',0),('0.2',2),('100',300)])
def test_outs_use_baseball_not_decimal_innings(value,want):
    assert outs_from_baseball_innings(value)==want


@pytest.mark.parametrize('value',['1.3','4.01','-2.0'])
def test_invalid_innings_rejected(value):
    with pytest.raises(ValueError):outs_from_baseball_innings(value)


def row():
    return dict(Season=2015,SeasonMin=2015,SeasonMax=2015,Position='SS',xMLBAMID=123,playerid=99,
        PlayerName='Example',Inn=500.1,TInn=500.33333333,RngR=3.,ErrR=-1.,ARM=None,DPR=2.,UZR=4.)


def page(rows,total=1,qual='0',year=2015):
    query=dict(season=year,season1=year,stats='fld',qual=qual)
    obj=dict(props=dict(pageProps=dict(qsContext=query,dehydratedState=dict(queries=[dict(queryKey=['leaders/major-league/data',query],
        state=dict(data=dict(data=rows,totalCount=total,status=200)))]))))
    return '<script id="__NEXT_DATA__" type="application/json">'+json.dumps(obj)+'</script>'


def test_complete_source_has_fixed_season():
    rows,meta=decode(page([row()]),2015)
    assert rows==[row()] and meta['total_count']==1


def test_pagination_qualification_wrong_season_and_current_year_fail():
    for text,year in [(page([row()],total=2),2015),(page([row()],qual='y'),2015),(page([row()]),2016),(page([row()]),2026)]:
        with pytest.raises(ValueError):decode(text,year)


def test_components_are_not_total_uzr_or_defense():
    n=normalize(dict(row(),Defense=1000))
    assert n['older_conversion_runs']==2 and n['UZR']==4 and n['component_sum_gap']==0 and n['decimal_innings_check']


def test_unknown_error_credit_is_not_zero():
    n=normalize(dict(row(),ErrR=None))
    assert n['older_conversion_runs'] is None and n['older_conversion_rate'] is None


def test_aggregate_outfield_and_catcher_not_range():
    assert normalize(dict(row(),Position='OF')) is None
    assert normalize(dict(row(),Position='C')) is None


def test_no_name_only_identity_join():
    with pytest.raises(ValueError):normalize(dict(row(),xMLBAMID=None))
