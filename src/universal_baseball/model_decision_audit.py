"""Accounting identities for decision audits; no forecast fitting or selection."""
import numpy as np


def batting_identity(base_value, base_pa, pa, rate):
    """At fixed workload/rate, isolate the inherited direct-value residual."""
    b,w0,w,r=np.broadcast_arrays(*[np.asarray(v,float) for v in (base_value,base_pa,pa,rate)])
    if not all(np.isfinite(v).all() for v in (b,w0,w,r)):
        raise ValueError('Nonfinite inputs')
    product=w*r/600
    residual=b-w0*r/600
    return {'product':product,'marginal':product+residual,'inherited_residual':residual}


def exposure_weighted_identity(probability, pa, rate):
    """Population identity, not a claim that estimated regressions are exact."""
    p=np.asarray(probability,float);w=np.asarray(pa,float);r=np.asarray(rate,float)
    if p.shape!=w.shape or p.shape!=r.shape or p.ndim!=1:
        raise ValueError('Mismatched distributions')
    if not all(np.isfinite(v).all() for v in (p,w,r)) or (p<0).any() or (w<0).any() or not np.isclose(p.sum(),1):
        raise ValueError('Invalid distribution')
    exposure=np.dot(p,w)
    if exposure<=0:raise ValueError('Undefined rate without exposure')
    total=np.dot(p,w*r)
    return {'expected_exposure':float(exposure),'weighted_rate':float(total/exposure),
            'expected_production':float(total),'unweighted_product':float(exposure*np.dot(p,r))}
