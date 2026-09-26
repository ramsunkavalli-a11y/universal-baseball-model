"""Read-only review identities; not forecast corrections or model selection."""
import numpy as np


def component_loss_decomposition(other_prediction, other_actual, prediction, actual):
    """Split total MSE change versus neutral into component gain and cross-error."""
    op, oa, p, a = [np.asarray(x, float) for x in
                    (other_prediction, other_actual, prediction, actual)]
    if not (op.shape == oa.shape == p.shape == a.shape) or not op.size:
        raise ValueError('Nonempty matched arrays required')
    if not all(np.isfinite(x).all() for x in (op, oa, p, a)):
        raise ValueError('Finite inputs required')
    delta_component = float(np.mean((p-a)**2-a**2))
    cross_error = float(2*np.mean((op-oa)*p))
    delta_total = float(np.mean((op+p-oa-a)**2-(op-oa-a)**2))
    np.testing.assert_allclose(delta_total, delta_component+cross_error, atol=1e-12)
    return dict(component_mse_change=delta_component, cross_error_term=cross_error,
                total_mse_change=delta_total)


def workload_error_decomposition(probability, conditional_pa, actual_pa):
    """Ex-post attribution only; realized activity is NOT a forecast input."""
    p, q, w = [np.asarray(x, float) for x in (probability, conditional_pa, actual_pa)]
    if not (p.shape == q.shape == w.shape) or not p.size:
        raise ValueError('Nonempty matched arrays required')
    if not all(np.isfinite(x).all() for x in (p,q,w)) or ((p<0)|(p>1)).any() or (q<0).any() or (w<0).any():
        raise ValueError('Invalid probability/exposure')
    a = (w>0).astype(float)
    activity = float(np.sum((p-a)*q))
    workload = float(np.sum(a*(q-w)))
    total = float(np.sum(p*q-w))
    np.testing.assert_allclose(total, activity+workload, atol=1e-8)
    return dict(total_pa_error=total, activity_error_weighted_by_predicted_pa=activity,
                conditional_pa_error_among_actual_participants=workload)
