"""Value specified whole-player paths; never substitute a mean or invent rights."""
from __future__ import annotations

import numpy as np


def marginal_price(war, breakpoints, rates):
    """Continuous piecewise-linear price with explicit marginal dollar rates.

    Nonpositive production has no acquisition price; obligations remain payable.
    This convention does NOT floor net surplus or erase negative projected WAR.
    """
    breaks, r = np.asarray(breakpoints, float), np.asarray(rates, float)
    if len(r) != len(breaks)+1 or not np.isfinite(r).all() or (r < 0).any():
        raise ValueError('Invalid marginal rates')
    if not np.isfinite(breaks).all() or (breaks <= 0).any() or (np.diff(breaks) <= 0).any():
        raise ValueError('Invalid breakpoints')
    w = np.maximum(np.asarray(war, float), 0)
    if not np.isfinite(w).all():
        raise ValueError('Unknown performance')
    price, lower = np.zeros_like(w), 0.
    for upper, rate in zip(np.append(breaks, np.inf), r):
        price += np.maximum(np.minimum(w, upper)-lower, 0)*rate
        lower = upper
    return price


def value_paths(war, rights, obligations, *, target_kind, tail_complete,
                breakpoints, rates, discount_rate=0., weights=None):
    """Rights and costs are externally supplied paths, not fitted by this function.

    Rights may be fractional only if a caller has explicitly apportioned that
    season's production. Costs must include retained/guaranteed obligations even
    after rights end. The caller must supply a complete control AND liability tail.
    """
    if target_kind != 'whole_war':
        return {'status': 'unavailable', 'reason': 'requires_whole_war', 'mean_surplus': None}
    if not tail_complete:
        return {'status': 'unavailable', 'reason': 'unresolved_rights_or_liability_tail', 'mean_surplus': None}
    if war is None or rights is None or obligations is None:
        return {'status': 'unavailable', 'reason': 'missing_paths', 'mean_surplus': None}
    w, r, c = (np.asarray(a, float) for a in (war, rights, obligations))
    if w.ndim != 2 or not w.size or w.shape != r.shape or w.shape != c.shape:
        raise ValueError('Expected matching nonempty draw-by-year arrays')
    if not all(np.isfinite(a).all() for a in (w, r, c)):
        return {'status': 'unavailable', 'reason': 'unknown_path_entries', 'mean_surplus': None}
    if ((r < 0) | (r > 1)).any() or (c < 0).any() or not np.isfinite(discount_rate) or discount_rate < 0:
        raise ValueError('Invalid rights, obligations or discount rate')
    weights = np.ones(len(w))/len(w) if weights is None else np.asarray(weights, float)
    if weights.shape != (len(w),) or not np.isfinite(weights).all() or (weights < 0).any() or not np.isclose(weights.sum(), 1):
        raise ValueError('Invalid path probabilities')
    discount = (1+discount_rate)**(-np.arange(1, w.shape[1]+1))
    gross = (marginal_price(w, breakpoints, rates)*r*discount).sum(axis=1)
    cost = (c*discount).sum(axis=1)
    surplus = gross-cost
    return {'status': 'specified_scenario_only', 'mean_controlled_war': float(weights @ (w*r).sum(axis=1)),
            'mean_gross_value': float(weights @ gross), 'mean_cost': float(weights @ cost),
            'mean_surplus': float(weights @ surplus), 'surplus_paths': surplus.tolist()}
