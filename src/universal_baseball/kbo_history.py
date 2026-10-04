"""Conservative joining and accounting for two official KBO batting groups."""
import re

from bs4 import BeautifulSoup

HEADERS1 = ['순위','선수명','팀명','AVG','G','PA','AB','R','H','2B','3B','HR','TB','RBI','SAC','SF']
HEADERS2 = ['순위','선수명','팀명','AVG','BB','IBB','HBP','SO','GDP','SLG','OBP','OPS','MH','RISP','PH-BA']
FIELDS1 = ('games','pa','ab','runs','hits','doubles','triples','hr','tb','rbi','sh','sf')
FIELDS2 = ('bb','ibb','hbp','so','gdp')


def player_id(href):
    found=re.fullmatch(r'/Record/(?:Player/HitterDetail/Basic|Retire/Hitter)\.aspx\?playerId=(\d+)',href)
    if found is None:
        raise ValueError('Unrecognized official KBO identity link')
    return found[1]


def parse_group(html,group):
    soup=BeautifulSoup(html,'html.parser')
    tables=soup.select('table.tData01')
    assert len(tables)==1
    headers=[x.get_text(' ',strip=True) for x in tables[0].select('thead th')]
    assert headers==(HEADERS1 if group==1 else HEADERS2)
    rows=[]
    for tr in tables[0].select('tbody tr'):
        cells=tr.find_all('td',recursive=False)
        if not cells:
            continue
        assert len(cells)==len(headers)
        link=cells[1].find('a')
        assert link is not None
        row=dict(kbo_id=player_id(link['href']),player_name_ko=cells[1].get_text(strip=True),
                 displayed_team=cells[2].get_text(strip=True),raw_avg=cells[3].get_text(strip=True))
        fields=FIELDS1 if group==1 else FIELDS2
        for index,field in enumerate(fields,start=4):
            value=cells[index].get_text(strip=True)
            assert re.fullmatch(r'\d+',value), (field,value)
            row[field]=int(value)
        if group==2:
            for index,field in [(9,'raw_slg'),(10,'raw_obp'),(11,'raw_ops')]:
                row[field]=cells[index].get_text(strip=True)
        rows.append(row)
    assert rows and len({r['kbo_id'] for r in rows})==len(rows)
    return rows


def validate(row):
    for field in FIELDS1+FIELDS2:
        assert isinstance(row[field],int) and row[field]>=0
    assert row['hits']<=row['ab'] and row['hits']+row['so']<=row['ab']
    assert row['doubles']+row['triples']+row['hr']<=row['hits']
    assert row['ibb']<=row['bb']
    assert row['tb']==row['hits']+row['doubles']+2*row['triples']+3*row['hr']
    residual=row['pa']-sum(row[k] for k in ('ab','bb','hbp','sh','sf'))
    assert residual>=0
    rates={'avg':row['hits']/row['ab'] if row['ab'] else None,
           'slg':row['tb']/row['ab'] if row['ab'] else None}
    denominator=sum(row[k] for k in ('ab','bb','hbp','sf'))
    rates['obp']=sum(row[k] for k in ('hits','bb','hbp'))/denominator if denominator else None
    for rate,value in rates.items():
        published=row['raw_'+rate]
        if value is not None:
            assert re.fullmatch(r'\d+\.\d{3}',published) and abs(float(published)-value)<=.000501,(rate,published,value)
        else:
            assert published in ('0.000','-',''), (rate,published)
    return dict(row,unenumerated_pa=residual,**rates)


def join_groups(first,second,year):
    a={r['kbo_id']:r for r in first}; b={r['kbo_id']:r for r in second}
    assert len(a)==len(first) and len(b)==len(second)
    assert set(a)==set(b), 'Stat-group coverage differs; do not inner-join away missing players'
    rows=[]
    for key in sorted(a):
        for field in ('player_name_ko','displayed_team','raw_avg'):
            assert a[key][field]==b[key][field], ('Stat-group identity mismatch',key,field)
        rows.append(dict(validate(dict(a[key],**b[key])),season=year,
                         displayed_team_is_exposure_allocation=False,
                         current_retirement_path_used_as_feature=False,mlb_translation_fitted=False))
    return rows
