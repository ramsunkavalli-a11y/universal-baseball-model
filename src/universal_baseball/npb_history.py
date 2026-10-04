"""Qualified NPB season inputs, not league translations or arrival labels."""
from collections import defaultdict
from datetime import date
from io import BytesIO
from pathlib import Path
import re
from zipfile import ZipFile
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import polars as pl

COUNTS = ('games', 'pa', 'ab', 'runs', 'hits', 'doubles', 'triples', 'hr',
          'tb', 'rbi', 'sb', 'cs', 'sh', 'sf', 'bb', 'ibb', 'hbp', 'so', 'gdp')
HEADERS = ('', '選手', '試合', '打席', '打数', '得点', '安打', '二塁打',
           '三塁打', '本塁打', '塁打', '打点', '盗塁', '盗塁刺', '犠打',
           '犠飛', '四球', '故意四', '死球', '三振', '併殺打', '打率',
           '長打率', '出塁率')
PEOPLE_COLUMNS = ('key_uuid', 'key_npb', 'key_mlbam', 'name_first', 'name_last',
                  'birth_year', 'birth_month', 'birth_day')


def name_key(text):
    """Only whitespace changes are allowed; no transliteration/fuzzy merge."""
    return re.sub(r'\s+', '', text)


def season_links(html, season):
    if not 2005 <= season <= 2024:
        raise ValueError('Historical first-team season outside contracted scope')
    soup = BeautifulSoup(html, 'html.parser')
    if not re.search(rf'{season}年度', soup.title.get_text()):
        raise ValueError('Wrong season index')
    links = set()
    for a in soup.select('a[href]'):
        parsed = urlparse(urljoin(f'https://npb.jp/bis/{season}/stats/', a['href']))
        if parsed.netloc == 'npb.jp' and re.fullmatch(rf'/bis/{season}/stats/idb1_[a-z]+\.html', parsed.path):
            if parsed.query or parsed.fragment:
                raise ValueError('Unexpected first-team table query/fragment')
            links.add(parsed.path)
    links = sorted(links)
    if len(links) != 12:
        raise ValueError(f'Expected twelve first-team batting tables, got {len(links)}')
    return links


def roster_links(html, season):
    soup = BeautifulSoup(html, 'html.parser')
    links = {}
    for a in soup.select('a[href]'):
        if re.fullmatch(rf'/bis/players/search/yearly/{season}/\d+/', a['href']):
            key = name_key(a.get_text())
            if key in links and links[key] != a['href']:
                raise ValueError('Conflicting historical team listing')
            links[key] = a['href']
    if len(links) != 12:
        raise ValueError(f'Expected twelve historical identity listings, got {len(links)}')
    return links


def roster_names(html, season, team):
    soup = BeautifulSoup(html, 'html.parser')
    title = name_key(soup.title.get_text())
    if f'{name_key(team)}({season})' not in title:
        raise ValueError('Wrong team/year identity listing')
    result = defaultdict(set)
    for a in soup.select('a.player_unit_1[href]'):
        match = re.fullmatch(r'/bis/players/(\d+)\.html', a['href'])
        node = a.select_one('.name')
        if not match or node is None:
            raise ValueError('Unrecognized structured NPB identity')
        result[name_key(node.get_text())].add(match[1])
    if not result:
        raise ValueError('Empty identity listing')
    return dict(result)


def validate_counts(row):
    if any(not isinstance(row[k], int) or row[k] < 0 for k in COUNTS):
        raise ValueError('Invalid nonnegative count')
    if row['tb'] != row['hits'] + row['doubles'] + 2*row['triples'] + 3*row['hr']:
        raise ValueError('Total bases do not reconstruct')
    if row['doubles'] + row['triples'] + row['hr'] > row['hits']:
        raise ValueError('More extra-base hits than hits')
    if row['hits'] + row['so'] > row['ab'] or row['ibb'] > row['bb']:
        raise ValueError('Inconsistent batting counts')
    residual = row['pa'] - sum(row[k] for k in ('ab', 'bb', 'hbp', 'sh', 'sf'))
    if residual < 0:
        raise ValueError('Negative unenumerated PA')
    return residual


