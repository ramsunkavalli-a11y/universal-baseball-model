"""Independent cell reconstruction and six fixed-rule snapshot walks."""
import json
import math
from pathlib import Path
import re
import sys

from bs4 import BeautifulSoup
import polars as pl

import capture_international_hitter_snapshot_2026 as c
from universal_baseball.international_hitter_snapshot_2026 import controls, subtotal
from universal_baseball.npb_history import COUNTS, HEADERS, name_key
from universal_baseball.kbo_history import FIELDS1, FIELDS2, HEADERS1, HEADERS2
from universal_baseball.storage import sha256_file

PUBLIC = c.ROOT / 'reports/model-evidence/international-hitter-snapshot-2026-10-05'


def verify(mapping):
    for p, h in mapping.items(): assert sha256_file(Path(p)) == h, p


def snapshot_counts():
    hashes = {}; checks = {}; rows = {}
    for league in ['npb', 'kbo']:
        path = c.OUT / f'{league}-collection.json'; receipt = c.read(path)
        assert receipt['source_year'] == 2026 and not receipt['season_complete'] and receipt['new_fits'] == receipt['forecast_changes'] == 0
        verify(receipt['source_hashes'])
        f = pl.read_parquet(c.OUT / f'{league}.parquet'); assert sha256_file(c.OUT / f'{league}.parquet') == receipt['data_sha256']
        hashes[str(path)] = sha256_file(path); hashes[str(c.OUT / f'{league}.parquet')] = receipt['data_sha256']
        by_hash = {}
        for p in (c.RAW / league).glob('*.html'):
            by_hash.setdefault(sha256_file(p), []).append(p)
        for meta in receipt['captures']:
            assert meta['sha256'] in by_hash, meta['url']
            if meta.get('http_status') is not None: assert meta['http_status'] == 200
            assert meta['url'] == meta['returned_url']
        count_fields = 0
        if league == 'npb':
            for slug in f['table_slug'].unique().sort():
                group = f.filter(pl.col('table_slug') == slug)
                p = c.RAW / league / (slug + '.html'); soup = BeautifulSoup(p.read_bytes(), 'html.parser')
                assert tuple(name_key(x.get_text()) for x in soup.select('table.tablefix2 th')) == HEADERS[1:]
                raw = []
                for tr in soup.select('table.tablefix2 tr'):
                    cells = tr.find_all('td', recursive=False)
                    if not cells: continue
                    assert len(cells) == 23
                    for sup in cells[0].find_all('sup'): sup.extract()
                    raw.append(dict(name_key=name_key(cells[0].get_text()), **dict(zip(COUNTS, (int(x.get_text(strip=True)) for x in cells[1:20]), strict=True))))
                assert len(raw) == group.height
                indexed = {r['name_key']: r for r in raw}; assert len(indexed) == len(raw)
                for r in group.iter_rows(named=True):
                    assert all(r[k] == indexed[r['name_key']][k] for k in COUNTS)
                    count_fields += len(COUNTS)
        else:
            groups = []
            for number, fields, headers in [(1, FIELDS1, HEADERS1), (2, FIELDS2, HEADERS2)]:
                bodies = sorted((p for p in (c.RAW / league).glob('*.html') if re.search(rf'-group{number}-(count-first|page\d+)\.html$', p.name)),
                                key=lambda p: 1 if 'count-first' in p.name else int(re.search(r'page(\d+)', p.name)[1]))
                assert len(bodies) == receipt['groups'][number - 1]['last_page']
                raw = {}
                for p in bodies:
                    soup = BeautifulSoup(p.read_bytes(), 'html.parser')
                    assert [x.get_text(' ', strip=True) for x in soup.select('table.tData01 thead th')] == headers
                    for tr in soup.select('table.tData01 tbody tr'):
                        cells = tr.find_all('td', recursive=False)
                        if not cells: continue
                        m = re.search(r'playerId=(\d+)$', cells[1].find('a')['href']); assert m
                        key = m[1]; assert key not in raw
                        raw[key] = {k: int(cells[i].get_text(strip=True)) for i, k in enumerate(fields, 4)}
                assert set(raw) == set(f['kbo_id'])
                for r in f.iter_rows(named=True):
                    assert all(r[k] == raw[r['kbo_id']][k] for k in fields)
                    count_fields += len(fields)
                groups.append(raw)
            team_bodies = []
            for number in [1, 2]:
                ps = list((c.RAW / league).glob(f'*-teams-group{number}-year.html')); assert len(ps) == 1
                soup = BeautifulSoup(ps[0].read_bytes(), 'html.parser')
                headers = [x.get_text(strip=True) for x in soup.select('table.tData thead th')]
                team_bodies.append([dict(zip(headers, [x.get_text(strip=True) for x in tr.find_all('td', recursive=False)], strict=True)) for tr in soup.select('table.tData tbody tr')])
            assert all(len(t) == 10 for t in team_bodies)
            names = dict(zip(FIELDS1 + FIELDS2, ['G', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'TB', 'RBI', 'SAC', 'SF', 'BB', 'IBB', 'HBP', 'SO', 'GDP']))
            for field, header in names.items():
                if field == 'games': continue
                team = team_bodies[0 if field in FIELDS1 else 1]
                assert sum(int(r[header]) for r in team) == int(f[field].sum()), field
        rows[league] = f.to_dicts()
        checks[league] = dict(rows=len(f), PA=int(f['pa'].sum()), zero_PA_rows=int((f['pa'] == 0).sum()),
            count_cells_independently_reconstructed=count_fields, missing_MLB_key_rows=int(f['player_id'].is_null().sum()),
            residual_PA=int(f['unenumerated_pa'].sum()), source_complete_for_snapshot=True, season_complete=False,
            snapshot_provider_date=receipt.get('provider_index_asof'), source_identity_missing_rows=receipt.get('missing_source_key_rows', 0))
    return rows, checks, hashes


