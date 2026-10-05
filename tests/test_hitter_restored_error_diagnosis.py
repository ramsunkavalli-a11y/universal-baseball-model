"""Attribution weights must preserve origins and never invent inactive talent."""
import importlib
from pathlib import Path

import numpy as np
import polars as pl
import pytest


@pytest.fixture
def diagnostic(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    return importlib.import_module('diagnose_hitter_restored_errors')


def test_global_weights_partition_unequal_origin_populations(diagnostic):
    q = pl.DataFrame(dict(origin_year=[2017, 2017, 2018], next_pa=[100, 0, 200]))
    value, rate = diagnostic.global_weights(q)
    assert np.allclose(value, [.25, .25, .5])
    assert np.allclose(rate, [.5, 0, .5])
    errors = np.array([1., 9., 4.])
    masks = [np.array([True, False, False]), np.array([False, True, True])]
    assert np.isclose(sum(value[m] @ errors[m] for m in masks), value @ errors)
    # Reweighting each subgroup independently would destroy this attribution.
    assert not np.isclose(sum(np.mean(errors[m]) for m in masks), value @ errors)


def test_independent_geometry_accepts_unobserved_inactive_rate(diagnostic):
    n, pa = np.array([400., 0.]), np.array([100., 50.])
    old, new, a = np.array([5., 2.]), np.array([3., 3.]), np.array([3., np.nan])
    rep = np.full(2, .003)
    actual = np.array([400 * (3 / 600 + .003), 0.])
    q = pl.DataFrame(dict(next_pa=n, components_pa=pa, actual_relative_rate=a, origin_replacement_rate=rep,
                          current_rate=old, components_rate=new, actual_relative_value=actual,
                          current_value=pa * (old / 600 + rep), components_value=pa * (new / 600 + rep)))
    terms, helper = diagnostic.independent_terms(q, 'current')
    assert np.isfinite(terms).all()
    assert helper['new_hitting_error'][0] == 0
    assert np.isnan(helper['old_hitting_error'][1])
    assert terms[1, 1] == terms[1, 2] == 0 and terms[1, 3] != 0
    # More accurate active hitting can expose the common low-playing-time miss.
    assert terms[0, 1] < 0 and terms[0, 0] > 0
