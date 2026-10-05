"""One same-matrix zero-offset hitting fit after completed error diagnosis."""
import argparse
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_compatible_value import labels
from universal_baseball.hitter_past_direct_value import fit
from universal_baseball.storage import sha256_file
from prepare_hitter_overseas_integration import annual_labels
from fit_practical_hitter_v31 import weights
from run_hitter_count_baseline import ROOT, GEN, OUT as COUNT, TARGET, FUTURE, read, verify, matrix
from run_hitter_past_direct_value import past_rate
from run_hitter_mlb_events_restoration import OUT as PREVIOUS

OUT = GEN / 'hitter-absolute-rate'
CONTRACT = ROOT / 'docs/hitter-absolute-rate-contract.md'


def save(name, value):
    import json
    p = OUT / name
    assert not p.exists(), f'Preserve {p}'
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8', newline='\n')


def prepare():
    assert not OUT.exists()
    diagnosis = read(GEN / 'hitter-restored-error-diagnosis/final-review.json'); verify(diagnosis['hashes'])
    verify(read(GEN / 'hitter-restored-error-diagnosis/receipt.json')['hashes'])
    assert diagnosis['player_walkthrough_status'] == 'complete'
    verify({diagnosis['public_report']: diagnosis['public_report_sha256']})
    final = read(PREVIOUS / 'final-review.json'); verify(final['hashes'])
    assert final['player_walkthrough_status'] == 'complete'
    verify({final['public_report']: final['public_report_sha256']})
    pre = read(PREVIOUS / 'preflight.json'); verify(pre['source_hashes'])
    for cell in read(PREVIOUS / 'fit-report.json')['cells']:
        verify(cell['hashes'])
    old_cases = read(PREVIOUS / 'player-walks.json')['cases']
    assert len(old_cases) == 17
    actual, env = annual_labels(pl.read_parquet(GEN / 'practical-hitter-v31/dated-stints.parquet'))
    checks, cases = [], []
    paths = [Path(__file__), CONTRACT, ROOT / 'src/universal_baseball/hitter_past_direct_value.py',
             ROOT / 'scripts/run_hitter_count_baseline.py', ROOT / 'scripts/run_hitter_past_direct_value.py',
             ROOT / 'scripts/prepare_practical_hitter_v33.py', ROOT / 'scripts/fit_practical_hitter_v31.py',
             ROOT / 'src/universal_baseball/forecast_validation.py', ROOT / 'tests/test_hitter_absolute_rate.py',
             GEN / 'practical-hitter-v31/dated-stints.parquet', PREVIOUS / 'final-review.json', PREVIOUS / 'preflight.json',
             PREVIOUS / 'predictions.parquet', PREVIOUS / 'player-walks.json', PREVIOUS / 'profile-support.parquet',
             PREVIOUS / 'feature-ranges.json', GEN / 'hitter-restored-error-diagnosis/final-review.json']
    for k in range(5):
        p = COUNT / f'features-{k}.parquet'; paths.append(p)
        f = pl.read_parquet(p)
        assert f.height == 63314 and f['target_year'].max() == 2025
        raw = np.array([actual.get((r['target_year'], r['player_id']), np.zeros(8)) for r in f.iter_rows(named=True)])
        assert np.array_equal(raw, f.select(TARGET).to_numpy())
        lab = labels(raw, np.array([env[y] for y in f['origin_year']]), np.array([env[y] for y in f['target_year']]), f['origin_replacement_rate'].to_numpy())
        assert np.allclose(lab['relative_rate'], f['actual_relative_rate'], atol=1e-10)
        for case in old_cases:
            o = case['forecast']
            if o['outer_fold'] != k:
                continue
            one = f.filter(pl.col('row_id') == case['row_id'])
            b = float(past_rate(one)[0]); assert np.isclose(b, case['past_baseline_rate'], atol=1e-10)
            cases.append(dict(row_id=case['row_id'], player_name=o['player_name'], origin=o['origin_year'], information_date=case['information_date'],
                              previous_baseline=b, previous_residual=case['fitted_residual'], previous_rate=o['components_rate'],
                              new_training_offset=0, new_prediction_offset=0, production_retained_in_identical_matrix=True,
                              fixed_fit_subtraction_not_candidate=o['components_rate'] - b,
                              immutable_source_model_walk_sha256=sha256_file(PREVIOUS / 'player-walks.json')))
        for c in [r for r in pre['cells'] if r['fold'] == k]:
            tr = f.filter(pl.col('row_id').is_in(c['training_row_ids']) & (pl.col('next_pa') > 0)).sort('row_id')
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert tr['target_year'].max() <= c['year'] and 2020 not in tr['target_year']
            for arm, names in pre['arms'].items():
                _, note = preflight(tr, te, cutoff=c['year'], fold=k, features=names, expected_keys=te.select('row_id', 'horizon').iter_rows())
                assert np.isfinite(matrix(tr, names)).all() and np.isfinite(matrix(te, names)).all()
                assert not set(names) & set(TARGET + FUTURE + ['actual_relative_rate', 'next_pa'])
                checks.append(dict(origin=c['year'], fold=k, arm=arm, note=note, active_training_rows=tr.height, active_training_people=tr['player_id'].n_unique()))
        print(f'Absolute-target labels, unchanged inputs, support and preflights checked for fold {k}.', flush=True)
    assert len(checks) == 105 and len(cases) == 17
    OUT.mkdir(parents=True)
    save('preflight.json', dict(before_fitting=True, checks_before_fits=105, checks=checks, arms=pre['arms'], cells=pre['cells'], fixed_case_row_ids=pre['fixed_case_row_ids'],
                                source_walks=cases, source_walkthrough_status='pending_readable_gate', alpha=100,
                                inherited_support='Identical source/units/matrix and full/active identities: seven-input full/active joint support and ranges remain applicable, including all gaps',
                                protected_outcomes_used=False, deployment_approved=False, source_hashes={str(p): sha256_file(p) for p in paths}))


