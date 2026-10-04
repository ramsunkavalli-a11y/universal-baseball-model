"""Verify every exported forecast/input and assemble a matched hitting benchmark.

This is explorer QA, not another fitted model or a new statistical disposition.
The original builder receipt is retained. The additional benchmark artifact and
this verification have their own hashes; browser verification is separate.
"""
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import polars as pl

import build_hitter_risk_research_explorer as b
from prepare_practical_hitter_v33 import safe_matrix
from universal_baseball.storage import sha256_file


def validate_row(r, source):
    assert r['row_id'] == source['row_id']
    assert r['player_id'] == source['player_id']
    assert r['player_name'] == source['player_name']
    assert r['target_year'] == source['target_year'] == r['origin_year'] + 1
    assert r['target_year'] <= 2025
    for out, original in [('rate', 'preseason_rate'), ('p', 'preseason_p'),
            ('conditional_pa', 'preseason_conditional_pa'), ('pa', 'preseason_pa'),
            ('value', 'preseason_value'), ('replacement_rate', 'origin_replacement_rate'),
            ('next_pa', 'next_pa'), ('next_value', 'next_value')]:
        assert r[out] == source[original], (r['row_id'], out)
    assert math.isclose(r['pa'], r['p'] * r['conditional_pa'], abs_tol=1e-10)
    assert math.isclose(r['value'], r['pa'] * (r['rate']/600 + r['replacement_rate']), abs_tol=1e-10)
    if r['next_pa'] == 0:
        assert r['next_rate'] is None and r['next_value'] == 0
    else:
        assert r['next_rate'] == source['next_batting_rate']
        assert math.isclose(r['next_value'], r['next_pa'] * (r['next_rate']/600 + r['replacement_rate']), abs_tol=1e-10)
    for a in b.ARMS:
        expected = [source[a+'_'+s] for s in ['q10', 'q50', 'q90', 'p_negative', 'p_two', 'impossible_mass']]
        assert r['ranges'][a] == expected
        assert expected[0] <= expected[1] <= expected[2]
        assert all(0 <= x <= 1 for x in expected[3:])
        if a in ['associated', 'independent']:
            assert expected[-1] == 0


def matched_rates(q):
    pub = q.filter((pl.col('pa_0') > 0) & pl.col('steamer_index').is_not_null() & pl.col('zips_index').is_not_null())
    assert len(pub) == 2627
    active = pub.filter(pl.col('next_pa') > 0)
    assert len(active) == 2088
    rates = {}
    for label, col in [('baseline', 'preseason_rate'), ('steamer', 'steamer_rate'), ('zips', 'zips_rate')]:
        errors = []
        for year in sorted(active['target_year'].unique()):
            g = active.filter(pl.col('target_year') == year)
            delta = g[col].to_numpy() - g['next_batting_rate'].to_numpy()
            weight = g['next_pa'].to_numpy()
            errors.append([np.average(delta**2, weights=weight), np.average(abs(delta), weights=weight)])
        mean = np.mean(errors, axis=0)
        rates[label] = dict(rmse=float(np.sqrt(mean[0])), mae=float(mean[1]))
    return dict(public_rows=len(pub), active_rows=len(active), rates=rates,
        unit='Fixed-event batting wins per 600 PA, common origin environment; not official WAR',
        weighting='Equal target years; actual PA within year')


