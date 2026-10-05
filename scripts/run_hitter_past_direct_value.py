"""One matched scalar-rate contrast; unchanged count inputs and playing time."""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_compatible_value import labels
from universal_baseball.hitter_past_direct_value import baseline, fit
from universal_baseball.storage import sha256_file
from prepare_hitter_overseas_integration import annual_labels
from fit_practical_hitter_v31 import weights
from run_hitter_count_baseline import ROOT, GEN, OUT as COUNT, FEATURES, REF, FUTURE, TARGET, read, verify, matrix

OUT = GEN / 'hitter-past-direct-value'
CONTRACT = ROOT / 'docs/hitter-past-direct-value-contract.md'


def save(name, value):
    p = OUT / name
    assert not p.exists(), f'Preserve {p}'
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False, default=str) + '\n', encoding='utf8', newline='\n')


def past_rate(f, training=False):
    return baseline(f.select(FEATURES[:8]).to_numpy(), f.select(FUTURE if training else REF).to_numpy())


def prepare():
    assert not OUT.exists()
    diagnosis = read(GEN / 'hitter-count-error-diagnosis/final-review.json')
    assert diagnosis['player_walkthrough_status'] == 'complete'
    verify(diagnosis['hashes'])
    previous = read(COUNT / 'final-review.json'); verify(previous['hashes'])
    pre = read(COUNT / 'preflight.json'); verify(pre['source_hashes'])
    cases = read(COUNT / 'player-walks.json')['cases']
    q = pl.read_parquet(COUNT / 'predictions.parquet').sort('row_id')
    actual, environments = annual_labels(pl.read_parquet(GEN / 'practical-hitter-v31/dated-stints.parquet'))
    paths = [Path(__file__), CONTRACT, ROOT / 'src/universal_baseball/hitter_past_direct_value.py', ROOT / 'tests/test_hitter_past_direct_value.py',
             COUNT / 'preflight.json', COUNT / 'final-review.json', COUNT / 'predictions.parquet', COUNT / 'player-walks.json', COUNT / 'review-qualification.json',
             COUNT / 'profile-support.parquet', COUNT / 'feature-ranges.json', GEN / 'hitter-count-error-diagnosis/final-review.json', GEN / 'practical-hitter-v31/dated-stints.parquet',
             ROOT / 'scripts/run_hitter_count_baseline.py', ROOT / 'scripts/fit_practical_hitter_v31.py', ROOT / 'scripts/prepare_practical_hitter_v33.py', ROOT / 'scripts/prepare_hitter_overseas_integration.py', ROOT / 'src/universal_baseball/forecast_validation.py']
    checks = []; walks = []
    OUT.mkdir(parents=True)
    for k in range(5):
        p = COUNT / f'features-{k}.parquet'; paths.append(p)
        f = pl.read_parquet(p)
        assert f['target_year'].max() == 2025 and f.height == 63314
        raw = np.array([actual.get((r['target_year'], r['player_id']), np.zeros(8)) for r in f.iter_rows(named=True)])
        assert np.array_equal(raw, f.select(TARGET).to_numpy())
        assert np.allclose(f.select(FUTURE).to_numpy(), np.array([environments[y] for y in f['target_year']]), atol=1e-12)
        lab = labels(raw, np.array([environments[y] for y in f['origin_year']]), f.select(FUTURE).to_numpy(), f['origin_replacement_rate'].to_numpy())
        assert np.allclose(lab['relative_rate'], f['actual_relative_rate'], atol=1e-10)
        for case in cases:
            o = case['forecast']
            if o['outer_fold'] != k: continue
            one = f.filter(pl.col('row_id') == case['row_id'])
            rate = float(past_rate(one)[0])
            assert np.isclose(rate, case['past_baseline_rate'], atol=1e-10)
            walks.append(dict(row_id=case['row_id'], player_name=o['player_name'], origin_year=o['origin_year'],
                              own_origin_baseline_rate=rate, training_baseline_uses_matured_training_environment=True,
                              source_walk_sha256=sha256_file(COUNT / 'player-walks.json')))
        for c in [c for c in pre['cells'] if c['fold'] == k]:
            tr = f.filter(pl.col('row_id').is_in(c['training_row_ids']) & (pl.col('next_pa') > 0)).sort('row_id')
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert tr['target_year'].max() <= c['year'] and 2020 not in tr['target_year']
            for arm, names in pre['arms'].items():
                check, note = preflight(tr, te, cutoff=c['year'], fold=k, features=names, expected_keys=te.select('row_id', 'horizon').iter_rows())
                assert np.isfinite(matrix(tr, names)).all() and np.isfinite(matrix(te, names)).all()
                checks.append(dict(year=c['year'], fold=k, arm=arm, note=note, training_rows=tr.height, training_people=tr['player_id'].n_unique(), test_rows=te.height))
        print(f'Checked unchanged matrix and direct-rate baselines, fold {k}.', flush=True)
    assert len(checks) == 105 and len(walks) == 13
    # Forecast scoring references, not feature-matrix replacement metadata.
    raw = np.array([actual.get((r['target_year'], r['player_id']), np.zeros(8)) for r in q.iter_rows(named=True)])
    lab = labels(raw, np.array([environments[y] for y in q['origin_year']]), np.array([environments[y] for y in q['target_year']]), q['origin_replacement_rate'].to_numpy())
    assert np.allclose(lab['relative_value'], q['actual_relative_value'], atol=1e-10)
    save('preflight.json', dict(before_fitting=True, checks_before_fits=len(checks), checks=checks, arms=pre['arms'], cells=pre['cells'],
          fixed_case_row_ids=[r['row_id'] for r in cases], source_walks=walks, source_walkthrough_status='complete', alpha=100,
          inherited_support='Same source/units/features, same active/full training memberships; count profile-support and feature-ranges remain applicable, including gaps.',
          protected_outcomes_used=False, deployment_approved=False, source_hashes={str(p): sha256_file(p) for p in paths}))