def certify():
    pre = read(OUT / 'preflight.json'); verify(pre['source_hashes'])
    doc = ROOT / 'docs/hitter-absolute-rate-source-review.md'
    assert doc.exists() and pre['checks_before_fits'] == 105
    content = doc.read_text(encoding='utf8')
    for r in pre['source_walks']:
        assert str(r['row_id']) in content
    save('source-review.json', dict(approved_for_fixed_fit=True, source_walkthrough_status='complete', protected_outcomes_used=False,
                                    hashes={str(p): sha256_file(p) for p in [Path(__file__), doc, OUT / 'preflight.json']}))


def run_fit():
    pre = read(OUT / 'preflight.json'); verify(pre['source_hashes'])
    source = read(OUT / 'source-review.json'); verify(source['hashes'])
    assert source['approved_for_fixed_fit'] and not (OUT / 'fit-report.json').exists()
    seal = dict(runner_sha256=sha256_file(Path(__file__)), preflight_sha256=sha256_file(OUT / 'preflight.json'), source_review_sha256=sha256_file(OUT / 'source-review.json'))
    if (OUT / 'fit-seal.json').exists():
        assert read(OUT / 'fit-seal.json') == seal
    else:
        save('fit-seal.json', seal)
    previous = pl.read_parquet(PREVIOUS / 'predictions.parquet').sort('row_id')
    forecasts, receipts = [], []
    with threadpool_limits(limits=2):
        frames = {k: pl.read_parquet(COUNT / f'features-{k}.parquet') for k in range(5)}
        for c in pre['cells']:
            y, k = c['year'], c['fold']; p = OUT / f'forecast-{y}-{k}.parquet'
            if p.exists():
                note = read(OUT / f'fit-{y}-{k}.json'); verify(note['hashes']); receipts.append(note); forecasts.append(pl.read_parquet(p)); continue
            f = frames[k]
            tr = f.filter(pl.col('row_id').is_in(c['training_row_ids']) & (pl.col('next_pa') > 0)).sort('row_id')
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            q = previous.filter(pl.col('row_id').is_in(te['row_id'])).sort('row_id'); assert q['row_id'].equals(te['row_id'])
            candidate, heads, hashes = {}, [], {}
            for arm, names in pre['arms'].items():
                m = fit(matrix(tr, names), tr['actual_relative_rate'].to_numpy(), np.zeros(tr.height), weights(tr) * tr['next_pa'].to_numpy())
                path = OUT / f'{arm}-rate-{y}-{k}.joblib'; assert not path.exists(); joblib.dump(m, path, compress=3)
                hashes[str(path)] = sha256_file(path); candidate[arm] = m.predict(matrix(te, names))
                heads.append(dict(arm=arm, path=str(path), features=names, training_rows=tr.height, training_people=tr['player_id'].n_unique(), alpha=100,
                                  maximum_target_year=int(tr['target_year'].max()), training_offset=0, inference_offset=0))
            rate = np.where(te['prior_debut'].to_numpy() == 0, candidate['prospect'], np.where(te['sc_tracked'].to_numpy(), candidate['tracking'], candidate['base']))
            pa = q['components_pa'].to_numpy()
            q = q.with_columns(pl.Series('absolute_rate', rate), pl.Series('absolute_pa', pa), pl.Series('absolute_value', pa * (rate / 600 + q['origin_replacement_rate'].to_numpy())))
            assert np.isfinite(q.select('absolute_rate', 'absolute_pa', 'absolute_value').to_numpy()).all()
            q.write_parquet(p); hashes[str(p)] = sha256_file(p)
            note = dict(origin=y, fold=k, heads=heads, hashes=hashes); save(f'fit-{y}-{k}.json', note)
            receipts.append(note); forecasts.append(q)
            print(f'Fitted absolute-rate comparison {y}/{k}; sources and PA fixed.', flush=True)
    q = pl.concat(forecasts).sort('row_id')
    assert q.height == 30519 and q.select(previous.columns).equals(previous) and q['absolute_pa'].equals(q['components_pa'])
    q.write_parquet(OUT / 'predictions.parquet')
    save('fit-report.json', dict(new_heads=105, cells=receipts, rows=30519, predictions_sha256=sha256_file(OUT / 'predictions.parquet'),
                                player_walkthrough_status='pending', protected_outcomes_used=False, deployment_approved=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=['prepare', 'certify', 'fit'])
    {'prepare': prepare, 'certify': certify, 'fit': run_fit}[parser.parse_args().phase]()
