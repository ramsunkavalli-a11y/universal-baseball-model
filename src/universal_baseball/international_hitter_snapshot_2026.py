"""Strict 2026 snapshot readers; never certify completed overseas seasons."""
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from universal_baseball.npb_history import COUNTS, HEADERS, name_key, validate_counts


def npb_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    if not soup.title or not re.search('2026年度', soup.title.get_text()):
        raise ValueError('Wrong snapshot season')
    links = set()
    for a in soup.select('a[href]'):
        u = urlparse(urljoin('https://npb.jp/bis/2026/stats/', a['href']))
        if re.fullmatch(r'/bis/2026/stats/idb1_[a-z]+\.html', u.path):
            if u.netloc != 'npb.jp' or u.query or u.fragment:
                raise ValueError('Wrong first-team host/query')
            links.add(u.path)
    if len(links) != 12:
        raise ValueError('Need all twelve first-team club tables')
    return sorted(links)


def snapshot_date(html):
    text = BeautifulSoup(html, 'html.parser').get_text(' ', strip=True)
    dates = set(re.findall(r'(2026)年\s*(\d+)月\s*(\d+)日\s*現在', text))
    if len(dates) > 1:
        raise ValueError('Conflicting provider snapshot dates')
    return '-'.join(f'{int(x):02d}' if i else x for i, x in enumerate(next(iter(dates)))) if dates else None


def batting_rows(html):
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.get_text(' ', strip=True) if soup.title else ''
    m = re.match(r'^2026年度 (.+?) 個人打撃成績', title)
    if not m or any(t in title for t in ('ファーム', 'イースタン', 'ウエスタン', 'ポストシーズン')):
        raise ValueError('Wrong year or first-team scope')
    tables = soup.select('table.tablefix2')
    if len(tables) != 1 or tuple(name_key(c.get_text()) for c in tables[0].select('th')) != HEADERS[1:]:
        raise ValueError('Changed batting headers/layout')
    rows, seen = [], set()
    for tr in tables[0].find_all('tr'):
        cells = tr.find_all('td', recursive=False)
        if not cells: continue
        if len(cells) != 23: raise ValueError('Changed row length')
        markers = cells[0].find_all('sup')
        marker = markers[0].get_text(strip=True) if len(markers) == 1 else ''
        if len(markers) > 1 or marker not in ('', '*', '+'): raise ValueError('Unknown handedness')
        for node in markers: node.extract()
        name = cells[0].get_text(' ', strip=True); key = name_key(name)
        if not key or key in seen: raise ValueError('Missing/duplicate name')
        seen.add(key)
        numbers = [c.get_text(strip=True) for c in cells[1:20]]
        if not all(re.fullmatch(r'\d+', v) for v in numbers): raise ValueError('Noninteger count')
        r = dict(season=2026, team_name=m[1], player_name_ja=name, name_key=key,
                 bats={'': 'R', '*': 'L', '+': 'S'}[marker], **dict(zip(COUNTS, map(int, numbers), strict=True)))
        r['unenumerated_pa'] = validate_counts(r)
        den = {'avg': r['ab'], 'slg': r['ab'], 'obp': r['ab'] + r['bb'] + r['hbp'] + r['sf']}
        num = {'avg': r['hits'], 'slg': r['tb'], 'obp': r['hits'] + r['bb'] + r['hbp']}
        for k, cell in zip(('avg', 'slg', 'obp'), cells[20:23], strict=True):
            shown = float(cell.get_text(strip=True)); computed = num[k] / den[k] if den[k] else None
            if computed is not None and abs(shown - computed) > .000501: raise ValueError('Incorrect displayed rate')
            r['source_' + k] = shown; r[k] = computed
        rows.append(r)
    if not rows: raise ValueError('Empty batting table')
    return m[1], rows


def controls(rows, key):
    stable = lambda r: (str(r.get(key) or ''), str(r.get('team_name') or r.get('displayed_team') or ''), str(r.get('name_key') or ''))
    positive = [r for r in rows if r['pa'] > 0]
    zero = sorted((r for r in rows if r['pa'] == 0), key=stable)
    if not positive or not zero: raise ValueError('Declared source controls unavailable')
    return [('largest_PA', min(positive, key=lambda r: (-r['pa'], stable(r)))),
            ('smallest_positive_PA', min(positive, key=lambda r: (r['pa'], stable(r)))),
            ('zero_PA_row', zero[0])]


def subtotal(rows, key, value, cutoff):
    fields = ('pa', 'ab', 'hits', 'doubles', 'triples', 'hr', 'bb', 'ibb', 'hbp', 'so', 'sh', 'sf')
    eligible = [r for r in rows if value is not None and r.get(key) == value and 2024 <= r['season'] <= cutoff]
    counts = {f: sum(r[f] for r in eligible) for f in fields}
    events = {'K': counts['so'], 'UBB': counts['bb'] - counts['ibb'], 'HBP': counts['hbp'],
              '1B': counts['hits'] - counts['doubles'] - counts['triples'] - counts['hr'],
              '2B': counts['doubles'], '3B': counts['triples'], 'HR': counts['hr']}
    events['other'] = counts['pa'] - sum(events.values())
    if any(v < 0 for v in events.values()): raise ValueError('Invalid exclusive events')
    return dict(cutoff=cutoff, key_qualified=value is not None, source_rows=len(eligible), counts=counts,
                events=events, rates={k: v / counts['pa'] if counts['pa'] else None for k, v in events.items()})
