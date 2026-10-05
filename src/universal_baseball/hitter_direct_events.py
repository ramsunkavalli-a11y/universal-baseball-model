"""Defined conversion and proper categorical scoring, with no fitted settings."""
import numpy as np

from .hitter_compatible_value import UNIT
from .mlb_event_logit import VALUES


def probabilities(p):
    p = np.asarray(p, float)
    if p.shape[-1:] != (8,) or not np.isfinite(p).all() or (p <= 0).any() or not np.allclose(p.sum(-1), 1, atol=1e-10, rtol=0):
        raise ValueError('Positive coherent eight-event probability required')
    return p


def convert(p, reference):
    p, reference = probabilities(p), probabilities(reference)
    if p.shape != reference.shape:
        raise ValueError('Paired reference required')
    terms = (p - reference) * VALUES * UNIT
    return terms.sum(-1), terms


def proper_losses(p, counts):
    p = probabilities(p)
    counts = np.asarray(counts, float)
    if counts.shape != p.shape or not np.isfinite(counts).all() or (counts < 0).any():
        raise ValueError('Paired actual event counts required')
    pa = counts.sum(-1)
    if (pa <= 0).any():
        raise ValueError('Non-arrival has no observed event forecast loss')
    frequency = counts / pa[..., None]
    logloss = -(frequency * np.log(p)).sum(-1)
    # Expected one-hot Brier, not squared distance to empirical frequencies.
    brier = (p * p).sum(-1) - 2 * (p * frequency).sum(-1) + 1
    return logloss, brier


def rate_routing(direct, supported, prior_debut, addition, current, fallback):
    arrays = [np.asarray(x) for x in [direct, supported, prior_debut, addition, current, fallback]]
    if any(x.shape != arrays[0].shape for x in arrays):
        raise ValueError('Paired route fields required')
    direct, supported, prior_debut, addition, current, fallback = arrays
    eligible = (prior_debut == 0) | addition.astype(bool)
    used = eligible & supported.astype(bool)
    base = np.where(addition, fallback, current)
    result = np.where(used, direct, base)
    if not np.isfinite(result).all():
        raise ValueError('Missing finite routing fallback')
    return result, used
