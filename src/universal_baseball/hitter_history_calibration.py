"""Observed-history summaries and past-only prospect calibration, research only."""
import numpy as np
import polars as pl
from scipy.optimize import minimize
from scipy.special import expit, logit

from universal_baseball.hitter_detail_arrival import TARGETS
from universal_baseball.multiyear_hitter_value import CORE_RATES

LEVELS = {'RK': 0, 'ROOKIE': 0, 'A-': 1, 'A': 2, 'A+': 3,
          'AA': 4, 'AAA': 5, 'MLB': 6}


def add_history(panel):
    """Add PA-weighted summaries without filling a canceled season or looking ahead."""
    keys = ['origin_year', 'player_id']
    if panel.select(keys).is_duplicated().any():
        raise ValueError('Duplicate snapshot')
    base = panel.select(*keys, 'pa_lag0', 'missing_lag0',
                        *[r+'_lag0' for r in CORE_RATES],
                        *[f'share_{l}_lag0' for l in LEVELS])
    base = base.with_columns(
        pl.sum_horizontal([pl.col(f'share_{l}_lag0').fill_null(0)*rank
                           for l, rank in LEVELS.items()]).alias('_rank'))
    out = panel
    for lag in (1, 2, 3):
        previous = base.with_columns((pl.col('origin_year')+lag).alias('origin_year'))
        previous = previous.rename({c: f'_h{lag}_{c}' for c in base.columns if c not in keys})
        out = out.join(previous, on=keys, how='left', validate='1:1', maintain_order='left')
    valid = {k: ((pl.col(f'_h{k}_missing_lag0') == 0)
                 & (pl.col(f'_h{k}_pa_lag0') > 0)).fill_null(False) for k in (1, 2, 3)}
    weights = {k: pl.when(valid[k]).then(pl.col(f'_h{k}_pa_lag0')*.7**k)
               .otherwise(0.) for k in (1, 2, 3)}
    current_valid = ((pl.col('missing_lag0') == 0) & (pl.col('pa_lag0') > 0)).fill_null(False)
    current_weight = pl.when(current_valid).then(pl.col('pa_lag0')).otherwise(0.)
    prior_weight = pl.sum_horizontal(list(weights.values()))
    exprs = [pl.sum_horizontal([v.cast(pl.Int32) for v in valid.values()]).alias('history__prior_seasons'),
             pl.coalesce([pl.when(valid[k]).then(pl.lit(k)) for k in (1, 2, 3)])
             .alias('history__last_gap'),
             prior_weight.log1p().alias('history__log_prior_weighted_pa'),
             (prior_weight+current_weight).log1p().alias('history__log_total_weighted_pa'),
             (current_weight/(prior_weight+current_weight)).alias('history__current_evidence_share')]
    for rate in (*CORE_RATES, '_rank'):
        col = rate+'_lag0' if rate != '_rank' else '_rank'
        numerator = pl.sum_horizontal([
            pl.when(pl.col(f'_h{k}_{col}').is_finite()).then(weights[k]*pl.col(f'_h{k}_{col}'))
            .otherwise(0.) for k in weights])
        denominator = pl.sum_horizontal([
            pl.when(pl.col(f'_h{k}_{col}').is_finite()).then(weights[k]).otherwise(0.) for k in weights])
        current = (pl.col(rate+'_lag0') if rate != '_rank' else
                   pl.sum_horizontal([pl.col(f'share_{l}_lag0').fill_null(0)*rank
                                      for l, rank in LEVELS.items()]))
        cw = pl.when(current.is_finite()).then(current_weight).otherwise(0.)
        exprs += [pl.when(denominator > 0).then(numerator/denominator)
                  .alias('history__prior_'+rate),
                  pl.when(denominator+cw > 0).then(
                      (numerator+pl.when(cw > 0).then(cw*current).otherwise(0.))/(denominator+cw))
                  .alias('history__pooled_'+rate)]
    gain = pl.col('path0__level_path__primary_level_change')
    exprs += [(gain*pl.col('age_centered')).alias('history__advancement_age'),
              (gain*pl.col('log_pa_lag0')).alias('history__advancement_exposure')]
    names = [e.meta.output_name() for e in exprs]
    out = out.with_columns(exprs).drop([c for c in out.columns if c.startswith('_h')])
    return out, names


def calibration_pool(history, cutoff, target):
    h = TARGETS[target]
    if cutoff+h > 2025:
        raise ValueError('Protected target')
    pool = history.filter((pl.col('target') == target) & pl.col('prospect')
                          & (pl.col('origin_year') < cutoff)
                          & (pl.col('origin_year')+h <= cutoff)
                          & ~((pl.col('origin_year') < 2020) & (pl.col('origin_year')+h >= 2020))
                          & pl.col('actual').is_finite())
    years = sorted(pool['origin_year'].unique().to_list())[-5:]
    return pool.filter(pl.col('origin_year').is_in(years))


def calibrate(history, current, cutoff, target):
    pool = calibration_pool(history, cutoff, target)
    if pool.select('origin_year', 'player_id').is_duplicated().any():
        raise ValueError('Calibration history must contain one raw arm only')
    years = sorted(pool['origin_year'].unique().to_list())
    y = pool['actual'].to_numpy()
    note = {'origins': years, 'rows': pool.height, 'positives': int(y.sum()),
            'latest_label': max(years)+TARGETS[target] if years else None,
            'penalty': 10., 'fallback': bool(len(years) < 3 or y.sum() < 20 or (1-y).sum() < 20)}
    prob = current['probability'].to_numpy().copy()
    if note['fallback']:
        note.update(intercept=0., slope=1.)
        return prob, note
    w = pool.with_columns((1/pl.len().over('origin_year')).alias('_w'))['_w'].to_numpy()
    w = w / w.mean()
    x = logit(np.clip(pool['probability'].to_numpy(), 1e-6, 1-1e-6))

    def objective(theta):
        a, b = theta
        z = a+b*x
        loss = np.dot(w, np.logaddexp(0, z)-y*z) + 5*(a*a+(b-1)**2)
        resid = w*(expit(z)-y)
        grad = np.array([resid.sum()+10*a, resid@x+10*(b-1)])
        return loss, grad

    fit = minimize(objective, [0., 1.], jac=True, method='L-BFGS-B',
                   bounds=[(-10., 10.), (.05, 5.)], options={'ftol': 1e-12, 'gtol': 1e-8})
    if not fit.success:
        raise RuntimeError(f'Calibration failed: {fit.message}')
    a, b = fit.x
    mask = current['prospect'].to_numpy()
    prob[mask] = expit(a+b*logit(np.clip(prob[mask], 1e-6, 1-1e-6)))
    note.update(intercept=float(a), slope=float(b), objective=float(fit.fun))
    return np.clip(prob, 1e-6, 1-1e-6), note
