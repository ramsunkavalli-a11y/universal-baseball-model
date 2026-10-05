"""One fixed opportunity contrast after reviewing nonmedical observation sources."""
import argparse
from pathlib import Path
import subprocess
import sys

import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

import run_hitter_employment_comparison as recipe
from universal_baseball.nonmedical_opportunity import FIELDS, OBS, sources, frame, support
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights

ROOT, GEN = recipe.ROOT, recipe.GEN
BASE = GEN / 'hitter-employment-comparison-v2'
SOURCE = GEN / 'hitter-nonmedical-observation'
OUT = GEN / 'hitter-nonmedical-opportunity'
read, verify = recipe.read, recipe.verify


def save(name, payload):
    recipe.OUT = OUT
    recipe.save(name, payload)


def prepare():
    if OUT.exists():
        raise ValueError('Preserve execution; no automatic restart')
    for folder in [SOURCE, BASE]:
        final = read(folder / 'final-review.json')
        assert final['player_walkthrough_status'] == 'complete'
        verify(final['hashes'])
    oldpre = read(BASE / 'preflight.json')
    verify(oldpre['hashes'])
    fit = read(BASE / 'fit-report.json')
    assert sha256_file(BASE / 'predictions.parquet') == fit['predictions_sha256']
    check = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
        'tests/test_nonmedical_observation.py', 'tests/test_nonmedical_opportunity.py'],
        cwd=ROOT, capture_output=True, text=True)
    if check.returncode:
        raise ValueError(check.stdout + check.stderr)
    observations = {r['candidate_key']: r for r in pl.read_parquet(SOURCE / 'observations.parquet').to_dicts()}
    source = sources(read(GEN / 'hitter-status-evidence-v2/status-ledger.json')['rows'], observations)
    assert source.height == 83300
    job_features = [OBS.get(n, n) for n in oldpre['job_features']]
    assert len(job_features) == len(set(job_features)) == 293
    assert sum(a != b for a, b in zip(job_features, oldpre['job_features'], strict=True)) == 8
    paths = [Path(__file__), ROOT / 'src/universal_baseball/nonmedical_opportunity.py',
        ROOT / 'tests/test_nonmedical_opportunity.py', ROOT / 'docs/hitter-nonmedical-opportunity-contract.md',
        ROOT / 'src/universal_baseball/forecast_validation.py', ROOT / 'scripts/fit_practical_hitter_v31.py',
        SOURCE / 'final-review.json', SOURCE / 'observations.parquet',
        GEN / 'hitter-status-evidence-v2/status-ledger.json', BASE / 'final-review.json',
        BASE / 'preflight.json', BASE / 'fit-report.json', BASE / 'predictions.parquet']
    paths += [BASE / f'features-{k}.parquet' for k in range(5)]
    paths += [ROOT / h['path'] for c in fit['cells'] for h in c['heads']]
    OUT.mkdir()
    save('source-seal.json', dict(before_fitting=True, hashes={str(p.relative_to(ROOT)): sha256_file(p) for p in paths}))
    source.write_parquet(OUT / 'source-inputs.parquet')
    paths.append(OUT / 'source-inputs.parquet')
    frames = {}
    marks = None
    for k in range(5):
        old = pl.read_parquet(BASE / f'features-{k}.parquet').sort('row_id')
        new = frame(old, source)
        assert new.height == 63314
        new.write_parquet(OUT / f'features-{k}.parquet')
        paths.append(OUT / f'features-{k}.parquet')
        frames[k] = new
        if k == 0:
            changed = np.any(new.select(FIELDS).to_numpy() != new.select(list(OBS.values())).to_numpy(), axis=1)
            marks = new.select('row_id').with_columns(pl.Series('observation_input_changed', changed))
    q = pl.read_parquet(BASE / 'predictions.parquet').sort('row_id')
    assert q.height == 30519 and q['target_year'].max() == 2025
    checks, profiles, ranges = [], [], []
    for c in oldpre['cells']:
        y, k = c['year'], c['fold']
        f = frames[k]
        tr = f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
        te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
        assert tr['ctx_information_date'].max() < te['ctx_information_date'].min()
        assert te['row_id'].equals(q.filter((pl.col('origin_year') == y) & (pl.col('outer_fold') == k))['row_id'])
        for arm, names in [('corrected_job', oldpre['job_features']), ('observation', job_features)]:
            for head, sub in [('participation', tr), ('conditional_pa', tr.filter(pl.col('next_pa') > 0))]:
                checked, note = preflight(sub, te, cutoff=y, fold=k, features=names,
                    expected_keys=te.select('row_id', 'horizon').iter_rows())
                d = support(sub, te, observation=arm == 'observation').join(checked.select(
                    'row_id', 'extrapolation', 'sparse_profile'), on='row_id', validate='1:1').with_columns(
                    pl.lit(arm).alias('arm'), pl.lit(head).alias('head'),
                    pl.lit(y).alias('origin'), pl.lit(k).alias('fold'))
                profiles.append(d)
                checks.append(dict(arm=arm, head=head, origin=y, fold=k, **note,
                    exact_profile_zero=int((d['profile_people'] == 0).sum()),
                    exact_profile_under20=int((d['profile_people'] < 20).sum())))
                low, high = sub.select(names).to_numpy().min(axis=0), sub.select(names).to_numpy().max(axis=0)
                outside = ((te.select(names).to_numpy() < low) | (te.select(names).to_numpy() > high)).sum(axis=0)
                ranges.extend(dict(arm=arm, head=head, origin=y, fold=k, feature=n,
                    minimum=float(a), maximum=float(b), test_outside=int(v))
                    for n, a, b, v in zip(names, low, high, outside, strict=True))
    replayed = 0
    with threadpool_limits(limits=2):
        for c in fit['cells']:
            y, k = c['origin'], c['fold']
            te = frames[k].filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            g = q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            for h in c['heads']:
                path = ROOT / h['path']
                assert sha256_file(path) == h['sha256']
                assert h['features'] == oldpre['job_features']
                m = joblib.load(path)
                cls = HistGradientBoostingClassifier if h['head'] == 'participation' else HistGradientBoostingRegressor
                assert m.get_params() == cls(**oldpre['settings']).get_params()
                x = te.select(h['features']).to_numpy()
                v = m.predict_proba(x)[:, 1] if h['head'] == 'participation' else m.predict(x)
                col = 'corrected_job_raw_p' if h['head'] == 'participation' else 'corrected_job_raw_conditional_pa'
                assert np.allclose(v, g[col], atol=1e-10, rtol=0)
                replayed += 1
    assert len(checks) == 140 and replayed == 70
    marks.write_parquet(OUT / 'source-changes.parquet')
    pl.concat(profiles).write_parquet(OUT / 'profile-support.parquet')
    save('feature-ranges.json', dict(rows=ranges))
    save('preflight.json', dict(before_fitting=True, checks=checks, cells=oldpre['cells'],
        settings=oldpre['settings'], job_features=job_features, baseline_features=oldpre['job_features'],
        baseline_heads_replayed=70, source_rows=63314, evaluation_rows=30519,
        changed_source_input_rows=int(marks['observation_input_changed'].sum()),
        new_fits=0, player_walkthrough_status='pending', deployment_approved=False,
        hashes={str(p.relative_to(ROOT)): sha256_file(p) for p in paths + [OUT / 'source-changes.parquet',
            OUT / 'profile-support.parquet', OUT / 'feature-ranges.json', OUT / 'source-seal.json']}))
    verify(read(OUT / 'source-seal.json')['hashes'])
    print(__import__('json').dumps(dict(preflight='complete', checks=140, baseline_heads_replayed=70,
        changed_source_input_rows=int(marks['observation_input_changed'].sum()), new_fits=0)), flush=True)


