"""Explicit new source boundary; original historical parsers stay sealed."""
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


def npb_2025_links(html):
    soup=BeautifulSoup(html,'html.parser')
    if soup.title is None or not re.search(r'2025年度',soup.title.get_text()):
        raise ValueError('Wrong NPB season index')
    links=set()
    for a in soup.select('a[href]'):
        u=urlparse(urljoin('https://npb.jp/bis/2025/stats/',a['href']))
        if re.fullmatch(r'/bis/2025/stats/idb1_[a-z]+\.html',u.path):
            if u.netloc!='npb.jp' or u.query or u.fragment:
                raise ValueError('Unqualified first-team source URL')
            links.add(u.path)
    if len(links)!=12:
        raise ValueError(f'Expected twelve first-team tables, got {len(links)}')
    return sorted(links)


def recent_counts(rows,player_id,origin,*,start=2023):
    """Source counts only; future records cannot change origin history."""
    fields=('pa','ab','hits','doubles','triples','hr','bb','ibb','hbp','so','sh','sf')
    selected=[r for r in rows if r.get('player_id')==player_id and start<=r['season']<=origin]
    totals={k:sum(r[k] for r in selected) for k in fields}
    pa=totals['pa']
    events={'K':totals['so'],'UBB':totals['bb']-totals['ibb'],'HBP':totals['hbp'],
        '1B':totals['hits']-totals['doubles']-totals['triples']-totals['hr'],
        '2B':totals['doubles'],'3B':totals['triples'],'HR':totals['hr']}
    events['other']=pa-sum(events.values())
    if any(x<0 for x in events.values()):
        raise ValueError('Invalid exclusive event counts')
    return dict(player_id=player_id,origin=origin,counts=totals,events=events,
        event_rates={k:v/pa if pa else None for k,v in events.items()},
        observed_positive_seasons=sorted({r['season'] for r in selected if r['pa']>0}),
        selected_source_rows=len(selected),mlb_translation_fitted=False)
