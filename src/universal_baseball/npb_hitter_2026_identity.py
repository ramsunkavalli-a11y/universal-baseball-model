"""Current-year identity only; ignore role, rights and transfer metadata."""
from collections import defaultdict
from datetime import date
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from universal_baseball.npb_history import name_key


def listings(html):
    soup = BeautifulSoup(html, 'html.parser'); result = {}
    for a in soup.select('a[href]'):
        u = urlparse(urljoin('https://npb.jp/bis/teams/', a['href']))
        if re.fullmatch(r'/bis/teams/rst_[a-z]+\.html', u.path):
            if u.netloc != 'npb.jp' or u.query or u.fragment: raise ValueError('Wrong identity host/query')
            key = name_key(a.get_text())
            if key in result and result[key] != u.path: raise ValueError('Conflicting club listing')
            result[key] = u.path
    if len(result) != 12: raise ValueError('Need twelve current club identity listings')
    return result


def names(html, team):
    soup = BeautifulSoup(html, 'html.parser')
    title = name_key(soup.title.get_text()) if soup.title else ''
    if name_key(team) + '2026年度選手一覧' not in title: raise ValueError('Wrong club or year')
    found = defaultdict(set); dates = {}
    for tr in soup.select('tr.rosterPlayer'):
        cells = tr.find_all('td', recursive=False)
        a = cells[1].find('a') if len(cells) >= 3 else None
        match = re.fullmatch(r'/bis/players/(\d+)\.html', a['href']) if a else None
        if not match: raise ValueError('Unqualified structured player identity')
        key = match[1]; name = name_key(a.get_text()); raw = cells[2].get_text(strip=True)
        if not name or not re.fullmatch(r'\d{4}\.\d{2}\.\d{2}', raw): raise ValueError('Malformed static identity')
        dob = date(*map(int, raw.split('.'))).isoformat()
        if key in dates and dates[key] != dob: raise ValueError('Conflicting static birth dates')
        dates[key] = dob; found[name].add(key)
    if not found: raise ValueError('Empty structured identity listing')
    return dict(found), dates
