import numpy as np
import polars as pl
import pytest

from universal_baseball.linked_employment_recency import OLD, NEW, transform, feature_names, support


def test_transform_preserves_sources_and_unlinked_age():
    f = pl.DataFrame({OLD: [2., 2., 0.], 'status_major_link': [0, 1, 1], 'future_label': [0, 100, 300]})
    g = transform(f)
    assert g.select(f.columns).equals(f)
    assert g[NEW].to_list() == [2., 0., 0.]
    assert transform(f.with_columns(pl.lit(999).alias('future_label')))[NEW].equals(g[NEW])


@pytest.mark.parametrize('age,link', [(-1, 0), (np.nan, 0), (1, 2), (1, np.nan)])
def test_invalid_source(age, link):
    with pytest.raises(ValueError):
        transform(pl.DataFrame({OLD: [float(age)], 'status_major_link': [float(link)]}))


def test_order_and_single_replacement():
    assert feature_names(['x', OLD, 'y']) == ['x', NEW, 'y']
    for names in [['x'], [OLD, OLD], [OLD, NEW]]:
        with pytest.raises(ValueError):
            feature_names(names)


def test_distinct_people_and_unsupported_profiles():
    a = pl.DataFrame(dict(row_id=[1, 2], player_id=[7, 7], age=[25., 25.], work_1=[500., 500.],
        work_2=[300., 300.], pa_0=[0, 0], status_major_link=[1, 1], obs_status_unresolved_nonmedical=[0, 0]))
    b = a.with_columns(pl.Series('row_id', [3, 4]), pl.Series('status_major_link', [1, 0]))
    assert support(a, b)['continuity_people'].to_list() == [1, 0]
