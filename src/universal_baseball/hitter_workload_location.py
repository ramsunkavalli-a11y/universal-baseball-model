"""Diagnostic summaries of saved workload laws; never fit or change a mean."""
import numpy as np
import polars as pl
from scipy.stats import betabinom


def scalar_median(p, conditional_mean, concentration):
    """Smallest integer whose mixture CDF reaches .5, checked on both sides."""
    assert 0 <= p <= 1 and 1 <= conditional_mean <= 800 and concentration > 0
    if p <= .5:
        return dict(median=0, cdf_before=0., cdf_at=1-p, positive_quantile=None)
    alpha = 1-.5/p
    if conditional_mean in [1, 800]:
        value = int(conditional_mean)
        return dict(median=value, cdf_before=1-p, cdf_at=1., positive_quantile=alpha)
    mu = (conditional_mean-1)/799
    a, b = mu*concentration, (1-mu)*concentration
    value = 1+int(betabinom.ppf(alpha, 799, a, b))
    before = 1-p + p*float(betabinom.cdf(value-2, 799, a, b))
    at = 1-p + p*float(betabinom.cdf(value-1, 799, a, b))
    assert before < .5 <= at, (value, before, at)
    return dict(median=value, cdf_before=before, cdf_at=at, positive_quantile=alpha)


def location_score(frame, column):
    """Equal represented target years, with raw sums kept separately."""
    assert len(frame) and frame[column].null_count() == 0
    year_terms = []
    for _, g in frame.group_by('target_year'):
        error = (g[column]-g['next_pa']).to_numpy()
        assert np.isfinite(error).all()
        year_terms.append([np.mean(error**2), np.mean(abs(error)), np.mean(error)])
    mse, mae, bias = np.mean(year_terms, axis=0)
    return dict(rmse=float(np.sqrt(mse)), mae=float(mae), bias=float(bias),
                total=float(frame[column].sum()))


def paired_location(frame, absolute):
    y = frame['next_pa'].to_numpy()
    mean = frame['preseason_pa'].to_numpy()-y
    median = frame['risk_q50'].to_numpy()-y
    delta = abs(median)-abs(mean) if absolute else median**2-mean**2
    years, yi = np.unique(frame['target_year'].to_numpy(), return_inverse=True)
    players, pi = np.unique(frame['player_id'].to_numpy(), return_inverse=True)
    den = np.zeros((len(players), len(years))); num = den.copy()
    np.add.at(den, (pi, yi), 1); np.add.at(num, (pi, yi), delta)
    rng = np.random.default_rng(104); draws = []
    for _ in range(1000):
        w = np.bincount(rng.integers(0, len(players), len(players)), minlength=len(players))
        count = w@den
        if (count > 0).all():
            draws.append(float(np.mean((w@num)/count)))
    assert len(draws) > 950
    return dict(metric='MAE' if absolute else 'MSE', contrast='median minus mean',
                estimate=float(np.mean(num.sum(axis=0)/den.sum(axis=0))),
                lower=float(np.quantile(draws, .025)), upper=float(np.quantile(draws, .975)),
                replicates=len(draws), seed=104,
                limit='Nominal player-clustered development sensitivity; no fresh holdout')