def prepare():
    assert not (c.OUT / 'review.json').exists()
    current, checks, hashes = snapshot_counts(); cases = []
    old_paths = {
        'npb': [c.ROOT / 'reports/generated/npb-hitting-history/reviewed-batting.parquet', c.ROOT / 'reports/generated/international-hitter-source-2025/npb-2025.parquet'],
        'kbo': [c.ROOT / 'reports/generated/kbo-hitting-history/first-team-batting.parquet', c.ROOT / 'reports/generated/international-hitter-source-2025/kbo-2025-identities.parquet']}
    for league, key in [('npb', 'npb_id'), ('kbo', 'kbo_id')]:
        history = [r for p in old_paths[league] for r in pl.read_parquet(p).iter_rows(named=True) if r['season'] >= 2024]
        history += current[league]
        for p in old_paths[league]: hashes[str(p)] = sha256_file(p)
        for kind, row in controls(current[league], key):
            identity = row.get(key)
            before = subtotal(history, key, identity, 2025); after = subtotal(history, key, identity, 2026)
            mutated = [dict(r, pa=999999) if r['season'] == 2026 else dict(r) for r in history]
            assert subtotal(mutated, key, identity, 2025) == before
            grouped = {}
            for r in current[league]:
                if r.get(key) is not None and r[key] != identity:
                    g = grouped.setdefault(r[key], dict(source_key=r[key], name=r.get('player_name_ja') or r.get('player_name_ko'), pa=0, birth_date=r.get('birth_date')))
                    g['pa'] += r['pa']
            def distance(peer):
                exposure = abs(math.log1p(peer['pa']) - math.log1p(after['counts']['pa']))
                if row.get('birth_date') and peer.get('birth_date'):
                    exposure += abs(int(row['birth_date'][:4]) - int(peer['birth_date'][:4])) / 2
                return exposure, peer['source_key']
            peers = sorted(grouped.values(), key=distance)[:3]
            selected = [r for r in history if identity is not None and r.get(key) == identity]
            cases.append(dict(league=league, control=kind, source_key=identity, source_name=row.get('player_name_ja') or row.get('player_name_ko'),
                selected_table_row=dict(row), MLB_key=row.get('player_id'), cutoff2025=before, cutoff2026=after,
                annual_history=selected, comparison_source_peers=peers, future_source_mutation_pass=True,
                MLB_talent_forecast=None, MLB_opportunity_forecast=None, predictive_outcome=None,
                interpretation='Count exposure and rates only; zero table PA is not proof of no professional career or zero talent.'))
    assert len(cases) == 6
    hashes[str(Path(__file__))] = sha256_file(Path(__file__))
    c.save('review.json', dict(source_checks=checks, source_cases=cases, count_cells=sum(v['count_cells_independently_reconstructed'] for v in checks.values()),
        source_hashes=hashes, independent_reconstruction_pass=True, future_mutation_checks=6,
        source_walkthrough_status='pending_readable_review', new_fits=0, forecasts_changed=False,
        completed_2026_MLB_evaluation_unchanged=True, raw_2026_MLB_outcomes_read=False))
    print(json.dumps(dict(checks=checks, cases=[dict(league=r['league'], control=r['control'], name=r['source_name'],
        source_key=r['source_key'], MLB_key=r['MLB_key'], before_PA=r['cutoff2025']['counts']['pa'],
        after_PA=r['cutoff2026']['counts']['pa'], source_row_PA=r['selected_table_row']['pa'],
        before_HR=r['cutoff2025']['counts']['hr'], after_HR=r['cutoff2026']['counts']['hr']) for r in cases]), ensure_ascii=False, indent=2), flush=True)


