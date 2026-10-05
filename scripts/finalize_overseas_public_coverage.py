"""Independent literal CSV joins and coverage accounting; no accuracy certification."""
from collections import Counter
from pathlib import Path
import csv
import json
import math
import subprocess
import sys
import tempfile
import polars as pl
from audit_overseas_public_coverage import ROOT, GEN, OUT, MANIFEST, read, save, verify
from universal_baseball.storage import sha256_file


def main():
    if (OUT / 'final-review.json').exists(): raise ValueError('Preserve completed audit')
    seal = read(OUT / 'source-seal.json'); verify(seal['hashes'])
    d = read(OUT / 'coverage.json'); w = read(OUT / 'player-walks.json')
    q = pl.read_parquet(GEN / 'foreign-count-calibration/predictions.parquet').filter(pl.col('source_present'))
    ledger = {r['row_id']: r for r in d['ledger']}
    if set(ledger) != set(q['row_id']) or len(d['ledger']) != 266: raise ValueError('Population mismatch')
    archive = {}
    for r in read(MANIFEST)['records']:
        with (ROOT / r['private_file']).open(encoding='utf-8-sig', newline='') as stream:
            raw = list(csv.DictReader(stream))
        mapping = {}
        for v in raw:
            token = v['MLBAMID'] or ''
            if token.isascii() and token.isdigit() and int(token) > 0:
                if int(token) in mapping: raise ValueError('Repeated raw identity')
                mapping[int(token)] = v
        archive[r['system'].lower(), r['year']] = mapping
    checks = 0
    for r in q.to_dicts():
        g = ledger[r['row_id']]
        for k in ('player_id', 'origin_year', 'target_year', 'source_addition', 'route_used', 'pa_0', 'prior_debut'):
            if g[k] != r[k]: raise ValueError('Origin membership field mismatch')
            checks += 1
        for s in ('steamer', 'zips'):
            key = (s, r['target_year']); v = archive.get(key, {}).get(r['player_id'])
            expected = ('archive_year_unavailable' if key not in archive else 'identity_absent' if v is None
                        else 'zero_projected_PA' if float(v['PA']) == 0 else 'positive_projected_PA')
            got = g['public'][s]
            if got['status'] != expected: raise ValueError('Coverage state mismatch')
            checks += 1
            if v is None:
                if got['projection'] is not None: raise ValueError('Fabricated missing forecast')
                continue
            a = got['projection']; pa = float(v['PA'])
            if (a['name'], a['FG_id'], a['PA']) != (v['Name'], v['PlayerId'], pa):
                raise ValueError('Literal public row mismatch')
            checks += 3
            if not pa:
                if a['event_probability'] is not None: raise ValueError('Invented zero-PA rate')
                continue
            hits = sum(float(v[n]) for n in ('1B', '2B', '3B', 'HR'))
            if abs(hits - float(v['H'])) > .001: raise ValueError('Source hit accounting outside intake tolerance')
            events = [pa - float(v['SO']) - (float(v['BB']) - float(v['IBB'])) - float(v['HBP']) - hits,
                      float(v['SO']), float(v['BB']) - float(v['IBB']), float(v['HBP']),
                      *[float(v[n]) for n in ('1B', '2B', '3B', 'HR')]]
            for actual, count in zip(a['event_probability'], events):
                if not math.isclose(actual, count / pa, abs_tol=1e-12, rel_tol=0):
                    raise ValueError('Independent event denominator mismatch')
                checks += 1
            if a['workload_interpretation'] != ('unconditional' if s == 'steamer' else 'conditional'):
                raise ValueError('Wrong workload semantics')
    for g in d['groups']:
        name = g['scope']; members = list(ledger.values())
        if name == 'original_foreign': members = [r for r in members if not r['source_addition']]
        elif name == 'fresh_original': members = [r for r in members if not r['source_addition'] and r['route_used']]
        elif name == 'additions': members = [r for r in members if r['source_addition']]
        elif name.startswith('target_'): members = [r for r in members if r['target_year'] == int(name[7:])]
        if g['rows'] != len(members) or g['people'] != len({r['player_id'] for r in members}):
            raise ValueError('Group size mismatch')
        for s in ('steamer', 'zips'):
            if g['systems'][s] != dict(Counter(r['public'][s]['status'] for r in members)):
                raise ValueError('Coverage total mismatch')
            checks += 1
    if len(w['cases']) != 59 or {r['coverage']['row_id'] for r in w['cases']} != {
            r['row_id'] for r in read(GEN / 'overseas-opportunity-inventory/inventory.json')['walks']}:
        raise ValueError('Retained walk mismatch')
    doc = ROOT / 'docs/hitter-overseas-public-coverage-result.md'
    text = doc.read_text(encoding='utf8')
    if 'Read-only source diagnosis complete' not in text or 'one-PA' not in text or 'Bethancourt' not in text:
        raise ValueError('Human review or source limitations missing')
    temp = Path(tempfile.mkdtemp(prefix='overseas-public-review-tests-', dir=GEN))
    if temp.parent.resolve() != GEN.resolve() or list(temp.iterdir()): raise ValueError('Unsafe test temporary path')
    test = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
        'tests/test_overseas_public_coverage.py', f'--basetemp={temp}'], cwd=ROOT, capture_output=True, text=True)
    if test.returncode: raise ValueError(test.stdout + test.stderr)
    freezes = []
    for script in ('verify_hitter_selected_2026_freeze.py', 'verify_hitter_full_2026_freeze.py'):
        proc = subprocess.run([sys.executable, str(ROOT / 'scripts' / script)], cwd=ROOT, capture_output=True, text=True)
        if proc.returncode: raise ValueError(proc.stdout + proc.stderr)
        freezes.append(dict(script=script, result=json.loads(proc.stdout),
            qualification='Verifies original package; does not reopen the completed 2026 evaluation.'))
    verify(seal['hashes'])
    paths = [doc, Path(__file__), OUT / 'source-seal.json', OUT / 'coverage.json', OUT / 'player-walks.json']
    receipt = dict(status='source_diagnosis_complete', player_walkthrough_status='complete',
        rows=266, people=140, focal_origins=18, unique_source_walks=59, independent_checks=checks,
        tests=test.stdout, new_fits=0, new_forecasts=0, new_2026_outcomes_read=False,
        accuracy_leaderboard_computed=False, predictive_gain_claimed=False, deployment_approved=False,
        exact_snapshot_day_known=False, freeze_checks=freezes,
        next_boundary='Audit original-cutoff overseas employment and intended role sources, not another broad fit.',
        hashes={str(p.relative_to(ROOT)): sha256_file(p) for p in paths})
    save('final-review.json', receipt)
    public = ROOT / 'reports/model-evidence/overseas-public-coverage'
    if public.exists(): raise ValueError('Preserve public completion receipt')
    public.mkdir()
    (public / 'report.json').write_text(json.dumps(dict(**receipt, coverage=d['groups']), indent=2, allow_nan=False)
        + '\n', encoding='utf8', newline='\n')
    print(json.dumps(dict(status=receipt['status'], independent_checks=checks, tests=test.stdout,
                         new_fits=0, forecast_packages_unchanged=True)), flush=True)


if __name__ == '__main__': main()
