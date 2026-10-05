"""Retain the complete locked foreign cohort and reviewed cases, with no new fits."""
from collections import Counter
from pathlib import Path
import json
import polars as pl
from universal_baseball.overseas_public_coverage import read_archive, coverage_status
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / 'reports/generated'
OUT = GEN / 'overseas-public-coverage'
MANIFEST = ROOT / 'model_artifacts/public-benchmark-intake-v2/verified-archive-manifest.json'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def save(name, value):
    path = OUT / name
    if path.exists(): raise ValueError('Preserve existing execution artifact')
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf8', newline='\n')


def verify(hashes):
    for p, digest in hashes.items():
        if sha256_file(ROOT / p) != digest: raise ValueError(f'Changed sealed source: {p}')


def main():
    if OUT.exists(): raise ValueError('Inspect existing audit rather than restarting')
    inventory = read(GEN / 'overseas-opportunity-inventory/inventory.json')
    prior = read(GEN / 'overseas-opportunity-inventory/final-review.json')
    if prior['player_walkthrough_status'] != 'complete': raise ValueError('Prior review incomplete')
    verify(prior['hashes'])
    manifest = read(MANIFEST)
    paths = [MANIFEST, Path(__file__), ROOT / 'src/universal_baseball/overseas_public_coverage.py',
        ROOT / 'tests/test_overseas_public_coverage.py', ROOT / 'docs/hitter-overseas-public-coverage-contract.md',
        GEN / 'foreign-count-calibration/predictions.parquet',
        GEN / 'foreign-count-calibration/player-walks.json',
        GEN / 'hitter-evidence-representation/predictions.parquet',
        GEN / 'overseas-opportunity-inventory/inventory.json',
        GEN / 'overseas-opportunity-inventory/final-review.json',
        ROOT / 'model_artifacts/hitter-selected-2026-frozen-2026-10-05/freeze-manifest.json',
        ROOT / 'model_artifacts/hitter-full-2026-confirmation-forecast-2026-09-20/manifest.json']
    paths += [ROOT / r['private_file'] for r in manifest['records']]
    hashes = {str(p.relative_to(ROOT)): sha256_file(p) for p in paths}
    for r in manifest['records']:
        if hashes[r['private_file']] != r['sha256']: raise ValueError('Public export hash mismatch')
    OUT.mkdir()
    save('source-seal.json', dict(hashes=hashes, new_fits=0, target_year_maximum=2025,
        exact_public_snapshot_days_unknown=True, no_accuracy_leaderboard=True))
    archives, intake = {}, []
    for r in manifest['records']:
        key = (r['system'].lower(), r['year'])
        if key in archives: raise ValueError('Duplicate system/year archive')
        archives[key], note = read_archive(ROOT / r['private_file'], r); intake.append(note)
    q = pl.read_parquet(GEN / 'foreign-count-calibration/predictions.parquet').filter(pl.col('source_present')).sort('row_id')
    rep = pl.read_parquet(GEN / 'hitter-evidence-representation/predictions.parquet')
    if q.height != 266 or q['row_id'].n_unique() != 266 or q['target_year'].max() != 2025:
        raise ValueError('Changed population')
    ledger = []
    for r in q.to_dicts():
        entry = {k: r[k] for k in ('row_id', 'player_id', 'player_name', 'origin_year', 'target_year',
                                  'source_addition', 'route_used', 'pa_0', 'prior_debut')}
        entry['public'] = {}
        for s in ('steamer', 'zips'):
            status, raw = coverage_status(archives, s, r['target_year'], r['player_id'])
            entry['public'][s] = dict(status=status, projection=raw)
        ledger.append(entry)
    groups = []
    scopes = [('all_foreign', ledger), ('original_foreign', [r for r in ledger if not r['source_addition']]),
              ('fresh_original', [r for r in ledger if not r['source_addition'] and r['route_used']]),
              ('additions', [r for r in ledger if r['source_addition']])]
    scopes += [(f'target_{y}', [r for r in ledger if r['target_year'] == y]) for y in sorted({r['target_year'] for r in ledger})]
    for name, members in scopes:
        groups.append(dict(scope=name, rows=len(members), people=len({r['player_id'] for r in members}),
            systems={s: dict(Counter(r['public'][s]['status'] for r in members)) for s in ('steamer', 'zips')}))
    lookup = {r['row_id']: r for r in ledger}
    modeled = {r['row_id']: r for r in rep.filter(pl.col('row_id').is_in(list(lookup))).to_dicts()}
    walks = []
    for w in inventory['walks']:
        r = lookup[w['row_id']]
        model = modeled[w['row_id']]
        if r['player_id'] != w['source']['player_id'] or r['origin_year'] != w['source']['origin_year']:
            raise ValueError('Changed source walk identity')
        walks.append(dict(coverage=r, source_context=w['source'], dated_employment=w['status']['employment'],
            job_inputs=w['reconstructed_professional_activity'], held_support=w['held_training_same_profile'],
            existing_forecasts={k: model[k] for k in ('current_p', 'current_conditional_pa', 'current_pa',
                'domestic_p', 'domestic_conditional_pa', 'domestic_pa', 'repaired_domestic_p',
                'repaired_domestic_conditional_pa', 'repaired_domestic_pa')},
            actual_MLB_PA=model['next_pa'], current_forecast_missing=bool(r['source_addition']),
            head_trace_reference=f'reports/generated/overseas-opportunity-inventory/inventory.json#row_id={w["row_id"]}'))
    selected = read(GEN / 'foreign-count-calibration/player-walks.json')['cases']
    ids = {w['coverage']['row_id'] for w in walks}
    for c in selected:
        for t in [c['trace'], *[p['trace'] for p in c['peers']]]:
            if t['forecast']['row_id'] not in ids: raise ValueError('Dropped earlier focal or peer')
    if len(selected) != 18 or len(walks) != 59: raise ValueError('Changed walk selection')
    save('coverage.json', dict(groups=groups, intake=intake, ledger=ledger, human_review_status='pending',
        new_fits=0, new_forecasts=0, exact_snapshot_day_known=False, no_accuracy_leaderboard=True))
    save('player-walks.json', dict(focal_origins=18, unique_walks=59, cases=walks, human_review_status='pending'))
    verify(hashes)
    print(json.dumps(dict(groups=groups, intake=intake, unique_walks=len(walks), new_fits=0), indent=2), flush=True)


if __name__ == '__main__': main()
