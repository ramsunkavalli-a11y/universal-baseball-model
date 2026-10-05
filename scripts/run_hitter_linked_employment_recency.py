"""One sealed employment-age interaction; fixed hitting, folds and settings."""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

from universal_baseball.forecast_validation import preflight
from universal_baseball.linked_employment_recency import NEW, transform, feature_names, support
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights
from run_hitter_employment_comparison import read, verify

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'reports/generated/hitter-nonmedical-opportunity'
OUT = ROOT / 'reports/generated/hitter-linked-employment-recency'
FIXED = [(665487, 2022), (656555, 2023), (628356, 2017), (453056, 2018),
         (666158, 2023), (474832, 2023), (680757, 2021), (592450, 2024)]


def save(name, value):
    path = OUT / name
    if path.exists():
        raise FileExistsError(f'Preserve {path}')
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False, default=str) + '\n',
                    encoding='utf8', newline='\n')


def prepare():
    assert not OUT.exists(), 'Preserve existing preparation'
    final = read(BASE / 'final-review.json')
    assert final['player_walkthrough_status'] == 'complete'
    verify(final['hashes'])
    old = read(BASE / 'preflight.json')
    verify(old['hashes'])
    names = feature_names(old['job_features'])
    assert len(names) == 293
    fit = read(BASE / 'fit-report.json')
    q = pl.read_parquet(BASE / 'predictions.parquet').sort('row_id')
    assert sha256_file(BASE / 'predictions.parquet') == fit['predictions_sha256']
    assert q.height == 30519 and q['target_year'].max() == 2025
    cases = []
    for pid, year in FIXED:
        case = q.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == year))
        assert case.height == 1, (pid, year)
        cases.append(int(case['row_id'][0]))
    paths = [Path(__file__), ROOT / 'docs/hitter-linked-employment-recency-contract.md',
        ROOT / 'src/universal_baseball/linked_employment_recency.py', ROOT / 'tests/test_linked_employment_recency.py',
        ROOT / 'src/universal_baseball/forecast_validation.py', ROOT / 'scripts/fit_practical_hitter_v31.py',
        BASE / 'preflight.json', BASE / 'fit-report.json', BASE / 'predictions.parquet', BASE / 'final-review.json']
    frames, checks, profiles = {}, [], []
    # Validate all sources before creating output, to avoid a half-written prep.
    for k in range(5):
        path = BASE / f'features-{k}.parquet'
        oldframe = pl.read_parquet(path).sort('row_id')
        frames[k] = transform(oldframe)
        assert frames[k].select(oldframe.columns).equals(oldframe)
        paths.append(path)
    replayed = 0
    with threadpool_limits(limits=2):
        for c in fit['cells']:
            y, k = c['origin'], c['fold']
            te = frames[k].filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            g = q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert te['row_id'].equals(g['row_id'])
            for h in c['heads']:
                path = ROOT / h['path']
                assert sha256_file(path) == h['sha256']
                assert h['features'] == old['job_features']
                model = joblib.load(path)
                cls = HistGradientBoostingClassifier if h['head'] == 'participation' else HistGradientBoostingRegressor
                assert model.get_params() == cls(**old['settings']).get_params()
                x = te.select(h['features']).to_numpy()
                pred = model.predict_proba(x)[:, 1] if h['head'] == 'participation' else model.predict(x)
                col = 'observation_raw_p' if h['head'] == 'participation' else 'observation_raw_conditional_pa'
                assert np.allclose(pred, g[col], atol=1e-10, rtol=0)
                paths.append(path)
                replayed += 1
        for c in old['cells']:
            y, k = c['year'], c['fold']
            f = frames[k]
            tr = f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert tr['ctx_information_date'].max() < te['ctx_information_date'].min()
            for head, sub in [('participation', tr), ('conditional_pa', tr.filter(pl.col('next_pa') > 0))]:
                _, note = preflight(sub, te, cutoff=y, fold=k, features=names,
                                    expected_keys=te.select('row_id', 'horizon').iter_rows())
                s = support(sub, te).with_columns(pl.lit(y).alias('origin'), pl.lit(k).alias('fold'), pl.lit(head).alias('head'))
                profiles.append(s)
                checks.append(dict(year=y, fold=k, head=head, **note,
                    continuity_zero=int((s['continuity_people'] == 0).sum()),
                    continuity_under20=int((s['continuity_people'] < 20).sum()),
                    input_min=float(sub[NEW].min()), input_max=float(sub[NEW].max()),
                    test_outside=int(((te[NEW] < sub[NEW].min()) | (te[NEW] > sub[NEW].max())).sum())))
    assert replayed == len(checks) == 70
    OUT.mkdir()
    for k, f in frames.items():
        path = OUT / f'features-{k}.parquet'
        f.write_parquet(path)
        paths.append(path)
    path = OUT / 'support.parquet'
    pl.concat(profiles).write_parquet(path)
    paths.append(path)
    save('preflight.json', dict(before_fitting=True, settings=old['settings'], features=names,
        baseline_features=old['job_features'], cells=old['cells'], checks=checks, baseline_heads_replayed=replayed,
        fixed_cases=cases, source_rows=63314, evaluated_rows=30519, original_rows=30506,
        source_facts_changed=False, protected_2026_outcomes_used=False, deployment_approved=False,
        hashes={str(p): sha256_file(p) for p in paths}))
    print('Seventy benchmark replays and full/active gates complete. No new fits yet.', flush=True)


