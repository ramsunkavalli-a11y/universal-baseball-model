"""Separate preparation and fitting; historical targets stop in 2025."""
from collections import defaultdict
import argparse
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from prepare_foreign_borrowed_stability import data, CachedReferences
from universal_baseball.foreign_component_translation import profile, training_pairs
from universal_baseball.foreign_component_translation_v2 import histories
from universal_baseball.foreign_count_calibration import fit, fresh_foreign_route
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / 'reports/generated'
OUT = GEN / 'foreign-count-calibration'
PRIOR = GEN / 'foreign-borrowed-stability'
REP = GEN / 'hitter-evidence-representation'
SOURCES = GEN / 'foreign-origin-inputs'
CONTRACT = ROOT / 'docs/hitter-foreign-count-calibration-contract.md'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def save(name, value):
    path = OUT / name
    if path.exists():
        raise ValueError(f'Existing execution artifact; inspect rather than overwrite: {path}')
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf8', newline='\n')


def verify(mapping):
    for p, h in mapping.items():
        path = Path(p)
        if not path.is_absolute():
            path = ROOT / path
        if sha256_file(path) != h:
            raise ValueError(f'Changed sealed input: {path}')


def loaded():
    rows, domestic = data()
    refs = CachedReferences(rows)
    history = histories(rows)
    pairs = read(SOURCES / 'pair-role-evidence.json')['pairs']
    source = {r['candidate_key']: r for r in read(SOURCES / 'origin-inputs.json')['rows']}
    return domestic, refs, history, pairs, source


def prepare():
    if OUT.exists():
        raise ValueError('Inspect existing preparation; do not restart')
    last = read(PRIOR / 'final-review.json')
    if last['player_walkthrough_status'] != 'complete_for_component_comparison':
        raise ValueError('Prior component review incomplete')
    verify(last['source_hashes']); verify(last['artifact_hashes'])
    review = read(REP / 'final-review.json')
    if review['player_walkthrough_status'] != 'complete':
        raise ValueError('Prior whole-model review incomplete')
    verify(review['hashes'])
    tests = subprocess.run([sys.executable, '-m', 'pytest', '-q', 'tests/test_foreign_count_calibration.py'],
                           cwd=ROOT, capture_output=True, text=True)
    if tests.returncode:
        raise RuntimeError(tests.stdout + tests.stderr)
    q = pl.read_parquet(REP / 'predictions.parquet').sort('row_id')
    if q.height != 30519 or q['target_year'].max() != 2025 or q['row_id'].n_unique() != q.height:
        raise ValueError('Changed fixed comparison population')
    domestic, refs, history, pairs, source = loaded()
    raw = pl.read_parquet(GEN / 'practical-hitter-v31/counts.parquet').filter(pl.col('season') <= 2024)
    byperson = defaultdict(list)
    for r in raw.to_dicts():
        byperson[r['player_id']].append(r)
    oldfits = {(m['cutoff'], tuple(m['excluded_folds'])): m for m in read(PRIOR / 'fits.json')['fits']}
    oldprofiles = {(p['candidate_key'], p['outer_fold']): p for p in read(PRIOR / 'profiles.json')['profiles']}
    routes = []
    for r in q.to_dicts():
        y, k, pid = r['origin_year'], r['outer_fold'], r['player_id']
        key = f'{y}:{pid}'; s = source.get(key); p = oldprofiles.get((key, k))
        route = fresh_foreign_route(s, byperson[pid], y)
        if s and (p is None or p['excluded_folds'] != [k] or p['origin_year'] != y):
            raise ValueError('Missing held-player foreign profile')
        routes.append(dict(row_id=r['row_id'], candidate_key=key, **route,
            foreign_source_present=s is not None, supported=p is not None and not p['missing_translation'],
            age=r['age'], prior_debut=r['prior_debut'], source_addition=r['source_addition'],
            recent_foreign_pa=s['recent_foreign_pa'] if s else 0,
            dated_hitter_hint=s['dated_role_hint'] if s else 'no_foreign_source'))
    cells = []
    for y, k in sorted(set(q.select('origin_year', 'outer_fold').iter_rows())):
        selected = [p for p in domestic if p['target_year'] <= y and p['fold'] != k]
        movers = training_pairs(pairs, y, [k])
        old = oldfits[y, (k,)]
        keys = [[p['player_id'], p['source_year']] for p in selected]
        if keys != old['domestic_keys'] or len(movers) != len(old['foreign_pairs']):
            raise ValueError('Changed calibration membership')
        if any(p['target_year'] > y or p['fold'] == k for p in selected):
            raise ValueError('Leaking chronological/player calibration')
        for p in selected:
            refs.get('MLB', p['target_year'], [k])
            for s in p['history']:
                if s['season'] > p['source_year']:
                    raise ValueError('Future source history')
                refs.get('MLB', s['season'], [k])
        group = q.filter((pl.col('origin_year') == y) & (pl.col('outer_fold') == k))
        members = [route['candidate_key'] for route in routes if route['row_id'] in set(group['row_id']) and route['foreign_source_present']]
        cells.append(dict(origin=y, fold=k, domestic_keys=keys,
            domestic_people=len({p['player_id'] for p in selected}),
            domestic_pairs=len(selected), foreign_movers=len(movers),
            foreign_people_by_league=old['people_by_league'],
            retained_foreign_keys=[[p['player_id'], p['a'], p['from_year'], p['through_year']] for p in movers],
            maximum_target=max(p['target_year'] for p in selected),
            domestic_profile_support=old['domestic_profile_support'],
            foreign_profile_members=members, evaluation_ids=group['row_id'].to_list()))
    paths = [CONTRACT, Path(__file__), ROOT / 'src/universal_baseball/foreign_count_calibration.py',
        ROOT / 'tests/test_foreign_count_calibration.py', PRIOR / 'final-review.json', PRIOR / 'fits.json',
        PRIOR / 'profiles.json', PRIOR / 'domestic-calibration.json', REP / 'final-review.json',
        REP / 'predictions.parquet', SOURCES / 'origin-inputs.json', SOURCES / 'pair-role-evidence.json',
        GEN / 'practical-hitter-v31/counts.parquet', GEN / 'practical-hitter-v31/dated-stints.parquet',
        GEN / 'hitter-minor-statcast-precision/scored-predictions.parquet',
        ROOT / 'src/universal_baseball/hitter_compatible_value.py',
        ROOT / 'src/universal_baseball/hitter_direct_events.py',
        ROOT / 'src/universal_baseball/foreign_borrowed_stability.py',
        ROOT / 'src/universal_baseball/foreign_component_translation.py',
        ROOT / 'src/universal_baseball/foreign_component_translation_v2.py',
        ROOT / 'scripts/prepare_foreign_borrowed_stability.py',
        ROOT / 'scripts/prepare_foreign_component_translation.py',
        ROOT / 'scripts/prepare_hitter_overseas_integration.py']
    OUT.mkdir()
    save('preflight.json', dict(cells=cells, routes=routes, before_all_fits=True, new_fits=0,
        original_evaluation_rows=30506, source_additions=13, tests=tests.stdout,
        source_hashes={**last['source_hashes'], **{str(p.relative_to(ROOT)): sha256_file(p) for p in paths}},
        target_year_maximum=2025, source_year_maximum=2024, player_walkthrough_status='pending',
        deployment_approved=False, frozen_2026_forecasts_changed=False))
    print(json.dumps(dict(cells=len(cells), forecasts=len(routes), foreign_sources=sum(r['foreign_source_present'] for r in routes),
                         route_eligible=sum(r['eligible'] for r in routes), new_fits=0, tests=tests.stdout)), flush=True)


