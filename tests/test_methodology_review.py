import numpy as np
import pytest
from universal_baseball.methodology_review import component_loss_decomposition, workload_error_decomposition


def test_perfect_component_can_worsen_total_when_other_errors_cancel():
    r=component_loss_decomposition([1,1],[0,0],[1,1],[1,1])
    assert r == dict(component_mse_change=-1, cross_error_term=2, total_mse_change=1)


def test_workload_attribution_keeps_false_positives_and_missed_arrivals():
    r=workload_error_decomposition([.2,.8],[100,200],[300,0])
    assert r['total_pa_error']==-120
    assert r['activity_error_weighted_by_predicted_pa']==80
    assert r['conditional_pa_error_among_actual_participants']==-200


def test_same_identity_weights_are_not_recomputed_for_conditional_head():
    # Equal weight per person before conditioning is a different target measure.
    actual=np.array([100,600,600])
    original_weights=np.array([.25,.5,.5])
    recomputed_weights=np.array([1,.5,.5])
    assert np.average(actual,weights=original_weights)==500
    assert np.average(actual,weights=recomputed_weights)==350


@pytest.mark.parametrize('p,q,w', [([1.1],[1],[1]),([.5],[-1],[1]),([.5],[1],[np.nan])])
def test_invalid_inputs_fail(p,q,w):
    with pytest.raises(ValueError):workload_error_decomposition(p,q,w)
