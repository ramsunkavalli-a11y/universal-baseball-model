"""Complete paging and both basic groups for fixed source-review seasons."""
from collections import Counter
from datetime import datetime,timezone
import json
from pathlib import Path
import re

from bs4 import BeautifulSoup
import polars as pl
import requests

import probe_kbo_hitting_source as probe
from universal_baseball.kbo_history import parse_group,join_groups,FIELDS1,FIELDS2
from universal_baseball.storage import sha256_file

ROOT=probe.ROOT
OUT=ROOT/'reports/generated/kbo-hitting-source-probe'
SEASONS=(2005,2015,2020,2023,2024)


def state(soup,url):
    action,values=probe.form_state(soup)
    # Relative Basic2 action must resolve against its actual directory/page.
    from urllib.parse import urljoin
    return urljoin(url,soup.find('form')['action']),values


def post(session,soup,url,name,event,updates=None):
    action,values=state(soup,url)
    values.update(updates or {})
    values['__EVENTTARGET']=event; values['__EVENTARGUMENT']=''
    return probe.request(session,name,action,values)


def page_number(soup):
    _,values=probe.form_state(soup)
    return int(values[probe.control(values,'$hfPage')])


def pager_event(soup,button):
    events=[]
    for a in soup.find_all('a',href=True):
        found=re.fullmatch(r"javascript:__doPostBack\('([^']+\$ucPager\$"+re.escape(button)+r")',''\)",a['href'])
        if found:
            events.append(found[1])
    assert len(events)==1,(button,events)
    return events[0]


def check_controls(soup,year,column):
    inspected=probe.inspect(soup,year)
    assert inspected['order_column']==column and inspected['order_direction']=='DESC'


def group(session,year,number,attempt):
    url=probe.BASE+f'/Record/Player/HitterBasic/Basic{number}.aspx'
    stem=f'qualification-{attempt}-{year}-group{number}'
    initial,meta=probe.request(session,stem+'-initial',url)
    receipts=[meta]
    _,values=state(initial,url)
    key=probe.control(values,'$ddlSeason$ddlSeason')
    historic,meta=post(session,initial,url,stem+'-year',key,{key:str(year)})
    receipts.append(meta)
    # Each column comes from a published sortable count header, not a hidden API.
    column='PA_CN' if number==1 else 'BB_CN'
    assert historic.find('a',href=f"javascript:sort('{column}');") is not None
    _,values=state(historic,url)
    key=probe.control(values,'$hfOrderByCol')
    prefix=key.removesuffix('hfOrderByCol')
    assert historic.find('a',href=f"javascript:__doPostBack('{prefix}lbtnOrderBy','')") is not None
    current,meta=post(session,historic,url,stem+'-count-first',prefix+'lbtnOrderBy',
                      {key:column,probe.control(values,'$hfOrderBy'):'DESC'})
    receipts.append(meta); check_controls(current,year,column)
    assert page_number(current)==1
    first_rows=parse_group(str(current),number)
    last,meta=post(session,current,url,stem+'-last-probe',pager_event(current,'btnLast'))
    receipts.append(meta); check_controls(last,year,column)
    last_page=page_number(last)
    assert 1<=last_page<=100
    last_rows=parse_group(str(last),number)
    if last_page==1:
        assert first_rows==last_rows
        return first_rows,receipts,dict(group=number,last_page=1,rows=len(first_rows))
    current,meta=post(session,last,url,stem+'-first-replay',pager_event(last,'btnFirst'))
    receipts.append(meta); check_controls(current,year,column)
    assert page_number(current)==1 and parse_group(str(current),number)==first_rows
    all_rows=list(first_rows)
    for number_page in range(2,last_page+1):
        # Numbered controls are positions within a five-page block, not global indices.
        matches=[]
        for a in current.find_all('a',href=True):
            if a.get_text(strip=True)==str(number_page):
                found=re.fullmatch(r"javascript:__doPostBack\('([^']+\$ucPager\$btnNo\d+)',''\)",a['href'])
                if found:
                    matches.append(found[1])
        assert len(matches)<=1
        event=matches[0] if matches else pager_event(current,'btnNext')
        current,meta=post(session,current,url,stem+f'-page{number_page}',event)
        receipts.append(meta); check_controls(current,year,column)
        assert page_number(current)==number_page, 'Pager did not advance to the requested global page'
        rows=parse_group(str(current),number)
        assert len(rows)==30 if number_page<last_page else 1<=len(rows)<=30
        if number_page==last_page:
            assert rows==last_rows
        all_rows.extend(rows)
        print(f'{year} group {number}: page {number_page}/{last_page}',flush=True)
    assert len(all_rows)==(last_page-1)*30+len(last_rows)
    assert len({r['kbo_id'] for r in all_rows})==len(all_rows)
    return all_rows,receipts,dict(group=number,last_page=last_page,rows=len(all_rows))


