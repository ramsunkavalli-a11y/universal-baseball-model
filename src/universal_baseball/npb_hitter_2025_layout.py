"""Strict reader for the new 2025 table; original 2005-24 parser unchanged."""
import re
from bs4 import BeautifulSoup
from universal_baseball.npb_history import COUNTS,HEADERS,name_key,validate_counts


def batting_2025_rows(html):
    soup=BeautifulSoup(html,'html.parser')
    title=soup.title.get_text(' ',strip=True) if soup.title else ''
    match=re.match(r'^2025年度 (.+?) 個人打撃成績',title)
    if not match or any(x in title for x in ['ファーム','イースタン','ウエスタン']):
        raise ValueError('Wrong year or farm table')
    tables=soup.select('table.tablefix2')
    if len(tables)!=1:
        raise ValueError('Expected one 2025 batting table')
    table=tables[0]
    if tuple(name_key(c.get_text()) for c in table.select('th'))!=HEADERS[1:]:
        raise ValueError('Changed 2025 batting headers')
    rows=[];seen=set()
    for tr in table.find_all('tr'):
        cells=tr.find_all('td',recursive=False)
        if not cells:continue
        if len(cells)!=23:raise ValueError('Changed 2025 row length')
        markers=cells[0].find_all('sup')
        marker=markers[0].get_text(strip=True) if len(markers)==1 else ''
        if len(markers)>1 or marker not in ['', '*','+']:
            raise ValueError('Unknown handedness superscript')
        for m in markers:m.extract()
        name=cells[0].get_text(' ',strip=True);key=name_key(name)
        if not key or key in seen:raise ValueError('Missing or duplicate name')
        seen.add(key)
        numbers=[c.get_text(strip=True) for c in cells[1:20]]
        if not all(re.fullmatch(r'\d+',n) for n in numbers):raise ValueError('Noninteger count')
        r=dict(season=2025,team_name=match[1],player_name_ja=name,name_key=key,
               bats={'':'R','*':'L','+':'S'}[marker],**dict(zip(COUNTS,map(int,numbers),strict=True)))
        r['unenumerated_pa']=validate_counts(r)
        den={'avg':r['ab'],'slg':r['ab'],'obp':r['ab']+r['bb']+r['hbp']+r['sf']}
        num={'avg':r['hits'],'slg':r['tb'],'obp':r['hits']+r['bb']+r['hbp']}
        for k,cell in zip(['avg','slg','obp'],cells[20:23],strict=True):
            shown=float(cell.get_text(strip=True));calculated=num[k]/den[k] if den[k] else None
            if calculated is not None and abs(shown-calculated)>.000501:raise ValueError('Incorrect displayed rate')
            r['source_'+k]=shown;r[k]=calculated
        rows.append(r)
    if not rows:raise ValueError('Empty first-team table')
    return match[1],rows
