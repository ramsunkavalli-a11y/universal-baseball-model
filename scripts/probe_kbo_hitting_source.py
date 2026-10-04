"""Bounded public-form historical source probe; no forecasts or model fitting."""
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import requests

from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT/'data/quarantine/kbo-hitting-source-probe'
OUT = ROOT/'reports/generated/kbo-hitting-source-probe'
BASE = 'https://www.koreabaseball.com'
CONTRACT = ROOT/'docs/hitter-kbo-source-probe-contract.md'


def write_new(path, value):
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)+'\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_text(encoding='utf8') == text, 'Preserve prior receipt'
    else:
        path.write_text(text, encoding='utf8', newline='\n')


def request(session, name, url, payload=None):
    path = RAW/(name+'.html')
    meta_path = RAW/(name+'.json')
    method = 'POST' if payload is not None else 'GET'
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding='utf8'))
        assert meta['method'] == method and meta['url'] == url
        assert sha256_file(path) == meta['sha256']
        assert meta['http_status'] == 200 and meta['returned_url'] == url, 'Error/redirect is not record data'
        return BeautifulSoup(path.read_bytes(), 'html.parser'), meta
    assert not path.exists(), 'Unreceipted source capture'
    time.sleep(1)
    response = session.request(method, url, data=payload, timeout=(10,40))
    RAW.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)
    meta = dict(method=method, url=url, returned_url=response.url, http_status=response.status_code,
                sha256=sha256_file(path), captured_utc=datetime.now(timezone.utc).isoformat(),
                request_sha256=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest(),
                historical_publication_vintage_verified=False, public_redistribution_approved=False)
    if payload is not None:
        write_new(RAW/(name+'.request.json'),payload)
    write_new(meta_path,meta)
    response.raise_for_status()
    assert response.url == url, ('Error/redirect is not record data', response.url)
    return BeautifulSoup(response.content,'html.parser'), meta


def form_state(soup):
    form = soup.find('form')
    assert form is not None and form.get('method','').lower() == 'post'
    state = {x['name']:x.get('value','') for x in form.select('input[name][type=hidden]')}
    for select in form.select('select[name]'):
        options = select.find_all('option')
        chosen = select.find('option', selected=True) or options[0]
        state[select['name']] = chosen.get('value','')
    return urljoin(BASE+'/Record/Player/HitterBasic/Basic1.aspx',form['action']),state


def control(state, suffix):
    keys = [k for k in state if k.endswith(suffix)]
    assert len(keys) == 1, (suffix,keys)
    return keys[0]


def inspect(soup, year):
    _, state = form_state(soup)
    assert state[control(state,'$ddlSeason$ddlSeason')] == str(year)
    assert state[control(state,'$ddlSeries$ddlSeries')] == '0'
    for suffix in ('$ddlTeam$ddlTeam','$ddlPos$ddlPos','$ddlSituation$ddlSituation','$ddlSituationDetail$ddlSituationDetail'):
        assert state[control(state,suffix)] == ''
    tables = soup.select('table.tData01')
    assert len(tables) == 1
    table = tables[0]
    headers = [x.get_text(' ',strip=True) for x in table.select('thead th')]
    rows = []
    for tr in table.select('tbody tr'):
        cells = tr.find_all('td',recursive=False)
        if not cells:
            continue
        link = cells[1].find('a')
        assert link is not None
        found = re.fullmatch(r'/Record/(?:Player/HitterDetail/Basic|Retire/Hitter)\.aspx\?playerId=(\d+)',link['href'])
        assert found is not None
        values = [c.get_text(' ',strip=True) for c in cells]
        assert len(values) == len(headers)
        rows.append(dict(kbo_id=found[1],values=values))
    page_links = [dict(label=a.get_text(' ',strip=True),href=a.get('href'))
                  for a in soup.find_all('a') if '$ucPager$' in (a.get('href') or '')]
    return dict(year=year,headers=headers,rows=rows,page_links=page_links,
                order_column=state[control(state,'$hfOrderByCol')],
                order_direction=state[control(state,'$hfOrderBy')])


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--fresh-session',action='store_true')
    args=parser.parse_args()
    prefix='fresh-' if args.fresh_session else ''
    output=OUT/(prefix+'probe.json')
    assert not output.exists(), 'Do not overwrite a completed probe'
    session=requests.Session()
    session.headers['User-Agent']='UBM historical research; low-rate public season-form probe'
    url=BASE+'/Record/Player/HitterBasic/Basic1.aspx'
    initial,meta=request(session,prefix+'initial-basic1',url)
    links=[dict(text=a.get_text(' ',strip=True),href=a.get('href')) for a in initial.find_all('a')
           if '/Record/Player/HitterBasic/' in (a.get('href') or '')]
    selections,receipts=[],[meta]
    for year in (2005,2015,2024):
        action,state=form_state(initial)
        season_key=control(state,'$ddlSeason$ddlSeason')
        assert initial.find('select',attrs={'name':season_key}).find('option',value=str(year)) is not None
        state[season_key]=str(year)
        state['__EVENTTARGET']=season_key
        state['__EVENTARGUMENT']=''
        historic,meta=request(session,prefix+f'{year}-basic1-average',action,state)
        selections.append(inspect(historic,year)); receipts.append(meta)
        action,state=form_state(historic)
        sort_key=control(state,'$hfOrderByCol')
        prefix=sort_key.removesuffix('hfOrderByCol')
        script='\n'.join(x.get_text() for x in historic.find_all('script'))
        assert prefix+'lbtnOrderBy' in script
        assert historic.find('a',attrs={'href':"javascript:sort('PA_CN');"}) is not None
        state[sort_key]='PA_CN'; state[control(state,'$hfOrderBy')]='DESC'
        state['__EVENTTARGET']=prefix+'lbtnOrderBy'; state['__EVENTARGUMENT']=''
        historic,meta=request(session,prefix+f'{year}-basic1-pa',action,state)
        selections.append(inspect(historic,year)); receipts.append(meta)
        print(json.dumps({k:v for k,v in selections[-1].items() if k!='rows'},ensure_ascii=False),flush=True)
        print('Returned rows',len(selections[-1]['rows']),'PA range', [r['values'][5] for r in selections[-1]['rows']][:3],flush=True)
    write_new(output,dict(contract_sha256=sha256_file(CONTRACT),code_sha256=sha256_file(Path(__file__)),
                                  captures=receipts,observed_group_links=links,selections=selections,
                                  coverage_qualified=False, forecasts_changed=False, new_fits=0))


if __name__=='__main__':
    main()
