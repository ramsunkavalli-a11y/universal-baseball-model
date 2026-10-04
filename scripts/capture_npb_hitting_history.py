"""Capture every contracted NPB first-team batting season, then review IDs."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
from threading import Lock
import time
from urllib.parse import urljoin

import polars as pl
import requests

from universal_baseball.chadwick import CHADWICK_SNAPSHOT_SHA
from universal_baseball.npb_history import (
    attach_npb_ids, batting_rows, name_key, read_npb_crosswalk,
    roster_links, roster_names, season_links,
)
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT/'data/quarantine/npb-hitting-history'
OUT = ROOT/'reports/generated/npb-hitting-history'
CONTRACT = ROOT/'docs/hitter-foreign-history-source-contract.md'
BASE = 'https://npb.jp'
LOCK = Lock()
LAST = 0.0


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def write_new(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    value = json.dumps(payload, ensure_ascii=False, allow_nan=False,
                       sort_keys=True, separators=(',', ':'))+'\n'
    if path.exists():
        if path.read_text(encoding='utf8') != value:
            raise ValueError(f'Preserve existing receipt: {path}')
    else:
        path.write_text(value, encoding='utf8', newline='\n')


def capture(name, url):
    global LAST
    path = RAW/name
    meta_path = path.with_suffix(path.suffix+'.metadata.json')
    if meta_path.exists():
        meta = read(meta_path)
        if meta['url'] != url or sha256_file(path) != meta['sha256']:
            raise ValueError('Capture provenance mismatch')
        return path.read_bytes(), meta
    if path.exists():
        raise ValueError(f'Unreceipted capture: {path}')
    with LOCK:
        time.sleep(max(0, 0.75-(time.monotonic()-LAST)))
        LAST = time.monotonic()
    response = requests.get(url, timeout=(10, 40), headers={
        'User-Agent': 'UBM historical baseball research; low-rate season-table collection'})
    response.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)
    meta = dict(url=url, returned_url=response.url, captured_utc=datetime.now(timezone.utc).isoformat(),
                sha256=sha256_file(path), bytes=len(response.content),
                historical_publication_vintage_verified=False,
                public_redistribution_approved=False)
    write_new(meta_path, meta)
    return response.content, meta


def indexes(season):
    html, meta = capture(f'season-index-{season}.html', f'{BASE}/bis/{season}/stats/')
    roster_html, roster_meta = capture('all-player-index.html', BASE+'/bis/players/all/index.html')
    return season_links(html, season), roster_links(roster_html, season), [meta, roster_meta]


def team(season, link, listings):
    slug = link.rsplit('/', 1)[-1].removesuffix('.html')
    html, meta = capture(f'{season}-{slug}.html', urljoin(BASE, link))
    team_name, rows = batting_rows(html, season)
    listing_link = listings.get(name_key(team_name))
    if listing_link is None:
        raise ValueError(f'No exact season/team identity index: {team_name}')
    identity_html, identity_meta = capture(f'{season}-{slug}-identities.html', urljoin(BASE, listing_link))
    names = roster_names(identity_html, season, team_name)
    result = attach_npb_ids(rows, names)
    for row in result:
        row['table_slug'] = slug
        row['source_url'] = meta['url']
        row['source_sha256'] = meta['sha256']
        row['identity_url'] = identity_meta['url']
        row['identity_sha256'] = identity_meta['sha256']
    return result, [meta, identity_meta]


def probe():
    archive_name = 'chadwick-'+CHADWICK_SNAPSHOT_SHA+'.zip'
    _, archive_meta = capture(archive_name,
        'https://codeload.github.com/chadwickbureau/register/zip/'+CHADWICK_SNAPSHOT_SHA)
    crosswalk = read_npb_crosswalk(RAW/archive_name)
    ids = {}
    for pid in (660271, 673548):
        found = [r['key_npb'] for r in crosswalk.values() if r['player_id'] == pid]
        if len(found) != 1:
            raise ValueError('Missing/conflicting pinned control crosswalk')
        ids[pid] = found[0]
    pairs = [(2005, 'f'), (2017, 'f'), (2018, 'f'), (2021, 'c'), (2022, 'c'), (2022, 'b')]
    captured, records = [archive_meta], []
    for season, code in pairs:
        links, listings, metas = indexes(season)
        captured.extend(metas)
        wanted = [x for x in links if x.endswith(f'idb1_{code}.html')]
        if len(wanted) != 1:
            raise ValueError('Missing probe table')
        rows, metas = team(season, wanted[0], listings)
        captured.extend(metas)
        records.extend(rows)
    controls = []
    for npb_id, season, expected in [(ids[660271], 2017, True), (ids[660271], 2018, False),
                                    (ids[673548], 2021, True), (ids[673548], 2022, False)]:
        selected = [r for r in records if r['season'] == season and r['npb_id'] == npb_id]
        controls.append(dict(npb_id=npb_id, season=season, expected=expected,
                             present=bool(selected), passes=bool(selected) == expected))
    result = dict(controls=controls, rows=len(records), captures=captured,
                  missing_identity_rows=sum(r['npb_id'] is None for r in records),
                  passed=all(c['passes'] for c in controls),
                  contract_sha256=sha256_file(CONTRACT),
                  parser_sha256=sha256_file(ROOT/'src/universal_baseball/npb_history.py'),
                  code_sha256=sha256_file(Path(__file__)), forecasts_changed=False, new_fits=0)
    write_new(OUT/'probe.json', result)
    if not result['passed']:
        raise ValueError('Source controls failed; preserve and review before broad capture')
    print('Source probe passed:', len(records), 'rows;', result['missing_identity_rows'], 'unresolved IDs', flush=True)


def collect():
    qualification = read(OUT/'probe.json')
    if not qualification['passed'] or qualification['contract_sha256'] != sha256_file(CONTRACT):
        raise ValueError('Unqualified source')
    if qualification['code_sha256'] != sha256_file(Path(__file__)) or qualification['parser_sha256'] != sha256_file(ROOT/'src/universal_baseball/npb_history.py'):
        raise ValueError('Preserve probe code; amend rather than change the qualified parser')
    if (OUT/'collection.json').exists():
        raise ValueError('Collection finished; inspect existing result instead of rerunning')
    rows, captures, checks = [], {}, []
    for season in range(2005, 2025):
        links, listings, metas = indexes(season)
        for meta in metas:
            captures[meta['url']] = meta
        annual = []
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda link: team(season, link, listings), links))
        for records, metas in results:
            annual.extend(records)
            for meta in metas:
                captures[meta['url']] = meta
        keys = [(r['table_slug'], r['name_key']) for r in annual]
        if len(keys) != len(set(keys)):
            raise ValueError('Duplicate source row keys')
        check = dict(season=season, teams=len(links), rows=len(annual),
                     pa=sum(r['pa'] for r in annual),
                     zero_pa_rows=sum(r['pa'] == 0 for r in annual),
                     unresolved_identity_rows=sum(r['npb_id'] is None for r in annual),
                     unenumerated_pa=sum(r['unenumerated_pa'] for r in annual))
        checks.append(check)
        rows.extend(annual)
        print('Captured:', check, flush=True)
    archive, meta = capture('chadwick-'+CHADWICK_SNAPSHOT_SHA+'.zip',
                            'https://codeload.github.com/chadwickbureau/register/zip/'+CHADWICK_SNAPSHOT_SHA)
    del archive
    captures[meta['url']] = meta
    crosswalk = read_npb_crosswalk(RAW/('chadwick-'+CHADWICK_SNAPSHOT_SHA+'.zip'))
    for row in rows:
        person = crosswalk.get(row['npb_id'], {})
        row['chadwick_uuid'] = person.get('key_uuid')
        row['player_id'] = person.get('player_id')
        row['birth_date'] = person.get('birth_date')
        row['crosswalk_status'] = ('missing_npb_identity' if row['npb_id'] is None else
                                  'missing_chadwick_npb' if not person else
                                  'npb_and_mlbam' if row['player_id'] else 'npb_without_mlbam')
    data = pl.DataFrame(rows).sort('season', 'table_slug', 'name_key')
    path = OUT/'first-team-batting.parquet'
    if path.exists():
        if not pl.read_parquet(path).equals(data):
            raise ValueError('Existing normalized rows differ')
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        data.write_parquet(path)
    report = dict(seasons=list(range(2005, 2025)), annual_checks=checks,
                  rows=data.height, captures=sorted(captures.values(), key=lambda r: r['url']),
                  identity_status=data.group_by('npb_identity_status').len().sort('npb_identity_status').to_dicts(),
                  crosswalk_status=data.group_by('crosswalk_status').len().sort('crosswalk_status').to_dicts(),
                  chadwick_snapshot=CHADWICK_SNAPSHOT_SHA, batting_sha256=sha256_file(path),
                  contract_sha256=sha256_file(CONTRACT),
                  parser_sha256=sha256_file(ROOT/'src/universal_baseball/npb_history.py'),
                  code_sha256=sha256_file(Path(__file__)),
                  source_review_status='pending', new_fits=0, forecasts_changed=False,
                  protected_2026_opened=False, kbo_collected=False, mlb_translation_fitted=False)
    write_new(OUT/'collection.json', report)
    print('Complete:', data.height, 'rows;', len(captures), 'captured sources', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['probe', 'collect'])
    args = parser.parse_args()
    (probe if args.mode == 'probe' else collect)()
