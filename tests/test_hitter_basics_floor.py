import importlib.util
from pathlib import Path

import numpy as np
import polars as pl
import pytest

spec = importlib.util.spec_from_file_location('basics', Path(__file__).parents[1] / 'scripts/check_hitter_basics_floor.py')
basics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(basics)


def sample():
    return pl.DataFrame(dict(row_id=[1, 2, 3], origin_year=[2023, 2023, 2024], target_year=[2024, 2024, 2025],
        source_addition=[False] * 3, current_pa=[600., 600., 600.], next_pa=[600, 0, 600],
        origin_replacement_rate=[.003] * 3, current_rate=[1., 1., 1.], scalar_baseline_rate=[0.] * 3,
        actual_relative_rate=[0., 0., 0.], actual_relative_value=[1.8, 0., 1.8]))


def test_equal_origin_and_nonarrival():
    q = sample()
    basics.validate(q)
    s = basics.score(q, 'current_rate')
    # Each origin equal weight, not each row. Nonarrival keeps its forecast error.
    assert s['value_rmse'] == pytest.approx(np.sqrt(((1 + 2.8 ** 2) / 2 + 1) / 2))
    assert s['rate_rmse'] == pytest.approx(1.)
    assert s['rows'] == 3 and s['active_rows'] == 2


@pytest.mark.parametrize('column,value', [('target_year', 2026), ('source_addition', True), ('current_pa', -1.),
    ('actual_relative_rate', float('nan')), ('origin_replacement_rate', 0.), ('next_pa', -1)])
def test_reject_invalid_scope(column, value):
    q = sample().with_columns(pl.lit(value).alias(column))
    with pytest.raises(ValueError):
        basics.validate(q)


def test_duplicate_and_empty():
    with pytest.raises(ValueError):
        basics.validate(pl.concat([sample(), sample()]))
    with pytest.raises(ValueError):
        basics.validate(sample().head(0))


def test_unobserved_rate_not_measured():
    q = sample().filter(pl.col('next_pa') == 0)
    s = basics.score(q, 'current_rate')
    assert s['rate_rmse'] is None and s['equal_player_rate_rmse'] is None
    assert s['value_rmse'] == pytest.approx(2.8)
