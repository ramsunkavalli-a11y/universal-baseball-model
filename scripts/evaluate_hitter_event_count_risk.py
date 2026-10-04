"""Reuse certified nested means; fit and simulate two fixed event-count laws."""
import json
import sys
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_event_count_risk import tilt, workload_center, fit_count_laws, simulate, mixture_terms
from universal_baseball.hitter_talent_bridge import event_counts
from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.mlb_event_logit import VALUES, EVENTS
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights
from prepare_practical_hitter_v33 import safe_matrix
import evaluate_hitter_offense_risk as old

ROOT = old.ROOT
OUT = ROOT/'reports/generated/hitter-event-count-risk'
WORK = Path('D:/UBM-Source-Cache/hitter-event-count-risk')


def read(p): return json.loads(Path(p).read_text(encoding='utf8'))


def write(p, obj):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf8', newline='\n')


def source():
    f = old.context()
    hist = pl.scan_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet').filter(
        (pl.col('bucket') == 'MLB') & (pl.col('season') <= 2024)).collect().sort('player_id', 'season')
    counts = event_counts(hist)
    folds = np.array([player_fold(pid) for pid in hist['player_id']])
    years = hist['season'].to_numpy()
    return f, hist, counts, folds, years


def references(frame, outer_fold, inner_fold, hist, counts, folds, years):
    probabilities = np.empty((len(frame), 8)); notes = []
    for year in sorted(frame['origin_year'].unique()):
        mask = (years == year) & (folds != outer_fold)
        if inner_fold is not None: mask &= folds != inner_fold
        assert mask.any(), 'Missing dated reference, not a zero profile'
        aggregate = counts[mask].sum(0)+.5; p = aggregate/aggregate.sum()
        rows = frame['origin_year'].to_numpy() == year; probabilities[rows] = p
        notes.append(dict(origin_year=year, outer_fold=outer_fold, inner_fold=inner_fold,
            source_rows=int(mask.sum()), people=hist.filter(pl.Series(mask))['player_id'].to_list(),
            probability=p.tolist(), excludes_outer_and_inner=True))
    return probabilities, notes


def bound_check(rate, index, center):
    rate, index, center = map(np.asarray, [rate, index, center])
    maximum_h = np.maximum(center, np.log(800)-center)
    low = index+(rate-maximum_h)/UNIT; high = index+(rate+maximum_h)/UNIT
    assert (low > VALUES.min()).all() and (high < VALUES.max()).all(), 'Amend before fits: slope bound crosses physical support'
    return dict(minimum_index_at_slope_bounds=float(low.min()), maximum_index_at_slope_bounds=float(high.max()),
                rows=len(rate), all_centers_physical=True)


