"""Seal corrected source inputs, then run one matched opportunity comparison."""
from pathlib import Path
import json
import sys

import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_dated_context import materialize
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/generated/hitter-dated-context-integration'
OLD = ROOT / 'reports/generated/hitter-preseason-readiness-v68'
POP = ROOT / 'reports/generated/hitter-preseason-population-source'
FOREIGN = ROOT / 'reports/generated/foreign-origin-inputs'
ANCHOR = ROOT / 'reports/generated/hitter-minor-statcast-precision/scored-predictions.parquet'
CONTRACT = ROOT / 'docs/hitter-dated-context-integration-contract.md'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def write(name, obj):
    p = OUT / name
    assert not p.exists(), f'Preserve {p}'
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False, default=str) + '\n', encoding='utf8', newline='\n')


def verify(mapping):
    for path, digest in mapping.items():
        p = Path(path)
        if not p.is_absolute():
            p = ROOT / p
        assert sha256_file(p) == digest, str(p)


def profiles(f):
    return f.with_columns((pl.col('age') // 5).cast(pl.Int64).alias('ctx_age_band'),
        pl.when(pl.col('pa_0') == 0).then(0).when(pl.col('pa_0') < 200).then(1).otherwise(2).alias('ctx_mlb_exposure'))


def prepare():
    assert not OUT.exists(), 'Inspect existing execution instead of restarting'
    review = read(FOREIGN / 'independent-review.json')
    assert review['status'] == 'source_reconstruction_complete'
    verify(review['hashes'])
    source_report = read(POP / 'final-review.json')
    assert source_report['player_walkthrough_status'] == 'complete_for_source'
    for name, digest in source_report['artifact_hashes'].items():
        assert sha256_file(ROOT / 'reports/model-evidence/hitter-preseason-population-source' / name) == digest
    old_pre = read(OLD / 'preflight.json')
    old = pl.read_parquet(OLD / 'features.parquet').sort('row_id')
    anchor = pl.read_parquet(ANCHOR).sort('row_id')
    population = pl.read_parquet(POP / 'population.parquet').to_dicts()
    foreign = read(FOREIGN / 'origin-inputs.json')['rows']
    updated, changes = materialize(old, population, foreign)
    assert old.height == updated.height == 63282 and anchor.height == 30506
    allowed = {'on_40man', 'source_position', 'age', 'age_centered', 'age_squared', 'age_unknown'}
    allowed |= {c for c in old.columns if c.startswith('position_')}
    assert all(set(c['changes']) <= allowed for c in changes)
    assert old.drop(sorted(allowed)).equals(updated.select(old.columns).drop(sorted(allowed)))
    extra = dict(population[0], origin_year=2099, target_year=2100, information_date='2100-01-01')
    assert materialize(old.head(10), population + [extra], foreign)[0].equals(updated.head(10))
    OUT.mkdir(parents=True)
    updated.write_parquet(OUT / 'features.parquet')
    write('source-changes.json', dict(changes=changes, allowed_columns=sorted(allowed),
        labels_and_original_membership_unchanged=True, future_context_mutation_invariant=True))
    cells, supports, profile_rows, ranges = [], [], [], []
    paths = [CONTRACT, Path(__file__), ROOT / 'src/universal_baseball/hitter_dated_context.py',
        ROOT / 'tests/test_hitter_dated_context.py', ROOT / 'src/universal_baseball/forecast_validation.py',
        ROOT / 'scripts/fit_practical_hitter_v31.py', OLD / 'preflight.json', OLD / 'features.parquet',
        POP / 'population.parquet', POP / 'final-review.json', FOREIGN / 'origin-inputs.json',
        FOREIGN / 'independent-review.json', ANCHOR, OUT / 'features.parquet', OUT / 'source-changes.json']
    keys = ['prior_debut', 'stage', 'ctx_age_band', 'ctx_mlb_exposure', 'ctx_foreign_history_known']
    for c in old_pre['cells']:
        y, k = c['year'], c['fold']
        tr = updated.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
        te = updated.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
        checks = {}
        assert max(tr['ctx_information_date']) < min(te['ctx_information_date'])
        for head, sub in [('participation', tr), ('conditional_pa', tr.filter(pl.col('next_pa') > 0))]:
            sup, note = preflight(sub, te, cutoff=y, fold=k, features=old_pre['pa_features'],
                                  expected_keys=te.select('row_id', 'horizon').iter_rows())
            checks[head] = note
            supports.append(sup.with_columns(pl.lit(head).alias('head'), pl.lit(y).alias('ctx_origin'), pl.lit(k).alias('ctx_fold')))
            a, b = profiles(sub), profiles(te)
            counts = a.group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
            profile_rows.append(b.select('row_id', *keys).join(counts, on=keys, how='left', validate='m:1').with_columns(
                pl.col('profile_people').fill_null(0), pl.lit(head).alias('head'), pl.lit(y).alias('ctx_origin'), pl.lit(k).alias('ctx_fold')))
            for name in ['age_centered', 'age_squared', 'age_unknown', 'on_40man', *[n for n in old_pre['pa_features'] if n.startswith('position_')]]:
                lo, hi = float(sub[name].min()), float(sub[name].max())
                ranges.append(dict(origin=y, fold=k, head=head, feature=name, low=lo, high=hi,
                    outside=int(((te[name] < lo) | (te[name] > hi)).sum())))
        old_fit = read(OLD / f'fit-{y}-{k}.json')
        for h in old_fit['heads']:
            assert sha256_file(Path(h['path'])) == h['sha256']
            paths.append(Path(h['path']))
        paths.append(OLD / f'fit-{y}-{k}.json')
        cells.append(dict(year=y, fold=k, training_row_ids=c['training_row_ids'], test_row_ids=c['test_row_ids'],
            information_date=c['information_date'], checks=checks, old_heads=old_fit['heads']))
        print(f'Before fits: {y}/{k} full and active checks recorded.', flush=True)
    assert {rid for c in cells for rid in c['test_row_ids']} == set(anchor['row_id'])
    pl.concat(supports).write_parquet(OUT / 'support.parquet')
    pl.concat(profile_rows).write_parquet(OUT / 'profile-support.parquet')
    write('feature-ranges.json', dict(ranges=ranges))
    paths += [OUT / 'support.parquet', OUT / 'profile-support.parquet', OUT / 'feature-ranges.json']
    changed = pl.DataFrame([dict(row_id=c['row_id']) for c in changes])
    write('preflight.json', dict(before_fitting=True, new_fits=0, cells=cells, features=old_pre['pa_features'], settings=old_pre['settings'],
        source_rows=63282, evaluation_rows=30506, changed_source_rows=len(changes),
        changed_forecast_rows=anchor.join(changed, on='row_id', how='inner').height,
        checks_before_fits=70, hitting_unchanged=True, additions_separately_pending=True,
        player_walkthrough_status='pending', protected_outcomes_used=False, deployment_approved=False,
        input_hashes={str(p): sha256_file(p) for p in set(paths)}))


def fit():
    pre = read(OUT / 'preflight.json'); verify(pre['input_hashes'])
    hashes = {str(p): sha256_file(p) for p in [Path(__file__), OUT / 'preflight.json']}
    if (OUT / 'fit-seal.json').exists():
        assert read(OUT / 'fit-seal.json') == hashes
    else:
        write('fit-seal.json', hashes)
    assert not (OUT / 'fit-report.json').exists(), 'Completed fit is not rerun'
    f = pl.read_parquet(OUT / 'features.parquet')
    old = pl.read_parquet(OLD / 'features.parquet')
    anchor = pl.read_parquet(ANCHOR)
    notes = []
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y, k = c['year'], c['fold']
            pp = OUT / f'forecast-{y}-{k}.parquet'
            if pp.exists():
                n = read(OUT / f'fit-{y}-{k}.json'); verify(n['hashes']); notes.append(n); continue
            tr = f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            before = old.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            q = anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert q['row_id'].equals(te['row_id'])
            heads, raw, hashes = [], {}, {}
            for head, sub in [('participation', tr), ('conditional_pa', tr.filter(pl.col('next_pa') > 0))]:
                h = next(h for h in c['old_heads'] if h['head'] == head)
                model = joblib.load(h['path'])
                bx = before.select(pre['features']).to_numpy()
                bp = model.predict_proba(bx)[:, 1] if head == 'participation' else model.predict(bx)
                column = 'preseason_raw_p' if head == 'participation' else 'preseason_raw_conditional_pa'
                assert np.allclose(bp, q[column], atol=1e-10, rtol=0)
                cls = HistGradientBoostingClassifier if head == 'participation' else HistGradientBoostingRegressor
                m = cls(**pre['settings'])
                target = 'next_active' if head == 'participation' else 'next_pa'
                m.fit(sub.select(pre['features']).to_numpy(), sub[target].to_numpy(), sample_weight=weights(sub))
                x = te.select(pre['features']).to_numpy()
                raw[head] = m.predict_proba(x)[:, 1] if head == 'participation' else m.predict(x)
                assert np.isfinite(raw[head]).all()
                path = OUT / f'{head}-{y}-{k}.joblib'; joblib.dump(m, path, compress=3)
                hashes[str(path)] = sha256_file(path)
                heads.append(dict(head=head, path=str(path), sha256=sha256_file(path),
                    training_rows=len(sub), training_people=sub['player_id'].n_unique(), maximum_target_year=int(sub['target_year'].max())))
            p = raw['participation'].copy()
            p[q['hard_unavailable'].to_numpy() | q['reported_retired'].to_numpy()] = 0
            cond = np.clip(raw['conditional_pa'], 1, 800)
            q = q.with_columns(pl.Series('ctx_raw_p', raw['participation']), pl.Series('ctx_p', p),
                pl.Series('ctx_raw_conditional_pa', raw['conditional_pa']), pl.Series('ctx_conditional_pa', cond),
                pl.Series('ctx_pa', p * cond), pl.col('combined_rate').alias('ctx_rate'))
            q = q.with_columns((pl.col('ctx_pa') * (pl.col('ctx_rate') / 600 + pl.col('origin_replacement_rate'))).alias('ctx_value'))
            q = q.join(te.select('row_id', 'ctx_changed', 'ctx_foreign_history_known'), on='row_id', validate='1:1')
            assert q.select(anchor.columns).equals(anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id'))
            q.write_parquet(pp); hashes[str(pp)] = sha256_file(pp)
            note = dict(year=y, fold=k, information_date=c['information_date'], heads=heads, hashes=hashes)
            write(f'fit-{y}-{k}.json', note); notes.append(note)
            print(f'Context {y}/{k}: two heads saved; original head forecasts replayed.', flush=True)
    result = pl.concat([pl.read_parquet(OUT / f'forecast-{c["year"]}-{c["fold"]}.parquet') for c in pre['cells']]).sort('row_id')
    assert result.height == 30506 and result.select(anchor.columns).equals(anchor.sort('row_id'))
    result.write_parquet(OUT / 'predictions.parquet')
    write('fit-report.json', dict(cells=notes, new_heads=70, old_heads_replayed=70, all_original_columns_exact=True,
        hitting_unchanged=True, output_sha256=sha256_file(OUT / 'predictions.parquet'), player_walkthrough_status='pending', deployment_approved=False))


if __name__ == '__main__':
    {'prepare': prepare, 'fit': fit}[sys.argv[1]]()