def run():
    pre = read(OUT / 'preflight.json'); verify(pre['source_hashes'])
    if (OUT / 'fit-report.json').exists() or list(OUT.glob('fit-*.json')):
        raise ValueError('Inspect actual prior execution before any resume')
    domestic, refs, history, pairs, sources = loaded()
    cache = {}; fits = []; profiles = []
    with threadpool_limits(limits=2):
        for cell in pre['cells']:
            y, k = cell['origin'], cell['fold']
            model = fit(domestic, pairs, history, refs, y, [k], cache)
            if model['domestic_keys'] != cell['domestic_keys'] or model['people_by_league'] != cell['foreign_people_by_league']:
                raise ValueError('Fit violated preflight membership')
            model['domestic_profile_support'] = cell['domestic_profile_support']
            model['fit_key'] = f'{y}-{k}'
            for key in cell['foreign_profile_members']:
                p = profile(sources[key], model, refs)
                for piece in p['leagues']:
                    piece['domestic_coordinate_extrapolation'] = [j for j, x in enumerate(piece['source_relative_clr'])
                        if x < model['domestic_x_min'][j] or x > model['domestic_x_max'][j]]
                profiles.append(dict(**p, outer_fold=k, fit_key=model['fit_key']))
            save(f'fit-{y}-{k}.json', model); fits.append(model)
            print(f'Completed count calibration {y}/{k}; {model["domestic_pairs"]} domestic pairs.', flush=True)
    save('profiles.json', dict(profiles=profiles))
    save('fit-report.json', dict(cells=len(fits), new_domestic_vector_fits=len(fits),
        new_foreign_offset_fits=sum(sum(n > 0 for n in m['people_by_league'].values()) for m in fits),
        profiles=len(profiles), missing_profiles=sum(p['missing_translation'] for p in profiles),
        preflight_sha256=sha256_file(OUT / 'preflight.json'),
        hashes={str(p.relative_to(ROOT)): sha256_file(p) for p in [OUT / 'profiles.json', *sorted(OUT.glob('fit-*.json'))]},
        player_walkthrough_status='pending', score_status='not_started', deployment_approved=False,
        frozen_2026_forecasts_changed=False))
    print(json.dumps(dict(cells=len(fits), profiles=len(profiles), status='fit_complete_review_pending')), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['prepare', 'fit'])
    {'prepare': prepare, 'fit': run}[parser.parse_args().action]()
