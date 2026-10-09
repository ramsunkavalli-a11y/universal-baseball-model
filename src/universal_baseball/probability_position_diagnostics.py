"""Discrete calibration and matched-position arithmetic, without model fitting."""
import numpy as np


def pit_bin_mass(pmf, actual, bins=10):
    """Integrate randomized PIT rather than incorrectly placing ties at midpoints."""
    pmf = np.asarray(pmf, dtype=float)
    actual = np.asarray(actual)
    assert pmf.ndim == 2 and len(actual) == len(pmf)
    assert np.isfinite(pmf).all() and (pmf >= 0).all()
    np.testing.assert_allclose(pmf.sum(axis=1), 1, atol=1e-10)
    assert ((actual >= 0) & (actual < pmf.shape[1]) & (actual == actual.astype(int))).all()
    actual = actual.astype(int)
    cdf = np.cumsum(pmf, axis=1)
    hi = np.clip(cdf[np.arange(len(pmf)), actual], 0, 1)
    mass = pmf[np.arange(len(pmf)), actual]
    lo = np.maximum(hi-mass, 0)
    edges = np.linspace(0, 1, bins+1)
    out = np.zeros((len(pmf), bins))
    # Extremely unlikely outcomes can have positive PMF below floating CDF
    # resolution. Use the represented interval width; keep collapsed atoms at
    # their CDF boundary instead of dropping them or dividing by tiny mass.
    width = hi-lo
    positive = width > 0
    for j in range(bins):
        out[positive, j] = np.maximum(0, np.minimum(hi[positive], edges[j+1])-
            np.maximum(lo[positive], edges[j]))/width[positive]
    # Impossible observations still remain, at the corresponding CDF boundary.
    for i in np.flatnonzero(~positive):
        out[i, min(bins-1, max(0, int(hi[i]*bins)))] = 1
    np.testing.assert_allclose(out.sum(axis=1), 1, atol=1e-8)
    return out, lo, hi, mass == 0


def quantile_exceedance(pmf, actual, alphas):
    cdf = np.cumsum(pmf, axis=1)
    quantiles = np.column_stack([np.argmax(cdf >= a, axis=1) for a in alphas])
    predicted = 1-cdf[np.arange(len(pmf))[:, None], quantiles]
    observed = np.asarray(actual)[:, None] > quantiles
    return quantiles, predicted, observed


def paired_position(cf_runs, cf_outs, corner_runs, corner_outs, cf_reference,
                    corner_reference, gap=10):
    """Rates in runs per 500 innings; gap in runs per 1458 innings."""
    assert cf_outs > 0 and corner_outs > 0
    cf = 1500*cf_runs/cf_outs
    corner = 1500*corner_runs/corner_outs
    raw = cf-corner
    relative = raw-cf_reference+corner_reference
    schedule = gap*500/1458
    return dict(cf_rate=cf, corner_rate=corner, raw_difference=raw,
        reference_difference=cf_reference-corner_reference,
        relative_difference=relative, relative_plus_schedule=relative+schedule,
        equalization_gap_per1458=-relative*1458/500,
        raw_plus_schedule=raw+schedule,
        relative_plus_transferred_schedule=relative+schedule+cf_reference-corner_reference)
