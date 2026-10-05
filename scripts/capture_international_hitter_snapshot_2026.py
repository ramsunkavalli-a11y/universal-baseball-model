"""Separate dated snapshot capture; no forecast, outcome or model access."""
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from urllib.parse import urljoin

import polars as pl
import requests

import capture_npb_hitting_history as npb
import probe_kbo_hitting_source as probe
import qualify_kbo_hitting_source as qualify
import capture_kbo_hitting_history as kbo
from universal_baseball.chadwick import CHADWICK_SNAPSHOT_SHA
from universal_baseball.npb_history import roster_links, roster_names, attach_npb_ids, name_key, read_npb_crosswalk
from universal_baseball.npb_identity_overlay import reviewed_id
from universal_baseball.kbo_history import join_groups, FIELDS1, FIELDS2
from universal_baseball.international_hitter_snapshot_2026 import npb_links, batting_rows, snapshot_date
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/generated/international-hitter-snapshot-2026-10-05'
RAW = ROOT / 'data/quarantine/international-hitter-snapshot-2026-10-05'
REGISTER = ROOT / f'data/quarantine/npb-hitting-history/chadwick-{CHADWICK_SNAPSHOT_SHA}.zip'


def read(p): return json.loads(p.read_text(encoding='utf8'))


def save(name, value):
    p = OUT / name
    assert not p.exists(), f'Preserve completed {p}'
    OUT.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False, default=str) + '\n', encoding='utf8', newline='\n')


def seals():
    paths = [Path(__file__), ROOT / 'docs/hitter-international-2026-snapshot-contract.md', REGISTER,
             ROOT / 'src/universal_baseball/international_hitter_snapshot_2026.py',
             *[Path(m.__file__) for m in (npb, probe, qualify, kbo)],
             ROOT / 'reports/model-evidence/international-hitter-source-2025/report.json']
    return {str(p): sha256_file(p) for p in paths}


def capture_npb():
    assert not (OUT / 'npb-collection.json').exists()
    hashes = seals(); npb.RAW = RAW / 'npb'
    body, index_meta = npb.capture('index.html', 'https://npb.jp/bis/2026/stats/')
    identity, identity_meta = npb.capture('identity-index.html', 'https://npb.jp/bis/players/all/index.html')
    links, listings = npb_links(body), roster_links(identity, 2026)
    crosswalk = read_npb_crosswalk(REGISTER); receipts = [index_meta, identity_meta]; rows = []; dates = []
    for link in links:
        slug = Path(link).stem
        raw, meta = npb.capture(slug + '.html', urljoin('https://npb.jp', link))
        team, records = batting_rows(raw); date = snapshot_date(raw); dates.append(date)
        raw_identity, im = npb.capture(slug + '-identity.html', urljoin('https://npb.jp', listings[name_key(team)]))
        names = roster_names(raw_identity, 2026, team)
        for r in attach_npb_ids(records, names):
            key, status = reviewed_id(r, names); person = crosswalk.get(key, {})
            rows.append(dict(r, npb_id=key, npb_identity_status=status, player_id=person.get('player_id'),
                             birth_date=person.get('birth_date'), table_slug=slug, provider_asof=date,
                             source_url=meta['url'], source_sha256=meta['sha256'],
                             identity_url=im['url'], identity_sha256=im['sha256']))
        receipts += [meta, im]
        print(f'NPB 2026 snapshot {slug}: {len(records)} rows, provider date {date}.', flush=True)
    assert len({d for d in dates if d}) <= 1, 'Moving snapshot; do not merge different dates'
    f = pl.DataFrame(rows, schema_overrides={'player_id': pl.Int64}).sort('table_slug', 'name_key')
    assert f['team_name'].n_unique() == 12 and f.unique(['table_slug', 'name_key']).height == f.height
    p = OUT / 'npb.parquet'; OUT.mkdir(parents=True, exist_ok=True); assert not p.exists(); f.write_parquet(p)
    save('npb-collection.json', dict(league='NPB', source_year=2026, rows=len(f), teams=12, PA=int(f['pa'].sum()),
         zero_PA_rows=int((f['pa'] == 0).sum()), missing_source_key_rows=int(f['npb_id'].is_null().sum()),
         missing_MLB_key_rows=int(f['player_id'].is_null().sum()), provider_index_asof=snapshot_date(body),
         provider_table_dates=dates, season_complete=False, season_completion_status='unproven_snapshot_only',
         captures=receipts, source_hashes=hashes, data_sha256=sha256_file(p), player_walkthrough_status='pending',
         new_fits=0, forecast_changes=0))


def capture_kbo():
    assert not (OUT / 'kbo-collection.json').exists()
    hashes = seals(); probe.RAW = RAW / 'kbo'
    attempt = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    session = requests.Session(); session.headers['User-Agent'] = 'UBM low-rate official source snapshot research'
    a, ra, ca = qualify.group(session, 2026, 1, attempt)
    b, rb, cb = qualify.group(session, 2026, 2, attempt)
    rows = join_groups(a, b, 2026)
    t1, r1 = kbo.team_rows(session, 2026, 1, attempt); t2, r2 = kbo.team_rows(session, 2026, 2, attempt)
    assert {r['팀명'] for r in t1} == {r['팀명'] for r in t2}
    headers = {**dict(zip(FIELDS1, ['G', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'TB', 'RBI', 'SAC', 'SF'])),
               **dict(zip(FIELDS2, ['BB', 'IBB', 'HBP', 'SO', 'GDP']))}
    for field, header in headers.items():
        if field != 'games': assert sum(int(t[header]) for t in (t1 if field in FIELDS1 else t2)) == sum(r[field] for r in rows), field
    identities = {}
    for p in [ROOT / 'reports/generated/kbo-identity-overlay/identities.parquet',
              ROOT / 'reports/generated/international-hitter-source-2025/kbo-2025-identities.parquet']:
        hashes[str(p)] = sha256_file(p)
        for r in pl.read_parquet(p).iter_rows(named=True):
            if r.get('player_id') is not None:
                old = identities.get(r['kbo_id'])
                assert old is None or old['player_id'] == r['player_id'], 'Conflicting static source identity'
                identities[r['kbo_id']] = r
    enriched = []
    for r in rows:
        person = identities.get(r['kbo_id'], {})
        enriched.append(dict(r, player_id=person.get('player_id'), birth_date=person.get('birth_date'),
                             english_name=person.get('english_name'), current_role_salary_status_used=False))
    f = pl.DataFrame(enriched, schema_overrides={'player_id': pl.Int64}).sort('kbo_id')
    p = OUT / 'kbo.parquet'; OUT.mkdir(parents=True, exist_ok=True); assert not p.exists(); f.write_parquet(p)
    save('kbo-collection.json', dict(league='KBO', source_year=2026, rows=len(f), teams=10, PA=int(f['pa'].sum()),
         zero_PA_rows=int((f['pa'] == 0).sum()), missing_MLB_key_rows=int(f['player_id'].is_null().sum()),
         season_complete=False, season_completion_status='unproven_snapshot_only', team_fields_reconciled=16,
         captures=ra + rb + r1 + r2, groups=[ca, cb], team_tables=[t1, t2], source_hashes=hashes,
         data_sha256=sha256_file(p), player_walkthrough_status='pending', new_fits=0, forecast_changes=0))


if __name__ == '__main__':
    {'npb': capture_npb, 'kbo': capture_kbo}[sys.argv[1]]()
