"""Additive adjudication and qualified capture; the original probe is preserved."""
import argparse
from calendar import monthrange
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path

import capture_hitter_preseason_population as original
from universal_baseball.storage import sha256_file

ROOT = original.ROOT
OUT = original.OUT
AMENDMENT = ROOT / 'docs/hitter-preseason-population-probe-amendment.md'


def months(start, end):
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    while first <= last:
        stop = min(last, date(first.year, first.month, monthrange(first.year, first.month)[1]))
        yield first.isoformat(), stop.isoformat()
        first = stop + timedelta(days=1)


def authority():
    p = original.read(OUT / 'probe.json')
    assert p['code_sha256'] == sha256_file(Path(original.__file__))
    assert p['contract_sha256'] == sha256_file(ROOT / 'docs/hitter-preseason-population-source-contract.md')
    for m in p['source_captures'].values():
        name = next(n for n in (OUT / 'captures').glob('*.json.metadata.json')
                    if original.read(n)['requested_url'] == m['requested_url'])
        raw = name.with_name(name.name.removesuffix('.metadata.json'))
        assert sha256_file(raw) == m['sha256']
    checks = []
    for c in p['checks']:
        if c['expected_presence'] is None:
            continue
        corrected = dict(c)
        if c['player_id'] == 660271 and c['roster_type'] == '40Man':
            corrected.update(expected_presence=False, passes=not c['present'],
                             reason='Minor contract; contract selected March 27, 2018. No later outcome used.')
        checks.append(corrected)
    assert all(c['passes'] for c in checks if c['roster_type'] == '40Man')
    receipt = dict(original_probe_sha256=sha256_file(OUT / 'probe.json'),
                   original_code_sha256=p['code_sha256'], original_contract_sha256=p['contract_sha256'],
                   amendment_sha256=sha256_file(AMENDMENT), code_sha256=sha256_file(Path(__file__)),
                   checks=checks, allowed_for_further_capture=['40Man'],
                   full_roster_admission_allowed=False, historical_rights_certified=False,
                   reason='Ohtani probe expectation corrected; fullRoster remains temporally disqualified.',
                   new_fits=0)
    original.write(OUT / 'probe-adjudication.json', receipt)
    return receipt


def collect():
    approved = authority()
    allmeta = []
    for year in range(2012, 2026):
        cutoff = original.read(original.CONFIG)[str(year)]['date']
        listing, meta = original.capture(f'teams-{year}.json', original.BASE + '/teams',
                                        dict(sportId=1, season=year))
        allmeta.append(meta)
        ids = sorted({t['id'] for t in listing['teams']})
        assert len(ids) == 30
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(original.roster, team, year, '40Man'): team for team in ids}
            for future in as_completed(futures):
                _, meta = future.result()
                allmeta.append(meta)
        start = f'{year-1}-10-01'
        tx, meta = original.capture(f'transactions-{year}.json', original.BASE + '/transactions',
                                    dict(startDate=start, endDate=cutoff))
        allmeta.append(meta)
        windows = list(months(start, cutoff))
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(original.capture, f'transactions-{year}-{a}-{b}.json',
                                    original.BASE + '/transactions', dict(startDate=a, endDate=b)): (a, b)
                       for a, b in windows}
            partition = {}
            for future in as_completed(futures):
                data, meta = future.result()
                allmeta.append(meta)
                for row in data['transactions']:
                    if row['id'] in partition:
                        assert partition[row['id']] == row, 'Conflicting transaction ID in windows'
                    partition[row['id']] = row
        whole = {r['id']: r for r in tx['transactions']}
        assert len(whole) == len(tx['transactions']), 'Duplicate transaction IDs in whole window'
        assert whole == partition, 'Whole versus monthly window mismatch; audit before materialization'
        print('Captured', year, cutoff, '30 team listings;', len(whole),
              'transactions reconcile with', len(windows), 'monthly windows', flush=True)
    original.write(OUT / 'capture-report-v2.json', dict(
        captures=allmeta, completed_years=list(range(2012, 2026)),
        source_review_status='pending', retrospective_provider=True,
        population_materialized=False, new_fits=0, protected_2026_opened=False,
        authority=approved, date_config_sha256=sha256_file(original.CONFIG)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['adjudicate', 'collect'])
    args = parser.parse_args()
    authority() if args.mode == 'adjudicate' else collect()