def team_rows(session,year,number,attempt):
    url=probe.BASE+f'/Record/Team/Hitter/Basic{number}.aspx'
    stem=f'qualification-{attempt}-{year}-teams-group{number}'
    initial,meta=probe.request(session,stem+'-initial',url)
    _,values=state(initial,url)
    key=probe.control(values,'$ddlSeason$ddlSeason')
    soup,second=post(session,initial,url,stem+'-year',key,{key:str(year)})
    _,values=state(soup,url)
    assert values[key]==str(year) and values[probe.control(values,'$ddlSeries$ddlSeries')]=='0'
    tables=soup.select('table.tData')
    assert len(tables)==1
    headers=[x.get_text(strip=True) for x in tables[0].select('thead th')]
    rows=[]
    for tr in tables[0].select('tbody tr'):
        cells=[x.get_text(strip=True) for x in tr.find_all('td',recursive=False)]
        assert len(cells)==len(headers)
        rows.append(dict(zip(headers,cells,strict=True)))
    assert len(rows)==(8 if year==2005 else 10)
    return rows,[meta,second]


def main():
    assert not (OUT/'qualification.json').exists(), 'Keep completed qualification immutable'
    original=json.loads((OUT/'fresh-probe.json').read_text(encoding='utf8'))
    assert original['code_sha256']==sha256_file(Path(probe.__file__))
    # A new attempt never uses another session's cached form state.
    attempt=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    receipts,all_rows,checks=[],[],[]
    for year in SEASONS:
        session=requests.Session()
        session.headers['User-Agent']='UBM historical research; low-rate published public form collection'
        first,meta,c1=group(session,year,1,attempt); receipts.extend(meta)
        second,meta,c2=group(session,year,2,attempt); receipts.extend(meta)
        joined=join_groups(first,second,year)
        totals1,meta=team_rows(session,year,1,attempt); receipts.extend(meta)
        totals2,meta=team_rows(session,year,2,attempt); receipts.extend(meta)
        count_headers={**dict(zip(FIELDS1,['G','PA','AB','R','H','2B','3B','HR','TB','RBI','SAC','SF'])),
                       **dict(zip(FIELDS2,['BB','IBB','HBP','SO','GDP']))}
        for field,header in count_headers.items():
            if field=='games':
                continue  # Player appearances do not sum to team games.
            teams=totals1 if field in FIELDS1 else totals2
            assert all(re.fullmatch(r'\d+',t[header]) for t in teams)
            expected=sum(int(t[header]) for t in teams)
            observed=sum(r[field] for r in joined)
            assert expected==observed,('Player/team totals disagree',year,field,expected,observed)
        checks.append(dict(season=year,groups=[c1,c2],rows=len(joined),
                           pa=sum(r['pa'] for r in joined),zero_pa=sum(r['pa']==0 for r in joined),
                           small_pa=sum(0<r['pa']<=10 for r in joined),
                           unenumerated_pa=sum(r['unenumerated_pa'] for r in joined),
                           team_count_fields_reconciled=16,all_displayed_players_preserved=True))
        all_rows.extend(joined)
        print('Qualified season',checks[-1],flush=True)
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/'qualified-seasons.parquet'
    assert not path.exists()
    pl.DataFrame(all_rows).sort('season','kbo_id').write_parquet(path)
    probe.write_new(OUT/'qualification.json',dict(attempt=attempt,seasons=list(SEASONS),
        captures=receipts,checks=checks,rows=len(all_rows),data_sha256=sha256_file(path),
        code_sha256=sha256_file(Path(__file__)),parser_sha256=sha256_file(ROOT/'src/universal_baseball/kbo_history.py'),
        original_probe_sha256=sha256_file(OUT/'fresh-probe.json'),
        player_walkthrough_status='pending',coverage_qualified=True,MLB_identity_links_qualified=False,
        forecasts_changed=False,new_fits=0,protected_2026_opened=False))


if __name__=='__main__':
    main()
