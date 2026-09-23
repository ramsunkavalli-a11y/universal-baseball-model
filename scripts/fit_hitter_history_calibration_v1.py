"""Fixed history/calibration ablation; generate past-only calibration forecasts."""
import argparse
import hashlib
import json
from pathlib import Path
import warnings
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from fit_hitter_arrival_coherence_v1 import save
from fit_hitter_detail_arrival_v1 import OUT as SOURCE, REFERENCES
from universal_baseball.hitter_detail_arrival import TARGETS, eligible, target_values, fit_probability
from universal_baseball.hitter_history_calibration import add_history, calibrate
from universal_baseball.storage import sha256_file

OUT = Path('reports/generated/hitter-history-calibration-v1')
PACKAGE = Path('model_artifacts/hitter-history-calibration-v1-2026-09-23')
MAIN = {'next_year': (2017, 2018, 2021, 2022, 2023, 2024),
        'arrival_three': (2021, 2022), 'regular_three': (2021, 2022)}
RAW = {'next_year': (2013, 2014, 2015, 2016, 2017, 2018, 2021, 2022, 2023, 2024),
       'arrival_three': (2013, 2014, 2015, 2016, 2019, 2021, 2022),
       'regular_three': (2013, 2014, 2015, 2016, 2019, 2021, 2022)}
CODE = [Path('docs/hitter-history-calibration-v1-plan.md'), Path(__file__),
        Path('src/universal_baseball/hitter_history_calibration.py'),
        Path('src/universal_baseball/hitter_detail_arrival.py'),
        Path('src/universal_baseball/hitter_model_tournament.py'),
        Path('tests/test_hitter_history_calibration.py')]


def hashes():
    return {str(p): sha256_file(p) for p in [*CODE, SOURCE/'input-panel.parquet',
            SOURCE/'prefit-manifest.json', SOURCE/'predictions.parquet',
            SOURCE/'reference-predictions.parquet']}


def assemble():
    source = pl.read_parquet(SOURCE/'input-panel.parquet')
    p, names = add_history(source)
    old = json.loads((SOURCE/'prefit-manifest.json').read_text())['arms']['R']
    return p, {'R': old, 'H': old+names}


