"""Separate empirical-anchor repair, leaving the V36 likelihood source intact."""
import numpy as np


def empirical_anchor(counts,league,prior=100.):
    if (counts<0).any() or (league<=0).any() or not np.allclose(league.sum(1),1):
        raise ValueError('Invalid empirical anchor inputs')
    return (counts+prior*league)/(counts.sum(1,keepdims=True)+prior)


def transport_anchor(anchor,origin_environment,target_environment):
    raw=anchor*target_environment/origin_environment
    return raw/raw.sum(1,keepdims=True)