def prepare():
    assert not (OUT/'preflight.json').exists(), 'Preserve experiment'
    final = read(old.OUT/'final-report.json'); old.check_hashes(final['evidence_hashes']); old.check_hashes(final['local_fit_hashes'])
    review = read(old.OUT/'review-verification.json'); old.check_hashes(review['input_hashes'])
    assert final['player_walkthrough_status'] == 'complete' and review['independently_verified_scalar_quantiles'] == 153
    pre = read(old.OUT/'preflight.json'); prior_fits = read(old.OUT/'fit-report.json')['cells']
    f, hist, counts, folds, years = source(); q = pl.read_parquet(old.current.OUT/'scored-predictions.parquet').sort('row_id')
    supports, profiles, cells = [], [], []; point_replays = set(); check_count = 0
    OUT.mkdir(parents=True, exist_ok=True); WORK.mkdir(parents=True, exist_ok=True)
    original = {(c['year'], c['fold']): c for c in read(old.current.OUT/'preflight.json')['cells']}
    with threadpool_limits(limits=2):
        for c, fit in zip(pre['cells'], prior_fits):
            y, k = c['year'], c['fold']; assert (y, k) == (fit['year'], fit['fold'])
            tr = f.filter(pl.col('row_id').is_in(original[y, k]['training_row_ids'])).filter(pl.col('next_pa') > 0).sort('row_id')
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            s, note = preflight(tr, te, cutoff=y, fold=k, features=pre['rate_features'], expected_keys=te.select('row_id', 'horizon').iter_rows())
            check_count += 1; supports.append(s.with_columns(pl.lit(y).alias('outer_year'), pl.lit(k).alias('outer_fold')))
            calibration = []; reference_notes = []; inner_notes = []
            for n, h in zip(c['nested'], fit['nested_heads']):
                train = f.filter(pl.col('row_id').is_in(n['training_row_ids'])).sort('row_id')
                val = f.filter(pl.col('row_id').is_in(n['validation_row_ids'])).sort('row_id')
                _, nn = preflight(train, val, cutoff=n['origin'], fold=n['inner_fold'], features=pre['rate_features'], expected_keys=val.select('row_id', 'horizon').iter_rows())
                check_count += 1; inner_notes.append(nn)
                assert not set(te['player_id']) & (set(train['player_id']) | set(val['player_id']))
                assert h['training_row_ids'] == n['training_row_ids'] and h['validation_row_ids'] == n['validation_row_ids']
                rp = pl.read_parquet(h['prediction_path']).sort('row_id')
                cp = old.workload.OUT/f'inner-{k}-{n["origin"]}.parquet'
                cr = read(old.workload.OUT/f'inner-{k}-{n["origin"]}.json')
                assert cr['training_row_ids'] == n['training_row_ids'] and cr['validation_row_ids'] == n['validation_row_ids']
                assert sha256_file(cp) == cr['prediction_sha256'] and sha256_file(Path(cr['model_path'])) == cr['model_sha256']
                op = pl.read_parquet(cp).sort('row_id'); assert op['row_id'].equals(rp['row_id']) and val['row_id'].equals(rp['row_id'])
                if h['model_path'] not in point_replays:
                    assert np.allclose(joblib.load(h['model_path']).predict(safe_matrix(val, pre['rate_features'])), rp['nested_rate'], atol=1e-10, rtol=0)
                    pa_names = read(old.workload.OUT/'preflight.json')['features']
                    assert np.allclose(joblib.load(cr['model_path']).predict(val.select(pa_names).to_numpy()), op['raw_conditional_pa'], atol=1e-10, rtol=0)
                    point_replays.add(h['model_path'])
                center, _ = workload_center(op['conditional_pa'], fit['workload_concentration'])
                ref, rn = references(val, k, n['inner_fold'], hist, counts, folds, years)
                bound = bound_check(rp['nested_rate'], val['origin_index'], center)
                refprob = tilt(ref, val['origin_index'].to_numpy()+rp['nested_rate'].to_numpy()/UNIT)
                cal = val.select('row_id', 'player_id', 'origin_year', 'target_year', 'outer_fold', 'next_pa', 'common_rate_label', 'origin_index').with_columns(
                    rp['nested_rate'], op['conditional_pa'], pl.Series('workload_log_center', center),
                    *[pl.Series('reference_'+event, ref[:, j]) for j, event in enumerate(EVENTS)],
                    *[pl.Series('center_probability_'+event, refprob[:, j]) for j, event in enumerate(EVENTS)])
                calibration.append(cal.filter(pl.col('next_pa') > 0)); reference_notes.extend(rn)
                inner_notes[-1]['rate_bounds'] = bound
            cal = pl.concat(calibration).sort('row_id'); assert set(cal['row_id']) == set(c['calibration_row_ids'])
            assert not set(cal['player_id']) & set(te['player_id']) and cal['target_year'].max() <= y
            qp = q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            ref, rn = references(te, k, None, hist, counts, folds, years); reference_notes.extend(rn)
            center, _ = workload_center(qp['preseason_conditional_pa'], fit['workload_concentration'])
            bound = bound_check(qp['preseason_rate'], qp['origin_index'], center)
            test = qp.select('row_id', 'player_id', 'origin_year', 'target_year', 'outer_fold', 'origin_index', 'origin_replacement_rate',
                             'preseason_p', 'preseason_conditional_pa', 'preseason_pa', 'preseason_rate', 'preseason_value', 'next_pa', 'next_value').with_columns(
                pl.Series('workload_log_center', center), *[pl.Series('reference_'+event, ref[:, j]) for j, event in enumerate(EVENTS)])
            calp = WORK/f'calibration-inputs-{y}-{k}.parquet'; tep = WORK/f'forecast-inputs-{y}-{k}.parquet'
            cal.write_parquet(calp); test.write_parquet(tep)
            oldcal = f.filter(pl.col('row_id').is_in(c['calibration_row_ids']))
            profiles.append(old.calibration_profiles(f, oldcal, te).with_columns(pl.lit(y).alias('outer_year'), pl.lit(k).alias('outer_fold')))
            cells.append(dict(year=y, fold=k, test_row_ids=c['test_row_ids'], calibration_row_ids=c['calibration_row_ids'],
                calibration_path=str(calp), test_path=str(tep), reference_notes=reference_notes,
                workload_concentration=fit['workload_concentration'], outer_preflight=note, inner_preflights=inner_notes,
                forecast_rate_bounds=bound, calibration_people=cal['player_id'].n_unique(),
                artifact_hashes={str(p): sha256_file(p) for p in [calp, tep]}))
            print(f'Prepared {y}/{k}: reused nested means; event centers and mean conservation checked', flush=True)
    assert check_count == 130 and len(point_replays) == 50
    pl.concat(supports).write_parquet(OUT/'outer-support.parquet')
    pl.concat(profiles).write_parquet(OUT/'calibration-profile-support.parquet')
    paths = [Path(__file__), ROOT/'src/universal_baseball/hitter_event_count_risk.py', ROOT/'tests/test_hitter_event_count_risk.py',
        ROOT/'docs/hitter-event-count-risk-contract.md', old.OUT/'preflight.json', old.OUT/'final-report.json',
        old.OUT/'review-verification.json', old.OUT/'fit-report.json', old.WORK/'scored-predictions.parquet',
        old.current.OUT/'scored-predictions.parquet', old.current.OUT/'features.parquet', old.VALUE/'features.parquet',
        ROOT/'reports/generated/practical-hitter-v31/counts.parquet', OUT/'outer-support.parquet', OUT/'calibration-profile-support.parquet']
    write(OUT/'preflight.json', dict(before_fitting=True, new_fits=0, actual_checks=130, nested_Ridge_replays=50, nested_PA_replays=50,
        cells=cells, positive_draws=4096, monte_carlo_seed=88004, rate_bounds_checked_before_fitting=True,
        input_hashes={str(p): sha256_file(p) for p in paths}, player_walkthrough_status='pending', protected_outcomes_used=False))


