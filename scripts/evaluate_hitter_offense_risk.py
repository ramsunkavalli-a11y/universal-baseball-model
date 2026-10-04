"""Prefit provenance, genuinely nested rate heads, and fixed-mean offense risks."""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits

from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_compatible_value import labels, UNIT
from universal_baseball.hitter_offense_risk import fit_rate_variances, offense_distribution
from universal_baseball.hitter_talent_bridge import event_counts
from universal_baseball.hitter_workload_risk import mixture_pmf
from universal_baseball.mlb_event_logit import EVENTS, VALUES
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights
from prepare_practical_hitter_v33 import safe_matrix
import evaluate_hitter_preseason_readiness_v68 as current
import prepare_hitter_workload_risk as workload

ROOT = current.ROOT
OUT = ROOT/'reports/generated/hitter-offense-risk'
WORK = Path('D:/UBM-Source-Cache/hitter-offense-risk')
RATE = ROOT/'reports/generated/practical-hitter-numeric-repair-v53'
VALUE = ROOT/'reports/generated/hitter-compatible-value-v63'


def read(p):
    return json.loads(Path(p).read_text(encoding='utf8'))


def write(p, obj):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, allow_nan=False, ensure_ascii=False)+'\n', encoding='utf8')


def check_hashes(obj):
    for p, h in obj.items():
        assert sha256_file(Path(p)) == h, p


def context():
    f = pl.read_parquet(current.OUT/'features.parquet').sort('row_id')
    v = pl.read_parquet(VALUE/'features.parquet').sort('row_id')
    assert f['row_id'].equals(v['row_id'])
    for s in ['common_rate_label', 'relative_rate_label', 'common_value_label', 'origin_index']:
        if s not in f.columns:
            f = f.with_columns(v[s])
    # This corrected replacement is a label/value reference, never a rate input.
    f = f.with_columns(v['origin_replacement_rate'])
    return f


def calibration_profiles(f, calibration, test):
    keys = ['prior_debut', 'stage', 'age_band', 'rank_band', 'new_draftee', 'thin_pro', 'source_position']
    groups = current.tagged(calibration).group_by(keys).agg(pl.col('player_id').n_unique().alias('calibration_people'))
    return current.tagged(test).select('row_id', *keys).join(groups, on=keys, how='left', validate='m:1').with_columns(
        pl.col('calibration_people').fill_null(0))