def run_fit():
    pre = read(OUT / 'preflight.json'); verify(pre['source_hashes'])
    assert pre['checks_before_fits'] == 105 and pre['source_walkthrough_status'] == 'complete'
    assert not (OUT / 'fit-report.json').exists()
    seal = dict(runner_sha256=sha256_file(Path(__file__)), preflight_sha256=sha256_file(OUT / 'preflight.json'))
    if (OUT / 'fit-seal.json').exists(): assert read(OUT / 'fit-seal.json') == seal
    else: save('fit-seal.json', seal)
    previous = pl.read_parquet(COUNT / 'predictions.parquet').sort('row_id')
    forecasts = []; receipts = []
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y, k = c['year'], c['fold']; p = OUT / f'forecast-{y}-{k}.parquet'
            if p.exists():
                note = read(OUT / f'fit-{y}-{k}.json'); verify(note['hashes']); receipts.append(note); forecasts.append(pl.read_parquet(p)); continue
            f = pl.read_parquet(COUNT / f'features-{k}.parquet')
            tr = f.filter(pl.col('row_id').is_in(c['training_row_ids']) & (pl.col('next_pa') > 0)).sort('row_id')
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            q = previous.filter(pl.col('row_id').is_in(te['row_id'])).sort('row_id')
            assert q['row_id'].equals(te['row_id'])
            train_base, test_base = past_rate(tr, True), past_rate(te)
            candidate = {}; heads = []; hashes = {}
            for arm, names in pre['arms'].items():
                m = fit(matrix(tr, names), tr['actual_relative_rate'].to_numpy(), train_base, weights(tr) * tr['next_pa'].to_numpy())
                path = OUT / f'{arm}-rate-{y}-{k}.joblib'; assert not path.exists(); joblib.dump(m, path, compress=3)
                hashes[str(path)] = sha256_file(path)
                candidate[arm] = test_base + m.predict(matrix(te, names))
                heads.append(dict(arm=arm, path=str(path), features=names, training_rows=tr.height, training_people=tr['player_id'].n_unique(), alpha=100, maximum_target_year=int(tr['target_year'].max())))
            rate = np.where(te['prior_debut'].to_numpy() == 0, candidate['prospect'], np.where(te['sc_tracked'].to_numpy(), candidate['tracking'], candidate['base']))
            pa = q['count_pa'].to_numpy()
            q = q.with_columns(pl.Series('scalar_rate', rate), pl.Series('scalar_baseline_rate', test_base), pl.Series('scalar_pa', pa),
                               pl.Series('scalar_value', pa * (rate / 600 + q['origin_replacement_rate'].to_numpy())))
            assert np.isfinite(q.select('scalar_rate', 'scalar_pa', 'scalar_value').to_numpy()).all()
            q.write_parquet(p); hashes[str(p)] = sha256_file(p)
            note = dict(origin=y, fold=k, heads=heads, hashes=hashes); save(f'fit-{y}-{k}.json', note)
            receipts.append(note); forecasts.append(q)
            print(f'Fitted matched direct-rate heads {y}/{k}; fixed jobs.', flush=True)
    q = pl.concat(forecasts).sort('row_id')
    assert q.height == 30519 and q.select(previous.columns).equals(previous) and q['scalar_pa'].equals(q['count_pa'])
    q.write_parquet(OUT / 'predictions.parquet')
    save('fit-report.json', dict(new_heads=105, cells=receipts, rows=q.height, predictions_sha256=sha256_file(OUT / 'predictions.parquet'), player_walkthrough_status='pending', protected_outcomes_used=False, deployment_approved=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=['prepare', 'fit']); args = parser.parse_args()
    {'prepare': prepare, 'fit': run_fit}[args.phase]()