def verify_prefit(pre):
    expected = dict(pre['hashes'])
    repair = OUT/'runtime-repair.json'
    if repair.exists():
        amendment = json.loads(repair.read_text())
        assert amendment['original_prefit_sha256'] == sha256_file(OUT/'prefit-manifest.json')
        for path, change in amendment['changes'].items():
            assert expected[path] == change['before']
            expected[path] = change['after']
    assert expected == hashes()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--freeze', action='store_true'); args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True); (OUT/'fits').mkdir(exist_ok=True)
    panel, arms = assemble()
    if args.freeze:
        if (OUT/'prefit-manifest.json').exists(): raise ValueError('Already frozen')
        save(OUT/'prefit-manifest.json', {'hashes': hashes(), 'arms': arms, 'raw_folds': RAW,
                                       'main_folds': MAIN, 'protected_outcomes_used': False})
        print(json.dumps({'frozen': True, 'features': {k: len(v) for k, v in arms.items()}})); return
    pre = json.loads((OUT/'prefit-manifest.json').read_text()); verify_prefit(pre)
    assert pre['arms'] == arms
    old = pl.read_parquet(SOURCE/'predictions.parquet').filter(~pl.col('cold') & (pl.col('arm') == 'R') & (pl.col('engine') == 'lightgbm'))
    frames = []; notes = []
    for target, years in RAW.items():
        for year in years:
            test = panel.filter(pl.col('origin_year') == year)
            train = eligible(panel, year, target)
            for arm in arms:
                path = OUT/'fits'/f'{target}-{year}-{arm}.parquet'
                if path.exists() and path.with_suffix('.json').exists():
                    frame = pl.read_parquet(path); note = json.loads(path.with_suffix('.json').read_text())
                    assert sha256_file(path) == note['sha256']
                else:
                    inherited = old.filter((pl.col('target') == target) & (pl.col('origin_year') == year))
                    print(f'{target} {year} {arm}', flush=True)
                    if arm == 'R' and inherited.height:
                        frame = inherited; note = {'inherited': True, 'training_rows': train.height,
                                                   'latest_label': int(train['origin_year'].max())+TARGETS[target]}
                    else:
                        p, note = fit_probability(train, test, arms[arm], target)
                        frame = test.select('origin_year', 'player_id', 'age', 'stage', 'prospect',
                                            'recent_debut', 'prior_debut', 'mlb_pa_lag0').with_columns(
                            pl.Series('actual', target_values(test, target)), pl.Series('probability', p),
                            pl.lit(target).alias('target'), pl.lit(arm).alias('arm'),
                            pl.lit('lightgbm').alias('engine'), pl.lit(False).alias('cold'),
                            pl.lit(year < 2020 <= year+TARGETS[target]).alias('pandemic'))
                    frame.write_parquet(path)
                    note.update(year=year, target=target, arm=arm, sha256=sha256_file(path))
                    save(path.with_suffix('.json'), note)
                frames.append(frame); notes.append(note)
    raw = pl.concat(frames, how='vertical_relaxed')
    raw.write_parquet(OUT/'raw-predictions.parquet')
    output = []; calibrators = []
    for target, years in MAIN.items():
        for year in (*years, *((2019,) if TARGETS[target] == 3 else ())):
            for arm in arms:
                history = raw.filter((pl.col('arm') == arm) & (pl.col('target') == target))
                current = history.filter(pl.col('origin_year') == year)
                p, note = calibrate(history, current, year, target)
                output += [current, current.with_columns(pl.Series('probability', p), pl.lit(arm+'C').alias('arm'))]
                calibrators.append({'year': year, 'target': target, 'arm': arm, **note})
    predictions = pl.concat(output); predictions.write_parquet(OUT/'predictions.parquet')
    # End-to-end mutation: future labels and future predictor snapshots cannot affect 2022 H/HC.
    changed = pl.read_parquet(SOURCE/'input-panel.parquet')
    for h in (1, 2, 3):
        changed = changed.with_columns(pl.when(pl.col('origin_year')+h > 2022).then(9999.)
                                      .otherwise(pl.col(f'pa_h{h}')).alias(f'pa_h{h}'))
    changed = changed.with_columns(*[
        pl.when(pl.col('origin_year') > 2022).then(987.).otherwise(pl.col(c).cast(pl.Float64)).alias(c)
        for c in set(arms['R']+['pa_lag0'])])
    changed, _ = add_history(changed)
    print('Future-mutation refit', flush=True)
    test = changed.filter(pl.col('origin_year') == 2022)
    mp, _ = fit_probability(eligible(changed, 2022, 'regular_three'), test, arms['H'], 'regular_three')
    orig = raw.filter((pl.col('origin_year') == 2022) & (pl.col('arm') == 'H') & (pl.col('target') == 'regular_three'))
    np.testing.assert_array_equal(mp, orig['probability'])
    history = raw.filter((pl.col('arm') == 'H') & (pl.col('target') == 'regular_three')).with_columns(
        pl.when(pl.col('origin_year')+3 > 2022).then(1-pl.col('actual')).otherwise(pl.col('actual')).alias('actual'))
    cp, _ = calibrate(history, orig.with_columns(pl.Series('probability', mp)), 2022, 'regular_three')
    expected = predictions.filter((pl.col('origin_year') == 2022) & (pl.col('arm') == 'HC') & (pl.col('target') == 'regular_three'))
    np.testing.assert_array_equal(cp, expected['probability'])
    verify_prefit(pre)
    if (OUT/'runtime-repair.json').exists():
        repair = json.loads((OUT/'runtime-repair.json').read_text())
        module = Path('src/universal_baseball/hitter_history_calibration.py')
        original = module.read_bytes().replace(
            b"'fallback': bool(len(years) < 3 or y.sum() < 20 or (1-y).sum() < 20)",
            b"'fallback': len(years) < 3 or y.sum() < 20 or (1-y).sum() < 20")
        assert hashlib.sha256(original).hexdigest() == repair['changes'][str(module)]['before']
        namespace = {}; exec(compile(original, str(module), 'exec'), namespace)
        for n in calibrators:
            history = raw.filter((pl.col('arm') == n['arm']) & (pl.col('target') == n['target']))
            current = history.filter(pl.col('origin_year') == n['year'])
            frozen_p, _ = namespace['calibrate'](history, current, n['year'], n['target'])
            saved = predictions.filter((pl.col('arm') == n['arm']+'C') &
                    (pl.col('target') == n['target']) & (pl.col('origin_year') == n['year']))
            np.testing.assert_allclose(frozen_p, saved['probability'], rtol=0, atol=1e-12)
    save(OUT/'fit-manifest.json', {'fits': notes, 'calibrators': calibrators,
         'future_mutation_maximum_difference': float(np.max(abs(cp-expected['probability'].to_numpy()))),
         'prefit_sha256': sha256_file(OUT/'prefit-manifest.json'),
         'files': {n: sha256_file(OUT/n) for n in ('raw-predictions.parquet', 'predictions.parquet')},
         'production_forecasts_changed': False, 'protected_outcomes_used': False})
    print(json.dumps({'raw_folds': len(notes), 'new_fits': sum(not n.get('inherited', False) for n in notes),
                      'rows': predictions.height, 'mutation_passed': True}))


if __name__ == '__main__':
    warnings.filterwarnings('ignore', message='X does not have valid feature names')
    with threadpool_limits(limits=4): main()