def prepare():
    assert not (OUT/'preflight.json').exists(), 'Preserve this fixed experiment'
    parent = read(workload.OUT/'final-report.json')
    assert parent['player_walkthrough_status'] == 'complete'
    check_hashes(parent['source_and_execution_hashes']); check_hashes(parent['review_hashes'])
    wp = read(workload.OUT/'preflight.json')
    rp = read(RATE/'preflight.json')
    f = context(); q = pl.read_parquet(current.OUT/'scored-predictions.parquet').sort('row_id')
    r = pl.read_parquet(RATE/'features.parquet').sort('row_id')
    assert len(f) == 63282 and len(q) == 30506
    assert f.select(rp['rate_features']).equals(r.select(rp['rate_features']))
    assert not set(rp['rate_features']) & {'common_rate_label', 'origin_index', 'origin_replacement_rate'}
    actual = f.select(['count_'+e for e in EVENTS]).to_numpy() if 'count_other' in f.columns else None
    v = pl.read_parquet(VALUE/'features.parquet').sort('row_id')
    actual = v.select(['count_'+e for e in EVENTS]).to_numpy()
    hist = pl.scan_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet').filter(
        (pl.col('season') <= 2025) & (pl.col('bucket') == 'MLB')).collect().sort('player_id', 'season')
    raw = hist.select('player_id', pl.col('season').alias('target_year')).with_columns(
        [pl.Series('independent_'+e, x) for e, x in zip(EVENTS, event_counts(hist).T)])
    control = f.select('row_id', 'player_id', 'target_year', 'next_pa').join(
        raw, on=['player_id', 'target_year'], how='left', validate='m:1').sort('row_id')
    assert control.filter((pl.col('next_pa') > 0) & pl.col('independent_other').is_null()).is_empty()
    independently = control.select([pl.col('independent_'+e).fill_null(0) for e in EVENTS]).to_numpy()
    assert np.array_equal(actual, independently)
    z = labels(actual, v.select(['origin_env_'+e for e in EVENTS]).to_numpy(),
               v.select(['target_env_'+e for e in EVENTS]).to_numpy(), f['origin_replacement_rate'])
    for a, b in [('common_rate', 'common_rate_label'), ('relative_rate', 'next_batting_rate'), ('common_value', 'common_value_label')]:
        assert np.allclose(z[a], f[b], atol=1e-10, rtol=0), (a, b)
    fq = f.filter(pl.col('row_id').is_in(q['row_id'])).sort('row_id')
    assert np.allclose(fq['common_rate_label'], q['next_batting_rate'], atol=1e-10, rtol=0)
    assert np.allclose(fq['common_value_label'], q['next_value'], atol=1e-10, rtol=0)
    assert np.allclose(q['preseason_value'], q['preseason_pa']*(q['preseason_rate']/600+q['origin_replacement_rate']), atol=1e-10)
    nested_checks = []; outer_checks = []; prof = []; cells = []
    original = {(c['year'], c['fold']): c for c in read(current.OUT/'preflight.json')['cells']}
    for c in wp['cells']:
        y, k = c['year'], c['fold']; old = original[y, k]
        te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
        train = f.filter(pl.col('row_id').is_in(old['training_row_ids'])).filter(pl.col('next_pa') > 0).sort('row_id')
        sup, note = preflight(train, te, cutoff=y, fold=k, features=rp['rate_features'], expected_keys=te.select('row_id', 'horizon').iter_rows())
        outer_checks.append(sup.with_columns(pl.lit(y).alias('outer_year'), pl.lit(k).alias('outer_fold')))
        for n in c['nested']:
            tr = f.filter(pl.col('row_id').is_in(n['training_row_ids'])).sort('row_id')
            val = f.filter(pl.col('row_id').is_in(n['validation_row_ids'])).sort('row_id')
            s, nn = preflight(tr, val, cutoff=n['origin'], fold=n['inner_fold'], features=rp['rate_features'], expected_keys=val.select('row_id', 'horizon').iter_rows())
            assert not set(te['player_id']) & (set(tr['player_id']) | set(val['player_id']))
            nested_checks.append(dict(outer_year=y, outer_fold=k, inner_origin=n['origin'], **nn))
        cal = f.filter(pl.col('row_id').is_in(c['calibration_row_ids'])).sort('row_id')
        assert cal['next_pa'].min() > 0 and cal['target_year'].max() <= y
        assert not set(cal['player_id']) & set(te['player_id'])
        assert cal.height >= 50 and cal['player_id'].n_unique() >= 30, 'No estimated fallback in this contract'
        prof.append(calibration_profiles(f, cal, te).with_columns(pl.lit(y).alias('outer_year'), pl.lit(k).alias('outer_fold')))
        cells.append(dict(**c, rate_outer_preflight=note))
    OUT.mkdir(parents=True, exist_ok=True); WORK.mkdir(parents=True, exist_ok=True)
    pl.concat(outer_checks).write_parquet(OUT/'outer-support.parquet')
    pl.concat(prof).write_parquet(OUT/'calibration-profile-support.parquet')
    write(OUT/'nested-checks.json', nested_checks)
    paths = [Path(__file__), ROOT/'src/universal_baseball/hitter_offense_risk.py', ROOT/'tests/test_hitter_offense_risk.py',
             ROOT/'docs/hitter-offense-risk-contract.md', current.OUT/'features.parquet', current.OUT/'scored-predictions.parquet',
             VALUE/'features.parquet', RATE/'preflight.json', RATE/'features.parquet', ROOT/'reports/generated/practical-hitter-v31/counts.parquet',
             workload.OUT/'preflight.json', workload.OUT/'fit-report.json', workload.OUT/'final-report.json',
             OUT/'outer-support.parquet', OUT/'calibration-profile-support.parquet', OUT/'nested-checks.json',
             ROOT/'scripts/prepare_practical_hitter_v33.py', ROOT/'scripts/fit_practical_hitter_v31.py']
    write(OUT/'preflight.json', dict(before_fitting=True, new_fits=0, cells=cells, rate_features=rp['rate_features'],
        ridge_alpha=100, fixed_forecasts=30506, actual_rate_checks=130, nested_checks=95,
        unique_nested_heads=50, independent_event_labels_exact=True, corrected_common_origin_units=True,
        rate_features_identical=True, input_hashes={str(p): sha256_file(p) for p in paths},
        protected_outcomes_used=False, player_walkthrough_status='pending'))
    print('All 130 rate checks and independent event-label controls saved before fitting.', flush=True)