def fit():
    pre = read(OUT/'preflight.json'); old.check_hashes(pre['input_hashes']); notes = []
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y, k = c['year'], c['fold']; finalp = WORK/f'forecast-{y}-{k}.parquet'
            if finalp.exists():
                note = read(WORK/f'fit-{y}-{k}.json'); old.check_hashes(note['output_hashes']); notes.append(note); continue
            old.check_hashes(c['artifact_hashes']); cal = pl.read_parquet(c['calibration_path']); te = pl.read_parquet(c['test_path'])
            pars = fit_count_laws(cal['common_rate_label'], cal['next_pa'], cal['nested_rate'], cal['origin_index'],
                cal.select(['reference_'+v for v in EVENTS]).to_numpy(), cal['workload_log_center'], weights(cal))
            write(WORK/f'parameters-{y}-{k}.json', pars)
            outputs = []
            for r in te.iter_rows(named=True):
                output = {'row_id': r['row_id']}; reference = np.array([r['reference_'+v] for v in EVENTS])
                for arm in ['independent', 'associated']:
                    par = pars[arm]
                    draws = simulate(reference, r['preseason_rate'], r['origin_index'], r['origin_replacement_rate'], r['preseason_p'],
                        r['preseason_conditional_pa'], c['workload_concentration'], par['phi'], par['beta'], row_id=r['row_id'], draws=pre['positive_draws'])
                    terms = mixture_terms(draws['values'], r['preseason_p'], r['next_value'])
                    assert np.isclose(draws['expected_value'], r['preseason_value'], atol=1e-10, rtol=0)
                    output.update({arm+'_'+name: value for name, value in terms.items()})
                    output[arm+'_expected_value'] = draws['expected_value']
                outputs.append(output)
            result = te.hstack(pl.DataFrame(outputs).drop('row_id')); result.write_parquet(finalp)
            note = dict(year=y, fold=k, parameters=pars, forecast_rows=len(result), total_positive_draws=len(result)*pre['positive_draws']*2,
                calibration_people=c['calibration_people'], workload_concentration=c['workload_concentration'],
                output_hashes={str(p): sha256_file(p) for p in [finalp, WORK/f'parameters-{y}-{k}.json']},
                integer_event_checks_pass=True, sampled_envelope_failures=0, theoretical_means_exact=True, player_walkthrough_status='pending')
            write(WORK/f'fit-{y}-{k}.json', note); notes.append(note)
            print(f'Counts {y}/{k}: phi {pars["associated"]["phi"]:.2f}, beta {pars["associated"]["beta"]:+.4f}; {len(result)} forecasts', flush=True)
    q = pl.concat([pl.read_parquet(WORK/f'forecast-{c["year"]}-{c["fold"]}.parquet') for c in pre['cells']]).sort('row_id')
    assert len(q) == 30506 and q['row_id'].n_unique() == 30506
    q.write_parquet(WORK/'predictions.parquet')
    write(OUT/'fit-report.json', dict(cells=notes, forecasts=len(q), new_point_models=0, new_count_calibrations=70,
        positive_draws=pre['positive_draws'], output_sha256=sha256_file(WORK/'predictions.parquet'),
        theoretical_means_exact=True, physical_envelope_failures=0, player_walkthrough_status='pending',
        current_candidate_changed=False, protected_outcomes_used=False))


if __name__ == '__main__':
    {'prepare': prepare, 'fit': fit}[sys.argv[1]]()