def finish():
    public = PUBLIC / 'report.json'; assert not public.exists()
    r = c.read(c.OUT / 'review.json'); verify(r['source_hashes'])
    docs = [c.ROOT / 'docs/hitter-international-2026-snapshot-result.md', c.ROOT / 'docs/hitter-international-2026-snapshot-player-review.md']
    text = docs[1].read_text(encoding='utf8')
    for case in r['source_cases']: assert case['source_name'] in text and str(case['cutoff2026']['counts']['pa']) in text
    package_checks = []
    for dirname, filename in [('hitter-selected-2026-frozen-2026-10-05', 'freeze-manifest.json'), ('hitter-full-2026-confirmation-forecast-2026-09-20', 'manifest.json')]:
        path = c.ROOT / 'model_artifacts' / dirname / filename
        if filename == 'manifest.json' and not path.exists():
            # The legacy verifier's package layout differs; check its existing
            # forecast bytes independently, without claiming a new outcome test.
            import subprocess
            result = subprocess.run([sys.executable, '-X', 'utf8', str(c.ROOT / 'scripts/verify_hitter_full_2026_freeze.py')], cwd=c.ROOT, capture_output=True, text=True, check=True)
            package_checks.append(json.loads(result.stdout)); continue
        manifest = c.read(path)
        for entry in manifest['files']: assert sha256_file(path.parent / entry['path']) == entry['sha256']
        package_checks.append(dict(package=dirname, files=len(manifest['files']), unchanged=True, manifest_sha256=sha256_file(path)))
    hashes = {str(p.relative_to(c.ROOT)): sha256_file(p) for p in [*docs, c.OUT / 'review.json', c.ROOT / 'docs/hitter-next-action-correction.md']}
    PUBLIC.mkdir(parents=True, exist_ok=True)
    payload = dict(r, source_walkthrough_status='complete_for_dated_source_snapshot', season_completion_qualified=False,
        universal_MLB_crosswalk_qualified=False, historical_role_or_park_exposure_qualified=False,
        deployment_approved=False, predictive_improvement_established=False, broad_goal_complete=False,
        player_forecasts_changed=False, freeze_preservation_checks=package_checks,
        completed_readable_review_hashes=hashes, disposition='Retain dated raw count evidence for later source preparation, not final season totals, translated MLB talent or an approved forecast replacement.')
    public.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8', newline='\n')
    print('Source snapshot review complete; six count walks, no fits, no frozen forecast or 2026 MLB evaluation changes.', flush=True)


if __name__ == '__main__':
    {'prepare': prepare, 'finish': finish}[sys.argv[1]]()