def main():
    report_path = b.OUT/'build-report.json'
    receipt = b.e.read(report_path)
    b.e.old.check_hashes(receipt['source_hashes'])
    b.e.old.check_hashes(receipt['saved_head_hashes'])
    for rel, h in receipt['output_hashes'].items():
        assert sha256_file(b.DIST/rel) == h, rel
    meta = b.e.read(b.DIST/'metadata.json')
    q = pl.read_parquet(b.e.WORK/'scored-predictions.parquet').sort('row_id')
    f = b.e.old.context().filter(pl.col('row_id').is_in(q['row_id'].to_list())).sort('row_id')
    assert f['row_id'].equals(q['row_id'])
    rx = safe_matrix(f, meta['rate_features'])
    px = f.select(meta['opportunity_features']).to_numpy()
    source = {r['row_id']: r for r in q.iter_rows(named=True)}
    inputs = {rid: i for i, rid in enumerate(q['row_id'])}
    contexts = {r['row_id']: r for r in pl.read_parquet(b.TEAM/'features.parquet').iter_rows(named=True)}
    reviewed = {c['origin']['row_id']: c for c in b.e.read(b.e.OUT/'reviewed-cases.json')}
    hist = pl.read_parquet(b.e.ROOT/'reports/generated/practical-hitter-v31/counts.parquet').filter(pl.col('season') <= 2024)
    raw = {}
    for h in hist.iter_rows(named=True):
        raw.setdefault(h['player_id'], []).append([h[k] for k in b.HISTORY_FIELDS])
    seen = set(); nonarrivals = 0; unknown = 0; org_counts = {}
    for year in meta['target_years']:
        chunk = b.e.read(b.DIST/f'years/{year}.json')
        ids = {r['player_id'] for r in chunk['rows']}
        assert set(chunk['history']) == {str(p) for p in ids}
        for pid in ids:
            expected = sorted([h for h in raw.get(pid, []) if year-3 <= h[0] <= year-1], key=lambda h: (h[0], h[1]))
            assert chunk['history'][str(pid)] == expected, ('source history', year, pid)
        for r in chunk['rows']:
            rid = r['row_id']; assert rid not in seen; seen.add(rid)
            validate_row(r, source[rid]); assert r['target_year'] == year
            c = contexts[rid]
            org = c['context_parent'] if c['context_reason'] == 'known' and c['context_parent'] is not None else 'Unknown affiliation'
            assert r['org'] == org and r['team_basis'] == c['context_basis']
            assert r['information_date'] == meta['information_dates'][str(year)]
            assert r['reviewed'] == (rid in reviewed)
            unknown += org == 'Unknown affiliation'; nonarrivals += r['next_pa'] == 0
            key = str(year)+'|'+org; org_counts[key] = org_counts.get(key, 0)+1
            z = b.e.read(b.DIST/f'details/{rid}.json'); i = inputs[rid]
            assert z['row_id'] == rid
            assert z['rate_inputs'] == b.encoded(rx[i])
            assert z['opportunity_inputs'] == b.encoded(px[i])
            assert len(z['rate_contributions']) == len(meta['rate_features']) == 199
            assert all(x is not None for x in z['rate_contributions'])
            assert math.isclose(z['rate_intercept']+sum(z['rate_contributions']), r['rate'], abs_tol=1e-10)
            assert z['replayed_rate'] == r['rate'] or math.isclose(z['replayed_rate'], r['rate'], abs_tol=1e-10)
            if rid in reviewed:
                review = b.e.read(b.DIST/f'reviews/{rid}.json')
                assert review['note'] == reviewed[rid]['baseball_review']
                assert review['peers'] == reviewed[rid]['peers']
        print('Verified complete exported source/input/forecast rows', year, len(chunk['rows']), flush=True)
    assert seen == set(source) and len(seen) == 30506
    assert len(list((b.DIST/'details').glob('*.json'))) == 30506
    assert len(reviewed) == len(list((b.DIST/'reviews').glob('*.json'))) == 18
    assert unknown == receipt['unknown_affiliations']
    assert len(receipt['actual_rate_and_opportunity_model_replays']) == 35
    assert len(receipt['saved_head_hashes']) == 105
    benchmark_path = b.e.old.VALUE/'scores.json'
    scores = next(s for s in b.e.read(benchmark_path) if s['scope'] == 'public_broad')
    benchmark = matched_rates(q)
    for arm in benchmark['rates']:
        for metric in ['rmse', 'mae']:
            assert math.isclose(benchmark['rates'][arm][metric], scores['rates'][arm][metric], abs_tol=1e-10)
    b.write(b.DIST/'hitting-benchmark.json', benchmark)
    freeze = json.loads(subprocess.check_output([str(b.e.ROOT/'.venv/Scripts/python.exe'), '-X', 'utf8',
        str(b.e.ROOT/'scripts/verify_hitter_full_2026_freeze.py')], cwd=b.e.ROOT))
    assert freeze['status'] == 'verified' and freeze['protected_2026_opened'] is False
    b.e.write(b.OUT/'data-verification.json', dict(forecasts_verified=len(seen),
        complete_input_files_verified=len(seen), reviewed_walkthroughs=18, nonarrival_rates_unobserved=nonarrivals,
        unknown_affiliations=unknown, organization_year_counts=org_counts,
        history_joins_and_cutoffs_verified=True, exact_saved_inputs_verified=True,
        expected_and_actual_value_arithmetic_verified=True, all_four_saved_ranges_verified=True,
        public_hitting_benchmarks_independently_recomputed=benchmark,
        source_hashes={str(report_path): sha256_file(report_path), str(Path(__file__)): sha256_file(Path(__file__)),
            str(benchmark_path): sha256_file(benchmark_path)},
        extra_artifact_hashes={'hitting-benchmark.json': sha256_file(b.DIST/'hitting-benchmark.json')},
        frozen_verification=freeze, browser_verification_status='pending',
        new_models_fitted=0, research_only=True, full_goal_complete=False))
    print('Explorer data verified; browser QA remains separate.', flush=True)


if __name__ == '__main__':
    main()
