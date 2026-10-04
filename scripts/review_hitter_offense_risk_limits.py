"""Describe physical tails and PA-related calibration bias without changing fits."""
import joblib
from pathlib import Path
import numpy as np
import polars as pl
from scipy.stats import norm
from threadpoolctl import threadpool_limits

from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.hitter_workload_risk import mixture_pmf
from universal_baseball.mlb_event_logit import VALUES
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file
from evaluate_hitter_readiness_v49 import logit_trace
from prepare_practical_hitter_v33 import safe_matrix
from score_hitter_offense_risk import scalar_quantiles
import evaluate_hitter_offense_risk as e


def main():
    assert not (e.OUT/'limits.json').exists(), 'Preserve the descriptive review'
    verified = e.read(e.OUT/'verification.json'); e.check_hashes(verified['output_hashes'])
    q = pl.read_parquet(e.WORK/'scored-predictions.parquet')
    fits = e.read(e.OUT/'fit-report.json')['cells']; f = e.context()
    groups = [('all', q), ('current_MLB', q.filter(pl.col('pa_0') > 0)),
              ('conditional_under100', q.filter(pl.col('preseason_conditional_pa') < 100)),
              ('conditional_100to299', q.filter(pl.col('preseason_conditional_pa').is_between(100, 300, closed='left'))),
              ('conditional_300plus', q.filter(pl.col('preseason_conditional_pa') >= 300))]
    physical = [dict(scope=name, rows=len(g), mean_impossible_mass=float(g['sample_impossible_mass'].mean()),
        maximum_impossible_mass=float(g['sample_impossible_mass'].max()), rows_above_one_percent=int((g['sample_impossible_mass'] > .01).sum())) for name, g in groups]
    bias = []
    for c in fits:
        cal = pl.read_parquet(c['calibration_path']).with_columns((pl.col('common_rate_label')-pl.col('nested_rate')).alias('residual'))
        for name, cond in [('1to49', pl.col('next_pa') < 50), ('50to299', pl.col('next_pa').is_between(50, 300, closed='left')),
                           ('300plus', pl.col('next_pa') >= 300)]:
            g = cal.filter(cond)
            bias.append(dict(outer_year=c['year'], outer_fold=c['fold'], diagnostic_actual_pa_band=name,
                rows=len(g), people=g['player_id'].n_unique(), residual_mean=float(g['residual'].mean()),
                residual_mse=float((g['residual']**2).mean()), qualification='Actual PA is a diagnostic, not a forecast-time routing rule'))
    row = q.sort('sample_impossible_mass', descending=True).row(0, named=True)
    y, k, pid = row['origin_year'], row['outer_fold'], row['player_id']
    cell = next(c for c in fits if (c['year'], c['fold']) == (y, k))
    ft = f.filter(pl.col('row_id') == row['row_id']); names = e.read(e.OUT/'preflight.json')['rate_features']
    model = joblib.load(cell['outer_rate_model']['path']); x = safe_matrix(ft, names)[0]
    assert np.isclose(model.intercept_+x @ model.coef_, row['preseason_rate'], atol=1e-10)
    point_names = e.read(e.current.OUT/'preflight.json')['pa_features']; point_paths = {}
    with threadpool_limits(limits=2):
        for head in e.read(e.current.OUT/f'fit-{y}-{k}.json')['heads']:
            assert sha256_file(Path(head['path'])) == head['sha256']
            m = joblib.load(head['path']); px = ft.select(point_names).to_numpy()[0]
            if head['head'] == 'participation':
                assert np.isclose(m.predict_proba(px[None])[0, 1], row['preseason_raw_p'], atol=1e-10)
                point_paths['participation'] = logit_trace(m, px, point_names)
            else:
                assert np.isclose(m.predict(px[None])[0], row['preseason_raw_conditional_pa'], atol=1e-10)
                point_paths['conditional_pa'] = trace(m, px, point_names)
    pmf = mixture_pmf([row['preseason_p']], [row['preseason_conditional_pa']], cell['workload_concentration'])[0]
    a, b = [cell['variance_parameters']['sample_dependent'][v] for v in ['a', 'b']]
    quantiles = scalar_quantiles(pmf, row['preseason_rate'], row['origin_replacement_rate'], a, b)
    assert np.allclose(quantiles, [row['sample_q'+str(n)] for n in [10, 50, 90]], atol=1e-8)
    n = np.arange(1, 801); sd = n/600*np.sqrt(np.maximum(a+b*600/n, 1e-8))
    mu = n*(row['preseason_rate']/600+row['origin_replacement_rate'])
    lower = n*((VALUES.min()-row['origin_index'])*UNIT/600+row['origin_replacement_rate'])
    upper = n*((VALUES.max()-row['origin_index'])*UNIT/600+row['origin_replacement_rate'])
    masses = pmf[1:]*(norm.cdf(lower, mu, sd)+norm.sf(upper, mu, sd))
    assert np.isclose(masses.sum(), row['sample_impossible_mass'], atol=1e-12)
    peers = q.filter((pl.col('origin_year') == y) & (pl.col('player_id') != pid) & (pl.col('prior_debut') == row['prior_debut']) &
        (pl.col('stage') == row['stage'])).with_columns((((pl.col('age')-row['age'])/3)**2+
        ((pl.col('pa_0')-row['pa_0'])/250)**2+(pl.col('pooled_mlb_quality')-row['pooled_mlb_quality'])**2+
        (pl.col('source_position') != row['source_position']).cast(pl.Float64)).alias('distance')).sort('distance', 'player_id').head(4)
    counts = pl.scan_parquet(e.ROOT/'reports/generated/practical-hitter-v31/counts.parquet').filter(pl.col('season') <= 2025).collect()
    case = dict(origin=row, selection=['largest impossible joint PA and offense probability, descriptive post-result case'],
        source_history=counts.filter((pl.col('player_id') == pid) & pl.col('season').is_between(y-2, y)).sort('season', 'bucket').to_dicts(),
        observed_target_counts=counts.filter((pl.col('player_id') == pid) & (pl.col('season') == y+1) & (pl.col('bucket') == 'MLB')).to_dicts(),
        actual_rate_inputs=ft.select(names).row(0, named=True), actual_opportunity_inputs=ft.select(point_names).row(0, named=True),
        rate_intercept=float(model.intercept_), rate_contributions=dict(zip(names, (x*model.coef_).tolist())), point_paths=point_paths,
        variance_parameters=cell['variance_parameters'], calibration_path=cell['calibration_path'],
        calibration_people=cell['calibration_people'], pa_probability_mass=pmf.tolist(), independent_quantiles={'sample': quantiles},
        impossible_mass_by_pa=masses.tolist(),
        peers=peers.select('player_id', 'player_name', 'age', 'source_position', 'pa_0', 'pooled_mlb_quality', 'preseason_p',
            'preseason_pa', 'preseason_rate', 'preseason_value', 'sample_q10', 'sample_q90', 'next_pa', 'next_value', 'distance').to_dicts(),
        peer_limit='Same origin, broad stage and debut history; age, position, MLB exposure and quality; not speed or medical history',
        player_walkthrough_status='pending')
    e.write(e.OUT/'physical-case.json', case)
    e.write(e.OUT/'limits.json', dict(physical_groups=physical, calibration_bias_by_actual_pa=bias,
        complete_physical_distribution_claim=False, explanation='Normal conditional offense permits impossible outcomes at very small PA; no clipping, routing or fits changed',
        physical_case_row_id=row['row_id'], source_scoring_failure='First scorer failed on boolean negation after all replays, before scores were saved. Explicit float conversion repaired only event-score arithmetic; fits and predictions unchanged.',
        protected_outcomes_used=False))
    print('PHYSICAL', physical, flush=True)
    print('CASE', row['row_id'], row['player_name'], y, row['preseason_pa'], row['preseason_rate'], row['preseason_value'],
          quantiles, 'actual', row['next_pa'], row['next_value'], 'impossible', row['sample_impossible_mass'], flush=True)
    print('STATS', case['source_history'], flush=True)
    print('PEERS', case['peers'], flush=True)


if __name__ == '__main__':
    main()
