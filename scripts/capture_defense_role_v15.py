"""Bounded historical role-source capture, never a fit or outcome selection."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import json

from universal_baseball.official_capture import capture_official_json
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/generated/defense-role-v15'
PUBLIC = ROOT / 'reports/model-evidence/defense-role-v15'
CONTRACT = ROOT / 'docs/defense-role-v15-source-contract.md'
WALK = ROOT / 'reports/generated/defense-jobs-v14/player-walkthrough.json'
SOURCE = ROOT / 'reports/generated/defense-position-opportunity-v7/source.parquet'
ALL_SPORTS = '1,11,12,13,14,16'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def receipt(name, value):
    for folder in (OUT, PUBLIC):
        save(folder / name, value)


def capture(endpoint, name):
    path = OUT / 'captures' / (name + '.json')
    meta = path.with_suffix('.capture.json')
    if path.exists():
        m = read(meta)
        assert m['endpoint'] == endpoint and sha256_file(path) == m['sha256']
        return read(path)
    assert not meta.exists()
    c = capture_official_json(endpoint)
    c.write_raw(path)
    save(meta, dict(endpoint=endpoint, url=c.url, status_code=c.status_code,
                   retrieved_at_utc=c.retrieved_at_utc.isoformat(), sha256=c.content_sha256))
    return c.data


def log_endpoint(pid, year, sports=None):
    assert 2004 <= year <= 2024
    extra = f'&sportIds={sports}' if sports else ''
    return f'people/{pid}/stats?stats=gameLog&group=fielding&season={year}&gameType=R{extra}'


def check_seal():
    seal = read(OUT / 'capture-seal.json')
    for path, expected in seal['hashes'].items():
        assert sha256_file(Path(path)) == expected, path


def probe():
    protections()
    OUT.mkdir(parents=True, exist_ok=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    if not (OUT / 'capture-seal.json').exists():
        receipt('capture-seal.json', dict(before_capture=True, no_fits=True, max_input_season=2024,
            hashes={str(p): sha256_file(p) for p in [Path(__file__), CONTRACT, WALK, SOURCE]},
            initial_probe_cases=['Schwarber 2023', 'Ohtani 2023', 'Buxton 2024',
                                 'Eldridge 2024 minor sport scope']))
    check_seal()
    jobs = [(log_endpoint(656941, 2023), 'probe-Schwarber-2023'),
            (log_endpoint(660271, 2023), 'probe-Ohtani-2023'),
            (log_endpoint(621439, 2024), 'probe-Buxton-2024'),
            ('stats?stats=byDateRange&group=fielding&season=2023&leagueIds=104&playerPool=ALL'
             '&limit=50000&gameType=R&startDate=08/01/2023&endDate=12/31/2023', 'probe-date-range-2023'),
            (log_endpoint(805811, 2024, ALL_SPORTS), 'probe-Eldridge-2024-all-sports'),
            (log_endpoint(621439, 2024, ALL_SPORTS), 'probe-Buxton-2024-all-sports')]
    def one(job):
        endpoint, name = job
        data = capture(endpoint, name)
        print(name, [(g.get('type', {}).get('displayName'), len(g.get('splits', [])))
                     for g in data.get('stats', [])], flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(one, jobs))
    protections()


def expand():
    protections(); check_seal()
    assert (OUT / 'probe-review.json').exists(), 'Review probe scope before expansion'
    review = read(OUT / 'probe-review.json')
    assert review['all_sports_scope_verified'] and review['gamelog_source_integrity'] == 'pass'
    # Reuse all fixed/outcome-blind cases, including failures, not only famous successes.
    walk = read(WALK)
    cases = {(r['player_id'], r['origin']): r['name'] for c in walk['cases'] for r in c['records']}
    cases.update({(621439, 2023): 'Byron Buxton temporary DH year',
                  (805811, 2023): 'Bryce Eldridge earlier RF use'})
    # Contributor IDs MUST be reconciled to the saved training-source diagnosis.
    diagnosis = read(ROOT / 'reports/generated/defense-jobs-v14/source-profile-diagnosis.json')
    for name, year in [('Jonah Bride', 2021), ('Jonathan Aranda', 2021), ('Eric Wagaman', 2023)]:
        matches = [r for r in diagnosis['Eldridge_prior_contributors']
                   if r['player_name'] == name and r['origin_year'] == year]
        assert len(matches) == 1, (name, year)
        # Use certified saved source IDs, not typed identifiers.
        cases[(matches[0]['player_id'], year)] = name + ' prior contributor'
    manifest = dict(selection='All 19 fixed v14 focal and 57 origin-blind peer records, deduplicated; '
                              'Buxton/Eldridge prior year and three named prior contributors added for source tracing.',
        requests=[dict(player_id=pid, season=y, name=name, endpoint=log_endpoint(pid,y,ALL_SPORTS),
                       capture_name=f'log-{y}-{pid}-all-sports') for (pid,y), name in sorted(cases.items())],
        max_season=2024, no_fits=True, probe_review_sha256=sha256_file(OUT/'probe-review.json'))
    if (OUT/'expansion-manifest.json').exists():
        assert read(OUT/'expansion-manifest.json') == manifest
    else:
        receipt('expansion-manifest.json', manifest)
    def one(r):
        data = capture(r['endpoint'], r['capture_name'])
        print(f"Captured {r['season']} {r['name']}: "
              f"{sum(len(g.get('splits', [])) for g in data.get('stats', []))} position-game rows", flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(one, manifest['requests']))
    protections()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['probe', 'expand'])
    mode = parser.parse_args().mode
    globals()[mode]()
