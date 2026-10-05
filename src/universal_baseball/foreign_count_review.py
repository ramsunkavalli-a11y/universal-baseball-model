"""Independent arithmetic for reviewing, not refitting, the locked calibration."""
import numpy as np


def pooled_coordinate(seasons):
    own, ref, mass = np.zeros(8), np.zeros(8), 0.
    for s in seasons:
        c = np.asarray(s['counts'], dtype=float)
        n = s['recency'] * c.sum()
        own += n * (c + .5) / (c.sum() + 4)
        ref += n * np.asarray(s['reference'])
        mass += n
    if mass <= 0:
        raise ValueError('No observed source exposure')
    own /= mass; ref /= mass
    a, b = np.log(own), np.log(ref)
    return a - a.mean() - b + b.mean()


def loss_gradient(theta, x, target, reference, exposure, fixed=None):
    """Count cross-entropy independently expanded without the fitted objective."""
    theta, x, target, reference, exposure = map(np.asarray, (theta, x, target, reference, exposure))
    a, b = (theta[:8], theta[8:]) if fixed is None else (fixed[0] + theta, fixed[1])
    z = np.log(reference) + a + b * x
    shifted = z - z.max(axis=1, keepdims=True)
    p = np.exp(shifted); p /= p.sum(axis=1, keepdims=True)
    loss = -float(np.sum(exposure[:, None] * target * np.log(p))) + float(theta @ theta)
    error = exposure[:, None] * (p - target)
    gradient = np.r_[error.sum(0), (error*x).sum(0)] if fixed is None else error.sum(0)
    return loss, gradient + 2*theta


def kkt_residual(theta, gradient, domestic):
    g = np.asarray(gradient).copy()
    if domestic:
        for j in range(8, 16):
            if theta[j] < -1e-10 or theta[j] > 2+1e-10:
                raise ValueError('Slope outside bounds')
            if theta[j] <= 1e-8 and g[j] > 0 or theta[j] >= 2-1e-8 and g[j] < 0:
                g[j] = 0
    return float(np.max(abs(g)))


def peer_distance(a, b):
    """Only origin-known age, exposure, debut and employment hints; no targets."""
    return (abs(a['age']-b['age'])/5
        + abs(np.log1p(a['recent_foreign_pa'])-np.log1p(b['recent_foreign_pa']))
        + 2*(bool(a['prior_debut']) != bool(b['prior_debut']))
        + 2*(a['positive_MLB_context'] != b['positive_MLB_context']))