def fit():
    pre = read(OUT / 'preflight.json')
    verify(pre['hashes'])
    assert pre['before_fitting'] and pre['baseline_heads_replayed'] == 70
    assert not (OUT / 'fit-report.json').exists()
    seal = dict(runner_sha256=sha256_file(Path(__file__)), preflight_sha256=sha256_file(OUT / 'preflight.json'))
    if (OUT / 'fit-seal.json').exists():
        assert read(OUT / 'fit-seal.json') == seal
    else:
        save('fit-seal.json', seal)
    baseline = pl.read_parquet(BASE / 'predictions.parquet').sort('row_id')
    parts, receipts = [], []
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y, k = c['year'], c['fold']
            note_path = OUT / f'fit-{y}-{k}.json'
            if note_path.exists():
                note = read(note_path)
                verify(note['hashes'])
                receipts.append(note)
                parts.append(pl.read_parquet(OUT / f'forecast-{y}-{k}.parquet'))
                continue
            f = pl.read_parquet(OUT / f'features-{k}.parquet')
            tr = f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            g = baseline.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert g['row_id'].equals(te['row_id'])
            heads, predictions, hashes = [], {}, {}
            for head, sub, cls, target in [('participation', tr, HistGradientBoostingClassifier, 'next_active'),
                ('conditional_pa', tr.filter(pl.col('next_pa') > 0), HistGradientBoostingRegressor, 'next_pa')]:
                path = OUT / f'model-{head}-{y}-{k}.joblib'
                assert not path.exists(), 'Incomplete cell requires explicit recovery, never silent overwrite'
                model = cls(**pre['settings'])
                model.fit(sub.select(pre['features']).to_numpy(), sub[target].to_numpy(), sample_weight=weights(sub))
                joblib.dump(model, path, compress=3)
                hashes[str(path)] = sha256_file(path)
                heads.append(dict(head=head, path=str(path), features=pre['features'], training_rows=sub.height,
                    training_people=sub['player_id'].n_unique(), maximum_training_target=int(sub['target_year'].max())))
                x = te.select(pre['features']).to_numpy()
                predictions[head] = model.predict_proba(x)[:, 1] if head == 'participation' else model.predict(x)
            probability = predictions['participation'].copy()
            probability[(te['status_hard_unavailable'].to_numpy() > 0) | (te['status_retired'].to_numpy() > 0)] = 0.
            conditional = np.clip(predictions['conditional_pa'], 1, 800)
            pa = probability * conditional
            rate = g['observation_rate'].to_numpy()
            g = g.with_columns(pl.Series('recency_raw_p', predictions['participation']),
                pl.Series('recency_raw_conditional_pa', predictions['conditional_pa']),
                pl.Series('recency_p', probability), pl.Series('recency_conditional_pa', conditional),
                pl.Series('recency_pa', pa), pl.Series('recency_rate', rate),
                pl.Series('recency_value', pa * (rate / 600 + g['origin_replacement_rate'].to_numpy())))
            assert np.isfinite(g.select([n for n in g.columns if n.startswith('recency_')]).to_numpy()).all()
            assert g.select(baseline.columns).equals(baseline.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id'))
            path = OUT / f'forecast-{y}-{k}.parquet'
            g.write_parquet(path)
            hashes[str(path)] = sha256_file(path)
            note = dict(origin=y, fold=k, heads=heads, hashes=hashes)
            save(note_path.name, note)
            receipts.append(note)
            parts.append(g)
            print(f'Completed {y}/{k}: two opportunity heads; hitting unchanged.', flush=True)
    q = pl.concat(parts).sort('row_id')
    assert q.height == 30519 and q.select(baseline.columns).equals(baseline)
    q.write_parquet(OUT / 'predictions.parquet')
    save('fit-report.json', dict(new_heads=70, cells=receipts, rows=q.height,
        predictions_sha256=sha256_file(OUT / 'predictions.parquet'), player_walkthrough_status='pending',
        protected_2026_outcomes_used=False, deployment_approved=False))
    verify(pre['hashes'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['prepare', 'fit'])
    {'prepare': prepare, 'fit': fit}[parser.parse_args().phase]()
