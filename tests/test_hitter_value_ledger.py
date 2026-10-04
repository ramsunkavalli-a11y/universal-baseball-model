import numpy as np
import pytest
from universal_baseball.hitter_value_ledger import miss_terms, equal_origin_loss
from universal_baseball.hitter_compatible_value import UNIT


def terms(**overrides):
    values = dict(expected_pa=[400.], predicted_rate=[1.], actual_pa=[600.],
                  actual_relative_rate=[2.], replacement_rate=[.003],
                  origin_index=[.3], target_index=[.32])
    values.update(overrides)
    return miss_terms(**values)


def test_three_terms_reconstruct_two_different_residuals():
    z = terms()
    assert np.allclose(z['relative_actual'] - z['predicted'], z['opportunity'] + z['hitting'])
    assert np.allclose(z['common_actual'] - z['predicted'], z['opportunity'] + z['hitting'] + z['environment'])
    assert np.isclose(z['environment'][0], 600 * .02 * UNIT / 600)


def test_future_environment_does_not_change_forecast():
    a = terms(); b = terms(target_index=[.4])
    for key in ['predicted', 'relative_actual', 'opportunity', 'hitting']:
        assert np.array_equal(a[key], b[key])
    assert not np.array_equal(a['common_actual'], b['common_actual'])


def test_nonarrival_has_no_rate_error_or_environment_effect():
    a = terms(actual_pa=[0.], actual_relative_rate=[0.])
    b = terms(actual_pa=[0.], actual_relative_rate=[10.])
    assert a['relative_actual'][0] == a['common_actual'][0] == 0
    assert a['hitting'][0] == a['environment'][0] == 0
    assert a['opportunity'][0] == -a['predicted'][0]
    assert np.array_equal(a['relative_actual'], b['relative_actual'])


def test_signed_terms_can_cancel_without_correct_components():
    z = terms(predicted_rate=[3.], actual_relative_rate=[1.3333333333333333])
    assert z['opportunity'][0] > 0 and z['hitting'][0] < 0
    assert np.isclose((z['opportunity'] + z['hitting'])[0], -.06666666666666665)


def test_period_weighting_is_not_pooled_row_weighting():
    z = equal_origin_loss([0., 0., 0.], [1., 1., 3.], [2022, 2022, 2023])
    assert z['mse'] == 5 and z['mae'] == 2 and z['bias'] == -2


@pytest.mark.parametrize('kwargs', [dict(expected_pa=[-1.]), dict(replacement_rate=[0.]),
                                  dict(actual_relative_rate=[np.nan]), dict(actual_pa=[1., 2.])])
def test_invalid_diagnostics_rejected(kwargs):
    with pytest.raises(ValueError):
        terms(**kwargs)