def fit():
    pre = read(OUT/'preflight.json'); check_hashes(pre['input_hashes'])
    f = context(); q = pl.read_parquet(current.OUT/'scored-predictions.parquet').sort('row_id')
    workload_fits = {(x['year'], x['fold']): x for x in read(workload.OUT/'fit-report.json')['cells']}
    notes = []; replayed = set(); outer_replays = 0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y, k = c['year'], c['fold']; output = WORK/f'forecast-{y}-{k}.parquet'
            if output.exists():
                note = read(WORK/f'fit-{y}-{k}.json'); check_hashes(note['output_hashes'])
                notes.append(note); continue
            calibration = []; heads = []
            for n in c['nested']:
                tag = f'inner-rate-{k}-{n["origin"]}'; modelp = WORK/(tag+'.joblib')
                predp = WORK/(tag+'.parquet'); receipt = WORK/(tag+'.json')
                tr = f.filter(pl.col('row_id').is_in(n['training_row_ids'])).sort('row_id')
                val = f.filter(pl.col('row_id').is_in(n['validation_row_ids'])).sort('row_id')
                if receipt.exists():
                    h = read(receipt); check_hashes(h['output_hashes'])
                    assert h['training_row_ids'] == n['training_row_ids'] and h['validation_row_ids'] == n['validation_row_ids']
                else:
                    model = Ridge(alpha=100); w = weights(tr)*tr['next_pa'].to_numpy(); w *= len(w)/w.sum()
                    model.fit(safe_matrix(tr, pre['rate_features']), tr['next_batting_rate'].to_numpy(), sample_weight=w)
                    pred = model.predict(safe_matrix(val, pre['rate_features']))
                    assert np.isfinite(pred).all(); joblib.dump(model, modelp, compress=3)
                    val.select('row_id', 'player_id', 'origin_year', 'target_year', 'outer_fold', 'next_pa', 'common_rate_label').with_columns(
                        pl.Series('nested_rate', pred)).write_parquet(predp)
                    h = dict(outer_fold=k, inner_origin=n['origin'], training_row_ids=n['training_row_ids'],
                             validation_row_ids=n['validation_row_ids'], model_path=str(modelp), prediction_path=str(predp),
                             output_hashes={str(p): sha256_file(p) for p in [modelp, predp]})
                    write(receipt, h)
                    print(f'Nested Ridge {k}/{n["origin"]}: {len(tr)} training, {len(val)} predictions', flush=True)
                saved = pl.read_parquet(predp).sort('row_id')
                if str(modelp) not in replayed:
                    model = joblib.load(modelp)
                    assert np.allclose(model.predict(safe_matrix(val, pre['rate_features'])), saved['nested_rate'], atol=1e-10, rtol=0)
                    replayed.add(str(modelp))
                calibration.append(saved.filter(pl.col('next_pa') > 0)); heads.append(h)
            cal = pl.concat(calibration).sort('row_id')
            assert set(cal['row_id']) == set(c['calibration_row_ids'])
            pars = fit_rate_variances((cal['common_rate_label']-cal['nested_rate']).to_numpy(), cal['next_pa'].to_numpy(), weights(cal))
            cp = WORK/f'calibration-{y}-{k}.parquet'; cal.write_parquet(cp)
            te = q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            ft = f.filter(pl.col('row_id').is_in(te['row_id'])).sort('row_id')
            rh = next(h for h in read(RATE/f'fit-{y}-{k}.json')['heads'] if h['head'] == 'rate')
            assert sha256_file(Path(rh['path'])) == rh['sha256']
            assert np.allclose(joblib.load(rh['path']).predict(safe_matrix(ft, pre['rate_features'])), te['preseason_rate'], atol=1e-10, rtol=0)
            outer_replays += 1
            kap = workload_fits[y, k]['concentration']['concentration']
            result = te.select('row_id', 'player_id', 'player_name', 'origin_year', 'target_year', 'outer_fold', 'next_pa', 'next_value',
                               'preseason_p', 'preseason_conditional_pa', 'preseason_pa', 'preseason_rate', 'preseason_value')
            values = {name: [] for name in ['fixed', 'constant', 'sample']}
            for start in range(0, len(te), 96):
                g = te.slice(start, 96)
                pmf = mixture_pmf(g['preseason_p'], g['preseason_conditional_pa'], kap)
                for arm, a, b in [('fixed', None, 0), ('constant', pars['constant_variance'], 0),
                                  ('sample', pars['sample_dependent']['a'], pars['sample_dependent']['b'])]:
                    terms = offense_distribution(pmf, g['preseason_rate'], g['origin_replacement_rate'], g['next_value'],
                        a=a, b=b, origin_index=g['origin_index'], unit=UNIT, event_min=float(VALUES.min()), event_max=float(VALUES.max()))
                    assert np.allclose(terms['expected_value'], g['preseason_value'], atol=1e-10, rtol=0)
                    values[arm].append(pl.DataFrame({arm+'_'+name: val for name, val in terms.items()}))
            for arm in values:
                result = result.hstack(pl.concat(values[arm]))
            result.write_parquet(output)
            note = dict(year=y, fold=k, variance_parameters=pars, calibration_rows=len(cal),
                        calibration_people=cal['player_id'].n_unique(), calibration_path=str(cp),
                        nested_heads=heads, workload_concentration=kap, outer_rate_model=rh,
                        output_hashes={str(p): sha256_file(p) for p in [output, cp]}, player_walkthrough_status='pending')
            write(WORK/f'fit-{y}-{k}.json', note); notes.append(note)
            print(f'Offense {y}/{k}: a={pars["sample_dependent"]["a"]:.4f}, b={pars["sample_dependent"]["b"]:.4f}', flush=True)
    result = pl.concat([pl.read_parquet(WORK/f'forecast-{c["year"]}-{c["fold"]}.parquet') for c in pre['cells']]).sort('row_id')
    assert len(result) == 30506 and result['row_id'].equals(q['row_id'])
    for arm in ['fixed', 'constant', 'sample']:
        assert np.allclose(result[arm+'_expected_value'], q['preseason_value'], atol=1e-10, rtol=0)
    result.write_parquet(WORK/'predictions.parquet')
    write(OUT/'fit-report.json', dict(cells=notes, forecasts=len(result), original_columns_exact=True,
        new_unique_nested_heads=50, actual_nested_heads_replayed=len(replayed), outer_rate_replays_this_run=outer_replays,
        input_hashes=pre['input_hashes'], output_sha256=sha256_file(WORK/'predictions.parquet'),
        player_walkthrough_status='pending', protected_outcomes_used=False, current_candidate_changed=False))
    print('Fixed offense distributions saved; scoring and player review remain pending.', flush=True)


if __name__ == '__main__':
    {'prepare': prepare, 'fit': fit}[sys.argv[1]]()
