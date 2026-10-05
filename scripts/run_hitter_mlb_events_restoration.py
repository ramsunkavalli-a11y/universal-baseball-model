"""One prospectively fixed seven-input restoration after completed source audit."""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_mlb_events import DETAIL
from universal_baseball.hitter_past_direct_value import fit
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights
from run_hitter_count_baseline import ROOT, GEN, OUT as COUNT, read, verify, matrix
from run_hitter_mlb_detail_restoration import profiles as quality_profiles
from run_hitter_past_direct_value import past_rate

OUT = GEN / 'hitter-mlb-events-restoration'
PREVIOUS = GEN / 'hitter-mlb-detail-restoration'
AUDIT = GEN / 'hitter-mlb-events-source-audit'


def save(name, obj):
    path = OUT / name
    assert not path.exists(), f'Preserve {path}'
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8', newline='\n')


def profiles(f):
    absent = pl.col('pooled_MLB_pa') == 0
    return quality_profiles(f).with_columns(
        pl.when(absent).then(pl.lit('no_MLB')).when(pl.col('pooled_MLB_K') < .15).then(pl.lit('low'))
        .when(pl.col('pooled_MLB_K') > .30).then(pl.lit('high')).otherwise(pl.lit('middle')).alias('MLB_K_group'),
        pl.when(absent).then(pl.lit('no_MLB')).when(pl.col('pooled_MLB_HR') < .02).then(pl.lit('low'))
        .when(pl.col('pooled_MLB_HR') > .05).then(pl.lit('high')).otherwise(pl.lit('middle')).alias('MLB_HR_group'))


def prepare():
    assert not OUT.exists()
    final = read(PREVIOUS / 'final-review.json'); verify(final['hashes'])
    assert final['player_walkthrough_status'] == 'complete'
    verify({final['public_report']: final['public_report_sha256']})
    audit = read(AUDIT / 'final-review.json'); verify(audit['hashes']); verify(audit['completion_hashes'])
    assert audit['source_walkthrough_status'] == 'complete' and audit['fitted_models'] == 0
    verify({audit['public_report']: audit['public_report_sha256']})
    previous = read(PREVIOUS / 'preflight.json'); verify(previous['source_hashes'])
    for c in read(PREVIOUS / 'fit-report.json')['cells']:
        verify(c['hashes'])
    arms = {arm: names + DETAIL for arm, names in previous['arms'].items()}
    assert {k: len(v) for k, v in arms.items()} == dict(base=123, prospect=132, tracking=186)
    assert all(len(v) == len(set(v)) for v in arms.values())
    fixed = sorted(r['row_id'] for r in read(PREVIOUS / 'player-walks.json')['cases'])
    assert len(fixed) == 17
    paths = [Path(__file__), ROOT / 'docs/hitter-mlb-events-restoration-contract.md',
             ROOT / 'src/universal_baseball/hitter_mlb_events.py', ROOT / 'tests/test_hitter_mlb_events.py',
             PREVIOUS / 'final-review.json', PREVIOUS / 'preflight.json', PREVIOUS / 'predictions.parquet',
             PREVIOUS / 'player-walks.json', AUDIT / 'final-review.json', AUDIT / 'source-walks.json',
             ROOT / 'src/universal_baseball/hitter_past_direct_value.py', ROOT / 'scripts/run_hitter_past_direct_value.py',
             ROOT / 'scripts/run_hitter_count_baseline.py', ROOT / 'scripts/run_hitter_mlb_detail_restoration.py',
             ROOT / 'scripts/prepare_practical_hitter_v33.py', ROOT / 'scripts/fit_practical_hitter_v31.py',
             ROOT / 'src/universal_baseball/forecast_validation.py']
    checks, support, ranges = [], [], []
    keys = ['prior_debut', 'stage', 'age_group', 'mlb_exposure', 'MLB_quality_group',
            'has_NPB', 'has_KBO', 'scout_high', 'MLB_K_group', 'MLB_HR_group']
    for k in range(5):
        path = COUNT / f'features-{k}.parquet'; f = pl.read_parquet(path); paths.append(path)
        for c in [c for c in previous['cells'] if c['fold'] == k]:
            full = f.filter(pl.col('row_id').is_in(c['training_row_ids']))
            tr = full.filter(pl.col('next_pa') > 0).sort('row_id')
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert tr['target_year'].max() <= c['year'] and 2020 not in tr['target_year']
            for arm, names in arms.items():
                _, note = preflight(tr, te, cutoff=c['year'], fold=k, features=names,
                                    expected_keys=te.select('row_id', 'horizon').iter_rows())
                assert np.isfinite(matrix(tr, names)).all() and np.isfinite(matrix(te, names)).all()
                checks.append(dict(origin=c['year'], fold=k, arm=arm, note=note))
                for name in DETAIL:
                    lo, hi = float(tr[name].min()), float(tr[name].max())
                    bad = (te[name] < lo) | (te[name] > hi)
                    if bad.any():
                        ranges.append(dict(origin=c['year'], fold=k, arm=arm, feature=name,
                                           minimum=lo, maximum=hi, row_ids=te.filter(pl.Series(bad))['row_id'].to_list()))
            for subset, g in [('full', full), ('active', tr)]:
                cnt = profiles(g).group_by(keys).agg(pl.col('player_id').n_unique().alias('people'))
                support.append(profiles(te).select('row_id', *keys).join(cnt, on=keys, how='left', validate='m:1')
                               .with_columns(pl.col('people').fill_null(0), pl.lit(subset).alias('subset'),
                                             pl.lit(c['year']).alias('origin'), pl.lit(k).alias('fold')))
        print(f'Extended MLB-component preflight and support complete, fold {k}.', flush=True)
    assert len(checks) == 105
    OUT.mkdir(parents=True)
    pl.concat(support).write_parquet(OUT / 'profile-support.parquet')
    save('feature-ranges.json', ranges)
    paths += [OUT / 'profile-support.parquet', OUT / 'feature-ranges.json']
    save('preflight.json', dict(before_fitting=True, checks_before_fits=105, checks=checks,
                               arms=arms, cells=previous['cells'], fixed_case_row_ids=fixed,
                               alpha=100, source_hashes={str(p): sha256_file(p) for p in paths},
                               source_walkthrough_status='complete_in_prior_audit',
                               protected_outcomes_used=False, deployment_approved=False))