def batting_rows(html, season):
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.get_text(' ', strip=True)
    match = re.match(rf'^{season}年度 (.+?) 個人打撃成績', title)
    if not match or 'ファーム' in title or 'イースタン' in title or 'ウエスタン' in title:
        raise ValueError('Wrong season/first-team batting table')
    team = match[1]
    tables = [t for t in soup.find_all('table') if t.select('tr.ststats')]
    if len(tables) != 1:
        raise ValueError('Expected one batting table')
    table = tables[0]
    heads = [name_key(c.get_text()) for c in table.select('th')]
    if tuple(heads) != HEADERS:
        raise ValueError(f'Unrecognized batting headers {heads}')
    result, seen = [], set()
    for tr in table.select('tr.ststats'):
        cells = [c.get_text(' ', strip=True) for c in tr.find_all('td', recursive=False)]
        if len(cells) != 24:
            raise ValueError('Changed batting column count')
        name = cells[1]
        key = name_key(name)
        if not key or key in seen:
            raise ValueError('Missing/duplicate player name within team season')
        seen.add(key)
        if cells[0] not in ('', '*', '+'):
            raise ValueError('Unknown handedness marker')
        row = dict(season=season, team_name=team, player_name_ja=name, name_key=key,
                   bats={'': 'R', '*': 'L', '+': 'S'}[cells[0]])
        row.update({k: int(v) for k, v in zip(COUNTS, cells[2:21], strict=True)})
        row['unenumerated_pa'] = validate_counts(row)
        denominators = {'avg': row['ab'], 'slg': row['ab'],
                        'obp': row['ab'] + row['bb'] + row['hbp'] + row['sf']}
        numerators = {'avg': row['hits'], 'slg': row['tb'],
                      'obp': row['hits'] + row['bb'] + row['hbp']}
        for k, value in zip(('avg', 'slg', 'obp'), cells[21:24], strict=True):
            shown = float(value)
            calculated = numerators[k]/denominators[k] if denominators[k] else None
            if calculated is not None and abs(shown-calculated) > 0.000501:
                raise ValueError(f'Rounded {k} does not reconstruct')
            row['source_'+k] = shown
            row[k] = calculated
        result.append(row)
    return team, result


def attach_npb_ids(rows, listing):
    output = []
    for row in rows:
        ids = listing.get(row['name_key'], set())
        output.append(dict(row, npb_id=next(iter(ids)) if len(ids) == 1 else None,
                           npb_identity_status='exact_season_team_name' if len(ids) == 1
                           else 'ambiguous' if ids else 'missing_listing_name'))
    return output


def read_npb_crosswalk(path: Path):
    """Keep all NPB identities, not only MLB survivors; ignore career spans."""
    frames = []
    with ZipFile(path) as archive:
        members = sorted(m for m in archive.namelist()
                         if re.search(r'/data/people-[0-9a-f]\.csv$', m))
        if len(members) != 16:
            raise ValueError('Incomplete pinned Chadwick shards')
        for member in members:
            frame = pl.read_csv(BytesIO(archive.read(member)), infer_schema=False,
                                null_values=['', 'NA'])
            frames.append(frame.select(PEOPLE_COLUMNS))
    people = pl.concat(frames).filter(pl.col('key_npb').is_not_null()).to_dicts()
    result = {}
    for row in people:
        key = row['key_npb']
        if key in result:
            raise ValueError('Conflicting structured NPB crosswalk ID')
        row['player_id'] = int(row['key_mlbam']) if row['key_mlbam'] else None
        try:
            row['birth_date'] = date(*[int(row['birth_'+k]) for k in ('year', 'month', 'day')]).isoformat()
        except (ValueError, TypeError):
            row['birth_date'] = None
        result[key] = row
    return result


def history_at(rows, npb_id, origin, start=2005):
    """No future seasons or MLB outcomes can affect a player's input history."""
    known = [r for r in rows if r['npb_id'] == npb_id and start <= r['season'] <= origin]
    recent = [r for r in known if r['season'] >= origin-2]
    totals = {k: sum(r[k] for r in recent) for k in COUNTS}
    pa = totals['pa']
    bip_ab = totals['ab'] - totals['so'] - totals['hr'] + totals['sf']
    return dict(npb_id=npb_id, origin_year=origin,
                history_seasons=sorted({r['season'] for r in known if r['pa'] > 0}),
                observed_history_pa=sum(r['pa'] for r in known),
                experience_left_truncated=True, recent_counts=totals,
                ubb_rate=(totals['bb']-totals['ibb'])/pa if pa else None,
                k_rate=totals['so']/pa if pa else None,
                hr_rate=totals['hr']/pa if pa else None,
                babip=(totals['hits']-totals['hr'])/bip_ab if bip_ab else None,
                input_source='NPB first-team seasons', mlb_translation_fitted=False)