def fit():
    pre = read(OUT / 'preflight.json')
    verify(pre['hashes'])
    if (OUT / 'fit-report.json').exists() or list(OUT.glob('model-*.joblib')) or list(OUT.glob('forecast-*.parquet')):
        raise ValueError('Preserve existing fit execution; do not restart')
    assert len(pre['checks']) == 140 and pre['baseline_heads_replayed'] == 70
    save('fit-seal.json', dict(before_fitting=True, preflight_sha256=sha256_file(OUT / 'preflight.json')))
    q = pl.read_parquet(BASE / 'predictions.parquet').sort('row_id')
    parts, cells = [], []
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y, k = c['year'], c['fold']
            f = pl.read_parquet(OUT / f'features-{k}.parquet')
            tr = f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            g = q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert te['row_id'].equals(g['row_id'])
            heads, pred = [], {}
            for head, sub, cls, target in [('participation', tr, HistGradientBoostingClassifier, 'next_active'),
                ('conditional_pa', tr.filter(pl.col('next_pa') > 0), HistGradientBoostingRegressor, 'next_pa')]:
                m = cls(**pre['settings'])
                names = pre['job_features']
                m.fit(sub.select(names).to_numpy(), sub[target].to_numpy(), sample_weight=weights(sub))
                path = OUT / f'model-{head}-{y}-{k}.joblib'
                joblib.dump(m, path, compress=3)
                heads.append(dict(head=head, path=str(path.relative_to(ROOT)), sha256=sha256_file(path),
                    origin=y, fold=k, training_rows=sub.height, training_people=sub['player_id'].n_unique(),
                    maximum_training_target=int(sub['target_year'].max()), features=names))
                x = te.select(names).to_numpy()
                pred[head] = m.predict_proba(x)[:, 1] if head == 'participation' else m.predict(x)
            probability = pred['participation'].copy()
            probability[(te['status_hard_unavailable'].to_numpy() > 0) | (te['status_retired'].to_numpy() > 0)] = 0
            conditional = np.clip(pred['conditional_pa'], 1, 800)
            pa = probability * conditional
            rate = g['corrected_job_rate'].to_numpy()
            g = g.with_columns(pl.Series('observation_raw_p', pred['participation']),
                pl.Series('observation_raw_conditional_pa', pred['conditional_pa']),
                pl.Series('observation_p', probability), pl.Series('observation_conditional_pa', conditional),
                pl.Series('observation_pa', pa), pl.Series('observation_rate', rate),
                pl.Series('observation_value', pa * (rate / 600 + g['origin_replacement_rate'].to_numpy())))
            assert g.select(q.columns).equals(q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id'))
            assert np.isfinite(g.select([n for n in g.columns if n.startswith('observation_')]).to_numpy()).all()
            path = OUT / f'forecast-{y}-{k}.parquet'
            g.write_parquet(path)
            note = dict(origin=y, fold=k, heads=heads, predictions_path=str(path.relative_to(ROOT)),
                        predictions_sha256=sha256_file(path), test_row_ids=c['test_row_ids'])
            save(f'fit-{y}-{k}.json', note)
            cells.append(note)
            parts.append(g)
            print(__import__('json').dumps(dict(fitted_origin=y, fold=k, heads=2, rows=g.height)), flush=True)
    result = pl.concat(parts).sort('row_id')
    assert result.height == 30519 and result.select(q.columns).equals(q)
    result = result.join(pl.read_parquet(OUT / 'source-changes.parquet'), on='row_id', validate='1:1')
    result.write_parquet(OUT / 'predictions.parquet')
    save('fit-report.json', dict(cells=cells, new_heads=70, rows=30519,
        predictions_sha256=sha256_file(OUT / 'predictions.parquet'), player_walkthrough_status='pending',
        deployment_approved=False, completed_2026_evaluation_unchanged=True))
    verify(pre['hashes'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['prepare', 'fit'])
    {'prepare': prepare, 'fit': fit}[parser.parse_args().phase]()