def certify():
    pre = read(OUT / 'preflight.json'); verify(pre['source_hashes'])
    doc = ROOT / 'docs/hitter-mlb-events-restoration-source-review.md'
    assert doc.exists() and pre['checks_before_fits'] == 105
    save('source-review.json', dict(approved_for_fixed_fit=True, source_walkthrough_status='complete',
                                   hashes={str(p): sha256_file(p) for p in [Path(__file__), doc, OUT / 'preflight.json']},
                                   protected_outcomes_used=False, deployment_approved=False))


def run_fit():
    pre = read(OUT / 'preflight.json'); verify(pre['source_hashes'])
    cert = read(OUT / 'source-review.json'); verify(cert['hashes'])
    assert cert['approved_for_fixed_fit'] and not (OUT / 'fit-report.json').exists()
    seal = dict(runner_sha256=sha256_file(Path(__file__)), preflight_sha256=sha256_file(OUT / 'preflight.json'),
                source_review_sha256=sha256_file(OUT / 'source-review.json'))
    if (OUT / 'fit-seal.json').exists():
        assert read(OUT / 'fit-seal.json') == seal
    else:
        save('fit-seal.json', seal)
    previous = pl.read_parquet(PREVIOUS / 'predictions.parquet').sort('row_id')
    forecasts, receipts = [], []
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y, k = c['year'], c['fold']; path = OUT / f'forecast-{y}-{k}.parquet'
            if path.exists():
                note = read(OUT / f'fit-{y}-{k}.json'); verify(note['hashes'])
                receipts.append(note); forecasts.append(pl.read_parquet(path)); continue
            f = pl.read_parquet(COUNT / f'features-{k}.parquet')
            tr = f.filter(pl.col('row_id').is_in(c['training_row_ids']) & (pl.col('next_pa') > 0)).sort('row_id')
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            q = previous.filter(pl.col('row_id').is_in(te['row_id'].to_list())).sort('row_id')
            assert q['row_id'].equals(te['row_id'])
            train_base, test_base = past_rate(tr, True), past_rate(te)
            assert np.allclose(test_base, q['scalar_baseline_rate'], atol=1e-10)
            candidate, heads, hashes = {}, [], {}
            for arm, names in pre['arms'].items():
                m = fit(matrix(tr, names), tr['actual_relative_rate'].to_numpy(), train_base,
                        weights(tr) * tr['next_pa'].to_numpy())
                p = OUT / f'{arm}-rate-{y}-{k}.joblib'; assert not p.exists()
                joblib.dump(m, p, compress=3); hashes[str(p)] = sha256_file(p)
                candidate[arm] = test_base + m.predict(matrix(te, names))
                heads.append(dict(arm=arm, path=str(p), features=names, training_rows=tr.height,
                                  training_people=tr['player_id'].n_unique(), maximum_target_year=int(tr['target_year'].max()), alpha=100))
            rate = np.where(te['prior_debut'].to_numpy() == 0, candidate['prospect'],
                            np.where(te['sc_tracked'].to_numpy(), candidate['tracking'], candidate['base']))
            pa = q['restored_pa'].to_numpy()
            q = q.with_columns(pl.Series('components_rate', rate), pl.Series('components_pa', pa),
                               pl.Series('components_value', pa * (rate / 600 + q['origin_replacement_rate'].to_numpy())))
            assert np.isfinite(q.select('components_rate', 'components_value').to_numpy()).all()
            q.write_parquet(path); hashes[str(path)] = sha256_file(path)
            note = dict(origin=y, fold=k, heads=heads, hashes=hashes)
            save(f'fit-{y}-{k}.json', note); receipts.append(note); forecasts.append(q)
            print(f'Fitted fixed MLB-component restoration {y}/{k}.', flush=True)
    q = pl.concat(forecasts).sort('row_id')
    assert q.height == 30519 and q.select(previous.columns).equals(previous)
    assert q['components_pa'].equals(q['restored_pa'])
    q.write_parquet(OUT / 'predictions.parquet')
    save('fit-report.json', dict(new_heads=105, cells=receipts, rows=q.height,
                                predictions_sha256=sha256_file(OUT / 'predictions.parquet'),
                                player_walkthrough_status='pending', protected_outcomes_used=False, deployment_approved=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('phase', choices=['prepare', 'certify', 'fit'])
    args = p.parse_args(); {'prepare': prepare, 'certify': certify, 'fit': run_fit}[args.phase]()
