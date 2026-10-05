"""Review only counting fields, including traded players' annual totals."""
from bs4 import BeautifulSoup

FIELDS={'games':'G','ab':'AB','runs':'R','hits':'H','doubles':'2B','triples':'3B',
        'hr':'HR','tb':'TB','rbi':'RBI','bb':'BB','hbp':'HBP','so':'SO','gdp':'GIDP'}


def annual_counts(html,year):
    soup=BeautifulSoup(html,'html.parser')
    tables=[t for t in soup.find_all('table') if [x.get_text(strip=True) for x in t.select('thead th')][:3]==['YEAR','TEAM','AVG']]
    if len(tables)!=1:raise ValueError('Expected one English annual record table')
    headers=[x.get_text(strip=True) for x in tables[0].select('thead th')]
    if set(FIELDS.values())-set(headers):raise ValueError('Missing shared count fields')
    rows=[]
    for tr in tables[0].select('tbody tr'):
        cells=[x.get_text(strip=True) for x in tr.find_all(['td','th'],recursive=False)]
        if not cells or cells[0]!=str(year):continue
        if len(cells)!=len(headers):raise ValueError('Changed annual columns')
        rows.append(dict(zip(headers,cells,strict=True)))
    if not rows:raise ValueError('Requested completed year absent')
    totals=[r for r in rows if r['TEAM'].upper() in ['TOTAL','TOT','합계','계']]
    parts=[r for r in rows if r not in totals]
    if len(totals)>1:raise ValueError('Conflicting annual totals')
    def counts(r):
        a={field:int(r[header]) for field,header in FIELDS.items()}
        if any(v<0 for v in a.values()):raise ValueError('Negative count')
        return a
    combined={field:sum(counts(r)[field] for r in parts) for field in FIELDS}
    if totals:
        total=counts(totals[0])
        if parts and total!=combined:raise ValueError('Team stints differ from annual total')
        combined=total
    return dict(counts=combined,source_rows=rows,team_stint_rows=len(parts),
                explicit_total_used=bool(totals),rates_summed_or_averaged=False)
